"""
PostgreSQL connection pool manager.

Phase 5.2: Accuracy Tracking System - Database Infrastructure
"""
import logging
import asyncpg
from typing import Optional

logger = logging.getLogger(__name__)


class DatabasePoolManager:
    """Manages PostgreSQL connection pool using asyncpg."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "ev_gamepad",
        user: str = "postgres",
        password: str = "",
        min_size: int = 2,
        max_size: int = 10
    ):
        """
        Initialize database pool manager.

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Database password
            min_size: Minimum pool size
            max_size: Maximum pool size
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> bool:
        """
        Create connection pool.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_size,
                max_size=self.max_size
            )
            logger.info(f"PostgreSQL pool created: {self.database}@{self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            return False

    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL pool closed")

    def get_pool(self) -> Optional[asyncpg.Pool]:
        """
        Get connection pool.

        Returns:
            Connection pool or None if not initialized
        """
        return self.pool

    async def is_connected(self) -> bool:
        """
        Check if pool is connected and healthy.

        Returns:
            True if pool is healthy, False otherwise
        """
        if not self.pool:
            return False

        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False
