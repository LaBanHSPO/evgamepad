"""
Support and Resistance level calculation.
Includes pivot points, Fibonacci retracements, and swing structure.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from app.advisor.swing_utils import find_swing_points, format_swing_levels

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
        # CRITICAL: Validate minimum data requirements
        if df is None or len(df) < 2:
            logger.error(f"Pivot calculation requires at least 2 candles, got {len(df) if df is not None else 0}")
            return {
                "pivot": 0.0,
                "r1": 0.0, "r2": 0.0, "r3": 0.0,
                "s1": 0.0, "s2": 0.0, "s3": 0.0,
                "method": method,
                "error": "Insufficient data"
            }

        # Validate method parameter
        valid_methods = ["standard", "fibonacci", "camarilla", "woodie"]
        if method not in valid_methods:
            logger.warning(f"Invalid pivot method '{method}', using 'standard'")
            method = "standard"

        # Use previous day/period data
        prev_high = float(df['high'].iloc[-2])
        prev_low = float(df['low'].iloc[-2])
        prev_close = float(df['close'].iloc[-2])

        # CRITICAL: Prevent division by zero
        if abs(prev_high - prev_low) < 1e-10:
            logger.warning(f"Zero range detected (H={prev_high}, L={prev_low}), using simple pivot")
            pp = prev_close
            return {
                "pivot": round(pp, 5),
                "r1": round(pp, 5), "r2": round(pp, 5), "r3": round(pp, 5),
                "s1": round(pp, 5), "s2": round(pp, 5), "s3": round(pp, 5),
                "method": method,
                "note": "Zero range - all levels at pivot"
            }

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
        # Use shared swing detection utility
        swing_highs, swing_lows = find_swing_points(df, window)
        return format_swing_levels(df, swing_highs, swing_lows, recent_count=5)

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
