"""
Personalized recommendation engine.
Combines technical analysis with user profile for tailored advice.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    HOLD = "hold"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

class RecommendationEngine:
    """
    Generates personalized trading recommendations by combining:
    - Technical indicators
    - Pattern recognition
    - Support/Resistance levels
    - User risk profile
    - AI-generated insights
    """

    def __init__(self, ai_summarizer=None):
        """
        Args:
            ai_summarizer: AISummarizer instance for natural language generation
        """
        self.ai_summarizer = ai_summarizer

    async def generate_recommendation(
        self,
        symbol: str,
        technical_data: Dict[str, Any],
        pattern_data: Optional[Dict[str, Any]] = None,
        sr_data: Optional[Dict[str, Any]] = None,
        risk_data: Optional[Dict[str, Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive trading recommendation.

        Args:
            symbol: Trading symbol
            technical_data: Output from TechnicalAnalyzer
            pattern_data: Output from PatternDetector
            sr_data: Output from SupportResistanceCalculator
            risk_data: Output from RiskAnalyzer
            user_profile: User preferences and risk settings
            language: Output language

        Returns:
            Comprehensive recommendation with signal, confidence, targets
        """
        result = {
            "symbol": symbol,
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Default user profile
        if user_profile is None:
            user_profile = {
                "risk_tolerance": "moderate",
                "preferred_timeframe": "H1",
            }

        # 1. Aggregate signals from technical analysis
        tech_signal = self._aggregate_technical_signals(technical_data)
        result["technical_signal"] = tech_signal

        # 2. Aggregate pattern signals
        pattern_signal = self._aggregate_pattern_signals(pattern_data) if pattern_data else None
        if pattern_signal:
            result["pattern_signal"] = pattern_signal

        # 3. Calculate overall signal
        overall = self._calculate_overall_signal(
            tech_signal, pattern_signal, user_profile
        )
        result["overall_signal"] = overall

        # 4. Determine entry/exit targets
        targets = self._calculate_targets(
            technical_data, sr_data, overall["signal"], user_profile
        )
        result["targets"] = targets

        # 5. Generate AI summary if available
        if self.ai_summarizer:
            combined_data = {
                "symbol": symbol,
                "timeframe": user_profile.get("preferred_timeframe", "H1"),
                "last_price": technical_data.get("last_close"),
                "indicators": technical_data.get("indicators", {}),
                "signals": technical_data.get("signals", {}),
                "candlestick_patterns": pattern_data or {},
                "support_resistance": sr_data or {},
                "risk_profile": user_profile.get("risk_tolerance", "moderate"),
            }

            ai_result = await self.ai_summarizer.generate_summary(
                combined_data, language=language
            )
            result["ai_summary"] = ai_result

        # 6. Final recommendation
        result["recommendation"] = self._format_recommendation(
            result, user_profile, language
        )

        return result

    def _aggregate_technical_signals(
        self,
        technical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregate signals from technical indicators into single assessment.
        """
        signals = technical_data.get("signals", {})
        indicators = technical_data.get("indicators", {})

        bullish_count = 0
        bearish_count = 0
        total_weight = 0

        # Weighted signal counting
        signal_weights = {
            "trend": 2.0,      # Trend is most important
            "volume": 1.8,     # Volume validation critical for fake pump detection
            "macd": 1.5,
            "rsi": 1.0,
            "bollinger": 0.8,
            "adx": 0.7,
        }

        for key, value in signals.items():
            weight = signal_weights.get(key, 1.0)
            total_weight += weight

            value_str = str(value).lower()

            # CRITICAL: Volume warnings should heavily reduce confidence
            if key == "volume":
                if "fake_pump" in value_str:
                    # Fake pump = strong bearish signal (likely manipulation)
                    bearish_count += weight * 2.5
                    logger.warning(f"⚠️ Fake volume pump detected - reducing confidence")
                elif "divergence" in value_str:
                    # Volume divergence = moderate bearish signal (unreliable volume)
                    bearish_count += weight * 1.5
                    logger.warning(f"⚠️ Volume divergence detected - reducing confidence")
                elif "confirmed" in value_str:
                    # Volume confirmed = neutral (doesn't add bullish/bearish, just validates)
                    # Don't modify counts, just logged for transparency
                    logger.debug(f"✓ Volume confirmed by market data")
            elif "bullish" in value_str or value in ["oversold", "lower_band"]:
                bullish_count += weight
            elif "bearish" in value_str or value in ["overbought", "upper_band"]:
                bearish_count += weight

        # Calculate signal strength
        if total_weight > 0:
            bullish_pct = bullish_count / total_weight
            bearish_pct = bearish_count / total_weight
        else:
            bullish_pct = bearish_pct = 0

        # Determine signal
        if bullish_pct > 0.6:
            signal = "bullish"
            strength = bullish_pct
        elif bearish_pct > 0.6:
            signal = "bearish"
            strength = bearish_pct
        else:
            signal = "neutral"
            strength = 1 - max(bullish_pct, bearish_pct)

        # RSI extreme check
        rsi = indicators.get("rsi")
        if rsi:
            if rsi < 30:
                signal = "bullish"  # Oversold
            elif rsi > 70:
                signal = "bearish"  # Overbought

        return {
            "signal": signal,
            "strength": round(strength, 2),
            "bullish_weight": round(bullish_count, 2),
            "bearish_weight": round(bearish_count, 2),
            "total_weight": round(total_weight, 2),
            "raw_signals": signals,
        }

    def _aggregate_pattern_signals(
        self,
        pattern_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Aggregate signals from detected patterns.
        """
        if not pattern_data:
            return None

        candlestick = pattern_data.get("candlestick_patterns", {})
        chart = pattern_data.get("chart_patterns", {})

        # Count pattern biases
        bullish = len(candlestick.get("bullish_patterns", []))
        bearish = len(candlestick.get("bearish_patterns", []))

        # Check chart patterns
        for pattern in chart.get("patterns", []):
            if pattern.get("bias") == "bullish":
                bullish += 2  # Chart patterns have more weight
            elif pattern.get("bias") == "bearish":
                bearish += 2

        total = bullish + bearish
        if total == 0:
            return None

        if bullish > bearish:
            signal = "bullish"
            confidence = bullish / total
        elif bearish > bullish:
            signal = "bearish"
            confidence = bearish / total
        else:
            signal = "neutral"
            confidence = 0.5

        return {
            "signal": signal,
            "confidence": round(confidence, 2),
            "bullish_patterns": bullish,
            "bearish_patterns": bearish,
            "strongest_pattern": candlestick.get("detected", [{}])[0].get("name") if candlestick.get("detected") else None,
        }

    def _calculate_overall_signal(
        self,
        tech_signal: Dict[str, Any],
        pattern_signal: Optional[Dict[str, Any]],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate final signal combining all inputs with user profile.
        """
        risk_tolerance = user_profile.get("risk_tolerance", "moderate")

        # Weight factors based on risk tolerance
        weights = {
            "conservative": {"technical": 0.7, "pattern": 0.3, "confirmation_required": True},
            "moderate": {"technical": 0.6, "pattern": 0.4, "confirmation_required": False},
            "aggressive": {"technical": 0.5, "pattern": 0.5, "confirmation_required": False},
        }

        w = weights.get(risk_tolerance, weights["moderate"])

        # Calculate weighted signal
        tech_score = 0
        if tech_signal["signal"] == "bullish":
            tech_score = tech_signal["strength"]
        elif tech_signal["signal"] == "bearish":
            tech_score = -tech_signal["strength"]

        pattern_score = 0
        if pattern_signal:
            if pattern_signal["signal"] == "bullish":
                pattern_score = pattern_signal["confidence"]
            elif pattern_signal["signal"] == "bearish":
                pattern_score = -pattern_signal["confidence"]

        combined_score = (tech_score * w["technical"]) + (pattern_score * w["pattern"])

        # Determine final signal
        if combined_score > 0.3:
            signal = "BUY"
            strength = SignalStrength.BUY
        elif combined_score > 0.6:
            signal = "BUY"
            strength = SignalStrength.STRONG_BUY
        elif combined_score < -0.3:
            signal = "SELL"
            strength = SignalStrength.SELL
        elif combined_score < -0.6:
            signal = "SELL"
            strength = SignalStrength.STRONG_SELL
        else:
            signal = "HOLD"
            strength = SignalStrength.HOLD

        # Conservative users need confirmation
        if w["confirmation_required"]:
            if tech_signal["signal"] != (pattern_signal or {}).get("signal"):
                signal = "HOLD"
                strength = SignalStrength.HOLD

        confidence = abs(combined_score) * 100
        confidence = max(0, min(100, confidence))

        return {
            "signal": signal,
            "strength": strength.value,
            "confidence": round(confidence),
            "combined_score": round(combined_score, 3),
            "risk_tolerance_applied": risk_tolerance,
        }

    def _calculate_targets(
        self,
        technical_data: Dict[str, Any],
        sr_data: Optional[Dict[str, Any]],
        signal: str,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate entry, stop loss, and take profit targets.
        """
        price = technical_data.get("last_close", 0)
        atr = technical_data.get("indicators", {}).get("atr", price * 0.01)

        if atr is None:
            atr = price * 0.01

        risk_tolerance = user_profile.get("risk_tolerance", "moderate")

        # ATR multipliers based on risk
        multipliers = {
            "conservative": {"sl": 2.0, "tp": 3.0},
            "moderate": {"sl": 1.5, "tp": 2.5},
            "aggressive": {"sl": 1.0, "tp": 2.0},
        }

        m = multipliers.get(risk_tolerance, multipliers["moderate"])

        targets = {
            "current_price": round(price, 5),
        }

        if signal == "BUY":
            targets["entry"] = round(price, 5)
            targets["stop_loss"] = round(price - (atr * m["sl"]), 5)
            targets["take_profit"] = round(price + (atr * m["tp"]), 5)

            # Use S/R if available
            if sr_data:
                nearest_support = sr_data.get("nearest_support")
                if nearest_support and isinstance(nearest_support, dict):
                    sr_stop = nearest_support.get("price")
                    if sr_stop and sr_stop < price:
                        targets["stop_loss_sr"] = round(sr_stop * 0.998, 5)

                nearest_resistance = sr_data.get("nearest_resistance")
                if nearest_resistance and isinstance(nearest_resistance, dict):
                    sr_tp = nearest_resistance.get("price")
                    if sr_tp and sr_tp > price:
                        targets["take_profit_sr"] = round(sr_tp, 5)

        elif signal == "SELL":
            targets["entry"] = round(price, 5)
            targets["stop_loss"] = round(price + (atr * m["sl"]), 5)
            targets["take_profit"] = round(price - (atr * m["tp"]), 5)

            if sr_data:
                nearest_resistance = sr_data.get("nearest_resistance")
                if nearest_resistance and isinstance(nearest_resistance, dict):
                    sr_stop = nearest_resistance.get("price")
                    if sr_stop and sr_stop > price:
                        targets["stop_loss_sr"] = round(sr_stop * 1.002, 5)

                nearest_support = sr_data.get("nearest_support")
                if nearest_support and isinstance(nearest_support, dict):
                    sr_tp = nearest_support.get("price")
                    if sr_tp and sr_tp < price:
                        targets["take_profit_sr"] = round(sr_tp, 5)

        return targets

    def _format_recommendation(
        self,
        result: Dict[str, Any],
        user_profile: Dict[str, Any],
        language: str
    ) -> Dict[str, Any]:
        """
        Format final recommendation for output.
        """
        overall = result.get("overall_signal", {})
        targets = result.get("targets", {})
        ai = result.get("ai_summary", {})

        signal = overall.get("signal", "HOLD")
        confidence = overall.get("confidence", 0)

        # Action text
        if language == "vi":
            action_text = {
                "BUY": "MUA",
                "SELL": "BÁN",
                "HOLD": "GIỮ",
            }
            confidence_text = f"Độ tin cậy: {confidence}%"
        else:
            action_text = {
                "BUY": "BUY",
                "SELL": "SELL",
                "HOLD": "HOLD",
            }
            confidence_text = f"Confidence: {confidence}%"

        return {
            "action": action_text.get(signal, signal),
            "signal": signal,
            "confidence": confidence,
            "confidence_text": confidence_text,
            "entry": targets.get("entry"),
            "stop_loss": targets.get("stop_loss"),
            "take_profit": targets.get("take_profit"),
            "summary": ai.get("summary", ""),
            "reasoning": ai.get("reasoning", ""),
        }
