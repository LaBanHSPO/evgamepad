"""
Unit tests for AISummarizer LLM provider fallback functionality.
Tests provider availability checking, fallback chain building, and graceful degradation.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.advisor.ai_summarizer import AISummarizer


class TestProviderAvailability:
    """Test provider availability detection."""

    def test_check_available_providers_all_configured(self):
        """Test when all providers have API keys."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="sk-xxx",
            zai_api_key="sk-zai-xxx"
        )
        assert set(summarizer.available_providers) == {"claude", "deepseek", "zai"}

    def test_check_available_providers_only_zai(self):
        """Test when only ZAI is configured."""
        summarizer = AISummarizer(
            anthropic_api_key="",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx"
        )
        assert summarizer.available_providers == ["zai"]

    def test_check_available_providers_only_claude(self):
        """Test when only Claude is configured."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="",
            zai_api_key=""
        )
        assert summarizer.available_providers == ["claude"]

    def test_check_available_providers_claude_and_zai(self):
        """Test when Claude and ZAI are configured."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx"
        )
        assert set(summarizer.available_providers) == {"claude", "zai"}

    def test_check_available_providers_none_configured(self):
        """Test when no providers are configured."""
        summarizer = AISummarizer(
            anthropic_api_key="",
            deepseek_api_key="",
            zai_api_key=""
        )
        assert summarizer.available_providers == []


class TestFallbackChain:
    """Test fallback chain building logic."""

    def test_build_fallback_chain_claude_primary_with_zai(self):
        """Test fallback chain when Claude is primary and ZAI is available."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx",
            default_model="claude"
        )
        chain = summarizer._build_fallback_chain("claude")
        assert chain == ["claude", "zai"]

    def test_build_fallback_chain_deepseek_primary_with_zai(self):
        """Test fallback chain when DeepSeek is primary and ZAI is available."""
        summarizer = AISummarizer(
            anthropic_api_key="",
            deepseek_api_key="sk-xxx",
            zai_api_key="sk-zai-xxx",
            default_model="deepseek"
        )
        chain = summarizer._build_fallback_chain("deepseek")
        assert chain == ["deepseek", "zai"]

    def test_build_fallback_chain_zai_primary(self):
        """Test fallback chain when ZAI is primary."""
        summarizer = AISummarizer(
            anthropic_api_key="",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx",
            default_model="zai"
        )
        chain = summarizer._build_fallback_chain("zai")
        assert chain == ["zai"]

    def test_build_fallback_chain_no_primary_zai_fallback(self):
        """Test ZAI fallback when primary unavailable."""
        summarizer = AISummarizer(
            anthropic_api_key="",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx",
            default_model="claude"
        )
        chain = summarizer._build_fallback_chain("claude")
        assert chain == ["zai"]

    def test_build_fallback_chain_all_providers(self):
        """Test fallback chain with all providers available."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="sk-xxx",
            zai_api_key="sk-zai-xxx",
            default_model="claude"
        )
        chain = summarizer._build_fallback_chain("claude")
        # Claude first, ZAI second, then DeepSeek
        assert chain[0] == "claude"
        assert chain[1] == "zai"
        assert "deepseek" in chain

    def test_build_fallback_chain_no_providers(self):
        """Test fallback chain when no providers available."""
        summarizer = AISummarizer(
            anthropic_api_key="",
            deepseek_api_key="",
            zai_api_key="",
            default_model="claude"
        )
        chain = summarizer._build_fallback_chain("claude")
        assert chain == []


class TestGenerateSummaryFallback:
    """Test generate_summary() with fallback logic."""

    @pytest.mark.asyncio
    async def test_generate_summary_claude_success(self):
        """Test successful generation with Claude."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="",
            zai_api_key="",
            default_model="claude"
        )

        # Mock the Claude API call
        with patch.object(summarizer, '_call_anthropic', new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = '{"summary": "Test", "signal": "BUY", "confidence": 75, "reasoning": "Test reasoning"}'

            result = await summarizer.generate_summary(
                {"symbol": "XAUUSD", "timeframe": "H1", "price": 2650},
                use_cache=False
            )

            assert result["model"] == "claude"
            assert result["signal"] == "BUY"
            assert result["confidence"] == 75
            mock_claude.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_summary_fallback_to_zai(self):
        """Test fallback from Claude to ZAI on error."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx",
            default_model="claude"
        )

        # Mock Claude to fail, ZAI to succeed
        with patch.object(summarizer, '_call_anthropic', new_callable=AsyncMock) as mock_claude, \
             patch.object(summarizer, '_call_zai', new_callable=AsyncMock) as mock_zai:

            mock_claude.side_effect = Exception("Claude API error")
            mock_zai.return_value = '{"summary": "Test from ZAI", "signal": "SELL", "confidence": 80, "reasoning": "ZAI analysis"}'

            result = await summarizer.generate_summary(
                {"symbol": "XAUUSD", "timeframe": "H1", "price": 2650},
                use_cache=False
            )

            assert result["model"] == "zai"
            assert result["signal"] == "SELL"
            assert result["confidence"] == 80
            mock_claude.assert_called_once()
            mock_zai.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_summary_all_providers_fail(self):
        """Test error response when all providers fail."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx",
            default_model="claude"
        )

        # Mock both to fail
        with patch.object(summarizer, '_call_anthropic', new_callable=AsyncMock) as mock_claude, \
             patch.object(summarizer, '_call_zai', new_callable=AsyncMock) as mock_zai:

            mock_claude.side_effect = Exception("Claude API error")
            mock_zai.side_effect = Exception("ZAI API error")

            result = await summarizer.generate_summary(
                {"symbol": "XAUUSD", "timeframe": "H1", "price": 2650},
                use_cache=False
            )

            assert result["model"] == "fallback"
            assert result["signal"] == "HOLD"
            assert result["confidence"] == 0
            assert "providers_tried" in result
            assert result["providers_tried"] == ["claude", "zai"]


class TestGeneratePortfolioAdviceFallback:
    """Test generate_portfolio_advice() with fallback logic."""

    @pytest.mark.asyncio
    async def test_portfolio_advice_fallback_to_zai(self):
        """Test fallback from Claude to ZAI for portfolio advice."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx",
            default_model="claude"
        )

        positions = [{
            "symbol": "XAUUSD",
            "entry_price": 2650,
            "current_price": 2660,
            "pnl_pct": 0.38,
            "r_multiple": 1.5,
            "risk_status": "safe",
            "technical_signal": "bullish"
        }]

        portfolio_health = {
            "total_risk_exposure": 2.5,
            "current_drawdown": 0,
            "score": 85,
            "status": "HEALTHY"
        }

        # Mock Claude to fail, ZAI to succeed
        with patch.object(summarizer, '_call_anthropic', new_callable=AsyncMock) as mock_claude, \
             patch.object(summarizer, '_call_zai', new_callable=AsyncMock) as mock_zai:

            mock_claude.side_effect = Exception("Claude API error")
            mock_zai.return_value = '{"summary": "Portfolio healthy", "overall_risk": "LOW", "priority_actions": [], "reasoning": "Good position", "confidence": 85}'

            result = await summarizer.generate_portfolio_advice(
                positions=positions,
                portfolio_health=portfolio_health,
                account_balance=10000,
                risk_profile="conservative",
                language="en",
                use_cache=False
            )

            assert result["model"] == "zai"
            assert result["overall_risk"] == "LOW"
            mock_claude.assert_called_once()
            mock_zai.assert_called_once()

    @pytest.mark.asyncio
    async def test_portfolio_advice_all_providers_fail(self):
        """Test error response when all providers fail for portfolio advice."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx",
            default_model="claude"
        )

        positions = [{
            "symbol": "XAUUSD",
            "entry_price": 2650,
            "current_price": 2660,
            "pnl_pct": 0.38,
            "r_multiple": 1.5,
            "risk_status": "safe",
            "technical_signal": "bullish"
        }]

        portfolio_health = {
            "total_risk_exposure": 2.5,
            "current_drawdown": 0,
            "score": 85,
            "status": "HEALTHY"
        }

        # Mock both to fail
        with patch.object(summarizer, '_call_anthropic', new_callable=AsyncMock) as mock_claude, \
             patch.object(summarizer, '_call_zai', new_callable=AsyncMock) as mock_zai:

            mock_claude.side_effect = Exception("Claude API error")
            mock_zai.side_effect = Exception("ZAI API error")

            result = await summarizer.generate_portfolio_advice(
                positions=positions,
                portfolio_health=portfolio_health,
                account_balance=10000,
                risk_profile="conservative",
                language="en",
                use_cache=False
            )

            assert result["model"] == "fallback"
            assert result["overall_risk"] == "MODERATE"
            assert "providers_tried" in result
