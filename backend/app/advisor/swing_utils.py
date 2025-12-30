"""
Shared utility functions for swing point detection.
Used by pattern_detector and support_resistance modules.
"""
import logging
from typing import Tuple, List, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)

def find_swing_points(
    df: pd.DataFrame,
    window: int = 5
) -> Tuple[List[int], List[int]]:
    """
    Find swing high and low points in OHLCV data.

    Args:
        df: OHLCV DataFrame with 'high' and 'low' columns
        window: Number of candles on each side to compare

    Returns:
        Tuple of (swing_high_indices, swing_low_indices)
    """
    if df is None or len(df) < (2 * window + 1):
        logger.warning(f"Insufficient data for swing detection (need {2 * window + 1}+ candles)")
        return [], []

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

def format_swing_levels(
    df: pd.DataFrame,
    swing_highs: List[int],
    swing_lows: List[int],
    recent_count: int = 5
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Format swing points as S/R levels with metadata.

    Args:
        df: OHLCV DataFrame
        swing_highs: List of swing high indices
        swing_lows: List of swing low indices
        recent_count: Number of recent swings to return

    Returns:
        Dict with formatted swing_highs and swing_lows
    """
    if df is None:
        return {"swing_highs": [], "swing_lows": []}

    formatted_highs = []
    for idx in swing_highs[-recent_count:]:
        try:
            formatted_highs.append({
                "price": round(float(df['high'].iloc[idx]), 5),
                "time": df['time'].iloc[idx].isoformat() if hasattr(df['time'].iloc[idx], 'isoformat') else str(df['time'].iloc[idx]),
                "index": idx,
            })
        except (IndexError, KeyError) as e:
            logger.warning(f"Error formatting swing high at index {idx}: {e}")
            continue

    formatted_lows = []
    for idx in swing_lows[-recent_count:]:
        try:
            formatted_lows.append({
                "price": round(float(df['low'].iloc[idx]), 5),
                "time": df['time'].iloc[idx].isoformat() if hasattr(df['time'].iloc[idx], 'isoformat') else str(df['time'].iloc[idx]),
                "index": idx,
            })
        except (IndexError, KeyError) as e:
            logger.warning(f"Error formatting swing low at index {idx}: {e}")
            continue

    return {
        "swing_highs": formatted_highs,
        "swing_lows": formatted_lows,
    }
