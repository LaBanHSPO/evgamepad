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
