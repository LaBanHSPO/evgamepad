"""
Unit tests for VolumeValidator - MT5 + TwelveData volume validation.
Tests volume divergence detection and fake pump identification.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Import from app
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.advisor.volume_validator import VolumeValidator, VolumeValidationResult


class TestVolumeValidationResult:
    """Test VolumeValidationResult data class."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = VolumeValidationResult(
            mt5_volume=1000.0,
            market_volume=1200.0,
            divergence_pct=0.15,
            is_divergent=False,
            is_fake_pump=False,
            confidence=0.85,
            message="Volume confirmed"
        )

        data = result.to_dict()
        assert data["mt5_volume"] == 1000.0
        assert data["market_volume"] == 1200.0
        assert data["divergence_pct"] == 0.15
        assert data["is_divergent"] is False
        assert data["is_fake_pump"] is False
        assert data["confidence"] == 0.85
        assert data["message"] == "Volume confirmed"


class TestVolumeValidator:
    """Test VolumeValidator initialization and configuration."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        validator = VolumeValidator(api_key="test_key")
        assert validator.api_key == "test_key"
        assert validator.divergence_threshold == 0.30  # Default from config

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with patch('app.advisor.volume_validator.config.TWELVEDATA_API_KEY', ''):
            validator = VolumeValidator()
            assert validator.td_client is None

    @pytest.mark.asyncio
    async def test_fetch_market_volume_without_client(self):
        """Test that fetch returns None when client not initialized."""
        with patch('app.advisor.volume_validator.config.TWELVEDATA_API_KEY', ''):
            validator = VolumeValidator()
            result = await validator.fetch_market_volume("XAUUSD", "H1", 100)
            assert result is None

    @pytest.mark.asyncio
    async def test_symbol_conversion(self):
        """Test MT5 symbol format conversion to TwelveData format."""
        validator = VolumeValidator(api_key="test_key")

        # Mock TDClient.time_series to verify symbol conversion
        mock_ts = Mock()
        mock_ts.as_pandas.return_value = pd.DataFrame({
            'volume': [1000, 1100, 1200]
        }, index=pd.date_range('2025-01-01', periods=3, freq='H'))

        with patch.object(validator.td_client, 'time_series', return_value=mock_ts):
            result = await validator.fetch_market_volume("XAUUSD", "H1", 3)

            # Verify time_series was called with converted symbol
            validator.td_client.time_series.assert_called_once()
            call_kwargs = validator.td_client.time_series.call_args[1]
            assert call_kwargs['symbol'] == "XAU/USD"
            assert call_kwargs['interval'] == "1h"
            assert call_kwargs['outputsize'] == 3

    @pytest.mark.asyncio
    async def test_timeframe_conversion(self):
        """Test MT5 timeframe conversion to TwelveData interval."""
        validator = VolumeValidator(api_key="test_key")

        timeframe_map = {
            "M1": "1min",
            "M5": "5min",
            "H1": "1h",
            "H4": "4h",
            "D1": "1day",
            "W1": "1week",
        }

        for mt5_tf, expected_interval in timeframe_map.items():
            mock_ts = Mock()
            mock_ts.as_pandas.return_value = pd.DataFrame({
                'volume': [1000]
            }, index=pd.date_range('2025-01-01', periods=1))

            with patch.object(validator.td_client, 'time_series', return_value=mock_ts):
                await validator.fetch_market_volume("EURUSD", mt5_tf, 1)

                call_kwargs = validator.td_client.time_series.call_args[1]
                assert call_kwargs['interval'] == expected_interval


class TestVolumeValidation:
    """Test volume validation logic."""

    @pytest.mark.asyncio
    async def test_validate_volume_no_divergence(self):
        """Test validation when volumes are aligned (no divergence)."""
        validator = VolumeValidator(api_key="test_key")

        # MT5 data with volume
        mt5_df = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=10, freq='H'),
            'open': [1800] * 10,
            'high': [1810] * 10,
            'low': [1790] * 10,
            'close': [1805] * 10,
            'volume': [1000] * 10  # Avg = 1000
        })

        # Mock TwelveData market volume (similar to MT5)
        market_df = pd.DataFrame({
            'datetime': pd.date_range('2025-01-01', periods=10, freq='H'),
            'volume': [1050] * 10  # Avg = 1050 (5% difference)
        })

        with patch.object(validator, 'fetch_market_volume', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = market_df

            result = await validator.validate_volume(mt5_df, "XAUUSD", "H1")

            assert result.mt5_volume == 1000.0
            assert result.market_volume == 1050.0
            assert result.divergence_pct < 0.30  # Below threshold
            assert result.is_divergent is False
            assert result.is_fake_pump is False
            assert result.confidence > 0.7

    @pytest.mark.asyncio
    async def test_validate_volume_with_divergence(self):
        """Test validation when volumes diverge significantly."""
        validator = VolumeValidator(api_key="test_key")

        # MT5 data with higher volume
        mt5_df = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=10, freq='H'),
            'volume': [1500] * 10  # Avg = 1500
        })

        # Market volume is much lower
        market_df = pd.DataFrame({
            'datetime': pd.date_range('2025-01-01', periods=10, freq='H'),
            'volume': [1000] * 10  # Avg = 1000 (50% divergence)
        })

        with patch.object(validator, 'fetch_market_volume', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = market_df

            result = await validator.validate_volume(mt5_df, "XAUUSD", "H1")

            assert result.divergence_pct > 0.30  # Above threshold
            assert result.is_divergent is True
            assert result.confidence < 0.7

    @pytest.mark.asyncio
    async def test_validate_volume_fake_pump(self):
        """Test detection of fake volume pump (broker >> market)."""
        validator = VolumeValidator(api_key="test_key")

        # MT5 broker volume is 3x market volume
        mt5_df = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=10, freq='H'),
            'volume': [3000] * 10  # Avg = 3000
        })

        market_df = pd.DataFrame({
            'datetime': pd.date_range('2025-01-01', periods=10, freq='H'),
            'volume': [1000] * 10  # Avg = 1000 (3x difference)
        })

        with patch.object(validator, 'fetch_market_volume', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = market_df

            result = await validator.validate_volume(mt5_df, "XAUUSD", "H1")

            assert result.is_fake_pump is True
            assert result.is_divergent is True
            assert "Fake volume pump" in result.message

    @pytest.mark.asyncio
    async def test_validate_volume_market_unavailable(self):
        """Test graceful degradation when market data unavailable."""
        validator = VolumeValidator(api_key="test_key")

        mt5_df = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=10, freq='H'),
            'volume': [1000] * 10
        })

        # Market data fetch fails
        with patch.object(validator, 'fetch_market_volume', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            result = await validator.validate_volume(mt5_df, "XAUUSD", "H1")

            assert result.mt5_volume == 1000.0
            assert result.market_volume is None
            assert result.divergence_pct is None
            assert result.is_divergent is False
            assert result.confidence == 0.5
            assert "unavailable" in result.message.lower()


class TestBreakoutValidation:
    """Test breakout volume validation."""

    @pytest.mark.asyncio
    async def test_genuine_breakout(self):
        """Test detection of genuine breakout (confirmed by market)."""
        validator = VolumeValidator(api_key="test_key")

        # Both broker and market show volume increase
        market_df = pd.DataFrame({
            'datetime': pd.date_range('2025-01-01', periods=20, freq='H'),
            'volume': [1000] * 19 + [2000]  # 2x on last candle
        })

        with patch.object(validator, 'fetch_market_volume', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = market_df

            result = await validator.validate_breakout_volume(
                current_volume=2000,
                avg_volume=1000,
                symbol="XAUUSD",
                timeframe="H1"
            )

            assert result["is_genuine_breakout"] is True
            assert result["volume_ratio"] == 2.0
            assert result["market_confirmed"] is True
            assert result["confidence"] > 0.6

    @pytest.mark.asyncio
    async def test_fake_breakout(self):
        """Test detection of fake breakout (broker only, not market)."""
        validator = VolumeValidator(api_key="test_key")

        # Market volume doesn't increase
        market_df = pd.DataFrame({
            'datetime': pd.date_range('2025-01-01', periods=20, freq='H'),
            'volume': [1000] * 20  # No increase
        })

        with patch.object(validator, 'fetch_market_volume', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = market_df

            result = await validator.validate_breakout_volume(
                current_volume=2000,  # Broker shows 2x increase
                avg_volume=1000,
                symbol="XAUUSD",
                timeframe="H1"
            )

            assert result["is_genuine_breakout"] is False
            assert result["volume_ratio"] == 2.0  # Broker shows breakout
            assert result["market_confirmed"] is False  # But market doesn't
            assert result["confidence"] == 0.3  # Low confidence
            assert "Fake breakout" in result["message"]

    @pytest.mark.asyncio
    async def test_breakout_market_unavailable(self):
        """Test breakout validation without market data."""
        validator = VolumeValidator(api_key="test_key")

        with patch.object(validator, 'fetch_market_volume', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            result = await validator.validate_breakout_volume(
                current_volume=2000,
                avg_volume=1000,
                symbol="XAUUSD",
                timeframe="H1"
            )

            assert result["is_genuine_breakout"] is True  # Falls back to standard rule
            assert result["market_confirmed"] is False
            assert result["confidence"] == 0.5
            assert "unconfirmed" in result["message"].lower()


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_empty_mt5_dataframe(self):
        """Test handling of empty MT5 DataFrame."""
        validator = VolumeValidator(api_key="test_key")

        mt5_df = pd.DataFrame()
        result = await validator.validate_volume(mt5_df, "XAUUSD", "H1")

        assert result.mt5_volume == 0.0
        assert result.market_volume is None
        assert "unavailable" in result.message.lower()

    @pytest.mark.asyncio
    async def test_missing_volume_column(self):
        """Test handling of missing volume column in MT5 data."""
        validator = VolumeValidator(api_key="test_key")

        mt5_df = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=10, freq='H'),
            'close': [1800] * 10
            # Missing 'volume' column
        })

        result = await validator.validate_volume(mt5_df, "XAUUSD", "H1")

        assert result.mt5_volume == 0.0
        assert "unavailable" in result.message.lower()

    @pytest.mark.asyncio
    async def test_api_exception_handling(self):
        """Test graceful handling of API exceptions."""
        validator = VolumeValidator(api_key="test_key")

        mt5_df = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=10, freq='H'),
            'volume': [1000] * 10
        })

        # Simulate API error
        with patch.object(validator, 'fetch_market_volume', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("API rate limit exceeded")

            result = await validator.validate_volume(mt5_df, "XAUUSD", "H1")

            # Should not crash, should return unvalidated result
            assert result.mt5_volume == 1000.0
            assert result.market_volume is None
