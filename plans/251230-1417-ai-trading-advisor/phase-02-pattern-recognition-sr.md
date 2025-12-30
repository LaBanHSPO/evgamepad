# Phase 2: Pattern Recognition & Support/Resistance

## Context Links
- Main Plan: `plan.md`
- Phase 1: `phase-01-technical-analysis-engine.md`
- Research: `research/researcher-01-technical-analysis.md`

---

## Overview

Implement candlestick pattern detection (60+ patterns via pandas-ta), chart pattern recognition (rule-based), and support/resistance level calculation (pivot points, Fibonacci, swing H/L). Expose via `advisor:pattern_scan` Socket.IO event.

**Effort:** 8 hours
**Priority:** P1 (required for meaningful trading advice)

---

## Key Insights from Research

1. **Candlestick patterns:** 60+ patterns detectable via pandas-ta/TA-Lib CDL functions
2. **Chart patterns:** Head & shoulders, flags, triangles, wedges - use rule-based detection initially
3. **Support/Resistance layers:** Static pivots, dynamic Fibonacci, volume profile nodes, swing structure
4. **Multi-timeframe:** S/R from higher TF more significant; patterns on lower TF for entry timing

---

## Requirements

### Functional
- FR1: Detect 20+ candlestick patterns (doji, hammer, engulfing, morning star, etc.)
- FR2: Identify basic chart patterns (double top/bottom, H&S, triangles)
- FR3: Calculate support/resistance levels via pivot points
- FR4: Calculate Fibonacci retracement levels from recent swings
- FR5: Detect swing high/low structure points
- FR6: Cache pattern results in Redis (5min TTL)
- FR7: Emit via `advisor:pattern_scan` event

### Non-Functional
- NFR1: Pattern scan < 800ms (fresh), < 50ms (cached)
- NFR2: Minimize false positives (require confirmation candle)
- NFR3: Return confidence score for each pattern

---

## Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    advisor_events.py                           │
│               @sio.event('advisor:pattern_scan')               │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                   advisor_processor.py                         │
│              AdvisorProcessor.process_pattern_scan()           │
└──────────────────────────┬─────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│ pattern_        │ │ support_        │ │ data_fetcher.py     │
│ detector.py     │ │ resistance.py   │ │ (from Phase 1)      │
│                 │ │                 │ │                     │
│ - candlestick   │ │ - pivot_points  │ │ - fetch_ohlcv()     │
│ - chart_patterns│ │ - fibonacci     │ │                     │
│ - trend_lines   │ │ - swing_hl      │ │                     │
└────────┬────────┘ └────────┬────────┘ └─────────────────────┘
         │                   │
         ▼                   ▼
   ┌─────────────┐    ┌─────────────┐
   │ pandas-ta   │    │ numpy/scipy │
   │ CDL funcs   │    │ for S/R     │
   └─────────────┘    └─────────────┘
```

---

## Related Code Files

### From Phase 1 (USE)
- `backend/app/advisor/data_fetcher.py`
- `backend/app/database/redis_client.py`
- `backend/app/processors/advisor_processor.py`
- `backend/app/events/advisor_events.py`

### New (CREATE)
- `backend/app/advisor/pattern_detector.py`
- `backend/app/advisor/support_resistance.py`
- `backend/app/models/advisor_models.py` (extend)

---

## Implementation Steps

### Step 1: Pattern Detector (3h)

**File:** `backend/app/advisor/pattern_detector.py`

```python
"""
Pattern detection for candlestick and chart patterns.
Uses pandas-ta for candlestick patterns, custom logic for chart patterns.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import pandas_ta as ta
import numpy as np

logger = logging.getLogger(__name__)

# Candlestick pattern mapping (pandas-ta CDL function names)
CANDLESTICK_PATTERNS = {
    # Reversal patterns (bullish)
    "hammer": "cdl_hammer",
    "inverted_hammer": "cdl_invertedhammer",
    "morning_star": "cdl_morningstar",
    "bullish_engulfing": "cdl_engulfing",  # value > 0
    "piercing": "cdl_piercing",
    "three_white_soldiers": "cdl_3whitesoldiers",
    "dragonfly_doji": "cdl_dragonflydoji",

    # Reversal patterns (bearish)
    "shooting_star": "cdl_shootingstar",
    "hanging_man": "cdl_hangingman",
    "evening_star": "cdl_eveningstar",
    "bearish_engulfing": "cdl_engulfing",  # value < 0
    "dark_cloud_cover": "cdl_darkcloudcover",
    "three_black_crows": "cdl_3blackcrows",
    "gravestone_doji": "cdl_gravestonedoji",

    # Continuation patterns
    "doji": "cdl_doji",
    "spinning_top": "cdl_spinningtop",
    "marubozu": "cdl_marubozu",

    # Complex patterns
    "harami": "cdl_harami",
    "harami_cross": "cdl_haramicross",
    "tweezer_top": None,  # Custom implementation
    "tweezer_bottom": None,  # Custom implementation
}

class PatternDetector:
    """Detects candlestick and chart patterns in OHLCV data."""

    def __init__(self, lookback: int = 5):
        """
        Args:
            lookback: Number of candles to scan for patterns (default 5)
        """
        self.lookback = lookback

    def detect_candlestick_patterns(
        self,
        df: pd.DataFrame,
        patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect candlestick patterns in OHLCV data.

        Args:
            df: OHLCV DataFrame
            patterns: List of patterns to scan. If None, scan all.

        Returns:
            Dict with detected patterns and their locations
        """
        if df is None or len(df) < 10:
            return {"error": "Insufficient data for pattern detection"}

        results = {
            "detected": [],
            "bullish_patterns": [],
            "bearish_patterns": [],
            "neutral_patterns": [],
        }

        patterns_to_scan = patterns or list(CANDLESTICK_PATTERNS.keys())

        for pattern_name in patterns_to_scan:
            try:
                detected = self._detect_single_pattern(df, pattern_name)
                if detected:
                    results["detected"].append(detected)

                    # Categorize
                    if detected["bias"] == "bullish":
                        results["bullish_patterns"].append(detected["name"])
                    elif detected["bias"] == "bearish":
                        results["bearish_patterns"].append(detected["name"])
                    else:
                        results["neutral_patterns"].append(detected["name"])

            except Exception as e:
                logger.warning(f"Pattern detection failed for {pattern_name}: {e}")

        results["pattern_count"] = len(results["detected"])
        results["overall_bias"] = self._calculate_bias(results)

        return results

    def _detect_single_pattern(
        self,
        df: pd.DataFrame,
        pattern_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect a single candlestick pattern.
        Returns info if found in last N candles.
        """
        # Get pandas-ta function name
        func_name = CANDLESTICK_PATTERNS.get(pattern_name)
        if func_name is None:
            # Custom pattern - skip for now
            return None

        # Get the CDL function
        cdl_func = getattr(ta, func_name, None)
        if cdl_func is None:
            return None

        # Calculate pattern
        try:
            result = cdl_func(df['open'], df['high'], df['low'], df['close'])
        except Exception:
            return None

        if result is None:
            return None

        # Check last N candles for pattern
        recent = result.iloc[-self.lookback:]
        for i, val in enumerate(recent):
            if val != 0 and not pd.isna(val):
                idx = len(df) - self.lookback + i
                candle_time = df['time'].iloc[idx]

                # Determine bias
                if val > 0:
                    bias = "bullish"
                elif val < 0:
                    bias = "bearish"
                else:
                    bias = "neutral"

                return {
                    "name": pattern_name,
                    "bias": bias,
                    "strength": abs(int(val)),  # 100 or 200 typically
                    "candle_index": idx,
                    "candle_time": candle_time.isoformat() if hasattr(candle_time, 'isoformat') else str(candle_time),
                    "price": float(df['close'].iloc[idx]),
                }

        return None

    def _calculate_bias(self, results: Dict[str, Any]) -> str:
        """Calculate overall pattern bias."""
        bullish = len(results["bullish_patterns"])
        bearish = len(results["bearish_patterns"])

        if bullish > bearish:
            return "bullish"
        elif bearish > bullish:
            return "bearish"
        else:
            return "neutral"

    def detect_chart_patterns(
        self,
        df: pd.DataFrame,
        min_pattern_bars: int = 10
    ) -> Dict[str, Any]:
        """
        Detect chart patterns (double top/bottom, head & shoulders, etc.)
        Uses rule-based detection with swing point analysis.

        Args:
            df: OHLCV DataFrame
            min_pattern_bars: Minimum bars for valid pattern

        Returns:
            Dict with detected chart patterns
        """
        if df is None or len(df) < 50:
            return {"patterns": [], "error": "Need 50+ candles for chart patterns"}

        results = {"patterns": []}

        # Detect swing points first
        swing_highs, swing_lows = self._find_swing_points(df)

        # Double Top detection
        double_top = self._detect_double_top(df, swing_highs)
        if double_top:
            results["patterns"].append(double_top)

        # Double Bottom detection
        double_bottom = self._detect_double_bottom(df, swing_lows)
        if double_bottom:
            results["patterns"].append(double_bottom)

        # Head and Shoulders (simplified)
        hs = self._detect_head_shoulders(df, swing_highs, swing_lows)
        if hs:
            results["patterns"].append(hs)

        return results

    def _find_swing_points(
        self,
        df: pd.DataFrame,
        window: int = 5
    ) -> Tuple[List[int], List[int]]:
        """
        Find swing high and low points.

        Returns:
            Tuple of (swing_high_indices, swing_low_indices)
        """
        highs = []
        lows = []

        for i in range(window, len(df) - window):
            # Check if this is a swing high
            is_swing_high = all(
                df['high'].iloc[i] >= df['high'].iloc[i-j] and
                df['high'].iloc[i] >= df['high'].iloc[i+j]
                for j in range(1, window + 1)
            )
            if is_swing_high:
                highs.append(i)

            # Check if this is a swing low
            is_swing_low = all(
                df['low'].iloc[i] <= df['low'].iloc[i-j] and
                df['low'].iloc[i] <= df['low'].iloc[i+j]
                for j in range(1, window + 1)
            )
            if is_swing_low:
                lows.append(i)

        return highs, lows

    def _detect_double_top(
        self,
        df: pd.DataFrame,
        swing_highs: List[int],
        tolerance: float = 0.02
    ) -> Optional[Dict[str, Any]]:
        """
        Detect double top pattern.
        Two similar highs with a valley between.
        """
        if len(swing_highs) < 2:
            return None

        # Check last two swing highs
        recent_highs = swing_highs[-2:]
        h1_idx, h2_idx = recent_highs

        h1_price = df['high'].iloc[h1_idx]
        h2_price = df['high'].iloc[h2_idx]

        # Highs should be within tolerance
        if abs(h1_price - h2_price) / h1_price > tolerance:
            return None

        # Find valley between
        valley_slice = df['low'].iloc[h1_idx:h2_idx+1]
        valley_price = valley_slice.min()
        valley_idx = valley_slice.idxmin()

        # Pattern should have reasonable proportions
        pattern_height = (h1_price + h2_price) / 2 - valley_price
        if pattern_height / h1_price < 0.01:  # At least 1% height
            return None

        return {
            "type": "double_top",
            "bias": "bearish",
            "confidence": 0.7,
            "neckline": float(valley_price),
            "target": float(valley_price - pattern_height),
            "stop_loss": float(max(h1_price, h2_price) * 1.005),
            "formation": {
                "first_top": {"index": h1_idx, "price": float(h1_price)},
                "second_top": {"index": h2_idx, "price": float(h2_price)},
                "valley": {"index": int(valley_idx), "price": float(valley_price)},
            }
        }

    def _detect_double_bottom(
        self,
        df: pd.DataFrame,
        swing_lows: List[int],
        tolerance: float = 0.02
    ) -> Optional[Dict[str, Any]]:
        """
        Detect double bottom pattern.
        Two similar lows with a peak between.
        """
        if len(swing_lows) < 2:
            return None

        recent_lows = swing_lows[-2:]
        l1_idx, l2_idx = recent_lows

        l1_price = df['low'].iloc[l1_idx]
        l2_price = df['low'].iloc[l2_idx]

        if abs(l1_price - l2_price) / l1_price > tolerance:
            return None

        # Find peak between
        peak_slice = df['high'].iloc[l1_idx:l2_idx+1]
        peak_price = peak_slice.max()
        peak_idx = peak_slice.idxmax()

        pattern_height = peak_price - (l1_price + l2_price) / 2
        if pattern_height / l1_price < 0.01:
            return None

        return {
            "type": "double_bottom",
            "bias": "bullish",
            "confidence": 0.7,
            "neckline": float(peak_price),
            "target": float(peak_price + pattern_height),
            "stop_loss": float(min(l1_price, l2_price) * 0.995),
            "formation": {
                "first_bottom": {"index": l1_idx, "price": float(l1_price)},
                "second_bottom": {"index": l2_idx, "price": float(l2_price)},
                "peak": {"index": int(peak_idx), "price": float(peak_price)},
            }
        }

    def _detect_head_shoulders(
        self,
        df: pd.DataFrame,
        swing_highs: List[int],
        swing_lows: List[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect head and shoulders pattern (simplified).
        Requires: Left shoulder < Head > Right shoulder, with similar shoulder heights.
        """
        if len(swing_highs) < 3:
            return None

        # Need at least 3 swing highs
        recent = swing_highs[-3:]
        ls_idx, head_idx, rs_idx = recent

        ls_price = df['high'].iloc[ls_idx]
        head_price = df['high'].iloc[head_idx]
        rs_price = df['high'].iloc[rs_idx]

        # Head must be higher than both shoulders
        if not (head_price > ls_price and head_price > rs_price):
            return None

        # Shoulders should be similar (within 5%)
        if abs(ls_price - rs_price) / ls_price > 0.05:
            return None

        # Find neckline (lows between shoulders and head)
        left_neck = df['low'].iloc[ls_idx:head_idx+1].min()
        right_neck = df['low'].iloc[head_idx:rs_idx+1].min()
        neckline = (left_neck + right_neck) / 2

        pattern_height = head_price - neckline

        return {
            "type": "head_and_shoulders",
            "bias": "bearish",
            "confidence": 0.65,
            "neckline": float(neckline),
            "target": float(neckline - pattern_height),
            "stop_loss": float(head_price * 1.005),
            "formation": {
                "left_shoulder": {"index": ls_idx, "price": float(ls_price)},
                "head": {"index": head_idx, "price": float(head_price)},
                "right_shoulder": {"index": rs_idx, "price": float(rs_price)},
            }
        }
```

### Step 2: Support/Resistance Calculator (2.5h)

**File:** `backend/app/advisor/support_resistance.py`

```python
"""
Support and Resistance level calculation.
Includes pivot points, Fibonacci retracements, and swing structure.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class SupportResistanceCalculator:
    """Calculates support and resistance levels from OHLCV data."""

    def __init__(self):
        pass

    def calculate_all(
        self,
        df: pd.DataFrame,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate all S/R levels.

        Args:
            df: OHLCV DataFrame
            current_price: Current price (uses last close if not provided)

        Returns:
            Dict with all S/R levels
        """
        if df is None or len(df) < 20:
            return {"error": "Need 20+ candles for S/R calculation"}

        if current_price is None:
            current_price = float(df['close'].iloc[-1])

        results = {
            "current_price": current_price,
            "pivot_points": self.calculate_pivot_points(df),
            "fibonacci": self.calculate_fibonacci_levels(df),
            "swing_levels": self.calculate_swing_levels(df),
            "support_levels": [],
            "resistance_levels": [],
        }

        # Aggregate all levels
        all_levels = self._aggregate_levels(results, current_price)
        results["support_levels"] = all_levels["support"]
        results["resistance_levels"] = all_levels["resistance"]

        # Find nearest S/R
        results["nearest_support"] = all_levels["support"][0] if all_levels["support"] else None
        results["nearest_resistance"] = all_levels["resistance"][0] if all_levels["resistance"] else None

        return results

    def calculate_pivot_points(
        self,
        df: pd.DataFrame,
        method: str = "standard"
    ) -> Dict[str, float]:
        """
        Calculate pivot points from previous period.

        Methods: standard, fibonacci, camarilla, woodie

        Returns:
            Dict with P, S1-S3, R1-R3
        """
        # Use previous day/period data
        prev_high = float(df['high'].iloc[-2])
        prev_low = float(df['low'].iloc[-2])
        prev_close = float(df['close'].iloc[-2])

        if method == "standard":
            pp = (prev_high + prev_low + prev_close) / 3
            r1 = 2 * pp - prev_low
            s1 = 2 * pp - prev_high
            r2 = pp + (prev_high - prev_low)
            s2 = pp - (prev_high - prev_low)
            r3 = prev_high + 2 * (pp - prev_low)
            s3 = prev_low - 2 * (prev_high - pp)

        elif method == "fibonacci":
            pp = (prev_high + prev_low + prev_close) / 3
            diff = prev_high - prev_low
            r1 = pp + 0.382 * diff
            s1 = pp - 0.382 * diff
            r2 = pp + 0.618 * diff
            s2 = pp - 0.618 * diff
            r3 = pp + diff
            s3 = pp - diff

        elif method == "camarilla":
            pp = (prev_high + prev_low + prev_close) / 3
            diff = prev_high - prev_low
            r1 = prev_close + diff * 1.1 / 12
            s1 = prev_close - diff * 1.1 / 12
            r2 = prev_close + diff * 1.1 / 6
            s2 = prev_close - diff * 1.1 / 6
            r3 = prev_close + diff * 1.1 / 4
            s3 = prev_close - diff * 1.1 / 4

        else:  # woodie
            pp = (prev_high + prev_low + 2 * prev_close) / 4
            r1 = 2 * pp - prev_low
            s1 = 2 * pp - prev_high
            r2 = pp + prev_high - prev_low
            s2 = pp - prev_high + prev_low
            r3 = r1 + prev_high - prev_low
            s3 = s1 - prev_high + prev_low

        return {
            "pivot": round(pp, 5),
            "r1": round(r1, 5),
            "r2": round(r2, 5),
            "r3": round(r3, 5),
            "s1": round(s1, 5),
            "s2": round(s2, 5),
            "s3": round(s3, 5),
            "method": method,
        }

    def calculate_fibonacci_levels(
        self,
        df: pd.DataFrame,
        lookback: int = 50
    ) -> Dict[str, Any]:
        """
        Calculate Fibonacci retracement levels from recent swing.

        Uses highest high and lowest low in lookback period.

        Returns:
            Dict with Fibonacci levels and trend direction
        """
        recent = df.iloc[-lookback:]

        swing_high = float(recent['high'].max())
        swing_low = float(recent['low'].min())
        swing_high_idx = recent['high'].idxmax()
        swing_low_idx = recent['low'].idxmin()

        # Determine trend direction
        if swing_high_idx > swing_low_idx:
            trend = "uptrend"
            # In uptrend, Fib levels are measured from low to high
            diff = swing_high - swing_low
            levels = {
                "0.0": swing_low,
                "0.236": swing_low + 0.236 * diff,
                "0.382": swing_low + 0.382 * diff,
                "0.5": swing_low + 0.5 * diff,
                "0.618": swing_low + 0.618 * diff,
                "0.786": swing_low + 0.786 * diff,
                "1.0": swing_high,
            }
        else:
            trend = "downtrend"
            # In downtrend, Fib levels are measured from high to low
            diff = swing_high - swing_low
            levels = {
                "0.0": swing_high,
                "0.236": swing_high - 0.236 * diff,
                "0.382": swing_high - 0.382 * diff,
                "0.5": swing_high - 0.5 * diff,
                "0.618": swing_high - 0.618 * diff,
                "0.786": swing_high - 0.786 * diff,
                "1.0": swing_low,
            }

        return {
            "trend": trend,
            "swing_high": round(swing_high, 5),
            "swing_low": round(swing_low, 5),
            "levels": {k: round(v, 5) for k, v in levels.items()},
        }

    def calculate_swing_levels(
        self,
        df: pd.DataFrame,
        window: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Calculate swing high/low levels (structure-based S/R).

        Returns:
            Dict with recent swing highs and lows as S/R levels
        """
        swing_highs = []
        swing_lows = []

        for i in range(window, len(df) - window):
            # Swing high
            if all(df['high'].iloc[i] >= df['high'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['high'].iloc[i] >= df['high'].iloc[i+j] for j in range(1, window+1)):
                swing_highs.append({
                    "price": round(float(df['high'].iloc[i]), 5),
                    "time": df['time'].iloc[i].isoformat() if hasattr(df['time'].iloc[i], 'isoformat') else str(df['time'].iloc[i]),
                    "index": i,
                })

            # Swing low
            if all(df['low'].iloc[i] <= df['low'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['low'].iloc[i] <= df['low'].iloc[i+j] for j in range(1, window+1)):
                swing_lows.append({
                    "price": round(float(df['low'].iloc[i]), 5),
                    "time": df['time'].iloc[i].isoformat() if hasattr(df['time'].iloc[i], 'isoformat') else str(df['time'].iloc[i]),
                    "index": i,
                })

        # Return most recent 5
        return {
            "swing_highs": swing_highs[-5:],
            "swing_lows": swing_lows[-5:],
        }

    def _aggregate_levels(
        self,
        results: Dict[str, Any],
        current_price: float
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate all levels and sort by distance from current price.
        """
        support = []
        resistance = []

        # Add pivot point levels
        pivots = results.get("pivot_points", {})
        for key in ["s1", "s2", "s3"]:
            if pivots.get(key):
                level = {"price": pivots[key], "source": "pivot", "type": key}
                if pivots[key] < current_price:
                    support.append(level)
                else:
                    resistance.append(level)

        for key in ["r1", "r2", "r3"]:
            if pivots.get(key):
                level = {"price": pivots[key], "source": "pivot", "type": key}
                if pivots[key] > current_price:
                    resistance.append(level)
                else:
                    support.append(level)

        # Add Fibonacci levels
        fib = results.get("fibonacci", {})
        fib_levels = fib.get("levels", {})
        for key, price in fib_levels.items():
            level = {"price": price, "source": "fibonacci", "type": key}
            if price < current_price:
                support.append(level)
            else:
                resistance.append(level)

        # Add swing levels
        swing = results.get("swing_levels", {})
        for sh in swing.get("swing_highs", []):
            level = {"price": sh["price"], "source": "swing", "type": "swing_high"}
            if sh["price"] > current_price:
                resistance.append(level)
            else:
                support.append(level)

        for sl in swing.get("swing_lows", []):
            level = {"price": sl["price"], "source": "swing", "type": "swing_low"}
            if sl["price"] < current_price:
                support.append(level)
            else:
                resistance.append(level)

        # Sort by distance from current price
        support.sort(key=lambda x: current_price - x["price"])
        resistance.sort(key=lambda x: x["price"] - current_price)

        # Remove duplicates (within 0.1% tolerance)
        support = self._dedupe_levels(support)
        resistance = self._dedupe_levels(resistance)

        return {"support": support[:5], "resistance": resistance[:5]}

    def _dedupe_levels(
        self,
        levels: List[Dict[str, Any]],
        tolerance: float = 0.001
    ) -> List[Dict[str, Any]]:
        """Remove duplicate levels within tolerance."""
        if not levels:
            return levels

        deduped = [levels[0]]
        for level in levels[1:]:
            is_duplicate = any(
                abs(level["price"] - existing["price"]) / existing["price"] < tolerance
                for existing in deduped
            )
            if not is_duplicate:
                deduped.append(level)

        return deduped
```

### Step 3: Extend Advisor Events (1h)

**Modify:** `backend/app/events/advisor_events.py`

Add new event handler:

```python
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

        if not symbol:
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                "Symbol is required"
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
```

### Step 4: Extend Advisor Processor (1h)

**Modify:** `backend/app/processors/advisor_processor.py`

Add to imports:
```python
from app.advisor.pattern_detector import PatternDetector
from app.advisor.support_resistance import SupportResistanceCalculator
```

Add to __init__:
```python
self.pattern_detector = PatternDetector()
self.sr_calculator = SupportResistanceCalculator()
```

Add new method:
```python
async def process_pattern_scan(
    self,
    sid: str,
    symbol: str,
    timeframe: str,
    include_sr: bool = True
) -> Dict[str, Any]:
    """
    Process pattern scan request.
    """
    logger.info(f"[{sid}] Processing pattern scan: {symbol} {timeframe}")

    # Check cache
    cache_key = f"patterns:{symbol}:{timeframe}"
    if self.redis_client:
        cached = await self.redis_client._client.get(cache_key)
        if cached:
            import json
            data = json.loads(cached)
            data['cached'] = True
            return success_response(data)

    # Fetch OHLCV data (need more candles for patterns)
    df = await self.data_fetcher.fetch_ohlcv(symbol, timeframe, count=200)
    if df is None:
        return error_response(
            ErrorCode.MT5_ERROR,
            f"Failed to fetch data for {symbol} {timeframe}"
        )

    result = {
        "symbol": symbol,
        "timeframe": timeframe,
        "last_price": float(df['close'].iloc[-1]),
    }

    # Detect candlestick patterns
    candlestick = self.pattern_detector.detect_candlestick_patterns(df)
    result["candlestick_patterns"] = candlestick

    # Detect chart patterns
    chart_patterns = self.pattern_detector.detect_chart_patterns(df)
    result["chart_patterns"] = chart_patterns

    # Calculate S/R levels
    if include_sr:
        sr_levels = self.sr_calculator.calculate_all(df)
        result["support_resistance"] = sr_levels

    result["cached"] = False
    result["computed_at"] = datetime.utcnow().isoformat()

    # Cache result
    if self.redis_client:
        import json
        await self.redis_client._client.setex(
            cache_key,
            300,  # 5 min TTL
            json.dumps(result, default=str)
        )

    return success_response(result)
```

### Step 5: Update Models (0.5h)

**Modify:** `backend/app/models/advisor_models.py`

Add new models:

```python
class CandlestickPattern(BaseModel):
    """Single candlestick pattern detection."""
    name: str
    bias: str  # bullish, bearish, neutral
    strength: int
    candle_index: int
    candle_time: str
    price: float

class ChartPattern(BaseModel):
    """Chart pattern (double top, H&S, etc.)."""
    type: str
    bias: str
    confidence: float
    neckline: float
    target: float
    stop_loss: float
    formation: Dict[str, Any]

class SupportResistanceLevel(BaseModel):
    """Single S/R level."""
    price: float
    source: str  # pivot, fibonacci, swing
    type: str    # s1, r1, 0.618, swing_high, etc.

class PatternScanResponse(BaseModel):
    """Response for advisor:pattern_scan event."""
    success: bool = True
    symbol: str
    timeframe: str
    last_price: float
    candlestick_patterns: Dict[str, Any]
    chart_patterns: Dict[str, Any]
    support_resistance: Optional[Dict[str, Any]] = None
    cached: bool = False
    computed_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## Todo List

- [ ] Create `backend/app/advisor/pattern_detector.py`
- [ ] Create `backend/app/advisor/support_resistance.py`
- [ ] Extend `backend/app/events/advisor_events.py` - add pattern_scan
- [ ] Extend `backend/app/processors/advisor_processor.py` - add pattern methods
- [ ] Extend `backend/app/models/advisor_models.py` - add pattern models
- [ ] Write unit tests for pattern_detector
- [ ] Write unit tests for support_resistance
- [ ] Test Socket.IO events manually
- [ ] Verify caching works for pattern results

---

## Success Criteria

- [ ] Detect 15+ candlestick patterns correctly
- [ ] Double top/bottom detection accuracy > 70%
- [ ] Pivot points calculate correctly (verify vs TradingView)
- [ ] Fibonacci levels calculate correctly
- [ ] S/R levels sorted by proximity to current price
- [ ] Cache reduces response time for pattern scan

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| pandas-ta CDL functions differ from TA-Lib | Low | Cross-check with known patterns |
| Chart pattern false positives | Medium | Add confirmation requirements |
| S/R level clustering | Low | Deduplication with tolerance |
| Insufficient data for patterns | Medium | Require minimum 200 candles |

---

## Security Considerations

- Validate timeframe input (whitelist allowed values)
- Limit pattern lookback period (prevent DoS)
- Sanitize all float values before JSON response

---

## Next Steps

After Phase 2 completion:
1. Verify pattern detection against known historical data
2. Compare S/R levels with TradingView for validation
3. Begin Phase 3: Risk Analyzer & Position Sizing
