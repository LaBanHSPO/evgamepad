"""
Unit tests for portfolio analysis feature.
"""
import pytest
from datetime import datetime
from app.models.advisor_models import PositionInput, PortfolioAnalysisRequest
from app.processors.advisor_processor import AdvisorProcessor

@pytest.fixture
def sample_positions():
    """Sample positions for testing."""
    return [
        PositionInput(
            symbol="XAUUSD",
            entry_price=2100.50,
            current_price=2095.00,
            position_size=0.5,
            stop_loss=2090.00,
            timeframe="H1"
        ),
        PositionInput(
            symbol="EURUSD",
            entry_price=1.0850,
            current_price=1.0870,
            position_size=1.0,
            stop_loss=1.0830,
            timeframe="H1"
        )
    ]

class TestPortfolioAnalysisModels:
    """Test Pydantic models for portfolio analysis."""

    def test_position_input_validation(self):
        """Test PositionInput model validation."""
        # Valid position
        pos = PositionInput(
            symbol="XAUUSD",
            entry_price=2100.50,
            position_size=0.5
        )
        assert pos.symbol == "XAUUSD"
        assert pos.entry_price == 2100.50
        assert pos.position_size == 0.5
        assert pos.timeframe == "H1"  # Default

        # Invalid position (negative price)
        with pytest.raises(ValueError):
            PositionInput(
                symbol="XAUUSD",
                entry_price=-100,
                position_size=0.5
            )

    def test_portfolio_analysis_request_validation(self):
        """Test PortfolioAnalysisRequest validation."""
        positions = [
            PositionInput(symbol="XAUUSD", entry_price=2100, position_size=0.5)
        ]

        # Valid request
        req = PortfolioAnalysisRequest(
            positions=positions,
            account_balance=10000,
            risk_profile="conservative"
        )
        assert len(req.positions) == 1
        assert req.account_balance == 10000
        assert req.risk_profile == "conservative"
        assert req.language == "vi"  # Default

        # Invalid request (too many positions)
        with pytest.raises(ValueError):
            PortfolioAnalysisRequest(
                positions=[positions[0]] * 11,  # Max 10
                account_balance=10000
            )

        # Invalid request (invalid risk profile)
        with pytest.raises(ValueError):
            PortfolioAnalysisRequest(
                positions=positions,
                account_balance=10000,
                risk_profile="invalid"
            )

class TestAdvisorProcessor:
    """Test AdvisorProcessor portfolio methods."""

    @pytest.mark.asyncio
    async def test_calculate_portfolio_health(self, sample_positions):
        """Test portfolio health calculation."""
        processor = AdvisorProcessor(mt5_manager=None, redis_client=None)

        # Mock position results
        position_results = [
            {
                "symbol": "XAUUSD",
                "entry_price": 2100.50,
                "current_price": 2095.00,
                "position_size": 0.5,
                "stop_loss": 2090.00,
                "pnl_pct": -0.26,
                "risk_status": "approaching_stop",
            },
            {
                "symbol": "EURUSD",
                "entry_price": 1.0850,
                "current_price": 1.0870,
                "position_size": 1.0,
                "stop_loss": 1.0830,
                "pnl_pct": 0.18,
                "risk_status": "safe",
            }
        ]

        health = processor._calculate_portfolio_health(position_results, 10000)

        assert 0 <= health["score"] <= 100
        assert health["status"] in ["HEALTHY", "CAUTION", "DANGER"]
        assert health["total_risk_exposure"] >= 0
        assert health["current_drawdown"] >= 0
        assert health["positions_at_risk"] == 1  # One approaching stop

    def test_generate_portfolio_cache_key(self):
        """Test portfolio cache key generation."""
        processor = AdvisorProcessor(mt5_manager=None, redis_client=None)

        positions = [
            PositionInput(symbol="XAUUSD", entry_price=2100, position_size=0.5)
        ]

        key1 = processor._generate_portfolio_cache_key(positions, 10000, "conservative")
        key2 = processor._generate_portfolio_cache_key(positions, 10000, "conservative")

        # Same input should generate same key
        assert key1 == key2
        assert key1.startswith("portfolio_analysis:")

        # Different risk profile should generate different key
        key3 = processor._generate_portfolio_cache_key(positions, 10000, "aggressive")
        assert key1 != key3

@pytest.mark.asyncio
class TestPortfolioAnalysisIntegration:
    """Integration tests for portfolio analysis."""

    async def test_portfolio_analysis_event_validation(self):
        """Test event handler input validation."""
        # This would require Socket.IO client setup
        # Placeholder for integration test
        pass

    async def test_portfolio_analysis_cache_hit(self):
        """Test portfolio analysis cache hit."""
        # This would require Redis setup
        # Placeholder for cache test
        pass

    async def test_llm_portfolio_advice_fallback(self):
        """Test LLM fallback when API fails."""
        # This would test AI summarizer fallback logic
        # Placeholder for LLM test
        pass

# Run tests with: pytest backend/tests/test_portfolio_analysis.py -v
