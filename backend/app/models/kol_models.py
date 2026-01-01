"""
Data models for KOL (Key Opinion Leader) message system.

Feature: KOL Updates MVP
Created: 2025-12-31
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class KOLMessageRequest(BaseModel):
    """
    Request schema for KOL webhook messages.

    Received from Zalo webhook when KOL posts a trading signal.
    """

    kol_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="KOL identifier (alphanumeric + underscore)"
    )
    kol_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="KOL display name"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Trading signal message content"
    )
    timestamp: str = Field(
        ...,
        description="Message timestamp in ISO 8601 format"
    )
    zalo_message_id: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Zalo's internal message ID"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional webhook metadata (zalo_user_id, source, etc.)"
    )

    @field_validator('kol_id')
    @classmethod
    def validate_kol_id(cls, v: str) -> str:
        """Validate kol_id is alphanumeric + underscore only."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('kol_id must be alphanumeric with optional underscores/hyphens')
        return v

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate timestamp is valid ISO 8601 format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError('timestamp must be valid ISO 8601 format (e.g., 2025-12-31T10:00:00Z)')
        return v

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "kol_id": "trader_pro_vn",
                "kol_name": "Trader Pro VN",
                "message": "Canh Buy XAU ET 13-15 SL: 09, Buy XAU entry 14-16 SL:10 1/2 vol",
                "timestamp": "2025-12-31T10:15:30Z",
                "zalo_message_id": "msg_abc123",
                "metadata": {
                    "zalo_user_id": "123456",
                    "source": "zalo_group"
                }
            }
        }


class KOLMessageResponse(BaseModel):
    """
    Response schema for KOL webhook endpoint.

    Returned after processing webhook message.
    """

    success: bool = Field(..., description="Whether message was processed successfully")
    message_id: str = Field(..., description="UUID of stored message")
    deduplicated: bool = Field(
        default=False,
        description="True if message was duplicate (hash already exists)"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "deduplicated": False
            }
        }


class KOLMessage(BaseModel):
    """
    Internal model matching database schema.

    Used for reading from kol_messages table.
    """

    id: UUID = Field(..., description="Message UUID (primary key)")
    kol_id: str = Field(..., description="KOL identifier")
    kol_name: str = Field(..., description="KOL display name")
    message_text: str = Field(..., description="Trading signal content")
    message_hash: str = Field(..., description="MD5 deduplication hash")
    zalo_message_id: Optional[str] = Field(default=None, description="Zalo message ID")
    received_at: datetime = Field(..., description="Webhook receipt timestamp")
    created_at: datetime = Field(..., description="Database creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        """Pydantic config."""
        from_attributes = True  # Enable ORM mode for asyncpg records
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "kol_id": "trader_pro_vn",
                "kol_name": "Trader Pro VN",
                "message_text": "Canh Buy XAU ET 13-15 SL: 09",
                "message_hash": "abc123def456",
                "zalo_message_id": "msg_abc123",
                "received_at": "2025-12-31T10:15:30+00:00",
                "created_at": "2025-12-31T10:15:31+00:00",
                "updated_at": "2025-12-31T10:15:31+00:00",
                "metadata": {
                    "zalo_user_id": "123456",
                    "source": "zalo_group"
                }
            }
        }


class KOLMessageBroadcast(BaseModel):
    """
    Socket.IO event payload for broadcasting new KOL messages.

    Emitted on 'kol:new_message' event to all connected clients.
    """

    message_id: str = Field(..., description="Message UUID")
    kol_id: str = Field(..., description="KOL identifier")
    kol_name: str = Field(..., description="KOL display name")
    message: str = Field(..., description="Trading signal content")
    received_at: str = Field(..., description="Webhook receipt timestamp (ISO 8601)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "kol_id": "trader_pro_vn",
                "kol_name": "Trader Pro VN",
                "message": "Canh Buy XAU ET 13-15 SL: 09",
                "received_at": "2025-12-31T10:15:30Z",
                "metadata": {
                    "zalo_user_id": "123456"
                }
            }
        }
