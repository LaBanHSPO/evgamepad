"""
KOL message processor.

Handles KOL webhook messages: deduplication, storage, and real-time broadcasting.

Feature: KOL Updates MVP
Created: 2025-12-31
"""
import logging
import hashlib
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.kol_models import (
    KOLMessageRequest,
    KOLMessageResponse,
    KOLMessage,
    KOLMessageBroadcast
)
from app.database.pool_manager import DatabasePoolManager

logger = logging.getLogger(__name__)


class KOLProcessor:
    """
    Processor for KOL trading signal messages.

    Responsibilities:
    - Calculate message hash for deduplication
    - Check if message already exists (duplicate detection)
    - Insert new messages into database
    - Broadcast new messages via Socket.IO
    """

    def __init__(self, db_pool_manager: DatabasePoolManager, sio):
        """
        Initialize KOL processor.

        Args:
            db_pool_manager: PostgreSQL connection pool manager
            sio: Socket.IO server instance for broadcasting
        """
        self.db = db_pool_manager
        self.sio = sio

    @staticmethod
    def calculate_message_hash(kol_id: str, timestamp: str, message: str) -> str:
        """
        Generate MD5 hash for message deduplication.

        Hash format: MD5(kol_id|timestamp|message)

        Args:
            kol_id: KOL identifier
            timestamp: ISO 8601 timestamp string
            message: Message content

        Returns:
            32-character MD5 hex digest
        """
        content = f"{kol_id}|{timestamp}|{message}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    async def process_kol_message(self, request: KOLMessageRequest) -> KOLMessageResponse:
        """
        Process incoming KOL webhook message.

        Flow:
        1. Calculate message hash for deduplication
        2. Check if hash exists in database
        3. If duplicate: return existing message_id with deduplicated=True
        4. If new: insert into database, broadcast via Socket.IO
        5. Return message_id with deduplicated=False

        Args:
            request: KOL webhook message request

        Returns:
            KOLMessageResponse with message_id and deduplication status

        Raises:
            Exception: Database connection errors, validation errors
        """
        logger.info(f"Processing KOL message from {request.kol_id}: {request.message[:50]}...")

        # Calculate deduplication hash
        message_hash = self.calculate_message_hash(
            request.kol_id,
            request.timestamp,
            request.message
        )

        try:
            # Check for duplicate message
            existing_message = await self._check_duplicate(message_hash)
            if existing_message:
                logger.info(f"Duplicate message detected: hash={message_hash}, id={existing_message['id']}")
                return KOLMessageResponse(
                    success=True,
                    message_id=str(existing_message['id']),
                    deduplicated=True
                )

            # Insert new message
            new_message = await self._insert_message(request, message_hash)
            logger.info(f"New message inserted: id={new_message.id}")

            # Broadcast to Socket.IO clients
            await self._broadcast_message(new_message)

            return KOLMessageResponse(
                success=True,
                message_id=str(new_message.id),
                deduplicated=False
            )

        except Exception as e:
            logger.error(f"Error processing KOL message: {e}", exc_info=True)
            raise

    async def _check_duplicate(self, message_hash: str) -> Optional[dict]:
        """
        Check if message hash already exists in database.

        Args:
            message_hash: MD5 hash to check

        Returns:
            Existing message record if found, None otherwise
        """
        if not self.db.pool:
            raise RuntimeError("Database pool not initialized")

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, kol_id, message_text FROM kol_messages WHERE message_hash = $1",
                message_hash
            )
            return dict(row) if row else None

    async def _insert_message(self, request: KOLMessageRequest, message_hash: str) -> KOLMessage:
        """
        Insert new KOL message into database.

        Args:
            request: KOL message request
            message_hash: Calculated MD5 hash

        Returns:
            KOLMessage object with inserted data

        Raises:
            Exception: Database insertion errors
        """
        if not self.db.pool:
            raise RuntimeError("Database pool not initialized")

        # Parse timestamp
        received_at = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO kol_messages (
                    kol_id, kol_name, message_text, message_hash,
                    zalo_message_id, received_at, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, kol_id, kol_name, message_text, message_hash,
                          zalo_message_id, received_at, created_at, updated_at, metadata
                """,
                request.kol_id,
                request.kol_name,
                request.message,
                message_hash,
                request.zalo_message_id,
                received_at,
                request.metadata
            )

        return KOLMessage(**dict(row))

    async def _broadcast_message(self, message: KOLMessage) -> None:
        """
        Broadcast new KOL message to all connected Socket.IO clients.

        Emits 'kol:new_message' event with message data.

        Args:
            message: KOLMessage to broadcast

        Note:
            Broadcast failures are logged but do not raise exceptions
            (webhook should succeed even if Socket.IO broadcast fails)
        """
        try:
            # Create broadcast payload
            broadcast = KOLMessageBroadcast(
                message_id=str(message.id),
                kol_id=message.kol_id,
                kol_name=message.kol_name,
                message=message.message_text,
                received_at=message.received_at.isoformat(),
                metadata=message.metadata
            )

            # Emit to all connected clients
            await self.sio.emit(
                'kol:new_message',
                broadcast.model_dump(),
                namespace='/'
            )

            logger.info(f"Broadcast message {message.id} to all clients")

        except Exception as e:
            # Log warning but don't fail the webhook request
            logger.warning(f"Failed to broadcast message {message.id} via Socket.IO: {e}", exc_info=True)
