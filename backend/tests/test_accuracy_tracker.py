"""
Tests for accuracy tracking system (Phase 5.2).
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch
from app.advisor.accuracy_tracker import AccuracyTracker


@pytest.fixture
def mock_db_pool():
    """Mock asyncpg connection pool."""
    pool = AsyncMock()
    conn = AsyncMock()

    # Mock connection context manager
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    return pool, conn


@pytest.fixture
def tracker(mock_db_pool):
    """Create AccuracyTracker instance with mocked pool."""
    pool, _ = mock_db_pool
    return AccuracyTracker(pool)


class TestAccuracyTracker:
    """Test accuracy tracking system."""

    @pytest.mark.asyncio
    async def test_record_winning_trade(self, tracker, mock_db_pool):
        """Test recording winning BUY trade."""
        _, conn = mock_db_pool
        outcome_id = uuid4()
        conn.fetchval.return_value = outcome_id
        conn.execute.return_value = None

        result = await tracker.record_outcome(
            symbol="XAUUSD",
            timeframe="H1",
            signal="BUY",
            confidence=85,
            entry_price=2634.50,
            exit_price=2640.20,
            exit_reason="take_profit"
        )

        assert result == outcome_id
        assert conn.fetchval.called
        assert conn.execute.called  # Materialized view refresh

    @pytest.mark.asyncio
    async def test_record_losing_trade(self, tracker, mock_db_pool):
        """Test recording losing SELL trade."""
        _, conn = mock_db_pool
        outcome_id = uuid4()
        conn.fetchval.return_value = outcome_id
        conn.execute.return_value = None

        result = await tracker.record_outcome(
            symbol="EURUSD",
            timeframe="H4",
            signal="SELL",
            confidence=70,
            entry_price=1.1050,
            exit_price=1.1075,  # Loss for SELL
            exit_reason="stop_loss"
        )

        assert result == outcome_id
        # Verify P/L calculation is correct (negative for loss)
        call_args = conn.fetchval.call_args[0]
        pnl_pct = call_args[12]  # pnl_pct is 13th param
        assert pnl_pct < 0  # Should be negative for loss

    @pytest.mark.asyncio
    async def test_record_break_even_trade(self, tracker, mock_db_pool):
        """Test recording break-even trade (within 0.1%)."""
        _, conn = mock_db_pool
        outcome_id = uuid4()
        conn.fetchval.return_value = outcome_id
        conn.execute.return_value = None

        result = await tracker.record_outcome(
            symbol="GBPUSD",
            timeframe="M15",
            signal="BUY",
            confidence=50,
            entry_price=1.2500,
            exit_price=1.2501,  # 0.008% gain = break even
            exit_reason="manual"
        )

        assert result == outcome_id
        call_args = conn.fetchval.call_args[0]
        outcome = call_args[10]  # outcome is 11th param
        assert outcome == "break_even"

    @pytest.mark.asyncio
    async def test_accuracy_report_no_data(self, tracker, mock_db_pool):
        """Test accuracy report with no trades."""
        _, conn = mock_db_pool
        conn.fetchrow.return_value = {"total_trades": 0}

        report = await tracker.get_accuracy_report(
            symbol="XAUUSD",
            timeframe="H1",
            days=7
        )

        assert report["total_trades"] == 0
        assert "message" in report
        assert "No trades recorded" in report["message"]

    @pytest.mark.asyncio
    async def test_accuracy_report_with_data(self, tracker, mock_db_pool):
        """Test accuracy report with trade data."""
        _, conn = mock_db_pool

        # Mock data: 10 trades, 7 wins, 3 losses
        conn.fetchrow.return_value = {
            "total_trades": 10,
            "wins": 7,
            "losses": 3,
            "break_evens": 0,
            "win_rate_pct": 70.0,
            "avg_pnl_pct": 2.5,
            "avg_win_pct": 4.2,
            "avg_loss_pct": 1.8,
            "profit_factor": 2.33,
            "best_trade_pct": 8.5,
            "worst_trade_pct": -3.2,
            "avg_hold_hours": 4.5
        }

        report = await tracker.get_accuracy_report(
            symbol="XAUUSD",
            timeframe="H1",
            days=30
        )

        assert report["total_trades"] == 10
        assert report["wins"] == 7
        assert report["losses"] == 3
        assert report["win_rate_pct"] == 70.0
        assert report["profit_factor"] == 2.33
        assert report["recommendation"] == "Excellent - High confidence trades"

    @pytest.mark.asyncio
    async def test_best_performing_configs(self, tracker, mock_db_pool):
        """Test fetching best-performing configurations."""
        _, conn = mock_db_pool

        conn.fetch.return_value = [
            {
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "signal": "BUY",
                "total_trades": 25,
                "win_rate_pct": 76.0,
                "avg_pnl_pct": 3.2,
                "profit_factor": 2.8
            },
            {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "signal": "SELL",
                "total_trades": 18,
                "win_rate_pct": 72.0,
                "avg_pnl_pct": 2.1,
                "profit_factor": 2.1
            }
        ]

        configs = await tracker.get_best_performing_configs(
            min_trades=10,
            days=30
        )

        assert len(configs) == 2
        assert configs[0]["symbol"] == "XAUUSD"
        assert configs[0]["win_rate_pct"] == 76.0
        assert configs[1]["symbol"] == "EURUSD"

    @pytest.mark.asyncio
    async def test_refresh_accuracy_view(self, tracker, mock_db_pool):
        """Test materialized view refresh."""
        _, conn = mock_db_pool
        conn.execute.return_value = None

        await tracker.refresh_accuracy_view()

        conn.execute.assert_called_once_with(
            "REFRESH MATERIALIZED VIEW recommendation_accuracy"
        )

    def test_generate_recommendation_excellent(self, tracker):
        """Test recommendation generation for excellent performance."""
        stats = {"win_rate_pct": 75.0, "profit_factor": 2.5}
        rec = tracker._generate_recommendation(stats)
        assert rec == "Excellent - High confidence trades"

    def test_generate_recommendation_good(self, tracker):
        """Test recommendation generation for good performance."""
        stats = {"win_rate_pct": 65.0, "profit_factor": 1.8}
        rec = tracker._generate_recommendation(stats)
        assert rec == "Good - Reliable performance"

    def test_generate_recommendation_acceptable(self, tracker):
        """Test recommendation generation for acceptable performance."""
        stats = {"win_rate_pct": 55.0, "profit_factor": 1.2}
        rec = tracker._generate_recommendation(stats)
        assert rec == "Acceptable - Use with caution"

    def test_generate_recommendation_poor(self, tracker):
        """Test recommendation generation for poor performance."""
        stats = {"win_rate_pct": 40.0, "profit_factor": 0.8}
        rec = tracker._generate_recommendation(stats)
        assert rec == "Avoid - Poor historical performance"

    @pytest.mark.asyncio
    async def test_record_outcome_with_timestamps(self, tracker, mock_db_pool):
        """Test recording outcome with custom timestamps."""
        _, conn = mock_db_pool
        outcome_id = uuid4()
        conn.fetchval.return_value = outcome_id
        conn.execute.return_value = None

        entry_at = datetime(2025, 12, 30, 10, 0, 0)
        exit_at = datetime(2025, 12, 30, 14, 30, 0)

        result = await tracker.record_outcome(
            symbol="XAUUSD",
            timeframe="H1",
            signal="BUY",
            confidence=85,
            entry_price=2634.50,
            exit_price=2640.20,
            entry_at=entry_at,
            exit_at=exit_at
        )

        assert result == outcome_id
        call_args = conn.fetchval.call_args[0]

        # Verify timestamps were passed correctly
        assert call_args[17] == entry_at
        assert call_args[18] == exit_at

        # Verify held_duration calculation
        held_duration = call_args[13]
        assert held_duration == (exit_at - entry_at)

    @pytest.mark.asyncio
    async def test_record_outcome_with_optional_params(self, tracker, mock_db_pool):
        """Test recording outcome with all optional parameters."""
        _, conn = mock_db_pool
        outcome_id = uuid4()
        rec_id = uuid4()
        user_id = uuid4()

        conn.fetchval.return_value = outcome_id
        conn.execute.return_value = None

        provenance = {
            "data_sources": ["MT5", "TwelveData"],
            "cache_hits": 2
        }

        result = await tracker.record_outcome(
            symbol="XAUUSD",
            timeframe="H1",
            signal="BUY",
            confidence=85,
            entry_price=2634.50,
            exit_price=2640.20,
            stop_loss=2625.00,
            take_profit=2645.00,
            exit_reason="take_profit",
            provenance=provenance,
            recommendation_id=rec_id,
            user_id=user_id
        )

        assert result == outcome_id
        call_args = conn.fetchval.call_args[0]

        # Verify all params were passed
        assert call_args[0] == rec_id  # recommendation_id
        assert call_args[1] == user_id  # user_id
        assert call_args[8] == 2625.00  # stop_loss
        assert call_args[9] == 2645.00  # take_profit
        assert call_args[16] == provenance  # provenance

    @pytest.mark.asyncio
    async def test_pnl_calculation_buy_signal(self, tracker, mock_db_pool):
        """Test P/L calculation for BUY signal."""
        _, conn = mock_db_pool
        conn.fetchval.return_value = uuid4()
        conn.execute.return_value = None

        await tracker.record_outcome(
            symbol="XAUUSD",
            timeframe="H1",
            signal="BUY",
            confidence=85,
            entry_price=2000.00,
            exit_price=2050.00  # +50 / 2000 = 2.5%
        )

        call_args = conn.fetchval.call_args[0]
        pnl_pct = call_args[12]

        assert abs(pnl_pct - 2.5) < 0.01  # 2.5% profit

    @pytest.mark.asyncio
    async def test_pnl_calculation_sell_signal(self, tracker, mock_db_pool):
        """Test P/L calculation for SELL signal."""
        _, conn = mock_db_pool
        conn.fetchval.return_value = uuid4()
        conn.execute.return_value = None

        await tracker.record_outcome(
            symbol="EURUSD",
            timeframe="H1",
            signal="SELL",
            confidence=75,
            entry_price=1.1000,
            exit_price=1.0950  # Entry - Exit = +50 pips
        )

        call_args = conn.fetchval.call_args[0]
        pnl_pct = call_args[12]

        # For SELL: (entry - exit) / entry = (1.1000 - 1.0950) / 1.1000 = ~0.45%
        assert pnl_pct > 0  # Should be positive profit
        assert abs(pnl_pct - 0.45) < 0.01

    @pytest.mark.asyncio
    async def test_matched_prediction_buy(self, tracker, mock_db_pool):
        """Test matched_prediction for BUY signal."""
        _, conn = mock_db_pool
        conn.fetchval.return_value = uuid4()
        conn.execute.return_value = None

        # Winning BUY: exit > entry
        await tracker.record_outcome(
            symbol="XAUUSD",
            timeframe="H1",
            signal="BUY",
            confidence=85,
            entry_price=2000.00,
            exit_price=2050.00
        )

        call_args = conn.fetchval.call_args[0]
        matched_prediction = call_args[14]
        assert matched_prediction is True

    @pytest.mark.asyncio
    async def test_matched_prediction_sell(self, tracker, mock_db_pool):
        """Test matched_prediction for SELL signal."""
        _, conn = mock_db_pool
        conn.fetchval.return_value = uuid4()
        conn.execute.return_value = None

        # Losing SELL: exit > entry (price went up)
        await tracker.record_outcome(
            symbol="EURUSD",
            timeframe="H1",
            signal="SELL",
            confidence=70,
            entry_price=1.1000,
            exit_price=1.1050
        )

        call_args = conn.fetchval.call_args[0]
        matched_prediction = call_args[14]
        assert matched_prediction is False  # Price moved opposite direction
