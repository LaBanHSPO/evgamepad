from enum import Enum
from typing import Dict, Any, Optional

class ErrorCode(Enum):
    """Standardized error codes"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MT5_NOT_CONNECTED = "MT5_NOT_CONNECTED"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    INSUFFICIENT_MARGIN = "INSUFFICIENT_MARGIN"
    ORDER_REJECTED = "ORDER_REJECTED"
    POSITION_NOT_FOUND = "POSITION_NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    RECONNECTION_FAILED = "RECONNECTION_FAILED"
    ORDER_RECONCILIATION_FAILED = "ORDER_RECONCILIATION_FAILED"

def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create success response"""
    return {
        'success': True,
        **data
    }

def error_response(
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create error response"""
    return {
        'success': False,
        'code': code.value,
        'message': message,
        'details': details or {}
    }
