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
