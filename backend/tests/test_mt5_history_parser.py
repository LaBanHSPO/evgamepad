"""
Tests for MT5 history parser (Phase 5.2).
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from app.advisor.mt5_history_parser import MT5HistoryParser


@pytest.fixture
def mock_mt5_manager():
    """Mock MT5 connection manager."""
    return MagicMock()


@pytest.fixture
def mock_accuracy_tracker():
    """Mock accuracy tracker."""
    tracker = AsyncMock()
    tracker.record_outcome.return_value = uuid4()
    return tracker


@pytest.fixture
def mock_db_pool():
    """Mock database pool."""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None
    return pool, conn


@pytest.fixture
def parser(mock_mt5_manager, mock_accuracy_tracker, mock_db_pool):
    """Create MT5HistoryParser instance."""
    pool, _ = mock_db_pool
    return MT5HistoryParser(mock_mt5_manager, mock_accuracy_tracker, pool)


class TestMT5HistoryParser:
    """Test MT5 history parser."""

    @pytest.mark.asyncio
    async def test_sync_closed_positions_success(self, parser, mock_accuracy_tracker):
        """Test successful MT5 sync."""
        with patch.object(parser, '_fetch_mt5_history') as mock_fetch_mt5, \
             patch.object(parser, '_fetch_recent_recommendations') as mock_fetch_recs, \
             patch.object(parser, '_match_deals_to_recommendations') as mock_match:

            # Mock MT5 deals
            mock_fetch_mt5.return_value = [
                {
                    "deal_id": 12345,
                    "symbol": "XAUUSD",
                    "entry_price": 2634.50,
                    "exit_price": 2640.20,
                    "entry_at": datetime.utcnow(),
                    "exit_at": datetime.utcnow()
                }
            ]

            # Mock recommendations
            mock_fetch_recs.return_value = [
                {
                    "id": uuid4(),
                    "symbol": "XAUUSD",
                    "timeframe": "H1",
                    "signal": "BUY",
                    "confidence": 85,
                    "entry_price": 2634.50
                }
            ]

            # Mock matches
            mock_match.return_value = [
                {
                    "deal_id": 12345,
                    "recommendation_id": uuid4(),
                    "symbol": "XAUUSD",
                    "timeframe": "H1",
                    "signal": "BUY",
                    "confidence": 85,
                    "entry_price": 2634.50,
                    "exit_price": 2640.20,
                    "exit_reason": "take_profit",
                    "entry_at": datetime.utcnow(),
                    "exit_at": datetime.utcnow()
                }
            ]

            result = await parser.sync_closed_positions(days_back=7)

            assert result["total_deals_fetched"] == 1
            assert result["matched"] == 1
            assert result["new_outcomes"] == 1
            assert mock_accuracy_tracker.record_outcome.called

    @pytest.mark.asyncio
    async def test_fetch_recent_recommendations(self, parser, mock_db_pool):
        """Test fetching recommendations from database."""
        _, conn = mock_db_pool
        rec_id = uuid4()

        conn.fetch.return_value = [
            {
                "id": rec_id,
                "symbol": "XAUUSD",
                "timeframe": "H1",
                "signal": "BUY",
                "confidence": 85,
                "entry_price": 2634.50,
                "stop_loss": 2625.00,
                "take_profit": 2645.00,
                "created_at": datetime.utcnow()
            }
        ]

        recs = await parser._fetch_recent_recommendations(days_back=7)

        assert len(recs) == 1
        assert recs[0]["id"] == rec_id
        assert recs[0]["symbol"] == "XAUUSD"

    def test_calculate_match_score_perfect(self, parser):
        """Test match score calculation for perfect match."""
        deal = {
            "symbol": "XAUUSD",
            "entry_price": 2634.50,
            "entry_at": datetime.utcnow()
        }

        rec = {
            "symbol": "XAUUSD",
            "entry_price": 2634.50,
            "created_at": datetime.utcnow()
        }

        score = parser._calculate_match_score(deal, rec)

        # Perfect match: 0.4 (symbol) + 0.4 (price) + 0.2 (time) = 1.0
        assert score == 1.0

    def test_calculate_match_score_symbol_mismatch(self, parser):
        """Test match score with different symbols."""
        deal = {"symbol": "EURUSD", "entry_price": 1.1000, "entry_at": datetime.utcnow()}
        rec = {"symbol": "XAUUSD", "entry_price": 1.1000, "created_at": datetime.utcnow()}

        score = parser._calculate_match_score(deal, rec)

        assert score == 0.0  # Different symbols = no match

    def test_calculate_match_score_price_tolerance(self, parser):
        """Test match score with price within tolerance."""
        deal = {"symbol": "XAUUSD", "entry_price": 2634.50, "entry_at": datetime.utcnow()}
        rec = {
            "symbol": "XAUUSD",
            "entry_price": 2634.76,  # 0.01% difference
            "created_at": datetime.utcnow()
        }

        score = parser._calculate_match_score(deal, rec)

        # Should get full price score (within 0.1% tolerance)
        assert score >= 0.8  # Symbol + Price + Time

    def test_determine_exit_reason_take_profit(self, parser):
        """Test exit reason detection for take profit."""
        deal = {"exit_price": 2645.00, "comment": ""}
        rec = {"take_profit": 2645.00, "stop_loss": 2625.00}

        reason = parser._determine_exit_reason(deal, rec)

        assert reason == "take_profit"

    def test_determine_exit_reason_stop_loss(self, parser):
        """Test exit reason detection for stop loss."""
        deal = {"exit_price": 2625.00, "comment": ""}
        rec = {"take_profit": 2645.00, "stop_loss": 2625.00}

        reason = parser._determine_exit_reason(deal, rec)

        assert reason == "stop_loss"

    def test_determine_exit_reason_manual(self, parser):
        """Test exit reason detection for manual close."""
        deal = {"exit_price": 2635.00, "comment": "manual close by user"}
        rec = {"take_profit": 2645.00, "stop_loss": 2625.00}

        reason = parser._determine_exit_reason(deal, rec)

        assert reason == "manual"

    def test_match_deals_to_recommendations(self, parser):
        """Test deal-to-recommendation matching logic."""
        deals = [
            {
                "deal_id": 1,
                "symbol": "XAUUSD",
                "entry_price": 2634.50,
                "exit_price": 2640.20,
                "entry_at": datetime.utcnow(),
                "exit_at": datetime.utcnow()
            }
        ]

        recs = [
            {
                "id": uuid4(),
                "symbol": "XAUUSD",
                "timeframe": "H1",
                "signal": "BUY",
                "confidence": 85,
                "entry_price": 2634.50,
                "stop_loss": 2625.00,
                "take_profit": 2645.00,
                "created_at": datetime.utcnow()
            }
        ]

        matches = parser._match_deals_to_recommendations(deals, recs)

        assert len(matches) == 1
        assert matches[0]["symbol"] == "XAUUSD"
        assert matches[0]["deal_id"] == 1

    def test_match_deals_minimum_score_threshold(self, parser):
        """Test that matches below 80% threshold are rejected."""
        deals = [
            {
                "deal_id": 1,
                "symbol": "XAUUSD",
                "entry_price": 2634.50,
                "entry_at": datetime.utcnow()
            }
        ]

        recs = [
            {
                "id": uuid4(),
                "symbol": "XAUUSD",
                "timeframe": "H1",
                "signal": "BUY",
                "confidence": 85,
                "entry_price": 2700.00,  # Very different price
                "created_at": datetime.utcnow() - timedelta(hours=5)  # Old timestamp
            }
        ]

        matches = parser._match_deals_to_recommendations(deals, recs)

        assert len(matches) == 0  # Should not match due to low score
