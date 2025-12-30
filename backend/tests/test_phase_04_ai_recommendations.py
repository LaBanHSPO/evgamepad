"""
Unit tests for Phase 04 - AI-powered recommendations.
Tests AISummarizer, RecommendationEngine, UserProfile models, and integration flows.
"""
import pytest
import sys
import os
import json
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.advisor.ai_summarizer import AISummarizer, TECHNICAL_SUMMARY_PROMPT_VI, TECHNICAL_SUMMARY_PROMPT_EN
from app.advisor.recommendation_engine import RecommendationEngine, SignalStrength
from app.models.user_profile import UserProfile, UserProfileUpdate, RiskTolerance, RecommendationRequest, RecommendationResponse
from app.models.advisor_models import TechnicalIndicators, SignalSummary


# ============================================================================
# AISummarizer Tests
# ============================================================================

class TestAISummarizer:
    """Test suite for AISummarizer."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock._client = AsyncMock()
        return redis_mock

    @pytest.fixture
    def summarizer(self, mock_redis):
        """Create AISummarizer instance with mocks."""
        return AISummarizer(
            anthropic_api_key="test_key_anthropic",
            deepseek_api_key="test_key_deepseek",
            default_model="claude",
            redis_client=mock_redis
        )

    def test_initialization(self, summarizer):
        """Test AISummarizer initializes correctly."""
        assert summarizer.anthropic_key == "test_key_anthropic"
        assert summarizer.deepseek_key == "test_key_deepseek"
        assert summarizer.default_model == "claude"
        assert summarizer.redis is not None

    def test_generate_cache_key(self, summarizer):
        """Test cache key generation."""
        data = {
            "symbol": "XAUUSD",
            "timeframe": "H1",
            "rsi_signal": "overbought",
            "trend": "bullish",
            "risk_profile": "moderate",
            "price": 2105.456,
        }
        cache_key = summarizer._generate_cache_key(data)

        assert cache_key.startswith("ai_summary:")
        # "ai_summary:" (11 chars) + 32 char MD5
        assert len(cache_key) == 43

        # Same data should generate same key
        cache_key2 = summarizer._generate_cache_key(data)
        assert cache_key == cache_key2

        # Different data should generate different key
        data["price"] = 2115.123
        cache_key3 = summarizer._generate_cache_key(data)
        assert cache_key != cache_key3

    @pytest.mark.asyncio
    async def test_cache_hit(self, summarizer, mock_redis):
        """Test cache hit scenario."""
        data = {
            "symbol": "XAUUSD",
            "timeframe": "H1",
            "rsi_signal": "overbought",
            "trend": "bullish",
            "risk_profile": "moderate",
            "price": 2105.0,
        }

        cached_response = {
            "summary": "Cached summary",
            "signal": "SELL",
            "confidence": 85,
            "reasoning": "From cache"
        }

        # Mock cache hit
        mock_redis._client.get = AsyncMock(return_value=json.dumps(cached_response))

        result = await summarizer.generate_summary(data, language="vi", use_cache=True)

        assert result["cached"] == True
        assert result["summary"] == "Cached summary"
        assert result["signal"] == "SELL"
        assert result["confidence"] == 85

    @pytest.mark.asyncio
    async def test_cache_miss(self, summarizer, mock_redis):
        """Test cache miss scenario."""
        data = {
            "symbol": "XAUUSD",
            "timeframe": "H1",
            "rsi_signal": "neutral",
            "trend": "neutral",
            "risk_profile": "moderate",
            "price": 2105.0,
            "indicators": {"rsi": 50},
            "signals": {"trend": "neutral"},
            "candlestick_patterns": {"detected": []},
            "support_resistance": {},
        }

        # Mock cache miss
        mock_redis._client.get = AsyncMock(return_value=None)

        # Mock Claude API call
        with patch.object(summarizer, '_call_claude', new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = json.dumps({
                "summary": "Generated summary",
                "signal": "HOLD",
                "confidence": 50,
                "reasoning": "Neutral signals"
            })

            result = await summarizer.generate_summary(data, language="vi", use_cache=True)

            assert result["cached"] == False
            assert result["model"] == "claude"
            assert result["language"] == "vi"
            assert result["signal"] == "HOLD"
            mock_claude.assert_called_once()

    def test_build_prompt_vietnamese(self, summarizer):
        """Test Vietnamese prompt building."""
        data = {
            "symbol": "XAUUSD",
            "timeframe": "H1",
            "last_price": 2105.50,
            "indicators": {
                "rsi": 65,
                "macd": {"macd": 0.5, "signal": 0.3},
                "atr": 10,
            },
            "signals": {
                "rsi": "overbought",
                "trend": "bullish",
                "macd": "bullish"
            },
            "candlestick_patterns": {
                "detected": [{"name": "Hammer"}]
            },
            "support_resistance": {
                "nearest_support": {"price": 2100},
                "nearest_resistance": {"price": 2110}
            },
            "risk_profile": "moderate",
        }

        prompt = summarizer._build_prompt(data, "vi")

        assert "XAUUSD" in prompt
        assert "H1" in prompt
        assert "2105.5" in prompt
        assert "65" in prompt
        assert "Hammer" in prompt
        assert "2100" in prompt
        assert "2110" in prompt
        assert "moderate" in prompt
        assert "Việt" in prompt or "tiếng Việt" in prompt.lower() or "bạn là" in prompt.lower()

    def test_build_prompt_english(self, summarizer):
        """Test English prompt building."""
        data = {
            "symbol": "XAUUSD",
            "timeframe": "H4",
            "last_price": 2105.50,
            "indicators": {
                "rsi": 35,
                "macd": {"macd": -0.2, "signal": -0.1},
            },
            "signals": {
                "rsi": "oversold",
                "trend": "bearish",
            },
            "candlestick_patterns": {
                "detected": []
            },
            "support_resistance": {},
            "risk_profile": "aggressive",
        }

        prompt = summarizer._build_prompt(data, "en")

        assert "XAUUSD" in prompt
        assert "H4" in prompt
        assert "35" in prompt
        assert "aggressive" in prompt
        assert "You are a technical analysis expert" in prompt

    def test_parse_response_valid_json(self, summarizer):
        """Test parsing valid JSON response."""
        response = json.dumps({
            "summary": "Strong bullish trend",
            "signal": "BUY",
            "confidence": "75%",
            "reasoning": "All indicators aligned"
        })

        result = summarizer._parse_response(response)

        assert result["summary"] == "Strong bullish trend"
        assert result["signal"] == "BUY"
        assert result["confidence"] == 75  # Percentage converted
        assert result["reasoning"] == "All indicators aligned"

    def test_parse_response_json_in_markdown(self, summarizer):
        """Test parsing JSON wrapped in markdown code blocks."""
        response = """```json
{
  "summary": "Analysis result",
  "signal": "SELL",
  "confidence": 60,
  "reasoning": "Bearish signals detected"
}
```"""

        result = summarizer._parse_response(response)

        assert result["signal"] == "SELL"
        assert result["confidence"] == 60
        assert result["summary"] == "Analysis result"

    def test_parse_response_invalid_signal_normalization(self, summarizer):
        """Test signal normalization to valid values."""
        response = json.dumps({
            "summary": "Test",
            "signal": "maybe",
            "confidence": 50,
            "reasoning": "Test"
        })

        result = summarizer._parse_response(response)

        # Invalid signals normalized to HOLD
        assert result["signal"] == "HOLD"

    def test_parse_response_confidence_bounds(self, summarizer):
        """Test confidence is bounded between 0 and 100."""
        # Test value > 100
        response = json.dumps({
            "summary": "Test",
            "signal": "BUY",
            "confidence": 150,
            "reasoning": "Test"
        })

        result = summarizer._parse_response(response)
        assert result["confidence"] == 100

        # Test negative value
        response = json.dumps({
            "summary": "Test",
            "signal": "BUY",
            "confidence": -50,
            "reasoning": "Test"
        })

        result = summarizer._parse_response(response)
        assert result["confidence"] == 0

    def test_parse_response_fallback_invalid_json(self, summarizer):
        """Test fallback parsing for invalid JSON."""
        response = "This is not JSON but contains BUY signal"

        result = summarizer._parse_response(response)

        assert result["signal"] == "BUY"
        assert result["confidence"] == 50  # Default fallback
        assert result["summary"][:50] in response[:500] or response[:500] in result["summary"]

    def test_parse_response_fallback_sell_detection(self, summarizer):
        """Test fallback parsing detects SELL signal."""
        response = "I think we should SELL this position"

        result = summarizer._parse_response(response)

        assert result["signal"] == "SELL"

    @pytest.mark.asyncio
    async def test_generate_summary_with_claude(self, summarizer):
        """Test complete summary generation with Claude."""
        data = {
            "symbol": "XAUUSD",
            "timeframe": "H1",
            "last_price": 2105.50,
            "indicators": {"rsi": 55},
            "signals": {"trend": "neutral"},
            "candlestick_patterns": {},
            "support_resistance": {},
            "risk_profile": "moderate",
        }

        with patch.object(summarizer, '_call_claude', new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = json.dumps({
                "summary": "Neutral conditions",
                "signal": "HOLD",
                "confidence": 50,
                "reasoning": "Balanced signals"
            })

            result = await summarizer.generate_summary(data, model="claude")

            assert result["model"] == "claude"
            assert result["signal"] == "HOLD"
            assert "generated_at" in result

    @pytest.mark.asyncio
    async def test_generate_summary_with_deepseek(self, summarizer):
        """Test complete summary generation with DeepSeek."""
        data = {
            "symbol": "XAUUSD",
            "timeframe": "H1",
            "last_price": 2105.50,
            "indicators": {"rsi": 75},
            "signals": {"trend": "bullish"},
            "candlestick_patterns": {},
            "support_resistance": {},
            "risk_profile": "moderate",
        }

        with patch.object(summarizer, '_call_deepseek', new_callable=AsyncMock) as mock_deepseek:
            mock_deepseek.return_value = json.dumps({
                "summary": "Strong bullish",
                "signal": "BUY",
                "confidence": 80,
                "reasoning": "Strong signals"
            })

            result = await summarizer.generate_summary(data, model="deepseek")

            assert result["model"] == "deepseek"
            assert result["signal"] == "BUY"
            assert result["confidence"] == 80

    @pytest.mark.asyncio
    async def test_generate_summary_error_handling(self, summarizer):
        """Test error handling in summary generation."""
        data = {
            "symbol": "XAUUSD",
            "timeframe": "H1",
            "last_price": 2105.50,
            "indicators": {},
            "signals": {},
            "candlestick_patterns": {},
            "support_resistance": {},
            "risk_profile": "moderate",
        }

        with patch.object(summarizer, '_call_claude', side_effect=RuntimeError("API Error")):
            result = await summarizer.generate_summary(data)

            assert result["signal"] == "HOLD"
            assert result["confidence"] == 0
            assert "error" in result


# ============================================================================
# RecommendationEngine Tests
# ============================================================================

class TestRecommendationEngine:
    """Test suite for RecommendationEngine."""

    @pytest.fixture
    def mock_ai_summarizer(self):
        """Create mock AI summarizer."""
        summarizer = AsyncMock()
        summarizer.generate_summary = AsyncMock(return_value={
            "summary": "AI Generated summary",
            "signal": "BUY",
            "confidence": 75,
            "reasoning": "Multiple bullish signals"
        })
        return summarizer

    @pytest.fixture
    def engine(self, mock_ai_summarizer):
        """Create RecommendationEngine instance."""
        return RecommendationEngine(mock_ai_summarizer)

    def test_initialization(self, engine, mock_ai_summarizer):
        """Test engine initializes with AI summarizer."""
        assert engine.ai_summarizer == mock_ai_summarizer

    def test_aggregate_technical_signals_bullish(self, engine):
        """Test aggregating bullish technical signals."""
        technical_data = {
            "signals": {
                "trend": "bullish",
                "macd": "bullish",
                "rsi": "normal",
                "bollinger": "lower_band"
            },
            "indicators": {
                "rsi": 35
            }
        }

        result = engine._aggregate_technical_signals(technical_data)

        assert result["signal"] == "bullish"
        assert result["strength"] > 0
        assert result["bullish_weight"] > result["bearish_weight"]

    def test_aggregate_technical_signals_bearish(self, engine):
        """Test aggregating bearish technical signals."""
        technical_data = {
            "signals": {
                "trend": "bearish",
                "macd": "bearish",
                "rsi": "normal",
            },
            "indicators": {
                "rsi": 75  # Overbought
            }
        }

        result = engine._aggregate_technical_signals(technical_data)

        assert result["signal"] == "bearish"
        assert result["bearish_weight"] >= result["bullish_weight"]

    def test_aggregate_technical_signals_rsi_extreme(self, engine):
        """Test RSI extreme values override other signals."""
        # RSI < 30 (oversold) should signal bullish
        technical_data = {
            "signals": {
                "trend": "bearish",
                "macd": "bearish",
            },
            "indicators": {
                "rsi": 20
            }
        }

        result = engine._aggregate_technical_signals(technical_data)
        assert result["signal"] == "bullish"  # RSI override

        # RSI > 70 (overbought) should signal bearish
        technical_data["indicators"]["rsi"] = 80
        result = engine._aggregate_technical_signals(technical_data)
        assert result["signal"] == "bearish"

    def test_aggregate_pattern_signals_bullish_patterns(self, engine):
        """Test aggregating bullish pattern signals."""
        pattern_data = {
            "candlestick_patterns": {
                "bullish_patterns": ["Hammer", "Engulfing"],
                "bearish_patterns": [],
                "detected": [{"name": "Hammer"}]
            },
            "chart_patterns": {
                "patterns": [
                    {"bias": "bullish"},
                    {"bias": "bullish"}
                ]
            }
        }

        result = engine._aggregate_pattern_signals(pattern_data)

        assert result["signal"] == "bullish"
        assert result["bullish_patterns"] == 6  # 2 candlestick + 2*2 chart
        assert result["confidence"] > 0.5

    def test_aggregate_pattern_signals_none(self, engine):
        """Test pattern aggregation with no patterns."""
        pattern_data = {
            "candlestick_patterns": {
                "bullish_patterns": [],
                "bearish_patterns": [],
                "detected": []
            },
            "chart_patterns": {
                "patterns": []
            }
        }

        result = engine._aggregate_pattern_signals(pattern_data)
        assert result is None

    def test_calculate_overall_signal_moderate_conservative(self, engine):
        """Test overall signal with conservative risk profile."""
        tech_signal = {
            "signal": "bullish",
            "strength": 0.8,
        }
        pattern_signal = {
            "signal": "bullish",
            "confidence": 0.9,
        }
        user_profile = {
            "risk_tolerance": "conservative"
        }

        result = engine._calculate_overall_signal(tech_signal, pattern_signal, user_profile)

        assert result["signal"] in ["BUY", "HOLD"]
        assert result["risk_tolerance_applied"] == "conservative"
        assert "confidence" in result
        assert isinstance(result["confidence"], (int, float))

    def test_calculate_overall_signal_aggressive_no_confirmation(self, engine):
        """Test overall signal with aggressive profile doesn't require confirmation."""
        tech_signal = {
            "signal": "bullish",
            "strength": 0.7,
        }
        pattern_signal = {
            "signal": "bearish",
            "confidence": 0.6,
        }
        user_profile = {
            "risk_tolerance": "aggressive"
        }

        result = engine._calculate_overall_signal(tech_signal, pattern_signal, user_profile)

        # Aggressive doesn't require confirmation, so can still get BUY
        assert result["signal"] in ["BUY", "SELL", "HOLD"]
        assert result["risk_tolerance_applied"] == "aggressive"

    def test_calculate_targets_buy_signal(self, engine):
        """Test target calculation for BUY signal."""
        technical_data = {
            "last_close": 2100,
            "indicators": {"atr": 10}
        }
        sr_data = {
            "nearest_support": {"price": 2090},
            "nearest_resistance": {"price": 2120}
        }
        user_profile = {
            "risk_tolerance": "moderate"
        }

        targets = engine._calculate_targets(technical_data, sr_data, "BUY", user_profile)

        assert targets["current_price"] == 2100
        assert targets["entry"] == 2100
        assert targets["stop_loss"] < targets["entry"]
        assert targets["take_profit"] > targets["entry"]
        assert targets["stop_loss_sr"] is not None
        assert targets["take_profit_sr"] is not None

    def test_calculate_targets_sell_signal(self, engine):
        """Test target calculation for SELL signal."""
        technical_data = {
            "last_close": 2100,
            "indicators": {"atr": 10}
        }
        sr_data = {
            "nearest_support": {"price": 2080},
            "nearest_resistance": {"price": 2110}
        }
        user_profile = {
            "risk_tolerance": "conservative"
        }

        targets = engine._calculate_targets(technical_data, sr_data, "SELL", user_profile)

        assert targets["entry"] == 2100
        assert targets["stop_loss"] > targets["entry"]
        assert targets["take_profit"] < targets["entry"]

    def test_calculate_targets_atr_multipliers_by_risk(self, engine):
        """Test ATR multipliers change by risk tolerance."""
        technical_data = {
            "last_close": 2100,
            "indicators": {"atr": 10}
        }
        user_profile_conservative = {"risk_tolerance": "conservative"}
        user_profile_aggressive = {"risk_tolerance": "aggressive"}

        targets_c = engine._calculate_targets(technical_data, None, "BUY", user_profile_conservative)
        targets_a = engine._calculate_targets(technical_data, None, "BUY", user_profile_aggressive)

        # Conservative should have tighter stop loss (larger multiplier)
        sl_distance_c = abs(targets_c["stop_loss"] - targets_c["entry"])
        sl_distance_a = abs(targets_a["stop_loss"] - targets_a["entry"])

        assert sl_distance_c > sl_distance_a  # Conservative has wider stop

    def test_format_recommendation_vietnamese(self, engine):
        """Test recommendation formatting in Vietnamese."""
        result = {
            "overall_signal": {
                "signal": "BUY",
                "confidence": 75,
            },
            "targets": {
                "entry": 2100,
                "stop_loss": 2095,
                "take_profit": 2115,
            },
            "ai_summary": {
                "summary": "Bullish conditions",
                "reasoning": "Strong signals"
            }
        }
        user_profile = {"risk_tolerance": "moderate"}

        recommendation = engine._format_recommendation(result, user_profile, "vi")

        assert recommendation["action"] == "MUA"
        assert recommendation["signal"] == "BUY"
        assert recommendation["confidence"] == 75
        assert "Độ tin cậy" in recommendation["confidence_text"]
        assert recommendation["entry"] == 2100

    def test_format_recommendation_english(self, engine):
        """Test recommendation formatting in English."""
        result = {
            "overall_signal": {
                "signal": "SELL",
                "confidence": 60,
            },
            "targets": {
                "entry": 2100,
                "stop_loss": 2110,
                "take_profit": 2080,
            },
            "ai_summary": {
                "summary": "Bearish trend",
                "reasoning": "Multiple sell signals"
            }
        }
        user_profile = {"risk_tolerance": "moderate"}

        recommendation = engine._format_recommendation(result, user_profile, "en")

        assert recommendation["action"] == "SELL"
        assert "Confidence" in recommendation["confidence_text"]

    @pytest.mark.asyncio
    async def test_generate_recommendation_full_flow(self, engine, mock_ai_summarizer):
        """Test complete recommendation generation flow."""
        technical_data = {
            "last_close": 2100,
            "indicators": {"atr": 10, "rsi": 65},
            "signals": {"trend": "bullish", "macd": "bullish"}
        }
        pattern_data = {
            "candlestick_patterns": {
                "bullish_patterns": ["Hammer"],
                "bearish_patterns": [],
                "detected": [{"name": "Hammer"}]
            },
            "chart_patterns": {"patterns": []}
        }
        sr_data = {
            "nearest_support": {"price": 2095},
            "nearest_resistance": {"price": 2120}
        }
        user_profile = {
            "risk_tolerance": "moderate",
            "preferred_timeframe": "H1"
        }

        result = await engine.generate_recommendation(
            symbol="XAUUSD",
            technical_data=technical_data,
            pattern_data=pattern_data,
            sr_data=sr_data,
            user_profile=user_profile,
            language="vi"
        )

        assert result["symbol"] == "XAUUSD"
        assert "technical_signal" in result
        assert "overall_signal" in result
        assert "targets" in result
        assert "recommendation" in result
        assert "ai_summary" in result
        assert result["recommendation"]["action"] == "MUA"  # Vietnamese for BUY


# ============================================================================
# UserProfile Model Tests
# ============================================================================

class TestUserProfile:
    """Test suite for UserProfile models."""

    def test_user_profile_valid(self):
        """Test UserProfile with valid data."""
        profile = UserProfile(
            user_id="user123",
            risk_tolerance=RiskTolerance.MODERATE,
            preferred_timeframes=["H1", "H4"],
            watchlist=["XAUUSD", "EURUSD"]
        )

        assert profile.user_id == "user123"
        assert profile.risk_tolerance == RiskTolerance.MODERATE
        assert len(profile.preferred_timeframes) == 2
        assert profile.language == "vi"  # Default
        assert profile.max_position_risk == 0.02  # Default

    def test_user_profile_risk_tolerance_enum(self):
        """Test RiskTolerance enum values."""
        assert RiskTolerance.CONSERVATIVE == "conservative"
        assert RiskTolerance.MODERATE == "moderate"
        assert RiskTolerance.AGGRESSIVE == "aggressive"

    def test_user_profile_field_validation(self):
        """Test UserProfile field constraints."""
        # Test max_position_risk bounds
        with pytest.raises(ValueError):
            UserProfile(
                user_id="user123",
                max_position_risk=0.15  # Too high
            )

        with pytest.raises(ValueError):
            UserProfile(
                user_id="user123",
                max_position_risk=0.001  # Too low
            )

    def test_user_profile_language_pattern(self):
        """Test language field pattern validation."""
        with pytest.raises(ValueError):
            UserProfile(
                user_id="user123",
                language="fr"  # Invalid
            )

        # Valid
        profile_en = UserProfile(user_id="user123", language="en")
        assert profile_en.language == "en"

    def test_user_profile_update_model(self):
        """Test UserProfileUpdate model."""
        update = UserProfileUpdate(
            risk_tolerance=RiskTolerance.AGGRESSIVE,
            language="en"
        )

        assert update.risk_tolerance == RiskTolerance.AGGRESSIVE
        assert update.language == "en"
        assert update.preferred_timeframes is None

    def test_recommendation_request_model(self):
        """Test RecommendationRequest model."""
        request = RecommendationRequest(
            symbol="XAUUSD",
            timeframe="H1",
            language="vi",
            include_ai_summary=True
        )

        assert request.symbol == "XAUUSD"
        assert request.timeframe == "H1"
        assert request.include_ai_summary == True

    def test_recommendation_request_validation(self):
        """Test RecommendationRequest validation."""
        # Symbol too long
        with pytest.raises(ValueError):
            RecommendationRequest(symbol="A" * 21)

        # Invalid language
        with pytest.raises(ValueError):
            RecommendationRequest(symbol="XAUUSD", language="fr")

    def test_recommendation_response_model(self):
        """Test RecommendationResponse model."""
        response = RecommendationResponse(
            symbol="XAUUSD",
            overall_signal={"signal": "BUY", "confidence": 75},
            targets={"entry": 2100, "stop_loss": 2095},
            recommendation={"action": "MUA", "signal": "BUY"}
        )

        assert response.symbol == "XAUUSD"
        assert response.overall_signal["signal"] == "BUY"
        assert response.success == True  # Default


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase04Integration:
    """Integration tests for Phase 04 AI Recommendations."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock._client = AsyncMock()
        return redis_mock

    @pytest.fixture
    def components(self, mock_redis):
        """Create all Phase 04 components."""
        summarizer = AISummarizer(
            anthropic_api_key="test_key",
            deepseek_api_key="test_key",
            default_model="claude",
            redis_client=mock_redis
        )
        engine = RecommendationEngine(summarizer)
        return {
            "summarizer": summarizer,
            "engine": engine,
            "redis": mock_redis
        }

    @pytest.mark.asyncio
    async def test_full_recommendation_flow_with_mocks(self, components):
        """Test full recommendation flow with mocked external dependencies."""
        engine = components["engine"]
        summarizer = components["summarizer"]

        # Mock cache miss
        components["redis"]._client.get = AsyncMock(return_value=None)

        # Mock LLM call
        with patch.object(summarizer, '_call_claude', new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = json.dumps({
                "summary": "Strong bullish momentum",
                "signal": "BUY",
                "confidence": 80,
                "reasoning": "Multiple bullish indicators aligned"
            })

            # Generate recommendation
            result = await engine.generate_recommendation(
                symbol="XAUUSD",
                technical_data={
                    "last_close": 2100,
                    "indicators": {"atr": 10, "rsi": 65},
                    "signals": {"trend": "bullish", "macd": "bullish"}
                },
                pattern_data={
                    "candlestick_patterns": {
                        "bullish_patterns": ["Hammer"],
                        "bearish_patterns": [],
                        "detected": [{"name": "Hammer"}]
                    },
                    "chart_patterns": {"patterns": []}
                },
                sr_data={
                    "nearest_support": {"price": 2095},
                    "nearest_resistance": {"price": 2120}
                },
                user_profile={
                    "risk_tolerance": "moderate",
                    "preferred_timeframe": "H1"
                },
                language="vi"
            )

            # Verify complete flow
            assert result["symbol"] == "XAUUSD"
            assert result["technical_signal"]["signal"] == "bullish"
            assert result["overall_signal"]["signal"] == "BUY"
            assert result["targets"]["entry"] == 2100
            assert result["ai_summary"]["confidence"] == 80
            assert result["recommendation"]["action"] == "MUA"

    @pytest.mark.asyncio
    async def test_recommendation_with_cache_hit(self, components):
        """Test recommendation uses cached AI summary."""
        engine = components["engine"]

        # Mock cache hit
        cached_summary = {
            "summary": "Cached result",
            "signal": "HOLD",
            "confidence": 50,
            "reasoning": "From cache"
        }
        components["redis"]._client.get = AsyncMock(
            return_value=json.dumps(cached_summary)
        )

        result = await engine.generate_recommendation(
            symbol="XAUUSD",
            technical_data={
                "last_close": 2100,
                "indicators": {"atr": 10, "rsi": 50},
                "signals": {"trend": "neutral"}
            },
            user_profile={"risk_tolerance": "moderate"},
            language="vi"
        )

        # Should use cached summary
        assert result["ai_summary"]["cached"] == True
        assert result["ai_summary"]["summary"] == "Cached result"

    @pytest.mark.asyncio
    async def test_recommendation_error_resilience(self, components):
        """Test recommendation continues despite AI summary errors."""
        engine = components["engine"]
        summarizer = components["summarizer"]

        # Mock AI summary error
        with patch.object(summarizer, '_call_claude', side_effect=RuntimeError("API Error")):
            result = await engine.generate_recommendation(
                symbol="XAUUSD",
                technical_data={
                    "last_close": 2100,
                    "indicators": {"atr": 10, "rsi": 65},
                    "signals": {"trend": "bullish"}
                },
                user_profile={"risk_tolerance": "moderate"},
                language="vi"
            )

            # Should still have recommendation even if AI fails
            assert "overall_signal" in result
            assert "targets" in result
            assert "recommendation" in result
            # AI summary will have error
            assert "error" in result["ai_summary"]

    def test_risk_profiles_consistency(self):
        """Test risk profile consistency across components."""
        # Create profiles
        conservative = UserProfile(
            user_id="c1",
            risk_tolerance=RiskTolerance.CONSERVATIVE
        )
        moderate = UserProfile(
            user_id="m1",
            risk_tolerance=RiskTolerance.MODERATE
        )
        aggressive = UserProfile(
            user_id="a1",
            risk_tolerance=RiskTolerance.AGGRESSIVE
        )

        # All should be valid
        assert conservative.risk_tolerance == RiskTolerance.CONSERVATIVE
        assert moderate.risk_tolerance == RiskTolerance.MODERATE
        assert aggressive.risk_tolerance == RiskTolerance.AGGRESSIVE

    def test_signal_strength_enum(self):
        """Test SignalStrength enum values."""
        assert SignalStrength.STRONG_BUY.value == "strong_buy"
        assert SignalStrength.BUY.value == "buy"
        assert SignalStrength.HOLD.value == "hold"
        assert SignalStrength.SELL.value == "sell"
        assert SignalStrength.STRONG_SELL.value == "strong_sell"


# ============================================================================
# Async Test Execution
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
