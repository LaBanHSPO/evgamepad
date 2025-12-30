"""
Chain-of-Thought reasoning engine for transparent AI recommendations.
Breaks down complex recommendations into verifiable steps.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from .data_provenance_tracker import ProvenanceTracker, DataSource, DataType, ValidationStatus

logger = logging.getLogger(__name__)


class RecommendationAction(Enum):
    """Recommendation actions."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    WEAK_BUY = "WEAK_BUY"
    HOLD = "HOLD"
    WEAK_SELL = "WEAK_SELL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class ReasoningStep:
    """Single step in chain-of-thought reasoning."""

    step_number: int
    category: str  # "trend", "momentum", "volume", "pattern", "risk"
    description: str
    indicators_used: List[str]
    points_awarded: int
    max_points: int
    confidence: float
    provenance_keys: List[str]  # Keys to provenance_map

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)


@dataclass
class ChainOfThoughtResult:
    """Complete chain-of-thought explanation."""

    steps: List[ReasoningStep]
    total_score: int
    max_score: int
    confidence: float  # 0.0-1.0
    recommendation: RecommendationAction
    reasoning_summary: str
    risks_identified: List[str]
    data_gaps: List[str]  # What data is missing

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "steps": [step.to_dict() for step in self.steps],
            "total_score": self.total_score,
            "max_score": self.max_score,
            "confidence": round(self.confidence, 2),
            "confidence_pct": round(self.confidence * 100),
            "recommendation": self.recommendation.value,
            "reasoning_summary": self.reasoning_summary,
            "risks_identified": self.risks_identified,
            "data_gaps": self.data_gaps
        }


class ChainOfThoughtEngine:
    """
    Generates transparent, step-by-step reasoning for recommendations.

    Scoring system:
    - Trend Analysis: 0-3 points
    - Momentum Signals: 0-3 points
    - Volume Validation: 0-2 points
    - Pattern Confirmation: 0-2 points
    - Risk Assessment: 0-2 points
    Total: 0-12 points

    Confidence mapping:
    - 10-12 points = 0.80-1.00 confidence (STRONG signal)
    - 7-9 points = 0.60-0.79 confidence (MODERATE signal)
    - 4-6 points = 0.40-0.59 confidence (WEAK signal)
    - 0-3 points = 0.00-0.39 confidence (NO TRADE)
    """

    def __init__(self, provenance_tracker: ProvenanceTracker):
        """
        Args:
            provenance_tracker: Shared provenance tracker instance
        """
        self.provenance = provenance_tracker
        self.max_total_score = 12

    def generate_explanation(
        self,
        technical_data: Dict[str, Any],
        pattern_data: Optional[Dict[str, Any]],
        risk_data: Optional[Dict[str, Any]],
        volume_validation: Optional[Dict[str, Any]],
        current_price: float
    ) -> ChainOfThoughtResult:
        """
        Generate complete chain-of-thought explanation.

        Args:
            technical_data: Output from TechnicalAnalyzer
            pattern_data: Output from PatternDetector
            risk_data: Output from RiskAnalyzer
            volume_validation: Volume validation results
            current_price: Current market price

        Returns:
            ChainOfThoughtResult with step-by-step reasoning
        """
        steps = []
        total_score = 0

        # Step 1: Trend Analysis
        trend_step = self._analyze_trend(technical_data, current_price)
        steps.append(trend_step)
        total_score += trend_step.points_awarded

        # Step 2: Momentum Signals
        momentum_step = self._analyze_momentum(technical_data)
        steps.append(momentum_step)
        total_score += momentum_step.points_awarded

        # Step 3: Volume Validation
        volume_step = self._analyze_volume(volume_validation, technical_data)
        steps.append(volume_step)
        total_score += volume_step.points_awarded

        # Step 4: Pattern Confirmation (if available)
        if pattern_data:
            pattern_step = self._analyze_patterns(pattern_data)
            steps.append(pattern_step)
            total_score += pattern_step.points_awarded

        # Step 5: Risk Assessment (if available)
        if risk_data:
            risk_step = self._analyze_risk(risk_data)
            steps.append(risk_step)
            total_score += risk_step.points_awarded

        # Calculate confidence
        confidence = total_score / self.max_total_score

        # Determine recommendation
        recommendation = self._map_score_to_action(total_score, confidence)

        # Generate reasoning summary
        reasoning_summary = self._generate_summary(steps, total_score, recommendation)

        # Identify risks and data gaps
        risks = self._identify_risks(steps, technical_data, pattern_data, volume_validation)
        data_gaps = self._identify_data_gaps(pattern_data, risk_data, volume_validation)

        return ChainOfThoughtResult(
            steps=steps,
            total_score=total_score,
            max_score=self.max_total_score,
            confidence=confidence,
            recommendation=recommendation,
            reasoning_summary=reasoning_summary,
            risks_identified=risks,
            data_gaps=data_gaps
        )

    def _analyze_trend(
        self,
        technical_data: Dict[str, Any],
        current_price: float
    ) -> ReasoningStep:
        """Analyze trend indicators (max 3 points)."""
        points = 0
        max_points = 3
        indicators_used = []
        description_parts = []

        indicators = technical_data.get("indicators", {})
        signals = technical_data.get("signals", {})

        # EMA trend (1 point)
        ema_21 = indicators.get("ema_21")
        ema_50 = indicators.get("ema_50")
        if ema_21 and ema_50:
            indicators_used.extend(["ema_21", "ema_50"])
            if current_price > ema_21 > ema_50:
                points += 1
                description_parts.append(f"✅ Bullish EMA alignment: Price ({current_price:.2f}) > EMA21 ({ema_21:.2f}) > EMA50 ({ema_50:.2f})")
            elif current_price < ema_21 < ema_50:
                points -= 1
                description_parts.append(f"❌ Bearish EMA alignment: Price ({current_price:.2f}) < EMA21 ({ema_21:.2f}) < EMA50 ({ema_50:.2f})")
            else:
                description_parts.append(f"⚠️ Mixed EMA signals: Price ({current_price:.2f}), EMA21 ({ema_21:.2f}), EMA50 ({ema_50:.2f})")

        # ADX trend strength (1 point)
        adx = indicators.get("adx", {})
        if isinstance(adx, dict):
            adx_val = adx.get("adx")
            if adx_val:
                indicators_used.append("adx")
                if adx_val > 25:
                    points += 1
                    description_parts.append(f"✅ Strong trend: ADX = {adx_val:.1f}")
                else:
                    description_parts.append(f"⚠️ Weak trend: ADX = {adx_val:.1f}")

        # Trend signal (1 point)
        trend_signal = signals.get("trend")
        if trend_signal:
            if trend_signal == "bullish":
                points += 1
                description_parts.append(f"✅ Bullish trend confirmed")
            elif trend_signal == "bearish":
                points -= 1
                description_parts.append(f"❌ Bearish trend detected")

        # Clamp points to [0, max_points]
        points = max(0, min(points, max_points))

        description = f"**Trend Analysis:** {' | '.join(description_parts)}"

        return ReasoningStep(
            step_number=1,
            category="trend",
            description=description,
            indicators_used=indicators_used,
            points_awarded=points,
            max_points=max_points,
            confidence=points / max_points if max_points > 0 else 0.5,
            provenance_keys=indicators_used
        )

    def _analyze_momentum(
        self,
        technical_data: Dict[str, Any]
    ) -> ReasoningStep:
        """Analyze momentum indicators (max 3 points)."""
        points = 0
        max_points = 3
        indicators_used = []
        description_parts = []

        indicators = technical_data.get("indicators", {})
        signals = technical_data.get("signals", {})

        # RSI (1 point)
        rsi = indicators.get("rsi")
        if rsi:
            indicators_used.append("rsi")
            if rsi < 30:
                points += 1
                description_parts.append(f"✅ RSI oversold: {rsi:.1f}")
            elif rsi > 70:
                points -= 1
                description_parts.append(f"❌ RSI overbought: {rsi:.1f}")
            else:
                description_parts.append(f"⚠️ RSI neutral: {rsi:.1f}")

        # MACD (2 points for crossover, 1 for position)
        macd_signal = signals.get("macd")
        if macd_signal:
            indicators_used.append("macd")
            if "bullish_crossover" in str(macd_signal).lower():
                points += 2
                description_parts.append(f"✅ MACD bullish crossover")
            elif "bearish_crossover" in str(macd_signal).lower():
                points -= 2
                description_parts.append(f"❌ MACD bearish crossover")
            elif "bullish" in str(macd_signal).lower():
                points += 1
                description_parts.append(f"✅ MACD bullish position")
            elif "bearish" in str(macd_signal).lower():
                points -= 1
                description_parts.append(f"❌ MACD bearish position")

        # Clamp points
        points = max(0, min(points, max_points))

        description = f"**Momentum Signals:** {' | '.join(description_parts)}"

        return ReasoningStep(
            step_number=2,
            category="momentum",
            description=description,
            indicators_used=indicators_used,
            points_awarded=points,
            max_points=max_points,
            confidence=points / max_points if max_points > 0 else 0.5,
            provenance_keys=indicators_used
        )

    def _analyze_volume(
        self,
        volume_validation: Optional[Dict[str, Any]],
        technical_data: Dict[str, Any]
    ) -> ReasoningStep:
        """Analyze volume validation (max 2 points)."""
        points = 0
        max_points = 2
        indicators_used = ["volume_validation"]
        description_parts = []

        if not volume_validation:
            description = "⚠️ **Volume Validation:** No market volume data available"
            return ReasoningStep(
                step_number=3,
                category="volume",
                description=description,
                indicators_used=[],
                points_awarded=0,
                max_points=max_points,
                confidence=0.5,
                provenance_keys=[]
            )

        is_fake_pump = volume_validation.get("is_fake_pump", False)
        is_divergent = volume_validation.get("is_divergent", False)
        divergence_pct = volume_validation.get("divergence_pct", 0)

        if is_fake_pump:
            points = 0  # Severe penalty - no points awarded
            description_parts.append(f"🚨 FAKE VOLUME PUMP detected ({divergence_pct*100:.1f}% divergence)")
        elif is_divergent:
            points = 1  # Moderate concern
            description_parts.append(f"⚠️ Volume divergence: {divergence_pct*100:.1f}% (unreliable)")
        else:
            points = 2  # Volume confirmed
            description_parts.append(f"✅ Volume confirmed: {divergence_pct*100:.1f}% divergence (within threshold)")

        mt5_vol = volume_validation.get("mt5_volume", 0)
        market_vol = volume_validation.get("market_volume")
        if market_vol:
            description_parts.append(f"MT5: {mt5_vol:.0f}, Market: {market_vol:.0f}")

        description = f"**Volume Validation:** {' | '.join(description_parts)}"

        return ReasoningStep(
            step_number=3,
            category="volume",
            description=description,
            indicators_used=indicators_used,
            points_awarded=points,
            max_points=max_points,
            confidence=points / max_points if max_points > 0 else 0.5,
            provenance_keys=indicators_used
        )

    def _analyze_patterns(
        self,
        pattern_data: Dict[str, Any]
    ) -> ReasoningStep:
        """Analyze candlestick/chart patterns (max 2 points)."""
        points = 0
        max_points = 2
        indicators_used = ["candlestick_patterns"]
        description_parts = []

        candlestick = pattern_data.get("candlestick_patterns", {})
        bullish_patterns = candlestick.get("bullish_patterns", [])
        bearish_patterns = candlestick.get("bearish_patterns", [])

        if bullish_patterns:
            points += min(len(bullish_patterns), 2)
            pattern_names = [p.get("name", "unknown") for p in bullish_patterns[:2]]
            description_parts.append(f"✅ Bullish patterns: {', '.join(pattern_names)}")

        if bearish_patterns:
            points -= min(len(bearish_patterns), 2)
            pattern_names = [p.get("name", "unknown") for p in bearish_patterns[:2]]
            description_parts.append(f"❌ Bearish patterns: {', '.join(pattern_names)}")

        if not bullish_patterns and not bearish_patterns:
            description_parts.append("⚠️ No significant patterns detected")

        # Clamp points
        points = max(0, min(points, max_points))

        description = f"**Pattern Confirmation:** {' | '.join(description_parts)}"

        return ReasoningStep(
            step_number=4,
            category="pattern",
            description=description,
            indicators_used=indicators_used,
            points_awarded=points,
            max_points=max_points,
            confidence=points / max_points if max_points > 0 else 0.5,
            provenance_keys=indicators_used
        )

    def _analyze_risk(
        self,
        risk_data: Dict[str, Any]
    ) -> ReasoningStep:
        """Analyze risk assessment (max 2 points)."""
        points = 0
        max_points = 2
        indicators_used = ["risk_analysis"]
        description_parts = []

        rr = risk_data.get("risk_reward", {})
        rr_ratio = rr.get("rr_ratio", 0)
        recommendation = rr.get("recommendation", "poor")

        # R/R ratio scoring
        if rr_ratio >= 3.0:
            points = 2
            description_parts.append(f"✅ Excellent R/R: {rr_ratio:.1f}:1 ({recommendation})")
        elif rr_ratio >= 2.0:
            points = 2
            description_parts.append(f"✅ Good R/R: {rr_ratio:.1f}:1 ({recommendation})")
        elif rr_ratio >= 1.5:
            points = 1
            description_parts.append(f"⚠️ Acceptable R/R: {rr_ratio:.1f}:1 ({recommendation})")
        else:
            points = 0
            description_parts.append(f"❌ Poor R/R: {rr_ratio:.1f}:1 ({recommendation})")

        # Position sizing
        position_sizing = risk_data.get("position_sizing", {})
        ff = position_sizing.get("fixed_fractional", {})
        if "limit_exceeded" in ff:
            description_parts.append("⚠️ Position size capped at risk limit")

        description = f"**Risk Assessment:** {' | '.join(description_parts)}"

        return ReasoningStep(
            step_number=5,
            category="risk",
            description=description,
            indicators_used=indicators_used,
            points_awarded=points,
            max_points=max_points,
            confidence=points / max_points if max_points > 0 else 0.5,
            provenance_keys=indicators_used
        )

    def _map_score_to_action(
        self,
        total_score: int,
        confidence: float
    ) -> RecommendationAction:
        """Map total score to recommendation action."""
        if total_score >= 10:
            return RecommendationAction.STRONG_BUY if confidence > 0.85 else RecommendationAction.BUY
        elif total_score >= 7:
            return RecommendationAction.BUY if confidence > 0.7 else RecommendationAction.WEAK_BUY
        elif total_score >= 5:
            return RecommendationAction.HOLD
        elif total_score >= 3:
            return RecommendationAction.WEAK_SELL
        elif total_score >= 1:
            return RecommendationAction.SELL
        else:
            return RecommendationAction.STRONG_SELL

    def _generate_summary(
        self,
        steps: List[ReasoningStep],
        total_score: int,
        recommendation: RecommendationAction
    ) -> str:
        """Generate natural language summary."""
        strong_points = [s for s in steps if s.points_awarded >= s.max_points * 0.7]
        weak_points = [s for s in steps if s.points_awarded < s.max_points * 0.4]

        summary_parts = [
            f"Recommendation: **{recommendation.value}** ({total_score}/{self.max_total_score} points)"
        ]

        if strong_points:
            categories = [s.category.title() for s in strong_points]
            summary_parts.append(f"Strong signals from: {', '.join(categories)}")

        if weak_points:
            categories = [s.category.title() for s in weak_points]
            summary_parts.append(f"Weak signals from: {', '.join(categories)}")

        return " | ".join(summary_parts)

    def _identify_risks(
        self,
        steps: List[ReasoningStep],
        technical_data: Dict[str, Any],
        pattern_data: Optional[Dict[str, Any]],
        volume_validation: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Identify risks and concerns."""
        risks = []

        # Volume warnings
        if volume_validation:
            if volume_validation.get("is_fake_pump"):
                risks.append("🚨 CRITICAL: Fake volume pump detected - likely market manipulation")
            elif volume_validation.get("is_divergent"):
                risks.append("⚠️ Volume divergence - broker volume differs from market data")

        # Weak trend
        trend_step = next((s for s in steps if s.category == "trend"), None)
        if trend_step and trend_step.confidence < 0.5:
            risks.append("⚠️ Weak trend - direction unclear")

        # Conflicting signals
        momentum_step = next((s for s in steps if s.category == "momentum"), None)
        if trend_step and momentum_step:
            if trend_step.points_awarded > 2 and momentum_step.points_awarded < 1:
                risks.append("⚠️ Conflicting signals - strong trend but weak momentum")

        return risks

    def _identify_data_gaps(
        self,
        pattern_data: Optional[Dict[str, Any]],
        risk_data: Optional[Dict[str, Any]],
        volume_validation: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Identify missing data that could improve recommendation."""
        gaps = []

        if not pattern_data:
            gaps.append("Pattern analysis not performed")

        if not risk_data:
            gaps.append("Risk assessment not calculated")

        if not volume_validation:
            gaps.append("Volume validation unavailable - cannot detect fake pumps")

        # Always missing (future phases)
        gaps.append("News sentiment not analyzed")
        gaps.append("Cross-market correlations not checked")

        return gaps
