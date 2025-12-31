"""Tests for leaderboard service."""
import pytest
from decimal import Decimal
from app.services.leaderboard_service import LeaderboardService
from app.models.game_models import LeaderboardEntry
from app.database.redis_client import RedisClient
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_redis_client():
    """Create mock Redis client."""
    client = MagicMock(spec=RedisClient)
    client.zadd = AsyncMock(return_value=1)
    client.expire = AsyncMock(return_value=True)
    client.zrevrange = AsyncMock(return_value=[])
    client.zrevrank = AsyncMock(return_value=None)
    client.zscore = AsyncMock(return_value=None)
    client.zcard = AsyncMock(return_value=0)
    return client

@pytest.fixture
def leaderboard_service_with_redis(mock_redis_client):
    """Create leaderboard service with mock Redis."""
    service = LeaderboardService(redis_client=mock_redis_client)
    return service

@pytest.fixture
def leaderboard_service_no_redis():
    """Create leaderboard service without Redis."""
    service = LeaderboardService(redis_client=None)
    return service

@pytest.mark.asyncio
async def test_update_team_score_with_redis(leaderboard_service_with_redis, mock_redis_client):
    """Test team score update in Redis."""
    session_id = "test-session-1"
    team_id = "team-1"
    pnl = Decimal("1500.50")

    await leaderboard_service_with_redis.update_team_score(session_id, team_id, pnl)

    # Verify Redis update
    mock_redis_client.zadd.assert_called_once_with(f"leaderboard:{session_id}", {team_id: float(pnl)})
    mock_redis_client.expire.assert_called_once_with(f"leaderboard:{session_id}", 3600)

@pytest.mark.asyncio
async def test_update_team_score_without_redis(leaderboard_service_no_redis):
    """Test team score update without Redis (should handle gracefully)."""
    session_id = "test-session-1"
    team_id = "team-1"
    pnl = Decimal("1500.50")

    # Should not raise exception
    await leaderboard_service_no_redis.update_team_score(session_id, team_id, pnl)

@pytest.mark.asyncio
async def test_get_leaderboard_redis_cache_miss(leaderboard_service_with_redis, mock_redis_client):
    """Test leaderboard fetch when Redis returns empty."""
    session_id = "test-session-2"

    # Mock Redis cache miss
    mock_redis_client.zrevrange.return_value = []

    with patch('app.services.leaderboard_service.postgres_client') as mock_pg:
        # Mock materialized view fallback - return AsyncMock for fetch
        mock_pg.fetch = AsyncMock(return_value=[])

        rankings = await leaderboard_service_with_redis.get_leaderboard(session_id, limit=10)

        # Should attempt all tiers
        assert mock_redis_client.zrevrange.called
        assert mock_pg.fetch.called

@pytest.mark.asyncio
async def test_get_total_teams_with_redis(leaderboard_service_with_redis, mock_redis_client):
    """Test getting total teams count from Redis."""
    session_id = "test-session-3"
    mock_redis_client.zcard.return_value = 5

    total = await leaderboard_service_with_redis.get_total_teams(session_id)

    assert total == 5
    mock_redis_client.zcard.assert_called_once_with(f"leaderboard:{session_id}")

@pytest.mark.asyncio
async def test_get_total_teams_without_redis(leaderboard_service_no_redis):
    """Test getting total teams count without Redis (fallback to DB)."""
    session_id = "test-session-4"

    with patch('app.services.leaderboard_service.postgres_client') as mock_pg:
        mock_pg.fetchval = AsyncMock(return_value=3)

        total = await leaderboard_service_no_redis.get_total_teams(session_id)

        assert total == 3
        assert mock_pg.fetchval.called
