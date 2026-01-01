"""
KOL webhook API router.

Provides REST API endpoint for receiving KOL messages from Zalo webhook.

Feature: KOL Updates MVP
Created: 2025-12-31
"""
import logging
import secrets
from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Annotated

from app.models.kol_models import KOLMessageRequest, KOLMessageResponse
from app.processors.kol_processor import KOLProcessor
from app.config import config

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(
    prefix="/api/v1/kol",
    tags=["kol"]
)

# Global processor instance (set by main.py during startup)
kol_processor: KOLProcessor = None


def set_kol_processor(processor: KOLProcessor):
    """Set global KOL processor instance (called from main.py)."""
    global kol_processor
    kol_processor = processor


async def verify_api_key(authorization: Annotated[str, Header()]) -> bool:
    """
    Verify Bearer token API key for webhook authentication.

    Args:
        authorization: Authorization header value (format: "Bearer {token}")

    Returns:
        True if valid

    Raises:
        HTTPException: 401 Unauthorized if invalid
    """
    # Parse Bearer token
    if not authorization.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header format")
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Bearer {token}"
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    # Validate API key exists in config
    if not config.KOL_WEBHOOK_API_KEY:
        logger.error("KOL_WEBHOOK_API_KEY not configured in environment")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error"
        )

    # Constant-time comparison to prevent timing attacks
    is_valid = secrets.compare_digest(token, config.KOL_WEBHOOK_API_KEY)

    if not is_valid:
        logger.warning(f"Invalid API key attempt: {token[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return True


@router.post("/message", response_model=KOLMessageResponse)
async def receive_kol_message(
    request: KOLMessageRequest,
    authorized: Annotated[bool, Depends(verify_api_key)]
) -> KOLMessageResponse:
    """
    Receive KOL trading signal from Zalo webhook.

    Authentication: Requires valid Bearer token in Authorization header

    Args:
        request: KOL message request payload
        authorized: Authentication dependency

    Returns:
        KOLMessageResponse with message_id and deduplication status

    Raises:
        HTTPException: 401 Unauthorized, 400 Bad Request, 503 Service Unavailable
    """
    logger.info(f"Received webhook from KOL: {request.kol_id}")

    if not kol_processor:
        logger.error("KOL processor not initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready"
        )

    try:
        # Process message (deduplication, storage, broadcast)
        response = await kol_processor.process_kol_message(request)

        logger.info(
            f"Processed message: id={response.message_id}, "
            f"deduplicated={response.deduplicated}, "
            f"kol={request.kol_id}"
        )

        return response

    except ValueError as e:
        # Validation errors
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except RuntimeError as e:
        # Database connection errors
        logger.error(f"Database error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")

    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error processing KOL message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
