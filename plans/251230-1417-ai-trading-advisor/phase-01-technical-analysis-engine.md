# Phase 1: Technical Analysis Engine

## Context Links
- Main Plan: `plan.md`
- Research: `research/researcher-01-technical-analysis.md`
- Architecture: `../reports/researcher-251230-1418-ai-trading-advisor-architecture.md`
- Existing Backend: `backend/app/`

---

## Overview

Build core technical indicator calculation engine using pandas-ta library. Implement Redis caching for computed indicators to achieve sub-50ms response times on cache hits. Expose via `advisor:technical_summary` Socket.IO event.

**Effort:** 8 hours
**Priority:** P1 (foundation for all other phases)

---

## Key Insights from Research

1. **pandas-ta chosen over TA-Lib:** Easier installation (pure pip), 150+ indicators, adequate performance for <1000 users
2. **Capital Companion validated indicators:** 21 EMA, RSI, MACD, Bollinger Bands, ATR
3. **Multi-timeframe analysis:** Analyze 15m, 1h, 4h, 1D simultaneously for "power zones"
4. **Caching strategy:** Pre-compute 50-100 candles; 5min TTL; update on new close

---

## Requirements

### Functional
- FR1: Calculate 10 core indicators for any symbol/timeframe
- FR2: Support multi-timeframe analysis (15m, H1, H4, D1)
- FR3: Cache computed indicators in Redis (5min TTL)
- FR4: Fetch OHLCV data from MT5 terminal
- FR5: Emit results via `advisor:technical_summary` event

### Non-Functional
- NFR1: Fresh computation < 500ms
- NFR2: Cached response < 50ms
- NFR3: Handle 100 concurrent requests

---

## Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    advisor_events.py                           │
│               @sio.event('advisor:technical_summary')          │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                   advisor_processor.py                         │
│              AdvisorProcessor.process_technical_summary()      │
└──────────────────────────┬─────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│ data_fetcher.py │ │redis_client │ │technical_       │
│                 │ │   .py       │ │analyzer.py      │
│ - fetch_ohlcv() │ │             │ │                 │
│ - from MT5      │ │ - get_cache │ │ - calculate_    │
│ - from TwelveD  │ │ - set_cache │ │   indicators()  │
└────────┬────────┘ └──────┬──────┘ └────────┬────────┘
         │                 │                  │
         │        ┌────────┴────────┐         │
         │        │                 │         │
         ▼        ▼                 ▼         │
    ┌─────────┐ ┌─────────┐   ┌─────────┐    │
    │   MT5   │ │  Redis  │   │pandas-ta│◄───┘
    │Terminal │ │  Cache  │   │ library │
    └─────────┘ └─────────┘   └─────────┘
```

### Data Flow

```
Request: { symbol: "XAUUSD", timeframes: ["H1", "H4"] }
                           │
                           ▼
                   Check Redis Cache
                   ┌────────┴────────┐
               HIT │                 │ MISS
                   ▼                 ▼
            Return cached      Fetch OHLCV from MT5
                           │
                           ▼
                   Calculate indicators
                   (pandas-ta)
                           │
                           ▼
                   Store in Redis
                   (TTL: 5 min)
                           │
                           ▼
                   Return response
```

---

## Related Code Files

### Existing (KEEP)
- `backend/app/main.py` - Add advisor service initialization
- `backend/app/sio.py` - Socket.IO server (no changes)
- `backend/app/config.py` - Add Redis config
- `backend/app/mt5/connection_manager.py` - Use for data fetching

### New (CREATE)
- `backend/app/advisor/__init__.py`
- `backend/app/advisor/technical_analyzer.py`
- `backend/app/advisor/data_fetcher.py`
- `backend/app/database/redis_client.py`
- `backend/app/events/advisor_events.py`
- `backend/app/processors/advisor_processor.py`
- `backend/app/models/advisor_models.py`

---

## Implementation Steps

### Step 1: Redis Client (1h)

**File:** `backend/app/database/redis_client.py`

```python
"""
Redis cache client for technical indicators.
Implements get/set with automatic serialization and TTL.
"""
import json
import logging
from typing import Optional, Any, Dict
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisClient:
    """Async Redis client wrapper for indicator caching."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> bool:
        """Initialize Redis connection pool."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            await self._client.ping()
            logger.info(f"Redis connected: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False

    async def disconnect(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis disconnected")

    async def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        Get cached indicators for symbol/timeframe.
        Returns None if cache miss.
        """
        if not self._client:
            return None

        key = f"indicators:{symbol}:{timeframe}"
        try:
            data = await self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Redis GET failed: {e}")
            return None

    async def set_indicators(
        self,
        symbol: str,
        timeframe: str,
        data: Dict[str, Any],
        ttl: int = 300  # 5 minutes
    ) -> bool:
        """
        Cache indicators for symbol/timeframe.
        TTL in seconds (default 5 min).
        """
        if not self._client:
            return False

        key = f"indicators:{symbol}:{timeframe}"
        try:
            await self._client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")
            return False

    async def is_connected(self) -> bool:
        """Check Redis connection health."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except:
            return False
```

### Step 2: Data Fetcher (1.5h)

**File:** `backend/app/advisor/data_fetcher.py`

```python
"""
OHLCV data fetcher from MT5 terminal.
Supports multiple timeframes and lookback periods.
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

# MT5 timeframe mapping
MT5_TIMEFRAMES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
    "W1": 10080,
    "MN1": 43200,
}

class DataFetcher:
    """Fetches OHLCV data from MT5 terminal."""

    def __init__(self, mt5_manager):
        """
        Args:
            mt5_manager: MT5ConnectionManager instance
        """
        self.mt5_manager = mt5_manager

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        count: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from MT5.

        Args:
            symbol: Trading symbol (e.g., "XAUUSD")
            timeframe: Timeframe string (e.g., "H1", "H4", "D1")
            count: Number of candles to fetch (default 100)

        Returns:
            DataFrame with columns: time, open, high, low, close, volume
            None if fetch fails
        """
        try:
            # Import MT5 in thread to avoid blocking
            import MetaTrader5 as mt5

            # Convert timeframe string to MT5 constant
            tf_minutes = MT5_TIMEFRAMES.get(timeframe.upper())
            if tf_minutes is None:
                logger.error(f"Invalid timeframe: {timeframe}")
                return None

            # Map to MT5 timeframe constant
            tf_map = {
                1: mt5.TIMEFRAME_M1,
                5: mt5.TIMEFRAME_M5,
                15: mt5.TIMEFRAME_M15,
                30: mt5.TIMEFRAME_M30,
                60: mt5.TIMEFRAME_H1,
                240: mt5.TIMEFRAME_H4,
                1440: mt5.TIMEFRAME_D1,
                10080: mt5.TIMEFRAME_W1,
                43200: mt5.TIMEFRAME_MN1,
            }
            mt5_tf = tf_map.get(tf_minutes)

            # Fetch data in thread (MT5 is blocking)
            def _fetch():
                rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)
                return rates

            rates = await asyncio.to_thread(_fetch)

            if rates is None or len(rates) == 0:
                logger.warning(f"No data returned for {symbol} {timeframe}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.rename(columns={
                'tick_volume': 'volume'
            })

            # Select and order columns
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]

            logger.debug(f"Fetched {len(df)} candles for {symbol} {timeframe}")
            return df

        except Exception as e:
            logger.exception(f"Failed to fetch OHLCV for {symbol} {timeframe}: {e}")
            return None

    async def fetch_multi_timeframe(
        self,
        symbol: str,
        timeframes: List[str],
        count: int = 100
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Fetch OHLCV for multiple timeframes concurrently.

        Args:
            symbol: Trading symbol
            timeframes: List of timeframe strings
            count: Number of candles per timeframe

        Returns:
            Dict mapping timeframe to DataFrame (or None if failed)
        """
        tasks = [
            self.fetch_ohlcv(symbol, tf, count)
            for tf in timeframes
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            tf: result if not isinstance(result, Exception) else None
            for tf, result in zip(timeframes, results)
        }
```

### Step 3: Technical Analyzer (2.5h)

**File:** `backend/app/advisor/technical_analyzer.py`

```python
"""
Technical indicator calculator using pandas-ta.
Computes moving averages, oscillators, volatility indicators.
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import pandas_ta as ta

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """Calculates technical indicators for OHLCV data."""

    # Default indicator parameters
    DEFAULT_PARAMS = {
        "sma_periods": [20, 50, 200],
        "ema_periods": [9, 21, 50],
        "rsi_period": 14,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "bb_period": 20,
        "bb_std": 2,
        "atr_period": 14,
        "adx_period": 14,
        "stoch_k": 14,
        "stoch_d": 3,
    }

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Args:
            params: Override default indicator parameters
        """
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}

    def calculate_indicators(
        self,
        df: pd.DataFrame,
        indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate technical indicators from OHLCV DataFrame.

        Args:
            df: OHLCV DataFrame with columns: time, open, high, low, close, volume
            indicators: List of indicators to calculate. If None, calculates all.

        Returns:
            Dict with indicator values and metadata
        """
        if df is None or df.empty:
            return {"error": "No data provided"}

        # Default to all indicators
        if indicators is None:
            indicators = ["sma", "ema", "rsi", "macd", "bb", "atr", "adx", "stoch", "obv"]

        result = {
            "symbol": None,  # Set by caller
            "timeframe": None,  # Set by caller
            "candles": len(df),
            "last_close": float(df['close'].iloc[-1]),
            "last_time": df['time'].iloc[-1].isoformat() if hasattr(df['time'].iloc[-1], 'isoformat') else str(df['time'].iloc[-1]),
            "indicators": {},
            "signals": {},
        }

        try:
            # === MOVING AVERAGES ===
            if "sma" in indicators:
                for period in self.params["sma_periods"]:
                    sma = ta.sma(df['close'], length=period)
                    if sma is not None and len(sma) > 0:
                        result["indicators"][f"sma_{period}"] = round(float(sma.iloc[-1]), 5) if pd.notna(sma.iloc[-1]) else None

            if "ema" in indicators:
                for period in self.params["ema_periods"]:
                    ema = ta.ema(df['close'], length=period)
                    if ema is not None and len(ema) > 0:
                        result["indicators"][f"ema_{period}"] = round(float(ema.iloc[-1]), 5) if pd.notna(ema.iloc[-1]) else None

            # === MOMENTUM ===
            if "rsi" in indicators:
                rsi = ta.rsi(df['close'], length=self.params["rsi_period"])
                if rsi is not None and len(rsi) > 0:
                    rsi_val = float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None
                    result["indicators"]["rsi"] = round(rsi_val, 2) if rsi_val else None
                    # Signal
                    if rsi_val:
                        if rsi_val < 30:
                            result["signals"]["rsi"] = "oversold"
                        elif rsi_val > 70:
                            result["signals"]["rsi"] = "overbought"
                        else:
                            result["signals"]["rsi"] = "neutral"

            if "macd" in indicators:
                macd = ta.macd(
                    df['close'],
                    fast=self.params["macd_fast"],
                    slow=self.params["macd_slow"],
                    signal=self.params["macd_signal"]
                )
                if macd is not None and len(macd) > 0:
                    macd_line = macd.iloc[-1, 0] if pd.notna(macd.iloc[-1, 0]) else None
                    signal_line = macd.iloc[-1, 2] if pd.notna(macd.iloc[-1, 2]) else None
                    histogram = macd.iloc[-1, 1] if pd.notna(macd.iloc[-1, 1]) else None

                    result["indicators"]["macd"] = {
                        "macd": round(float(macd_line), 5) if macd_line else None,
                        "signal": round(float(signal_line), 5) if signal_line else None,
                        "histogram": round(float(histogram), 5) if histogram else None,
                    }

                    # Signal: crossover detection
                    if macd_line and signal_line:
                        if len(macd) >= 2:
                            prev_macd = macd.iloc[-2, 0] if pd.notna(macd.iloc[-2, 0]) else None
                            prev_signal = macd.iloc[-2, 2] if pd.notna(macd.iloc[-2, 2]) else None
                            if prev_macd and prev_signal:
                                if prev_macd < prev_signal and macd_line > signal_line:
                                    result["signals"]["macd"] = "bullish_crossover"
                                elif prev_macd > prev_signal and macd_line < signal_line:
                                    result["signals"]["macd"] = "bearish_crossover"
                                else:
                                    result["signals"]["macd"] = "bullish" if macd_line > signal_line else "bearish"

            if "stoch" in indicators:
                stoch = ta.stoch(
                    df['high'], df['low'], df['close'],
                    k=self.params["stoch_k"],
                    d=self.params["stoch_d"]
                )
                if stoch is not None and len(stoch) > 0:
                    k_val = float(stoch.iloc[-1, 0]) if pd.notna(stoch.iloc[-1, 0]) else None
                    d_val = float(stoch.iloc[-1, 1]) if pd.notna(stoch.iloc[-1, 1]) else None
                    result["indicators"]["stochastic"] = {
                        "k": round(k_val, 2) if k_val else None,
                        "d": round(d_val, 2) if d_val else None,
                    }

            # === VOLATILITY ===
            if "bb" in indicators:
                bb = ta.bbands(
                    df['close'],
                    length=self.params["bb_period"],
                    std=self.params["bb_std"]
                )
                if bb is not None and len(bb) > 0:
                    result["indicators"]["bollinger"] = {
                        "upper": round(float(bb.iloc[-1, 0]), 5) if pd.notna(bb.iloc[-1, 0]) else None,
                        "middle": round(float(bb.iloc[-1, 1]), 5) if pd.notna(bb.iloc[-1, 1]) else None,
                        "lower": round(float(bb.iloc[-1, 2]), 5) if pd.notna(bb.iloc[-1, 2]) else None,
                    }
                    # Signal: price position relative to bands
                    if all(bb.iloc[-1, :3].notna()):
                        price = df['close'].iloc[-1]
                        upper = bb.iloc[-1, 0]
                        lower = bb.iloc[-1, 2]
                        if price >= upper:
                            result["signals"]["bollinger"] = "upper_band"
                        elif price <= lower:
                            result["signals"]["bollinger"] = "lower_band"
                        else:
                            result["signals"]["bollinger"] = "inside"

            if "atr" in indicators:
                atr = ta.atr(
                    df['high'], df['low'], df['close'],
                    length=self.params["atr_period"]
                )
                if atr is not None and len(atr) > 0:
                    atr_val = float(atr.iloc[-1]) if pd.notna(atr.iloc[-1]) else None
                    result["indicators"]["atr"] = round(atr_val, 5) if atr_val else None
                    # ATR as % of price
                    if atr_val:
                        result["indicators"]["atr_pct"] = round(atr_val / df['close'].iloc[-1] * 100, 2)

            # === TREND ===
            if "adx" in indicators:
                adx = ta.adx(
                    df['high'], df['low'], df['close'],
                    length=self.params["adx_period"]
                )
                if adx is not None and len(adx) > 0:
                    adx_val = float(adx.iloc[-1, 0]) if pd.notna(adx.iloc[-1, 0]) else None
                    plus_di = float(adx.iloc[-1, 1]) if pd.notna(adx.iloc[-1, 1]) else None
                    minus_di = float(adx.iloc[-1, 2]) if pd.notna(adx.iloc[-1, 2]) else None

                    result["indicators"]["adx"] = {
                        "adx": round(adx_val, 2) if adx_val else None,
                        "plus_di": round(plus_di, 2) if plus_di else None,
                        "minus_di": round(minus_di, 2) if minus_di else None,
                    }

                    # Signal: trend strength
                    if adx_val:
                        if adx_val < 20:
                            result["signals"]["adx"] = "no_trend"
                        elif adx_val < 40:
                            result["signals"]["adx"] = "moderate_trend"
                        else:
                            result["signals"]["adx"] = "strong_trend"

            # === VOLUME ===
            if "obv" in indicators:
                obv = ta.obv(df['close'], df['volume'])
                if obv is not None and len(obv) > 0:
                    result["indicators"]["obv"] = int(obv.iloc[-1]) if pd.notna(obv.iloc[-1]) else None

            # === TREND DIRECTION ===
            # Simple trend based on EMAs
            ema_21 = result["indicators"].get("ema_21")
            ema_50 = result["indicators"].get("ema_50")
            price = result["last_close"]

            if ema_21 and ema_50:
                if price > ema_21 > ema_50:
                    result["signals"]["trend"] = "bullish"
                elif price < ema_21 < ema_50:
                    result["signals"]["trend"] = "bearish"
                else:
                    result["signals"]["trend"] = "mixed"

            return result

        except Exception as e:
            logger.exception(f"Error calculating indicators: {e}")
            return {"error": str(e)}

    def get_overall_signal(self, indicators_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate individual signals into overall assessment.

        Args:
            indicators_result: Output from calculate_indicators()

        Returns:
            Dict with overall signal, confidence, and reasoning
        """
        signals = indicators_result.get("signals", {})

        bullish_count = 0
        bearish_count = 0
        neutral_count = 0

        for key, value in signals.items():
            if "bullish" in str(value).lower() or value in ["oversold", "lower_band"]:
                bullish_count += 1
            elif "bearish" in str(value).lower() or value in ["overbought", "upper_band"]:
                bearish_count += 1
            else:
                neutral_count += 1

        total = bullish_count + bearish_count + neutral_count
        if total == 0:
            return {"signal": "neutral", "confidence": 0, "reasoning": "No signals available"}

        if bullish_count > bearish_count:
            signal = "bullish"
            confidence = bullish_count / total
        elif bearish_count > bullish_count:
            signal = "bearish"
            confidence = bearish_count / total
        else:
            signal = "neutral"
            confidence = neutral_count / total

        return {
            "signal": signal,
            "confidence": round(confidence, 2),
            "bullish_signals": bullish_count,
            "bearish_signals": bearish_count,
            "neutral_signals": neutral_count,
            "reasoning": signals,
        }
```

### Step 4: Advisor Models (0.5h)

**File:** `backend/app/models/advisor_models.py`

```python
"""
Pydantic models for AI Trading Advisor responses.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class TechnicalIndicators(BaseModel):
    """Container for computed technical indicators."""
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[Dict[str, float]] = None
    bollinger: Optional[Dict[str, float]] = None
    atr: Optional[float] = None
    atr_pct: Optional[float] = None
    adx: Optional[Dict[str, float]] = None
    stochastic: Optional[Dict[str, float]] = None
    obv: Optional[int] = None

class SignalSummary(BaseModel):
    """Aggregated signal assessment."""
    signal: str = Field(..., description="Overall signal: bullish, bearish, neutral")
    confidence: float = Field(..., ge=0, le=1, description="Confidence 0-1")
    bullish_signals: int = 0
    bearish_signals: int = 0
    neutral_signals: int = 0
    reasoning: Dict[str, str] = Field(default_factory=dict)

class TechnicalSummaryResponse(BaseModel):
    """Response for advisor:technical_summary event."""
    success: bool = True
    symbol: str
    timeframe: str
    last_close: float
    last_time: str
    candles: int
    indicators: Dict[str, Any]
    signals: Dict[str, str]
    overall: SignalSummary
    cached: bool = False
    computed_at: datetime = Field(default_factory=datetime.utcnow)

class TechnicalSummaryRequest(BaseModel):
    """Request for advisor:technical_summary event."""
    symbol: str = Field(..., min_length=1, max_length=20)
    timeframe: str = Field(default="H1", pattern="^(M1|M5|M15|M30|H1|H4|D1|W1|MN1)$")
    indicators: Optional[List[str]] = None

class MultiTimeframeRequest(BaseModel):
    """Request for multi-timeframe analysis."""
    symbol: str = Field(..., min_length=1, max_length=20)
    timeframes: List[str] = Field(default=["H1", "H4", "D1"])
    indicators: Optional[List[str]] = None
```

### Step 5: Advisor Events (1.5h)

**File:** `backend/app/events/advisor_events.py`

```python
"""
Socket.IO events for AI Trading Advisor.
Handles technical analysis requests.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from app.sio import sio
from app.models.responses import error_response, ErrorCode

logger = logging.getLogger(__name__)

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

        if not symbol:
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                "Symbol is required"
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

        if not symbol:
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                "Symbol is required"
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
```

### Step 6: Advisor Processor (1h)

**File:** `backend/app/processors/advisor_processor.py`

```python
"""
Advisor command processor.
Routes Socket.IO events to technical analysis components.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.advisor.technical_analyzer import TechnicalAnalyzer
from app.advisor.data_fetcher import DataFetcher
from app.database.redis_client import RedisClient
from app.models.responses import success_response, error_response, ErrorCode

logger = logging.getLogger(__name__)

class AdvisorProcessor:
    """
    Central processor for advisor commands.
    Handles caching, data fetching, and analysis coordination.
    """

    def __init__(
        self,
        mt5_manager,
        redis_client: Optional[RedisClient] = None
    ):
        self.data_fetcher = DataFetcher(mt5_manager)
        self.analyzer = TechnicalAnalyzer()
        self.redis_client = redis_client

    async def process_technical_summary(
        self,
        sid: str,
        symbol: str,
        timeframe: str,
        indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process technical summary request with caching.
        """
        logger.info(f"[{sid}] Processing technical summary: {symbol} {timeframe}")

        # Check cache first
        if self.redis_client:
            cached = await self.redis_client.get_indicators(symbol, timeframe)
            if cached:
                logger.debug(f"[{sid}] Cache hit for {symbol} {timeframe}")
                cached['cached'] = True
                return success_response(cached)

        # Fetch OHLCV data
        df = await self.data_fetcher.fetch_ohlcv(symbol, timeframe, count=100)
        if df is None:
            return error_response(
                ErrorCode.MT5_ERROR,
                f"Failed to fetch data for {symbol} {timeframe}"
            )

        # Calculate indicators
        result = self.analyzer.calculate_indicators(df, indicators)
        if "error" in result:
            return error_response(ErrorCode.INTERNAL_ERROR, result["error"])

        # Add metadata
        result["symbol"] = symbol
        result["timeframe"] = timeframe
        result["overall"] = self.analyzer.get_overall_signal(result)
        result["cached"] = False
        result["computed_at"] = datetime.utcnow().isoformat()

        # Cache result
        if self.redis_client:
            await self.redis_client.set_indicators(symbol, timeframe, result, ttl=300)

        return success_response(result)

    async def process_multi_timeframe(
        self,
        sid: str,
        symbol: str,
        timeframes: List[str]
    ) -> Dict[str, Any]:
        """
        Process multi-timeframe analysis.
        Returns analysis for each timeframe + alignment summary.
        """
        logger.info(f"[{sid}] Processing multi-timeframe: {symbol} {timeframes}")

        results = {}
        signals = []

        for tf in timeframes:
            # Process each timeframe
            tf_result = await self.process_technical_summary(sid, symbol, tf, None)
            if tf_result.get('success'):
                results[tf] = tf_result.get('data', {})
                overall = results[tf].get('overall', {})
                signals.append({
                    "timeframe": tf,
                    "signal": overall.get('signal', 'neutral'),
                    "confidence": overall.get('confidence', 0),
                })
            else:
                results[tf] = {"error": tf_result.get('message', 'Failed')}

        # Calculate alignment
        bullish_count = sum(1 for s in signals if s['signal'] == 'bullish')
        bearish_count = sum(1 for s in signals if s['signal'] == 'bearish')
        total = len(signals)

        if bullish_count == total:
            alignment = "strong_bullish"
        elif bearish_count == total:
            alignment = "strong_bearish"
        elif bullish_count > bearish_count:
            alignment = "bullish_bias"
        elif bearish_count > bullish_count:
            alignment = "bearish_bias"
        else:
            alignment = "mixed"

        return success_response({
            "symbol": symbol,
            "timeframes": results,
            "alignment": {
                "status": alignment,
                "bullish_count": bullish_count,
                "bearish_count": bearish_count,
                "signals": signals,
            },
            "power_zone": alignment in ["strong_bullish", "strong_bearish"],
            "computed_at": datetime.utcnow().isoformat(),
        })
```

### Step 7: Integration with main.py (0.5h)

**Modify:** `backend/app/main.py`

Add to imports:
```python
from app.database.redis_client import RedisClient
from app.processors.advisor_processor import AdvisorProcessor
from app.events import advisor_events
```

Add to global instances:
```python
redis_client = None
advisor_processor = None
```

Add to lifespan (after mt5_manager init):
```python
# Initialize Redis
redis_client = RedisClient(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB
)
if not await redis_client.connect():
    logger.warning("Redis not available - caching disabled")
    redis_client = None

# Initialize Advisor Processor
advisor_processor = AdvisorProcessor(mt5_manager, redis_client)

# Inject into advisor events
advisor_events.advisor_processor = advisor_processor
advisor_events.redis_client = redis_client
```

Add to config.py:
```python
# Redis
REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
```

Update health check:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if mt5_manager and mt5_manager.is_connected() else "unhealthy",
        "mt5_connected": mt5_manager.is_connected() if mt5_manager else False,
        "redis_connected": await redis_client.is_connected() if redis_client else False,
        "connected_clients": len(session_manager.sessions) if session_manager else 0,
    }
```

---

## Todo List

- [ ] Create `backend/app/database/__init__.py`
- [ ] Create `backend/app/database/redis_client.py`
- [ ] Create `backend/app/advisor/__init__.py`
- [ ] Create `backend/app/advisor/data_fetcher.py`
- [ ] Create `backend/app/advisor/technical_analyzer.py`
- [ ] Create `backend/app/models/advisor_models.py`
- [ ] Create `backend/app/events/advisor_events.py`
- [ ] Create `backend/app/processors/advisor_processor.py`
- [ ] Modify `backend/app/config.py` - add Redis config
- [ ] Modify `backend/app/main.py` - add advisor initialization
- [ ] Update `backend/requirements.txt` - add pandas-ta, redis
- [ ] Write unit tests for technical_analyzer
- [ ] Test Socket.IO events manually

---

## Success Criteria

- [ ] `advisor:technical_summary` event returns valid indicators
- [ ] Redis caching reduces response time from ~500ms to <50ms
- [ ] All 10 indicators calculate correctly
- [ ] Multi-timeframe analysis identifies power zones
- [ ] Health check shows Redis status

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| pandas-ta installation issues | Medium | Fallback to ta library |
| MT5 data gaps | Medium | Return partial data with warning |
| Redis connection failure | Low | Continue without caching |
| Large computation time | Medium | Limit default candle count to 100 |

---

## Security Considerations

- Validate symbol input (alphanumeric only, max 20 chars)
- Rate limit advisor events (10 req/min/client)
- Sanitize all data before JSON serialization
- No sensitive data in Redis cache keys

---

## Next Steps

After Phase 1 completion:
1. Verify all indicators calculate correctly via manual testing
2. Measure cache hit rate and latency
3. Begin Phase 2: Pattern Recognition & S/R
