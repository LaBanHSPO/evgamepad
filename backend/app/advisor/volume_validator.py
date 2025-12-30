"""
Volume validation using hybrid MT5 + TwelveData approach.
Detects volume divergence and confirms breakouts with real market volume.
"""
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import pandas as pd
from twelvedata import TDClient

from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class VolumeValidationResult:
    """Result of volume validation analysis."""
    mt5_volume: float
    market_volume: Optional[float]
    divergence_pct: Optional[float]
    is_divergent: bool
    is_fake_pump: bool
    confidence: float
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class VolumeValidator:
    """
    Validates volume data by comparing MT5 broker volume with TwelveData market volume.

    Purpose:
    - MT5 broker volume ≠ total market volume
    - Detect volume divergence (broker vs market)
    - Confirm breakouts with real market volume
    - Identify fake volume pumps
    """

    def _convert_symbol_format(self, symbol: str) -> str:
        """
        Convert MT5 symbol to TwelveData format.

        Examples:
            XAUUSD -> XAU/USD (forex pairs)
            EURUSD -> EUR/USD
            BTCUSDT -> BTC/USDT (crypto)
            US30 -> US30 (indices - keep as-is)

        Args:
            symbol: MT5 symbol format

        Returns:
            TwelveData-compatible symbol format
        """
        # Already in correct format
        if "/" in symbol:
            return symbol

        # Forex pairs: 6 uppercase chars -> XXX/YYY
        if len(symbol) == 6 and symbol.isupper() and symbol.isalpha():
            return f"{symbol[:3]}/{symbol[3:]}"

        # Crypto pairs ending with common quote currencies
        for quote in ["USDT", "BUSD", "USD", "EUR", "BTC", "ETH"]:
            if symbol.endswith(quote) and len(symbol) > len(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"

        # Default: return as-is (indices, commodities, etc.)
        logger.debug(f"Symbol {symbol} format unchanged for TwelveData")
        return symbol

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: TwelveData API key (defaults to config)
        """
        self.api_key = api_key or config.TWELVEDATA_API_KEY
        self.divergence_threshold = config.VOLUME_DIVERGENCE_THRESHOLD

        # Validate threshold (must be between 0 and 1)
        if not (0.0 <= self.divergence_threshold <= 1.0):
            logger.warning(
                f"Invalid VOLUME_DIVERGENCE_THRESHOLD={self.divergence_threshold}, "
                f"using default 0.30"
            )
            self.divergence_threshold = 0.30

        self.td_client = None

        if self.api_key:
            try:
                self.td_client = TDClient(apikey=self.api_key)
                logger.info("TwelveData client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize TwelveData client: {e}")
        else:
            logger.warning("TwelveData API key not configured - volume validation disabled")

    async def fetch_market_volume(
        self,
        symbol: str,
        timeframe: str,
        count: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Fetch market-wide volume data from TwelveData.

        Args:
            symbol: Trading symbol (e.g., "XAUUSD" -> "XAU/USD")
            timeframe: Timeframe string (e.g., "H1", "D1")
            count: Number of candles to fetch

        Returns:
            DataFrame with columns: datetime, volume
            None if fetch fails or API key not configured
        """
        if not self.td_client:
            logger.debug("TwelveData client not available - skipping market volume fetch")
            return None

        try:
            # Convert MT5 symbol format to TwelveData format
            td_symbol = self._convert_symbol_format(symbol)

            # Convert timeframe to TwelveData interval
            # H1 -> 1h, H4 -> 4h, D1 -> 1day
            interval_map = {
                "M1": "1min",
                "M5": "5min",
                "M15": "15min",
                "M30": "30min",
                "H1": "1h",
                "H4": "4h",
                "D1": "1day",
                "W1": "1week",
                "MN1": "1month"
            }
            interval = interval_map.get(timeframe.upper())
            if not interval:
                logger.warning(f"Unsupported timeframe for TwelveData: {timeframe}")
                return None

            # Fetch time series data in thread (blocking call)
            def _fetch():
                ts = self.td_client.time_series(
                    symbol=td_symbol,
                    interval=interval,
                    outputsize=count,
                    timezone="UTC"
                )
                return ts.as_pandas()

            df = await asyncio.to_thread(_fetch)

            if df is None or df.empty:
                logger.warning(f"No market volume data returned for {td_symbol} {interval}")
                return None

            # Ensure datetime index and volume column exist
            if 'volume' not in df.columns:
                logger.warning(f"Volume column missing from TwelveData response for {td_symbol}")
                return None

            # Convert index to datetime if needed
            df.index = pd.to_datetime(df.index)

            # Return only datetime and volume
            result = pd.DataFrame({
                'datetime': df.index,
                'volume': df['volume'].astype(float)
            })

            logger.debug(f"Fetched {len(result)} market volume candles for {td_symbol} {interval}")
            return result

        except Exception as e:
            logger.exception(f"Failed to fetch market volume for {symbol} {timeframe}: {e}")
            return None

    async def validate_volume(
        self,
        mt5_df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> VolumeValidationResult:
        """
        Validate MT5 broker volume against TwelveData market volume.

        Args:
            mt5_df: DataFrame with MT5 OHLCV data (must have 'volume' column)
            symbol: Trading symbol
            timeframe: Timeframe string

        Returns:
            VolumeValidationResult with divergence analysis
        """
        # Calculate average MT5 broker volume
        if 'volume' not in mt5_df.columns or mt5_df.empty:
            logger.warning("MT5 DataFrame missing volume data")
            return VolumeValidationResult(
                mt5_volume=0.0,
                market_volume=None,
                divergence_pct=None,
                is_divergent=False,
                is_fake_pump=False,
                confidence=0.0,
                message="MT5 volume data unavailable"
            )

        mt5_avg_volume = float(mt5_df['volume'].mean())

        # Fetch market volume from TwelveData with exception handling
        try:
            market_df = await self.fetch_market_volume(symbol, timeframe, count=len(mt5_df))
        except Exception as e:
            logger.warning(f"Failed to fetch market volume for {symbol}: {e}")
            market_df = None

        # If TwelveData unavailable, return unvalidated result
        if market_df is None or market_df.empty:
            return VolumeValidationResult(
                mt5_volume=mt5_avg_volume,
                market_volume=None,
                divergence_pct=None,
                is_divergent=False,
                is_fake_pump=False,
                confidence=0.5,
                message="Market volume validation unavailable - using MT5 broker volume only"
            )

        # Calculate average market volume
        market_avg_volume = float(market_df['volume'].mean())

        # Calculate divergence percentage
        if market_avg_volume > 0:
            divergence_pct = abs(mt5_avg_volume - market_avg_volume) / market_avg_volume
        else:
            divergence_pct = 0.0

        # Detect volume divergence
        is_divergent = divergence_pct > self.divergence_threshold

        # Detect fake volume pump (broker volume >> market volume)
        is_fake_pump = False
        if market_avg_volume > 0:
            volume_ratio = mt5_avg_volume / market_avg_volume
            # If MT5 broker volume is 2x+ higher than market volume, likely fake pump
            is_fake_pump = volume_ratio > 2.0 and is_divergent

        # Calculate confidence score
        # High confidence if volumes align, low if divergent
        confidence = max(0.0, min(1.0, 1.0 - divergence_pct))

        # Generate message
        if is_fake_pump:
            message = f"⚠️ Fake volume pump detected! Broker volume {divergence_pct*100:.1f}% higher than market"
        elif is_divergent:
            message = f"⚠️ Volume divergence detected: {divergence_pct*100:.1f}% difference"
        else:
            message = f"✓ Volume confirmed: {divergence_pct*100:.1f}% divergence (within threshold)"

        return VolumeValidationResult(
            mt5_volume=mt5_avg_volume,
            market_volume=market_avg_volume,
            divergence_pct=divergence_pct,
            is_divergent=is_divergent,
            is_fake_pump=is_fake_pump,
            confidence=confidence,
            message=message
        )

    async def validate_breakout_volume(
        self,
        current_volume: float,
        avg_volume: float,
        symbol: str,
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Validate if a breakout volume is genuine using market volume confirmation.

        Args:
            current_volume: Current candle volume
            avg_volume: Average volume (e.g., 20-period average)
            symbol: Trading symbol
            timeframe: Timeframe string

        Returns:
            Dict with breakout validation results
        """
        # Calculate volume increase ratio
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0.0

        # Fetch recent market volume for comparison
        market_df = await self.fetch_market_volume(symbol, timeframe, count=20)

        if market_df is None or market_df.empty:
            return {
                "is_genuine_breakout": volume_ratio > 1.5,  # Standard 1.5x rule
                "volume_ratio": volume_ratio,
                "market_confirmed": False,
                "confidence": 0.5,
                "message": "Breakout volume unconfirmed - market data unavailable"
            }

        # Get latest market volume
        latest_market_volume = float(market_df['volume'].iloc[-1])
        market_avg_volume = float(market_df['volume'].mean())
        market_volume_ratio = latest_market_volume / market_avg_volume if market_avg_volume > 0 else 0.0

        # Confirm breakout if both broker AND market show volume increase
        broker_breakout = volume_ratio > 1.5
        market_breakout = market_volume_ratio > 1.5
        is_genuine_breakout = broker_breakout and market_breakout

        # Calculate confidence
        if is_genuine_breakout:
            confidence = min(0.95, 0.6 + min(volume_ratio, market_volume_ratio) * 0.1)
        elif broker_breakout and not market_breakout:
            confidence = 0.3  # Low confidence - possible fake breakout
        else:
            confidence = 0.5

        # Generate message
        if is_genuine_breakout:
            message = f"✓ Genuine breakout confirmed: Broker {volume_ratio:.1f}x, Market {market_volume_ratio:.1f}x"
        elif broker_breakout and not market_breakout:
            message = f"⚠️ Fake breakout suspected: Broker {volume_ratio:.1f}x, Market {market_volume_ratio:.1f}x"
        else:
            message = f"No significant breakout: Broker {volume_ratio:.1f}x, Market {market_volume_ratio:.1f}x"

        return {
            "is_genuine_breakout": is_genuine_breakout,
            "volume_ratio": volume_ratio,
            "market_volume_ratio": market_volume_ratio,
            "market_confirmed": market_breakout,
            "confidence": confidence,
            "message": message
        }
