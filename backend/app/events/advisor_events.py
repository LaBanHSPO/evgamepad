"""
Socket.IO events for AI Trading Advisor.
Handles technical analysis requests.
"""
import logging
import re
from typing import Dict, Any
from datetime import datetime
from pydantic import ValidationError

from app.sio import sio
from app.models.responses import error_response, ErrorCode
from app.advisor.data_fetcher import MT5_TIMEFRAMES
from app.models.advisor_models import PortfolioAnalysisRequest

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

@sio.event
async def advisor_risk_analysis(sid: str, data: Dict[str, Any]):
    """
    Handle risk analysis request.

    Request: {
        "symbol": "XAUUSD",
        "account_balance": 10000,
        "entry_price": 2100.50,
        "stop_loss": 2095.00,
        "take_profit": 2115.00,
        "risk_profile": "moderate",
        "timeframe": "H1"  # optional, for ATR calculation
    }

    Response: {
        "success": true,
        "risk_reward": {...},
        "position_sizing": {...},
        "recommendation": {...}
    }
    """
    logger.info(f"Risk analysis request from {sid}: {data}")

    try:
        # Validate required fields
        required = ["account_balance", "entry_price", "stop_loss", "take_profit"]
        for field in required:
            if field not in data:
                await sio.emit('advisor:error', error_response(
                    ErrorCode.VALIDATION_ERROR,
                    f"Missing required field: {field}"
                ), to=sid)
                return

        # Validate numeric fields
        try:
            account_balance = float(data["account_balance"])
            entry_price = float(data["entry_price"])
            stop_loss = float(data["stop_loss"])
            take_profit = float(data["take_profit"])
        except (ValueError, TypeError):
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                "All price fields must be valid numbers"
            ), to=sid)
            return

        # Validate symbol if provided
        symbol = data.get("symbol", "").upper()
        if symbol and not validate_symbol(symbol):
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                "Invalid symbol format (alphanumeric, max 20 chars)"
            ), to=sid)
            return

        if advisor_processor:
            result = await advisor_processor.process_risk_analysis(
                sid,
                symbol,
                account_balance,
                entry_price,
                stop_loss,
                take_profit,
                data.get("risk_profile", "moderate"),
                data.get("timeframe", "H1"),
            )
            await sio.emit('advisor:risk_result', result, to=sid)
        else:
            await sio.emit('advisor:error', error_response(
                ErrorCode.INTERNAL_ERROR,
                "Advisor processor not initialized"
            ), to=sid)

    except Exception as e:
        logger.exception(f"Risk analysis failed for {sid}: {e}")
        await sio.emit('advisor:error', error_response(
            ErrorCode.INTERNAL_ERROR,
            str(e)
        ), to=sid)

@sio.event
async def advisor_recommendation(sid: str, data: Dict[str, Any]):
    """
    Handle personalized recommendation request.

    Request: {
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "language": "vi",
        "risk_profile": "moderate"
    }

    Response: {
        "success": true,
        "symbol": "XAUUSD",
        "recommendation": {...},
        "ai_summary": {...}
    }
    """
    logger.info(f"Recommendation request from {sid}: {data.get('symbol')}")

    try:
        symbol = data.get('symbol', '').upper()
        timeframe = data.get('timeframe', 'H1').upper()
        language = data.get('language', 'vi')
        risk_profile = data.get('risk_profile', 'moderate')

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
            result = await advisor_processor.process_recommendation(
                sid, symbol, timeframe, language, risk_profile
            )
            await sio.emit('advisor:recommendation_result', result, to=sid)
        else:
            await sio.emit('advisor:error', error_response(
                ErrorCode.INTERNAL_ERROR,
                "Advisor processor not initialized"
            ), to=sid)

    except Exception as e:
        logger.exception(f"Recommendation failed for {sid}: {e}")
        await sio.emit('advisor:error', error_response(
            ErrorCode.INTERNAL_ERROR,
            str(e)
        ), to=sid)

@sio.event
async def advisor_portfolio_analysis(sid: str, data: Dict[str, Any]):
    """
    Handle portfolio analysis request.

    Request: {
        "positions": [
            {
                "symbol": "XAUUSD",
                "entry_price": 2100.50,
                "current_price": 2095.00,  # Optional
                "position_size": 0.5,
                "stop_loss": 2090.00,  # Optional
                "timeframe": "H1"
            }
        ],
        "account_balance": 10000,
        "risk_profile": "conservative",
        "language": "vi"
    }

    Response: advisor:portfolio_result event
    """
    logger.info(f"Portfolio analysis request from {sid}: {len(data.get('positions', []))} positions")

    try:
        # Validate request using Pydantic
        try:
            request = PortfolioAnalysisRequest(**data)
        except ValidationError as e:
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                f"Invalid portfolio analysis request: {str(e)}"
            ), to=sid)
            return

        # Validate symbols
        for pos in request.positions:
            if not validate_symbol(pos.symbol):
                await sio.emit('advisor:error', error_response(
                    ErrorCode.VALIDATION_ERROR,
                    f"Invalid symbol format: {pos.symbol}"
                ), to=sid)
                return

        # Process request
        if advisor_processor:
            result = await advisor_processor.process_portfolio_analysis(
                sid,
                request.positions,
                request.account_balance,
                request.risk_profile,
                request.language
            )
            await sio.emit('advisor:portfolio_result', result, to=sid)
        else:
            await sio.emit('advisor:error', error_response(
                ErrorCode.INTERNAL_ERROR,
                "Advisor processor not initialized"
            ), to=sid)

    except Exception as e:
        logger.exception(f"Portfolio analysis failed for {sid}: {e}")
        await sio.emit('advisor:error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Portfolio analysis failed: {str(e)}"
        ), to=sid)

@sio.event
async def advisor_explain_recommendation(sid: str, data: Dict[str, Any]):
    """
    Generate chain-of-thought explanation for recommendation.

    Request: {
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "recommendation_id": "uuid" (optional)
    }

    Response: {
        "success": true,
        "data": {
            "symbol": "XAUUSD",
            "timeframe": "H1",
            "explainability": {
                "steps": [...],
                "total_score": 10,
                "max_score": 12,
                "confidence": 0.83,
                "recommendation": "BUY",
                "reasoning_summary": "...",
                "risks_identified": [...],
                "data_gaps": [...]
            },
            "provenance": {...}
        }
    }
    """
    logger.info(f"Explain recommendation request from {sid}: {data.get('symbol')}")

    try:
        symbol = data.get('symbol', '').upper()
        timeframe = data.get('timeframe', 'H1').upper()

        # Validate inputs
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

        # Generate fresh recommendation with explainability
        if advisor_processor:
            result = await advisor_processor.process_recommendation(
                sid=sid,
                symbol=symbol,
                timeframe=timeframe,
                language='en',
                risk_profile='moderate',
                enable_explainability=True
            )

            # Extract explainability data
            if result.get('success') and 'explainability' in result:
                await sio.emit('advisor:explanation_result', {
                    "success": True,
                    "data": {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "explainability": result.get('explainability'),
                        "provenance": result.get('provenance')
                    }
                }, to=sid)
            else:
                await sio.emit('advisor:error', error_response(
                    ErrorCode.INTERNAL_ERROR,
                    "Explainability data not available (feature may be disabled)"
                ), to=sid)
        else:
            await sio.emit('advisor:error', error_response(
                ErrorCode.INTERNAL_ERROR,
                "Advisor processor not initialized"
            ), to=sid)

    except Exception as e:
        logger.exception(f"Explain recommendation failed for {sid}: {e}")
        await sio.emit('advisor:error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Explanation generation failed: {str(e)}"
        ), to=sid)
