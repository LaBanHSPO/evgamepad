"""
Pattern detection for candlestick and chart patterns.
Uses pandas-ta for candlestick patterns, custom logic for chart patterns.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import pandas_ta_classic as ta
import numpy as np

from app.advisor.swing_utils import find_swing_points

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

        # Detect swing points first using shared utility
        swing_highs, swing_lows = find_swing_points(df)

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
