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
