This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
backend/
  app/
    advisor/
      __init__.py
      data_fetcher.py
      pattern_detector.py
      support_resistance.py
      technical_analyzer.py
    database/
      __init__.py
      redis_client.py
    events/
      __init__.py
      advisor_events.py
      trading_events.py
    models/
      __init__.py
      advisor_models.py
      responses.py
    mt5/
      __init__.py
      circuit_breaker.py
      connection_manager.py
      error_handler.py
      trading_operations.py
    processors/
      __init__.py
      advisor_processor.py
      command_processor.py
    tasks/
      __init__.py
      cleanup_task.py
    __init__.py
    config.py
    logging_config.py
    main.py
    README.md
    reconnection_manager.py
    session_manager.py
    sio.py
    validation.py
  tests/
    __init__.py
    conftest.py
    test_circuit_breaker.py
    test_command_processor.py
    test_connection_manager.py
    test_events.py
    test_reconnection.py
    test_technical_analyzer.py
    test_trading_operations.py
  .env.example
  .gitignore
  README.md
  requirements.txt
guide/
  COMMANDS.md
  COMMANDS.yaml
  ENVIRONMENT_RESOLVER.md
  SKILLS.md
  SKILLS.yaml
public/
  favicon.ico
  placeholder.svg
  robots.txt
scripts/
  prepare-release-assets.cjs
  send-discord-release.cjs
src/
  components/
    ui/
      accordion.tsx
      alert-dialog.tsx
      alert.tsx
      aspect-ratio.tsx
      avatar.tsx
      badge.tsx
      breadcrumb.tsx
      button.tsx
      calendar.tsx
      card.tsx
      carousel.tsx
      chart.tsx
      checkbox.tsx
      collapsible.tsx
      command.tsx
      context-menu.tsx
      dialog.tsx
      drawer.tsx
      dropdown-menu.tsx
      form.tsx
      hover-card.tsx
      input-otp.tsx
      input.tsx
      label.tsx
      menubar.tsx
      navigation-menu.tsx
      pagination.tsx
      popover.tsx
      progress.tsx
      radio-group.tsx
      resizable.tsx
      scroll-area.tsx
      select.tsx
      separator.tsx
      sheet.tsx
      sidebar.tsx
      skeleton.tsx
      slider.tsx
      sonner.tsx
      switch.tsx
      table.tsx
      tabs.tsx
      textarea.tsx
      toast.tsx
      toaster.tsx
      toggle-group.tsx
      toggle.tsx
      tooltip.tsx
      use-toast.ts
    ActiveOrdersPanel.tsx
    AIAnalysisPanel.tsx
    CapitalCompanionPanel.tsx
    GamepadControllerHints.tsx
    GamepadPositions.tsx
    GamepadQuickTrade.tsx
    GlobalGamepadHandler.tsx
    KOLUpdatesPanel.tsx
    MajorNewsPanel.tsx
    MarketOverviewPanel.tsx
    MarketSentimentPanel.tsx
    MissionLogPanel.tsx
    MonitorNav.tsx
    NavLink.tsx
    OrderEntryPanel.tsx
    PositionManagerPanel.tsx
    PriceActionPanel.tsx
    RiskManagementPanel.tsx
    SystemHeader.tsx
  context/
    SocketContext.tsx
  hooks/
    use-mobile.tsx
    use-toast.ts
    useGamepad.ts
  lib/
    utils.ts
  pages/
    Action.tsx
    NotFound.tsx
    Plan.tsx
    Portfolio.tsx
  App.css
  App.tsx
  index.css
  main.tsx
  vite-env.d.ts
.gitignore
.repomixignore
CLAUDE.md
components.json
eslint.config.js
index.html
package.json
postcss.config.js
README.md
tailwind.config.ts
tsconfig.app.json
tsconfig.json
tsconfig.node.json
vite.config.ts
```

# Files

## File: backend/app/advisor/__init__.py
````python
"""AI Trading Advisor package."""
````

## File: backend/app/advisor/data_fetcher.py
````python
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
            try:
                import MetaTrader5 as mt5
            except ImportError:
                logger.error("MetaTrader5 not available on this platform")
                return None

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
````

## File: backend/app/advisor/pattern_detector.py
````python
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
````

## File: backend/app/advisor/support_resistance.py
````python
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
````

## File: backend/app/advisor/technical_analyzer.py
````python
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
````

## File: backend/app/database/__init__.py
````python
"""Database clients package."""
````

## File: backend/app/database/redis_client.py
````python
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
        ttl: int = 60  # 1 minute (adjusted from 5min)
    ) -> bool:
        """
        Cache indicators for symbol/timeframe.
        TTL in seconds (default 1 min per validation adjustment).
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
        except Exception:
            return False
````

## File: backend/app/events/advisor_events.py
````python
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

logger = logging.getLogger(__name__)

def validate_symbol(symbol: str) -> bool:
    """Validate symbol: alphanumeric + max 20 chars."""
    return bool(re.match(r'^[A-Z0-9]{1,20}$', symbol))

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
````

## File: backend/app/models/advisor_models.py
````python
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
````

## File: backend/app/processors/advisor_processor.py
````python
"""
Advisor command processor.
Routes Socket.IO events to technical analysis components.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.advisor.technical_analyzer import TechnicalAnalyzer
from app.advisor.data_fetcher import DataFetcher
from app.advisor.pattern_detector import PatternDetector
from app.advisor.support_resistance import SupportResistanceCalculator
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
        self.pattern_detector = PatternDetector()
        self.sr_calculator = SupportResistanceCalculator()
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
            await self.redis_client.set_indicators(symbol, timeframe, result, ttl=60)

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
````

## File: backend/tests/test_technical_analyzer.py
````python
"""
Unit tests for TechnicalAnalyzer.
Tests indicator calculations and signal generation.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
sys.path.insert(0, '../')

from app.advisor.technical_analyzer import TechnicalAnalyzer


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='H')

    # Generate realistic price data with trend
    base_price = 2000
    trend = np.linspace(0, 100, 100)
    noise = np.random.normal(0, 5, 100)
    close_prices = base_price + trend + noise

    # Generate OHLCV with realistic relationships
    data = {
        'time': dates,
        'open': close_prices * (1 + np.random.uniform(-0.002, 0.002, 100)),
        'high': close_prices * (1 + np.random.uniform(0, 0.005, 100)),
        'low': close_prices * (1 - np.random.uniform(0, 0.005, 100)),
        'close': close_prices,
        'volume': np.random.randint(1000, 5000, 100)
    }

    return pd.DataFrame(data)


class TestTechnicalAnalyzer:
    """Test suite for TechnicalAnalyzer."""

    def test_initialization(self):
        """Test analyzer initializes with default params."""
        analyzer = TechnicalAnalyzer()
        assert analyzer.params['rsi_period'] == 14
        assert analyzer.params['macd_fast'] == 12
        assert analyzer.params['macd_slow'] == 26

    def test_initialization_custom_params(self):
        """Test analyzer accepts custom parameters."""
        custom_params = {'rsi_period': 21, 'atr_period': 20}
        analyzer = TechnicalAnalyzer(params=custom_params)
        assert analyzer.params['rsi_period'] == 21
        assert analyzer.params['atr_period'] == 20
        assert analyzer.params['macd_fast'] == 12  # Default preserved

    def test_calculate_indicators_empty_data(self):
        """Test handling of empty DataFrame."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(None)
        assert 'error' in result

        empty_df = pd.DataFrame()
        result = analyzer.calculate_indicators(empty_df)
        assert 'error' in result

    def test_calculate_sma(self, sample_ohlcv_data):
        """Test SMA calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data, indicators=['sma'])

        assert 'sma_20' in result['indicators']
        assert 'sma_50' in result['indicators']
        assert 'sma_200' in result['indicators']
        assert result['indicators']['sma_20'] is not None
        assert isinstance(result['indicators']['sma_20'], float)

    def test_calculate_ema(self, sample_ohlcv_data):
        """Test EMA calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data, indicators=['ema'])

        assert 'ema_9' in result['indicators']
        assert 'ema_21' in result['indicators']
        assert 'ema_50' in result['indicators']
        assert result['indicators']['ema_21'] is not None

    def test_calculate_rsi(self, sample_ohlcv_data):
        """Test RSI calculation and signals."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data, indicators=['rsi'])

        assert 'rsi' in result['indicators']
        rsi_value = result['indicators']['rsi']
        assert rsi_value is not None
        assert 0 <= rsi_value <= 100

        # Check signal generation
        assert 'rsi' in result['signals']
        assert result['signals']['rsi'] in ['oversold', 'overbought', 'neutral']

    def test_calculate_macd(self, sample_ohlcv_data):
        """Test MACD calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data, indicators=['macd'])

        assert 'macd' in result['indicators']
        macd_data = result['indicators']['macd']
        assert 'macd' in macd_data
        assert 'signal' in macd_data
        assert 'histogram' in macd_data

        # Check signal
        if 'macd' in result['signals']:
            assert result['signals']['macd'] in [
                'bullish', 'bearish', 'bullish_crossover', 'bearish_crossover'
            ]

    def test_calculate_bollinger_bands(self, sample_ohlcv_data):
        """Test Bollinger Bands calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data, indicators=['bb'])

        assert 'bollinger' in result['indicators']
        bb_data = result['indicators']['bollinger']
        assert 'upper' in bb_data
        assert 'middle' in bb_data
        assert 'lower' in bb_data

        # Upper should be > middle > lower
        if all(v is not None for v in bb_data.values()):
            assert bb_data['upper'] > bb_data['middle'] > bb_data['lower']

    def test_calculate_atr(self, sample_ohlcv_data):
        """Test ATR calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data, indicators=['atr'])

        assert 'atr' in result['indicators']
        assert 'atr_pct' in result['indicators']
        assert result['indicators']['atr'] is not None
        assert result['indicators']['atr'] > 0
        assert result['indicators']['atr_pct'] > 0

    def test_calculate_adx(self, sample_ohlcv_data):
        """Test ADX calculation and trend signals."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data, indicators=['adx'])

        assert 'adx' in result['indicators']
        adx_data = result['indicators']['adx']
        assert 'adx' in adx_data
        assert 'plus_di' in adx_data
        assert 'minus_di' in adx_data

        # Check signal
        if 'adx' in result['signals']:
            assert result['signals']['adx'] in ['no_trend', 'moderate_trend', 'strong_trend']

    def test_calculate_all_indicators(self, sample_ohlcv_data):
        """Test calculating all indicators at once."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data)

        # Check metadata
        assert result['candles'] == 100
        assert 'last_close' in result
        assert 'last_time' in result
        assert 'indicators' in result
        assert 'signals' in result

        # Check indicators exist
        assert len(result['indicators']) > 0
        assert len(result['signals']) > 0

    def test_get_overall_signal_bullish(self, sample_ohlcv_data):
        """Test overall signal aggregation for bullish scenario."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data)
        overall = analyzer.get_overall_signal(result)

        assert 'signal' in overall
        assert 'confidence' in overall
        assert 'bullish_signals' in overall
        assert 'bearish_signals' in overall
        assert 'neutral_signals' in overall
        assert 'reasoning' in overall

        # Signal should be one of the valid values
        assert overall['signal'] in ['bullish', 'bearish', 'neutral']

        # Confidence should be between 0 and 1
        assert 0 <= overall['confidence'] <= 1

    def test_get_overall_signal_no_signals(self):
        """Test overall signal with no signals available."""
        analyzer = TechnicalAnalyzer()
        result = {'signals': {}}
        overall = analyzer.get_overall_signal(result)

        assert overall['signal'] == 'neutral'
        assert overall['confidence'] == 0
        assert overall['reasoning'] == "No signals available"

    def test_metadata_fields(self, sample_ohlcv_data):
        """Test that all metadata fields are populated."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data)

        assert result['candles'] == len(sample_ohlcv_data)
        assert isinstance(result['last_close'], float)
        assert result['last_close'] > 0
        assert result['last_time'] is not None

    def test_trend_signal_generation(self, sample_ohlcv_data):
        """Test trend signal based on EMA alignment."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_indicators(sample_ohlcv_data, indicators=['ema'])

        # If EMAs are calculated, trend should be determined
        if 'ema_21' in result['indicators'] and 'ema_50' in result['indicators']:
            if result['indicators']['ema_21'] and result['indicators']['ema_50']:
                assert 'trend' in result['signals']
                assert result['signals']['trend'] in ['bullish', 'bearish', 'mixed']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
````

## File: backend/app/mt5/circuit_breaker.py
````python
import logging
import time
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failed, rejecting requests
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    """
    Circuit breaker pattern for MT5 operations
    Prevents cascading failures from broken MT5 connection
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        recovery_timeout: float = 5.0
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Failures before opening circuit
            timeout: Seconds to wait before attempting recovery
            recovery_timeout: Timeout for recovery attempts
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout

        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker: recovered to CLOSED")

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        # If in HALF_OPEN state, any failure trips the breaker
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker: HALF_OPEN attempt failed -> OPEN"
            )
            return

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker: OPEN (failures: {self.failure_count})"
                )

    def can_execute(self) -> bool:
        """Check if operation can proceed"""

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout expired to attempt recovery
            if self.last_failure_time and time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.failure_count = 0
                logger.info("Circuit breaker: attempting HALF_OPEN recovery")
                return True
            return False

        # HALF_OPEN: allow single attempt
        return True

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            RuntimeError: If circuit is open
            Exception: From executed function
        """
        if not self.can_execute():
            raise RuntimeError(
                f"Circuit breaker is {self.state.value} - operation rejected"
            )

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def get_state(self) -> str:
        """Get current state string"""
        return self.state.value

    def reset(self):
        """Reset circuit breaker"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        logger.info("Circuit breaker reset")
````

## File: backend/app/tasks/cleanup_task.py
````python
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class CleanupTask:
    """Background task for periodic cleanup"""

    def __init__(self, reconnection_manager, interval: int = 60):
        """
        Initialize cleanup task

        Args:
            reconnection_manager: ReconnectionManager instance
            interval: Cleanup interval in seconds
        """
        self.reconnection_manager = reconnection_manager
        self.interval = interval
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def run(self):
        """Run cleanup loop"""
        self.running = True
        logger.info(f"Cleanup task started (interval: {self.interval}s)")

        while self.running:
            try:
                await asyncio.sleep(self.interval)

                # Cleanup expired sessions
                expired_count = self.reconnection_manager.cleanup_expired_sessions()
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions")

            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.exception("Error in cleanup task")

    def start(self):
        """Start cleanup task"""
        if not self.task:
            self.task = asyncio.create_task(self.run())
            logger.info("Cleanup task scheduled")

    async def stop(self):
        """Stop cleanup task"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            logger.info("Cleanup task stopped")
````

## File: backend/app/README.md
````markdown
- uv pip install -r requirements.txt
- uv run --python .venv311 python -m app.main
````

## File: backend/app/reconnection_manager.py
````python
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class ReconnectionManager:
    """
    Manage client reconnection and session recovery
    """

    def __init__(self, session_ttl: int = 300):
        """
        Initialize reconnection manager

        Args:
            session_ttl: Session time-to-live in seconds (default 5 minutes)
        """
        self.session_ttl = session_ttl
        self.disconnected_sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def store_disconnected_session(self, sid: str, session_data: Dict[str, Any]):
        """
        Store session data when client disconnects

        Args:
            sid: Session ID
            session_data: Session state to preserve
        """
        with self._lock:
            self.disconnected_sessions[sid] = {
                'data': session_data,
                'disconnected_at': datetime.utcnow(),
                'pending_orders': session_data.get('pending_orders', {}),
                'reconnection_count': 0,
            }
            logger.info(f"Session {sid} stored for recovery (TTL: {self.session_ttl}s)")

    def recover_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to recover session data

        Args:
            sid: Session ID

        Returns:
            Session data if found and not expired, None otherwise
        """
        with self._lock:
            if sid not in self.disconnected_sessions:
                logger.debug(f"No stored session for {sid}")
                return None

            stored = self.disconnected_sessions[sid]
            disconnected_at = stored['disconnected_at']

            # Check expiration
            if datetime.utcnow() - disconnected_at > timedelta(seconds=self.session_ttl):
                logger.warning(f"Session {sid} expired (TTL exceeded)")
                del self.disconnected_sessions[sid]
                return None

            # Recover session
            logger.info(f"Recovering session {sid}")
            stored['reconnection_count'] += 1
            return stored['data']

    def cleanup_expired_sessions(self):
        """Remove expired disconnected sessions"""
        with self._lock:
            now = datetime.utcnow()
            expired = []

            for sid, stored in self.disconnected_sessions.items():
                disconnected_at = stored['disconnected_at']
                if now - disconnected_at > timedelta(seconds=self.session_ttl):
                    expired.append(sid)

            for sid in expired:
                logger.info(f"Cleaning up expired session {sid}")
                del self.disconnected_sessions[sid]

            return len(expired)

    def get_pending_orders(self, sid: str) -> List[Dict[str, Any]]:
        """
        Get pending orders for session

        Args:
            sid: Session ID

        Returns:
            List of pending orders
        """
        with self._lock:
            if sid in self.disconnected_sessions:
                pending = self.disconnected_sessions[sid].get('pending_orders', {})
                return list(pending.values())
            return []

    def remove_session(self, sid: str):
        """Remove session from storage"""
        with self._lock:
            if sid in self.disconnected_sessions:
                del self.disconnected_sessions[sid]
                logger.debug(f"Removed stored session {sid}")
````

## File: backend/app/session_manager.py
````python
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class SessionManager:
    """Manage Socket.IO client sessions"""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def create_session(self, sid: str, initial_data: Dict[str, Any] = None):
        """Create new session for client"""
        with self._lock:
            self.sessions[sid] = initial_data or {}
            logger.debug(f"Session created: {sid}")

    def get_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        with self._lock:
            return self.sessions.get(sid)

    def update_session(self, sid: str, data: Dict[str, Any]):
        """Update session data"""
        with self._lock:
            if sid in self.sessions:
                self.sessions[sid].update(data)
                logger.debug(f"Session updated: {sid}")

    def remove_session(self, sid: str):
        """Remove session"""
        with self._lock:
            if sid in self.sessions:
                del self.sessions[sid]
                logger.debug(f"Session removed: {sid}")

    def add_pending_order(self, sid: str, order_id: str, order_data: Dict[str, Any]):
        """Track pending order for session"""
        with self._lock:
            session = self.sessions.get(sid)
            if session:
                if 'pending_orders' not in session:
                    session['pending_orders'] = {}
                session['pending_orders'][order_id] = {
                    'data': order_data,
                    'timestamp': datetime.utcnow(),
                }

    def remove_pending_order(self, sid: str, order_id: str):
        """Remove pending order"""
        with self._lock:
            session = self.sessions.get(sid)
            if session and 'pending_orders' in session:
                session['pending_orders'].pop(order_id, None)

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all sessions (for debugging)"""
        with self._lock:
            return self.sessions.copy()
````

## File: backend/app/sio.py
````python
import logging
from socketio import AsyncServer
from app.config import config

logger = logging.getLogger(__name__)

# Socket.IO Server Configuration
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # VPN network - adjust for production
    ping_interval=25,          # Heartbeat every 25s
    ping_timeout=60,           # Disconnect after 60s no response
    max_http_buffer_size=1000000,  # 1MB max message size (1e6)
    logger=logger,
    engineio_logger=logger if config.DEBUG else False,
)
````

## File: backend/app/validation.py
````python
from typing import Dict, Any, Tuple

def validate_login_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate login command payload"""
    required = ['account', 'password', 'server']

    # Check required fields
    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Type validation
    if not isinstance(data['account'], int):
        return False, "Account must be an integer"

    if not isinstance(data['password'], str) or not data['password']:
        return False, "Password must be a non-empty string"

    if not isinstance(data['server'], str) or not data['server']:
        return False, "Server must be a non-empty string"

    return True, ""

def validate_order_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate buy/sell order command"""
    required = ['symbol', 'volume']

    # Check required fields
    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Symbol validation
    if not isinstance(data['symbol'], str) or not data['symbol']:
        return False, "Symbol must be a non-empty string"

    # Volume validation
    try:
        volume = float(data['volume'])
        if volume <= 0:
            return False, "Volume must be positive"
        if volume > 100:  # Sanity check
            return False, "Volume exceeds maximum (100 lots)"
    except (ValueError, TypeError):
        return False, "Volume must be a number"

    # Optional: SL/TP validation
    if 'sl' in data:
        try:
            float(data['sl'])
        except (ValueError, TypeError):
            return False, "SL must be a number"

    if 'tp' in data:
        try:
            float(data['tp'])
        except (ValueError, TypeError):
            return False, "TP must be a number"

    return True, ""

def validate_modify_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate modify position command"""
    required = ['ticket']

    # Check required fields
    if 'ticket' not in data:
        return False, "Missing required field: ticket"

    # Ticket validation
    try:
        int(data['ticket'])
    except (ValueError, TypeError):
        return False, "Ticket must be an integer"

    # At least one modification
    if 'sl' not in data and 'tp' not in data:
        return False, "Must provide at least one of: sl, tp"

    # SL/TP validation
    if 'sl' in data:
        try:
            float(data['sl'])
        except (ValueError, TypeError):
            return False, "SL must be a number"

    if 'tp' in data:
        try:
            float(data['tp'])
        except (ValueError, TypeError):
            return False, "TP must be a number"

    return True, ""

def validate_close_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate close position command"""
    required = ['ticket']

    if 'ticket' not in data:
        return False, "Missing required field: ticket"

    # Ticket validation
    try:
        int(data['ticket'])
    except (ValueError, TypeError):
        return False, "Ticket must be an integer"

    # Optional volume validation
    if 'volume' in data:
        try:
            volume = float(data['volume'])
            if volume <= 0:
                return False, "Volume must be positive"
        except (ValueError, TypeError):
            return False, "Volume must be a number"

    return True, ""
````

## File: backend/tests/conftest.py
````python
import sys
from unittest.mock import MagicMock

# Mock MetaTrader5 module before it is imported by app modules
# This allows running tests on non-Windows environments (Linux/Mac)
# where the MetaTrader5 package cannot be installed.
module_name = 'MetaTrader5'
if module_name not in sys.modules:
    mock_mt5 = MagicMock()
    # Define constants used in code
    mock_mt5.TRADE_RETCODE_DONE = 10009
    mock_mt5.TRADE_RETCODE_REQUOTE = 10004
    mock_mt5.TRADE_RETCODE_TIMEOUT = 10022
    mock_mt5.TRADE_RETCODE_INVALID_PRICE = 10015
    mock_mt5.TRADE_RETCODE_PRICE_OFF = 10016
    mock_mt5.TRADE_RETCODE_PRICE_CHANGED = 10017
    mock_mt5.TRADE_RETCODE_CONNECTION = 10018
    mock_mt5.TRADE_RETCODE_ERROR = 10000
    mock_mt5.TRADE_RETCODE_DONE_PARTIAL = 10010
    mock_mt5.TRADE_RETCODE_INVALID = 10013
    
    mock_mt5.ORDER_TYPE_BUY = 0
    mock_mt5.ORDER_TYPE_SELL = 1
    
    mock_mt5.TRADE_ACTION_DEAL = 1
    mock_mt5.TRADE_ACTION_SLTP = 6
    
    mock_mt5.ORDER_TIME_GTC = 0
    mock_mt5.ORDER_FILLING_IOC = 1
    
    sys.modules[module_name] = mock_mt5
````

## File: backend/tests/test_circuit_breaker.py
````python
import unittest
import time
from unittest.mock import MagicMock
from app.mt5.circuit_breaker import CircuitBreaker, CircuitState

class TestCircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.cb = CircuitBreaker(
            failure_threshold=5,
            timeout=1.0,  # Short timeout for testing
            recovery_timeout=0.1
        )

    def test_closed_state_initially(self):
        self.assertEqual(self.cb.state, CircuitState.CLOSED)
        self.assertEqual(self.cb.failure_count, 0)

    def test_failure_counting(self):
        self.cb.record_failure()
        self.assertEqual(self.cb.failure_count, 1)
        self.assertEqual(self.cb.state, CircuitState.CLOSED)

    def test_circuit_opens_after_threshold(self):
        # Fail 5 times
        for _ in range(5):
            self.cb.record_failure()

        self.assertEqual(self.cb.failure_count, 5)
        self.assertEqual(self.cb.state, CircuitState.OPEN)

    def test_rejects_execution_when_open(self):
        self.cb.state = CircuitState.OPEN
        self.cb.last_failure_time = time.time()
        
        with self.assertRaises(RuntimeError):
            self.cb.execute(lambda: True)

    def test_recovery_to_half_open(self):
        self.cb.state = CircuitState.OPEN
        self.cb.last_failure_time = time.time() - 2.0  # Past timeout
        self.cb.failure_count = 5

        # Should transition to half-open
        self.assertTrue(self.cb.can_execute())
        self.assertEqual(self.cb.state, CircuitState.HALF_OPEN)

    def test_success_closes_half_open(self):
        self.cb.state = CircuitState.HALF_OPEN
        
        self.cb.execute(lambda: "success")
        
        self.assertEqual(self.cb.state, CircuitState.CLOSED)
        self.assertEqual(self.cb.failure_count, 0)

    def test_failure_reopens_half_open(self):
        self.cb.state = CircuitState.HALF_OPEN
        
        try:
            self.cb.execute(lambda: exec('raise Exception("fail")'))
        except Exception:
            pass
            
        self.assertEqual(self.cb.state, CircuitState.OPEN)

if __name__ == '__main__':
    unittest.main()
````

## File: backend/tests/test_command_processor.py
````python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.processors.command_processor import CommandProcessor
from app.models.responses import ErrorCode

@pytest.fixture
def mock_mt5_manager():
    manager = Mock()
    manager.is_connected.return_value = True
    return manager

@pytest.fixture
def processor(mock_mt5_manager):
    return CommandProcessor(mock_mt5_manager)

@pytest.mark.asyncio
async def test_process_buy_order_success(processor):
    """Test successful buy order processing"""
    with patch.object(processor.trading_ops, 'place_buy_market') as mock_buy:
        mock_buy.return_value = {
            'ticket': 123456,
            'price': 1.0850,
            'volume': 0.01,
            'timestamp': '2025-12-21T10:00:00Z'
        }

        result = await processor.process_buy_order(
            sid='test_client',
            symbol='EURUSD',
            volume=0.01,
            sl=1.0800,
            tp=1.0900
        )

        if not result['success']:
            print(f"Test Failed. Result: {result}")

        assert result['success'] is True
        assert result['ticket'] == 123456
        assert result['symbol'] == 'EURUSD'
        assert result['price'] == 1.0850
        assert 'command_id' in result

@pytest.mark.asyncio
async def test_process_buy_order_validation_error(processor):
    """Test buy order with validation error"""
    with patch.object(processor.trading_ops, 'place_buy_market') as mock_buy:
        mock_buy.side_effect = ValueError("Invalid symbol")

        result = await processor.process_buy_order(
            sid='test_client',
            symbol='INVALID',
            volume=0.01
        )

        assert result['success'] is False
        assert result['code'] == ErrorCode.VALIDATION_ERROR.value
        assert "Invalid symbol" in result['message']

@pytest.mark.asyncio
async def test_process_buy_order_mt5_error(processor):
    """Test buy order with MT5 connection error"""
    with patch.object(processor.trading_ops, 'place_buy_market') as mock_buy:
        mock_buy.side_effect = RuntimeError("MT5 not connected")

        result = await processor.process_buy_order(
            sid='test_client',
            symbol='EURUSD',
            volume=0.01
        )

        assert result['success'] is False
        assert result['code'] == ErrorCode.MT5_NOT_CONNECTED.value

@pytest.mark.asyncio
async def test_process_sell_order_success(processor):
    """Test successful sell order processing"""
    with patch.object(processor.trading_ops, 'place_sell_market') as mock_sell:
        mock_sell.return_value = {
            'ticket': 654321,
            'price': 1.0840,
            'volume': 0.01,
            'timestamp': '2025-12-21T10:00:00Z'
        }

        result = await processor.process_sell_order(
            sid='test_client',
            symbol='EURUSD',
            volume=0.01
        )

        assert result['success'] is True
        assert result['ticket'] == 654321
        assert result['type'] == 'sell' if 'type' in result else True # check handled by endpoint, here just check success

@pytest.mark.asyncio
async def test_process_modify_position_success(processor):
    """Test successful position modification"""
    with patch.object(processor.trading_ops, 'modify_position') as mock_modify:
        mock_modify.return_value = {
            'ticket': 123456,
            'new_sl': 1.0820,
            'new_tp': 1.0920,
            'modified_at': '2025-12-21T10:05:00Z'
        }

        result = await processor.process_modify_position(
            sid='test_client',
            ticket=123456,
            sl=1.0820,
            tp=1.0920
        )

        assert result['success'] is True
        assert result['ticket'] == 123456
        assert result['sl'] == 1.0820

@pytest.mark.asyncio
async def test_process_close_position_success(processor):
    """Test successful position close"""
    with patch.object(processor.trading_ops, 'close_position') as mock_close:
        mock_close.return_value = {
            'ticket': 123456,
            'close_ticket': 999999,
            'close_price': 1.0850,
            'volume_closed': 0.01,
            'profit': 10.0,
            'closed_at': '2025-12-21T10:10:00Z'
        }

        result = await processor.process_close_position(
            sid='test_client',
            ticket=123456
        )

        assert result['success'] is True
        assert result['ticket'] == 123456
        assert result['profit'] == 10.0
````

## File: backend/tests/test_connection_manager.py
````python
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.mt5.connection_manager import MT5ConnectionManager

@pytest.fixture
def mock_mt5():
    with patch('app.mt5.connection_manager.mt5') as mock:
        mock.initialize.return_value = True
        mock.terminal_info.return_value = MagicMock(connected=True, trade_allowed=True)
        yield mock

def test_connect_success(mock_mt5):
    manager = MT5ConnectionManager()
    assert manager.connect() is True
    assert manager.is_connected() is True

def test_connect_failure(mock_mt5):
    mock_mt5.initialize.return_value = False
    manager = MT5ConnectionManager()
    assert manager.connect() is False
    assert manager.is_connected() is False

def test_disconnect(mock_mt5):
    manager = MT5ConnectionManager()
    manager.connect()
    manager.disconnect()
    mock_mt5.shutdown.assert_called()
    assert manager._connected is False

def test_health_check_reconnect(mock_mt5):
    # This is harder to test without sleeping, but we can verify logic
    manager = MT5ConnectionManager(check_interval=0.1)
    
    # Mock initial connection
    manager.connect()
    
    # Simulate disconnect
    mock_mt5.terminal_info.return_value.connected = False
    
    # Attempt reconnect logic directly to avoid thread race conditions in simple test
    result = manager._attempt_reconnect(max_attempts=1)
    assert result is True
    assert mock_mt5.initialize.call_count >= 2 # Once for init, once for reconnect
````

## File: backend/tests/test_events.py
````python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.events import trading_events
from app.validation import validate_login_command

@pytest.mark.asyncio
async def test_connect_event():
    """Test client connection"""
    # Mock sio and session_manager
    sid = "test_client_1"
    environ = {'REMOTE_ADDR': '192.168.1.100'}
    
    with patch('app.events.trading_events.sio', new_callable=AsyncMock) as mock_sio, \
         patch('app.events.trading_events.session_manager') as mock_sm:
        
        # Call connect handler
        await trading_events.connect(sid, environ)
        
        # Verify session created
        mock_sm.create_session.assert_called_once()
        args = mock_sm.create_session.call_args[0]
        assert args[0] == sid
        assert args[1]['remote_addr'] == '192.168.1.100'
        
        # Verify welcome message
        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == 'connected'
        assert call_args[1]['to'] == sid

def test_login_validation():
    """Test login command validation"""
    # Valid
    valid, msg = validate_login_command({
        'account': 12345678,
        'password': 'test',
        'server': 'Demo'
    })
    assert valid is True

    # Invalid - missing field
    valid, msg = validate_login_command({
        'account': 12345678,
        'password': 'test'
    })
    assert valid is False
    assert 'server' in msg

@pytest.mark.asyncio
async def test_login_event_success():
    """Test successful login"""
    sid = "test_sid"
    data = {
        'account': 12345678,
        'password': 'pass',
        'server': 'server'
    }
    
    mock_account_info = {
        'login': 12345678,
        'name': 'Test User',
        'server': 'server',
        'currency': 'USD',
        'balance': 1000.0,
        'equity': 1000.0,
        'leverage': 100
    }

    with patch('app.events.trading_events.sio', new_callable=AsyncMock) as mock_sio, \
         patch('app.events.trading_events.session_manager') as mock_sm, \
         patch('app.events.trading_events.mt5_manager') as mock_mt5:
        
        mock_mt5.login_account.return_value = mock_account_info
        mock_sm.get_session.return_value = {}

        await trading_events.login(sid, data)
        
        mock_mt5.login_account.assert_called_once_with(12345678, 'pass', 'server')
        # Check success emission
        # We can't easily check the content of arguments with assert_called_with if they are complex objects
        # But we can check calls list
        assert mock_sio.emit.called
        call_args = mock_sio.emit.call_args_list[0]
        assert call_args[0][0] == 'login_result'
        assert call_args[0][1]['success'] is True
        assert call_args[1]['to'] == sid
````

## File: backend/tests/test_reconnection.py
````python
import unittest
import time
from datetime import datetime, timedelta
from app.reconnection_manager import ReconnectionManager

class TestReconnectionManager(unittest.TestCase):
    def setUp(self):
        self.rm = ReconnectionManager(session_ttl=1) # 1 second TTL

    def test_store_and_recover_session(self):
        sid = "test_sid"
        session_data = {"user": "test", "pending_orders": {}}
        
        self.rm.store_disconnected_session(sid, session_data)
        
        recovered = self.rm.recover_session(sid)
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered['user'], "test")

    def test_session_expiration(self):
        sid = "expired_sid"
        session_data = {"user": "test"}
        
        self.rm.store_disconnected_session(sid, session_data)
        
        # Wait for expiration
        time.sleep(1.1)
        
        recovered = self.rm.recover_session(sid)
        self.assertIsNone(recovered)

    def test_cleanup_task(self):
        self.rm.store_disconnected_session("s1", {})
        self.rm.store_disconnected_session("s2", {})
        
        time.sleep(1.1)
        
        removed = self.rm.cleanup_expired_sessions()
        self.assertEqual(removed, 2)
        self.assertEqual(len(self.rm.disconnected_sessions), 0)

    def test_reconnection_count_increments(self):
        sid = "count_sid"
        self.rm.store_disconnected_session(sid, {})
        
        self.rm.recover_session(sid) # 1st
        self.assertEqual(self.rm.disconnected_sessions[sid]['reconnection_count'], 1)

if __name__ == '__main__':
    unittest.main()
````

## File: backend/tests/test_trading_operations.py
````python
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from app.mt5.trading_operations import TradingOperations
from app.mt5.connection_manager import MT5ConnectionManager
import MetaTrader5 as mt5

@pytest.fixture
def mock_conn():
    conn = Mock(spec=MT5ConnectionManager)
    conn.is_connected.return_value = True
    return conn

@pytest.mark.asyncio
async def test_place_buy_market(mock_conn):
    ops = TradingOperations(mock_conn)

    # Mock MT5
    with patch('app.mt5.trading_operations.mt5') as mock_mt5, \
         patch('app.mt5.error_handler.mt5', mock_mt5): # Patch where ErrorHandler uses it too
        
        mock_mt5.symbol_info.return_value = MagicMock(visible=True)
        mock_mt5.symbol_info_tick.return_value = MagicMock(ask=1.0850, bid=1.0848)
        
        mock_ret = MagicMock()
        mock_ret.retcode = 10009 # DONE
        mock_ret.order = 123456
        mock_ret.price = 1.0850
        mock_ret._asdict.return_value = {'retcode': 10009, 'ticket': 123456, 'price': 1.0850}
        
        mock_mt5.order_send.return_value = mock_ret
        mock_mt5.TRADE_RETCODE_DONE = 10009
        mock_mt5.ORDER_TYPE_BUY = 0

        result = await ops.place_buy_market('EURUSD', 0.01, sl=1.0800, tp=1.0900)

        assert result['ticket'] == 123456
        assert result['price'] == 1.0850
        mock_mt5.order_send.assert_called_once()

@pytest.mark.asyncio
async def test_place_order_not_connected(mock_conn):
    mock_conn.is_connected.return_value = False
    ops = TradingOperations(mock_conn)
    result = await ops.place_buy_market('EURUSD', 0.01)
    # Check retcode for connection error (whatever we mapped or MT5 const)
    assert 'retcode' in result

@pytest.mark.asyncio
async def test_modify_position(mock_conn):
    ops = TradingOperations(mock_conn)
    
    with patch('app.mt5.trading_operations.mt5') as mock_mt5:
        # Mock existing position
        mock_pos = MagicMock()
        mock_pos._asdict.return_value = {'ticket': 123, 'symbol': 'EURUSD', 'sl': 1.0, 'tp': 2.0}
        mock_mt5.positions_get.return_value = [mock_pos]
        
        # Mock successful modification
        mock_ret = MagicMock()
        mock_ret.retcode = 10009
        mock_ret._asdict.return_value = {'retcode': 10009}
        mock_mt5.order_send.return_value = mock_ret
        mock_mt5.TRADE_RETCODE_DONE = 10009
        
        result = await ops.modify_position(123, new_sl=1.1)
        
        assert result['retcode'] == 10009
        args, _ = mock_mt5.order_send.call_args
        request = args[0]
        assert request['action'] == mt5.TRADE_ACTION_SLTP
        assert request['sl'] == 1.1
        assert request['tp'] == 2.0 # Unchanged
````

## File: backend/.env.example
````
MT5_ACCOUNT=0
MT5_PASSWORD=
MT5_SERVER=

MT5_CONN_TIMEOUT=30
MT5_HEALTH_INTERVAL=5
MT5_MAX_RETRIES=3
MT5_RETRY_DELAY=1

MT5_SLIPPAGE=20
MT5_FILLING=IOC
````

## File: backend/.gitignore
````
.env
.venv
````

## File: backend/README.md
````markdown
# MT5 SocketIO Server - Phase 1

## Overview
Phase 1 implements the foundation for the MT5 SocketIO Trading Server, including:
- Connection management with health checks and auto-reconnection
- Trading operations (Buy, Sell, Modify, Close)
- Error handling with retry logic
- Configuration management

## Setup

### Prerequisites
- Windows OS (required for MetaTrader5 Python package)
- MetaTrader 5 Terminal installed
- Python 3.11+

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Environment:
   ```bash
   copy .env.example .env
   # Edit .env with your MT5 account credentials
   ```

## Running Tests

To run the unit tests:
```bash
pytest tests/
```

Note: The tests use mocks and can run on non-Windows systems if `MetaTrader5` is mocked in `sys.modules` (handled in `tests/conftest.py`).

## Usage Example

```python
import asyncio
from app.mt5.connection_manager import MT5ConnectionManager
from app.mt5.trading_operations import TradingOperations

async def main():
    manager = MT5ConnectionManager()
    if manager.connect():
        ops = TradingOperations(manager)
        
        # Place buy order
        result = await ops.place_buy_market("EURUSD", 0.01)
        print(result)
        
        manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```
````

## File: guide/COMMANDS.md
````markdown
# Commands Catalog

Auto-generated catalog of all available commands in ClaudeKit Engineer.

**Last Updated**: 2025-11-21

**Total Commands**: 54

## Categories

- [Bootstrap Commands](#bootstrap)
- [Content Creation](#content)
- [Cook Commands](#cook)
- [Core Commands](#core)
- [Design Commands](#design)
- [Documentation](#docs)
- [Fix & Debug](#fix)
- [Git Commands](#git)
- [Integrations](#integrate)
- [Planning](#plan)
- [Code Review](#review)
- [Scout Commands](#scout)
- [Skill Management](#skill)

## Bootstrap Commands

### `/ck:bootstrap:auto`
**Complexity**: ⚡⚡⚡⚡

**Description**: Bootstrap a new project automatically

**Usage**: `/ck:bootstrap:auto user-requirements`


### `/ck:bootstrap:auto:fast`
**Complexity**: ⚡⚡⚡

**Description**: Quickly bootstrap a new project automatically

**Usage**: `/ck:bootstrap:auto:fast user-requirements`


## Content Creation

### `/ck:content:cro`
**Description**: Analyze the current content and optimize for conversion

**Usage**: `/ck:content:cro issues`


### `/ck:content:enhance`
**Description**: Analyze the current copy issues and enhance it

**Usage**: `/ck:content:enhance issues`


### `/ck:content:fast`
**Description**: Write creative & smart copy [FAST]

**Usage**: `/ck:content:fast user-request`


### `/ck:content:good`
**Description**: Write good creative & smart copy [GOOD]

**Usage**: `/ck:content:good user-request`


## Cook Commands

### `/ck:cook:auto`
**Complexity**: ⚡⚡

**Description**: Implement a feature automatically ("trust me bro")

**Usage**: `/ck:cook:auto tasks`


### `/ck:cook:auto:fast`
**Complexity**: ⚡

**Description**: No research. Only scout, plan & implement ["trust me bro"]

**Usage**: `/ck:cook:auto:fast tasks-or-prompt`


## Core Commands

### `/ck:ask`
**Complexity**: ⚡

**Description**: Answer technical and architectural questions.

**Usage**: `/ck:ask technical-question`


### `/ck:bootstrap`
**Complexity**: ⚡⚡⚡⚡⚡

**Description**: Bootstrap a new project step by step

**Usage**: `/ck:bootstrap user-requirements`


### `/ck:brainstorm`
**Complexity**: ⚡⚡

**Description**: Brainstorm a feature

**Usage**: `/ck:brainstorm question`


### `/ck:code`
**Complexity**: ⚡

**Description**: Start coding & testing an existing plan

**Usage**: `/ck:code plan`


### `/ck:cook`
**Complexity**: ⚡⚡⚡

**Description**: Implement a feature [step by step]

**Usage**: `/ck:cook tasks`


### `/ck:debug`
**Complexity**: ⚡⚡

**Description**: Debugging technical issues and providing solutions.

**Usage**: `/ck:debug issues`


### `/ck:fix`
**Complexity**: ⚡⚡

**Description**: Analyze and fix small issues [AUTO DETECT COMPLEXITY]

**Usage**: `/ck:fix issues`


### `/ck:journal`
**Complexity**: ⚡

**Description**: Write some journal entries.


### `/ck:plan`
**Complexity**: ⚡⚡⚡

**Description**: Intelligent plan creation with prompt enhancement

**Usage**: `/ck:plan task`


### `/ck:scout`
**Description**: 


### `/ck:test`
**Complexity**: ⚡

**Description**: Run tests locally and analyze the summary report.


### `/ck:use-mcp`
**Description**: Utilize tools of Model Context Protocol (MCP) servers

**Usage**: `/ck:use-mcp task`


### `/ck:watzup`
**Complexity**: ⚡

**Description**: Review recent changes and wrap up the work


## Design Commands

### `/ck:design:3d`
**Description**: Create immersive interactive 3D designs with Three.js

**Usage**: `/ck:design:3d tasks`


### `/ck:design:describe`
**Description**: Describe a design based on screenshot/video

**Usage**: `/ck:design:describe screenshot`


### `/ck:design:fast`
**Description**: Create a quick design

**Usage**: `/ck:design:fast tasks`


### `/ck:design:good`
**Description**: Create an immersive design

**Usage**: `/ck:design:good tasks`


### `/ck:design:screenshot`
**Description**: Create a design based on screenshot

**Usage**: `/ck:design:screenshot screenshot`


### `/ck:design:video`
**Description**: Create a design based on video

**Usage**: `/ck:design:video video`


## Documentation

### `/ck:docs:init`
**Complexity**: ⚡⚡⚡⚡

**Description**: Analyze the codebase and create initial documentation


### `/ck:docs:summarize`
**Description**: 


### `/ck:docs:update`
**Complexity**: ⚡⚡⚡

**Description**: Analyze the codebase and update documentation


## Fix & Debug

### `/ck:fix:ci`
**Complexity**: ⚡

**Description**: Analyze Github Actions logs and fix issues

**Usage**: `/ck:fix:ci github-actions-url`


### `/ck:fix:fast`
**Complexity**: ⚡

**Description**: Analyze and fix small issues [FAST]

**Usage**: `/ck:fix:fast issues`


### `/ck:fix:hard`
**Complexity**: ⚡⚡⚡

**Description**: Use subagents to plan and fix hard issues

**Usage**: `/ck:fix:hard issues`


### `/ck:fix:logs`
**Complexity**: ⚡

**Description**: Analyze logs and fix issues

**Usage**: `/ck:fix:logs issue`


### `/ck:fix:test`
**Complexity**: ⚡⚡

**Description**: Run test suite and fix issues

**Usage**: `/ck:fix:test issues`


### `/ck:fix:types`
**Complexity**: ⚡

**Description**: Fix type errors


### `/ck:fix:ui`
**Complexity**: ⚡⚡

**Description**: Analyze and fix UI issues

**Usage**: `/ck:fix:ui issue`


## Git Commands

### `/ck:git:cm`
**Description**: Stage all files and create a commit.


### `/ck:git:cp`
**Description**: Stage, commit and push all code in the current branch


### `/ck:git:pr`
**Description**: 


## Integrations

### `/ck:integrate:polar`
**Complexity**: ⚡⚡

**Description**: Implement payment integration with Polar.sh

**Usage**: `/ck:integrate:polar tasks`


### `/ck:integrate:sepay`
**Complexity**: ⚡⚡

**Description**: Implement payment integration with SePay.vn

**Usage**: `/ck:integrate:sepay tasks`


## Planning

### `/ck:plan:ci`
**Description**: Analyze Github Actions logs and provide a plan to fix the issues

**Usage**: `/ck:plan:ci github-actions-url`


### `/ck:plan:cro`
**Description**: Create a CRO plan for the given content

**Usage**: `/ck:plan:cro issues`


### `/ck:plan:fast`
**Complexity**: ⚡⚡

**Description**: No research. Only analyze and create an implementation plan

**Usage**: `/ck:plan:fast task`


### `/ck:plan:hard`
**Complexity**: ⚡⚡⚡

**Description**: Research, analyze, and create an implementation plan

**Usage**: `/ck:plan:hard task`


### `/ck:plan:two`
**Complexity**: ⚡⚡⚡⚡

**Description**: Research & create an implementation plan with 2 approaches

**Usage**: `/ck:plan:two task`


## Code Review

### `/ck:review:codebase`
**Complexity**: ⚡⚡⚡

**Description**: Scan & analyze the codebase.

**Usage**: `/ck:review:codebase tasks-or-prompt`


## Scout Commands

### `/ck:scout:ext`
**Description**: 


## Skill Management

### `/ck:skill:add`
**Description**: 


### `/ck:skill:create`
**Description**: Create a new agent skill

**Usage**: `/ck:skill:create prompt-or-llms-or-github-url`


### `/ck:skill:fix-logs`
**Description**: Fix the agent skill based on `logs.txt` file.

**Usage**: `/ck:skill:fix-logs prompt-or-path-to-skill`


### `/ck:skill:optimize`
**Description**: 


### `/ck:skill:optimize:auto`
**Description**:
````

## File: guide/COMMANDS.yaml
````yaml
metadata:
  title: Commands Catalog
  description: Auto-generated catalog of all available commands in ClaudeKit Engineer
  last_updated: '2025-11-27'
  total_commands: 55
categories:
  core: Core Commands
  bootstrap: Bootstrap Commands
  content: Content Creation
  cook: Cook Commands
  design: Design Commands
  docs: Documentation
  fix: Fix & Debug
  git: Git Commands
  integrate: Integrations
  plan: Planning
  review: Code Review
  scout: Scout Commands
  skill: Skill Management
commands:
  core:
  - name: ck-help
    path: ck-help.md
    description: ClaudeKit usage guide - just type naturally
    argument_hint:
    - category|command|task
    power_level: 1
    category: core
  - name: ask
    path: ask.md
    description: Answer technical and architectural questions.
    argument_hint:
    - technical-question
    power_level: 1
    category: core
  - name: bootstrap
    path: bootstrap.md
    description: Bootstrap a new project step by step
    argument_hint:
    - user-requirements
    power_level: 5
    category: core
  - name: brainstorm
    path: brainstorm.md
    description: Brainstorm a feature
    argument_hint:
    - question
    power_level: 2
    category: core
  - name: code
    path: code.md
    description: Start coding & testing an existing plan
    argument_hint:
    - plan
    power_level: 1
    category: core
  - name: cook
    path: cook.md
    description: Implement a feature [step by step]
    argument_hint:
    - tasks
    power_level: 3
    category: core
  - name: debug
    path: debug.md
    description: Debugging technical issues and providing solutions.
    argument_hint:
    - issues
    power_level: 2
    category: core
  - name: fix
    path: fix.md
    description: Analyze and fix small issues [AUTO DETECT COMPLEXITY]
    argument_hint:
    - issues
    power_level: 2
    category: core
  - name: journal
    path: journal.md
    description: Write some journal entries.
    argument_hint: ''
    power_level: 1
    category: core
  - name: plan
    path: plan.md
    description: Intelligent plan creation with prompt enhancement
    argument_hint:
    - task
    power_level: 3
    category: core
  - name: scout
    path: scout.md
    description: ''
    argument_hint: ''
    power_level: 0
    category: core
  - name: test
    path: test.md
    description: Run tests locally and analyze the summary report.
    argument_hint: ''
    power_level: 1
    category: core
  - name: use-mcp
    path: use-mcp.md
    description: Utilize tools of Model Context Protocol (MCP) servers
    argument_hint:
    - task
    power_level: 0
    category: core
  - name: watzup
    path: watzup.md
    description: Review recent changes and wrap up the work
    argument_hint: ''
    power_level: 1
    category: core
  bootstrap:
  - name: bootstrap:auto
    path: bootstrap/auto.md
    description: Bootstrap a new project automatically
    argument_hint:
    - user-requirements
    power_level: 4
    category: bootstrap
  - name: bootstrap:auto:fast
    path: bootstrap/auto/fast.md
    description: Quickly bootstrap a new project automatically
    argument_hint:
    - user-requirements
    power_level: 3
    category: bootstrap
  content:
  - name: content:cro
    path: content/cro.md
    description: Analyze the current content and optimize for conversion
    argument_hint:
    - issues
    power_level: 0
    category: content
  - name: content:enhance
    path: content/enhance.md
    description: Analyze the current copy issues and enhance it
    argument_hint:
    - issues
    power_level: 0
    category: content
  - name: content:fast
    path: content/fast.md
    description: Write creative & smart copy [FAST]
    argument_hint:
    - user-request
    power_level: 0
    category: content
  - name: content:good
    path: content/good.md
    description: Write good creative & smart copy [GOOD]
    argument_hint:
    - user-request
    power_level: 0
    category: content
  cook:
  - name: cook:auto
    path: cook/auto.md
    description: Implement a feature automatically ("trust me bro")
    argument_hint:
    - tasks
    power_level: 2
    category: cook
  - name: cook:auto:fast
    path: cook/auto/fast.md
    description: No research. Only scout, plan & implement ["trust me bro"]
    argument_hint:
    - tasks-or-prompt
    power_level: 1
    category: cook
  design:
  - name: design:3d
    path: design/3d.md
    description: Create immersive interactive 3D designs with Three.js
    argument_hint:
    - tasks
    power_level: 0
    category: design
  - name: design:describe
    path: design/describe.md
    description: Describe a design based on screenshot/video
    argument_hint:
    - screenshot
    power_level: 0
    category: design
  - name: design:fast
    path: design/fast.md
    description: Create a quick design
    argument_hint:
    - tasks
    power_level: 0
    category: design
  - name: design:good
    path: design/good.md
    description: Create an immersive design
    argument_hint:
    - tasks
    power_level: 0
    category: design
  - name: design:screenshot
    path: design/screenshot.md
    description: Create a design based on screenshot
    argument_hint:
    - screenshot
    power_level: 0
    category: design
  - name: design:video
    path: design/video.md
    description: Create a design based on video
    argument_hint:
    - video
    power_level: 0
    category: design
  docs:
  - name: docs:init
    path: docs/init.md
    description: Analyze the codebase and create initial documentation
    argument_hint: ''
    power_level: 4
    category: docs
  - name: docs:summarize
    path: docs/summarize.md
    description: ''
    argument_hint: ''
    power_level: 0
    category: docs
  - name: docs:update
    path: docs/update.md
    description: Analyze the codebase and update documentation
    argument_hint: ''
    power_level: 3
    category: docs
  fix:
  - name: fix:ci
    path: fix/ci.md
    description: Analyze Github Actions logs and fix issues
    argument_hint:
    - github-actions-url
    power_level: 1
    category: fix
  - name: fix:fast
    path: fix/fast.md
    description: Analyze and fix small issues [FAST]
    argument_hint:
    - issues
    power_level: 1
    category: fix
  - name: fix:hard
    path: fix/hard.md
    description: Use subagents to plan and fix hard issues
    argument_hint:
    - issues
    power_level: 3
    category: fix
  - name: fix:logs
    path: fix/logs.md
    description: Analyze logs and fix issues
    argument_hint:
    - issue
    power_level: 1
    category: fix
  - name: fix:test
    path: fix/test.md
    description: Run test suite and fix issues
    argument_hint:
    - issues
    power_level: 2
    category: fix
  - name: fix:types
    path: fix/types.md
    description: Fix type errors
    argument_hint: ''
    power_level: 1
    category: fix
  - name: fix:ui
    path: fix/ui.md
    description: Analyze and fix UI issues
    argument_hint:
    - issue
    power_level: 2
    category: fix
  git:
  - name: git:cm
    path: git/cm.md
    description: Stage all files and create a commit.
    argument_hint: ''
    power_level: 0
    category: git
  - name: git:cp
    path: git/cp.md
    description: Stage, commit and push all code in the current branch
    argument_hint: ''
    power_level: 0
    category: git
  - name: git:pr
    path: git/pr.md
    description: ''
    argument_hint: ''
    power_level: 0
    category: git
  integrate:
  - name: integrate:polar
    path: integrate/polar.md
    description: Implement payment integration with Polar.sh
    argument_hint:
    - tasks
    power_level: 2
    category: integrate
  - name: integrate:sepay
    path: integrate/sepay.md
    description: Implement payment integration with SePay.vn
    argument_hint:
    - tasks
    power_level: 2
    category: integrate
  plan:
  - name: plan:ci
    path: plan/ci.md
    description: Analyze Github Actions logs and provide a plan to fix the issues
    argument_hint:
    - github-actions-url
    power_level: 0
    category: plan
  - name: plan:cro
    path: plan/cro.md
    description: Create a CRO plan for the given content
    argument_hint:
    - issues
    power_level: 0
    category: plan
  - name: plan:fast
    path: plan/fast.md
    description: No research. Only analyze and create an implementation plan
    argument_hint:
    - task
    power_level: 2
    category: plan
  - name: plan:hard
    path: plan/hard.md
    description: Research, analyze, and create an implementation plan
    argument_hint:
    - task
    power_level: 3
    category: plan
  - name: plan:two
    path: plan/two.md
    description: Research & create an implementation plan with 2 approaches
    argument_hint:
    - task
    power_level: 4
    category: plan
  review:
  - name: review:codebase
    path: review/codebase.md
    description: Scan & analyze the codebase.
    argument_hint:
    - tasks-or-prompt
    power_level: 3
    category: review
  scout:
  - name: scout:ext
    path: scout/ext.md
    description: ''
    argument_hint: ''
    power_level: 0
    category: scout
  skill:
  - name: skill:add
    path: skill/add.md
    description: ''
    argument_hint: ''
    power_level: 0
    category: skill
  - name: skill:create
    path: skill/create.md
    description: Create a new agent skill
    argument_hint:
    - prompt-or-llms-or-github-url
    power_level: 0
    category: skill
  - name: skill:fix-logs
    path: skill/fix-logs.md
    description: Fix the agent skill based on `logs.txt` file.
    argument_hint:
    - prompt-or-path-to-skill
    power_level: 0
    category: skill
  - name: skill:optimize
    path: skill/optimize.md
    description: ''
    argument_hint: ''
    power_level: 0
    category: skill
  - name: skill:optimize:auto
    path: skill/optimize/auto.md
    description: ''
    argument_hint: ''
    power_level: 0
    category: skill
````

## File: guide/ENVIRONMENT_RESOLVER.md
````markdown
# Centralized Environment Variable Resolution

## Overview

All Claude Code skills now use a centralized environment variable resolver (`~/.claude/scripts/resolve_env.py`) for consistent configuration management across project-local and user-global scopes.

## Priority Hierarchy

Environment variables are resolved in this order (highest to lowest):

1. **process.env** - Runtime environment variables (HIGHEST)
2. **PROJECT/.claude/skills/\<skill\>/.env** - Project skill-specific overrides
3. **PROJECT/.claude/skills/.env** - Project shared across all skills
4. **PROJECT/.claude/.env** - Project global defaults
5. **~/.claude/skills/\<skill\>/.env** - User skill-specific overrides
6. **~/.claude/skills/.env** - User shared across all skills
7. **~/.claude/.env** - User global defaults (LOWEST)

## Benefits

### 1. **Consistency**
All skills use the same resolution logic - no more divergent implementations.

### 2. **Flexibility**
Supports both project-local and user-global configurations:
- **Project-local** (`.claude/` in project): Version-controlled, team-shared defaults
- **User-global** (`~/.claude/`): Personal overrides, API keys, machine-specific config

### 3. **Debuggability**
Built-in tools for troubleshooting:
```bash
# Show hierarchy for specific skill
python ~/.claude/scripts/resolve_env.py --show-hierarchy --skill ai-multimodal

# Find where variable is defined
python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --find-all

# Resolve with verbose output
python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --skill ai-multimodal --verbose
```

### 4. **Maintainability**
Single source of truth - update once, affects all skills.

## Usage

### CLI Usage

```bash
# Resolve variable for specific skill
python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --skill ai-multimodal

# With default value
python ~/.claude/scripts/resolve_env.py API_KEY --default fallback-value

# Export format for shell
eval $(python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --export)

# Show hierarchy
python ~/.claude/scripts/resolve_env.py --show-hierarchy --skill ai-multimodal
```

### Python API Usage

```python
import sys
from pathlib import Path

# Import centralized resolver
sys.path.insert(0, str(Path.home() / '.claude' / 'scripts'))
from resolve_env import resolve_env

# Resolve API key
api_key = resolve_env('GEMINI_API_KEY', skill='ai-multimodal')

if not api_key:
    print("Error: GEMINI_API_KEY not found")
    sys.exit(1)

# Use api_key...
```

### Integration in Skills

Skills automatically use the centralized resolver with fallback:

```python
# Import centralized environment resolver
sys.path.insert(0, str(Path.home() / '.claude' / 'scripts'))
try:
    from resolve_env import resolve_env
    CENTRALIZED_RESOLVER_AVAILABLE = True
except ImportError:
    CENTRALIZED_RESOLVER_AVAILABLE = False
    # Fallback to legacy resolution...

def find_api_key() -> Optional[str]:
    if CENTRALIZED_RESOLVER_AVAILABLE:
        return resolve_env('GEMINI_API_KEY', skill='skill-name')
    # Fallback logic...
```

## Common Scenarios

### Scenario 1: Global Default
```bash
# ~/.claude/.env
GEMINI_API_KEY=my-personal-key
```
Result: All skills use `my-personal-key` by default.

### Scenario 2: Project Override
```bash
# ~/.claude/.env
GEMINI_API_KEY=personal-key

# PROJECT/.claude/.env
GEMINI_API_KEY=team-shared-key
```
Result: When working in PROJECT, skills use `team-shared-key`.

### Scenario 3: Skill-Specific Override
```bash
# ~/.claude/.env
GEMINI_API_KEY=default-key

# ~/.claude/skills/ai-multimodal/.env
GEMINI_API_KEY=high-quota-key
```
Result: ai-multimodal uses `high-quota-key`, other skills use `default-key`.

### Scenario 4: Runtime Testing
```bash
export GEMINI_API_KEY=test-key
python script.py
```
Result: All skills use `test-key` regardless of config files.

## Debugging

### Check Hierarchy
```bash
python ~/.claude/scripts/resolve_env.py --show-hierarchy --skill ai-multimodal
```

Output shows which config files exist (✓) and their priority:
```
Environment Variable Resolution Hierarchy
============================================================

Priority order (highest to lowest):
1. process.env - Runtime environment
2. Project skill-specific (ai-multimodal) ✗ /path/to/project/.claude/skills/ai-multimodal/.env
3. Project skills shared          ✓ /path/to/project/.claude/skills/.env
4. Project global                 ✓ /path/to/project/.claude/.env
5. User skill-specific (ai-multimodal) ✗ /Users/user/.claude/skills/ai-multimodal/.env
6. User skills shared             ✓ /Users/user/.claude/skills/.env
7. User global                    ✓ /Users/user/.claude/.env
```

### Find All Locations
```bash
python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --find-all
```

Shows everywhere the variable is defined and which one wins:
```
Variable 'GEMINI_API_KEY' found in 2 location(s):
============================================================

2. Project global
   Path: /path/to/project/.claude/.env
   Value: AIza...FJI

7. User global
   Path: /Users/user/.claude/.env
   Value: AIza...XYZ

============================================================
✓ Resolved value (highest priority): AIza...FJI
```

### Verbose Resolution
```bash
python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --skill ai-multimodal --verbose
```

Shows step-by-step where the resolver looks:
```
✗ GEMINI_API_KEY not in: Runtime environment
✗ GEMINI_API_KEY not in: Project skill-specific (ai-multimodal) (file not found)
✓ GEMINI_API_KEY found in: Project skills shared
  Path: /path/to/project/.claude/skills/.env
```

## Migration Guide

### For Existing Skills

1. Keep existing `find_api_key()` function as fallback
2. Add centralized resolver import at top:
```python
sys.path.insert(0, str(Path.home() / '.claude' / 'scripts'))
try:
    from resolve_env import resolve_env
    CENTRALIZED_RESOLVER_AVAILABLE = True
except ImportError:
    CENTRALIZED_RESOLVER_AVAILABLE = False
```

3. Update resolution logic:
```python
def find_api_key() -> Optional[str]:
    if CENTRALIZED_RESOLVER_AVAILABLE:
        return resolve_env('GEMINI_API_KEY', skill='skill-name')
    # Keep fallback logic for backward compatibility
```

### For New Skills

Simply use the centralized resolver directly:
```python
from resolve_env import resolve_env

api_key = resolve_env('API_KEY_NAME', skill='skill-name')
```

## Files Created

1. **~/.claude/scripts/resolve_env.py** - Centralized resolver implementation
2. **~/.claude/scripts/README.md** - Detailed usage documentation
3. **.claude/ENVIRONMENT_RESOLVER.md** (this file) - Project documentation

## Updated Files

1. **.claude/.env.example** - Added resolver reference
2. **.claude/skills/.env.example** - Added resolver reference
3. **.claude/skills/ai-multimodal/.env.example** - Added resolver reference
4. **.claude/skills/ai-multimodal/scripts/gemini_batch_process.py** - Integrated resolver
5. **.claude/skills/ai-multimodal/SKILL.md** - Updated documentation

## Next Steps

1. **Test the resolver** with your actual API keys
2. **Update other skills** to use centralized resolver
3. **Create config files** as needed:
   - `~/.claude/.env` for personal defaults
   - `.claude/.env` in projects for team defaults
   - `.claude/skills/<skill>/.env` for skill-specific overrides

## Support

- Documentation: `~/.claude/scripts/README.md`
- Show hierarchy: `python ~/.claude/scripts/resolve_env.py --show-hierarchy`
- Debug variable: `python ~/.claude/scripts/resolve_env.py VAR_NAME --verbose`
````

## File: guide/SKILLS.md
````markdown
# Skills Catalog

Auto-generated catalog of all available skills in ClaudeKit Engineer.

**Last Updated**: 2025-11-21

**Total Skills**: 33

## Categories

- [AI & Machine Learning](#ai-ml)
- [Backend Development](#backend)
- [Database & Storage](#database)
- [Development Tools](#dev-tools)
- [Frameworks & Platforms](#frameworks)
- [Frontend & Design](#frontend)
- [Infrastructure & DevOps](#infrastructure)
- [Multimedia & Processing](#multimedia)
- [Utilities & Helpers](#utilities)

## Legend

- 📦 Has executable scripts
- 📚 Has reference documentation

## AI & Machine Learning

### 📦 📚 `ai-multimodal`

Process and generate multimedia content using Google Gemini API. Capabilities include analyze audio files (transcription with timestamps, summarization, speech understanding, music/sound analysis up to 9.5 hours), understand images (captioning, object detection, OCR, visual Q&A, segmentation), process videos (scene detection, Q&A, temporal analysis, YouTube URLs, up to 6 hours), extract from documents (PDF tables, forms, charts, diagrams, multi-page), generate images (text-to-image with Imagen 4, editing, composition, refinement), generate videos (text-to-video with Veo 3, 8-second clips with native audio). Use when working with audio/video files, analyzing images or screenshots, processing PDF documents, extracting structured data from media, creating images/videos from text prompts, or implementing multimodal AI features. Supports Gemini 3/2.5, Imagen 4, and Veo 3 models with context windows up to 2M tokens.

**Location**: `.claude/skills/ai-multimodal/SKILL.md`

### `google-adk-python`

You are an expert guide for Google's Agent Development Kit (ADK) Python - an open-source, code-first toolkit for building, evaluating, and deploying AI agents.

**Location**: `.claude/skills/google-adk-python/SKILL.md`

## Backend Development

### 📚 `backend-development`

Build robust backend systems with modern technologies (Node.js, Python, Go, Rust), frameworks (NestJS, FastAPI, Django), databases (PostgreSQL, MongoDB, Redis), APIs (REST, GraphQL, gRPC), authentication (OAuth 2.1, JWT), testing strategies, security best practices (OWASP Top 10), performance optimization, scalability patterns (microservices, caching, sharding), DevOps practices (Docker, Kubernetes, CI/CD), and monitoring. Use when designing APIs, implementing authentication, optimizing database queries, setting up CI/CD pipelines, handling security vulnerabilities, building microservices, or developing production-ready backend systems.

**Location**: `.claude/skills/backend-development/SKILL.md`

### 📦 📚 `better-auth`

Implement authentication and authorization with Better Auth - a framework-agnostic TypeScript authentication framework. Features include email/password authentication with verification, OAuth providers (Google, GitHub, Discord, etc.), two-factor authentication (TOTP, SMS), passkeys/WebAuthn support, session management, role-based access control (RBAC), rate limiting, and database adapters. Use when adding authentication to applications, implementing OAuth flows, setting up 2FA/MFA, managing user sessions, configuring authorization rules, or building secure authentication systems for web applications.

**Location**: `.claude/skills/better-auth/SKILL.md`

### 📦 📚 `payment-integration`

Implement payment integrations with SePay (Vietnamese payment gateway with VietQR, bank transfers, cards) and Polar (global SaaS monetization platform with subscriptions, usage-based billing, automated benefits). Use when integrating payment processing, implementing checkout flows, managing subscriptions, handling webhooks, processing bank transfers, generating QR codes, automating benefit delivery, or building billing systems. Supports authentication (API keys, OAuth2), product management, customer portals, tax compliance (Polar as MoR), and comprehensive SDK integrations (Node.js, PHP, Python, Go, Laravel, Next.js).

**Location**: `.claude/skills/payment-integration/SKILL.md`

## Database & Storage

### 📦 📚 `databases`

Work with MongoDB (document database, BSON documents, aggregation pipelines, Atlas cloud) and PostgreSQL (relational database, SQL queries, psql CLI, pgAdmin). Use when designing database schemas, writing queries and aggregations, optimizing indexes for performance, performing database migrations, configuring replication and sharding, implementing backup and restore strategies, managing database users and permissions, analyzing query performance, or administering production databases.

**Location**: `.claude/skills/databases/SKILL.md`

## Development Tools

### 📚 `claude-code`

Activate when users ask about Claude Code installation, slash commands (/cook, /plan, /fix, /test, /docs, /design, /git), creating/managing Agent Skills, configuring MCP servers, setting up hooks/plugins, IDE integration (VS Code, JetBrains), CI/CD workflows, enterprise deployment (SSO, RBAC, sandboxing), troubleshooting authentication/performance issues, or advanced features (extended thinking, caching, checkpointing).

**Location**: `.claude/skills/claude-code/SKILL.md`

### 📦 📚 `docs-seeker`

Search technical documentation using executable scripts to detect query type, fetch from llms.txt sources (context7.com), and analyze results. Use when user needs: (1) Topic-specific documentation (features/components/concepts), (2) Library/framework documentation, (3) GitHub repository analysis, (4) Documentation discovery with automated agent distribution strategy

**Location**: `.claude/skills/docs-seeker/SKILL.md`

### 📦 📚 `mcp-management`

Manage Model Context Protocol (MCP) servers - discover, analyze, and execute tools/prompts/resources from configured MCP servers. Use when working with MCP integrations, need to discover available MCP capabilities, filter MCP tools for specific tasks, execute MCP tools programmatically, access MCP prompts/resources, or implement MCP client functionality. Supports intelligent tool selection, multi-server management, and context-efficient capability discovery.

**Location**: `.claude/skills/mcp-management/SKILL.md`

### 📦 📚 `repomix`

Package entire code repositories into single AI-friendly files using Repomix. Capabilities include pack codebases with customizable include/exclude patterns, generate multiple output formats (XML, Markdown, plain text), preserve file structure and context, optimize for AI consumption with token counting, filter by file types and directories, add custom headers and summaries. Use when packaging codebases for AI analysis, creating repository snapshots for LLM context, analyzing third-party libraries, preparing for security audits, generating documentation context, or evaluating unfamiliar codebases.

**Location**: `.claude/skills/repomix/SKILL.md`

### 📦 `skill-creator`

Guide for creating effective skills, adding skill references, skill scripts or optimizing existing skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, frameworks, libraries or plugins usage, or API and tool integrations.

**Location**: `.claude/skills/skill-creator/SKILL.md`

## Frameworks & Platforms

### 📚 `mobile-development`

Build modern mobile applications with React Native, Flutter, Swift/SwiftUI, and Kotlin/Jetpack Compose. Covers mobile-first design principles, performance optimization (battery, memory, network), offline-first architecture, platform-specific guidelines (iOS HIG, Material Design), testing strategies, security best practices, accessibility, app store deployment, and mobile development mindset. Use when building mobile apps, implementing mobile UX patterns, optimizing for mobile constraints, or making native vs cross-platform decisions.

**Location**: `.claude/skills/mobile-development/SKILL.md`

### 📦 📚 `shopify`

Build Shopify applications, extensions, and themes using GraphQL/REST APIs, Shopify CLI, Polaris UI components, and Liquid templating. Capabilities include app development with OAuth authentication, checkout UI extensions for customizing checkout flow, admin UI extensions for dashboard integration, POS extensions for retail, theme development with Liquid, webhook management, billing API integration, product/order/customer management. Use when building Shopify apps, implementing checkout customizations, creating admin interfaces, developing themes, integrating payment processing, managing store data via APIs, or extending Shopify functionality.

**Location**: `.claude/skills/shopify/SKILL.md`

### 📦 📚 `web-frameworks`

Build modern full-stack web applications with Next.js (App Router, Server Components, RSC, PPR, SSR, SSG, ISR), Turborepo (monorepo management, task pipelines, remote caching, parallel execution), and RemixIcon (3100+ SVG icons in outlined/filled styles). Use when creating React applications, implementing server-side rendering, setting up monorepos with multiple packages, optimizing build performance and caching strategies, adding icon libraries, managing shared dependencies, or working with TypeScript full-stack projects.

**Location**: `.claude/skills/web-frameworks/SKILL.md`

## Frontend & Design

### 📚 `aesthetic`

Create aesthetically beautiful interfaces following proven design principles. Use when building UI/UX, analyzing designs from inspiration sites, generating design images with ai-multimodal, implementing visual hierarchy and color theory, adding micro-interactions, or creating design documentation. Includes workflows for capturing and analyzing inspiration screenshots with chrome-devtools and ai-multimodal, iterative design image generation until aesthetic standards are met, and comprehensive design system guidance covering BEAUTIFUL (aesthetic principles), RIGHT (functionality/accessibility), SATISFYING (micro-interactions), and PEAK (storytelling) stages. Integrates with chrome-devtools, ai-multimodal, media-processing, ui-styling, and web-frameworks skills.

**Location**: `.claude/skills/aesthetic/SKILL.md`

### 📚 `frontend-design`

Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications, OR when they provide screenshots/images/designs to replicate or draw inspiration from. For screenshot inputs, extracts design guidelines first using ai-multimodal analysis, then implements code following those guidelines. Generates creative, polished code that avoids generic AI aesthetics.

**Location**: `.claude/skills/frontend-design/SKILL.md`

### `frontend-development`

Frontend development guidelines for React/TypeScript applications. Modern patterns including Suspense, lazy loading, useSuspenseQuery, file organization with features directory, MUI v7 styling, TanStack Router, performance optimization, and TypeScript best practices. Use when creating components, pages, features, fetching data, styling, routing, or working with frontend code.

**Location**: `.claude/skills/frontend-development/SKILL.md`

### 📦 `mcp-builder`

Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).

**Location**: `.claude/skills/mcp-builder/SKILL.md`

### 📚 `threejs`

Build immersive 3D web experiences with Three.js - WebGL/WebGPU library for scenes, cameras, geometries, materials, lights, animations, loaders, post-processing, shaders (including node-based TSL), compute, physics, VR/XR, and advanced rendering. Use when creating 3D visualizations, games, interactive graphics, data viz, product configurators, architectural walkthroughs, or WebGL/WebGPU applications. Covers OrbitControls, GLTF/FBX loading, PBR materials, shadow mapping, post-processing effects (bloom, SSAO, SSR), custom shaders, instancing, LOD, animation systems, and WebXR.

**Location**: `.claude/skills/threejs/SKILL.md`

### 📦 📚 `ui-styling`

Create beautiful, accessible user interfaces with shadcn/ui components (built on Radix UI + Tailwind), Tailwind CSS utility-first styling, and canvas-based visual designs. Use when building user interfaces, implementing design systems, creating responsive layouts, adding accessible components (dialogs, dropdowns, forms, tables), customizing themes and colors, implementing dark mode, generating visual designs and posters, or establishing consistent styling patterns across applications.

**Location**: `.claude/skills/ui-styling/SKILL.md`

## Infrastructure & DevOps

### 📦 📚 `devops`

Deploy and manage cloud infrastructure on Cloudflare (Workers, R2, D1, KV, Pages, Durable Objects, Browser Rendering), Docker containers, and Google Cloud Platform (Compute Engine, GKE, Cloud Run, App Engine, Cloud Storage). Use when deploying serverless functions to the edge, configuring edge computing solutions, managing Docker containers and images, setting up CI/CD pipelines, optimizing cloud infrastructure costs, implementing global caching strategies, working with cloud databases, or building cloud-native applications.

**Location**: `.claude/skills/devops/SKILL.md`

## Multimedia & Processing

### 📦 📚 `chrome-devtools`

Browser automation, debugging, and performance analysis using Puppeteer CLI scripts. Use for automating browsers, taking screenshots, analyzing performance, monitoring network traffic, web scraping, form automation, and JavaScript debugging.

**Location**: `.claude/skills/chrome-devtools/SKILL.md`

### 📦 `document-skills/docx`

Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. When Claude needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks

**Location**: `.claude/skills/document-skills/docx/SKILL.md`

### 📦 `document-skills/pdf`

Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. When Claude needs to fill in a PDF form or programmatically process, generate, or analyze PDF documents at scale.

**Location**: `.claude/skills/document-skills/pdf/SKILL.md`

### 📦 `document-skills/pptx`

Presentation creation, editing, and analysis. When Claude needs to work with presentations (.pptx files) for: (1) Creating new presentations, (2) Modifying or editing content, (3) Working with layouts, (4) Adding comments or speaker notes, or any other presentation tasks

**Location**: `.claude/skills/document-skills/pptx/SKILL.md`

### `document-skills/xlsx`

Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization. When Claude needs to work with spreadsheets (.xlsx, .xlsm, .csv, .tsv, etc) for: (1) Creating new spreadsheets with formulas and formatting, (2) Reading or analyzing data, (3) Modify existing spreadsheets while preserving formulas, (4) Data analysis and visualization in spreadsheets, or (5) Recalculating formulas

**Location**: `.claude/skills/document-skills/xlsx/SKILL.md`

### 📦 📚 `media-processing`

Process multimedia files with FFmpeg (video/audio encoding, conversion, streaming, filtering, hardware acceleration), ImageMagick (image manipulation, format conversion, batch processing, effects, composition), and RMBG (AI-powered background removal). Use when converting media formats, encoding videos with specific codecs (H.264, H.265, VP9), resizing/cropping images, removing backgrounds from images, extracting audio from video, applying filters and effects, optimizing file sizes, creating streaming manifests (HLS/DASH), generating thumbnails, batch processing images, creating composite images, or implementing media processing pipelines. Supports 100+ formats, hardware acceleration (NVENC, QSV), and complex filtergraphs.

**Location**: `.claude/skills/media-processing/SKILL.md`

## Utilities & Helpers

### 📚 `code-review`

Use when receiving code review feedback (especially if unclear or technically questionable), when completing tasks or major features requiring review before proceeding, or before making any completion/success claims. Covers three practices - receiving feedback with technical rigor over performative agreement, requesting reviews via code-reviewer subagent, and verification gates requiring evidence before any status claims. Essential for subagent-driven development, pull requests, and preventing false completion claims.

**Location**: `.claude/skills/code-review/SKILL.md`

### 📦 📚 `debugging`

Systematic debugging framework ensuring root cause investigation before fixes. Includes four-phase debugging process, backward call stack tracing, multi-layer validation, and verification protocols. Use when encountering bugs, test failures, unexpected behavior, performance issues, or before claiming work complete. Prevents random fixes, masks over symptoms, and false completion claims.

**Location**: `.claude/skills/debugging/SKILL.md`

### 📚 `planning`

Use when you need to plan technical solutions that are scalable, secure, and maintainable.

**Location**: `.claude/skills/planning/SKILL.md`

### 📚 `problem-solving`

Apply systematic problem-solving techniques for complexity spirals (simplification cascades), innovation blocks (collision-zone thinking), recurring patterns (meta-pattern recognition), assumption constraints (inversion exercise), scale uncertainty (scale game), and dispatch when stuck. Techniques derived from Microsoft Amplifier project patterns adapted for immediate application.

**Location**: `.claude/skills/problem-solving/SKILL.md`

### `research`

Use when you need to research, analyze, and plan technical solutions that are scalable, secure, and maintainable.

**Location**: `.claude/skills/research/SKILL.md`

### 📦 📚 `sequential-thinking`

Apply structured, reflective problem-solving for complex tasks requiring multi-step analysis, revision capability, and hypothesis verification. Use for complex problem decomposition, adaptive planning, analysis needing course correction, problems with unclear scope, multi-step solutions, and hypothesis-driven work.

**Location**: `.claude/skills/sequential-thinking/SKILL.md`
````

## File: guide/SKILLS.yaml
````yaml
metadata:
  title: Skills Catalog
  description: Auto-generated catalog of all available skills in ClaudeKit Engineer
  last_updated: '2025-11-27'
  total_skills: 33
categories:
  ai-ml: AI & Machine Learning
  frontend: Frontend & Design
  backend: Backend Development
  infrastructure: Infrastructure & DevOps
  database: Database & Storage
  dev-tools: Development Tools
  multimedia: Multimedia & Processing
  frameworks: Frameworks & Platforms
  utilities: Utilities & Helpers
  other: Other
legend:
  has_scripts: 📦 Has executable scripts
  has_references: 📚 Has reference documentation
skills:
  frontend:
  - name: aesthetic
    path: aesthetic/SKILL.md
    description: Create aesthetically beautiful interfaces following proven design
      principles. Use when building UI/UX, analyzing designs from inspiration sites,
      generating design images with ai-multimodal, implementing visual hierarchy and
      color theory, adding micro-interactions, or creating design documentation. Includes
      workflows for capturing and analyzing inspiration screenshots with chrome-devtools
      and ai-multimodal, iterative design image generation until aesthetic standards
      are met, and comprehensive design system guidance covering BEAUTIFUL (aesthetic
      principles), RIGHT (functionality/accessibility), SATISFYING (micro-interactions),
      and PEAK (storytelling) stages. Integrates with chrome-devtools, ai-multimodal,
      media-processing, ui-styling, and web-frameworks skills.
    category: frontend
    has_scripts: false
    has_references: true
  - name: frontend-design
    path: frontend-design/SKILL.md
    description: Create distinctive, production-grade frontend interfaces with high
      design quality. Use this skill when the user asks to build web components, pages,
      or applications, OR when they provide screenshots/images/designs to replicate
      or draw inspiration from. For screenshot inputs, extracts design guidelines
      first using ai-multimodal analysis, then implements code following those guidelines.
      Generates creative, polished code that avoids generic AI aesthetics.
    category: frontend
    has_scripts: false
    has_references: true
  - name: frontend-development
    path: frontend-development/SKILL.md
    description: Frontend development guidelines for React/TypeScript applications.
      Modern patterns including Suspense, lazy loading, useSuspenseQuery, file organization
      with features directory, MUI v7 styling, TanStack Router, performance optimization,
      and TypeScript best practices. Use when creating components, pages, features,
      fetching data, styling, routing, or working with frontend code.
    category: frontend
    has_scripts: false
    has_references: false
  - name: mcp-builder
    path: mcp-builder/SKILL.md
    description: Guide for creating high-quality MCP (Model Context Protocol) servers
      that enable LLMs to interact with external services through well-designed tools.
      Use when building MCP servers to integrate external APIs or services, whether
      in Python (FastMCP) or Node/TypeScript (MCP SDK).
    category: frontend
    has_scripts: true
    has_references: false
  - name: threejs
    path: threejs/SKILL.md
    description: Build immersive 3D web experiences with Three.js - WebGL/WebGPU library
      for scenes, cameras, geometries, materials, lights, animations, loaders, post-processing,
      shaders (including node-based TSL), compute, physics, VR/XR, and advanced rendering.
      Use when creating 3D visualizations, games, interactive graphics, data viz,
      product configurators, architectural walkthroughs, or WebGL/WebGPU applications.
      Covers OrbitControls, GLTF/FBX loading, PBR materials, shadow mapping, post-processing
      effects (bloom, SSAO, SSR), custom shaders, instancing, LOD, animation systems,
      and WebXR.
    category: frontend
    has_scripts: false
    has_references: true
  - name: ui-styling
    path: ui-styling/SKILL.md
    description: Create beautiful, accessible user interfaces with shadcn/ui components
      (built on Radix UI + Tailwind), Tailwind CSS utility-first styling, and canvas-based
      visual designs. Use when building user interfaces, implementing design systems,
      creating responsive layouts, adding accessible components (dialogs, dropdowns,
      forms, tables), customizing themes and colors, implementing dark mode, generating
      visual designs and posters, or establishing consistent styling patterns across
      applications.
    category: frontend
    has_scripts: true
    has_references: true
  ai-ml:
  - name: ai-multimodal
    path: ai-multimodal/SKILL.md
    description: Process and generate multimedia content using Google Gemini API.
      Capabilities include analyze audio files (transcription with timestamps, summarization,
      speech understanding, music/sound analysis up to 9.5 hours), understand images
      (captioning, object detection, OCR, visual Q&A, segmentation), process videos
      (scene detection, Q&A, temporal analysis, YouTube URLs, up to 6 hours), extract
      from documents (PDF tables, forms, charts, diagrams, multi-page), generate images
      (text-to-image with Imagen 4, editing, composition, refinement), generate videos
      (text-to-video with Veo 3, 8-second clips with native audio). Use when working
      with audio/video files, analyzing images or screenshots, processing PDF documents,
      extracting structured data from media, creating images/videos from text prompts,
      or implementing multimodal AI features. Supports Gemini 3/2.5, Imagen 4, and
      Veo 3 models with context windows up to 2M tokens.
    category: ai-ml
    has_scripts: true
    has_references: true
  - name: google-adk-python
    path: google-adk-python/SKILL.md
    description: You are an expert guide for Google's Agent Development Kit (ADK)
      Python - an open-source, code-first toolkit for building, evaluating, and deploying
      AI agents.
    category: ai-ml
    has_scripts: false
    has_references: false
  backend:
  - name: backend-development
    path: backend-development/SKILL.md
    description: Build robust backend systems with modern technologies (Node.js, Python,
      Go, Rust), frameworks (NestJS, FastAPI, Django), databases (PostgreSQL, MongoDB,
      Redis), APIs (REST, GraphQL, gRPC), authentication (OAuth 2.1, JWT), testing
      strategies, security best practices (OWASP Top 10), performance optimization,
      scalability patterns (microservices, caching, sharding), DevOps practices (Docker,
      Kubernetes, CI/CD), and monitoring. Use when designing APIs, implementing authentication,
      optimizing database queries, setting up CI/CD pipelines, handling security vulnerabilities,
      building microservices, or developing production-ready backend systems.
    category: backend
    has_scripts: false
    has_references: true
  - name: better-auth
    path: better-auth/SKILL.md
    description: Implement authentication and authorization with Better Auth - a framework-agnostic
      TypeScript authentication framework. Features include email/password authentication
      with verification, OAuth providers (Google, GitHub, Discord, etc.), two-factor
      authentication (TOTP, SMS), passkeys/WebAuthn support, session management, role-based
      access control (RBAC), rate limiting, and database adapters. Use when adding
      authentication to applications, implementing OAuth flows, setting up 2FA/MFA,
      managing user sessions, configuring authorization rules, or building secure
      authentication systems for web applications.
    category: backend
    has_scripts: true
    has_references: true
  - name: payment-integration
    path: payment-integration/SKILL.md
    description: Implement payment integrations with SePay (Vietnamese payment gateway
      with VietQR, bank transfers, cards) and Polar (global SaaS monetization platform
      with subscriptions, usage-based billing, automated benefits). Use when integrating
      payment processing, implementing checkout flows, managing subscriptions, handling
      webhooks, processing bank transfers, generating QR codes, automating benefit
      delivery, or building billing systems. Supports authentication (API keys, OAuth2),
      product management, customer portals, tax compliance (Polar as MoR), and comprehensive
      SDK integrations (Node.js, PHP, Python, Go, Laravel, Next.js).
    category: backend
    has_scripts: true
    has_references: true
  multimedia:
  - name: chrome-devtools
    path: chrome-devtools/SKILL.md
    description: Browser automation, debugging, and performance analysis using Puppeteer
      CLI scripts. Use for automating browsers, taking screenshots, analyzing performance,
      monitoring network traffic, web scraping, form automation, and JavaScript debugging.
    category: multimedia
    has_scripts: true
    has_references: true
  - name: document-skills/docx
    path: document-skills/docx/SKILL.md
    description: 'Comprehensive document creation, editing, and analysis with support
      for tracked changes, comments, formatting preservation, and text extraction.
      When Claude needs to work with professional documents (.docx files) for: (1)
      Creating new documents, (2) Modifying or editing content, (3) Working with tracked
      changes, (4) Adding comments, or any other document tasks'
    category: multimedia
    has_scripts: true
    has_references: false
  - name: document-skills/pdf
    path: document-skills/pdf/SKILL.md
    description: Comprehensive PDF manipulation toolkit for extracting text and tables,
      creating new PDFs, merging/splitting documents, and handling forms. When Claude
      needs to fill in a PDF form or programmatically process, generate, or analyze
      PDF documents at scale.
    category: multimedia
    has_scripts: true
    has_references: false
  - name: document-skills/pptx
    path: document-skills/pptx/SKILL.md
    description: 'Presentation creation, editing, and analysis. When Claude needs
      to work with presentations (.pptx files) for: (1) Creating new presentations,
      (2) Modifying or editing content, (3) Working with layouts, (4) Adding comments
      or speaker notes, or any other presentation tasks'
    category: multimedia
    has_scripts: true
    has_references: false
  - name: document-skills/xlsx
    path: document-skills/xlsx/SKILL.md
    description: 'Comprehensive spreadsheet creation, editing, and analysis with support
      for formulas, formatting, data analysis, and visualization. When Claude needs
      to work with spreadsheets (.xlsx, .xlsm, .csv, .tsv, etc) for: (1) Creating
      new spreadsheets with formulas and formatting, (2) Reading or analyzing data,
      (3) Modify existing spreadsheets while preserving formulas, (4) Data analysis
      and visualization in spreadsheets, or (5) Recalculating formulas'
    category: multimedia
    has_scripts: false
    has_references: false
  - name: media-processing
    path: media-processing/SKILL.md
    description: Process multimedia files with FFmpeg (video/audio encoding, conversion,
      streaming, filtering, hardware acceleration), ImageMagick (image manipulation,
      format conversion, batch processing, effects, composition), and RMBG (AI-powered
      background removal). Use when converting media formats, encoding videos with
      specific codecs (H.264, H.265, VP9), resizing/cropping images, removing backgrounds
      from images, extracting audio from video, applying filters and effects, optimizing
      file sizes, creating streaming manifests (HLS/DASH), generating thumbnails,
      batch processing images, creating composite images, or implementing media processing
      pipelines. Supports 100+ formats, hardware acceleration (NVENC, QSV), and complex
      filtergraphs.
    category: multimedia
    has_scripts: true
    has_references: true
  dev-tools:
  - name: claude-code
    path: claude-code/SKILL.md
    description: Activate when users ask about Claude Code installation, slash commands
      (/cook, /plan, /fix, /test, /docs, /design, /git), creating/managing Agent Skills,
      configuring MCP servers, setting up hooks/plugins, IDE integration (VS Code,
      JetBrains), CI/CD workflows, enterprise deployment (SSO, RBAC, sandboxing),
      troubleshooting authentication/performance issues, or advanced features (extended
      thinking, caching, checkpointing).
    category: dev-tools
    has_scripts: false
    has_references: true
  - name: docs-seeker
    path: docs-seeker/SKILL.md
    description: 'Search technical documentation using executable scripts to detect
      query type, fetch from llms.txt sources (context7.com), and analyze results.
      Use when user needs: (1) Topic-specific documentation (features/components/concepts),
      (2) Library/framework documentation, (3) GitHub repository analysis, (4) Documentation
      discovery with automated agent distribution strategy'
    category: dev-tools
    has_scripts: true
    has_references: true
  - name: mcp-management
    path: mcp-management/SKILL.md
    description: Manage Model Context Protocol (MCP) servers - discover, analyze,
      and execute tools/prompts/resources from configured MCP servers. Use when working
      with MCP integrations, need to discover available MCP capabilities, filter MCP
      tools for specific tasks, execute MCP tools programmatically, access MCP prompts/resources,
      or implement MCP client functionality. Supports intelligent tool selection,
      multi-server management, and context-efficient capability discovery.
    category: dev-tools
    has_scripts: true
    has_references: true
  - name: repomix
    path: repomix/SKILL.md
    description: Package entire code repositories into single AI-friendly files using
      Repomix. Capabilities include pack codebases with customizable include/exclude
      patterns, generate multiple output formats (XML, Markdown, plain text), preserve
      file structure and context, optimize for AI consumption with token counting,
      filter by file types and directories, add custom headers and summaries. Use
      when packaging codebases for AI analysis, creating repository snapshots for
      LLM context, analyzing third-party libraries, preparing for security audits,
      generating documentation context, or evaluating unfamiliar codebases.
    category: dev-tools
    has_scripts: true
    has_references: true
  - name: skill-creator
    path: skill-creator/SKILL.md
    description: Guide for creating effective skills, adding skill references, skill
      scripts or optimizing existing skills. This skill should be used when users
      want to create a new skill (or update an existing skill) that extends Claude's
      capabilities with specialized knowledge, workflows, frameworks, libraries or
      plugins usage, or API and tool integrations.
    category: dev-tools
    has_scripts: true
    has_references: false
  utilities:
  - name: code-review
    path: code-review/SKILL.md
    description: Use when receiving code review feedback (especially if unclear or
      technically questionable), when completing tasks or major features requiring
      review before proceeding, or before making any completion/success claims. Covers
      three practices - receiving feedback with technical rigor over performative
      agreement, requesting reviews via code-reviewer subagent, and verification gates
      requiring evidence before any status claims. Essential for subagent-driven development,
      pull requests, and preventing false completion claims.
    category: utilities
    has_scripts: false
    has_references: true
  - name: debugging
    path: debugging/SKILL.md
    description: Systematic debugging framework ensuring root cause investigation
      before fixes. Includes four-phase debugging process, backward call stack tracing,
      multi-layer validation, and verification protocols. Use when encountering bugs,
      test failures, unexpected behavior, performance issues, or before claiming work
      complete. Prevents random fixes, masks over symptoms, and false completion claims.
    category: utilities
    has_scripts: true
    has_references: true
  - name: planning
    path: planning/SKILL.md
    description: Use when you need to plan technical solutions that are scalable,
      secure, and maintainable.
    category: utilities
    has_scripts: false
    has_references: true
  - name: problem-solving
    path: problem-solving/SKILL.md
    description: Apply systematic problem-solving techniques for complexity spirals
      (simplification cascades), innovation blocks (collision-zone thinking), recurring
      patterns (meta-pattern recognition), assumption constraints (inversion exercise),
      scale uncertainty (scale game), and dispatch when stuck. Techniques derived
      from Microsoft Amplifier project patterns adapted for immediate application.
    category: utilities
    has_scripts: false
    has_references: true
  - name: research
    path: research/SKILL.md
    description: Use when you need to research, analyze, and plan technical solutions
      that are scalable, secure, and maintainable.
    category: utilities
    has_scripts: false
    has_references: false
  - name: sequential-thinking
    path: sequential-thinking/SKILL.md
    description: Apply structured, reflective problem-solving for complex tasks requiring
      multi-step analysis, revision capability, and hypothesis verification. Use for
      complex problem decomposition, adaptive planning, analysis needing course correction,
      problems with unclear scope, multi-step solutions, and hypothesis-driven work.
    category: utilities
    has_scripts: true
    has_references: true
  database:
  - name: databases
    path: databases/SKILL.md
    description: Work with MongoDB (document database, BSON documents, aggregation
      pipelines, Atlas cloud) and PostgreSQL (relational database, SQL queries, psql
      CLI, pgAdmin). Use when designing database schemas, writing queries and aggregations,
      optimizing indexes for performance, performing database migrations, configuring
      replication and sharding, implementing backup and restore strategies, managing
      database users and permissions, analyzing query performance, or administering
      production databases.
    category: database
    has_scripts: true
    has_references: true
  infrastructure:
  - name: devops
    path: devops/SKILL.md
    description: Deploy and manage cloud infrastructure on Cloudflare (Workers, R2,
      D1, KV, Pages, Durable Objects, Browser Rendering), Docker containers, and Google
      Cloud Platform (Compute Engine, GKE, Cloud Run, App Engine, Cloud Storage).
      Use when deploying serverless functions to the edge, configuring edge computing
      solutions, managing Docker containers and images, setting up CI/CD pipelines,
      optimizing cloud infrastructure costs, implementing global caching strategies,
      working with cloud databases, or building cloud-native applications.
    category: infrastructure
    has_scripts: true
    has_references: true
  frameworks:
  - name: mobile-development
    path: mobile-development/SKILL.md
    description: Build modern mobile applications with React Native, Flutter, Swift/SwiftUI,
      and Kotlin/Jetpack Compose. Covers mobile-first design principles, performance
      optimization (battery, memory, network), offline-first architecture, platform-specific
      guidelines (iOS HIG, Material Design), testing strategies, security best practices,
      accessibility, app store deployment, and mobile development mindset. Use when
      building mobile apps, implementing mobile UX patterns, optimizing for mobile
      constraints, or making native vs cross-platform decisions.
    category: frameworks
    has_scripts: false
    has_references: true
  - name: shopify
    path: shopify/SKILL.md
    description: Build Shopify applications, extensions, and themes using GraphQL/REST
      APIs, Shopify CLI, Polaris UI components, and Liquid templating. Capabilities
      include app development with OAuth authentication, checkout UI extensions for
      customizing checkout flow, admin UI extensions for dashboard integration, POS
      extensions for retail, theme development with Liquid, webhook management, billing
      API integration, product/order/customer management. Use when building Shopify
      apps, implementing checkout customizations, creating admin interfaces, developing
      themes, integrating payment processing, managing store data via APIs, or extending
      Shopify functionality.
    category: frameworks
    has_scripts: true
    has_references: true
  - name: web-frameworks
    path: web-frameworks/SKILL.md
    description: Build modern full-stack web applications with Next.js (App Router,
      Server Components, RSC, PPR, SSR, SSG, ISR), Turborepo (monorepo management,
      task pipelines, remote caching, parallel execution), and RemixIcon (3100+ SVG
      icons in outlined/filled styles). Use when creating React applications, implementing
      server-side rendering, setting up monorepos with multiple packages, optimizing
      build performance and caching strategies, adding icon libraries, managing shared
      dependencies, or working with TypeScript full-stack projects.
    category: frameworks
    has_scripts: true
    has_references: true
````

## File: public/placeholder.svg
````
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" fill="none"><rect width="1200" height="1200" fill="#EAEAEA" rx="3"/><g opacity=".5"><g opacity=".5"><path fill="#FAFAFA" d="M600.709 736.5c-75.454 0-136.621-61.167-136.621-136.62 0-75.454 61.167-136.621 136.621-136.621 75.453 0 136.62 61.167 136.62 136.621 0 75.453-61.167 136.62-136.62 136.62Z"/><path stroke="#C9C9C9" stroke-width="2.418" d="M600.709 736.5c-75.454 0-136.621-61.167-136.621-136.62 0-75.454 61.167-136.621 136.621-136.621 75.453 0 136.62 61.167 136.62 136.621 0 75.453-61.167 136.62-136.62 136.62Z"/></g><path stroke="url(#a)" stroke-width="2.418" d="M0-1.209h553.581" transform="scale(1 -1) rotate(45 1163.11 91.165)"/><path stroke="url(#b)" stroke-width="2.418" d="M404.846 598.671h391.726"/><path stroke="url(#c)" stroke-width="2.418" d="M599.5 795.742V404.017"/><path stroke="url(#d)" stroke-width="2.418" d="m795.717 796.597-391.441-391.44"/><path fill="#fff" d="M600.709 656.704c-31.384 0-56.825-25.441-56.825-56.824 0-31.384 25.441-56.825 56.825-56.825 31.383 0 56.824 25.441 56.824 56.825 0 31.383-25.441 56.824-56.824 56.824Z"/><g clip-path="url(#e)"><path fill="#666" fill-rule="evenodd" d="M616.426 586.58h-31.434v16.176l3.553-3.554.531-.531h9.068l.074-.074 8.463-8.463h2.565l7.18 7.181V586.58Zm-15.715 14.654 3.698 3.699 1.283 1.282-2.565 2.565-1.282-1.283-5.2-5.199h-6.066l-5.514 5.514-.073.073v2.876a2.418 2.418 0 0 0 2.418 2.418h26.598a2.418 2.418 0 0 0 2.418-2.418v-8.317l-8.463-8.463-7.181 7.181-.071.072Zm-19.347 5.442v4.085a6.045 6.045 0 0 0 6.046 6.045h26.598a6.044 6.044 0 0 0 6.045-6.045v-7.108l1.356-1.355-1.282-1.283-.074-.073v-17.989h-38.689v23.43l-.146.146.146.147Z" clip-rule="evenodd"/></g><path stroke="#C9C9C9" stroke-width="2.418" d="M600.709 656.704c-31.384 0-56.825-25.441-56.825-56.824 0-31.384 25.441-56.825 56.825-56.825 31.383 0 56.824 25.441 56.824 56.825 0 31.383-25.441 56.824-56.824 56.824Z"/></g><defs><linearGradient id="a" x1="554.061" x2="-.48" y1=".083" y2=".087" gradientUnits="userSpaceOnUse"><stop stop-color="#C9C9C9" stop-opacity="0"/><stop offset=".208" stop-color="#C9C9C9"/><stop offset=".792" stop-color="#C9C9C9"/><stop offset="1" stop-color="#C9C9C9" stop-opacity="0"/></linearGradient><linearGradient id="b" x1="796.912" x2="404.507" y1="599.963" y2="599.965" gradientUnits="userSpaceOnUse"><stop stop-color="#C9C9C9" stop-opacity="0"/><stop offset=".208" stop-color="#C9C9C9"/><stop offset=".792" stop-color="#C9C9C9"/><stop offset="1" stop-color="#C9C9C9" stop-opacity="0"/></linearGradient><linearGradient id="c" x1="600.792" x2="600.794" y1="403.677" y2="796.082" gradientUnits="userSpaceOnUse"><stop stop-color="#C9C9C9" stop-opacity="0"/><stop offset=".208" stop-color="#C9C9C9"/><stop offset=".792" stop-color="#C9C9C9"/><stop offset="1" stop-color="#C9C9C9" stop-opacity="0"/></linearGradient><linearGradient id="d" x1="404.85" x2="796.972" y1="403.903" y2="796.02" gradientUnits="userSpaceOnUse"><stop stop-color="#C9C9C9" stop-opacity="0"/><stop offset=".208" stop-color="#C9C9C9"/><stop offset=".792" stop-color="#C9C9C9"/><stop offset="1" stop-color="#C9C9C9" stop-opacity="0"/></linearGradient><clipPath id="e"><path fill="#fff" d="M581.364 580.535h38.689v38.689h-38.689z"/></clipPath></defs></svg>
````

## File: public/robots.txt
````
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Twitterbot
Allow: /

User-agent: facebookexternalhit
Allow: /

User-agent: *
Allow: /
````

## File: scripts/prepare-release-assets.cjs
````
#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * Generate metadata.json aligned with the package version and
 * bundle the release archive ahead of the semantic-release publish step.
 */
(function main() {
  const version = process.argv[2];

  if (!version) {
    console.error('✗ Missing required version argument for prepare-release-assets');
    process.exit(1);
  }

  const projectRoot = process.cwd();
  const packageJsonPath = path.join(projectRoot, 'package.json');
  const claudeDir = path.join(projectRoot, '.claude');
  const metadataPath = path.join(claudeDir, 'metadata.json');
  const distDir = path.join(projectRoot, 'dist');
  const archivePath = path.join(distDir, 'claudekit-engineer.zip');

  try {
    if (!fs.existsSync(packageJsonPath)) {
      throw new Error('package.json not found');
    }

    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

    if (packageJson.version !== version) {
      console.warn(
        `⚠️ package.json version (${packageJson.version}) does not match semantic-release version (${version}).`
      );
    }

    const requiredFields = ['name', 'description', 'repository'];
    const missingFields = requiredFields.filter((field) => !packageJson[field]);

    if (missingFields.length > 0) {
      throw new Error(`Missing required fields in package.json: ${missingFields.join(', ')}`);
    }

    if (!fs.existsSync(claudeDir)) {
      fs.mkdirSync(claudeDir, { recursive: true });
    }

    const metadata = {
      version: packageJson.version,
      name: packageJson.name,
      description: packageJson.description,
      buildDate: new Date().toISOString(),
      repository: packageJson.repository,
      download: {
        lastDownloadedAt: null,
        downloadedBy: null,
        installCount: 0,
      },
    };

    fs.writeFileSync(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`, 'utf8');
    console.log(`✓ Generated metadata.json with version ${metadata.version}`);

    if (!fs.existsSync(distDir)) {
      fs.mkdirSync(distDir, { recursive: true });
    }

    if (fs.existsSync(archivePath)) {
      fs.unlinkSync(archivePath);
    }

    const archiveTargets = [
      '.claude',
      'plans',
      '.gitignore',
      '.repomixignore',
      '.mcp.json',
      'CLAUDE.md',
    ];

    const existingTargets = archiveTargets.filter((target) => fs.existsSync(path.join(projectRoot, target)));

    if (existingTargets.length === 0) {
      throw new Error('No release assets found to include in archive.');
    }

    const zipCommand = ['zip', '-r', archivePath, ...existingTargets].join(' ');
    execSync(zipCommand, { stdio: 'inherit' });
    console.log(`✓ Prepared ${archivePath}`);
  } catch (error) {
    console.error(`✗ Failed to prepare release assets: ${error.message}`);
    process.exit(1);
  }
})();
````

## File: scripts/send-discord-release.cjs
````
/**
 * Send Release Notification to Discord using Embeds
 *
 * Usage:
 *   node send-discord-release.cjs <type> <webhook-url>
 *
 * Args:
 *   type: 'production' or 'beta'
 *   webhook-url: Discord webhook URL
 */

const fs = require('fs');
const https = require('https');
const { URL } = require('url');

// Parse command line arguments
const releaseType = process.argv[2]; // 'production' or 'beta'
const webhookUrl = process.argv[3];

if (!releaseType || !webhookUrl) {
  console.error('Usage: node send-discord-release.cjs <type> <webhook-url>');
  process.exit(1);
}

// Read CHANGELOG.md and extract the latest release notes
function extractLatestRelease() {
  const changelogPath = 'CHANGELOG.md';

  if (!fs.existsSync(changelogPath)) {
    return {
      version: 'Unknown',
      date: new Date().toISOString().split('T')[0],
      sections: {}
    };
  }

  const content = fs.readFileSync(changelogPath, 'utf8');
  const lines = content.split('\n');

  let version = 'Unknown';
  let date = new Date().toISOString().split('T')[0];
  let collecting = false;
  let currentSection = null;
  const sections = {};

  for (const line of lines) {
    // Match version header: ## 1.15.0 (2025-11-22) or ## [1.15.0](url) (2025-11-22)
    const versionMatch = line.match(/^## \[?(\d+\.\d+\.\d+(?:-beta\.\d+)?)\]?.*?\((\d{4}-\d{2}-\d{2})\)/);
    if (versionMatch) {
      if (!collecting) {
        version = versionMatch[1];
        date = versionMatch[2];
        collecting = true;
        continue;
      } else {
        // Found next version, stop collecting
        break;
      }
    }

    if (!collecting) continue;

    // Match section headers (### Features, ### Bug Fixes, etc.)
    const sectionMatch = line.match(/^### (.+)/);
    if (sectionMatch) {
      currentSection = sectionMatch[1];
      sections[currentSection] = [];
      continue;
    }

    // Collect bullet points
    if (currentSection && line.trim().startsWith('*')) {
      const item = line.trim().substring(1).trim();
      if (item) {
        sections[currentSection].push(item);
      }
    }
  }

  return { version, date, sections };
}

// Create Discord embed
function createEmbed(release) {
  const isBeta = releaseType === 'beta';
  const color = isBeta ? 0xF59E0B : 0x10B981; // Orange for beta, Green for production
  const title = isBeta ? `🧪 Beta Release ${release.version}` : `🚀 Release ${release.version}`;
  const url = `https://github.com/claudekit/claudekit-engineer/releases/tag/v${release.version}`;

  // Map section names to emojis
  const sectionEmojis = {
    'Features': '🚀',
    'Bug Fixes': '🐞',
    'Documentation': '📚',
    'Styles': '💄',
    'Code Refactoring': '♻️',
    'Performance Improvements': '⚡',
    'Tests': '✅',
    'Build System': '🏗️',
    'CI': '👷',
    'Chores': '🔧'
  };

  const fields = [];

  // Add sections as embed fields
  for (const [sectionName, items] of Object.entries(release.sections)) {
    if (items.length === 0) continue;

    const emoji = sectionEmojis[sectionName] || '📌';
    let fieldValue = items.map(item => `• ${item}`).join('\n');

    // Discord field value max is 1024 characters
    if (fieldValue.length > 1024) {
      const truncateAt = fieldValue.lastIndexOf('\n', 1000);
      fieldValue = fieldValue.substring(0, truncateAt) + '\n... *(truncated)*';
    }

    fields.push({
      name: `${emoji} ${sectionName}`,
      value: fieldValue,
      inline: false
    });
  }

  // If no sections found, add a simple message
  if (fields.length === 0) {
    fields.push({
      name: '📋 Release Notes',
      value: 'Release completed successfully. See full changelog on GitHub.',
      inline: false
    });
  }

  const embed = {
    title,
    url,
    color,
    timestamp: new Date().toISOString(),
    footer: {
      text: isBeta ? 'Beta Release • Pre-release' : 'Production Release • Latest'
    },
    fields
  };

  return embed;
}

// Send to Discord
function sendToDiscord(embed) {
  const payload = {
    username: releaseType === 'beta' ? 'Beta Release Bot' : 'Release Bot',
    avatar_url: 'https://github.com/claudekit.png',
    embeds: [embed]
  };

  const url = new URL(webhookUrl);
  const options = {
    hostname: url.hostname,
    path: url.pathname + url.search,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  };

  const req = https.request(options, (res) => {
    let data = '';

    res.on('data', (chunk) => {
      data += chunk;
    });

    res.on('end', () => {
      if (res.statusCode >= 200 && res.statusCode < 300) {
        console.log('✅ Discord notification sent successfully');
      } else {
        console.error(`❌ Discord webhook failed with status ${res.statusCode}`);
        console.error(data);
        process.exit(1);
      }
    });
  });

  req.on('error', (error) => {
    console.error('❌ Error sending Discord notification:', error);
    process.exit(1);
  });

  req.write(JSON.stringify(payload));
  req.end();
}

// Main execution
try {
  const release = extractLatestRelease();
  console.log(`📦 Preparing ${releaseType} release notification for v${release.version}`);

  const embed = createEmbed(release);
  sendToDiscord(embed);
} catch (error) {
  console.error('❌ Error:', error);
  process.exit(1);
}
````

## File: src/components/ui/accordion.tsx
````typescript
import * as React from "react";
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

const Accordion = AccordionPrimitive.Root;

const AccordionItem = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Item>
>(({ className, ...props }, ref) => (
  <AccordionPrimitive.Item ref={ref} className={cn("border-b", className)} {...props} />
));
AccordionItem.displayName = "AccordionItem";

const AccordionTrigger = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Header className="flex">
    <AccordionPrimitive.Trigger
      ref={ref}
      className={cn(
        "flex flex-1 items-center justify-between py-4 font-medium transition-all hover:underline [&[data-state=open]>svg]:rotate-180",
        className,
      )}
      {...props}
    >
      {children}
      <ChevronDown className="h-4 w-4 shrink-0 transition-transform duration-200" />
    </AccordionPrimitive.Trigger>
  </AccordionPrimitive.Header>
));
AccordionTrigger.displayName = AccordionPrimitive.Trigger.displayName;

const AccordionContent = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Content
    ref={ref}
    className="overflow-hidden text-sm transition-all data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down"
    {...props}
  >
    <div className={cn("pb-4 pt-0", className)}>{children}</div>
  </AccordionPrimitive.Content>
));

AccordionContent.displayName = AccordionPrimitive.Content.displayName;

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
````

## File: src/components/ui/alert-dialog.tsx
````typescript
import * as React from "react";
import * as AlertDialogPrimitive from "@radix-ui/react-alert-dialog";

import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";

const AlertDialog = AlertDialogPrimitive.Root;

const AlertDialogTrigger = AlertDialogPrimitive.Trigger;

const AlertDialogPortal = AlertDialogPrimitive.Portal;

const AlertDialogOverlay = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Overlay
    className={cn(
      "fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className,
    )}
    {...props}
    ref={ref}
  />
));
AlertDialogOverlay.displayName = AlertDialogPrimitive.Overlay.displayName;

const AlertDialogContent = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Content>
>(({ className, ...props }, ref) => (
  <AlertDialogPortal>
    <AlertDialogOverlay />
    <AlertDialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
        className,
      )}
      {...props}
    />
  </AlertDialogPortal>
));
AlertDialogContent.displayName = AlertDialogPrimitive.Content.displayName;

const AlertDialogHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col space-y-2 text-center sm:text-left", className)} {...props} />
);
AlertDialogHeader.displayName = "AlertDialogHeader";

const AlertDialogFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className)} {...props} />
);
AlertDialogFooter.displayName = "AlertDialogFooter";

const AlertDialogTitle = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Title ref={ref} className={cn("text-lg font-semibold", className)} {...props} />
));
AlertDialogTitle.displayName = AlertDialogPrimitive.Title.displayName;

const AlertDialogDescription = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Description ref={ref} className={cn("text-sm text-muted-foreground", className)} {...props} />
));
AlertDialogDescription.displayName = AlertDialogPrimitive.Description.displayName;

const AlertDialogAction = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Action>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Action>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Action ref={ref} className={cn(buttonVariants(), className)} {...props} />
));
AlertDialogAction.displayName = AlertDialogPrimitive.Action.displayName;

const AlertDialogCancel = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Cancel>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Cancel>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Cancel
    ref={ref}
    className={cn(buttonVariants({ variant: "outline" }), "mt-2 sm:mt-0", className)}
    {...props}
  />
));
AlertDialogCancel.displayName = AlertDialogPrimitive.Cancel.displayName;

export {
  AlertDialog,
  AlertDialogPortal,
  AlertDialogOverlay,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
};
````

## File: src/components/ui/alert.tsx
````typescript
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const alertVariants = cva(
  "relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        destructive: "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div ref={ref} role="alert" className={cn(alertVariants({ variant }), className)} {...props} />
));
Alert.displayName = "Alert";

const AlertTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h5 ref={ref} className={cn("mb-1 font-medium leading-none tracking-tight", className)} {...props} />
  ),
);
AlertTitle.displayName = "AlertTitle";

const AlertDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("text-sm [&_p]:leading-relaxed", className)} {...props} />
  ),
);
AlertDescription.displayName = "AlertDescription";

export { Alert, AlertTitle, AlertDescription };
````

## File: src/components/ui/aspect-ratio.tsx
````typescript
import * as AspectRatioPrimitive from "@radix-ui/react-aspect-ratio";

const AspectRatio = AspectRatioPrimitive.Root;

export { AspectRatio };
````

## File: src/components/ui/avatar.tsx
````typescript
import * as React from "react";
import * as AvatarPrimitive from "@radix-ui/react-avatar";

import { cn } from "@/lib/utils";

const Avatar = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Root>
>(({ className, ...props }, ref) => (
  <AvatarPrimitive.Root
    ref={ref}
    className={cn("relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full", className)}
    {...props}
  />
));
Avatar.displayName = AvatarPrimitive.Root.displayName;

const AvatarImage = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Image>,
  React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Image>
>(({ className, ...props }, ref) => (
  <AvatarPrimitive.Image ref={ref} className={cn("aspect-square h-full w-full", className)} {...props} />
));
AvatarImage.displayName = AvatarPrimitive.Image.displayName;

const AvatarFallback = React.forwardRef<
  React.ElementRef<typeof AvatarPrimitive.Fallback>,
  React.ComponentPropsWithoutRef<typeof AvatarPrimitive.Fallback>
>(({ className, ...props }, ref) => (
  <AvatarPrimitive.Fallback
    ref={ref}
    className={cn("flex h-full w-full items-center justify-center rounded-full bg-muted", className)}
    {...props}
  />
));
AvatarFallback.displayName = AvatarPrimitive.Fallback.displayName;

export { Avatar, AvatarImage, AvatarFallback };
````

## File: src/components/ui/badge.tsx
````typescript
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
````

## File: src/components/ui/breadcrumb.tsx
````typescript
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { ChevronRight, MoreHorizontal } from "lucide-react";

import { cn } from "@/lib/utils";

const Breadcrumb = React.forwardRef<
  HTMLElement,
  React.ComponentPropsWithoutRef<"nav"> & {
    separator?: React.ReactNode;
  }
>(({ ...props }, ref) => <nav ref={ref} aria-label="breadcrumb" {...props} />);
Breadcrumb.displayName = "Breadcrumb";

const BreadcrumbList = React.forwardRef<HTMLOListElement, React.ComponentPropsWithoutRef<"ol">>(
  ({ className, ...props }, ref) => (
    <ol
      ref={ref}
      className={cn(
        "flex flex-wrap items-center gap-1.5 break-words text-sm text-muted-foreground sm:gap-2.5",
        className,
      )}
      {...props}
    />
  ),
);
BreadcrumbList.displayName = "BreadcrumbList";

const BreadcrumbItem = React.forwardRef<HTMLLIElement, React.ComponentPropsWithoutRef<"li">>(
  ({ className, ...props }, ref) => (
    <li ref={ref} className={cn("inline-flex items-center gap-1.5", className)} {...props} />
  ),
);
BreadcrumbItem.displayName = "BreadcrumbItem";

const BreadcrumbLink = React.forwardRef<
  HTMLAnchorElement,
  React.ComponentPropsWithoutRef<"a"> & {
    asChild?: boolean;
  }
>(({ asChild, className, ...props }, ref) => {
  const Comp = asChild ? Slot : "a";

  return <Comp ref={ref} className={cn("transition-colors hover:text-foreground", className)} {...props} />;
});
BreadcrumbLink.displayName = "BreadcrumbLink";

const BreadcrumbPage = React.forwardRef<HTMLSpanElement, React.ComponentPropsWithoutRef<"span">>(
  ({ className, ...props }, ref) => (
    <span
      ref={ref}
      role="link"
      aria-disabled="true"
      aria-current="page"
      className={cn("font-normal text-foreground", className)}
      {...props}
    />
  ),
);
BreadcrumbPage.displayName = "BreadcrumbPage";

const BreadcrumbSeparator = ({ children, className, ...props }: React.ComponentProps<"li">) => (
  <li role="presentation" aria-hidden="true" className={cn("[&>svg]:size-3.5", className)} {...props}>
    {children ?? <ChevronRight />}
  </li>
);
BreadcrumbSeparator.displayName = "BreadcrumbSeparator";

const BreadcrumbEllipsis = ({ className, ...props }: React.ComponentProps<"span">) => (
  <span
    role="presentation"
    aria-hidden="true"
    className={cn("flex h-9 w-9 items-center justify-center", className)}
    {...props}
  >
    <MoreHorizontal className="h-4 w-4" />
    <span className="sr-only">More</span>
  </span>
);
BreadcrumbEllipsis.displayName = "BreadcrumbElipssis";

export {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
  BreadcrumbEllipsis,
};
````

## File: src/components/ui/button.tsx
````typescript
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
````

## File: src/components/ui/calendar.tsx
````typescript
import * as React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { DayPicker } from "react-day-picker";

import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";

export type CalendarProps = React.ComponentProps<typeof DayPicker>;

function Calendar({ className, classNames, showOutsideDays = true, ...props }: CalendarProps) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn("p-3", className)}
      classNames={{
        months: "flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0",
        month: "space-y-4",
        caption: "flex justify-center pt-1 relative items-center",
        caption_label: "text-sm font-medium",
        nav: "space-x-1 flex items-center",
        nav_button: cn(
          buttonVariants({ variant: "outline" }),
          "h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100",
        ),
        nav_button_previous: "absolute left-1",
        nav_button_next: "absolute right-1",
        table: "w-full border-collapse space-y-1",
        head_row: "flex",
        head_cell: "text-muted-foreground rounded-md w-9 font-normal text-[0.8rem]",
        row: "flex w-full mt-2",
        cell: "h-9 w-9 text-center text-sm p-0 relative [&:has([aria-selected].day-range-end)]:rounded-r-md [&:has([aria-selected].day-outside)]:bg-accent/50 [&:has([aria-selected])]:bg-accent first:[&:has([aria-selected])]:rounded-l-md last:[&:has([aria-selected])]:rounded-r-md focus-within:relative focus-within:z-20",
        day: cn(buttonVariants({ variant: "ghost" }), "h-9 w-9 p-0 font-normal aria-selected:opacity-100"),
        day_range_end: "day-range-end",
        day_selected:
          "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground",
        day_today: "bg-accent text-accent-foreground",
        day_outside:
          "day-outside text-muted-foreground opacity-50 aria-selected:bg-accent/50 aria-selected:text-muted-foreground aria-selected:opacity-30",
        day_disabled: "text-muted-foreground opacity-50",
        day_range_middle: "aria-selected:bg-accent aria-selected:text-accent-foreground",
        day_hidden: "invisible",
        ...classNames,
      }}
      components={{
        IconLeft: ({ ..._props }) => <ChevronLeft className="h-4 w-4" />,
        IconRight: ({ ..._props }) => <ChevronRight className="h-4 w-4" />,
      }}
      {...props}
    />
  );
}
Calendar.displayName = "Calendar";

export { Calendar };
````

## File: src/components/ui/card.tsx
````typescript
import * as React from "react";

import { cn } from "@/lib/utils";

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-lg border bg-card text-card-foreground shadow-sm", className)} {...props} />
));
Card.displayName = "Card";

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />
  ),
);
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3 ref={ref} className={cn("text-2xl font-semibold leading-none tracking-tight", className)} {...props} />
  ),
);
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={cn("text-sm text-muted-foreground", className)} {...props} />
  ),
);
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />,
);
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center p-6 pt-0", className)} {...props} />
  ),
);
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
````

## File: src/components/ui/carousel.tsx
````typescript
import * as React from "react";
import useEmblaCarousel, { type UseEmblaCarouselType } from "embla-carousel-react";
import { ArrowLeft, ArrowRight } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

type CarouselApi = UseEmblaCarouselType[1];
type UseCarouselParameters = Parameters<typeof useEmblaCarousel>;
type CarouselOptions = UseCarouselParameters[0];
type CarouselPlugin = UseCarouselParameters[1];

type CarouselProps = {
  opts?: CarouselOptions;
  plugins?: CarouselPlugin;
  orientation?: "horizontal" | "vertical";
  setApi?: (api: CarouselApi) => void;
};

type CarouselContextProps = {
  carouselRef: ReturnType<typeof useEmblaCarousel>[0];
  api: ReturnType<typeof useEmblaCarousel>[1];
  scrollPrev: () => void;
  scrollNext: () => void;
  canScrollPrev: boolean;
  canScrollNext: boolean;
} & CarouselProps;

const CarouselContext = React.createContext<CarouselContextProps | null>(null);

function useCarousel() {
  const context = React.useContext(CarouselContext);

  if (!context) {
    throw new Error("useCarousel must be used within a <Carousel />");
  }

  return context;
}

const Carousel = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & CarouselProps>(
  ({ orientation = "horizontal", opts, setApi, plugins, className, children, ...props }, ref) => {
    const [carouselRef, api] = useEmblaCarousel(
      {
        ...opts,
        axis: orientation === "horizontal" ? "x" : "y",
      },
      plugins,
    );
    const [canScrollPrev, setCanScrollPrev] = React.useState(false);
    const [canScrollNext, setCanScrollNext] = React.useState(false);

    const onSelect = React.useCallback((api: CarouselApi) => {
      if (!api) {
        return;
      }

      setCanScrollPrev(api.canScrollPrev());
      setCanScrollNext(api.canScrollNext());
    }, []);

    const scrollPrev = React.useCallback(() => {
      api?.scrollPrev();
    }, [api]);

    const scrollNext = React.useCallback(() => {
      api?.scrollNext();
    }, [api]);

    const handleKeyDown = React.useCallback(
      (event: React.KeyboardEvent<HTMLDivElement>) => {
        if (event.key === "ArrowLeft") {
          event.preventDefault();
          scrollPrev();
        } else if (event.key === "ArrowRight") {
          event.preventDefault();
          scrollNext();
        }
      },
      [scrollPrev, scrollNext],
    );

    React.useEffect(() => {
      if (!api || !setApi) {
        return;
      }

      setApi(api);
    }, [api, setApi]);

    React.useEffect(() => {
      if (!api) {
        return;
      }

      onSelect(api);
      api.on("reInit", onSelect);
      api.on("select", onSelect);

      return () => {
        api?.off("select", onSelect);
      };
    }, [api, onSelect]);

    return (
      <CarouselContext.Provider
        value={{
          carouselRef,
          api: api,
          opts,
          orientation: orientation || (opts?.axis === "y" ? "vertical" : "horizontal"),
          scrollPrev,
          scrollNext,
          canScrollPrev,
          canScrollNext,
        }}
      >
        <div
          ref={ref}
          onKeyDownCapture={handleKeyDown}
          className={cn("relative", className)}
          role="region"
          aria-roledescription="carousel"
          {...props}
        >
          {children}
        </div>
      </CarouselContext.Provider>
    );
  },
);
Carousel.displayName = "Carousel";

const CarouselContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    const { carouselRef, orientation } = useCarousel();

    return (
      <div ref={carouselRef} className="overflow-hidden">
        <div
          ref={ref}
          className={cn("flex", orientation === "horizontal" ? "-ml-4" : "-mt-4 flex-col", className)}
          {...props}
        />
      </div>
    );
  },
);
CarouselContent.displayName = "CarouselContent";

const CarouselItem = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    const { orientation } = useCarousel();

    return (
      <div
        ref={ref}
        role="group"
        aria-roledescription="slide"
        className={cn("min-w-0 shrink-0 grow-0 basis-full", orientation === "horizontal" ? "pl-4" : "pt-4", className)}
        {...props}
      />
    );
  },
);
CarouselItem.displayName = "CarouselItem";

const CarouselPrevious = React.forwardRef<HTMLButtonElement, React.ComponentProps<typeof Button>>(
  ({ className, variant = "outline", size = "icon", ...props }, ref) => {
    const { orientation, scrollPrev, canScrollPrev } = useCarousel();

    return (
      <Button
        ref={ref}
        variant={variant}
        size={size}
        className={cn(
          "absolute h-8 w-8 rounded-full",
          orientation === "horizontal"
            ? "-left-12 top-1/2 -translate-y-1/2"
            : "-top-12 left-1/2 -translate-x-1/2 rotate-90",
          className,
        )}
        disabled={!canScrollPrev}
        onClick={scrollPrev}
        {...props}
      >
        <ArrowLeft className="h-4 w-4" />
        <span className="sr-only">Previous slide</span>
      </Button>
    );
  },
);
CarouselPrevious.displayName = "CarouselPrevious";

const CarouselNext = React.forwardRef<HTMLButtonElement, React.ComponentProps<typeof Button>>(
  ({ className, variant = "outline", size = "icon", ...props }, ref) => {
    const { orientation, scrollNext, canScrollNext } = useCarousel();

    return (
      <Button
        ref={ref}
        variant={variant}
        size={size}
        className={cn(
          "absolute h-8 w-8 rounded-full",
          orientation === "horizontal"
            ? "-right-12 top-1/2 -translate-y-1/2"
            : "-bottom-12 left-1/2 -translate-x-1/2 rotate-90",
          className,
        )}
        disabled={!canScrollNext}
        onClick={scrollNext}
        {...props}
      >
        <ArrowRight className="h-4 w-4" />
        <span className="sr-only">Next slide</span>
      </Button>
    );
  },
);
CarouselNext.displayName = "CarouselNext";

export { type CarouselApi, Carousel, CarouselContent, CarouselItem, CarouselPrevious, CarouselNext };
````

## File: src/components/ui/chart.tsx
````typescript
import * as React from "react";
import * as RechartsPrimitive from "recharts";

import { cn } from "@/lib/utils";

// Format: { THEME_NAME: CSS_SELECTOR }
const THEMES = { light: "", dark: ".dark" } as const;

export type ChartConfig = {
  [k in string]: {
    label?: React.ReactNode;
    icon?: React.ComponentType;
  } & ({ color?: string; theme?: never } | { color?: never; theme: Record<keyof typeof THEMES, string> });
};

type ChartContextProps = {
  config: ChartConfig;
};

const ChartContext = React.createContext<ChartContextProps | null>(null);

function useChart() {
  const context = React.useContext(ChartContext);

  if (!context) {
    throw new Error("useChart must be used within a <ChartContainer />");
  }

  return context;
}

const ChartContainer = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & {
    config: ChartConfig;
    children: React.ComponentProps<typeof RechartsPrimitive.ResponsiveContainer>["children"];
  }
>(({ id, className, children, config, ...props }, ref) => {
  const uniqueId = React.useId();
  const chartId = `chart-${id || uniqueId.replace(/:/g, "")}`;

  return (
    <ChartContext.Provider value={{ config }}>
      <div
        data-chart={chartId}
        ref={ref}
        className={cn(
          "flex aspect-video justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-none [&_.recharts-polar-grid_[stroke='#ccc']]:stroke-border [&_.recharts-radial-bar-background-sector]:fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border [&_.recharts-sector[stroke='#fff']]:stroke-transparent [&_.recharts-sector]:outline-none [&_.recharts-surface]:outline-none",
          className,
        )}
        {...props}
      >
        <ChartStyle id={chartId} config={config} />
        <RechartsPrimitive.ResponsiveContainer>{children}</RechartsPrimitive.ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  );
});
ChartContainer.displayName = "Chart";

const ChartStyle = ({ id, config }: { id: string; config: ChartConfig }) => {
  const colorConfig = Object.entries(config).filter(([_, config]) => config.theme || config.color);

  if (!colorConfig.length) {
    return null;
  }

  return (
    <style
      dangerouslySetInnerHTML={{
        __html: Object.entries(THEMES)
          .map(
            ([theme, prefix]) => `
${prefix} [data-chart=${id}] {
${colorConfig
  .map(([key, itemConfig]) => {
    const color = itemConfig.theme?.[theme as keyof typeof itemConfig.theme] || itemConfig.color;
    return color ? `  --color-${key}: ${color};` : null;
  })
  .join("\n")}
}
`,
          )
          .join("\n"),
      }}
    />
  );
};

const ChartTooltip = RechartsPrimitive.Tooltip;

const ChartTooltipContent = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<typeof RechartsPrimitive.Tooltip> &
    React.ComponentProps<"div"> & {
      hideLabel?: boolean;
      hideIndicator?: boolean;
      indicator?: "line" | "dot" | "dashed";
      nameKey?: string;
      labelKey?: string;
    }
>(
  (
    {
      active,
      payload,
      className,
      indicator = "dot",
      hideLabel = false,
      hideIndicator = false,
      label,
      labelFormatter,
      labelClassName,
      formatter,
      color,
      nameKey,
      labelKey,
    },
    ref,
  ) => {
    const { config } = useChart();

    const tooltipLabel = React.useMemo(() => {
      if (hideLabel || !payload?.length) {
        return null;
      }

      const [item] = payload;
      const key = `${labelKey || item.dataKey || item.name || "value"}`;
      const itemConfig = getPayloadConfigFromPayload(config, item, key);
      const value =
        !labelKey && typeof label === "string"
          ? config[label as keyof typeof config]?.label || label
          : itemConfig?.label;

      if (labelFormatter) {
        return <div className={cn("font-medium", labelClassName)}>{labelFormatter(value, payload)}</div>;
      }

      if (!value) {
        return null;
      }

      return <div className={cn("font-medium", labelClassName)}>{value}</div>;
    }, [label, labelFormatter, payload, hideLabel, labelClassName, config, labelKey]);

    if (!active || !payload?.length) {
      return null;
    }

    const nestLabel = payload.length === 1 && indicator !== "dot";

    return (
      <div
        ref={ref}
        className={cn(
          "grid min-w-[8rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl",
          className,
        )}
      >
        {!nestLabel ? tooltipLabel : null}
        <div className="grid gap-1.5">
          {payload.map((item, index) => {
            const key = `${nameKey || item.name || item.dataKey || "value"}`;
            const itemConfig = getPayloadConfigFromPayload(config, item, key);
            const indicatorColor = color || item.payload.fill || item.color;

            return (
              <div
                key={item.dataKey}
                className={cn(
                  "flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 [&>svg]:text-muted-foreground",
                  indicator === "dot" && "items-center",
                )}
              >
                {formatter && item?.value !== undefined && item.name ? (
                  formatter(item.value, item.name, item, index, item.payload)
                ) : (
                  <>
                    {itemConfig?.icon ? (
                      <itemConfig.icon />
                    ) : (
                      !hideIndicator && (
                        <div
                          className={cn("shrink-0 rounded-[2px] border-[--color-border] bg-[--color-bg]", {
                            "h-2.5 w-2.5": indicator === "dot",
                            "w-1": indicator === "line",
                            "w-0 border-[1.5px] border-dashed bg-transparent": indicator === "dashed",
                            "my-0.5": nestLabel && indicator === "dashed",
                          })}
                          style={
                            {
                              "--color-bg": indicatorColor,
                              "--color-border": indicatorColor,
                            } as React.CSSProperties
                          }
                        />
                      )
                    )}
                    <div
                      className={cn(
                        "flex flex-1 justify-between leading-none",
                        nestLabel ? "items-end" : "items-center",
                      )}
                    >
                      <div className="grid gap-1.5">
                        {nestLabel ? tooltipLabel : null}
                        <span className="text-muted-foreground">{itemConfig?.label || item.name}</span>
                      </div>
                      {item.value && (
                        <span className="font-mono font-medium tabular-nums text-foreground">
                          {item.value.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  },
);
ChartTooltipContent.displayName = "ChartTooltip";

const ChartLegend = RechartsPrimitive.Legend;

const ChartLegendContent = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> &
    Pick<RechartsPrimitive.LegendProps, "payload" | "verticalAlign"> & {
      hideIcon?: boolean;
      nameKey?: string;
    }
>(({ className, hideIcon = false, payload, verticalAlign = "bottom", nameKey }, ref) => {
  const { config } = useChart();

  if (!payload?.length) {
    return null;
  }

  return (
    <div
      ref={ref}
      className={cn("flex items-center justify-center gap-4", verticalAlign === "top" ? "pb-3" : "pt-3", className)}
    >
      {payload.map((item) => {
        const key = `${nameKey || item.dataKey || "value"}`;
        const itemConfig = getPayloadConfigFromPayload(config, item, key);

        return (
          <div
            key={item.value}
            className={cn("flex items-center gap-1.5 [&>svg]:h-3 [&>svg]:w-3 [&>svg]:text-muted-foreground")}
          >
            {itemConfig?.icon && !hideIcon ? (
              <itemConfig.icon />
            ) : (
              <div
                className="h-2 w-2 shrink-0 rounded-[2px]"
                style={{
                  backgroundColor: item.color,
                }}
              />
            )}
            {itemConfig?.label}
          </div>
        );
      })}
    </div>
  );
});
ChartLegendContent.displayName = "ChartLegend";

// Helper to extract item config from a payload.
function getPayloadConfigFromPayload(config: ChartConfig, payload: unknown, key: string) {
  if (typeof payload !== "object" || payload === null) {
    return undefined;
  }

  const payloadPayload =
    "payload" in payload && typeof payload.payload === "object" && payload.payload !== null
      ? payload.payload
      : undefined;

  let configLabelKey: string = key;

  if (key in payload && typeof payload[key as keyof typeof payload] === "string") {
    configLabelKey = payload[key as keyof typeof payload] as string;
  } else if (
    payloadPayload &&
    key in payloadPayload &&
    typeof payloadPayload[key as keyof typeof payloadPayload] === "string"
  ) {
    configLabelKey = payloadPayload[key as keyof typeof payloadPayload] as string;
  }

  return configLabelKey in config ? config[configLabelKey] : config[key as keyof typeof config];
}

export { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent, ChartStyle };
````

## File: src/components/ui/checkbox.tsx
````typescript
import * as React from "react";
import * as CheckboxPrimitive from "@radix-ui/react-checkbox";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

const Checkbox = React.forwardRef<
  React.ElementRef<typeof CheckboxPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root>
>(({ className, ...props }, ref) => (
  <CheckboxPrimitive.Root
    ref={ref}
    className={cn(
      "peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
      className,
    )}
    {...props}
  >
    <CheckboxPrimitive.Indicator className={cn("flex items-center justify-center text-current")}>
      <Check className="h-4 w-4" />
    </CheckboxPrimitive.Indicator>
  </CheckboxPrimitive.Root>
));
Checkbox.displayName = CheckboxPrimitive.Root.displayName;

export { Checkbox };
````

## File: src/components/ui/collapsible.tsx
````typescript
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible";

const Collapsible = CollapsiblePrimitive.Root;

const CollapsibleTrigger = CollapsiblePrimitive.CollapsibleTrigger;

const CollapsibleContent = CollapsiblePrimitive.CollapsibleContent;

export { Collapsible, CollapsibleTrigger, CollapsibleContent };
````

## File: src/components/ui/command.tsx
````typescript
import * as React from "react";
import { type DialogProps } from "@radix-ui/react-dialog";
import { Command as CommandPrimitive } from "cmdk";
import { Search } from "lucide-react";

import { cn } from "@/lib/utils";
import { Dialog, DialogContent } from "@/components/ui/dialog";

const Command = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive>
>(({ className, ...props }, ref) => (
  <CommandPrimitive
    ref={ref}
    className={cn(
      "flex h-full w-full flex-col overflow-hidden rounded-md bg-popover text-popover-foreground",
      className,
    )}
    {...props}
  />
));
Command.displayName = CommandPrimitive.displayName;

interface CommandDialogProps extends DialogProps {}

const CommandDialog = ({ children, ...props }: CommandDialogProps) => {
  return (
    <Dialog {...props}>
      <DialogContent className="overflow-hidden p-0 shadow-lg">
        <Command className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group]:not([hidden])_~[cmdk-group]]:pt-0 [&_[cmdk-group]]:px-2 [&_[cmdk-input-wrapper]_svg]:h-5 [&_[cmdk-input-wrapper]_svg]:w-5 [&_[cmdk-input]]:h-12 [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:py-3 [&_[cmdk-item]_svg]:h-5 [&_[cmdk-item]_svg]:w-5">
          {children}
        </Command>
      </DialogContent>
    </Dialog>
  );
};

const CommandInput = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Input>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Input>
>(({ className, ...props }, ref) => (
  <div className="flex items-center border-b px-3" cmdk-input-wrapper="">
    <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
    <CommandPrimitive.Input
      ref={ref}
      className={cn(
        "flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  </div>
));

CommandInput.displayName = CommandPrimitive.Input.displayName;

const CommandList = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.List>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.List
    ref={ref}
    className={cn("max-h-[300px] overflow-y-auto overflow-x-hidden", className)}
    {...props}
  />
));

CommandList.displayName = CommandPrimitive.List.displayName;

const CommandEmpty = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Empty>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Empty>
>((props, ref) => <CommandPrimitive.Empty ref={ref} className="py-6 text-center text-sm" {...props} />);

CommandEmpty.displayName = CommandPrimitive.Empty.displayName;

const CommandGroup = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Group>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Group>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Group
    ref={ref}
    className={cn(
      "overflow-hidden p-1 text-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground",
      className,
    )}
    {...props}
  />
));

CommandGroup.displayName = CommandPrimitive.Group.displayName;

const CommandSeparator = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Separator ref={ref} className={cn("-mx-1 h-px bg-border", className)} {...props} />
));
CommandSeparator.displayName = CommandPrimitive.Separator.displayName;

const CommandItem = React.forwardRef<
  React.ElementRef<typeof CommandPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof CommandPrimitive.Item>
>(({ className, ...props }, ref) => (
  <CommandPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[disabled=true]:pointer-events-none data-[selected='true']:bg-accent data-[selected=true]:text-accent-foreground data-[disabled=true]:opacity-50",
      className,
    )}
    {...props}
  />
));

CommandItem.displayName = CommandPrimitive.Item.displayName;

const CommandShortcut = ({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) => {
  return <span className={cn("ml-auto text-xs tracking-widest text-muted-foreground", className)} {...props} />;
};
CommandShortcut.displayName = "CommandShortcut";

export {
  Command,
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandShortcut,
  CommandSeparator,
};
````

## File: src/components/ui/context-menu.tsx
````typescript
import * as React from "react";
import * as ContextMenuPrimitive from "@radix-ui/react-context-menu";
import { Check, ChevronRight, Circle } from "lucide-react";

import { cn } from "@/lib/utils";

const ContextMenu = ContextMenuPrimitive.Root;

const ContextMenuTrigger = ContextMenuPrimitive.Trigger;

const ContextMenuGroup = ContextMenuPrimitive.Group;

const ContextMenuPortal = ContextMenuPrimitive.Portal;

const ContextMenuSub = ContextMenuPrimitive.Sub;

const ContextMenuRadioGroup = ContextMenuPrimitive.RadioGroup;

const ContextMenuSubTrigger = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.SubTrigger>,
  React.ComponentPropsWithoutRef<typeof ContextMenuPrimitive.SubTrigger> & {
    inset?: boolean;
  }
>(({ className, inset, children, ...props }, ref) => (
  <ContextMenuPrimitive.SubTrigger
    ref={ref}
    className={cn(
      "flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[state=open]:bg-accent data-[state=open]:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
      inset && "pl-8",
      className,
    )}
    {...props}
  >
    {children}
    <ChevronRight className="ml-auto h-4 w-4" />
  </ContextMenuPrimitive.SubTrigger>
));
ContextMenuSubTrigger.displayName = ContextMenuPrimitive.SubTrigger.displayName;

const ContextMenuSubContent = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.SubContent>,
  React.ComponentPropsWithoutRef<typeof ContextMenuPrimitive.SubContent>
>(({ className, ...props }, ref) => (
  <ContextMenuPrimitive.SubContent
    ref={ref}
    className={cn(
      "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
      className,
    )}
    {...props}
  />
));
ContextMenuSubContent.displayName = ContextMenuPrimitive.SubContent.displayName;

const ContextMenuContent = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof ContextMenuPrimitive.Content>
>(({ className, ...props }, ref) => (
  <ContextMenuPrimitive.Portal>
    <ContextMenuPrimitive.Content
      ref={ref}
      className={cn(
        "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md animate-in fade-in-80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
        className,
      )}
      {...props}
    />
  </ContextMenuPrimitive.Portal>
));
ContextMenuContent.displayName = ContextMenuPrimitive.Content.displayName;

const ContextMenuItem = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ContextMenuPrimitive.Item> & {
    inset?: boolean;
  }
>(({ className, inset, ...props }, ref) => (
  <ContextMenuPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 focus:bg-accent focus:text-accent-foreground",
      inset && "pl-8",
      className,
    )}
    {...props}
  />
));
ContextMenuItem.displayName = ContextMenuPrimitive.Item.displayName;

const ContextMenuCheckboxItem = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.CheckboxItem>,
  React.ComponentPropsWithoutRef<typeof ContextMenuPrimitive.CheckboxItem>
>(({ className, children, checked, ...props }, ref) => (
  <ContextMenuPrimitive.CheckboxItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 focus:bg-accent focus:text-accent-foreground",
      className,
    )}
    checked={checked}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <ContextMenuPrimitive.ItemIndicator>
        <Check className="h-4 w-4" />
      </ContextMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </ContextMenuPrimitive.CheckboxItem>
));
ContextMenuCheckboxItem.displayName = ContextMenuPrimitive.CheckboxItem.displayName;

const ContextMenuRadioItem = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.RadioItem>,
  React.ComponentPropsWithoutRef<typeof ContextMenuPrimitive.RadioItem>
>(({ className, children, ...props }, ref) => (
  <ContextMenuPrimitive.RadioItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 focus:bg-accent focus:text-accent-foreground",
      className,
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <ContextMenuPrimitive.ItemIndicator>
        <Circle className="h-2 w-2 fill-current" />
      </ContextMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </ContextMenuPrimitive.RadioItem>
));
ContextMenuRadioItem.displayName = ContextMenuPrimitive.RadioItem.displayName;

const ContextMenuLabel = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof ContextMenuPrimitive.Label> & {
    inset?: boolean;
  }
>(({ className, inset, ...props }, ref) => (
  <ContextMenuPrimitive.Label
    ref={ref}
    className={cn("px-2 py-1.5 text-sm font-semibold text-foreground", inset && "pl-8", className)}
    {...props}
  />
));
ContextMenuLabel.displayName = ContextMenuPrimitive.Label.displayName;

const ContextMenuSeparator = React.forwardRef<
  React.ElementRef<typeof ContextMenuPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof ContextMenuPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <ContextMenuPrimitive.Separator ref={ref} className={cn("-mx-1 my-1 h-px bg-border", className)} {...props} />
));
ContextMenuSeparator.displayName = ContextMenuPrimitive.Separator.displayName;

const ContextMenuShortcut = ({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) => {
  return <span className={cn("ml-auto text-xs tracking-widest text-muted-foreground", className)} {...props} />;
};
ContextMenuShortcut.displayName = "ContextMenuShortcut";

export {
  ContextMenu,
  ContextMenuTrigger,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuCheckboxItem,
  ContextMenuRadioItem,
  ContextMenuLabel,
  ContextMenuSeparator,
  ContextMenuShortcut,
  ContextMenuGroup,
  ContextMenuPortal,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuRadioGroup,
};
````

## File: src/components/ui/dialog.tsx
````typescript
import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";

const Dialog = DialogPrimitive.Root;

const DialogTrigger = DialogPrimitive.Trigger;

const DialogPortal = DialogPrimitive.Portal;

const DialogClose = DialogPrimitive.Close;

const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className,
    )}
    {...props}
  />
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
        className,
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity data-[state=open]:bg-accent data-[state=open]:text-muted-foreground hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;

const DialogHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col space-y-1.5 text-center sm:text-left", className)} {...props} />
);
DialogHeader.displayName = "DialogHeader";

const DialogFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className)} {...props} />
);
DialogFooter.displayName = "DialogFooter";

const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn("text-lg font-semibold leading-none tracking-tight", className)}
    {...props}
  />
));
DialogTitle.displayName = DialogPrimitive.Title.displayName;

const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description ref={ref} className={cn("text-sm text-muted-foreground", className)} {...props} />
));
DialogDescription.displayName = DialogPrimitive.Description.displayName;

export {
  Dialog,
  DialogPortal,
  DialogOverlay,
  DialogClose,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
};
````

## File: src/components/ui/drawer.tsx
````typescript
import * as React from "react";
import { Drawer as DrawerPrimitive } from "vaul";

import { cn } from "@/lib/utils";

const Drawer = ({ shouldScaleBackground = true, ...props }: React.ComponentProps<typeof DrawerPrimitive.Root>) => (
  <DrawerPrimitive.Root shouldScaleBackground={shouldScaleBackground} {...props} />
);
Drawer.displayName = "Drawer";

const DrawerTrigger = DrawerPrimitive.Trigger;

const DrawerPortal = DrawerPrimitive.Portal;

const DrawerClose = DrawerPrimitive.Close;

const DrawerOverlay = React.forwardRef<
  React.ElementRef<typeof DrawerPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DrawerPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DrawerPrimitive.Overlay ref={ref} className={cn("fixed inset-0 z-50 bg-black/80", className)} {...props} />
));
DrawerOverlay.displayName = DrawerPrimitive.Overlay.displayName;

const DrawerContent = React.forwardRef<
  React.ElementRef<typeof DrawerPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DrawerPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DrawerPortal>
    <DrawerOverlay />
    <DrawerPrimitive.Content
      ref={ref}
      className={cn(
        "fixed inset-x-0 bottom-0 z-50 mt-24 flex h-auto flex-col rounded-t-[10px] border bg-background",
        className,
      )}
      {...props}
    >
      <div className="mx-auto mt-4 h-2 w-[100px] rounded-full bg-muted" />
      {children}
    </DrawerPrimitive.Content>
  </DrawerPortal>
));
DrawerContent.displayName = "DrawerContent";

const DrawerHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("grid gap-1.5 p-4 text-center sm:text-left", className)} {...props} />
);
DrawerHeader.displayName = "DrawerHeader";

const DrawerFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("mt-auto flex flex-col gap-2 p-4", className)} {...props} />
);
DrawerFooter.displayName = "DrawerFooter";

const DrawerTitle = React.forwardRef<
  React.ElementRef<typeof DrawerPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DrawerPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DrawerPrimitive.Title
    ref={ref}
    className={cn("text-lg font-semibold leading-none tracking-tight", className)}
    {...props}
  />
));
DrawerTitle.displayName = DrawerPrimitive.Title.displayName;

const DrawerDescription = React.forwardRef<
  React.ElementRef<typeof DrawerPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DrawerPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DrawerPrimitive.Description ref={ref} className={cn("text-sm text-muted-foreground", className)} {...props} />
));
DrawerDescription.displayName = DrawerPrimitive.Description.displayName;

export {
  Drawer,
  DrawerPortal,
  DrawerOverlay,
  DrawerTrigger,
  DrawerClose,
  DrawerContent,
  DrawerHeader,
  DrawerFooter,
  DrawerTitle,
  DrawerDescription,
};
````

## File: src/components/ui/dropdown-menu.tsx
````typescript
import * as React from "react";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { Check, ChevronRight, Circle } from "lucide-react";

import { cn } from "@/lib/utils";

const DropdownMenu = DropdownMenuPrimitive.Root;

const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;

const DropdownMenuGroup = DropdownMenuPrimitive.Group;

const DropdownMenuPortal = DropdownMenuPrimitive.Portal;

const DropdownMenuSub = DropdownMenuPrimitive.Sub;

const DropdownMenuRadioGroup = DropdownMenuPrimitive.RadioGroup;

const DropdownMenuSubTrigger = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.SubTrigger>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.SubTrigger> & {
    inset?: boolean;
  }
>(({ className, inset, children, ...props }, ref) => (
  <DropdownMenuPrimitive.SubTrigger
    ref={ref}
    className={cn(
      "flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[state=open]:bg-accent focus:bg-accent",
      inset && "pl-8",
      className,
    )}
    {...props}
  >
    {children}
    <ChevronRight className="ml-auto h-4 w-4" />
  </DropdownMenuPrimitive.SubTrigger>
));
DropdownMenuSubTrigger.displayName = DropdownMenuPrimitive.SubTrigger.displayName;

const DropdownMenuSubContent = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.SubContent>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.SubContent>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.SubContent
    ref={ref}
    className={cn(
      "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
      className,
    )}
    {...props}
  />
));
DropdownMenuSubContent.displayName = DropdownMenuPrimitive.SubContent.displayName;

const DropdownMenuContent = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
        className,
      )}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
));
DropdownMenuContent.displayName = DropdownMenuPrimitive.Content.displayName;

const DropdownMenuItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item> & {
    inset?: boolean;
  }
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors data-[disabled]:pointer-events-none data-[disabled]:opacity-50 focus:bg-accent focus:text-accent-foreground",
      inset && "pl-8",
      className,
    )}
    {...props}
  />
));
DropdownMenuItem.displayName = DropdownMenuPrimitive.Item.displayName;

const DropdownMenuCheckboxItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.CheckboxItem>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.CheckboxItem>
>(({ className, children, checked, ...props }, ref) => (
  <DropdownMenuPrimitive.CheckboxItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors data-[disabled]:pointer-events-none data-[disabled]:opacity-50 focus:bg-accent focus:text-accent-foreground",
      className,
    )}
    checked={checked}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <Check className="h-4 w-4" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.CheckboxItem>
));
DropdownMenuCheckboxItem.displayName = DropdownMenuPrimitive.CheckboxItem.displayName;

const DropdownMenuRadioItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.RadioItem>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.RadioItem>
>(({ className, children, ...props }, ref) => (
  <DropdownMenuPrimitive.RadioItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors data-[disabled]:pointer-events-none data-[disabled]:opacity-50 focus:bg-accent focus:text-accent-foreground",
      className,
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <Circle className="h-2 w-2 fill-current" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.RadioItem>
));
DropdownMenuRadioItem.displayName = DropdownMenuPrimitive.RadioItem.displayName;

const DropdownMenuLabel = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Label> & {
    inset?: boolean;
  }
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Label
    ref={ref}
    className={cn("px-2 py-1.5 text-sm font-semibold", inset && "pl-8", className)}
    {...props}
  />
));
DropdownMenuLabel.displayName = DropdownMenuPrimitive.Label.displayName;

const DropdownMenuSeparator = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Separator ref={ref} className={cn("-mx-1 my-1 h-px bg-muted", className)} {...props} />
));
DropdownMenuSeparator.displayName = DropdownMenuPrimitive.Separator.displayName;

const DropdownMenuShortcut = ({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) => {
  return <span className={cn("ml-auto text-xs tracking-widest opacity-60", className)} {...props} />;
};
DropdownMenuShortcut.displayName = "DropdownMenuShortcut";

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuGroup,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
};
````

## File: src/components/ui/form.tsx
````typescript
import * as React from "react";
import * as LabelPrimitive from "@radix-ui/react-label";
import { Slot } from "@radix-ui/react-slot";
import { Controller, ControllerProps, FieldPath, FieldValues, FormProvider, useFormContext } from "react-hook-form";

import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";

const Form = FormProvider;

type FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> = {
  name: TName;
};

const FormFieldContext = React.createContext<FormFieldContextValue>({} as FormFieldContextValue);

const FormField = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  ...props
}: ControllerProps<TFieldValues, TName>) => {
  return (
    <FormFieldContext.Provider value={{ name: props.name }}>
      <Controller {...props} />
    </FormFieldContext.Provider>
  );
};

const useFormField = () => {
  const fieldContext = React.useContext(FormFieldContext);
  const itemContext = React.useContext(FormItemContext);
  const { getFieldState, formState } = useFormContext();

  const fieldState = getFieldState(fieldContext.name, formState);

  if (!fieldContext) {
    throw new Error("useFormField should be used within <FormField>");
  }

  const { id } = itemContext;

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  };
};

type FormItemContextValue = {
  id: string;
};

const FormItemContext = React.createContext<FormItemContextValue>({} as FormItemContextValue);

const FormItem = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => {
    const id = React.useId();

    return (
      <FormItemContext.Provider value={{ id }}>
        <div ref={ref} className={cn("space-y-2", className)} {...props} />
      </FormItemContext.Provider>
    );
  },
);
FormItem.displayName = "FormItem";

const FormLabel = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root>
>(({ className, ...props }, ref) => {
  const { error, formItemId } = useFormField();

  return <Label ref={ref} className={cn(error && "text-destructive", className)} htmlFor={formItemId} {...props} />;
});
FormLabel.displayName = "FormLabel";

const FormControl = React.forwardRef<React.ElementRef<typeof Slot>, React.ComponentPropsWithoutRef<typeof Slot>>(
  ({ ...props }, ref) => {
    const { error, formItemId, formDescriptionId, formMessageId } = useFormField();

    return (
      <Slot
        ref={ref}
        id={formItemId}
        aria-describedby={!error ? `${formDescriptionId}` : `${formDescriptionId} ${formMessageId}`}
        aria-invalid={!!error}
        {...props}
      />
    );
  },
);
FormControl.displayName = "FormControl";

const FormDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => {
    const { formDescriptionId } = useFormField();

    return <p ref={ref} id={formDescriptionId} className={cn("text-sm text-muted-foreground", className)} {...props} />;
  },
);
FormDescription.displayName = "FormDescription";

const FormMessage = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, children, ...props }, ref) => {
    const { error, formMessageId } = useFormField();
    const body = error ? String(error?.message) : children;

    if (!body) {
      return null;
    }

    return (
      <p ref={ref} id={formMessageId} className={cn("text-sm font-medium text-destructive", className)} {...props}>
        {body}
      </p>
    );
  },
);
FormMessage.displayName = "FormMessage";

export { useFormField, Form, FormItem, FormLabel, FormControl, FormDescription, FormMessage, FormField };
````

## File: src/components/ui/hover-card.tsx
````typescript
import * as React from "react";
import * as HoverCardPrimitive from "@radix-ui/react-hover-card";

import { cn } from "@/lib/utils";

const HoverCard = HoverCardPrimitive.Root;

const HoverCardTrigger = HoverCardPrimitive.Trigger;

const HoverCardContent = React.forwardRef<
  React.ElementRef<typeof HoverCardPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof HoverCardPrimitive.Content>
>(({ className, align = "center", sideOffset = 4, ...props }, ref) => (
  <HoverCardPrimitive.Content
    ref={ref}
    align={align}
    sideOffset={sideOffset}
    className={cn(
      "z-50 w-64 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
      className,
    )}
    {...props}
  />
));
HoverCardContent.displayName = HoverCardPrimitive.Content.displayName;

export { HoverCard, HoverCardTrigger, HoverCardContent };
````

## File: src/components/ui/input-otp.tsx
````typescript
import * as React from "react";
import { OTPInput, OTPInputContext } from "input-otp";
import { Dot } from "lucide-react";

import { cn } from "@/lib/utils";

const InputOTP = React.forwardRef<React.ElementRef<typeof OTPInput>, React.ComponentPropsWithoutRef<typeof OTPInput>>(
  ({ className, containerClassName, ...props }, ref) => (
    <OTPInput
      ref={ref}
      containerClassName={cn("flex items-center gap-2 has-[:disabled]:opacity-50", containerClassName)}
      className={cn("disabled:cursor-not-allowed", className)}
      {...props}
    />
  ),
);
InputOTP.displayName = "InputOTP";

const InputOTPGroup = React.forwardRef<React.ElementRef<"div">, React.ComponentPropsWithoutRef<"div">>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn("flex items-center", className)} {...props} />,
);
InputOTPGroup.displayName = "InputOTPGroup";

const InputOTPSlot = React.forwardRef<
  React.ElementRef<"div">,
  React.ComponentPropsWithoutRef<"div"> & { index: number }
>(({ index, className, ...props }, ref) => {
  const inputOTPContext = React.useContext(OTPInputContext);
  const { char, hasFakeCaret, isActive } = inputOTPContext.slots[index];

  return (
    <div
      ref={ref}
      className={cn(
        "relative flex h-10 w-10 items-center justify-center border-y border-r border-input text-sm transition-all first:rounded-l-md first:border-l last:rounded-r-md",
        isActive && "z-10 ring-2 ring-ring ring-offset-background",
        className,
      )}
      {...props}
    >
      {char}
      {hasFakeCaret && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="animate-caret-blink h-4 w-px bg-foreground duration-1000" />
        </div>
      )}
    </div>
  );
});
InputOTPSlot.displayName = "InputOTPSlot";

const InputOTPSeparator = React.forwardRef<React.ElementRef<"div">, React.ComponentPropsWithoutRef<"div">>(
  ({ ...props }, ref) => (
    <div ref={ref} role="separator" {...props}>
      <Dot />
    </div>
  ),
);
InputOTPSeparator.displayName = "InputOTPSeparator";

export { InputOTP, InputOTPGroup, InputOTPSlot, InputOTPSeparator };
````

## File: src/components/ui/input.tsx
````typescript
import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";

export { Input };
````

## File: src/components/ui/label.tsx
````typescript
import * as React from "react";
import * as LabelPrimitive from "@radix-ui/react-label";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const labelVariants = cva("text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70");

const Label = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root> & VariantProps<typeof labelVariants>
>(({ className, ...props }, ref) => (
  <LabelPrimitive.Root ref={ref} className={cn(labelVariants(), className)} {...props} />
));
Label.displayName = LabelPrimitive.Root.displayName;

export { Label };
````

## File: src/components/ui/menubar.tsx
````typescript
import * as React from "react";
import * as MenubarPrimitive from "@radix-ui/react-menubar";
import { Check, ChevronRight, Circle } from "lucide-react";

import { cn } from "@/lib/utils";

const MenubarMenu = MenubarPrimitive.Menu;

const MenubarGroup = MenubarPrimitive.Group;

const MenubarPortal = MenubarPrimitive.Portal;

const MenubarSub = MenubarPrimitive.Sub;

const MenubarRadioGroup = MenubarPrimitive.RadioGroup;

const Menubar = React.forwardRef<
  React.ElementRef<typeof MenubarPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof MenubarPrimitive.Root>
>(({ className, ...props }, ref) => (
  <MenubarPrimitive.Root
    ref={ref}
    className={cn("flex h-10 items-center space-x-1 rounded-md border bg-background p-1", className)}
    {...props}
  />
));
Menubar.displayName = MenubarPrimitive.Root.displayName;

const MenubarTrigger = React.forwardRef<
  React.ElementRef<typeof MenubarPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof MenubarPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <MenubarPrimitive.Trigger
    ref={ref}
    className={cn(
      "flex cursor-default select-none items-center rounded-sm px-3 py-1.5 text-sm font-medium outline-none data-[state=open]:bg-accent data-[state=open]:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
      className,
    )}
    {...props}
  />
));
MenubarTrigger.displayName = MenubarPrimitive.Trigger.displayName;

const MenubarSubTrigger = React.forwardRef<
  React.ElementRef<typeof MenubarPrimitive.SubTrigger>,
  React.ComponentPropsWithoutRef<typeof MenubarPrimitive.SubTrigger> & {
    inset?: boolean;
  }
>(({ className, inset, children, ...props }, ref) => (
  <MenubarPrimitive.SubTrigger
    ref={ref}
    className={cn(
      "flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[state=open]:bg-accent data-[state=open]:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
      inset && "pl-8",
      className,
    )}
    {...props}
  >
    {children}
    <ChevronRight className="ml-auto h-4 w-4" />
  </MenubarPrimitive.SubTrigger>
));
MenubarSubTrigger.displayName = MenubarPrimitive.SubTrigger.displayName;

const MenubarSubContent = React.forwardRef<
  React.ElementRef<typeof MenubarPrimitive.SubContent>,
  React.ComponentPropsWithoutRef<typeof MenubarPrimitive.SubContent>
>(({ className, ...props }, ref) => (
  <MenubarPrimitive.SubContent
    ref={ref}
    className={cn(
      "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
      className,
    )}
    {...props}
  />
));
MenubarSubContent.displayName = MenubarPrimitive.SubContent.displayName;

const MenubarContent = React.forwardRef<
  React.ElementRef<typeof MenubarPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof MenubarPrimitive.Content>
>(({ className, align = "start", alignOffset = -4, sideOffset = 8, ...props }, ref) => (
  <MenubarPrimitive.Portal>
    <MenubarPrimitive.Content
      ref={ref}
      align={align}
      alignOffset={alignOffset}
      sideOffset={sideOffset}
      className={cn(
        "z-50 min-w-[12rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
        className,
      )}
      {...props}
    />
  </MenubarPrimitive.Portal>
));
MenubarContent.displayName = MenubarPrimitive.Content.displayName;

const MenubarItem = React.forwardRef<
  React.ElementRef<typeof MenubarPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof MenubarPrimitive.Item> & {
    inset?: boolean;
  }
>(({ className, inset, ...props }, ref) => (
  <MenubarPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 focus:bg-accent focus:text-accent-foreground",
      inset && "pl-8",
      className,
    )}
    {...props}
  />
));
MenubarItem.displayName = MenubarPrimitive.Item.displayName;

const MenubarCheckboxItem = React.forwardRef<
  React.ElementRef<typeof MenubarPrimitive.CheckboxItem>,
  React.ComponentPropsWithoutRef<typeof MenubarPrimitive.CheckboxItem>
>(({ className, children, checked, ...props }, ref) => (
  <MenubarPrimitive.CheckboxItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 focus:bg-accent focus:text-accent-foreground",
      className,
    )}
    checked={checked}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <MenubarPrimitive.ItemIndicator>
        <Check className="h-4 w-4" />
      </MenubarPrimitive.ItemIndicator>
    </span>
    {children}
  </MenubarPrimitive.CheckboxItem>
));
MenubarCheckboxItem.displayName = MenubarPrimitive.CheckboxItem.displayName;

const MenubarRadioItem = React.forwardRef<
  React.ElementRef<typeof MenubarPrimitive.RadioItem>,
  React.ComponentPropsWithoutRef<typeof MenubarPrimitive.RadioItem>
>(({ className, children, ...props }, ref) => (
  <MenubarPrimitive.RadioItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 focus:bg-accent focus:text-accent-foreground",
      className,
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <MenubarPrimitive.ItemIndicator>
        <Circle className="h-2 w-2 fill-current" />
      </MenubarPrimitive.ItemIndicator>
    </span>
    {children}
  </MenubarPrimitive.RadioItem>
));
MenubarRadioItem.displayName = MenubarPrimitive.RadioItem.displayName;

const MenubarLabel = React.forwardRef<
  React.ElementRef<typeof MenubarPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof MenubarPrimitive.Label> & {
    inset?: boolean;
  }
>(({ className, inset, ...props }, ref) => (
  <MenubarPrimitive.Label
    ref={ref}
    className={cn("px-2 py-1.5 text-sm font-semibold", inset && "pl-8", className)}
    {...props}
  />
));
MenubarLabel.displayName = MenubarPrimitive.Label.displayName;

const MenubarSeparator = React.forwardRef<
  React.ElementRef<typeof MenubarPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof MenubarPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <MenubarPrimitive.Separator ref={ref} className={cn("-mx-1 my-1 h-px bg-muted", className)} {...props} />
));
MenubarSeparator.displayName = MenubarPrimitive.Separator.displayName;

const MenubarShortcut = ({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) => {
  return <span className={cn("ml-auto text-xs tracking-widest text-muted-foreground", className)} {...props} />;
};
MenubarShortcut.displayname = "MenubarShortcut";

export {
  Menubar,
  MenubarMenu,
  MenubarTrigger,
  MenubarContent,
  MenubarItem,
  MenubarSeparator,
  MenubarLabel,
  MenubarCheckboxItem,
  MenubarRadioGroup,
  MenubarRadioItem,
  MenubarPortal,
  MenubarSubContent,
  MenubarSubTrigger,
  MenubarGroup,
  MenubarSub,
  MenubarShortcut,
};
````

## File: src/components/ui/navigation-menu.tsx
````typescript
import * as React from "react";
import * as NavigationMenuPrimitive from "@radix-ui/react-navigation-menu";
import { cva } from "class-variance-authority";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

const NavigationMenu = React.forwardRef<
  React.ElementRef<typeof NavigationMenuPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof NavigationMenuPrimitive.Root>
>(({ className, children, ...props }, ref) => (
  <NavigationMenuPrimitive.Root
    ref={ref}
    className={cn("relative z-10 flex max-w-max flex-1 items-center justify-center", className)}
    {...props}
  >
    {children}
    <NavigationMenuViewport />
  </NavigationMenuPrimitive.Root>
));
NavigationMenu.displayName = NavigationMenuPrimitive.Root.displayName;

const NavigationMenuList = React.forwardRef<
  React.ElementRef<typeof NavigationMenuPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof NavigationMenuPrimitive.List>
>(({ className, ...props }, ref) => (
  <NavigationMenuPrimitive.List
    ref={ref}
    className={cn("group flex flex-1 list-none items-center justify-center space-x-1", className)}
    {...props}
  />
));
NavigationMenuList.displayName = NavigationMenuPrimitive.List.displayName;

const NavigationMenuItem = NavigationMenuPrimitive.Item;

const navigationMenuTriggerStyle = cva(
  "group inline-flex h-10 w-max items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[active]:bg-accent/50 data-[state=open]:bg-accent/50",
);

const NavigationMenuTrigger = React.forwardRef<
  React.ElementRef<typeof NavigationMenuPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof NavigationMenuPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <NavigationMenuPrimitive.Trigger
    ref={ref}
    className={cn(navigationMenuTriggerStyle(), "group", className)}
    {...props}
  >
    {children}{" "}
    <ChevronDown
      className="relative top-[1px] ml-1 h-3 w-3 transition duration-200 group-data-[state=open]:rotate-180"
      aria-hidden="true"
    />
  </NavigationMenuPrimitive.Trigger>
));
NavigationMenuTrigger.displayName = NavigationMenuPrimitive.Trigger.displayName;

const NavigationMenuContent = React.forwardRef<
  React.ElementRef<typeof NavigationMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof NavigationMenuPrimitive.Content>
>(({ className, ...props }, ref) => (
  <NavigationMenuPrimitive.Content
    ref={ref}
    className={cn(
      "left-0 top-0 w-full data-[motion^=from-]:animate-in data-[motion^=to-]:animate-out data-[motion^=from-]:fade-in data-[motion^=to-]:fade-out data-[motion=from-end]:slide-in-from-right-52 data-[motion=from-start]:slide-in-from-left-52 data-[motion=to-end]:slide-out-to-right-52 data-[motion=to-start]:slide-out-to-left-52 md:absolute md:w-auto",
      className,
    )}
    {...props}
  />
));
NavigationMenuContent.displayName = NavigationMenuPrimitive.Content.displayName;

const NavigationMenuLink = NavigationMenuPrimitive.Link;

const NavigationMenuViewport = React.forwardRef<
  React.ElementRef<typeof NavigationMenuPrimitive.Viewport>,
  React.ComponentPropsWithoutRef<typeof NavigationMenuPrimitive.Viewport>
>(({ className, ...props }, ref) => (
  <div className={cn("absolute left-0 top-full flex justify-center")}>
    <NavigationMenuPrimitive.Viewport
      className={cn(
        "origin-top-center relative mt-1.5 h-[var(--radix-navigation-menu-viewport-height)] w-full overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-90 md:w-[var(--radix-navigation-menu-viewport-width)]",
        className,
      )}
      ref={ref}
      {...props}
    />
  </div>
));
NavigationMenuViewport.displayName = NavigationMenuPrimitive.Viewport.displayName;

const NavigationMenuIndicator = React.forwardRef<
  React.ElementRef<typeof NavigationMenuPrimitive.Indicator>,
  React.ComponentPropsWithoutRef<typeof NavigationMenuPrimitive.Indicator>
>(({ className, ...props }, ref) => (
  <NavigationMenuPrimitive.Indicator
    ref={ref}
    className={cn(
      "top-full z-[1] flex h-1.5 items-end justify-center overflow-hidden data-[state=visible]:animate-in data-[state=hidden]:animate-out data-[state=hidden]:fade-out data-[state=visible]:fade-in",
      className,
    )}
    {...props}
  >
    <div className="relative top-[60%] h-2 w-2 rotate-45 rounded-tl-sm bg-border shadow-md" />
  </NavigationMenuPrimitive.Indicator>
));
NavigationMenuIndicator.displayName = NavigationMenuPrimitive.Indicator.displayName;

export {
  navigationMenuTriggerStyle,
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuContent,
  NavigationMenuTrigger,
  NavigationMenuLink,
  NavigationMenuIndicator,
  NavigationMenuViewport,
};
````

## File: src/components/ui/pagination.tsx
````typescript
import * as React from "react";
import { ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react";

import { cn } from "@/lib/utils";
import { ButtonProps, buttonVariants } from "@/components/ui/button";

const Pagination = ({ className, ...props }: React.ComponentProps<"nav">) => (
  <nav
    role="navigation"
    aria-label="pagination"
    className={cn("mx-auto flex w-full justify-center", className)}
    {...props}
  />
);
Pagination.displayName = "Pagination";

const PaginationContent = React.forwardRef<HTMLUListElement, React.ComponentProps<"ul">>(
  ({ className, ...props }, ref) => (
    <ul ref={ref} className={cn("flex flex-row items-center gap-1", className)} {...props} />
  ),
);
PaginationContent.displayName = "PaginationContent";

const PaginationItem = React.forwardRef<HTMLLIElement, React.ComponentProps<"li">>(({ className, ...props }, ref) => (
  <li ref={ref} className={cn("", className)} {...props} />
));
PaginationItem.displayName = "PaginationItem";

type PaginationLinkProps = {
  isActive?: boolean;
} & Pick<ButtonProps, "size"> &
  React.ComponentProps<"a">;

const PaginationLink = ({ className, isActive, size = "icon", ...props }: PaginationLinkProps) => (
  <a
    aria-current={isActive ? "page" : undefined}
    className={cn(
      buttonVariants({
        variant: isActive ? "outline" : "ghost",
        size,
      }),
      className,
    )}
    {...props}
  />
);
PaginationLink.displayName = "PaginationLink";

const PaginationPrevious = ({ className, ...props }: React.ComponentProps<typeof PaginationLink>) => (
  <PaginationLink aria-label="Go to previous page" size="default" className={cn("gap-1 pl-2.5", className)} {...props}>
    <ChevronLeft className="h-4 w-4" />
    <span>Previous</span>
  </PaginationLink>
);
PaginationPrevious.displayName = "PaginationPrevious";

const PaginationNext = ({ className, ...props }: React.ComponentProps<typeof PaginationLink>) => (
  <PaginationLink aria-label="Go to next page" size="default" className={cn("gap-1 pr-2.5", className)} {...props}>
    <span>Next</span>
    <ChevronRight className="h-4 w-4" />
  </PaginationLink>
);
PaginationNext.displayName = "PaginationNext";

const PaginationEllipsis = ({ className, ...props }: React.ComponentProps<"span">) => (
  <span aria-hidden className={cn("flex h-9 w-9 items-center justify-center", className)} {...props}>
    <MoreHorizontal className="h-4 w-4" />
    <span className="sr-only">More pages</span>
  </span>
);
PaginationEllipsis.displayName = "PaginationEllipsis";

export {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
};
````

## File: src/components/ui/popover.tsx
````typescript
import * as React from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";

import { cn } from "@/lib/utils";

const Popover = PopoverPrimitive.Root;

const PopoverTrigger = PopoverPrimitive.Trigger;

const PopoverContent = React.forwardRef<
  React.ElementRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(({ className, align = "center", sideOffset = 4, ...props }, ref) => (
  <PopoverPrimitive.Portal>
    <PopoverPrimitive.Content
      ref={ref}
      align={align}
      sideOffset={sideOffset}
      className={cn(
        "z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
        className,
      )}
      {...props}
    />
  </PopoverPrimitive.Portal>
));
PopoverContent.displayName = PopoverPrimitive.Content.displayName;

export { Popover, PopoverTrigger, PopoverContent };
````

## File: src/components/ui/progress.tsx
````typescript
import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";

import { cn } from "@/lib/utils";

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn("relative h-4 w-full overflow-hidden rounded-full bg-secondary", className)}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className="h-full w-full flex-1 bg-primary transition-all"
      style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
    />
  </ProgressPrimitive.Root>
));
Progress.displayName = ProgressPrimitive.Root.displayName;

export { Progress };
````

## File: src/components/ui/radio-group.tsx
````typescript
import * as React from "react";
import * as RadioGroupPrimitive from "@radix-ui/react-radio-group";
import { Circle } from "lucide-react";

import { cn } from "@/lib/utils";

const RadioGroup = React.forwardRef<
  React.ElementRef<typeof RadioGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof RadioGroupPrimitive.Root>
>(({ className, ...props }, ref) => {
  return <RadioGroupPrimitive.Root className={cn("grid gap-2", className)} {...props} ref={ref} />;
});
RadioGroup.displayName = RadioGroupPrimitive.Root.displayName;

const RadioGroupItem = React.forwardRef<
  React.ElementRef<typeof RadioGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof RadioGroupPrimitive.Item>
>(({ className, ...props }, ref) => {
  return (
    <RadioGroupPrimitive.Item
      ref={ref}
      className={cn(
        "aspect-square h-4 w-4 rounded-full border border-primary text-primary ring-offset-background focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      <RadioGroupPrimitive.Indicator className="flex items-center justify-center">
        <Circle className="h-2.5 w-2.5 fill-current text-current" />
      </RadioGroupPrimitive.Indicator>
    </RadioGroupPrimitive.Item>
  );
});
RadioGroupItem.displayName = RadioGroupPrimitive.Item.displayName;

export { RadioGroup, RadioGroupItem };
````

## File: src/components/ui/resizable.tsx
````typescript
import { GripVertical } from "lucide-react";
import * as ResizablePrimitive from "react-resizable-panels";

import { cn } from "@/lib/utils";

const ResizablePanelGroup = ({ className, ...props }: React.ComponentProps<typeof ResizablePrimitive.PanelGroup>) => (
  <ResizablePrimitive.PanelGroup
    className={cn("flex h-full w-full data-[panel-group-direction=vertical]:flex-col", className)}
    {...props}
  />
);

const ResizablePanel = ResizablePrimitive.Panel;

const ResizableHandle = ({
  withHandle,
  className,
  ...props
}: React.ComponentProps<typeof ResizablePrimitive.PanelResizeHandle> & {
  withHandle?: boolean;
}) => (
  <ResizablePrimitive.PanelResizeHandle
    className={cn(
      "relative flex w-px items-center justify-center bg-border after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 data-[panel-group-direction=vertical]:h-px data-[panel-group-direction=vertical]:w-full data-[panel-group-direction=vertical]:after:left-0 data-[panel-group-direction=vertical]:after:h-1 data-[panel-group-direction=vertical]:after:w-full data-[panel-group-direction=vertical]:after:-translate-y-1/2 data-[panel-group-direction=vertical]:after:translate-x-0 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-offset-1 [&[data-panel-group-direction=vertical]>div]:rotate-90",
      className,
    )}
    {...props}
  >
    {withHandle && (
      <div className="z-10 flex h-4 w-3 items-center justify-center rounded-sm border bg-border">
        <GripVertical className="h-2.5 w-2.5" />
      </div>
    )}
  </ResizablePrimitive.PanelResizeHandle>
);

export { ResizablePanelGroup, ResizablePanel, ResizableHandle };
````

## File: src/components/ui/scroll-area.tsx
````typescript
import * as React from "react";
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area";

import { cn } from "@/lib/utils";

const ScrollArea = React.forwardRef<
  React.ElementRef<typeof ScrollAreaPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.Root>
>(({ className, children, ...props }, ref) => (
  <ScrollAreaPrimitive.Root ref={ref} className={cn("relative overflow-hidden", className)} {...props}>
    <ScrollAreaPrimitive.Viewport className="h-full w-full rounded-[inherit]">{children}</ScrollAreaPrimitive.Viewport>
    <ScrollBar />
    <ScrollAreaPrimitive.Corner />
  </ScrollAreaPrimitive.Root>
));
ScrollArea.displayName = ScrollAreaPrimitive.Root.displayName;

const ScrollBar = React.forwardRef<
  React.ElementRef<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>,
  React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>
>(({ className, orientation = "vertical", ...props }, ref) => (
  <ScrollAreaPrimitive.ScrollAreaScrollbar
    ref={ref}
    orientation={orientation}
    className={cn(
      "flex touch-none select-none transition-colors",
      orientation === "vertical" && "h-full w-2.5 border-l border-l-transparent p-[1px]",
      orientation === "horizontal" && "h-2.5 flex-col border-t border-t-transparent p-[1px]",
      className,
    )}
    {...props}
  >
    <ScrollAreaPrimitive.ScrollAreaThumb className="relative flex-1 rounded-full bg-border" />
  </ScrollAreaPrimitive.ScrollAreaScrollbar>
));
ScrollBar.displayName = ScrollAreaPrimitive.ScrollAreaScrollbar.displayName;

export { ScrollArea, ScrollBar };
````

## File: src/components/ui/select.tsx
````typescript
import * as React from "react";
import * as SelectPrimitive from "@radix-ui/react-select";
import { Check, ChevronDown, ChevronUp } from "lucide-react";

import { cn } from "@/lib/utils";

const Select = SelectPrimitive.Root;

const SelectGroup = SelectPrimitive.Group;

const SelectValue = SelectPrimitive.Value;

const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1",
      className,
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <ChevronDown className="h-4 w-4 opacity-50" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
));
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName;

const SelectScrollUpButton = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.ScrollUpButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollUpButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollUpButton
    ref={ref}
    className={cn("flex cursor-default items-center justify-center py-1", className)}
    {...props}
  >
    <ChevronUp className="h-4 w-4" />
  </SelectPrimitive.ScrollUpButton>
));
SelectScrollUpButton.displayName = SelectPrimitive.ScrollUpButton.displayName;

const SelectScrollDownButton = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.ScrollDownButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollDownButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollDownButton
    ref={ref}
    className={cn("flex cursor-default items-center justify-center py-1", className)}
    {...props}
  >
    <ChevronDown className="h-4 w-4" />
  </SelectPrimitive.ScrollDownButton>
));
SelectScrollDownButton.displayName = SelectPrimitive.ScrollDownButton.displayName;

const SelectContent = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ className, children, position = "popper", ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      ref={ref}
      className={cn(
        "relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
        position === "popper" &&
          "data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1",
        className,
      )}
      position={position}
      {...props}
    >
      <SelectScrollUpButton />
      <SelectPrimitive.Viewport
        className={cn(
          "p-1",
          position === "popper" &&
            "h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]",
        )}
      >
        {children}
      </SelectPrimitive.Viewport>
      <SelectScrollDownButton />
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
));
SelectContent.displayName = SelectPrimitive.Content.displayName;

const SelectLabel = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Label>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Label ref={ref} className={cn("py-1.5 pl-8 pr-2 text-sm font-semibold", className)} {...props} />
));
SelectLabel.displayName = SelectPrimitive.Label.displayName;

const SelectItem = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 focus:bg-accent focus:text-accent-foreground",
      className,
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <SelectPrimitive.ItemIndicator>
        <Check className="h-4 w-4" />
      </SelectPrimitive.ItemIndicator>
    </span>

    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
));
SelectItem.displayName = SelectPrimitive.Item.displayName;

const SelectSeparator = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Separator ref={ref} className={cn("-mx-1 my-1 h-px bg-muted", className)} {...props} />
));
SelectSeparator.displayName = SelectPrimitive.Separator.displayName;

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
};
````

## File: src/components/ui/separator.tsx
````typescript
import * as React from "react";
import * as SeparatorPrimitive from "@radix-ui/react-separator";

import { cn } from "@/lib/utils";

const Separator = React.forwardRef<
  React.ElementRef<typeof SeparatorPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SeparatorPrimitive.Root>
>(({ className, orientation = "horizontal", decorative = true, ...props }, ref) => (
  <SeparatorPrimitive.Root
    ref={ref}
    decorative={decorative}
    orientation={orientation}
    className={cn("shrink-0 bg-border", orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]", className)}
    {...props}
  />
));
Separator.displayName = SeparatorPrimitive.Root.displayName;

export { Separator };
````

## File: src/components/ui/sheet.tsx
````typescript
import * as SheetPrimitive from "@radix-ui/react-dialog";
import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

const Sheet = SheetPrimitive.Root;

const SheetTrigger = SheetPrimitive.Trigger;

const SheetClose = SheetPrimitive.Close;

const SheetPortal = SheetPrimitive.Portal;

const SheetOverlay = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof SheetPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <SheetPrimitive.Overlay
    className={cn(
      "fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className,
    )}
    {...props}
    ref={ref}
  />
));
SheetOverlay.displayName = SheetPrimitive.Overlay.displayName;

const sheetVariants = cva(
  "fixed z-50 gap-4 bg-background p-6 shadow-lg transition ease-in-out data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:duration-300 data-[state=open]:duration-500",
  {
    variants: {
      side: {
        top: "inset-x-0 top-0 border-b data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top",
        bottom:
          "inset-x-0 bottom-0 border-t data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom",
        left: "inset-y-0 left-0 h-full w-3/4 border-r data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left sm:max-w-sm",
        right:
          "inset-y-0 right-0 h-full w-3/4  border-l data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right sm:max-w-sm",
      },
    },
    defaultVariants: {
      side: "right",
    },
  },
);

interface SheetContentProps
  extends React.ComponentPropsWithoutRef<typeof SheetPrimitive.Content>,
    VariantProps<typeof sheetVariants> {}

const SheetContent = React.forwardRef<React.ElementRef<typeof SheetPrimitive.Content>, SheetContentProps>(
  ({ side = "right", className, children, ...props }, ref) => (
    <SheetPortal>
      <SheetOverlay />
      <SheetPrimitive.Content ref={ref} className={cn(sheetVariants({ side }), className)} {...props}>
        {children}
        <SheetPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity data-[state=open]:bg-secondary hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none">
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </SheetPrimitive.Close>
      </SheetPrimitive.Content>
    </SheetPortal>
  ),
);
SheetContent.displayName = SheetPrimitive.Content.displayName;

const SheetHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col space-y-2 text-center sm:text-left", className)} {...props} />
);
SheetHeader.displayName = "SheetHeader";

const SheetFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className)} {...props} />
);
SheetFooter.displayName = "SheetFooter";

const SheetTitle = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof SheetPrimitive.Title>
>(({ className, ...props }, ref) => (
  <SheetPrimitive.Title ref={ref} className={cn("text-lg font-semibold text-foreground", className)} {...props} />
));
SheetTitle.displayName = SheetPrimitive.Title.displayName;

const SheetDescription = React.forwardRef<
  React.ElementRef<typeof SheetPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof SheetPrimitive.Description>
>(({ className, ...props }, ref) => (
  <SheetPrimitive.Description ref={ref} className={cn("text-sm text-muted-foreground", className)} {...props} />
));
SheetDescription.displayName = SheetPrimitive.Description.displayName;

export {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetOverlay,
  SheetPortal,
  SheetTitle,
  SheetTrigger,
};
````

## File: src/components/ui/sidebar.tsx
````typescript
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { VariantProps, cva } from "class-variance-authority";
import { PanelLeft } from "lucide-react";

import { useIsMobile } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const SIDEBAR_COOKIE_NAME = "sidebar:state";
const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 7;
const SIDEBAR_WIDTH = "16rem";
const SIDEBAR_WIDTH_MOBILE = "18rem";
const SIDEBAR_WIDTH_ICON = "3rem";
const SIDEBAR_KEYBOARD_SHORTCUT = "b";

type SidebarContext = {
  state: "expanded" | "collapsed";
  open: boolean;
  setOpen: (open: boolean) => void;
  openMobile: boolean;
  setOpenMobile: (open: boolean) => void;
  isMobile: boolean;
  toggleSidebar: () => void;
};

const SidebarContext = React.createContext<SidebarContext | null>(null);

function useSidebar() {
  const context = React.useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider.");
  }

  return context;
}

const SidebarProvider = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & {
    defaultOpen?: boolean;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
  }
>(({ defaultOpen = true, open: openProp, onOpenChange: setOpenProp, className, style, children, ...props }, ref) => {
  const isMobile = useIsMobile();
  const [openMobile, setOpenMobile] = React.useState(false);

  // This is the internal state of the sidebar.
  // We use openProp and setOpenProp for control from outside the component.
  const [_open, _setOpen] = React.useState(defaultOpen);
  const open = openProp ?? _open;
  const setOpen = React.useCallback(
    (value: boolean | ((value: boolean) => boolean)) => {
      const openState = typeof value === "function" ? value(open) : value;
      if (setOpenProp) {
        setOpenProp(openState);
      } else {
        _setOpen(openState);
      }

      // This sets the cookie to keep the sidebar state.
      document.cookie = `${SIDEBAR_COOKIE_NAME}=${openState}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`;
    },
    [setOpenProp, open],
  );

  // Helper to toggle the sidebar.
  const toggleSidebar = React.useCallback(() => {
    return isMobile ? setOpenMobile((open) => !open) : setOpen((open) => !open);
  }, [isMobile, setOpen, setOpenMobile]);

  // Adds a keyboard shortcut to toggle the sidebar.
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === SIDEBAR_KEYBOARD_SHORTCUT && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        toggleSidebar();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [toggleSidebar]);

  // We add a state so that we can do data-state="expanded" or "collapsed".
  // This makes it easier to style the sidebar with Tailwind classes.
  const state = open ? "expanded" : "collapsed";

  const contextValue = React.useMemo<SidebarContext>(
    () => ({
      state,
      open,
      setOpen,
      isMobile,
      openMobile,
      setOpenMobile,
      toggleSidebar,
    }),
    [state, open, setOpen, isMobile, openMobile, setOpenMobile, toggleSidebar],
  );

  return (
    <SidebarContext.Provider value={contextValue}>
      <TooltipProvider delayDuration={0}>
        <div
          style={
            {
              "--sidebar-width": SIDEBAR_WIDTH,
              "--sidebar-width-icon": SIDEBAR_WIDTH_ICON,
              ...style,
            } as React.CSSProperties
          }
          className={cn("group/sidebar-wrapper flex min-h-svh w-full has-[[data-variant=inset]]:bg-sidebar", className)}
          ref={ref}
          {...props}
        >
          {children}
        </div>
      </TooltipProvider>
    </SidebarContext.Provider>
  );
});
SidebarProvider.displayName = "SidebarProvider";

const Sidebar = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & {
    side?: "left" | "right";
    variant?: "sidebar" | "floating" | "inset";
    collapsible?: "offcanvas" | "icon" | "none";
  }
>(({ side = "left", variant = "sidebar", collapsible = "offcanvas", className, children, ...props }, ref) => {
  const { isMobile, state, openMobile, setOpenMobile } = useSidebar();

  if (collapsible === "none") {
    return (
      <div
        className={cn("flex h-full w-[--sidebar-width] flex-col bg-sidebar text-sidebar-foreground", className)}
        ref={ref}
        {...props}
      >
        {children}
      </div>
    );
  }

  if (isMobile) {
    return (
      <Sheet open={openMobile} onOpenChange={setOpenMobile} {...props}>
        <SheetContent
          data-sidebar="sidebar"
          data-mobile="true"
          className="w-[--sidebar-width] bg-sidebar p-0 text-sidebar-foreground [&>button]:hidden"
          style={
            {
              "--sidebar-width": SIDEBAR_WIDTH_MOBILE,
            } as React.CSSProperties
          }
          side={side}
        >
          <div className="flex h-full w-full flex-col">{children}</div>
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <div
      ref={ref}
      className="group peer hidden text-sidebar-foreground md:block"
      data-state={state}
      data-collapsible={state === "collapsed" ? collapsible : ""}
      data-variant={variant}
      data-side={side}
    >
      {/* This is what handles the sidebar gap on desktop */}
      <div
        className={cn(
          "relative h-svh w-[--sidebar-width] bg-transparent transition-[width] duration-200 ease-linear",
          "group-data-[collapsible=offcanvas]:w-0",
          "group-data-[side=right]:rotate-180",
          variant === "floating" || variant === "inset"
            ? "group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)_+_theme(spacing.4))]"
            : "group-data-[collapsible=icon]:w-[--sidebar-width-icon]",
        )}
      />
      <div
        className={cn(
          "fixed inset-y-0 z-10 hidden h-svh w-[--sidebar-width] transition-[left,right,width] duration-200 ease-linear md:flex",
          side === "left"
            ? "left-0 group-data-[collapsible=offcanvas]:left-[calc(var(--sidebar-width)*-1)]"
            : "right-0 group-data-[collapsible=offcanvas]:right-[calc(var(--sidebar-width)*-1)]",
          // Adjust the padding for floating and inset variants.
          variant === "floating" || variant === "inset"
            ? "p-2 group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)_+_theme(spacing.4)_+2px)]"
            : "group-data-[collapsible=icon]:w-[--sidebar-width-icon] group-data-[side=left]:border-r group-data-[side=right]:border-l",
          className,
        )}
        {...props}
      >
        <div
          data-sidebar="sidebar"
          className="flex h-full w-full flex-col bg-sidebar group-data-[variant=floating]:rounded-lg group-data-[variant=floating]:border group-data-[variant=floating]:border-sidebar-border group-data-[variant=floating]:shadow"
        >
          {children}
        </div>
      </div>
    </div>
  );
});
Sidebar.displayName = "Sidebar";

const SidebarTrigger = React.forwardRef<React.ElementRef<typeof Button>, React.ComponentProps<typeof Button>>(
  ({ className, onClick, ...props }, ref) => {
    const { toggleSidebar } = useSidebar();

    return (
      <Button
        ref={ref}
        data-sidebar="trigger"
        variant="ghost"
        size="icon"
        className={cn("h-7 w-7", className)}
        onClick={(event) => {
          onClick?.(event);
          toggleSidebar();
        }}
        {...props}
      >
        <PanelLeft />
        <span className="sr-only">Toggle Sidebar</span>
      </Button>
    );
  },
);
SidebarTrigger.displayName = "SidebarTrigger";

const SidebarRail = React.forwardRef<HTMLButtonElement, React.ComponentProps<"button">>(
  ({ className, ...props }, ref) => {
    const { toggleSidebar } = useSidebar();

    return (
      <button
        ref={ref}
        data-sidebar="rail"
        aria-label="Toggle Sidebar"
        tabIndex={-1}
        onClick={toggleSidebar}
        title="Toggle Sidebar"
        className={cn(
          "absolute inset-y-0 z-20 hidden w-4 -translate-x-1/2 transition-all ease-linear after:absolute after:inset-y-0 after:left-1/2 after:w-[2px] group-data-[side=left]:-right-4 group-data-[side=right]:left-0 hover:after:bg-sidebar-border sm:flex",
          "[[data-side=left]_&]:cursor-w-resize [[data-side=right]_&]:cursor-e-resize",
          "[[data-side=left][data-state=collapsed]_&]:cursor-e-resize [[data-side=right][data-state=collapsed]_&]:cursor-w-resize",
          "group-data-[collapsible=offcanvas]:translate-x-0 group-data-[collapsible=offcanvas]:after:left-full group-data-[collapsible=offcanvas]:hover:bg-sidebar",
          "[[data-side=left][data-collapsible=offcanvas]_&]:-right-2",
          "[[data-side=right][data-collapsible=offcanvas]_&]:-left-2",
          className,
        )}
        {...props}
      />
    );
  },
);
SidebarRail.displayName = "SidebarRail";

const SidebarInset = React.forwardRef<HTMLDivElement, React.ComponentProps<"main">>(({ className, ...props }, ref) => {
  return (
    <main
      ref={ref}
      className={cn(
        "relative flex min-h-svh flex-1 flex-col bg-background",
        "peer-data-[variant=inset]:min-h-[calc(100svh-theme(spacing.4))] md:peer-data-[variant=inset]:m-2 md:peer-data-[state=collapsed]:peer-data-[variant=inset]:ml-2 md:peer-data-[variant=inset]:ml-0 md:peer-data-[variant=inset]:rounded-xl md:peer-data-[variant=inset]:shadow",
        className,
      )}
      {...props}
    />
  );
});
SidebarInset.displayName = "SidebarInset";

const SidebarInput = React.forwardRef<React.ElementRef<typeof Input>, React.ComponentProps<typeof Input>>(
  ({ className, ...props }, ref) => {
    return (
      <Input
        ref={ref}
        data-sidebar="input"
        className={cn(
          "h-8 w-full bg-background shadow-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
          className,
        )}
        {...props}
      />
    );
  },
);
SidebarInput.displayName = "SidebarInput";

const SidebarHeader = React.forwardRef<HTMLDivElement, React.ComponentProps<"div">>(({ className, ...props }, ref) => {
  return <div ref={ref} data-sidebar="header" className={cn("flex flex-col gap-2 p-2", className)} {...props} />;
});
SidebarHeader.displayName = "SidebarHeader";

const SidebarFooter = React.forwardRef<HTMLDivElement, React.ComponentProps<"div">>(({ className, ...props }, ref) => {
  return <div ref={ref} data-sidebar="footer" className={cn("flex flex-col gap-2 p-2", className)} {...props} />;
});
SidebarFooter.displayName = "SidebarFooter";

const SidebarSeparator = React.forwardRef<React.ElementRef<typeof Separator>, React.ComponentProps<typeof Separator>>(
  ({ className, ...props }, ref) => {
    return (
      <Separator
        ref={ref}
        data-sidebar="separator"
        className={cn("mx-2 w-auto bg-sidebar-border", className)}
        {...props}
      />
    );
  },
);
SidebarSeparator.displayName = "SidebarSeparator";

const SidebarContent = React.forwardRef<HTMLDivElement, React.ComponentProps<"div">>(({ className, ...props }, ref) => {
  return (
    <div
      ref={ref}
      data-sidebar="content"
      className={cn(
        "flex min-h-0 flex-1 flex-col gap-2 overflow-auto group-data-[collapsible=icon]:overflow-hidden",
        className,
      )}
      {...props}
    />
  );
});
SidebarContent.displayName = "SidebarContent";

const SidebarGroup = React.forwardRef<HTMLDivElement, React.ComponentProps<"div">>(({ className, ...props }, ref) => {
  return (
    <div
      ref={ref}
      data-sidebar="group"
      className={cn("relative flex w-full min-w-0 flex-col p-2", className)}
      {...props}
    />
  );
});
SidebarGroup.displayName = "SidebarGroup";

const SidebarGroupLabel = React.forwardRef<HTMLDivElement, React.ComponentProps<"div"> & { asChild?: boolean }>(
  ({ className, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "div";

    return (
      <Comp
        ref={ref}
        data-sidebar="group-label"
        className={cn(
          "flex h-8 shrink-0 items-center rounded-md px-2 text-xs font-medium text-sidebar-foreground/70 outline-none ring-sidebar-ring transition-[margin,opa] duration-200 ease-linear focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0",
          "group-data-[collapsible=icon]:-mt-8 group-data-[collapsible=icon]:opacity-0",
          className,
        )}
        {...props}
      />
    );
  },
);
SidebarGroupLabel.displayName = "SidebarGroupLabel";

const SidebarGroupAction = React.forwardRef<HTMLButtonElement, React.ComponentProps<"button"> & { asChild?: boolean }>(
  ({ className, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";

    return (
      <Comp
        ref={ref}
        data-sidebar="group-action"
        className={cn(
          "absolute right-3 top-3.5 flex aspect-square w-5 items-center justify-center rounded-md p-0 text-sidebar-foreground outline-none ring-sidebar-ring transition-transform hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0",
          // Increases the hit area of the button on mobile.
          "after:absolute after:-inset-2 after:md:hidden",
          "group-data-[collapsible=icon]:hidden",
          className,
        )}
        {...props}
      />
    );
  },
);
SidebarGroupAction.displayName = "SidebarGroupAction";

const SidebarGroupContent = React.forwardRef<HTMLDivElement, React.ComponentProps<"div">>(
  ({ className, ...props }, ref) => (
    <div ref={ref} data-sidebar="group-content" className={cn("w-full text-sm", className)} {...props} />
  ),
);
SidebarGroupContent.displayName = "SidebarGroupContent";

const SidebarMenu = React.forwardRef<HTMLUListElement, React.ComponentProps<"ul">>(({ className, ...props }, ref) => (
  <ul ref={ref} data-sidebar="menu" className={cn("flex w-full min-w-0 flex-col gap-1", className)} {...props} />
));
SidebarMenu.displayName = "SidebarMenu";

const SidebarMenuItem = React.forwardRef<HTMLLIElement, React.ComponentProps<"li">>(({ className, ...props }, ref) => (
  <li ref={ref} data-sidebar="menu-item" className={cn("group/menu-item relative", className)} {...props} />
));
SidebarMenuItem.displayName = "SidebarMenuItem";

const sidebarMenuButtonVariants = cva(
  "peer/menu-button flex w-full items-center gap-2 overflow-hidden rounded-md p-2 text-left text-sm outline-none ring-sidebar-ring transition-[width,height,padding] hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 active:bg-sidebar-accent active:text-sidebar-accent-foreground disabled:pointer-events-none disabled:opacity-50 group-has-[[data-sidebar=menu-action]]/menu-item:pr-8 aria-disabled:pointer-events-none aria-disabled:opacity-50 data-[active=true]:bg-sidebar-accent data-[active=true]:font-medium data-[active=true]:text-sidebar-accent-foreground data-[state=open]:hover:bg-sidebar-accent data-[state=open]:hover:text-sidebar-accent-foreground group-data-[collapsible=icon]:!size-8 group-data-[collapsible=icon]:!p-2 [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
        outline:
          "bg-background shadow-[0_0_0_1px_hsl(var(--sidebar-border))] hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:shadow-[0_0_0_1px_hsl(var(--sidebar-accent))]",
      },
      size: {
        default: "h-8 text-sm",
        sm: "h-7 text-xs",
        lg: "h-12 text-sm group-data-[collapsible=icon]:!p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

const SidebarMenuButton = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<"button"> & {
    asChild?: boolean;
    isActive?: boolean;
    tooltip?: string | React.ComponentProps<typeof TooltipContent>;
  } & VariantProps<typeof sidebarMenuButtonVariants>
>(({ asChild = false, isActive = false, variant = "default", size = "default", tooltip, className, ...props }, ref) => {
  const Comp = asChild ? Slot : "button";
  const { isMobile, state } = useSidebar();

  const button = (
    <Comp
      ref={ref}
      data-sidebar="menu-button"
      data-size={size}
      data-active={isActive}
      className={cn(sidebarMenuButtonVariants({ variant, size }), className)}
      {...props}
    />
  );

  if (!tooltip) {
    return button;
  }

  if (typeof tooltip === "string") {
    tooltip = {
      children: tooltip,
    };
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent side="right" align="center" hidden={state !== "collapsed" || isMobile} {...tooltip} />
    </Tooltip>
  );
});
SidebarMenuButton.displayName = "SidebarMenuButton";

const SidebarMenuAction = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<"button"> & {
    asChild?: boolean;
    showOnHover?: boolean;
  }
>(({ className, asChild = false, showOnHover = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button";

  return (
    <Comp
      ref={ref}
      data-sidebar="menu-action"
      className={cn(
        "absolute right-1 top-1.5 flex aspect-square w-5 items-center justify-center rounded-md p-0 text-sidebar-foreground outline-none ring-sidebar-ring transition-transform peer-hover/menu-button:text-sidebar-accent-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0",
        // Increases the hit area of the button on mobile.
        "after:absolute after:-inset-2 after:md:hidden",
        "peer-data-[size=sm]/menu-button:top-1",
        "peer-data-[size=default]/menu-button:top-1.5",
        "peer-data-[size=lg]/menu-button:top-2.5",
        "group-data-[collapsible=icon]:hidden",
        showOnHover &&
          "group-focus-within/menu-item:opacity-100 group-hover/menu-item:opacity-100 data-[state=open]:opacity-100 peer-data-[active=true]/menu-button:text-sidebar-accent-foreground md:opacity-0",
        className,
      )}
      {...props}
    />
  );
});
SidebarMenuAction.displayName = "SidebarMenuAction";

const SidebarMenuBadge = React.forwardRef<HTMLDivElement, React.ComponentProps<"div">>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      data-sidebar="menu-badge"
      className={cn(
        "pointer-events-none absolute right-1 flex h-5 min-w-5 select-none items-center justify-center rounded-md px-1 text-xs font-medium tabular-nums text-sidebar-foreground",
        "peer-hover/menu-button:text-sidebar-accent-foreground peer-data-[active=true]/menu-button:text-sidebar-accent-foreground",
        "peer-data-[size=sm]/menu-button:top-1",
        "peer-data-[size=default]/menu-button:top-1.5",
        "peer-data-[size=lg]/menu-button:top-2.5",
        "group-data-[collapsible=icon]:hidden",
        className,
      )}
      {...props}
    />
  ),
);
SidebarMenuBadge.displayName = "SidebarMenuBadge";

const SidebarMenuSkeleton = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & {
    showIcon?: boolean;
  }
>(({ className, showIcon = false, ...props }, ref) => {
  // Random width between 50 to 90%.
  const width = React.useMemo(() => {
    return `${Math.floor(Math.random() * 40) + 50}%`;
  }, []);

  return (
    <div
      ref={ref}
      data-sidebar="menu-skeleton"
      className={cn("flex h-8 items-center gap-2 rounded-md px-2", className)}
      {...props}
    >
      {showIcon && <Skeleton className="size-4 rounded-md" data-sidebar="menu-skeleton-icon" />}
      <Skeleton
        className="h-4 max-w-[--skeleton-width] flex-1"
        data-sidebar="menu-skeleton-text"
        style={
          {
            "--skeleton-width": width,
          } as React.CSSProperties
        }
      />
    </div>
  );
});
SidebarMenuSkeleton.displayName = "SidebarMenuSkeleton";

const SidebarMenuSub = React.forwardRef<HTMLUListElement, React.ComponentProps<"ul">>(
  ({ className, ...props }, ref) => (
    <ul
      ref={ref}
      data-sidebar="menu-sub"
      className={cn(
        "mx-3.5 flex min-w-0 translate-x-px flex-col gap-1 border-l border-sidebar-border px-2.5 py-0.5",
        "group-data-[collapsible=icon]:hidden",
        className,
      )}
      {...props}
    />
  ),
);
SidebarMenuSub.displayName = "SidebarMenuSub";

const SidebarMenuSubItem = React.forwardRef<HTMLLIElement, React.ComponentProps<"li">>(({ ...props }, ref) => (
  <li ref={ref} {...props} />
));
SidebarMenuSubItem.displayName = "SidebarMenuSubItem";

const SidebarMenuSubButton = React.forwardRef<
  HTMLAnchorElement,
  React.ComponentProps<"a"> & {
    asChild?: boolean;
    size?: "sm" | "md";
    isActive?: boolean;
  }
>(({ asChild = false, size = "md", isActive, className, ...props }, ref) => {
  const Comp = asChild ? Slot : "a";

  return (
    <Comp
      ref={ref}
      data-sidebar="menu-sub-button"
      data-size={size}
      data-active={isActive}
      className={cn(
        "flex h-7 min-w-0 -translate-x-px items-center gap-2 overflow-hidden rounded-md px-2 text-sidebar-foreground outline-none ring-sidebar-ring aria-disabled:pointer-events-none aria-disabled:opacity-50 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 active:bg-sidebar-accent active:text-sidebar-accent-foreground disabled:pointer-events-none disabled:opacity-50 [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0 [&>svg]:text-sidebar-accent-foreground",
        "data-[active=true]:bg-sidebar-accent data-[active=true]:text-sidebar-accent-foreground",
        size === "sm" && "text-xs",
        size === "md" && "text-sm",
        "group-data-[collapsible=icon]:hidden",
        className,
      )}
      {...props}
    />
  );
});
SidebarMenuSubButton.displayName = "SidebarMenuSubButton";

export {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInput,
  SidebarInset,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarProvider,
  SidebarRail,
  SidebarSeparator,
  SidebarTrigger,
  useSidebar,
};
````

## File: src/components/ui/skeleton.tsx
````typescript
import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-md bg-muted", className)} {...props} />;
}

export { Skeleton };
````

## File: src/components/ui/slider.tsx
````typescript
import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";

import { cn } from "@/lib/utils";

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn("relative flex w-full touch-none select-none items-center", className)}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
      <SliderPrimitive.Range className="absolute h-full bg-primary" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb className="block h-5 w-5 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50" />
  </SliderPrimitive.Root>
));
Slider.displayName = SliderPrimitive.Root.displayName;

export { Slider };
````

## File: src/components/ui/sonner.tsx
````typescript
import { useTheme } from "next-themes";
import { Toaster as Sonner, toast } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme();

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg",
          description: "group-[.toast]:text-muted-foreground",
          actionButton: "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
          cancelButton: "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground",
        },
      }}
      {...props}
    />
  );
};

export { Toaster, toast };
````

## File: src/components/ui/switch.tsx
````typescript
import * as React from "react";
import * as SwitchPrimitives from "@radix-ui/react-switch";

import { cn } from "@/lib/utils";

const Switch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitives.Root
    className={cn(
      "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors data-[state=checked]:bg-primary data-[state=unchecked]:bg-input focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
      className,
    )}
    {...props}
    ref={ref}
  >
    <SwitchPrimitives.Thumb
      className={cn(
        "pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0",
      )}
    />
  </SwitchPrimitives.Root>
));
Switch.displayName = SwitchPrimitives.Root.displayName;

export { Switch };
````

## File: src/components/ui/table.tsx
````typescript
import * as React from "react";

import { cn } from "@/lib/utils";

const Table = React.forwardRef<HTMLTableElement, React.HTMLAttributes<HTMLTableElement>>(
  ({ className, ...props }, ref) => (
    <div className="relative w-full overflow-auto">
      <table ref={ref} className={cn("w-full caption-bottom text-sm", className)} {...props} />
    </div>
  ),
);
Table.displayName = "Table";

const TableHeader = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className, ...props }, ref) => <thead ref={ref} className={cn("[&_tr]:border-b", className)} {...props} />,
);
TableHeader.displayName = "TableHeader";

const TableBody = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className, ...props }, ref) => (
    <tbody ref={ref} className={cn("[&_tr:last-child]:border-0", className)} {...props} />
  ),
);
TableBody.displayName = "TableBody";

const TableFooter = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className, ...props }, ref) => (
    <tfoot ref={ref} className={cn("border-t bg-muted/50 font-medium [&>tr]:last:border-b-0", className)} {...props} />
  ),
);
TableFooter.displayName = "TableFooter";

const TableRow = React.forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(
  ({ className, ...props }, ref) => (
    <tr
      ref={ref}
      className={cn("border-b transition-colors data-[state=selected]:bg-muted hover:bg-muted/50", className)}
      {...props}
    />
  ),
);
TableRow.displayName = "TableRow";

const TableHead = React.forwardRef<HTMLTableCellElement, React.ThHTMLAttributes<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <th
      ref={ref}
      className={cn(
        "h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0",
        className,
      )}
      {...props}
    />
  ),
);
TableHead.displayName = "TableHead";

const TableCell = React.forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <td ref={ref} className={cn("p-4 align-middle [&:has([role=checkbox])]:pr-0", className)} {...props} />
  ),
);
TableCell.displayName = "TableCell";

const TableCaption = React.forwardRef<HTMLTableCaptionElement, React.HTMLAttributes<HTMLTableCaptionElement>>(
  ({ className, ...props }, ref) => (
    <caption ref={ref} className={cn("mt-4 text-sm text-muted-foreground", className)} {...props} />
  ),
);
TableCaption.displayName = "TableCaption";

export { Table, TableHeader, TableBody, TableFooter, TableHead, TableRow, TableCell, TableCaption };
````

## File: src/components/ui/tabs.tsx
````typescript
import * as React from "react";
import * as TabsPrimitive from "@radix-ui/react-tabs";

import { cn } from "@/lib/utils";

const Tabs = TabsPrimitive.Root;

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",
      className,
    )}
    {...props}
  />
));
TabsList.displayName = TabsPrimitive.List.displayName;

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
      className,
    )}
    {...props}
  />
));
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      className,
    )}
    {...props}
  />
));
TabsContent.displayName = TabsPrimitive.Content.displayName;

export { Tabs, TabsList, TabsTrigger, TabsContent };
````

## File: src/components/ui/textarea.tsx
````typescript
import * as React from "react";

import { cn } from "@/lib/utils";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      ref={ref}
      {...props}
    />
  );
});
Textarea.displayName = "Textarea";

export { Textarea };
````

## File: src/components/ui/toast.tsx
````typescript
import * as React from "react";
import * as ToastPrimitives from "@radix-ui/react-toast";
import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";

const ToastProvider = ToastPrimitives.Provider;

const ToastViewport = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Viewport>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Viewport>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Viewport
    ref={ref}
    className={cn(
      "fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]",
      className,
    )}
    {...props}
  />
));
ToastViewport.displayName = ToastPrimitives.Viewport.displayName;

const toastVariants = cva(
  "group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full",
  {
    variants: {
      variant: {
        default: "border bg-background text-foreground",
        destructive: "destructive group border-destructive bg-destructive text-destructive-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

const Toast = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Root> & VariantProps<typeof toastVariants>
>(({ className, variant, ...props }, ref) => {
  return <ToastPrimitives.Root ref={ref} className={cn(toastVariants({ variant }), className)} {...props} />;
});
Toast.displayName = ToastPrimitives.Root.displayName;

const ToastAction = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Action>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Action>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Action
    ref={ref}
    className={cn(
      "inline-flex h-8 shrink-0 items-center justify-center rounded-md border bg-transparent px-3 text-sm font-medium ring-offset-background transition-colors group-[.destructive]:border-muted/40 hover:bg-secondary group-[.destructive]:hover:border-destructive/30 group-[.destructive]:hover:bg-destructive group-[.destructive]:hover:text-destructive-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 group-[.destructive]:focus:ring-destructive disabled:pointer-events-none disabled:opacity-50",
      className,
    )}
    {...props}
  />
));
ToastAction.displayName = ToastPrimitives.Action.displayName;

const ToastClose = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Close>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Close>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Close
    ref={ref}
    className={cn(
      "absolute right-2 top-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity group-hover:opacity-100 group-[.destructive]:text-red-300 hover:text-foreground group-[.destructive]:hover:text-red-50 focus:opacity-100 focus:outline-none focus:ring-2 group-[.destructive]:focus:ring-red-400 group-[.destructive]:focus:ring-offset-red-600",
      className,
    )}
    toast-close=""
    {...props}
  >
    <X className="h-4 w-4" />
  </ToastPrimitives.Close>
));
ToastClose.displayName = ToastPrimitives.Close.displayName;

const ToastTitle = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Title>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Title>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Title ref={ref} className={cn("text-sm font-semibold", className)} {...props} />
));
ToastTitle.displayName = ToastPrimitives.Title.displayName;

const ToastDescription = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Description>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Description>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Description ref={ref} className={cn("text-sm opacity-90", className)} {...props} />
));
ToastDescription.displayName = ToastPrimitives.Description.displayName;

type ToastProps = React.ComponentPropsWithoutRef<typeof Toast>;

type ToastActionElement = React.ReactElement<typeof ToastAction>;

export {
  type ToastProps,
  type ToastActionElement,
  ToastProvider,
  ToastViewport,
  Toast,
  ToastTitle,
  ToastDescription,
  ToastClose,
  ToastAction,
};
````

## File: src/components/ui/toaster.tsx
````typescript
import { useToast } from "@/hooks/use-toast";
import { Toast, ToastClose, ToastDescription, ToastProvider, ToastTitle, ToastViewport } from "@/components/ui/toast";

export function Toaster() {
  const { toasts } = useToast();

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, ...props }) {
        return (
          <Toast key={id} {...props}>
            <div className="grid gap-1">
              {title && <ToastTitle>{title}</ToastTitle>}
              {description && <ToastDescription>{description}</ToastDescription>}
            </div>
            {action}
            <ToastClose />
          </Toast>
        );
      })}
      <ToastViewport />
    </ToastProvider>
  );
}
````

## File: src/components/ui/toggle-group.tsx
````typescript
import * as React from "react";
import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group";
import { type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";
import { toggleVariants } from "@/components/ui/toggle";

const ToggleGroupContext = React.createContext<VariantProps<typeof toggleVariants>>({
  size: "default",
  variant: "default",
});

const ToggleGroup = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root> & VariantProps<typeof toggleVariants>
>(({ className, variant, size, children, ...props }, ref) => (
  <ToggleGroupPrimitive.Root ref={ref} className={cn("flex items-center justify-center gap-1", className)} {...props}>
    <ToggleGroupContext.Provider value={{ variant, size }}>{children}</ToggleGroupContext.Provider>
  </ToggleGroupPrimitive.Root>
));

ToggleGroup.displayName = ToggleGroupPrimitive.Root.displayName;

const ToggleGroupItem = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Item> & VariantProps<typeof toggleVariants>
>(({ className, children, variant, size, ...props }, ref) => {
  const context = React.useContext(ToggleGroupContext);

  return (
    <ToggleGroupPrimitive.Item
      ref={ref}
      className={cn(
        toggleVariants({
          variant: context.variant || variant,
          size: context.size || size,
        }),
        className,
      )}
      {...props}
    >
      {children}
    </ToggleGroupPrimitive.Item>
  );
});

ToggleGroupItem.displayName = ToggleGroupPrimitive.Item.displayName;

export { ToggleGroup, ToggleGroupItem };
````

## File: src/components/ui/toggle.tsx
````typescript
import * as React from "react";
import * as TogglePrimitive from "@radix-ui/react-toggle";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const toggleVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors hover:bg-muted hover:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-accent data-[state=on]:text-accent-foreground",
  {
    variants: {
      variant: {
        default: "bg-transparent",
        outline: "border border-input bg-transparent hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-10 px-3",
        sm: "h-9 px-2.5",
        lg: "h-11 px-5",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

const Toggle = React.forwardRef<
  React.ElementRef<typeof TogglePrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof TogglePrimitive.Root> & VariantProps<typeof toggleVariants>
>(({ className, variant, size, ...props }, ref) => (
  <TogglePrimitive.Root ref={ref} className={cn(toggleVariants({ variant, size, className }))} {...props} />
));

Toggle.displayName = TogglePrimitive.Root.displayName;

export { Toggle, toggleVariants };
````

## File: src/components/ui/tooltip.tsx
````typescript
import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";

import { cn } from "@/lib/utils";

const TooltipProvider = TooltipPrimitive.Provider;

const Tooltip = TooltipPrimitive.Root;

const TooltipTrigger = TooltipPrimitive.Trigger;

const TooltipContent = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <TooltipPrimitive.Content
    ref={ref}
    sideOffset={sideOffset}
    className={cn(
      "z-50 overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
      className,
    )}
    {...props}
  />
));
TooltipContent.displayName = TooltipPrimitive.Content.displayName;

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider };
````

## File: src/components/ui/use-toast.ts
````typescript
import { useToast, toast } from "@/hooks/use-toast";

export { useToast, toast };
````

## File: src/components/ActiveOrdersPanel.tsx
````typescript
import { Clock, X, CheckCircle, AlertCircle } from "lucide-react";

const activeOrders = [
  {
    id: "ORD-4521",
    pair: "BTC/USD",
    type: "LIMIT BUY",
    price: "96,500.00",
    size: "0.15",
    filled: 0,
    status: "pending",
    time: "14:32:18",
  },
  {
    id: "ORD-4520",
    pair: "ETH/USD",
    type: "STOP LOSS",
    price: "3,380.00",
    size: "2.5",
    filled: 0,
    status: "active",
    time: "14:28:45",
  },
  {
    id: "ORD-4519",
    pair: "BTC/USD",
    type: "TAKE PROFIT",
    price: "99,000.00",
    size: "0.10",
    filled: 0,
    status: "active",
    time: "14:15:22",
  },
  {
    id: "ORD-4518",
    pair: "SOL/USD",
    type: "LIMIT BUY",
    price: "182.50",
    size: "25",
    filled: 60,
    status: "partial",
    time: "13:58:10",
  },
  {
    id: "ORD-4517",
    pair: "XAU/USD",
    type: "LIMIT SELL",
    price: "2,650.00",
    size: "5",
    filled: 100,
    status: "filled",
    time: "13:45:33",
  },
];

const getStatusIcon = (status: string) => {
  switch (status) {
    case "filled":
      return <CheckCircle className="w-4 h-4 text-terminal-green" />;
    case "partial":
      return <Clock className="w-4 h-4 text-primary animate-pulse" />;
    case "active":
      return <AlertCircle className="w-4 h-4 text-secondary" />;
    default:
      return <Clock className="w-4 h-4 text-muted-foreground" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case "filled":
      return "text-terminal-green";
    case "partial":
      return "text-primary";
    case "active":
      return "text-secondary";
    default:
      return "text-muted-foreground";
  }
};

export const ActiveOrdersPanel = () => {
  return (
    <div className="panel h-full">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-secondary" />
          <span className="panel-title">ACTIVE ORDERS</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-mono">
            {activeOrders.filter((o) => o.status !== "filled").length} PENDING
          </span>
          <div className="status-indicator online">
            <span className="w-2 h-2 rounded-full bg-terminal-green animate-pulse" />
          </div>
        </div>
      </div>

      <div className="space-y-1">
        {/* Header */}
        <div className="grid grid-cols-8 gap-2 text-xs text-muted-foreground px-2 py-1 border-b border-primary/20">
          <span>ORDER ID</span>
          <span>PAIR</span>
          <span>TYPE</span>
          <span className="text-right">PRICE</span>
          <span className="text-right">SIZE</span>
          <span className="text-center">FILLED</span>
          <span className="text-center">STATUS</span>
          <span className="text-center">ACTION</span>
        </div>

        {/* Orders */}
        {activeOrders.map((order, index) => (
          <div
            key={order.id}
            className={`grid grid-cols-8 gap-2 text-sm px-2 py-2 font-mono transition-colors hover:bg-primary/10 ${
              index % 2 === 0 ? "bg-panel-bg/50" : "bg-background/50"
            } ${order.status === "filled" ? "opacity-60" : ""}`}
          >
            <span className="text-muted-foreground">{order.id}</span>
            <span className="text-primary font-bold">{order.pair}</span>
            <span
              className={
                order.type.includes("BUY")
                  ? "text-terminal-green"
                  : order.type.includes("SELL")
                  ? "text-danger-red"
                  : "text-secondary"
              }
            >
              {order.type}
            </span>
            <span className="text-right text-foreground">${order.price}</span>
            <span className="text-right text-foreground">{order.size}</span>
            <div className="flex justify-center">
              <div className="w-12 h-1.5 bg-background rounded-full overflow-hidden">
                <div
                  className="h-full bg-terminal-green rounded-full transition-all"
                  style={{ width: `${order.filled}%` }}
                />
              </div>
            </div>
            <div className="flex items-center justify-center gap-1">
              {getStatusIcon(order.status)}
              <span className={`text-xs ${getStatusColor(order.status)}`}>
                {order.status.toUpperCase()}
              </span>
            </div>
            <div className="flex justify-center">
              {order.status !== "filled" && (
                <button className="p-1 hover:bg-danger-red/20 rounded transition-colors group">
                  <X className="w-4 h-4 text-muted-foreground group-hover:text-danger-red" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-2 border-t border-primary/20 flex justify-between text-xs">
        <span className="text-muted-foreground">Total Orders: {activeOrders.length}</span>
        <span className="text-terminal-green">
          Filled: {activeOrders.filter((o) => o.status === "filled").length}
        </span>
      </div>
    </div>
  );
};
````

## File: src/components/AIAnalysisPanel.tsx
````typescript
import { Brain, Zap, Target, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";

const analysisData = {
  marketPhase: "Accumulation",
  trend: "Bullish",
  confidence: 78,
  signals: [
    { type: "bullish", text: "RSI divergence detected on H4", priority: "high" },
    { type: "bullish", text: "Volume increasing on upward moves", priority: "medium" },
    { type: "neutral", text: "Price consolidating near resistance", priority: "medium" },
    { type: "bearish", text: "Funding rate elevated (0.045%)", priority: "low" }
  ],
  recommendation: "ACCUMULATE",
  keyLevels: {
    support: [96500, 95200, 93800],
    resistance: [98500, 100000, 102500]
  },
  riskLevel: "MODERATE"
};

export const AIAnalysisPanel = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState("Just now");

  useEffect(() => {
    const interval = setInterval(() => {
      setIsAnalyzing(true);
      setTimeout(() => setIsAnalyzing(false), 2000);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const getSignalIcon = (type: string) => {
    switch (type) {
      case "bullish":
        return <CheckCircle className="w-3 h-3 text-terminal-green" />;
      case "bearish":
        return <AlertTriangle className="w-3 h-3 text-danger-red" />;
      default:
        return <Target className="w-3 h-3 text-primary" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-danger-red/20 text-danger-red";
      case "medium":
        return "bg-primary/20 text-primary";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-secondary" />
          <h2 className="panel-title">AI ANALYSIS</h2>
        </div>
        <div className="flex items-center gap-2">
          {isAnalyzing ? (
            <>
              <Loader2 className="w-3 h-3 text-secondary animate-spin" />
              <span className="text-xs text-secondary">ANALYZING...</span>
            </>
          ) : (
            <>
              <Zap className="w-3 h-3 text-terminal-green" />
              <span className="text-xs text-terminal-green">READY</span>
            </>
          )}
        </div>
      </div>

      {/* Market Phase & Trend */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-panel-bg/50 rounded p-3 border border-border/30">
          <span className="text-xs text-muted-foreground block mb-1">PHASE</span>
          <span className="text-sm font-bold text-primary">{analysisData.marketPhase}</span>
        </div>
        <div className="bg-panel-bg/50 rounded p-3 border border-border/30">
          <span className="text-xs text-muted-foreground block mb-1">TREND</span>
          <span className="text-sm font-bold text-terminal-green">{analysisData.trend}</span>
        </div>
        <div className="bg-panel-bg/50 rounded p-3 border border-border/30">
          <span className="text-xs text-muted-foreground block mb-1">CONFIDENCE</span>
          <span className="text-sm font-bold text-foreground">{analysisData.confidence}%</span>
        </div>
      </div>

      {/* AI Recommendation */}
      <div className="bg-terminal-green/10 border border-terminal-green/30 rounded p-3 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-terminal-green" />
            <span className="text-sm text-muted-foreground">AI Recommendation:</span>
          </div>
          <span className="text-lg font-bold text-terminal-green tracking-wider">
            {analysisData.recommendation}
          </span>
        </div>
        <div className="mt-2 flex items-center gap-4 text-xs">
          <span className="text-muted-foreground">
            Risk Level: <span className="text-primary font-semibold">{analysisData.riskLevel}</span>
          </span>
        </div>
      </div>

      {/* Signals */}
      <div className="mb-4">
        <h3 className="text-xs text-muted-foreground mb-2 flex items-center gap-2">
          <Zap className="w-3 h-3" />
          ACTIVE SIGNALS
        </h3>
        <div className="space-y-2">
          {analysisData.signals.map((signal, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between bg-panel-bg/30 rounded px-3 py-2 border border-border/20"
            >
              <div className="flex items-center gap-2">
                {getSignalIcon(signal.type)}
                <span className="text-sm text-foreground/90">{signal.text}</span>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded ${getPriorityColor(signal.priority)}`}>
                {signal.priority.toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Key Levels */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-terminal-green/5 border border-terminal-green/20 rounded p-2">
          <span className="text-xs text-terminal-green block mb-1">SUPPORT LEVELS</span>
          <div className="flex flex-wrap gap-1">
            {analysisData.keyLevels.support.map((level, idx) => (
              <span key={idx} className="text-xs bg-terminal-green/20 text-terminal-green px-2 py-0.5 rounded">
                ${level.toLocaleString()}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-danger-red/5 border border-danger-red/20 rounded p-2">
          <span className="text-xs text-danger-red block mb-1">RESISTANCE LEVELS</span>
          <div className="flex flex-wrap gap-1">
            {analysisData.keyLevels.resistance.map((level, idx) => (
              <span key={idx} className="text-xs bg-danger-red/20 text-danger-red px-2 py-0.5 rounded">
                ${level.toLocaleString()}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-border/30 text-xs text-muted-foreground flex justify-between">
        <span>Last analysis: {lastUpdate}</span>
        <button 
          onClick={() => {
            setIsAnalyzing(true);
            setTimeout(() => {
              setIsAnalyzing(false);
              setLastUpdate("Just now");
            }, 2000);
          }}
          className="text-primary hover:underline"
        >
          Refresh Analysis →
        </button>
      </div>
    </div>
  );
};
````

## File: src/components/GamepadControllerHints.tsx
````typescript
import { Gamepad2 } from "lucide-react";

export const GamepadControllerHints = () => {
  return (
    <div className="panel bg-panel-bg/30">
      <div className="flex items-center justify-between flex-wrap gap-4 p-3">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Gamepad2 className="w-5 h-5 text-primary" />
          <span className="text-sm font-mono">CONTROLLER READY</span>
        </div>

        <div className="flex items-center gap-6 flex-wrap">
          {/* D-Pad */}
          <div className="flex items-center gap-2">
            <div className="flex flex-col items-center">
              <div className="w-5 h-5 border border-primary/50 rounded-sm flex items-center justify-center text-xs text-primary">▲</div>
              <div className="flex">
                <div className="w-5 h-5 border border-primary/50 rounded-sm flex items-center justify-center text-xs text-primary">◄</div>
                <div className="w-5 h-5" />
                <div className="w-5 h-5 border border-primary/50 rounded-sm flex items-center justify-center text-xs text-primary">►</div>
              </div>
              <div className="w-5 h-5 border border-primary/50 rounded-sm flex items-center justify-center text-xs text-primary">▼</div>
            </div>
            <span className="text-xs text-muted-foreground">NAVIGATE</span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint bg-terminal-green/20 text-terminal-green text-xs">A</div>
              <span className="text-xs text-muted-foreground">CONFIRM</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint bg-danger-red/20 text-danger-red text-xs">B</div>
              <span className="text-xs text-muted-foreground">BACK</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint bg-primary/20 text-primary text-xs">X</div>
              <span className="text-xs text-muted-foreground">ACTION</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint bg-secondary/20 text-secondary text-xs">Y</div>
              <span className="text-xs text-muted-foreground">SPECIAL</span>
            </div>
          </div>

          {/* Bumpers */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint text-xs px-2">LB</div>
              <span className="text-xs text-muted-foreground">TRADE</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="gamepad-button-hint text-xs px-2">RB</div>
              <span className="text-xs text-muted-foreground">POSITIONS</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
````

## File: src/components/GlobalGamepadHandler.tsx
````typescript
import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useGamepad } from "@/hooks/useGamepad";

export const GlobalGamepadHandler = () => {
    // Initialize gamepad polling globally
    useGamepad();

    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Monitor Switching Logic
            // [ = Prev Monitor (LT)
            // ] = Next Monitor (RT)

            const routes = ["/", "/m2", "/m3"];
            const currentPath = location.pathname;
            const currentIndex = routes.indexOf(currentPath); // -1 if not found

            if (currentIndex === -1) return; // Don't switch if on unknown route (e.g. 404)

            if (e.key === "[") {
                const nextIndex = (currentIndex - 1 + routes.length) % routes.length;
                navigate(routes[nextIndex]);
            } else if (e.key === "]") {
                const nextIndex = (currentIndex + 1) % routes.length;
                navigate(routes[nextIndex]);
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [navigate, location]);

    return null; // Logic only component
};
````

## File: src/components/KOLUpdatesPanel.tsx
````typescript
import { Users, MessageCircle, TrendingUp, TrendingDown, Minus, ExternalLink } from "lucide-react";

const kolUpdates = [
  {
    id: 1,
    name: "CryptoKing",
    handle: "@cryptoking",
    avatar: "CK",
    message: "BTC looking strong at 97k support. Expecting breakout to 100k soon. Long positions loaded.",
    sentiment: "bullish",
    time: "2m ago",
    followers: "1.2M",
    reliability: 87
  },
  {
    id: 2,
    name: "TradeMaster",
    handle: "@trademaster",
    avatar: "TM",
    message: "ETH/BTC ratio showing weakness. Rotating some ETH to BTC for now.",
    sentiment: "neutral",
    time: "8m ago",
    followers: "890K",
    reliability: 92
  },
  {
    id: 3,
    name: "WhaleAlert",
    handle: "@whalealert",
    avatar: "WA",
    message: "⚠️ Large BTC transfer detected: 5,000 BTC moved to exchange. Potential sell pressure incoming.",
    sentiment: "bearish",
    time: "15m ago",
    followers: "2.1M",
    reliability: 95
  },
  {
    id: 4,
    name: "DeFiGuru",
    handle: "@defiguru",
    avatar: "DG",
    message: "SOL ecosystem heating up. Multiple airdrops incoming. Accumulating SOL here.",
    sentiment: "bullish",
    time: "23m ago",
    followers: "567K",
    reliability: 78
  }
];

export const KOLUpdatesPanel = () => {
  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "bullish":
        return <TrendingUp className="w-4 h-4 text-terminal-green" />;
      case "bearish":
        return <TrendingDown className="w-4 h-4 text-danger-red" />;
      default:
        return <Minus className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "bullish":
        return "border-l-terminal-green bg-terminal-green/5";
      case "bearish":
        return "border-l-danger-red bg-danger-red/5";
      default:
        return "border-l-muted-foreground bg-muted/5";
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-primary" />
          <h2 className="panel-title">KOL UPDATES</h2>
        </div>
        <div className="flex items-center gap-2">
          <MessageCircle className="w-3 h-3 text-terminal-green animate-pulse" />
          <span className="text-xs text-terminal-green">LIVE FEED</span>
        </div>
      </div>

      <div className="space-y-3 max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/20">
        {kolUpdates.map((kol) => (
          <div
            key={kol.id}
            className={`p-3 rounded border-l-2 ${getSentimentColor(kol.sentiment)} transition-all hover:bg-muted/10`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-xs font-bold text-primary">
                  {kol.avatar}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-foreground">{kol.name}</span>
                    {getSentimentIcon(kol.sentiment)}
                  </div>
                  <span className="text-xs text-muted-foreground">{kol.handle} • {kol.followers}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="text-xs">
                  <span className="text-muted-foreground">Trust: </span>
                  <span className={kol.reliability >= 85 ? "text-terminal-green" : kol.reliability >= 70 ? "text-primary" : "text-danger-red"}>
                    {kol.reliability}%
                  </span>
                </div>
                <ExternalLink className="w-3 h-3 text-muted-foreground cursor-pointer hover:text-primary" />
              </div>
            </div>
            <p className="text-sm text-foreground/80 mt-2 leading-relaxed">{kol.message}</p>
            <span className="text-xs text-muted-foreground mt-1 block">{kol.time}</span>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-border/30 flex items-center justify-between text-xs text-muted-foreground">
        <span>Tracking 24 KOLs</span>
        <span className="text-primary cursor-pointer hover:underline">View All →</span>
      </div>
    </div>
  );
};
````

## File: src/components/MajorNewsPanel.tsx
````typescript
import { Newspaper, AlertCircle, TrendingUp, TrendingDown, Clock, ExternalLink } from "lucide-react";

const newsData = [
  {
    id: 1,
    title: "Fed signals potential rate pause in upcoming meeting",
    source: "Reuters",
    time: "5m ago",
    impact: "high",
    sentiment: "bullish",
    category: "MACRO",
    summary: "Federal Reserve officials hint at maintaining current rates, citing stable inflation data."
  },
  {
    id: 2,
    title: "BlackRock Bitcoin ETF sees $500M inflow",
    source: "Bloomberg",
    time: "18m ago",
    impact: "high",
    sentiment: "bullish",
    category: "INSTITUTIONAL",
    summary: "Record single-day inflow for IBIT as institutional demand continues to surge."
  },
  {
    id: 3,
    title: "SEC delays decision on Ethereum spot ETF",
    source: "CoinDesk",
    time: "45m ago",
    impact: "medium",
    sentiment: "bearish",
    category: "REGULATORY",
    summary: "Commission extends review period by 60 days, citing need for more public comment."
  },
  {
    id: 4,
    title: "Binance announces expansion into new markets",
    source: "The Block",
    time: "1h ago",
    impact: "medium",
    sentiment: "bullish",
    category: "EXCHANGE",
    summary: "Exchange receives regulatory approval in 3 new jurisdictions."
  },
  {
    id: 5,
    title: "Large whale moves 10,000 BTC to cold storage",
    source: "Whale Alert",
    time: "2h ago",
    impact: "low",
    sentiment: "bullish",
    category: "ON-CHAIN",
    summary: "Long-term holder signal as coins move off exchanges."
  }
];

export const MajorNewsPanel = () => {
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case "high":
        return "bg-danger-red text-danger-red";
      case "medium":
        return "bg-primary text-primary";
      default:
        return "bg-muted-foreground text-muted-foreground";
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    return sentiment === "bullish" ? (
      <TrendingUp className="w-4 h-4 text-terminal-green" />
    ) : (
      <TrendingDown className="w-4 h-4 text-danger-red" />
    );
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      MACRO: "bg-blue-500/20 text-blue-400",
      INSTITUTIONAL: "bg-purple-500/20 text-purple-400",
      REGULATORY: "bg-orange-500/20 text-orange-400",
      EXCHANGE: "bg-cyan-500/20 text-cyan-400",
      "ON-CHAIN": "bg-green-500/20 text-green-400"
    };
    return colors[category] || "bg-muted text-muted-foreground";
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-danger-red" />
          <h2 className="panel-title">MAJOR NEWS</h2>
        </div>
        <div className="flex items-center gap-2">
          <AlertCircle className="w-3 h-3 text-danger-red animate-pulse" />
          <span className="text-xs text-danger-red">HIGH IMPACT</span>
        </div>
      </div>

      <div className="space-y-3 max-h-[350px] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/20">
        {newsData.map((news) => (
          <div
            key={news.id}
            className="p-3 rounded bg-panel-bg/30 border border-border/30 hover:border-primary/30 transition-all cursor-pointer group"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-2 py-0.5 rounded ${getCategoryColor(news.category)}`}>
                    {news.category}
                  </span>
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${getImpactColor(news.impact)} bg-opacity-100`} />
                    <span className="text-xs text-muted-foreground">{news.impact.toUpperCase()}</span>
                  </div>
                </div>
                <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                  {news.title}
                </h3>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{news.summary}</p>
              </div>
              <div className="flex flex-col items-end gap-2">
                {getSentimentIcon(news.sentiment)}
                <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/20">
              <span className="text-xs text-muted-foreground">{news.source}</span>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="w-3 h-3" />
                {news.time}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-border/30 flex items-center justify-between">
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-danger-red" />
            <span className="text-muted-foreground">High: 2</span>
          </span>
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-primary" />
            <span className="text-muted-foreground">Medium: 2</span>
          </span>
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-muted-foreground" />
            <span className="text-muted-foreground">Low: 1</span>
          </span>
        </div>
        <span className="text-xs text-primary cursor-pointer hover:underline">View All News →</span>
      </div>
    </div>
  );
};
````

## File: src/components/MarketOverviewPanel.tsx
````typescript
import { TrendingUp, TrendingDown, Activity } from "lucide-react";

const marketData = [
  { pair: "BTC/USD", price: "97,842.50", change: "+2.34%", trend: "up", volume: "2.4B" },
  { pair: "ETH/USD", price: "3,456.78", change: "+1.87%", trend: "up", volume: "1.2B" },
  { pair: "EUR/USD", price: "1.0845", change: "-0.12%", trend: "down", volume: "890M" },
  { pair: "GBP/USD", price: "1.2634", change: "+0.08%", trend: "up", volume: "456M" },
  { pair: "XAU/USD", price: "2,634.50", change: "-0.45%", trend: "down", volume: "234M" },
  { pair: "SOL/USD", price: "187.45", change: "+5.67%", trend: "up", volume: "567M" },
];

export const MarketOverviewPanel = () => {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-primary animate-pulse" />
          <span className="panel-title">LIVE MARKET FEED</span>
        </div>
        <div className="status-indicator online">
          <span className="w-2 h-2 rounded-full bg-terminal-green animate-pulse" />
          <span className="text-xs">STREAMING</span>
        </div>
      </div>

      <div className="space-y-1">
        {/* Header row */}
        <div className="grid grid-cols-5 gap-2 text-xs text-muted-foreground px-2 py-1 border-b border-primary/20">
          <span>PAIR</span>
          <span className="text-right">PRICE</span>
          <span className="text-right">CHANGE</span>
          <span className="text-right">VOLUME</span>
          <span className="text-center">TREND</span>
        </div>

        {/* Data rows */}
        {marketData.map((item, index) => (
          <div
            key={item.pair}
            className={`grid grid-cols-5 gap-2 text-sm px-2 py-2 font-mono transition-colors hover:bg-primary/10 ${
              index % 2 === 0 ? "bg-panel-bg/50" : "bg-background/50"
            }`}
          >
            <span className="text-primary font-bold">{item.pair}</span>
            <span className="text-right text-foreground">{item.price}</span>
            <span
              className={`text-right ${
                item.trend === "up" ? "text-terminal-green" : "text-danger-red"
              }`}
            >
              {item.change}
            </span>
            <span className="text-right text-muted-foreground">{item.volume}</span>
            <div className="flex justify-center">
              {item.trend === "up" ? (
                <TrendingUp className="w-4 h-4 text-terminal-green" />
              ) : (
                <TrendingDown className="w-4 h-4 text-danger-red" />
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-2 border-t border-primary/20 flex justify-between text-xs text-muted-foreground">
        <span>Last Update: {new Date().toLocaleTimeString()}</span>
        <span className="text-terminal-green">● 6 PAIRS ACTIVE</span>
      </div>
    </div>
  );
};
````

## File: src/components/MarketSentimentPanel.tsx
````typescript
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { Brain, AlertTriangle, Shield, Zap } from "lucide-react";

const sentimentData = [
  { name: "Bullish", value: 62, color: "hsl(var(--terminal-green))" },
  { name: "Bearish", value: 28, color: "hsl(var(--danger-red))" },
  { name: "Neutral", value: 10, color: "hsl(var(--muted-foreground))" },
];

const indicators = [
  { label: "Fear & Greed", value: 72, status: "GREED", icon: Brain },
  { label: "Volatility Index", value: 23, status: "LOW", icon: Zap },
  { label: "Market Risk", value: 34, status: "MODERATE", icon: AlertTriangle },
  { label: "Trend Strength", value: 78, status: "STRONG", icon: Shield },
];

export const MarketSentimentPanel = () => {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-secondary" />
          <span className="panel-title">SENTIMENT ANALYSIS</span>
        </div>
        <div className="text-xs text-muted-foreground font-mono">
          AI CONFIDENCE: 94%
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Pie Chart */}
        <div className="flex flex-col items-center">
          <div className="h-32 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  innerRadius={35}
                  outerRadius={55}
                  dataKey="value"
                  strokeWidth={2}
                  stroke="hsl(var(--background))"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          {/* Legend */}
          <div className="flex gap-4 mt-2">
            {sentimentData.map((item) => (
              <div key={item.name} className="flex items-center gap-1 text-xs">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-muted-foreground">{item.name}</span>
                <span className="font-mono text-foreground">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Indicators */}
        <div className="space-y-2">
          {indicators.map((ind) => (
            <div
              key={ind.label}
              className="flex items-center justify-between bg-panel-bg/50 p-2 rounded border border-primary/10"
            >
              <div className="flex items-center gap-2">
                <ind.icon className="w-3 h-3 text-primary" />
                <span className="text-xs text-muted-foreground">{ind.label}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-16 h-1.5 bg-background rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${ind.value}%`,
                      background:
                        ind.value > 60
                          ? "hsl(var(--terminal-green))"
                          : ind.value > 40
                          ? "hsl(var(--primary))"
                          : "hsl(var(--danger-red))",
                    }}
                  />
                </div>
                <span className="text-xs font-mono text-foreground w-12 text-right">
                  {ind.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 p-2 bg-terminal-green/10 border border-terminal-green/30 rounded">
        <div className="flex items-center gap-2 text-terminal-green text-sm">
          <span className="w-2 h-2 rounded-full bg-terminal-green animate-pulse" />
          <span className="font-mono">MARKET BIAS: BULLISH | RECOMMENDED: LONG POSITIONS</span>
        </div>
      </div>
    </div>
  );
};
````

## File: src/components/MissionLogPanel.tsx
````typescript
import { ArrowUpRight, ArrowDownRight, History } from "lucide-react";

interface Trade {
  id: string;
  time: string;
  pair: string;
  type: 'LONG' | 'SHORT';
  size: string;
  result: 'WIN' | 'LOSS';
  pnl: string;
}

const trades: Trade[] = [
  { id: 'T-0847', time: '14:32:18', pair: 'BTC/USD', type: 'LONG', size: '0.15', result: 'WIN', pnl: '+$234.50' },
  { id: 'T-0846', time: '13:15:42', pair: 'ETH/USD', type: 'SHORT', size: '2.40', result: 'WIN', pnl: '+$156.20' },
  { id: 'T-0845', time: '11:48:09', pair: 'BTC/USD', type: 'LONG', size: '0.10', result: 'LOSS', pnl: '-$89.00' },
  { id: 'T-0844', time: '10:22:31', pair: 'SOL/USD', type: 'LONG', size: '45.00', result: 'WIN', pnl: '+$312.80' },
  { id: 'T-0843', time: '09:05:55', pair: 'ETH/USD', type: 'LONG', size: '1.80', result: 'WIN', pnl: '+$178.40' },
  { id: 'T-0842', time: '08:41:12', pair: 'BTC/USD', type: 'SHORT', size: '0.08', result: 'LOSS', pnl: '-$45.20' },
  { id: 'T-0841', time: '07:18:33', pair: 'XRP/USD', type: 'LONG', size: '1500', result: 'WIN', pnl: '+$89.60' },
  { id: 'T-0840', time: '06:52:47', pair: 'BTC/USD', type: 'LONG', size: '0.12', result: 'WIN', pnl: '+$267.30' },
];

const MissionLogPanel = () => {
  const winCount = trades.filter(t => t.result === 'WIN').length;
  const totalTrades = trades.length;
  const winRate = ((winCount / totalTrades) * 100).toFixed(1);

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="status-indicator status-online" />
        <History className="h-4 w-4 text-primary" />
        <h2 className="panel-title">Mission Log (Trade History)</h2>
        <div className="ml-auto flex items-center gap-4">
          <span className="text-xs text-muted-foreground">
            WIN RATE: <span className="text-terminal-green font-bold">{winRate}%</span>
          </span>
          <span className="text-xs text-muted-foreground">
            TOTAL: <span className="text-primary font-bold">{totalTrades}</span>
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-panel-border bg-muted/30">
              <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">ID</th>
              <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Time</th>
              <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Pair</th>
              <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Type</th>
              <th className="px-4 py-2 text-right text-xs font-bold uppercase tracking-wider text-muted-foreground">Size</th>
              <th className="px-4 py-2 text-center text-xs font-bold uppercase tracking-wider text-muted-foreground">Result</th>
              <th className="px-4 py-2 text-right text-xs font-bold uppercase tracking-wider text-muted-foreground">P&L</th>
            </tr>
          </thead>
          <tbody className="font-mono text-sm">
            {trades.map((trade, index) => (
              <tr 
                key={trade.id}
                className={`
                  border-b border-panel-border/50 transition-colors
                  ${index % 2 === 0 ? 'bg-background/30' : 'bg-muted/20'}
                  ${trade.result === 'WIN' ? 'bg-terminal-green/5' : ''}
                  hover:bg-primary/5
                `}
              >
                <td className="px-4 py-2 text-muted-foreground">{trade.id}</td>
                <td className="px-4 py-2 text-primary tabular-nums">{trade.time}</td>
                <td className="px-4 py-2 text-foreground font-bold">{trade.pair}</td>
                <td className="px-4 py-2">
                  <span className={`inline-flex items-center gap-1 ${
                    trade.type === 'LONG' ? 'text-terminal-green' : 'text-danger-red'
                  }`}>
                    {trade.type === 'LONG' ? (
                      <ArrowUpRight className="h-3 w-3" />
                    ) : (
                      <ArrowDownRight className="h-3 w-3" />
                    )}
                    {trade.type}
                  </span>
                </td>
                <td className="px-4 py-2 text-right tabular-nums text-foreground">{trade.size}</td>
                <td className="px-4 py-2 text-center">
                  <span className={`
                    inline-block px-2 py-0.5 rounded text-xs font-bold
                    ${trade.result === 'WIN' 
                      ? 'bg-terminal-green/20 text-terminal-green' 
                      : 'bg-danger-red/20 text-danger-red'
                    }
                  `}>
                    {trade.result}
                  </span>
                </td>
                <td className={`px-4 py-2 text-right font-bold tabular-nums ${
                  trade.result === 'WIN' ? 'text-terminal-green' : 'text-danger-red'
                }`}>
                  {trade.pnl}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="px-4 py-3 border-t border-panel-border bg-muted/20 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="text-xs">
            <span className="text-muted-foreground">Today's P&L: </span>
            <span className="text-terminal-green font-bold">+$1,104.60</span>
          </div>
          <div className="text-xs">
            <span className="text-muted-foreground">Avg Win: </span>
            <span className="text-terminal-green font-bold">$206.47</span>
          </div>
          <div className="text-xs">
            <span className="text-muted-foreground">Avg Loss: </span>
            <span className="text-danger-red font-bold">-$67.10</span>
          </div>
        </div>
        <div className="text-xs text-muted-foreground">
          Last Updated: <span className="text-primary">14:32:18 UTC</span>
        </div>
      </div>
    </div>
  );
};

export default MissionLogPanel;
````

## File: src/components/NavLink.tsx
````typescript
import { NavLink as RouterNavLink, NavLinkProps } from "react-router-dom";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface NavLinkCompatProps extends Omit<NavLinkProps, "className"> {
  className?: string;
  activeClassName?: string;
  pendingClassName?: string;
}

const NavLink = forwardRef<HTMLAnchorElement, NavLinkCompatProps>(
  ({ className, activeClassName, pendingClassName, to, ...props }, ref) => {
    return (
      <RouterNavLink
        ref={ref}
        to={to}
        className={({ isActive, isPending }) =>
          cn(className, isActive && activeClassName, isPending && pendingClassName)
        }
        {...props}
      />
    );
  },
);

NavLink.displayName = "NavLink";

export { NavLink };
````

## File: src/components/OrderEntryPanel.tsx
````typescript
import { useState } from "react";
import { Send, Shield, Zap } from "lucide-react";

export const OrderEntryPanel = () => {
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("LIMIT");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [price, setPrice] = useState("97,500.00");
  const [size, setSize] = useState("0.10");
  const [stopLoss, setStopLoss] = useState("");
  const [takeProfit, setTakeProfit] = useState("");

  return (
    <div className="panel h-full">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Send className="w-4 h-4 text-primary" />
          <span className="panel-title">ORDER ENTRY</span>
        </div>
        <div className="text-xs font-mono text-terminal-green">BTC/USD</div>
      </div>

      <div className="space-y-4">
        {/* Order Type Toggle */}
        <div className="grid grid-cols-2 gap-2">
          {(["MARKET", "LIMIT"] as const).map((type) => (
            <button
              key={type}
              onClick={() => setOrderType(type)}
              className={`py-2 text-sm font-mono rounded border transition-colors ${
                orderType === type
                  ? "bg-primary/20 border-primary text-primary"
                  : "bg-panel-bg border-primary/20 text-muted-foreground hover:border-primary/50"
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Buy/Sell Toggle */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => setSide("BUY")}
            className={`py-3 text-sm font-mono font-bold rounded transition-colors ${
              side === "BUY"
                ? "bg-terminal-green/20 border-2 border-terminal-green text-terminal-green"
                : "bg-panel-bg border border-primary/20 text-muted-foreground hover:border-terminal-green/50"
            }`}
          >
            LONG / BUY
          </button>
          <button
            onClick={() => setSide("SELL")}
            className={`py-3 text-sm font-mono font-bold rounded transition-colors ${
              side === "SELL"
                ? "bg-danger-red/20 border-2 border-danger-red text-danger-red"
                : "bg-panel-bg border border-primary/20 text-muted-foreground hover:border-danger-red/50"
            }`}
          >
            SHORT / SELL
          </button>
        </div>

        {/* Price Input (for LIMIT orders) */}
        {orderType === "LIMIT" && (
          <div>
            <label className="block text-xs text-muted-foreground mb-1">PRICE (USD)</label>
            <input
              type="text"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full bg-panel-bg border border-primary/30 rounded px-3 py-2 font-mono text-foreground focus:border-primary focus:outline-none"
            />
          </div>
        )}

        {/* Size Input */}
        <div>
          <label className="block text-xs text-muted-foreground mb-1">SIZE (BTC)</label>
          <input
            type="text"
            value={size}
            onChange={(e) => setSize(e.target.value)}
            className="w-full bg-panel-bg border border-primary/30 rounded px-3 py-2 font-mono text-foreground focus:border-primary focus:outline-none"
          />
          <div className="flex gap-2 mt-2">
            {["25%", "50%", "75%", "100%"].map((pct) => (
              <button
                key={pct}
                className="flex-1 py-1 text-xs font-mono bg-panel-bg border border-primary/20 rounded hover:border-primary/50 text-muted-foreground hover:text-primary transition-colors"
              >
                {pct}
              </button>
            ))}
          </div>
        </div>

        {/* Stop Loss / Take Profit */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs text-muted-foreground mb-1 flex items-center gap-1">
              <Shield className="w-3 h-3 text-danger-red" />
              STOP LOSS
            </label>
            <input
              type="text"
              value={stopLoss}
              onChange={(e) => setStopLoss(e.target.value)}
              placeholder="96,000.00"
              className="w-full bg-panel-bg border border-danger-red/30 rounded px-2 py-1.5 font-mono text-sm text-foreground focus:border-danger-red focus:outline-none placeholder:text-muted-foreground/50"
            />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1 flex items-center gap-1">
              <Zap className="w-3 h-3 text-terminal-green" />
              TAKE PROFIT
            </label>
            <input
              type="text"
              value={takeProfit}
              onChange={(e) => setTakeProfit(e.target.value)}
              placeholder="100,000.00"
              className="w-full bg-panel-bg border border-terminal-green/30 rounded px-2 py-1.5 font-mono text-sm text-foreground focus:border-terminal-green focus:outline-none placeholder:text-muted-foreground/50"
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          className={`w-full py-3 font-mono font-bold rounded transition-all ${
            side === "BUY"
              ? "bg-terminal-green text-background hover:bg-terminal-green/80"
              : "bg-danger-red text-background hover:bg-danger-red/80"
          }`}
        >
          {side === "BUY" ? "EXECUTE LONG" : "EXECUTE SHORT"}
        </button>

        {/* Risk Warning */}
        <div className="text-xs text-center text-muted-foreground font-mono">
          EST. RISK: <span className="text-primary">$975.00</span> (1% ACCOUNT)
        </div>
      </div>
    </div>
  );
};
````

## File: src/components/PositionManagerPanel.tsx
````typescript
import { TrendingUp, TrendingDown, DollarSign, Percent } from "lucide-react";

const positions = [
  {
    id: "POS-001",
    pair: "BTC/USD",
    type: "LONG",
    entry: "96,850.00",
    current: "97,842.50",
    size: "0.25",
    leverage: "10x",
    pnl: "+992.50",
    pnlPercent: "+10.25%",
    margin: "2,421.25",
    liquidation: "87,165.00",
  },
  {
    id: "POS-002",
    pair: "ETH/USD",
    type: "LONG",
    entry: "3,420.00",
    current: "3,456.78",
    size: "5.0",
    leverage: "5x",
    pnl: "+183.90",
    pnlPercent: "+1.08%",
    margin: "3,420.00",
    liquidation: "2,736.00",
  },
  {
    id: "POS-003",
    pair: "SOL/USD",
    type: "SHORT",
    entry: "192.50",
    current: "187.45",
    size: "50",
    leverage: "3x",
    pnl: "+252.50",
    pnlPercent: "+2.63%",
    margin: "3,208.33",
    liquidation: "256.67",
  },
];

const totalPnL = positions.reduce((acc, pos) => acc + parseFloat(pos.pnl.replace(/[+,]/g, "")), 0);
const totalMargin = positions.reduce((acc, pos) => acc + parseFloat(pos.margin.replace(/,/g, "")), 0);

export const PositionManagerPanel = () => {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-terminal-green" />
          <span className="panel-title">POSITION MANAGER</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-xs font-mono">
            <span className="text-muted-foreground">TOTAL P&L: </span>
            <span className={totalPnL >= 0 ? "text-terminal-green" : "text-danger-red"}>
              {totalPnL >= 0 ? "+" : ""}${totalPnL.toFixed(2)}
            </span>
          </div>
          <div className="text-xs font-mono">
            <span className="text-muted-foreground">MARGIN USED: </span>
            <span className="text-primary">${totalMargin.toLocaleString()}</span>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {positions.map((pos) => {
          const isLong = pos.type === "LONG";
          const isProfitable = pos.pnl.startsWith("+");

          return (
            <div
              key={pos.id}
              className={`p-3 rounded border ${
                isProfitable
                  ? "bg-terminal-green/5 border-terminal-green/30"
                  : "bg-danger-red/5 border-danger-red/30"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div
                    className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-bold ${
                      isLong
                        ? "bg-terminal-green/20 text-terminal-green"
                        : "bg-danger-red/20 text-danger-red"
                    }`}
                  >
                    {isLong ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    {pos.type}
                  </div>
                  <span className="text-primary font-bold">{pos.pair}</span>
                  <span className="text-xs text-secondary font-mono">{pos.leverage}</span>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div
                      className={`text-lg font-mono font-bold ${
                        isProfitable ? "text-terminal-green" : "text-danger-red"
                      }`}
                    >
                      ${pos.pnl}
                    </div>
                    <div
                      className={`text-xs font-mono ${
                        isProfitable ? "text-terminal-green/70" : "text-danger-red/70"
                      }`}
                    >
                      {pos.pnlPercent}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button className="px-3 py-1 text-xs font-mono bg-primary/20 text-primary rounded hover:bg-primary/30 transition-colors">
                      MODIFY
                    </button>
                    <button className="px-3 py-1 text-xs font-mono bg-danger-red/20 text-danger-red rounded hover:bg-danger-red/30 transition-colors">
                      CLOSE
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-5 gap-4 text-xs">
                <div>
                  <span className="text-muted-foreground">ENTRY</span>
                  <div className="font-mono text-foreground">${pos.entry}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">CURRENT</span>
                  <div className="font-mono text-foreground">${pos.current}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">SIZE</span>
                  <div className="font-mono text-foreground">{pos.size}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">MARGIN</span>
                  <div className="font-mono text-primary">${pos.margin}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">LIQUIDATION</span>
                  <div className="font-mono text-danger-red">${pos.liquidation}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-3 pt-2 border-t border-primary/20 flex justify-between text-xs">
        <span className="text-muted-foreground">Active Positions: {positions.length}</span>
        <button className="text-danger-red hover:text-danger-red/80 font-mono transition-colors">
          CLOSE ALL POSITIONS
        </button>
      </div>
    </div>
  );
};
````

## File: src/components/PriceActionPanel.tsx
````typescript
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { Activity, ArrowUp, ArrowDown } from "lucide-react";
import { useState } from "react";

const generatePriceData = () => {
  const data = [];
  let price = 97500;
  for (let i = 0; i < 48; i++) {
    price += (Math.random() - 0.48) * 200;
    data.push({
      time: `${String(Math.floor(i / 2)).padStart(2, "0")}:${i % 2 === 0 ? "00" : "30"}`,
      price: Math.round(price * 100) / 100,
      volume: Math.floor(Math.random() * 500 + 100),
    });
  }
  return data;
};

const priceData = generatePriceData();

const timeframes = ["1M", "5M", "15M", "1H", "4H", "1D"];

export const PriceActionPanel = () => {
  const [activeTimeframe, setActiveTimeframe] = useState("1H");
  
  const firstPrice = priceData[0].price;
  const lastPrice = priceData[priceData.length - 1].price;
  const priceChange = lastPrice - firstPrice;
  const isPositive = priceChange >= 0;

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            <span className="panel-title">BTC/USD PRICE ACTION</span>
          </div>
          
          <div className="flex items-center gap-1">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => setActiveTimeframe(tf)}
                className={`px-2 py-1 text-xs font-mono rounded transition-colors ${
                  activeTimeframe === tf
                    ? "bg-primary text-primary-foreground"
                    : "bg-panel-bg text-muted-foreground hover:bg-primary/20"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-2xl font-mono font-bold text-foreground">
              ${lastPrice.toLocaleString()}
            </div>
            <div
              className={`flex items-center gap-1 text-sm font-mono ${
                isPositive ? "text-terminal-green" : "text-danger-red"
              }`}
            >
              {isPositive ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
              {isPositive ? "+" : ""}
              {priceChange.toFixed(2)} ({((priceChange / firstPrice) * 100).toFixed(2)}%)
            </div>
          </div>
        </div>
      </div>

      <div className="h-48 mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={priceData}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={isPositive ? "hsl(var(--terminal-green))" : "hsl(var(--danger-red))"}
                  stopOpacity={0.4}
                />
                <stop
                  offset="95%"
                  stopColor={isPositive ? "hsl(var(--terminal-green))" : "hsl(var(--danger-red))"}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
              interval={7}
            />
            <YAxis
              domain={["dataMin - 100", "dataMax + 100"]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
              width={50}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--panel-bg))",
                border: "1px solid hsl(var(--primary))",
                borderRadius: "4px",
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "12px",
              }}
              labelStyle={{ color: "hsl(var(--primary))" }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, "Price"]}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke={isPositive ? "hsl(var(--terminal-green))" : "hsl(var(--danger-red))"}
              strokeWidth={2}
              fill="url(#priceGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 pt-2 border-t border-primary/20 grid grid-cols-4 gap-4 text-xs">
        <div>
          <span className="text-muted-foreground">HIGH</span>
          <div className="font-mono text-terminal-green">$98,234.50</div>
        </div>
        <div>
          <span className="text-muted-foreground">LOW</span>
          <div className="font-mono text-danger-red">$96,890.00</div>
        </div>
        <div>
          <span className="text-muted-foreground">OPEN</span>
          <div className="font-mono text-foreground">$97,125.00</div>
        </div>
        <div>
          <span className="text-muted-foreground">24H VOL</span>
          <div className="font-mono text-primary">2.4B USD</div>
        </div>
      </div>
    </div>
  );
};
````

## File: src/components/RiskManagementPanel.tsx
````typescript
import { useMemo } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { TrendingUp, AlertTriangle } from "lucide-react";

const RiskManagementPanel = () => {
  const accountBalance = 85;
  const riskExposure = 1.5;
  const maxRisk = 5;
  
  const isRiskSafe = riskExposure <= 2;

  const gaugeData = useMemo(() => {
    const percentage = (riskExposure / maxRisk) * 100;
    return [
      { value: percentage, name: "exposure" },
      { value: 100 - percentage, name: "remaining" },
    ];
  }, [riskExposure, maxRisk]);

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="status-indicator status-online" />
        <h2 className="panel-title">Risk Management Core</h2>
        <span className="ml-auto text-xs text-muted-foreground">
          MODULE: RM-CORE-01
        </span>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Account Balance Health Bar */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-terminal-green" />
                <span className="text-xs uppercase tracking-wider text-muted-foreground">
                  Account Balance
                </span>
              </div>
              <span className="font-display text-xl font-bold text-terminal-green data-value">
                {accountBalance}%
              </span>
            </div>
            
            <div className="relative h-6 bg-muted rounded-sm overflow-hidden border border-panel-border">
              <div 
                className="absolute inset-y-0 left-0 rounded-sm transition-all duration-1000"
                style={{ 
                  width: `${accountBalance}%`,
                  background: 'linear-gradient(90deg, hsl(200, 80%, 50%), hsl(142, 70%, 45%))',
                  boxShadow: '0 0 15px hsl(142 70% 45% / 0.5)'
                }}
              />
              {/* Grid lines */}
              <div className="absolute inset-0 flex">
                {[...Array(10)].map((_, i) => (
                  <div 
                    key={i} 
                    className="flex-1 border-r border-background/30 last:border-r-0"
                  />
                ))}
              </div>
            </div>
            
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0%</span>
              <span>CRITICAL</span>
              <span>OPTIMAL</span>
              <span>100%</span>
            </div>
          </div>

          {/* Risk Exposure Gauge */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className={`h-4 w-4 ${isRiskSafe ? 'text-terminal-green' : 'text-danger-red'}`} />
                <span className="text-xs uppercase tracking-wider text-muted-foreground">
                  Risk Exposure
                </span>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded ${isRiskSafe ? 'bg-terminal-green/20 text-terminal-green' : 'bg-danger-red/20 text-danger-red'}`}>
                {isRiskSafe ? 'SAFE ZONE' : 'DANGER'}
              </span>
            </div>

            <div className="relative flex items-center justify-center">
              <div className="w-48 h-24 overflow-hidden">
                <ResponsiveContainer width="100%" height={192}>
                  <PieChart>
                    <Pie
                      data={gaugeData}
                      cx="50%"
                      cy="100%"
                      startAngle={180}
                      endAngle={0}
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={0}
                      dataKey="value"
                      stroke="none"
                    >
                      <Cell 
                        fill={isRiskSafe ? "hsl(142, 70%, 45%)" : "hsl(0, 84%, 50%)"} 
                        style={{ 
                          filter: `drop-shadow(0 0 10px ${isRiskSafe ? 'hsl(142, 70%, 45%)' : 'hsl(0, 84%, 50%)'})`
                        }}
                      />
                      <Cell fill="hsl(0, 0%, 15%)" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              
              {/* Center Value */}
              <div className="absolute bottom-0 text-center">
                <span className={`font-display text-2xl font-bold data-value ${isRiskSafe ? 'text-terminal-green' : 'text-danger-red'}`}>
                  {riskExposure}%
                </span>
              </div>
            </div>

            <div className="flex justify-between text-xs text-muted-foreground px-4">
              <span>0%</span>
              <span className="text-terminal-green">2% MAX SAFE</span>
              <span>{maxRisk}%</span>
            </div>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="mt-6 grid grid-cols-4 gap-4 border-t border-panel-border pt-4">
          {[
            { label: 'MARGIN LEVEL', value: '1,245%', status: 'safe' },
            { label: 'DRAWDOWN', value: '3.2%', status: 'safe' },
            { label: 'OPEN POSITIONS', value: '3', status: 'warning' },
            { label: 'EQUITY', value: '$12,847', status: 'safe' },
          ].map((item) => (
            <div key={item.label} className="text-center">
              <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
              <p className={`font-display text-sm font-bold ${
                item.status === 'safe' ? 'text-terminal-green' : 
                item.status === 'warning' ? 'text-primary' : 'text-danger-red'
              }`}>
                {item.value}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RiskManagementPanel;
````

## File: src/context/SocketContext.tsx
````typescript
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  lastError: string | null;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

// Defaults to localhost:8000 if not specified in env
const SOCKET_URL = import.meta.env.VITE_WS_URL || 'http://localhost:8000';

export const SocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);

  useEffect(() => {
    const newSocket = io(SOCKET_URL, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
      setLastError(null);
    });

    newSocket.on('disconnect', () => {
      console.log('Socket disconnected');
      setIsConnected(false);
    });

    newSocket.on('connect_error', (err) => {
      console.error('Socket connection error:', err);
      setIsConnected(false);
      setLastError(err.message);
    });

    newSocket.on('error', (data: any) => {
        console.error('Socket operational error:', data);
        // If data is an object with message, extract it, otherwise stringify
        const msg = data?.message || (typeof data === 'string' ? data : JSON.stringify(data));
        setLastError(msg);
    });

    return () => {
      newSocket.close();
    };
  }, []);

  return (
    <SocketContext.Provider value={{ socket, isConnected, lastError }}>
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = (): SocketContextType => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};
````

## File: src/hooks/use-mobile.tsx
````typescript
import * as React from "react";

const MOBILE_BREAKPOINT = 768;

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(undefined);

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    };
    mql.addEventListener("change", onChange);
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return !!isMobile;
}
````

## File: src/hooks/use-toast.ts
````typescript
import * as React from "react";

import type { ToastActionElement, ToastProps } from "@/components/ui/toast";

const TOAST_LIMIT = 1;
const TOAST_REMOVE_DELAY = 1000000;

type ToasterToast = ToastProps & {
  id: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: ToastActionElement;
};

const actionTypes = {
  ADD_TOAST: "ADD_TOAST",
  UPDATE_TOAST: "UPDATE_TOAST",
  DISMISS_TOAST: "DISMISS_TOAST",
  REMOVE_TOAST: "REMOVE_TOAST",
} as const;

let count = 0;

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER;
  return count.toString();
}

type ActionType = typeof actionTypes;

type Action =
  | {
      type: ActionType["ADD_TOAST"];
      toast: ToasterToast;
    }
  | {
      type: ActionType["UPDATE_TOAST"];
      toast: Partial<ToasterToast>;
    }
  | {
      type: ActionType["DISMISS_TOAST"];
      toastId?: ToasterToast["id"];
    }
  | {
      type: ActionType["REMOVE_TOAST"];
      toastId?: ToasterToast["id"];
    };

interface State {
  toasts: ToasterToast[];
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>();

const addToRemoveQueue = (toastId: string) => {
  if (toastTimeouts.has(toastId)) {
    return;
  }

  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId);
    dispatch({
      type: "REMOVE_TOAST",
      toastId: toastId,
    });
  }, TOAST_REMOVE_DELAY);

  toastTimeouts.set(toastId, timeout);
};

export const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case "ADD_TOAST":
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
      };

    case "UPDATE_TOAST":
      return {
        ...state,
        toasts: state.toasts.map((t) => (t.id === action.toast.id ? { ...t, ...action.toast } : t)),
      };

    case "DISMISS_TOAST": {
      const { toastId } = action;

      // ! Side effects ! - This could be extracted into a dismissToast() action,
      // but I'll keep it here for simplicity
      if (toastId) {
        addToRemoveQueue(toastId);
      } else {
        state.toasts.forEach((toast) => {
          addToRemoveQueue(toast.id);
        });
      }

      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === toastId || toastId === undefined
            ? {
                ...t,
                open: false,
              }
            : t,
        ),
      };
    }
    case "REMOVE_TOAST":
      if (action.toastId === undefined) {
        return {
          ...state,
          toasts: [],
        };
      }
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.toastId),
      };
  }
};

const listeners: Array<(state: State) => void> = [];

let memoryState: State = { toasts: [] };

function dispatch(action: Action) {
  memoryState = reducer(memoryState, action);
  listeners.forEach((listener) => {
    listener(memoryState);
  });
}

type Toast = Omit<ToasterToast, "id">;

function toast({ ...props }: Toast) {
  const id = genId();

  const update = (props: ToasterToast) =>
    dispatch({
      type: "UPDATE_TOAST",
      toast: { ...props, id },
    });
  const dismiss = () => dispatch({ type: "DISMISS_TOAST", toastId: id });

  dispatch({
    type: "ADD_TOAST",
    toast: {
      ...props,
      id,
      open: true,
      onOpenChange: (open) => {
        if (!open) dismiss();
      },
    },
  });

  return {
    id: id,
    dismiss,
    update,
  };
}

function useToast() {
  const [state, setState] = React.useState<State>(memoryState);

  React.useEffect(() => {
    listeners.push(setState);
    return () => {
      const index = listeners.indexOf(setState);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }, [state]);

  return {
    ...state,
    toast,
    dismiss: (toastId?: string) => dispatch({ type: "DISMISS_TOAST", toastId }),
  };
}

export { useToast, toast };
````

## File: src/hooks/useGamepad.ts
````typescript
import { useEffect, useRef } from "react";

// Xbox Controller Standard Mapping (Standard Gamepad API)
// Buttons:
// 0: A
// 1: B
// 2: X
// 3: Y
// 4: LB
// 5: RB
// 6: LT (Analog, but often registers as button too)
// 7: RT
// 8: Back/View
// 9: Start/Menu
// 10: Left Stick Click
// 11: Right Stick Click
// 12: D-Pad Up
// 13: D-Pad Down
// 14: D-Pad Left
// 15: D-Pad Right

// Axes:
// 0: Left Stick X
// 1: Left Stick Y
// 2: Right Stick X
// 3: Right Stick Y

interface GamepadConfig {
    enableScrolling?: boolean;
    scrollSpeed?: number;
}

export const useGamepad = (config: GamepadConfig = {}) => {
    const { enableScrolling = true, scrollSpeed = 15 } = config;
    const requestRef = useRef<number>();
    const lastPressedRef = useRef<Set<number>>(new Set());
    const lastScrollTimeRef = useRef<number>(0);

    useEffect(() => {
        const pollGamepad = () => {
            const gamepads = navigator.getGamepads();
            const gp = gamepads[0]; // Assuming player 1

            if (gp) {
                const pressed = new Set<number>();

                // Check Buttons
                gp.buttons.forEach((btn, index) => {
                    if (btn.pressed) {
                        pressed.add(index);

                        // Trigger on PRESS (rising edge)
                        if (!lastPressedRef.current.has(index)) {
                            handleButtonPress(index);
                        }
                    }
                });

                lastPressedRef.current = pressed;

                // Check Axes for Scrolling
                if (enableScrolling) {
                    const now = Date.now();
                    if (now - lastScrollTimeRef.current > 16) { // Cap at ~60fps
                        const rightStickY = gp.axes[3];
                        if (Math.abs(rightStickY) > 0.2) { // Deadzone
                            window.scrollBy(0, rightStickY * scrollSpeed);
                            lastScrollTimeRef.current = now;
                        }
                    }
                }
            }

            requestRef.current = requestAnimationFrame(pollGamepad);
        };

        const handleButtonPress = (buttonIndex: number) => {
            let key = "";

            switch (buttonIndex) {
                case 0: key = "Enter"; break; // A -> Confirm
                case 1: key = "b"; break;     // B -> Back/Close
                case 2: key = "x"; break;     // X -> Action/Modify
                case 3: key = "y"; break;     // Y -> Alternative Action
                case 4: key = "q"; break;     // LB -> Tab Left
                case 5: key = "e"; break;     // RB -> Tab Right
                case 6: key = "["; break;     // LT -> Prev Monitor
                case 7: key = "]"; break;     // RT -> Next Monitor
                case 8: key = "m"; break;     // Back/View -> Mute
                case 9: key = "p"; break;     // Start/Menu -> Play
                case 10: key = "v"; break;    // L3 -> Talk
                case 12: key = "ArrowUp"; break;
                case 13: key = "ArrowDown"; break;
                case 14: key = "ArrowLeft"; break;
                case 15: key = "ArrowRight"; break;
            }

            if (key) {
                // Dispatch synthetic event
                const event = new KeyboardEvent("keydown", {
                    key: key,
                    code: key,
                    bubbles: true,
                    cancelable: true,
                    view: window,
                });
                window.dispatchEvent(event);
            }
        };

        requestRef.current = requestAnimationFrame(pollGamepad);

        return () => {
            if (requestRef.current) {
                cancelAnimationFrame(requestRef.current);
            }
        };
    }, [enableScrolling, scrollSpeed]);
};
````

## File: src/lib/utils.ts
````typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
````

## File: src/pages/Action.tsx
````typescript
import { useState, useCallback, useEffect } from "react";
import { SystemHeader } from "@/components/SystemHeader";
import { GamepadQuickTrade } from "@/components/GamepadQuickTrade";
import { GamepadPositions } from "@/components/GamepadPositions";
import { GamepadControllerHints } from "@/components/GamepadControllerHints";

import { SocketProvider } from "@/context/SocketContext";

const Action = () => {
  const [activeSection, setActiveSection] = useState<"portfolio" | "plan" | "action">("portfolio");

  // Gamepad navigation (mapped to q/w/e)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Use q/w/e for tab switching
      if (e.key === "q") {
        setActiveSection("portfolio");
      } else if (e.key === "w") {
        setActiveSection("plan");
      } else if (e.key === "e") {
        setActiveSection("action");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <SocketProvider>
      <div className="min-h-screen bg-background text-foreground p-4 relative overflow-hidden">
        {/* Scanlines overlay */}
        <div className="scanlines" />

        {/* CRT flicker effect */}
        <div className="crt-flicker" />

        {/* Main content */}
        <div className="relative z-10 max-w-7xl mx-auto space-y-4">
          <SystemHeader monitorNumber={2} title="ACTIONS" />

          {/* Section Tabs - Big gamepad-friendly buttons */}
          <div className="grid grid-cols-3 gap-4">
            <button
              onClick={() => setActiveSection("portfolio")}
              className={`gamepad-tile group ${activeSection === "portfolio" ? "gamepad-tile-active" : ""
                }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="gamepad-button-hint">Q</div>
                  <span className="text-xl font-display tracking-wider">PORTFOLIO</span>
                </div>
                {activeSection === "portfolio" && (
                  <div className="w-3 h-3 rounded-full bg-terminal-green animate-pulse" />
                )}
              </div>
            </button>

            <button
              onClick={() => setActiveSection("plan")}
              className={`gamepad-tile group ${activeSection === "plan" ? "gamepad-tile-active" : ""
                }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="gamepad-button-hint">W</div>
                  <span className="text-xl font-display tracking-wider">PLAN</span>
                </div>
                {activeSection === "plan" && (
                  <div className="w-3 h-3 rounded-full bg-terminal-green animate-pulse" />
                )}
              </div>
            </button>

            <button
              onClick={() => setActiveSection("action")}
              className={`gamepad-tile group ${activeSection === "action" ? "gamepad-tile-active" : ""
                }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="gamepad-button-hint">E</div>
                  <span className="text-xl font-display tracking-wider">ACTION</span>
                </div>
                {activeSection === "action" && (
                  <div className="w-3 h-3 rounded-full bg-terminal-green animate-pulse" />
                )}
              </div>
            </button>
          </div>

          {/* Main Content Area */}
          <div className="min-h-[60vh]">
            {activeSection === "portfolio" ? (
              <GamepadPositions />
            ) : activeSection === "plan" ? (
              <GamepadQuickTrade />
            ) : (
              <GamepadQuickTrade />
            )}
          </div>

          {/* Controller Hints Footer */}
          <GamepadControllerHints />
        </div>
      </div>
    </SocketProvider>
  );
};

export default Action;
````

## File: src/pages/NotFound.tsx
````typescript
import { useLocation } from "react-router-dom";
import { useEffect } from "react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted">
      <div className="text-center">
        <h1 className="mb-4 text-4xl font-bold">404</h1>
        <p className="mb-4 text-xl text-muted-foreground">Oops! Page not found</p>
        <a href="/" className="text-primary underline hover:text-primary/90">
          Return to Home
        </a>
      </div>
    </div>
  );
};

export default NotFound;
````

## File: src/pages/Plan.tsx
````typescript
import { SystemHeader } from "@/components/SystemHeader";
import { MarketOverviewPanel } from "@/components/MarketOverviewPanel";
import { PriceActionPanel } from "@/components/PriceActionPanel";
import { MarketSentimentPanel } from "@/components/MarketSentimentPanel";
import { KOLUpdatesPanel } from "@/components/KOLUpdatesPanel";
import { AIAnalysisPanel } from "@/components/AIAnalysisPanel";
import { MajorNewsPanel } from "@/components/MajorNewsPanel";
import CapitalCompanionPanel from "@/components/CapitalCompanionPanel";

const Plan = () => {
  return (
    <div className="min-h-screen bg-background text-foreground relative">
      {/* Scanlines overlay */}
      <div className="scanlines" />

      {/* CRT flicker effect */}
      <div className="crt-flicker" />

      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto">
        <div className="p-4 pb-0">
          <SystemHeader monitorNumber={1} title="PLAN" />
        </div>

        {/* Top: Capital Companion Logic - Sticky */}
        <div className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 p-4 border-b border-border/50 shadow-md">
          <CapitalCompanionPanel />
        </div>

        <div className="p-4 space-y-4">
          {/* Row 1: Market Overview & Sentiment */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <MarketOverviewPanel />
            <MarketSentimentPanel />
          </div>

          {/* Row 2: Price Action */}
          <PriceActionPanel />

          {/* Row 3: KOL Updates, AI Analysis, Major News */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <KOLUpdatesPanel />
            <AIAnalysisPanel />
            <MajorNewsPanel />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Plan;
````

## File: src/pages/Portfolio.tsx
````typescript
import { SystemHeader } from "@/components/SystemHeader";
import RiskManagementPanel from "@/components/RiskManagementPanel";
import MissionLogPanel from "@/components/MissionLogPanel";

const Index = () => {
  return (
    <div className="min-h-screen bg-background text-foreground p-4 relative overflow-hidden">
      {/* Scanlines overlay */}
      <div className="scanlines" />

      {/* CRT flicker effect */}
      <div className="crt-flicker" />

      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto space-y-4">
        <SystemHeader monitorNumber={3} title="PORTFOLIO" />

        {/* Top Panel: Risk Management Core */}
        <RiskManagementPanel />

        {/* Bottom Panel: Mission Log */}
        <MissionLogPanel />
      </div>

      {/* Corner Decorations */}
      <div className="fixed top-0 left-0 w-16 h-16 border-l-2 border-t-2 border-primary/30 pointer-events-none" />
      <div className="fixed top-0 right-0 w-16 h-16 border-r-2 border-t-2 border-primary/30 pointer-events-none" />
      <div className="fixed bottom-0 left-0 w-16 h-16 border-l-2 border-b-2 border-primary/30 pointer-events-none" />
      <div className="fixed bottom-0 right-0 w-16 h-16 border-r-2 border-b-2 border-primary/30 pointer-events-none" />

      {/* Version Watermark */}
      <div className="fixed bottom-4 right-4 text-xs text-muted-foreground/50 font-mono pointer-events-none">
        TRADING COMMAND CENTER v3.1.4
      </div>
    </div>
  );
};

export default Index;
````

## File: src/App.css
````css
#root {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.react:hover {
  filter: drop-shadow(0 0 2em #61dafbaa);
}

@keyframes logo-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: no-preference) {
  a:nth-of-type(2) .logo {
    animation: logo-spin infinite 20s linear;
  }
}

.card {
  padding: 2em;
}

.read-the-docs {
  color: #888;
}
````

## File: src/main.tsx
````typescript
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

createRoot(document.getElementById("root")!).render(<App />);
````

## File: src/vite-env.d.ts
````typescript
/// <reference types="vite/client" />
````

## File: .repomixignore
````
docs/*
plans/*
assets/*
dist/*
coverage/*
build/*
ios/*
android/*
tests/*
__tests__/*
__pycache__/*
node_modules/*

.opencode/*
.claude/*
.serena/*
.pnpm-store/*
.github/*
.dart_tool/*
.idea/*
.husky/*
.venv/*
````

## File: components.json
````json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
````

## File: eslint.config.js
````javascript
import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      "@typescript-eslint/no-unused-vars": "off",
    },
  },
);
````

## File: index.html
````html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <!-- TODO: Set the document title to the name of your application -->
    <title>Lovable App</title>
    <meta name="description" content="Lovable Generated Project" />
    <meta name="author" content="Lovable" />

    <!-- TODO: Update og:title to match your application name -->
    <meta property="og:title" content="Lovable App" />
    <meta property="og:description" content="Lovable Generated Project" />
    <meta property="og:type" content="website" />
    <meta property="og:image" content="https://lovable.dev/opengraph-image-p98pqg.png" />

    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:site" content="@Lovable" />
    <meta name="twitter:image" content="https://lovable.dev/opengraph-image-p98pqg.png" />
  </head>

  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
````

## File: postcss.config.js
````javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
````

## File: tsconfig.app.json
````json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": false,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noImplicitAny": false,
    "noFallthroughCasesInSwitch": false,

    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
````

## File: tsconfig.json
````json
{
  "files": [],
  "references": [{ "path": "./tsconfig.app.json" }, { "path": "./tsconfig.node.json" }],
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    },
    "noImplicitAny": false,
    "noUnusedParameters": false,
    "skipLibCheck": true,
    "allowJs": true,
    "noUnusedLocals": false,
    "strictNullChecks": false
  }
}
````

## File: tsconfig.node.json
````json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,

    /* Linting */
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["vite.config.ts"]
}
````

## File: vite.config.ts
````typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
````

## File: backend/app/mt5/error_handler.py
````python
import MetaTrader5 as mt5
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MT5ErrorHandler:
    # Retriable return codes
    RETRIABLE_CODES = {
        mt5.TRADE_RETCODE_REQUOTE,
        mt5.TRADE_RETCODE_TIMEOUT,
        mt5.TRADE_RETCODE_PRICE_OFF,
        mt5.TRADE_RETCODE_PRICE_CHANGED,
        mt5.TRADE_RETCODE_CONNECTION,
    }

    # Common error messages map (fallback if MT5 doesn't provide clear desc)
    ERROR_MESSAGES = {
        mt5.TRADE_RETCODE_DONE: "Request completed",
        mt5.TRADE_RETCODE_DONE_PARTIAL: "Request completed partially",
        mt5.TRADE_RETCODE_ERROR: "Common error",
        mt5.TRADE_RETCODE_TIMEOUT: "Request timed out",
        mt5.TRADE_RETCODE_INVALID: "Invalid request",
        mt5.TRADE_RETCODE_REQUOTE: "Requote",
        mt5.TRADE_RETCODE_PRICE_OFF: "Price is off quotes",
        mt5.TRADE_RETCODE_PRICE_CHANGED: "Price changed",
        mt5.TRADE_RETCODE_INVALID_PRICE: "Invalid price",
        mt5.TRADE_RETCODE_CONNECTION: "No connection",
    }

    @staticmethod
    def is_retriable(retcode: int) -> bool:
        """Check if the error code indicates the operation should be retried."""
        return retcode in MT5ErrorHandler.RETRIABLE_CODES

    @staticmethod
    def get_error_message(retcode: int) -> str:
        """Get human-readable error message for a return code."""
        return MT5ErrorHandler.ERROR_MESSAGES.get(retcode, f"Unknown error code: {retcode}")

    @staticmethod
    def order_with_retry(
        request: Dict[str, Any], 
        max_retries: int = 3, 
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Execute an order request with retry logic for retriable errors.
        This is a synchronous method (run in thread).
        """
        for attempt in range(max_retries):
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                logger.error("Order send returned None (MT5 internal error)")
                return {"retcode": mt5.TRADE_RETCODE_ERROR, "comment": "Internal MT5 API error"}
                
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return result._asdict()
            
            if MT5ErrorHandler.is_retriable(result.retcode):
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Retriable error {result.retcode} ({result.comment}), "
                        f"retrying in {retry_delay}s (Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    continue
            
            # If we get here, it's either success (handled above), 
            # non-retriable error, or out of retries
            logger.error(f"Order failed: {result.retcode} - {result.comment}")
            return result._asdict()
            
        return {"retcode": mt5.TRADE_RETCODE_TIMEOUT, "comment": "Max retries exceeded"}
````

## File: backend/app/mt5/trading_operations.py
````python
import MetaTrader5 as mt5
import logging
from typing import Dict, Any, Optional, List
from .connection_manager import MT5ConnectionManager
from .error_handler import MT5ErrorHandler
from ..config import config

logger = logging.getLogger(__name__)

class TradingOperations:
    """
    Handles all trading operations including order placement, modification, and closing.
    """
    def __init__(self, connection_manager: MT5ConnectionManager):
        self.conn = connection_manager

    def place_market_order(
        self, 
        symbol: str, 
        volume: float, 
        order_type: int, 
        sl: Optional[float] = None, 
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Place a market order (Buy or Sell)."""
        if not self.conn.is_connected():
            return {"retcode": mt5.TRADE_RETCODE_CONNECTION, "comment": "Not connected to MT5"}

        if not self.conn.is_autotrading_enabled():
            return {"retcode": mt5.TRADE_RETCODE_ERROR, "comment": "AutoTrading disabled in MT5 Terminal"}

        if not self._validate_symbol(symbol):
            return {"retcode": mt5.TRADE_RETCODE_INVALID, "comment": f"Symbol {symbol} not found or not visible"}

        price = self._get_market_price(symbol, order_type)
        if price is None:
            return {"retcode": mt5.TRADE_RETCODE_INVALID_PRICE, "comment": "Failed to get market price"}

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": int(config.DEFAULT_SLIPPAGE),
            "magic": 123456,  # TODO: Make configurable
            "comment": "SocketIO Server",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._get_filling_mode(symbol),
        }

        if sl:
            request["sl"] = sl
        if tp:
            request["tp"] = tp

        logger.info(f"Placing order: {symbol} {volume} lots @ {price}")
        return MT5ErrorHandler.order_with_retry(request)

    def place_buy_market(self, symbol: str, volume: float, sl: float = None, tp: float = None) -> Dict[str, Any]:
        """Convenience method for Buy Market order."""
        return self.place_market_order(symbol, volume, mt5.ORDER_TYPE_BUY, sl, tp)

    def place_sell_market(self, symbol: str, volume: float, sl: float = None, tp: float = None) -> Dict[str, Any]:
        """Convenience method for Sell Market order."""
        return self.place_market_order(symbol, volume, mt5.ORDER_TYPE_SELL, sl, tp)

    def modify_position(
        self, 
        ticket: int, 
        new_sl: Optional[float] = None, 
        new_tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Modify SL/TP of an existing position."""
        if not self.conn.is_connected():
            return {"retcode": mt5.TRADE_RETCODE_CONNECTION, "comment": "Not connected"}

        if not self.conn.is_autotrading_enabled():
            return {"retcode": mt5.TRADE_RETCODE_ERROR, "comment": "AutoTrading disabled in MT5 Terminal"}

        position = self.get_position(ticket)
        if not position:
            return {"retcode": mt5.TRADE_RETCODE_INVALID, "comment": "Position not found"}

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": position['symbol'],
            "sl": new_sl if new_sl is not None else position['sl'],
            "tp": new_tp if new_tp is not None else position['tp'],
        }

        logger.info(f"Modifying position {ticket}: SL={request['sl']}, TP={request['tp']}")
        return MT5ErrorHandler.order_with_retry(request)

    def close_position(self, ticket: int, volume: Optional[float] = None) -> Dict[str, Any]:
        """Close an existing position (full or partial)."""
        if not self.conn.is_connected():
            return {"retcode": mt5.TRADE_RETCODE_CONNECTION, "comment": "Not connected"}

        if not self.conn.is_autotrading_enabled():
            return {"retcode": mt5.TRADE_RETCODE_ERROR, "comment": "AutoTrading disabled in MT5 Terminal"}

        position = self.get_position(ticket)
        if not position:
            return {"retcode": mt5.TRADE_RETCODE_INVALID, "comment": "Position not found"}

        symbol = position['symbol']
        lot = volume if volume else position['volume']
        
        # Determine close type (Opposite of open type)
        order_type = mt5.ORDER_TYPE_SELL if position['type'] == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = self._get_market_price(symbol, order_type)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "deviation": int(config.DEFAULT_SLIPPAGE),
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._get_filling_mode(symbol),
        }

        logger.info(f"Closing position {ticket}: {lot} lots")
        return MT5ErrorHandler.order_with_retry(request)

    def get_position(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Get position details by ticket."""
        positions = mt5.positions_get(ticket=ticket)
        if positions and len(positions) > 0:
            return positions[0]._asdict()
        return None

    def get_all_positions(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open positions, optionally filtered by symbol."""
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
            
        if positions:
            return [p._asdict() for p in positions]
        return []

    def _validate_symbol(self, symbol: str) -> bool:
        """Check if symbol exists and is visible in Market Watch."""
        sym = mt5.symbol_info(symbol)
        if sym is None:
            # Try to select it
            if not mt5.symbol_select(symbol, True):
                return False
            sym = mt5.symbol_info(symbol)
            return sym is not None
        
        if not sym.visible:
            if not mt5.symbol_select(symbol, True):
                return False
        
        return True

    def _get_market_price(self, symbol: str, order_type: int) -> Optional[float]:
        """Get the correct price for the order type."""
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        
        if order_type == mt5.ORDER_TYPE_BUY:
            return tick.ask
        elif order_type == mt5.ORDER_TYPE_SELL:
            return tick.bid
        return None

    def _get_filling_mode(self, symbol: str) -> int:
        """Determine appropriate filling mode for symbol."""
        # This can be more complex based on symbol properties
        # For now, rely on config or default to IOC
        filling = config.ORDER_FILLING_TYPE
        if filling == "FOK":
            return mt5.ORDER_FILLING_FOK
        elif filling == "RETURN":
            return mt5.ORDER_FILLING_RETURN
        return mt5.ORDER_FILLING_IOC
````

## File: backend/app/config.py
````python
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # MT5 Credentials
    ACCOUNT_NUMBER: int = int(os.getenv("MT5_ACCOUNT", "0"))
    ACCOUNT_PASSWORD: str = os.getenv("MT5_PASSWORD", "")
    BROKER_SERVER: str = os.getenv("MT5_SERVER", "")

    # Connection
    CONNECTION_TIMEOUT: float = float(os.getenv("MT5_CONN_TIMEOUT", "30.0"))
    HEALTH_CHECK_INTERVAL: float = float(os.getenv("MT5_HEALTH_INTERVAL", "5.0"))

    # Retry
    MAX_ORDER_RETRIES: int = int(os.getenv("MT5_MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("MT5_RETRY_DELAY", "1.0"))

    # Trading
    DEFAULT_SLIPPAGE: float = float(os.getenv("MT5_SLIPPAGE", "20.0")) 
    ORDER_FILLING_TYPE: str = os.getenv("MT5_FILLING", "IOC")

    # Socket.IO Server
    SOCKETIO_HOST: str = os.getenv('SOCKETIO_HOST', '0.0.0.0')
    SOCKETIO_PORT: int = int(os.getenv('SOCKETIO_PORT', '8686'))
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'

    # Redis
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))

config = Config()
````

## File: backend/app/logging_config.py
````python
import logging
import sys

def setup_logging(debug: bool = False, json_format: bool = False):
    level = logging.DEBUG if debug else logging.INFO

    if json_format:
        # JSON structured logging for production
        try:
            from pythonjsonlogger import jsonlogger

            handler = logging.StreamHandler(sys.stdout)
            formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
            handler.setFormatter(formatter)

            logging.basicConfig(
                level=level,
                handlers=[handler]
            )
        except ImportError:
            # Fallback to standard logging
            logging.basicConfig(
                level=level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
    else:
        # Standard logging for development
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    return logging.getLogger("app")
````

## File: src/components/SystemHeader.tsx
````typescript
import { Activity, Shield, Wifi } from "lucide-react";
import { MonitorNav } from "./MonitorNav";

interface SystemHeaderProps {
  monitorNumber: number;
  title: string;
}

export const SystemHeader = ({ monitorNumber, title }: SystemHeaderProps) => {
  const currentTime = new Date().toLocaleTimeString('en-US', { 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });

  return (
    <header className="border-b border-primary/30 bg-panel-bg/50 px-4 py-3 rounded-t">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <h1 className="font-display text-lg font-bold tracking-wider text-primary">
              MONITOR {monitorNumber}
            </h1>
          </div>
          <span className="text-xs text-muted-foreground tracking-widest">
            {title}
          </span>
        </div>

        <MonitorNav />

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-terminal-green animate-pulse" />
            <span className="text-xs text-terminal-green">ONLINE</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Wifi className="h-4 w-4 text-primary" />
            <span className="text-xs text-muted-foreground">UPLINK: STABLE</span>
          </div>

          <div className="font-mono text-sm text-primary tabular-nums">
            {currentTime}
          </div>
        </div>
      </div>
    </header>
  );
};

export default SystemHeader;
````

## File: CLAUDE.md
````markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role & Responsibilities

Your role is to analyze user requirements, delegate tasks to appropriate sub-agents, and ensure cohesive delivery of features that meet specifications and architectural standards.

## Workflows

- Primary workflow: `./.claude/workflows/primary-workflow.md`
- Development rules: `./.claude/workflows/development-rules.md`
- Orchestration protocols: `./.claude/workflows/orchestration-protocol.md`
- Documentation management: `./.claude/workflows/documentation-management.md`
- And other workflows: `./.claude/workflows/*`

**IMPORTANT:** Analyze the skills catalog and activate the skills that are needed for the task during the process.
**IMPORTANT:** You must follow strictly the development rules in `./.claude/workflows/development-rules.md` file.
**IMPORTANT:** Before you plan or proceed any implementation, always read the `./README.md` file first to get context.
**IMPORTANT:** Sacrifice grammar for the sake of concision when writing reports.
**IMPORTANT:** In reports, list any unresolved questions at the end, if any.

## Python Scripts (Skills)

When running Python scripts from `.claude/skills/`, use the venv Python interpreter:
- **Linux/macOS:** `.claude/skills/.venv/bin/python3 scripts/xxx.py`
- **Windows:** `.claude\skills\.venv\Scripts\python.exe scripts\xxx.py`

This ensures packages installed by `install.sh` (google-genai, pypdf, etc.) are available.

## Documentation Management

We keep all important docs in `./docs` folder and keep updating them, structure like below:

```
./docs
├── project-overview-pdr.md
├── code-standards.md
├── codebase-summary.md
├── design-guidelines.md
├── deployment-guide.md
├── system-architecture.md
└── project-roadmap.md
```

**IMPORTANT:** *MUST READ* and *MUST COMPLY* all *INSTRUCTIONS* in project `./CLAUDE.md`, especially *WORKFLOWS* section is *CRITICALLY IMPORTANT*, this rule is *MANDATORY. NON-NEGOTIABLE. NO EXCEPTIONS. MUST REMEMBER AT ALL TIMES!!!*
````

## File: package.json
````json
{
  "name": "vite_react_shadcn_ts",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "build:dev": "vite build --mode development",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "@hookform/resolvers": "^3.10.0",
    "@radix-ui/react-accordion": "^1.2.12",
    "@radix-ui/react-alert-dialog": "^1.1.15",
    "@radix-ui/react-aspect-ratio": "^1.1.8",
    "@radix-ui/react-avatar": "^1.1.11",
    "@radix-ui/react-checkbox": "^1.3.3",
    "@radix-ui/react-collapsible": "^1.1.12",
    "@radix-ui/react-context-menu": "^2.2.16",
    "@radix-ui/react-dialog": "^1.1.15",
    "@radix-ui/react-dropdown-menu": "^2.1.16",
    "@radix-ui/react-hover-card": "^1.1.15",
    "@radix-ui/react-label": "^2.1.8",
    "@radix-ui/react-menubar": "^1.1.16",
    "@radix-ui/react-navigation-menu": "^1.2.14",
    "@radix-ui/react-popover": "^1.1.15",
    "@radix-ui/react-progress": "^1.1.8",
    "@radix-ui/react-radio-group": "^1.3.8",
    "@radix-ui/react-scroll-area": "^1.2.10",
    "@radix-ui/react-select": "^2.2.6",
    "@radix-ui/react-separator": "^1.1.8",
    "@radix-ui/react-slider": "^1.3.6",
    "@radix-ui/react-slot": "^1.2.4",
    "@radix-ui/react-switch": "^1.2.6",
    "@radix-ui/react-tabs": "^1.1.13",
    "@radix-ui/react-toast": "^1.2.15",
    "@radix-ui/react-toggle": "^1.1.10",
    "@radix-ui/react-toggle-group": "^1.1.11",
    "@radix-ui/react-tooltip": "^1.2.8",
    "@tanstack/react-query": "^5.90.12",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "cmdk": "^1.1.1",
    "date-fns": "^3.6.0",
    "embla-carousel-react": "^8.6.0",
    "input-otp": "^1.4.2",
    "lucide-react": "^0.462.0",
    "next-themes": "^0.3.0",
    "react": "^18.3.1",
    "react-day-picker": "^8.10.1",
    "react-dom": "^18.3.1",
    "react-hook-form": "^7.69.0",
    "react-resizable-panels": "^2.1.9",
    "react-router-dom": "^6.30.2",
    "recharts": "^2.15.4",
    "socket.io-client": "^4.8.1",
    "sonner": "^1.7.4",
    "tailwind-merge": "^2.6.0",
    "tailwindcss-animate": "^1.0.7",
    "vaul": "^0.9.9",
    "zod": "^3.25.76"
  },
  "devDependencies": {
    "@eslint/js": "^9.39.2",
    "@tailwindcss/typography": "^0.5.19",
    "@types/node": "^22.19.3",
    "@types/react": "^18.3.27",
    "@types/react-dom": "^18.3.7",
    "@vitejs/plugin-react-swc": "^3.11.0",
    "autoprefixer": "^10.4.23",
    "eslint": "^9.39.2",
    "eslint-plugin-react-hooks": "^5.2.0",
    "eslint-plugin-react-refresh": "^0.4.26",
    "globals": "^15.15.0",
    "lovable-tagger": "^1.1.13",
    "postcss": "^8.5.6",
    "tailwindcss": "^3.4.19",
    "typescript": "^5.9.3",
    "typescript-eslint": "^8.50.0",
    "vite": "^5.4.21"
  }
}
````

## File: README.md
````markdown
# EV GamePad Project
````

## File: tailwind.config.ts
````typescript
import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./pages/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Orbitron', 'sans-serif'],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        success: {
          DEFAULT: "hsl(var(--success))",
          foreground: "hsl(var(--success-foreground))",
        },
        warning: {
          DEFAULT: "hsl(var(--warning))",
          foreground: "hsl(var(--warning-foreground))",
        },
        amber: "hsl(var(--amber))",
        "amber-glow": "hsl(var(--amber-glow))",
        orange: "hsl(var(--orange))",
        "terminal-green": "hsl(var(--terminal-green))",
        "danger-red": "hsl(var(--danger-red))",
        "safe-blue": "hsl(var(--safe-blue))",
        "panel-bg": "hsl(var(--panel-bg))",
        "panel-border": "hsl(var(--panel-border))",
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        glow: {
          "0%, 100%": { boxShadow: "0 0 5px hsl(var(--amber))" },
          "50%": { boxShadow: "0 0 20px hsl(var(--amber)), 0 0 30px hsl(var(--amber))" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        glow: "glow 2s ease-in-out infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
````

## File: backend/app/models/responses.py
````python
from enum import Enum
from typing import Dict, Any, Optional

class ErrorCode(Enum):
    """Standardized error codes"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MT5_NOT_CONNECTED = "MT5_NOT_CONNECTED"
    MT5_ERROR = "MT5_ERROR"
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
````

## File: backend/app/processors/command_processor.py
````python
import logging
import uuid
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from app.mt5.trading_operations import TradingOperations
from app.mt5.connection_manager import MT5ConnectionManager
from app.models.responses import ErrorCode, error_response, success_response
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

class CommandProcessor:
    """
    Central command processing layer
    Routes Socket.IO events to MT5 operations
    """

    def __init__(self, mt5_manager: MT5ConnectionManager):
        self.mt5_manager = mt5_manager
        self.trading_ops = TradingOperations(mt5_manager)
        self.pending_commands: Dict[str, Dict[str, Any]] = {}

    async def _execute_mt5_operation(self, command_id: str, operation_name: str, func, **kwargs) -> Dict[str, Any]:
        """
        Helper to execute MT5 operations with common error handling and logging.
        """
        try:
            # Execute with circuit breaker protection (blocking call, wrapped in async)
            # We pass the function and kwargs to execute_with_circuit_breaker
            def wrapped_func():
                return func(**kwargs)

            result = await asyncio.to_thread(
                self.mt5_manager.execute_with_circuit_breaker,
                wrapped_func
            )
            return result

        except ValueError as e:
            # Validation error (invalid symbol, etc.)
            logger.warning(f"[{command_id}] {operation_name} validation failed: {e}")
            raise
        except RuntimeError as e:
            # MT5 connection error or Circuit Breaker Open
            logger.error(f"[{command_id}] {operation_name} failed (MT5 error): {e}")
            raise
        except Exception as e:
             # Generic error
            logger.exception(f"[{command_id}] {operation_name} failed unexpectedly")
            raise

    async def process_buy_order(
        self,
        sid: str,
        symbol: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process buy market order
        """
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing BUY order: {symbol} {volume} lots (client: {sid})")

        self.pending_commands[command_id] = {
            'type': 'buy',
            'symbol': symbol,
            'volume': volume,
            'client_id': sid,
            'started_at': datetime.utcnow(),
        }

        try:
            result = await self._execute_mt5_operation(
                command_id, "BUY order",
                self.trading_ops.place_buy_market,
                symbol=symbol,
                volume=volume,
                sl=sl,
                tp=tp
            )

            if result.get('retcode') != mt5.TRADE_RETCODE_DONE:
                retcode = result.get('retcode')
                comment = result.get('comment', 'Unknown MT5 error')
                logger.error(
                    f"[{command_id}] BUY order failed - retcode: {retcode}, comment: {comment}, "
                    f"symbol: {symbol}, volume: {volume}"
                )
                return error_response(
                    ErrorCode.MT5_ERROR,
                    f"MT5 Error {retcode}: {comment}",
                    details={'retcode': retcode, 'symbol': symbol, 'volume': volume}
                )

            logger.info(
                f"[{command_id}] BUY order executed: "
                f"Ticket={result['ticket']}, Price={result['price']}"
            )

            return success_response({
                'command_id': command_id,
                'ticket': result['ticket'],
                'symbol': symbol,
                'volume': result['volume'],
                'price': result['price'],
                'sl': sl,
                'tp': tp,
                'timestamp': result['timestamp'],
            })

        except ValueError as e:
            return error_response(ErrorCode.VALIDATION_ERROR, str(e))
        except RuntimeError as e:
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))
        except Exception as e:
            return error_response(ErrorCode.INTERNAL_ERROR, f"Order execution failed: {str(e)}")
        finally:
             self.pending_commands.pop(command_id, None)

    async def process_sell_order(
        self,
        sid: str,
        symbol: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process sell market order"""
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing SELL order: {symbol} {volume} lots (client: {sid})")

        self.pending_commands[command_id] = {
            'type': 'sell',
            'symbol': symbol,
            'volume': volume,
            'client_id': sid,
            'started_at': datetime.utcnow(),
        }

        try:
            result = await self._execute_mt5_operation(
                 command_id, "SELL order",
                self.trading_ops.place_sell_market,
                symbol=symbol,
                volume=volume,
                sl=sl,
                tp=tp
            )

            if result.get('retcode') != mt5.TRADE_RETCODE_DONE:
                retcode = result.get('retcode')
                comment = result.get('comment', 'Unknown MT5 error')
                logger.error(
                    f"[{command_id}] SELL order failed - retcode: {retcode}, comment: {comment}, "
                    f"symbol: {symbol}, volume: {volume}"
                )
                return error_response(
                    ErrorCode.MT5_ERROR,
                    f"MT5 Error {retcode}: {comment}",
                    details={'retcode': retcode, 'symbol': symbol, 'volume': volume}
                )

            logger.info(
                f"[{command_id}] SELL order executed: "
                f"Ticket={result['ticket']}, Price={result['price']}"
            )

            return success_response({
                'command_id': command_id,
                'ticket': result['ticket'],
                'symbol': symbol,
                'volume': result['volume'],
                'price': result['price'],
                'sl': sl,
                'tp': tp,
                'timestamp': result['timestamp'],
            })

        except ValueError as e:
            return error_response(ErrorCode.VALIDATION_ERROR, str(e))
        except RuntimeError as e:
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))
        except Exception as e:
            return error_response(ErrorCode.INTERNAL_ERROR, f"Order execution failed: {str(e)}")
        finally:
            self.pending_commands.pop(command_id, None)

    async def process_modify_position(
        self,
        sid: str,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process modify position TP/SL"""
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing MODIFY: Ticket={ticket} (client: {sid})")

        self.pending_commands[command_id] = {
            'type': 'modify',
            'ticket': ticket,
            'client_id': sid,
            'started_at': datetime.utcnow(),
        }

        try:
            result = await self._execute_mt5_operation(
                command_id, "MODIFY",
                self.trading_ops.modify_position,
                ticket=ticket,
                new_sl=sl,
                new_tp=tp
            )

            if result.get('retcode') != mt5.TRADE_RETCODE_DONE:
                retcode = result.get('retcode')
                comment = result.get('comment', 'Unknown MT5 error')
                logger.error(
                    f"[{command_id}] MODIFY failed - retcode: {retcode}, comment: {comment}, "
                    f"ticket: {ticket}"
                )
                return error_response(
                    ErrorCode.MT5_ERROR,
                    f"MT5 Error {retcode}: {comment}",
                    details={'retcode': retcode, 'ticket': ticket}
                )

            logger.info(
                f"[{command_id}] Position modified: "
                f"Ticket={ticket}, SL={result['new_sl']}, TP={result['new_tp']}"
            )

            return success_response({
                'command_id': command_id,
                'ticket': ticket,
                'sl': result['new_sl'],
                'tp': result['new_tp'],
                'modified_at': result['modified_at'],
            })

        except ValueError as e:
            return error_response(ErrorCode.POSITION_NOT_FOUND, str(e))
        except RuntimeError as e:
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))
        except Exception as e:
            return error_response(ErrorCode.INTERNAL_ERROR, f"Modify failed: {str(e)}")
        finally:
             self.pending_commands.pop(command_id, None)

    async def process_close_position(
        self,
        sid: str,
        ticket: int,
        volume: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process close position"""
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing CLOSE: Ticket={ticket} (client: {sid})")

        self.pending_commands[command_id] = {
            'type': 'close',
            'ticket': ticket,
            'client_id': sid,
            'started_at': datetime.utcnow(),
        }

        try:
            result = await self._execute_mt5_operation(
                command_id, "CLOSE",
                self.trading_ops.close_position,
                ticket=ticket,
                volume=volume
            )

            if result.get('retcode') != mt5.TRADE_RETCODE_DONE:
                retcode = result.get('retcode')
                comment = result.get('comment', 'Unknown MT5 error')
                logger.error(
                    f"[{command_id}] CLOSE failed - retcode: {retcode}, comment: {comment}, "
                    f"ticket: {ticket}"
                )
                return error_response(
                    ErrorCode.MT5_ERROR,
                    f"MT5 Error {retcode}: {comment}",
                    details={'retcode': retcode, 'ticket': ticket}
                )

            logger.info(
                f"[{command_id}] Position closed: "
                f"Ticket={ticket}, Price={result['close_price']}, Profit={result['profit']}"
            )

            return success_response({
                'command_id': command_id,
                'ticket': ticket,
                'close_ticket': result['close_ticket'],
                'close_price': result['close_price'],
                'volume_closed': result['volume_closed'],
                'profit': result['profit'],
                'closed_at': result['closed_at'],
            })

        except ValueError as e:
            return error_response(ErrorCode.POSITION_NOT_FOUND, str(e))
        except RuntimeError as e:
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))
        except Exception as e:
            return error_response(ErrorCode.INTERNAL_ERROR, f"Close failed: {str(e)}")
        finally:
             self.pending_commands.pop(command_id, None)

    def get_pending_commands(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending commands (for debugging)"""
        return self.pending_commands.copy()
````

## File: src/components/CapitalCompanionPanel.tsx
````typescript
import { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Volume2, VolumeX, MessageCircle, Sparkles, Play, User } from "lucide-react";

interface Message {
  id: number;
  text: string;
  isAI: boolean;
  timestamp: string;
  isNew?: boolean;
}

const initialMessages: Message[] = [
  {
    id: 1,
    text: "Good morning, Trader! I've been analyzing the markets while you were away. BTC is showing strong bullish momentum on the H4 timeframe.",
    isAI: true,
    timestamp: "08:30",
  },
  {
    id: 2,
    text: "I found a solid support level at $96,500. The risk/reward ratio looks favorable at 1:2.8. Want me to break it down for you?",
    isAI: true,
    timestamp: "08:31",
  },
];

const aiResponses = [
  "I'm seeing increased whale activity on-chain. This often precedes significant moves. Stay alert!",
  "The Fear & Greed index just shifted to 'Greed'. Historically, this suggests we might see some volatility ahead.",
  "Your current position is looking good! The trend is still intact. I'd recommend holding for now.",
  "I've spotted a potential divergence forming on the RSI. Let me keep monitoring this for you.",
  "Great news! The support level I mentioned earlier is holding strong. Confidence in this trade remains high.",
  "Remember to take breaks, Trader. A clear mind makes better decisions. I'll watch the charts for you.",
];

const CapitalCompanionPanel = () => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isTalking, setIsTalking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const [aiMood, setAiMood] = useState<"happy" | "thinking" | "alert">("happy");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Simulate incoming AI messages periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const randomChance = Math.random();
      if (randomChance > 0.7) {
        setAiMood("thinking");
        setIsThinking(true);

        setTimeout(() => {
          const randomResponse = aiResponses[Math.floor(Math.random() * aiResponses.length)];
          const newMessage: Message = {
            id: Date.now(),
            text: randomResponse,
            isAI: true,
            timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
            isNew: true,
          };
          setMessages(prev => [...prev, newMessage]);
          setHasNewMessage(true);
          setIsThinking(false);
          setAiMood("happy");

          // Remove "new" indicator after a few seconds
          setTimeout(() => {
            setMessages(prev => prev.map(m => m.id === newMessage.id ? { ...m, isNew: false } : m));
            setHasNewMessage(false);
          }, 3000);
        }, 2000);
      }
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  const handleTalkToggle = () => {
    setIsTalking(!isTalking);
    if (!isTalking) {
      // Simulate user talking
      setTimeout(() => {
        setIsTalking(false);
        setAiMood("thinking");
        setIsThinking(true);

        // AI responds
        setTimeout(() => {
          const responses = [
            "I understand your concern. Let me analyze that for you...",
            "That's a great question! Based on my analysis...",
            "I'm on it, Trader! Give me a moment to crunch the numbers.",
          ];
          const newMessage: Message = {
            id: Date.now(),
            text: responses[Math.floor(Math.random() * responses.length)],
            isAI: true,
            timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
            isNew: true,
          };
          setMessages(prev => [...prev, newMessage]);
          setIsThinking(false);
          setAiMood("happy");
        }, 1500);
      }, 3000);
    }
  };

  const playLatestMessage = () => {
    setHasNewMessage(false);
    // Simulate playing audio
  };

  // Gamepad/Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // p = Play Message (Start)
      // m = Toggle Mute (Back)
      // v = Toggle Talk (L3)
      if (e.key === "p" && hasNewMessage) {
        playLatestMessage();
      } else if (e.key === "m") {
        setIsMuted(prev => !prev);
      } else if (e.key === "v") {
        handleTalkToggle();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [hasNewMessage, isTalking]); // Added isTalking to dependencies as handleTalkToggle uses it via closure/state

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-secondary" />
          <h2 className="panel-title">CAPITAL COMPANION</h2>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isThinking ? "bg-secondary animate-pulse" : "bg-terminal-green"}`} />
          <span className="text-xs text-terminal-green">AI FRIEND</span>
        </div>
      </div>

      <div className="p-4 flex gap-4">
        {/* AI Avatar Section */}
        <div className="flex flex-col items-center gap-3">
          {/* Avatar Container */}
          <div className={`relative w-24 h-24 rounded-full bg-gradient-to-br from-secondary/30 to-primary/30 border-2 
            ${isTalking ? "border-terminal-green animate-pulse" : isThinking ? "border-secondary" : "border-primary/50"}
            flex items-center justify-center overflow-hidden transition-all duration-300`}
          >
            {/* AI Face */}
            <div className="relative">
              {/* Eyes */}
              <div className="flex gap-3 mb-2">
                <div className={`w-3 h-3 rounded-full bg-primary ${isThinking ? "animate-bounce" : ""}`}>
                  <div className="w-1 h-1 bg-white/80 rounded-full ml-0.5 mt-0.5" />
                </div>
                <div className={`w-3 h-3 rounded-full bg-primary ${isThinking ? "animate-bounce delay-100" : ""}`}>
                  <div className="w-1 h-1 bg-white/80 rounded-full ml-0.5 mt-0.5" />
                </div>
              </div>
              {/* Mouth */}
              <div className={`mx-auto w-6 h-2 rounded-full transition-all duration-300 
                ${aiMood === "happy" ? "bg-terminal-green" : aiMood === "thinking" ? "bg-secondary w-4 h-4" : "bg-danger-red"}`}
              />
            </div>

            {/* Glow effect when talking */}
            {isTalking && (
              <div className="absolute inset-0 bg-terminal-green/20 animate-pulse rounded-full" />
            )}

            {/* Thinking indicator */}
            {isThinking && (
              <div className="absolute -bottom-1 left-1/2 -translate-x-1/2">
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-1.5 h-1.5 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-1.5 h-1.5 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            )}
          </div>

          {/* AI Name */}
          <div className="text-center">
            <span className="text-sm font-bold text-primary">ATLAS</span>
            <span className="block text-xs text-muted-foreground">Your Trading AI</span>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col gap-2 w-full">
            {/* Talk Button */}
            <button
              onClick={handleTalkToggle}
              className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-all duration-300
                ${isTalking
                  ? "bg-terminal-green/20 border-terminal-green text-terminal-green animate-pulse"
                  : "bg-panel-bg border-primary/30 text-primary hover:border-primary hover:bg-primary/10"
                }`}
            >
              {isTalking ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              <span className="text-sm font-semibold">{isTalking ? "STOP" : "TALK"}</span>
            </button>

            {/* Play New Message Button */}
            <button
              onClick={playLatestMessage}
              disabled={!hasNewMessage}
              className={`flex items-center justify-center gap-2 px-4 py-2 rounded-lg border transition-all duration-300
                ${hasNewMessage
                  ? "bg-secondary/20 border-secondary text-secondary animate-pulse"
                  : "bg-panel-bg/30 border-border/30 text-muted-foreground opacity-50 cursor-not-allowed"
                }`}
            >
              <Play className="w-4 h-4" />
              <span className="text-xs">{hasNewMessage ? "NEW MSG" : "NO MSG"}</span>
            </button>

            {/* Mute Toggle */}
            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`flex items-center justify-center gap-2 px-3 py-2 rounded-lg border transition-all
                ${isMuted
                  ? "bg-danger-red/20 border-danger-red/50 text-danger-red"
                  : "bg-panel-bg/30 border-border/30 text-muted-foreground hover:text-foreground"
                }`}
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              <span className="text-xs">{isMuted ? "MUTED" : "SOUND"}</span>
            </button>
          </div>
        </div>

        {/* Chat Messages Section */}
        <div className="flex-1 flex flex-col">
          <div className="flex items-center gap-2 mb-2">
            <MessageCircle className="w-4 h-4 text-primary" />
            <span className="text-xs text-muted-foreground">CONVERSATION</span>
          </div>

          <div className="flex-1 bg-background/30 border border-border/30 rounded-lg p-3 overflow-y-auto max-h-[200px] space-y-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-2 ${message.isNew ? "animate-pulse" : ""}`}
              >
                {/* Avatar */}
                <div className={`w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs
                  ${message.isAI
                    ? "bg-gradient-to-br from-secondary/50 to-primary/50 border border-primary/30"
                    : "bg-terminal-green/20 border border-terminal-green/30"
                  }`}
                >
                  {message.isAI ? "A" : <User className="w-3 h-3" />}
                </div>

                {/* Message */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className={`text-xs font-semibold ${message.isAI ? "text-primary" : "text-terminal-green"}`}>
                      {message.isAI ? "Atlas" : "You"}
                    </span>
                    <span className="text-xs text-muted-foreground">{message.timestamp}</span>
                    {message.isNew && (
                      <span className="text-xs bg-secondary/30 text-secondary px-1.5 py-0.5 rounded">NEW</span>
                    )}
                  </div>
                  <p className={`text-sm leading-relaxed ${message.isAI ? "text-foreground/90" : "text-foreground/70"}`}>
                    {message.text}
                  </p>
                </div>
              </div>
            ))}

            {/* Thinking indicator in chat */}
            {isThinking && (
              <div className="flex gap-2">
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-secondary/50 to-primary/50 border border-primary/30 flex items-center justify-center text-xs">
                  A
                </div>
                <div className="flex items-center gap-1 text-muted-foreground">
                  <span className="text-xs">Atlas is thinking</span>
                  <div className="flex gap-0.5">
                    <div className="w-1 h-1 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-1 h-1 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-1 h-1 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Status */}
          <div className="mt-2 flex items-center justify-between text-xs">
            <span className="text-muted-foreground">
              {isTalking ? "🎤 Listening..." : isThinking ? "🤔 Analyzing..." : "💚 Ready to help"}
            </span>
            <span className="text-primary">{messages.length} messages</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CapitalCompanionPanel;
````

## File: src/components/GamepadPositions.tsx
````typescript
import { useState, useEffect, useCallback } from "react";
import { TrendingUp, TrendingDown, DollarSign, X, Edit3 } from "lucide-react";
import { useSocket } from "@/context/SocketContext";
import { toast } from "sonner";

// Hardcoded for now, but in future should come from context/socket
const positions = [
  {
    id: "POS-001",
    pair: "BTC/USD",
    type: "LONG",
    entry: "96,850.00",
    current: "97,842.50",
    size: "0.25",
    pnl: "+992.50",
    pnlPercent: "+10.25%",
  },
  {
    id: "POS-002",
    pair: "ETH/USD",
    type: "LONG",
    entry: "3,420.00",
    current: "3,456.78",
    size: "5.0",
    pnl: "+183.90",
    pnlPercent: "+1.08%",
  },
  {
    id: "POS-003",
    pair: "SOL/USD",
    type: "SHORT",
    entry: "192.50",
    current: "187.45",
    size: "50",
    pnl: "+252.50",
    pnlPercent: "+2.63%",
  },
];

export const GamepadPositions = () => {
  const [selectedPosition, setSelectedPosition] = useState(0);
  const [actionMode, setActionMode] = useState<"select" | "action">("select");
  const [selectedAction, setSelectedAction] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

  const { socket, isConnected } = useSocket();

  const handleResponse = useCallback((data: any) => {
    setIsProcessing(false);
    console.log("Position action response:", data);
    if (data.success) {
      toast.success("Action Executed Successfully", {
        description: data.message || "Operation complete",
      });
      // Here we should reload positions or remove the closed one from state if we were using dynamic state
      setActionMode("select"); // Reset UI
    } else {
      toast.error("Action Failed", {
        description: data.error || "Unknown error",
      });
    }
  }, []);

  useEffect(() => {
    if (!socket) return;
    socket.on("close_result", handleResponse);
    socket.on("modify_result", handleResponse);
    socket.on("error", handleResponse); // Reuse handler for error

    return () => {
      socket.off("close_result", handleResponse);
      socket.off("modify_result", handleResponse);
      socket.off("error", handleResponse);
    };
  }, [socket, handleResponse]);

  const executeAction = () => {
    if (!socket || !isConnected) {
      toast.error("Not Connected");
      return;
    }

    const pos = positions[selectedPosition];

    if (selectedAction === 0) {
      // Modify
      console.log("Modifying", pos.id);
      setIsProcessing(true);
      // Emitting mock modify with hardcoded SL/TP for demo
      socket.emit("modify", {
        ticket: pos.id,
        sl: 0.0, // Should be actual value
        tp: 0.0
      });
    } else if (selectedAction === 1) {
      // Close
      console.log("Closing", pos.id);
      setIsProcessing(true);
      socket.emit("close", {
        ticket: pos.id,
        volume: parseFloat(pos.size) // Assuming full close
      });
    }
  };

  const closeAll = () => {
    if (!socket || !isConnected) {
      toast.error("Not Connected");
      return;
    }
    console.log("Closing ALL");
    setIsProcessing(true);
    // Loop through positions and emit close for each
    // Note: In real app, might want a single 'close_all' event or batched.
    // For now, iterate.
    positions.forEach(pos => {
      socket.emit("close", {
        ticket: pos.id,
        volume: parseFloat(pos.size)
      });
    });
    // This simple iteration doesn't track individual success well but works for "fire and forget".
    toast.info("Close All initiated");
  };

  const totalPnL = positions.reduce(
    (acc, pos) => acc + parseFloat(pos.pnl.replace(/[+,]/g, "")),
    0
  );

  // Keyboard/gamepad navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (actionMode === "select") {
        switch (e.key) {
          case "ArrowUp":
            if (selectedPosition > 0) setSelectedPosition(selectedPosition - 1);
            break;
          case "ArrowDown":
            if (selectedPosition < positions.length - 1) setSelectedPosition(selectedPosition + 1);
            break;
          case "Enter":
          case " ":
            setActionMode("action");
            break;
        }
      } else {
        switch (e.key) {
          case "ArrowLeft":
            setSelectedAction(0);
            break;
          case "ArrowRight":
            setSelectedAction(1);
            break;
          case "Escape":
          case "b": // B Button acts as back in submenu
            setActionMode("select");
            break;
        }
      }

      // GLOBAL actions for this component (always active when mounted)
      if (e.key === "y") {
        // Y Button -> Close All
        closeAll();
      }

      if (actionMode === "select") {
        if (e.key === "x") {
          // X -> Modify currently selected
          setActionMode("action");
          setSelectedAction(0); // Select Modify
        }
      } else if (actionMode === "action") {
        if (e.key === "Enter") {
          // Execute selected action
          executeAction();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [actionMode, selectedPosition, selectedAction, isConnected, socket]);

  return (
    <div className="space-y-4">
      {/* Total P&L Header */}
      <div className="panel">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <DollarSign className="w-8 h-8 text-terminal-green" />
            <div>
              <div className="text-sm text-muted-foreground font-mono">TOTAL UNREALIZED P&L</div>
              <div className="text-4xl font-mono font-bold text-terminal-green">
                +${totalPnL.toFixed(2)}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground font-mono">ACTIVE POSITIONS</div>
            <div className="text-4xl font-display text-primary">{positions.length}</div>
          </div>
        </div>
      </div>

      {/* Position Cards - Big gamepad-friendly */}
      <div className="space-y-3">
        {positions.map((pos, index) => {
          const isLong = pos.type === "LONG";
          const isProfitable = pos.pnl.startsWith("+");
          const isSelected = selectedPosition === index;

          return (
            <button
              key={pos.id}
              onClick={() => {
                setSelectedPosition(index);
                setActionMode("action");
              }}
              className={`w-full text-left gamepad-position-card ${isSelected ? "gamepad-position-card-active" : ""
                } ${isProfitable ? "border-terminal-green/30" : "border-danger-red/30"}`}
            >
              <div className="flex items-center justify-between">
                {/* Left: Position Info */}
                <div className="flex items-center gap-4">
                  <div
                    className={`flex items-center justify-center w-16 h-16 rounded-xl ${isLong ? "bg-terminal-green/20" : "bg-danger-red/20"
                      }`}
                  >
                    {isLong ? (
                      <TrendingUp className={`w-8 h-8 text-terminal-green`} />
                    ) : (
                      <TrendingDown className={`w-8 h-8 text-danger-red`} />
                    )}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-display text-primary">{pos.pair}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-sm font-mono ${isLong
                          ? "bg-terminal-green/20 text-terminal-green"
                          : "bg-danger-red/20 text-danger-red"
                          }`}
                      >
                        {pos.type}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground font-mono mt-1">
                      SIZE: {pos.size} | ENTRY: ${pos.entry}
                    </div>
                  </div>
                </div>

                {/* Right: P&L */}
                <div className="text-right">
                  <div
                    className={`text-3xl font-mono font-bold ${isProfitable ? "text-terminal-green" : "text-danger-red"
                      }`}
                  >
                    ${pos.pnl}
                  </div>
                  <div
                    className={`text-lg font-mono ${isProfitable ? "text-terminal-green/70" : "text-danger-red/70"
                      }`}
                  >
                    {pos.pnlPercent}
                  </div>
                </div>

                {/* Selection indicator */}
                {isSelected && (
                  <div className="ml-4">
                    <div className="w-4 h-4 rounded-full bg-primary animate-pulse" />
                  </div>
                )}
              </div>

              {/* Action buttons when selected */}
              {isSelected && actionMode === "action" && (
                <div className="flex gap-4 mt-4 pt-4 border-t border-primary/20">
                  <button
                    onClick={() => { setSelectedAction(0); executeAction(); }}
                    className={`flex-1 py-4 rounded-lg border-2 font-display text-lg transition-all flex items-center justify-center gap-3 ${selectedAction === 0
                      ? "bg-primary/20 border-primary text-primary"
                      : "bg-panel-bg/50 border-muted/30 text-muted-foreground"
                      }`}
                  >
                    <div className="gamepad-button-hint">X</div>
                    <Edit3 className="w-5 h-5" />
                    <span>MODIFY</span>
                  </button>
                  <button
                    onClick={() => { setSelectedAction(1); executeAction(); }}
                    className={`flex-1 py-4 rounded-lg border-2 font-display text-lg transition-all flex items-center justify-center gap-3 ${selectedAction === 1
                      ? "bg-danger-red/20 border-danger-red text-danger-red"
                      : "bg-panel-bg/50 border-muted/30 text-muted-foreground"
                      }`}
                  >
                    <div className="gamepad-button-hint bg-danger-red/20 text-danger-red">B</div>
                    <X className="w-5 h-5" />
                    <span>CLOSE</span>
                  </button>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Close All Button */}
      <button
        onClick={closeAll}
        className="w-full py-5 rounded-xl border-2 border-danger-red/50 bg-danger-red/10 text-danger-red font-display text-xl tracking-wider hover:bg-danger-red/20 transition-all flex items-center justify-center gap-3"
      >
        <div className="gamepad-button-hint bg-danger-red/20 text-danger-red">Y</div>
        <span>CLOSE ALL POSITIONS</span>
      </button>

      {!isConnected && (
        <div className="text-center text-xs text-danger-red animate-pulse mt-4">
          DISCONNECTED FROM TRADING SERVER
        </div>
      )}
    </div>
  );
};
````

## File: src/components/GamepadQuickTrade.tsx
````typescript
import { useState, useEffect, useCallback } from "react";
import { TrendingUp, TrendingDown, Zap, Shield, Target } from "lucide-react";
import { useSocket } from "@/context/SocketContext";
import { toast } from "sonner";

const pairs = [
  { symbol: "BTC/USD", price: "97,842.50", change: "+2.34%" },
  { symbol: "ETH/USD", price: "3,456.78", change: "+1.87%" },
  { symbol: "SOL/USD", price: "187.45", change: "+5.67%" },
  { symbol: "XAU/USD", price: "2,634.50", change: "-0.45%" },
];

const sizes = ["0.01", "0.05", "0.10", "0.25", "0.50", "1.00"];

export const GamepadQuickTrade = () => {
  const [selectedPair, setSelectedPair] = useState(0);
  const [selectedSize, setSelectedSize] = useState(2);
  const [side, setSide] = useState<"LONG" | "SHORT">("LONG");
  const [focusArea, setFocusArea] = useState<"pair" | "size" | "action">("pair");
  const [isProcessing, setIsProcessing] = useState(false);

  const { socket, isConnected } = useSocket();

  const handleTradeResponse = useCallback((data: any) => {
    setIsProcessing(false);
    console.log("Order response:", data);
    if (data.success) {
      toast.success(`Order Executed: ${data.order?.ticket || "Success"}`, {
        description: `${data.order?.symbol} @ ${data.order?.price}`,
        duration: 3000,
      });
    } else {
      toast.error("Order Failed", {
        description: data.error || "Unknown error",
        duration: 5000,
      });
    }
  }, []);

  const handleError = useCallback((err: any) => {
    setIsProcessing(false);
    const msg = err?.message || err?.error || "Unknown error";
    toast.error("Trade Error", { description: msg });
  }, []);

  useEffect(() => {
    if (!socket) return;

    socket.on("order_result", handleTradeResponse);
    socket.on("error", handleError);

    return () => {
      socket.off("order_result", handleTradeResponse);
      socket.off("error", handleError);
    };
  }, [socket, handleTradeResponse, handleError]);

  const executeTrade = () => {
    if (!socket || !isConnected) {
      toast.error("Not Connected", { description: "Socket.IO server unreachable" });
      return;
    }

    if (isProcessing) return;

    const currentPair = pairs[selectedPair];
    const volume = parseFloat(sizes[selectedSize]);
    const symbol = currentPair.symbol.replace("/", "");

    setIsProcessing(true);
    const event = side === "LONG" ? "buy" : "sell";

    console.log(`Emitting ${event}: ${symbol} ${volume}`);

    socket.emit(event, {
      symbol: symbol,
      volume: volume,
      sl: 0.0,
      tp: 0.0,
    });
  };

  // Keyboard/gamepad navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case "ArrowUp":
          if (focusArea === "size") setFocusArea("pair");
          else if (focusArea === "action") setFocusArea("size");
          break;
        case "ArrowDown":
          if (focusArea === "pair") setFocusArea("size");
          else if (focusArea === "size") setFocusArea("action");
          break;
        case "ArrowLeft":
          if (focusArea === "pair" && selectedPair > 0) setSelectedPair(selectedPair - 1);
          if (focusArea === "size" && selectedSize > 0) setSelectedSize(selectedSize - 1);
          if (focusArea === "action") setSide("LONG");
          break;
        case "ArrowRight":
          if (focusArea === "pair" && selectedPair < pairs.length - 1) setSelectedPair(selectedPair + 1);
          if (focusArea === "size" && selectedSize < sizes.length - 1) setSelectedSize(selectedSize + 1);
          if (focusArea === "action") setSide("SHORT");
          break;
        case "Enter": // A Button
          if (focusArea === "action") {
            executeTrade();
          }
          break;
        case "x": // X Button -> Set Long
          setSide("LONG");
          setFocusArea("action");
          break;
        case "b": // B Button -> Set Short (if not used for back)
          setSide("SHORT");
          setFocusArea("action");
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [focusArea, selectedPair, selectedSize, side, socket, isConnected, isProcessing]);

  const currentPair = pairs[selectedPair];

  return (
    <div className="space-y-6">
      {/* Asset Selection - Big tiles */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            <span className="panel-title">SELECT ASSET</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="gamepad-button-hint text-xs">◄►</div>
            <span className="text-xs text-muted-foreground">D-PAD</span>
          </div>
        </div>

        <div className={`grid grid-cols-2 lg:grid-cols-4 gap-3 ${focusArea === "pair" ? "ring-2 ring-primary/50 rounded-lg p-2" : "p-2"}`}>
          {pairs.map((pair, index) => (
            <button
              key={pair.symbol}
              onClick={() => {
                setSelectedPair(index);
                setFocusArea("pair");
              }}
              className={`gamepad-tile-sm ${selectedPair === index ? "gamepad-tile-active" : ""
                }`}
            >
              <div className="text-lg font-display text-primary">{pair.symbol}</div>
              <div className="text-2xl font-mono font-bold mt-1">${pair.price}</div>
              <div className={`text-sm font-mono mt-1 ${pair.change.startsWith("+") ? "text-terminal-green" : "text-danger-red"
                }`}>
                {pair.change}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Size Selection - Slider-like big buttons */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-secondary" />
            <span className="panel-title">POSITION SIZE</span>
          </div>
          <div className="text-xl font-mono text-primary font-bold">
            {sizes[selectedSize]} {currentPair.symbol.split("/")[0]}
          </div>
        </div>

        <div className={`flex gap-2 ${focusArea === "size" ? "ring-2 ring-primary/50 rounded-lg p-2" : "p-2"}`}>
          {sizes.map((size, index) => (
            <button
              key={size}
              onClick={() => {
                setSelectedSize(index);
                setFocusArea("size");
              }}
              className={`flex-1 py-4 text-lg font-mono rounded-lg border-2 transition-all ${selectedSize === index
                ? "bg-primary/30 border-primary text-primary scale-105"
                : "bg-panel-bg/50 border-primary/20 text-muted-foreground hover:border-primary/50"
                }`}
            >
              {size}
            </button>
          ))}
        </div>
      </div>

      {/* Action Buttons - Massive gamepad-friendly */}
      <div className={`grid grid-cols-2 gap-6 ${focusArea === "action" ? "ring-2 ring-primary/50 rounded-lg p-3" : "p-1"}`}>
        <button
          onClick={() => {
            setSide("LONG");
            setFocusArea("action");
          }}
          className={`relative py-8 rounded-xl border-4 transition-all font-display text-2xl tracking-wider ${side === "LONG"
            ? "bg-terminal-green/20 border-terminal-green text-terminal-green scale-[1.02] shadow-[0_0_30px_rgba(34,197,94,0.3)]"
            : "bg-panel-bg/50 border-muted/30 text-muted-foreground hover:border-terminal-green/50"
            }`}
        >
          <div className="absolute top-2 left-3">
            <div className="gamepad-button-hint bg-terminal-green/20 text-terminal-green">X</div>
          </div>
          <TrendingUp className="w-10 h-10 mx-auto mb-2" />
          <div>LONG / BUY</div>
          <div className="text-sm font-mono mt-1 opacity-70">+{currentPair.price}</div>
        </button>

        <button
          onClick={() => {
            setSide("SHORT");
            setFocusArea("action");
          }}
          className={`relative py-8 rounded-xl border-4 transition-all font-display text-2xl tracking-wider ${side === "SHORT"
            ? "bg-danger-red/20 border-danger-red text-danger-red scale-[1.02] shadow-[0_0_30px_rgba(239,68,68,0.3)]"
            : "bg-panel-bg/50 border-muted/30 text-muted-foreground hover:border-danger-red/50"
            }`}
        >
          <div className="absolute top-2 left-3">
            <div className="gamepad-button-hint bg-danger-red/20 text-danger-red">B</div>
          </div>
          <TrendingDown className="w-10 h-10 mx-auto mb-2" />
          <div>SHORT / SELL</div>
          <div className="text-sm font-mono mt-1 opacity-70">-{currentPair.price}</div>
        </button>
      </div>

      {/* Execute Button - The big one */}
      <button
        onClick={executeTrade}
        disabled={isProcessing}
        className={`w-full py-6 rounded-xl border-4 font-display text-3xl tracking-widest transition-all ${isProcessing ? "opacity-50 cursor-not-allowed" : ""} ${side === "LONG"
          ? "bg-terminal-green text-background border-terminal-green hover:scale-[1.01] shadow-[0_0_40px_rgba(34,197,94,0.4)]"
          : "bg-danger-red text-background border-danger-red hover:scale-[1.01] shadow-[0_0_40px_rgba(239,68,68,0.4)]"
          }`}
      >
        <div className="flex items-center justify-center gap-4">
          <div className="gamepad-button-hint bg-background/20 text-background border-background/30">A</div>
          <span>{isProcessing ? "EXECUTING..." : `EXECUTE ${side}`}</span>
        </div>
      </button>

      {/* Risk Info */}
      <div className="flex justify-center gap-8 text-sm font-mono">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-danger-red" />
          <span className="text-muted-foreground">RISK:</span>
          <span className="text-primary">$975.00</span>
        </div>
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-terminal-green" />
          <span className="text-muted-foreground">LEVERAGE:</span>
          <span className="text-secondary">10x</span>
        </div>
      </div>

      {!isConnected && (
        <div className="text-center text-xs text-danger-red animate-pulse">
          DISCONNECTED FROM TRADING SERVER
        </div>
      )}
    </div>
  );
};
````

## File: src/components/MonitorNav.tsx
````typescript
import { NavLink } from "react-router-dom";
import { Monitor, BarChart3, Diamond, BriefcaseBusiness } from "lucide-react";

const monitors = [
  { path: "/", label: "1", title: "PORTFOLIO", icon: BriefcaseBusiness },
  { path: "/plan", label: "2", title: "PLAN", icon: BarChart3 },
  { path: "/action", label: "3", title: "ACTION", icon: Diamond },
];

export const MonitorNav = () => {
  return (
    <div className="flex items-center gap-1 bg-panel-bg/50 p-1 rounded border border-primary/20">
      {/* <Monitor className="w-4 h-4 text-muted-foreground mx-2" /> */}
      {monitors.map((mon) => (
        <NavLink
          key={mon.path}
          to={mon.path}
          className={({ isActive }) =>
            `flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded transition-all ${isActive
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-primary/20 hover:text-primary"
            }`
          }
        >
          <mon.icon className="w-3 h-3" />
          <span className="hidden sm:inline">{mon.label}:</span>
          <span>{mon.title}</span>
        </NavLink>
      ))}
    </div>
  );
};
````

## File: src/index.css
````css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Orbitron:wght@400;500;600;700;800;900&display=swap');

@layer base {
  :root {
    /* Industrial Sci-Fi Color Palette */
    --background: 0 0% 8%;
    --foreground: 38 100% 50%;

    --card: 0 0% 10%;
    --card-foreground: 38 100% 50%;

    --popover: 0 0% 10%;
    --popover-foreground: 38 100% 50%;

    --primary: 38 100% 50%;
    --primary-foreground: 0 0% 5%;

    --secondary: 25 100% 45%;
    --secondary-foreground: 0 0% 98%;

    --muted: 0 0% 15%;
    --muted-foreground: 38 60% 40%;

    --accent: 25 100% 50%;
    --accent-foreground: 0 0% 5%;

    --destructive: 0 84% 50%;
    --destructive-foreground: 0 0% 98%;

    --success: 142 70% 45%;
    --success-foreground: 0 0% 98%;

    --warning: 38 100% 50%;
    --warning-foreground: 0 0% 5%;

    --border: 38 50% 25%;
    --input: 0 0% 15%;
    --ring: 38 100% 50%;

    --radius: 0.25rem;

    /* Custom Industrial Colors */
    --amber: 38 100% 50%;
    --amber-glow: 38 100% 60%;
    --orange: 25 100% 50%;
    --terminal-green: 142 70% 45%;
    --danger-red: 0 84% 50%;
    --safe-blue: 200 80% 50%;
    --panel-bg: 0 0% 6%;
    --panel-border: 38 50% 20%;

    /* Gradients */
    --gradient-health: linear-gradient(90deg, hsl(200, 80%, 50%), hsl(142, 70%, 45%));
    --gradient-danger: linear-gradient(90deg, hsl(38, 100%, 50%), hsl(0, 84%, 50%));
    --gradient-panel: linear-gradient(180deg, hsl(0, 0%, 12%) 0%, hsl(0, 0%, 6%) 100%);

    /* Shadows */
    --glow-amber: 0 0 20px hsl(38 100% 50% / 0.3);
    --glow-green: 0 0 15px hsl(142 70% 45% / 0.4);
    --glow-red: 0 0 15px hsl(0 84% 50% / 0.4);

    --sidebar-background: 0 0% 8%;
    --sidebar-foreground: 38 100% 50%;
    --sidebar-primary: 38 100% 50%;
    --sidebar-primary-foreground: 0 0% 5%;
    --sidebar-accent: 0 0% 15%;
    --sidebar-accent-foreground: 38 100% 50%;
    --sidebar-border: 38 50% 20%;
    --sidebar-ring: 38 100% 50%;
  }
}

@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground font-mono;
    font-family: 'JetBrains Mono', monospace;
  }

  h1, h2, h3, h4, h5, h6 {
    font-family: 'Orbitron', sans-serif;
  }
}

@layer components {
  .panel {
    @apply relative bg-panel border border-panel-border rounded-sm overflow-hidden;
    background: var(--gradient-panel);
  }

  .panel-header {
    @apply px-4 py-2 border-b border-panel-border bg-muted/50 flex items-center gap-3;
  }

  .panel-title {
    @apply text-sm font-bold tracking-widest uppercase text-primary;
    font-family: 'Orbitron', sans-serif;
    text-shadow: 0 0 10px hsl(var(--amber) / 0.5);
  }

  .status-indicator {
    @apply w-2 h-2 rounded-full animate-pulse;
  }

  .status-online {
    @apply bg-terminal-green;
    box-shadow: var(--glow-green);
  }

  .status-warning {
    @apply bg-amber;
    box-shadow: var(--glow-amber);
  }

  .status-danger {
    @apply bg-danger-red;
    box-shadow: var(--glow-red);
  }

  .terminal-text {
    @apply font-mono text-sm leading-relaxed;
    color: hsl(var(--terminal-green));
    text-shadow: 0 0 5px hsl(var(--terminal-green) / 0.5);
  }

  .data-value {
    @apply font-bold tabular-nums;
    font-family: 'Orbitron', sans-serif;
  }

  /* Scanlines Effect */
  .scanlines {
    position: relative;
  }

  .scanlines::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0, 0, 0, 0.15) 2px,
      rgba(0, 0, 0, 0.15) 4px
    );
    pointer-events: none;
    z-index: 9999;
  }

  .scanlines::after {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(
      ellipse at center,
      transparent 0%,
      rgba(0, 0, 0, 0.3) 100%
    );
    pointer-events: none;
    z-index: 9998;
  }

  /* CRT Flicker Animation */
  @keyframes flicker {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.98; }
    25%, 75% { opacity: 0.99; }
  }

  .crt-flicker {
    animation: flicker 0.1s infinite;
  }

  /* Glow Text */
  .glow-text {
    text-shadow: 0 0 10px currentColor, 0 0 20px currentColor;
  }

  /* Typing animation for terminal */
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }

  .cursor-blink::after {
    content: '█';
    animation: blink 1s infinite;
  }
}

@layer utilities {
  .bg-panel {
    background-color: hsl(var(--panel-bg));
  }

  .border-panel-border {
    border-color: hsl(var(--panel-border));
  }

  .text-amber {
    color: hsl(var(--amber));
  }

  .text-terminal-green {
    color: hsl(var(--terminal-green));
  }

  .text-danger-red {
    color: hsl(var(--danger-red));
  }

  .bg-terminal-green {
    background-color: hsl(var(--terminal-green));
  }

  .bg-amber {
    background-color: hsl(var(--amber));
  }

  .bg-danger-red {
    background-color: hsl(var(--danger-red));
  }

  .bg-safe-blue {
    background-color: hsl(var(--safe-blue));
  }

  /* Gamepad-friendly UI Components */
  .gamepad-tile {
    @apply relative p-5 rounded-lg border-2 border-primary/30 bg-panel-bg/80 
           transition-all duration-200 ease-out
           hover:border-primary hover:bg-primary/10
           focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background;
  }

  .gamepad-tile-active {
    @apply border-primary bg-primary/20 scale-[1.02];
    box-shadow: 0 0 30px hsl(var(--primary) / 0.3), inset 0 0 20px hsl(var(--primary) / 0.1);
  }

  .gamepad-tile-sm {
    @apply p-4 rounded-lg border-2 border-primary/20 bg-panel-bg/60 
           transition-all duration-150 text-center
           hover:border-primary/60 hover:bg-primary/10
           focus:outline-none focus:ring-2 focus:ring-primary;
  }

  .gamepad-tile-sm.gamepad-tile-active {
    @apply border-primary bg-primary/20 scale-105;
    box-shadow: 0 0 20px hsl(var(--primary) / 0.4);
  }

  .gamepad-button-hint {
    @apply inline-flex items-center justify-center w-7 h-7 rounded-md 
           border-2 border-primary/50 bg-primary/10 
           text-xs font-bold text-primary font-mono;
  }

  .gamepad-position-card {
    @apply p-4 rounded-xl border-2 bg-panel-bg/50 transition-all duration-200
           hover:bg-primary/5 focus:outline-none;
  }

  .gamepad-position-card-active {
    @apply border-primary bg-primary/10 scale-[1.01];
    box-shadow: 0 0 25px hsl(var(--primary) / 0.2);
  }

  /* Focus ring for gamepad navigation */
  .gamepad-focus-ring {
    @apply ring-2 ring-primary ring-offset-2 ring-offset-background;
  }
}
````

## File: backend/app/events/trading_events.py
````python
import logging
from typing import Dict, Any
from datetime import datetime

from app.validation import (
    validate_login_command,
    validate_order_command,
    validate_modify_command,
    validate_close_command,
)
from app.models.responses import (
    success_response,
    error_response,
    ErrorCode,
)

# Global instances (will be injected from main.py)
from app.sio import sio

mt5_manager = None
session_manager = None
reconnection_manager = None
command_processor = None

logger = logging.getLogger(__name__)

# ============================================================================
# CONNECTION LIFECYCLE
# ============================================================================

@sio.event
async def connect(sid: str, environ: Dict[str, Any]):
    """Handle client connection with reconnection detection"""
    remote_addr = environ.get('REMOTE_ADDR', 'unknown')
    logger.info(f"Client {sid} connecting from {remote_addr}")

    # Attempt session recovery
    recovered_session = None
    if reconnection_manager:
        recovered_session = reconnection_manager.recover_session(sid)

    if recovered_session:
        # Reconnection detected
        logger.info(f"Reconnection detected for {sid}")

        # Restore session
        session_manager.create_session(sid, recovered_session)

        # Notify client of recovery
        await sio.emit('session_recovered', {
            'message': 'Session recovered',
            'session_id': sid,
            'pending_orders': reconnection_manager.get_pending_orders(sid) if reconnection_manager else [],
            'reconnected_at': datetime.utcnow().isoformat(),
        }, to=sid)
    else:
        # New connection
        logger.info(f"New client {sid} connected from {remote_addr}")

        # Initialize fresh session
        session_manager.create_session(sid, {
            'connected_at': datetime.utcnow(),
            'remote_addr': remote_addr,
            'mt5_logged_in': False,
            'pending_orders': {},
        })

        # Send welcome
        await sio.emit('connected', {
            'message': 'Connected to MT5 Trading Server',
            'session_id': sid,
            'server_time': datetime.utcnow().isoformat(),
        }, to=sid)

@sio.event
async def disconnect(sid: str):
    """Handle client disconnection with session preservation"""
    logger.info(f"Client {sid} disconnected")

    # Get session for preservation
    session = session_manager.get_session(sid)
    if session:
        # Store for recovery
        if reconnection_manager:
            reconnection_manager.store_disconnected_session(sid, session)

        # Log pending orders
        pending = session.get('pending_orders', {})
        if pending:
            logger.warning(
                f"Client {sid} disconnected with {len(pending)} pending orders - "
                f"session stored for recovery"
            )

    # Remove from active sessions
    session_manager.remove_session(sid)

# ============================================================================
# TRADING COMMANDS
# ============================================================================

@sio.event
async def login(sid: str, data: Dict[str, Any]):
    """Handle MT5 login command"""
    logger.info(f"Login request from {sid}")

    try:
        # Validate
        is_valid, error_msg = validate_login_command(data)
        if not is_valid:
            await sio.emit('error', error_response(
                ErrorCode.VALIDATION_ERROR,
                error_msg
            ), to=sid)
            return

        # Login to MT5 (using connection manager)
        account_info = mt5_manager.login_account(
            data['account'],
            data['password'],
            data['server']
        )
        
        if not account_info:
             raise Exception("Login failed on MT5")

        # Update session
        session = session_manager.get_session(sid)
        if session:
            session['mt5_logged_in'] = True
            session['account'] = data['account']

        # Send success
        await sio.emit('login_result', success_response({
            'account_info': {
                'login': account_info['login'],
                'name': account_info['name'],
                'server': account_info['server'],
                'currency': account_info['currency'],
                'balance': account_info['balance'],
                'equity': account_info['equity'],
                'leverage': account_info['leverage'],
            }
        }), to=sid)

        logger.info(f"Client {sid} logged in as {data['account']}")

    except Exception as e:
        logger.exception(f"Login failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Login failed: {str(e)}"
        ), to=sid)

@sio.event
async def buy(sid: str, data: Dict[str, Any]):
    """Handle buy market order"""
    logger.info(f"Buy order from {sid}: {data.get('symbol')} {data.get('volume')}")

    try:
        is_valid, error_msg = validate_order_command(data)
        if not is_valid:
            await sio.emit('error', error_response(ErrorCode.VALIDATION_ERROR, error_msg), to=sid)
            return

        # Use command processor if available
        if command_processor:
            response = await command_processor.process_buy_order(
                sid, 
                data['symbol'], 
                data['volume'], 
                data.get('sl'), 
                data.get('tp')
            )
            if response.get('success'):
                await sio.emit('order_result', response, to=sid)
            else:
                await sio.emit('error', response, to=sid)
        else:
             await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, "Command processor not initialized"), to=sid)

    except Exception as e:
        logger.exception(f"Buy failed for {sid}")
        await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, str(e)), to=sid)

@sio.event
async def sell(sid: str, data: Dict[str, Any]):
    """Handle sell market order"""
    logger.info(f"Sell order from {sid}: {data.get('symbol')} {data.get('volume')}")

    try:
        is_valid, error_msg = validate_order_command(data)
        if not is_valid:
            await sio.emit('error', error_response(ErrorCode.VALIDATION_ERROR, error_msg), to=sid)
            return

        if command_processor:
            response = await command_processor.process_sell_order(
                sid, 
                data['symbol'], 
                data['volume'], 
                data.get('sl'), 
                data.get('tp')
            )
            if response.get('success'):
                await sio.emit('order_result', response, to=sid)
            else:
                await sio.emit('error', response, to=sid)
        else:
             await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, "Command processor not initialized"), to=sid)

    except Exception as e:
        logger.exception(f"Sell failed for {sid}")
        await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, str(e)), to=sid)

@sio.event
async def modify(sid: str, data: Dict[str, Any]):
    """Handle modify position"""
    logger.info(f"Modify request from {sid}: ticket={data.get('ticket')}")

    try:
        is_valid, error_msg = validate_modify_command(data)
        if not is_valid:
            await sio.emit('error', error_response(ErrorCode.VALIDATION_ERROR, error_msg), to=sid)
            return

        if command_processor:
            response = await command_processor.process_modify_position(
                sid,
                data['ticket'],
                data.get('sl'),
                data.get('tp')
            )
            if response.get('success'):
                await sio.emit('modify_result', response, to=sid)
            else:
                await sio.emit('error', response, to=sid)
        else:
             await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, "Command processor not initialized"), to=sid)

    except Exception as e:
        logger.exception(f"Modify failed for {sid}")
        await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, str(e)), to=sid)

@sio.event
async def close(sid: str, data: Dict[str, Any]):
    """Handle close position"""
    logger.info(f"Close request from {sid}: ticket={data.get('ticket')}")

    try:
        is_valid, error_msg = validate_close_command(data)
        if not is_valid:
            await sio.emit('error', error_response(ErrorCode.VALIDATION_ERROR, error_msg), to=sid)
            return

        if command_processor:
            response = await command_processor.process_close_position(
                sid,
                data['ticket'],
                data.get('volume')
            )
            if response.get('success'):
                await sio.emit('close_result', response, to=sid)
            else:
                await sio.emit('error', response, to=sid)
        else:
             await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, "Command processor not initialized"), to=sid)

    except Exception as e:
        logger.exception(f"Close failed for {sid}")
        await sio.emit('error', error_response(ErrorCode.INTERNAL_ERROR, str(e)), to=sid)
````

## File: backend/app/mt5/connection_manager.py
````python
import MetaTrader5 as mt5
import threading
import time
import logging
from typing import Dict, Any, Optional, Callable
from ..config import config
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class MT5ConnectionManager:
    """
    Manages the connection to the MetaTrader 5 terminal.
    Handles initialization, login, health monitoring, and auto-reconnection.
    """
    def __init__(self, check_interval: float = 5.0, timeout: float = 30.0):
        self.check_interval = check_interval
        self.timeout = timeout
        self._connected = False
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._health_thread: Optional[threading.Thread] = None
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=30.0
        )
        
    def connect(self) -> bool:
        """Initialize MT5 connection and login."""
        with self._lock:
            if self._connected:
                return True

            logger.info("Initializing MT5 connection...")
            
            # Initialize MT5
            if not mt5.initialize(timeout=int(self.timeout * 1000)):
                logger.error(f"MT5 initialization failed, error: {mt5.last_error()}")
                return False

            # Login if credentials provided
            if config.ACCOUNT_NUMBER and config.ACCOUNT_PASSWORD and config.BROKER_SERVER:
                logger.info(f"Logging in to account {config.ACCOUNT_NUMBER}...")
                authorized = mt5.login(
                    config.ACCOUNT_NUMBER, 
                    password=config.ACCOUNT_PASSWORD, 
                    server=config.BROKER_SERVER
                )
                if not authorized:
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
            
            self._connected = True
            logger.info("MT5 connected successfully")
            
            # Log account info
            info = self.get_account_info()
            if info:
                logger.info(f"Account: {info.get('login')} ({info.get('server')})")
                logger.info(f"Balance: {info.get('balance')} {info.get('currency')}")

            # Start health check if not running
            self._start_health_check()
            return True

    def login_account(self, account: int, password: str, server: str) -> Optional[Dict[str, Any]]:
        """Login to specific MT5 account."""
        with self._lock:
            # Ensure initialized
            if not self._connected:
                if not mt5.initialize(timeout=int(self.timeout * 1000)):
                     logger.error("MT5 initialization failed during login request")
                     return None

            logger.info(f"Logging in to account {account}...")
            authorized = mt5.login(
                account, 
                password=password, 
                server=server
            )
            
            if authorized:
                self._connected = True
                logger.info(f"Successfully logged in to {account}")
                self.circuit_breaker.reset() # Reset circuit breaker on successful login
                return self.get_account_info()
            else:
                logger.error(f"Login failed for {account}: {mt5.last_error()}")
                return None

    def execute_with_circuit_breaker(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute MT5 operation with circuit breaker protection

        Args:
            func: MT5 function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            RuntimeError: If circuit is open or operation fails
        """
        if not self.is_connected():
            raise RuntimeError("MT5 not connected")

        try:
            return self.circuit_breaker.execute(func, *args, **kwargs)
        except RuntimeError as e:
            if "Circuit breaker is open" in str(e):
                logger.error("Circuit breaker OPEN - refusing MT5 operations")
            raise

    def disconnect(self):
        """Disconnect from MT5 and stop health check."""
        with self._lock:
            self._stop_event.set()
            if self._health_thread:
                self._health_thread.join(timeout=2.0)
            
            if self._connected:
                mt5.shutdown()
                self._connected = False
                logger.info("MT5 disconnected")

    def is_connected(self) -> bool:
        """Check if connected to MT5 and terminal is connected to server."""
        if not self._connected:
            return False
        
        # Check actual terminal state
        term_info = mt5.terminal_info()
        if term_info is None:
            return False
            
        return term_info.connected

    def is_autotrading_enabled(self) -> bool:
        """Check if AutoTrading (Algo Trading) is enabled in the terminal."""
        if not self.is_connected():
            return False
            
        term_info = mt5.terminal_info()
        if term_info is None:
            return False
            
        return term_info.trade_allowed

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get current account information."""
        if not self.is_connected():
            return None
        
        info = mt5.account_info()
        if info is None:
            return None
        return info._asdict()

    def _start_health_check(self):
        """Start the background health check thread."""
        if self._health_thread is not None and self._health_thread.is_alive():
            return

        self._stop_event.clear()
        self._health_thread = threading.Thread(
            target=self._health_check_loop, 
            name="MT5HealthCheck",
            daemon=True
        )
        self._health_thread.start()
        logger.info("Health check thread started")

    def _health_check_loop(self):
        """Background loop to monitor connection health."""
        while not self._stop_event.is_set():
            try:
                if self._connected:
                    if not self.is_connected():
                        logger.warning("Connection lost, attempting reconnect...")
                        if self._attempt_reconnect():
                             self.circuit_breaker.reset()
                
            except Exception as e:
                logger.error(f"Error in health check: {e}")
            
            time.sleep(self.check_interval)

    def _attempt_reconnect(self, max_attempts: int = 3) -> bool:
        """Attempt to reconnect to MT5."""
        with self._lock:
            self._connected = False
            # Ensure clean state
            mt5.shutdown()
            
            backoff = 1.0
            
            for attempt in range(max_attempts):
                logger.info(f"Reconnection attempt {attempt + 1}/{max_attempts}")
                
                if mt5.initialize(timeout=int(self.timeout * 1000)):
                    if config.ACCOUNT_NUMBER:
                        if mt5.login(config.ACCOUNT_NUMBER, config.ACCOUNT_PASSWORD, config.BROKER_SERVER):
                            self._connected = True
                            logger.info("Reconnection successful")
                            return True
                    else:
                        # If no login needed (just terminal init)
                        self._connected = True
                        logger.info("Reconnection successful (no login)")
                        return True
                
                time.sleep(backoff)
                backoff *= 2.0  # Exponential backoff
                
            logger.error("Reconnection failed after all attempts")
            return False
````

## File: backend/app/main.py
````python
from fastapi import FastAPI
from socketio import AsyncServer, ASGIApp
from contextlib import asynccontextmanager
import logging

from app.config import config
from app.logging_config import setup_logging
from app.mt5.connection_manager import MT5ConnectionManager
from app.session_manager import SessionManager
from app.reconnection_manager import ReconnectionManager
from app.processors.command_processor import CommandProcessor
from app.tasks.cleanup_task import CleanupTask
from app.database.redis_client import RedisClient
from app.processors.advisor_processor import AdvisorProcessor

# Initialize logging
logger = setup_logging(config.DEBUG)

# Global instances
mt5_manager = None
session_manager = None
reconnection_manager = None
command_processor = None
cleanup_task = None
redis_client = None
advisor_processor = None

from app.sio import sio

from app.events import trading_events
from app.events import advisor_events

# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    Initialize and cleanup resources
    """
    global mt5_manager, session_manager, reconnection_manager, command_processor, cleanup_task, redis_client, advisor_processor

    logger.info("Starting MT5 Socket.IO Trading Server...")

    # Initialize MT5 connection
    mt5_manager = MT5ConnectionManager(
        check_interval=config.HEALTH_CHECK_INTERVAL, # Kept original config variable
        timeout=config.CONNECTION_TIMEOUT # Kept original config variable
    )

    if not mt5_manager.connect():
        logger.error("Failed to connect to MT5 terminal")
        # In a real scenario, we might want to exit or retry,
        # but for now we'll continue to allow the server to start (for health check access)
        # raise RuntimeError("MT5 connection failed")

    logger.info("MT5 connection attempt finished")

    # Initialize session manager
    session_manager = SessionManager()
    
    # Initialize reconnection manager
    reconnection_manager = ReconnectionManager(session_ttl=300)  # 5 minutes
    logger.info("Reconnection manager initialized")

    # Initialize command processor
    command_processor = CommandProcessor(mt5_manager)

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

    # Start cleanup task
    cleanup_task = CleanupTask(reconnection_manager, interval=60)
    cleanup_task.start()

    # Inject dependencies into events module
    trading_events.mt5_manager = mt5_manager
    trading_events.session_manager = session_manager
    trading_events.reconnection_manager = reconnection_manager
    trading_events.command_processor = command_processor

    # Inject into advisor events
    advisor_events.advisor_processor = advisor_processor
    advisor_events.redis_client = redis_client

    # Store in app state (only mt5_manager is directly used by health check)
    app.state.mt5_manager = mt5_manager
    app.state.session_manager = session_manager # Kept for consistency, though events module now has it

    yield

    # Shutdown
    logger.info("Shutting down server...")

    if cleanup_task:
        await cleanup_task.stop()

    if redis_client:
        await redis_client.disconnect()

    if mt5_manager:
        mt5_manager.disconnect()
    logger.info("Server shutdown complete")

app = FastAPI(
    title="MT5 Trading Server",
    version="1.0.0",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if mt5_manager and mt5_manager.is_connected() else "unhealthy",
        "mt5_connected": mt5_manager.is_connected() if mt5_manager else False,
        "redis_connected": await redis_client.is_connected() if redis_client else False,
        "connected_clients": len(session_manager.sessions) if session_manager else 0,
    }

# Wrap with Socket.IO
asgi_app = ASGIApp(sio, app)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        asgi_app,
        host=config.SOCKETIO_HOST,
        port=config.SOCKETIO_PORT,
        log_level="debug" if config.DEBUG else "info"
    )
````

## File: backend/requirements.txt
````
MetaTrader5==5.0.45; sys_platform == 'win32'

python-dotenv==1.0.1
python-json-logger>=2.0.70
pytest==7.4.0
pytest-asyncio==0.21.0
fastapi==0.104.0
python-socketio==5.10.0
uvicorn[standard]==0.24.0
numpy<2

# Technical Analysis
pandas-ta==0.3.14b
pandas==2.0.3

# Redis Cache
redis==5.2.1
````

## File: src/App.tsx
````typescript
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Plan from "./pages/Plan";
import Action from "./pages/Action";
import Portfolio from "./pages/Portfolio";
import NotFound from "./pages/NotFound";

import { GlobalGamepadHandler } from "@/components/GlobalGamepadHandler";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <GlobalGamepadHandler />
        <Routes>
          <Route path="/plan" element={<Plan />} />
          <Route path="/action" element={<Action />} />
          <Route path="/" element={<Portfolio />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
````

## File: .gitignore
````
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*
pnpm-lock.yaml
bun.lockb
node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
.claude
__pycache__
.claude
````
