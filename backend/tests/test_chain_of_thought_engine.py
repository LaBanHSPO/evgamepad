"""
Tests for chain-of-thought reasoning engine.
"""
import pytest
from datetime import datetime

from app.advisor.chain_of_thought_engine import (
    ChainOfThoughtEngine,
    ChainOfThoughtResult,
    RecommendationAction
)
from app.advisor.data_provenance_tracker import (
    ProvenanceTracker,
    DataSource,
    DataType
)


class TestChainOfThoughtEngine:
    """Test chain-of-thought reasoning engine."""

    @pytest.fixture
    def provenance_tracker(self):
        return ProvenanceTracker()

    @pytest.fixture
    def cot_engine(self, provenance_tracker):
        return ChainOfThoughtEngine(provenance_tracker)

    def test_generate_explanation_bullish(self, cot_engine):
        """Test CoT generation for bullish scenario."""
        technical_data = {
            "indicators": {
                "ema_21": 2634.50,
                "ema_50": 2620.30,
                "rsi": 28.5,
                "adx": {"adx": 45, "plus_di": 25, "minus_di": 15},
                "macd": {"macd": 1.2, "signal": 0.8, "histogram": 0.4}
            },
            "signals": {
                "trend": "bullish",
                "macd": "bullish_crossover",
                "rsi": "oversold"
            },
            "last_close": 2634.50
        }

        volume_validation = {
            "is_fake_pump": False,
            "is_divergent": False,
            "divergence_pct": 0.027,
            "mt5_volume": 15200000,
            "market_volume": 14800000,
            "confidence": 0.85
        }

        result = cot_engine.generate_explanation(
            technical_data=technical_data,
            pattern_data=None,
            risk_data=None,
            volume_validation=volume_validation,
            current_price=2634.50
        )

        assert result.total_score >= 7  # Should be bullish
        assert result.confidence >= 0.55  # Adjusted for realistic confidence
        assert result.recommendation.value in ["BUY", "STRONG_BUY", "WEAK_BUY"]
        assert len(result.steps) >= 3  # Trend, Momentum, Volume

    def test_generate_explanation_bearish(self, cot_engine):
        """Test CoT generation for bearish scenario."""
        technical_data = {
            "indicators": {
                "ema_21": 2620.30,
                "ema_50": 2634.50,
                "rsi": 75.5,
                "adx": {"adx": 40},
            },
            "signals": {
                "trend": "bearish",
                "macd": "bearish_crossover",
                "rsi": "overbought"
            },
            "last_close": 2620.30
        }

        volume_validation = {
            "is_fake_pump": False,
            "is_divergent": False,
            "divergence_pct": 0.02
        }

        result = cot_engine.generate_explanation(
            technical_data=technical_data,
            pattern_data=None,
            risk_data=None,
            volume_validation=volume_validation,
            current_price=2620.30
        )

        # Bearish signals should result in low score
        assert result.total_score <= 5
        assert result.recommendation.value in ["HOLD", "SELL", "WEAK_SELL", "STRONG_SELL"]

    def test_generate_explanation_fake_pump(self, cot_engine):
        """Test CoT detects fake volume pump."""
        technical_data = {
            "indicators": {"ema_21": 2634.50, "ema_50": 2620.30},
            "signals": {"trend": "bullish"},
            "last_close": 2634.50
        }

        volume_validation = {
            "is_fake_pump": True,
            "is_divergent": True,
            "divergence_pct": 0.85,
            "mt5_volume": 50000000,
            "market_volume": 15000000
        }

        result = cot_engine.generate_explanation(
            technical_data=technical_data,
            pattern_data=None,
            risk_data=None,
            volume_validation=volume_validation,
            current_price=2634.50
        )

        # Volume step should award 0 points for fake pump
        volume_step = next(s for s in result.steps if s.category == "volume")
        assert volume_step.points_awarded == 0
        assert "FAKE VOLUME PUMP" in volume_step.description
        assert len(result.risks_identified) > 0
        assert any("CRITICAL" in risk for risk in result.risks_identified)

    def test_generate_explanation_with_patterns(self, cot_engine):
        """Test CoT with pattern data."""
        technical_data = {
            "indicators": {"ema_21": 2634.50, "ema_50": 2620.30},
            "signals": {"trend": "bullish"},
            "last_close": 2634.50
        }

        pattern_data = {
            "candlestick_patterns": {
                "bullish_patterns": [
                    {"name": "Morning Star", "confidence": 0.85},
                    {"name": "Bullish Engulfing", "confidence": 0.75}
                ],
                "bearish_patterns": []
            }
        }

        volume_validation = {
            "is_fake_pump": False,
            "is_divergent": False,
            "divergence_pct": 0.02
        }

        result = cot_engine.generate_explanation(
            technical_data=technical_data,
            pattern_data=pattern_data,
            risk_data=None,
            volume_validation=volume_validation,
            current_price=2634.50
        )

        # Should have pattern step
        pattern_step = next((s for s in result.steps if s.category == "pattern"), None)
        assert pattern_step is not None
        assert pattern_step.points_awarded > 0
        assert "Morning Star" in pattern_step.description or "Bullish Engulfing" in pattern_step.description

    def test_generate_explanation_with_risk_data(self, cot_engine):
        """Test CoT with risk assessment."""
        technical_data = {
            "indicators": {"ema_21": 2634.50},
            "signals": {"trend": "bullish"},
            "last_close": 2634.50
        }

        risk_data = {
            "risk_reward": {
                "rr_ratio": 3.2,
                "recommendation": "excellent"
            },
            "position_sizing": {
                "fixed_fractional": {}
            }
        }

        volume_validation = {"is_fake_pump": False, "is_divergent": False}

        result = cot_engine.generate_explanation(
            technical_data=technical_data,
            pattern_data=None,
            risk_data=risk_data,
            volume_validation=volume_validation,
            current_price=2634.50
        )

        # Should have risk step
        risk_step = next((s for s in result.steps if s.category == "risk"), None)
        assert risk_step is not None
        assert risk_step.points_awarded == 2  # Excellent R/R
        assert "Excellent R/R" in risk_step.description

    def test_trend_analysis_bullish_ema(self, cot_engine):
        """Test trend analysis with bullish EMA alignment."""
        technical_data = {
            "indicators": {
                "ema_21": 2634.50,
                "ema_50": 2620.30,
                "adx": {"adx": 30}
            },
            "signals": {"trend": "bullish"},
            "last_close": 2640.00
        }

        step = cot_engine._analyze_trend(technical_data, 2640.00)

        assert step.category == "trend"
        assert step.points_awarded >= 2  # EMA + ADX + Trend signal
        assert "Bullish EMA alignment" in step.description
        assert "Strong trend" in step.description

    def test_momentum_analysis_rsi_oversold(self, cot_engine):
        """Test momentum analysis with oversold RSI."""
        technical_data = {
            "indicators": {"rsi": 25.5},
            "signals": {"macd": "bullish_crossover"}
        }

        step = cot_engine._analyze_momentum(technical_data)

        assert step.category == "momentum"
        assert step.points_awarded >= 2  # RSI oversold + MACD crossover
        assert "RSI oversold" in step.description
        assert "MACD bullish crossover" in step.description

    def test_volume_analysis_divergence(self, cot_engine):
        """Test volume analysis with divergence."""
        volume_validation = {
            "is_fake_pump": False,
            "is_divergent": True,
            "divergence_pct": 0.45,
            "mt5_volume": 20000000,
            "market_volume": 14000000
        }

        step = cot_engine._analyze_volume(volume_validation, {})

        assert step.category == "volume"
        assert step.points_awarded == 1  # Divergent but not fake pump
        assert "Volume divergence" in step.description

    def test_volume_analysis_no_data(self, cot_engine):
        """Test volume analysis when data unavailable."""
        step = cot_engine._analyze_volume(None, {})

        assert step.category == "volume"
        assert step.points_awarded == 0
        assert "No market volume data available" in step.description
        assert step.confidence == 0.5

    def test_map_score_to_action(self, cot_engine):
        """Test score to action mapping."""
        # Strong buy
        action = cot_engine._map_score_to_action(12, 0.95)
        assert action == RecommendationAction.STRONG_BUY

        # Buy
        action = cot_engine._map_score_to_action(10, 0.80)
        assert action == RecommendationAction.BUY

        # Hold
        action = cot_engine._map_score_to_action(6, 0.50)
        assert action == RecommendationAction.HOLD

        # Sell
        action = cot_engine._map_score_to_action(2, 0.20)
        assert action == RecommendationAction.SELL

    def test_generate_summary(self, cot_engine):
        """Test reasoning summary generation."""
        from app.advisor.chain_of_thought_engine import ReasoningStep

        steps = [
            ReasoningStep(
                step_number=1,
                category="trend",
                description="Trend step",
                indicators_used=["ema"],
                points_awarded=3,
                max_points=3,
                confidence=1.0,
                provenance_keys=[]
            ),
            ReasoningStep(
                step_number=2,
                category="momentum",
                description="Momentum step",
                indicators_used=["rsi"],
                points_awarded=1,
                max_points=3,
                confidence=0.33,
                provenance_keys=[]
            ),
        ]

        summary = cot_engine._generate_summary(
            steps, 4, RecommendationAction.HOLD
        )

        assert "HOLD" in summary
        assert "4/12" in summary
        assert "Trend" in summary  # Strong signal
        assert "Momentum" in summary  # Weak signal

    def test_identify_risks(self, cot_engine):
        """Test risk identification."""
        from app.advisor.chain_of_thought_engine import ReasoningStep

        steps = [
            ReasoningStep(
                step_number=1,
                category="trend",
                description="",
                indicators_used=[],
                points_awarded=0,
                max_points=3,
                confidence=0.2,  # Weak trend
                provenance_keys=[]
            )
        ]

        volume_validation = {
            "is_fake_pump": True,
            "is_divergent": True
        }

        risks = cot_engine._identify_risks(steps, {}, None, volume_validation)

        assert len(risks) > 0
        assert any("CRITICAL" in risk for risk in risks)
        assert any("Weak trend" in risk for risk in risks)

    def test_identify_data_gaps(self, cot_engine):
        """Test data gap identification."""
        gaps = cot_engine._identify_data_gaps(None, None, None)

        assert "Pattern analysis not performed" in gaps
        assert "Risk assessment not calculated" in gaps
        assert any("Volume validation" in gap for gap in gaps)
        assert "News sentiment not analyzed" in gaps

    def test_to_dict_serialization(self, cot_engine):
        """Test result serialization."""
        technical_data = {
            "indicators": {"rsi": 50},
            "signals": {"trend": "neutral"},
            "last_close": 2630.00
        }

        result = cot_engine.generate_explanation(
            technical_data=technical_data,
            pattern_data=None,
            risk_data=None,
            volume_validation={"is_fake_pump": False, "is_divergent": False},
            current_price=2630.00
        )

        result_dict = result.to_dict()

        assert "steps" in result_dict
        assert "total_score" in result_dict
        assert "max_score" in result_dict
        assert "confidence" in result_dict
        assert "confidence_pct" in result_dict
        assert "recommendation" in result_dict
        assert "reasoning_summary" in result_dict
        assert "risks_identified" in result_dict
        assert "data_gaps" in result_dict

        # Check steps serialization
        assert isinstance(result_dict["steps"], list)
        if len(result_dict["steps"]) > 0:
            assert "step_number" in result_dict["steps"][0]
            assert "category" in result_dict["steps"][0]
