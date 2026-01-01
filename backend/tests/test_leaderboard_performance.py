"""Performance tests for leaderboard."""
import pytest
import asyncio
import time
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.leaderboard_service import LeaderboardService

@pytest.fixture
def mock_fast_redis():
    """Create fast mock Redis client."""
    client = MagicMock()
    client.zadd = AsyncMock(return_value=1)
    client.expire = AsyncMock(return_value=True)
    client.zrevrange = AsyncMock(return_value=[
        ("team-1", 2000.0),
        ("team-2", 1500.0),
        ("team-3", 1000.0)
    ])
    client.zrevrank = AsyncMock(return_value=0)
    client.zscore = AsyncMock(return_value=2000.0)
    client.zcard = AsyncMock(return_value=3)
    return client

@pytest.mark.asyncio
async def test_concurrent_updates_performance(mock_fast_redis):
    """Test 100 concurrent score updates."""
    service = LeaderboardService(redis_client=mock_fast_redis)

    tasks = []
    for i in range(100):
        task = service.update_team_score(
            "test-session",
            f"team-{i % 10}",  # 10 teams
            Decimal(str(1000 + i))
        )
        tasks.append(task)

    start = time.time()
    await asyncio.gather(*tasks)
    duration = time.time() - start

    print(f"100 updates in {duration:.2f}s ({duration*10:.1f}ms avg)")
    # Should complete fast with mocked Redis
    assert duration < 1.0  # Less than 1 second

@pytest.mark.asyncio
async def test_leaderboard_read_performance(mock_fast_redis):
    """Test read latency under load."""
    service = LeaderboardService(redis_client=mock_fast_redis)

    with patch.object(service, '_get_team_name', new=AsyncMock(return_value="Team")):
        with patch.object(service, '_get_team_size', new=AsyncMock(return_value=3)):
            times = []

            for _ in range(100):
                start = time.time()
                await service.get_leaderboard("test-session", 10)
                times.append(time.time() - start)

            avg = sum(times) / len(times)
            p95 = sorted(times)[int(len(times) * 0.95)]

            print(f"Avg: {avg*1000:.1f}ms, P95: {p95*1000:.1f}ms")
            # With mocked Redis, should be very fast
            assert avg < 0.01  # Average < 10ms
            assert p95 < 0.02  # P95 < 20ms
