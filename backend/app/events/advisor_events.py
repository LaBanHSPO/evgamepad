"""
Socket.IO events for AI Trading Advisor.
Handles technical analysis requests.
"""
import logging
import re
from typing import Dict, Any
from datetime import datetime

from app.sio import sio
from app.models.responses import error_response, ErrorCode
from app.advisor.data_fetcher import MT5_TIMEFRAMES

logger = logging.getLogger(__name__)

def validate_symbol(symbol: str) -> bool:
    """Validate symbol: alphanumeric + max 20 chars."""
    return bool(re.match(r'^[A-Z0-9]{1,20}$', symbol))

def validate_timeframe(timeframe: str) -> bool:
    """Validate timeframe against whitelist."""
    return timeframe in MT5_TIMEFRAMES

# Global instances (injected from main.py)
advisor_processor = None
redis_client = None

@sio.event
async def advisor_technical_summary(sid: str, data: Dict[str, Any]):
    """
    Handle technical summary request.

    Request: {
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "indicators": ["sma", "rsi", "macd"]  # optional
    }

    Response: {
        "success": true,
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "last_close": 2105.50,
        "indicators": {...},
        "signals": {...},
        "overall": {...}
    }
    """
    logger.info(f"Technical summary request from {sid}: {data.get('symbol')} {data.get('timeframe')}")

    try:
        # Validate input
        symbol = data.get('symbol', '').upper()
        timeframe = data.get('timeframe', 'H1').upper()
        indicators = data.get('indicators')

        if not symbol or not validate_symbol(symbol):
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                "Invalid symbol format (alphanumeric, max 20 chars)"
            ), to=sid)
            return

        if not validate_timeframe(timeframe):
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                f"Invalid timeframe '{timeframe}'. Allowed: {', '.join(MT5_TIMEFRAMES.keys())}"
            ), to=sid)
            return

        # Process request
        if advisor_processor:
            result = await advisor_processor.process_technical_summary(
                sid, symbol, timeframe, indicators
            )
            await sio.emit('advisor:technical_result', result, to=sid)
        else:
            await sio.emit('advisor:error', error_response(
                ErrorCode.INTERNAL_ERROR,
                "Advisor processor not initialized"
            ), to=sid)

    except Exception as e:
        logger.exception(f"Technical summary failed for {sid}: {e}")
        await sio.emit('advisor:error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Technical analysis failed: {str(e)}"
        ), to=sid)

@sio.event
async def advisor_multi_timeframe(sid: str, data: Dict[str, Any]):
    """
    Handle multi-timeframe analysis request.

    Request: {
        "symbol": "XAUUSD",
        "timeframes": ["H1", "H4", "D1"]
    }
    """
    logger.info(f"Multi-timeframe request from {sid}: {data.get('symbol')}")

    try:
        symbol = data.get('symbol', '').upper()
        timeframes = data.get('timeframes', ['H1', 'H4', 'D1'])

        if not symbol or not validate_symbol(symbol):
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                "Invalid symbol format (alphanumeric, max 20 chars)"
            ), to=sid)
            return

        if advisor_processor:
            result = await advisor_processor.process_multi_timeframe(
                sid, symbol, timeframes
            )
            await sio.emit('advisor:multi_timeframe_result', result, to=sid)
        else:
            await sio.emit('advisor:error', error_response(
                ErrorCode.INTERNAL_ERROR,
                "Advisor processor not initialized"
            ), to=sid)

    except Exception as e:
        logger.exception(f"Multi-timeframe analysis failed for {sid}: {e}")
        await sio.emit('advisor:error', error_response(
            ErrorCode.INTERNAL_ERROR,
            str(e)
        ), to=sid)

@sio.event
async def advisor_pattern_scan(sid: str, data: Dict[str, Any]):
    """
    Handle pattern scan request.

    Request: {
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "include_sr": true
    }

    Response: {
        "success": true,
        "symbol": "XAUUSD",
        "candlestick_patterns": [...],
        "chart_patterns": [...],
        "support_resistance": {...}
    }
    """
    logger.info(f"Pattern scan request from {sid}: {data.get('symbol')} {data.get('timeframe')}")

    try:
        symbol = data.get('symbol', '').upper()
        timeframe = data.get('timeframe', 'H1').upper()
        include_sr = data.get('include_sr', True)

        if not symbol or not validate_symbol(symbol):
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                "Invalid symbol format (alphanumeric, max 20 chars)"
            ), to=sid)
            return

        if not validate_timeframe(timeframe):
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                f"Invalid timeframe '{timeframe}'. Allowed: {', '.join(MT5_TIMEFRAMES.keys())}"
            ), to=sid)
            return

        if advisor_processor:
            result = await advisor_processor.process_pattern_scan(
                sid, symbol, timeframe, include_sr
            )
            await sio.emit('advisor:pattern_result', result, to=sid)
        else:
            await sio.emit('advisor:error', error_response(
                ErrorCode.INTERNAL_ERROR,
                "Advisor processor not initialized"
            ), to=sid)

    except Exception as e:
        logger.exception(f"Pattern scan failed for {sid}: {e}")
        await sio.emit('advisor:error', error_response(
            ErrorCode.INTERNAL_ERROR,
            str(e)
        ), to=sid)
