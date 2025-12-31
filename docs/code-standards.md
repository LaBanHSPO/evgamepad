# Code Standards & Patterns - EV GamePad

**Last Updated:** 2025-12-31
**Version:** Phase 01 - Leaderboard Infrastructure
**Target Audience:** Backend developers, code reviewers

---

## Table of Contents

1. Python Code Style
2. Async/Await Patterns
3. Database Patterns
4. API & Socket.IO Conventions
5. Error Handling
6. Testing Standards
7. Phase 01 (Leaderboard) Patterns

---

## 1. Python Code Style

### General Principles

- **Python 3.9+** - Match MTradingKit5 compatibility
- **PEP 8** - Follow standard guidelines
- **Type Hints** - Required for all public functions
- **Docstrings** - Google-style docstrings for classes/modules
- **Line Length** - Max 100 characters

### Naming Conventions

```python
# Constants
POSTGRES_TIMEOUT = 60
REDIS_DEFAULT_TTL = 300
MAX_TEAM_SIZE = 6

# Functions/methods
async def get_leaderboard_for_session():
    """Get leaderboard rankings."""

def calculate_pnl(open_price: float, close_price: float) -> float:
    """Calculate profit/loss."""

# Classes
class LeaderboardService:
    """Service for leaderboard operations."""

class PostgresClient:
    """Async PostgreSQL connection pool."""

# Private methods/variables
def _get_user_team(self, session_id: str) -> Optional[str]:
    """Internal helper - prefix with underscore."""

_cached_results = {}  # Module-level cache
```

### Type Hints

```python
# Good: Complete type hints
async def get_leaderboard(
    self,
    session_id: str,
    limit: int = 10
) -> List[LeaderboardEntry]:
    """Get top teams."""

# Bad: Missing return type
async def get_leaderboard(self, session_id, limit=10):
    pass

# Optional types for nullable values
async def get_my_rank(
    self,
    session_id: str,
    user_id: str
) -> Optional[LeaderboardEntry]:
    """May return None if user not in session."""
```

### Import Organization

```python
# 1. Standard library
import asyncio
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

# 2. Third-party
import asyncpg
import redis.asyncio as redis
from pydantic import BaseModel

# 3. Local application
from app.config import config
from app.database.postgres_client import postgres_client
from app.models.game_models import LeaderboardEntry
```

---

## 2. Async/Await Patterns

### Async Context Managers

```python
# Good: Use context managers for resource cleanup
async def fetch_data(self) -> List[Row]:
    async with self.pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM teams")

# Bad: Manual cleanup
async def fetch_data(self) -> List[Row]:
    conn = await self.pool.acquire()
    data = await conn.fetch("SELECT * FROM teams")
    # May leak if exception before close
    await conn.close()
```

### Concurrent Operations

```python
# Good: Use asyncio.gather for parallel execution
async def process_multi_timeframe(self, symbol: str, timeframes: List[str]):
    tasks = [
        self.process_timeframe(symbol, tf)
        for tf in timeframes
    ]
    results = await asyncio.gather(*tasks)
    return results

# Bad: Sequential execution (slow)
async def process_multi_timeframe(self, symbol: str, timeframes: List[str]):
    results = []
    for tf in timeframes:
        results.append(await self.process_timeframe(symbol, tf))
    return results
```

### Blocking Operations

```python
# Good: Use asyncio.to_thread for blocking calls
def _fetch_mt5_rates(symbol: str, timeframe: int, count: int):
    """Blocking MT5 call."""
    return mt5.copy_rates_from_pos(symbol, timeframe, 0, count)

async def fetch_ohlcv(self, symbol: str, timeframe: str):
    """Async wrapper."""
    mt5_tf = self.TIMEFRAME_MAP[timeframe]
    rates = await asyncio.to_thread(_fetch_mt5_rates, symbol, mt5_tf, 100)
    return rates

# Bad: Blocking call in async context (blocks event loop)
async def fetch_ohlcv(self, symbol: str, timeframe: str):
    # This BLOCKS the event loop - don't do this
    return mt5.copy_rates_from_pos(symbol, mt5_tf, 0, 100)
```

### Exception Handling in Async

```python
# Good: Catch exceptions at appropriate level
async def get_leaderboard(self, session_id: str) -> List[LeaderboardEntry]:
    try:
        result = await self._get_from_redis(session_id)
        if result:
            return result
        return await self._get_from_db(session_id)
    except Exception as e:
        logger.error(f"Leaderboard fetch failed: {e}")
        return []  # Graceful degradation

# Bad: Swallowing exceptions silently
async def get_leaderboard(self, session_id: str) -> List[LeaderboardEntry]:
    try:
        return await self._get_from_redis(session_id)
    except:  # Catches EVERYTHING
        pass  # Silent failure
```

---

## 3. Database Patterns

### PostgreSQL Query Style

```python
# Good: Parameterized queries (prevent SQL injection)
async def get_team(self, team_id: str) -> Optional[asyncpg.Record]:
    query = "SELECT * FROM teams WHERE team_id = $1"
    return await postgres_client.fetchrow(query, team_id)

# Bad: String interpolation (SQL injection vulnerability)
async def get_team(self, team_id: str) -> Optional[asyncpg.Record]:
    query = f"SELECT * FROM teams WHERE team_id = '{team_id}'"
    return await postgres_client.fetchrow(query)
```

### Connection Pool Management

```python
# Good: Use global pool instance
# At module level:
postgres_client = PostgresClient()

# In startup:
await postgres_client.initialize()

# In shutdown:
await postgres_client.close()

# Bad: Creating new connection per query
async def get_team(self, team_id: str):
    pool = await asyncpg.create_pool(...)  # Expensive
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM teams WHERE team_id = $1", team_id)
    await pool.close()  # Slow connection churn
```

### Transaction Handling

```python
# Good: Explicit transaction for multi-statement operations
async def create_team_with_members(self, team_name: str, members: List[str]):
    async with postgres_client.pool.acquire() as conn:
        async with conn.transaction():
            team_id = await conn.fetchval(
                "INSERT INTO teams (team_name) VALUES ($1) RETURNING team_id",
                team_name
            )

            for member_id in members:
                await conn.execute(
                    "INSERT INTO team_members (team_id, user_id) VALUES ($1, $2)",
                    team_id, member_id
                )
        return team_id  # Committed if no exception

# Bad: No transaction
async def create_team_with_members(self, team_name: str, members: List[str]):
    team_id = await postgres_client.fetchval(
        "INSERT INTO teams (team_name) VALUES ($1) RETURNING team_id",
        team_name
    )
    # If exception here, team created but no members added (inconsistent)
    for member_id in members:
        await postgres_client.execute(
            "INSERT INTO team_members (team_id, user_id) VALUES ($1, $2)",
            team_id, member_id
        )
```

### Query Performance

```python
# Good: Index-aware queries
# CREATE INDEX idx_positions_session_user ON positions(session_id, user_id)

query = """
    SELECT SUM(pnl) FROM positions
    WHERE session_id = $1 AND user_id = $2
"""
# Uses index, fast

# Bad: Full table scan
query = """
    SELECT SUM(pnl) FROM positions
    WHERE user_id = $1
"""
# No session_id in WHERE, full scan on large table
```

---

## 4. API & Socket.IO Conventions

### Request/Response Models

```python
# Good: Use Pydantic models for validation + schema
from pydantic import BaseModel, Field

class LeaderboardRequest(BaseModel):
    session_id: str
    limit: int = Field(default=10, le=100)  # Max 100
    user_id: Optional[str] = None

class LeaderboardResponse(BaseModel):
    rankings: List[LeaderboardEntry]
    my_rank: Optional[LeaderboardEntry] = None
    total_teams: int

# In handler:
@sio.on("leaderboard:get")
async def handle_get_leaderboard(sid, data):
    req = LeaderboardRequest(**data)  # Auto-validates
    result = await leaderboard_service.get_leaderboard(
        req.session_id, req.limit
    )
    await sio.emit("leaderboard:result", result.dict(), room=sid)

# Bad: No validation
@sio.on("leaderboard:get")
async def handle_get_leaderboard(sid, data):
    session_id = data.get("session_id")  # May be None
    limit = data.get("limit", 10)  # May be 999999
    # No type checking, no validation
```

### Error Response Format

```python
# Good: Consistent error structure
from app.models.responses import ErrorCode, error_response

await sio.emit("error", error_response(
    ErrorCode.VALIDATION_ERROR,
    "Invalid session_id",
    details={"field": "session_id"}
), room=sid)

# Response format:
{
    "success": False,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid session_id",
        "details": {"field": "session_id"}
    }
}
```

### Socket.IO Room Patterns

```python
# Good: Session-scoped rooms for broadcasts
sio.enter_room(sid, f"session:{session_id}")

# Broadcast to all in session
await sio.emit("leaderboard:update", {...}, room=f"session:{session_id}")

# Bad: User-global room (broadcasts to all user's connections)
sio.enter_room(sid, user_id)
await sio.emit("leaderboard:update", {...}, room=user_id)
# Problem: User may be in multiple sessions
```

---

## 5. Error Handling

### Exception Hierarchy

```python
# Define custom exceptions
class LeaderboardError(Exception):
    """Base exception for leaderboard operations."""

class SessionNotFoundError(LeaderboardError):
    """Session doesn't exist."""

class InvalidRankingError(LeaderboardError):
    """Ranking calculation failed."""

# Use specific exceptions
try:
    session = await self._get_session(session_id)
    if not session:
        raise SessionNotFoundError(f"Session {session_id} not found")
except SessionNotFoundError as e:
    logger.warning(str(e))
    await sio.emit("error", {...}, room=sid)
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    await sio.emit("error", {...}, room=sid)
```

### Logging Best Practices

```python
logger = logging.getLogger(__name__)

# Good: Structured logging with context
logger.info(f"Leaderboard sent to {sid} for session {session_id}")
logger.debug(f"Redis cache hit for session {session_id}")
logger.warning(f"Redis unavailable, falling back to DB")
logger.error(f"Leaderboard refresh failed: {e}")

# Bad: Generic messages without context
logger.info("Leaderboard sent")
logger.error("Error")

# Exception logging
try:
    await postgres_client.fetch(query)
except Exception as e:
    logger.exception(f"Query failed: {e}")  # Includes stack trace
```

### Graceful Degradation

```python
# Good: Fall back to working solution
async def get_leaderboard(self, session_id: str, limit: int):
    # Try Tier 1
    rankings = await self._get_from_redis(session_id, limit)
    if rankings:
        return rankings

    # Try Tier 2
    rankings = await self._get_from_materialized_view(session_id, limit)
    if rankings:
        return rankings

    # Tier 3: Always works (or error)
    return await self._get_from_direct_query(session_id, limit)

# Bad: Hard fail on first error
async def get_leaderboard(self, session_id: str, limit: int):
    # Exception here → no fallback
    return await self._get_from_redis(session_id, limit)
```

---

## 6. Testing Standards

### Unit Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestLeaderboardService:
    """Tests for LeaderboardService."""

    @pytest.fixture
    def service(self):
        """Create service with mocked Redis."""
        mock_redis = Mock()
        return LeaderboardService(redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_get_leaderboard_redis_hit(self, service):
        """Test cache hit path."""
        # Arrange
        service.redis_client.zrevrange.return_value = [
            ("team_1", 5000.0),
            ("team_2", 4500.0),
        ]

        # Act
        result = await service.get_leaderboard("session_1", 10)

        # Assert
        assert len(result) == 2
        assert result[0].rank == 1
        assert result[0].total_pnl == Decimal("5000.00")
```

### Integration Test Pattern

```python
@pytest.mark.integration
class TestLeaderboardIntegration:
    """Full integration tests against test database."""

    @pytest.fixture
    async def db(self):
        """Create test database."""
        await postgres_client.initialize()
        # Run migrations
        yield
        await postgres_client.close()

    @pytest.mark.asyncio
    async def test_leaderboard_accuracy(self, db):
        """Test three-tier caching accuracy."""
        # Insert test data
        session_id = await self._create_test_session()
        team_id = await self._create_test_team(session_id)

        # Get from Tier 3 (ground truth)
        direct = await service._get_from_direct_query(session_id, 10)

        # Get from Tier 2 (should match after refresh)
        await refresh_task._refresh_view()
        materialized = await service._get_from_materialized_view(session_id, 10)

        # Get from Tier 1 (should match after warm)
        await service._warm_redis_cache(session_id, materialized)
        redis_result = await service._get_from_redis(session_id, 10)

        # All should match
        assert direct == materialized == redis_result
```

---

## 7. Phase 01 (Leaderboard) Patterns

### Three-Tier Cache Implementation

```python
# Pattern: Fall-through cache with logging

class LeaderboardService:
    async def get_leaderboard(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[LeaderboardEntry]:
        """Three-tier leaderboard retrieval."""

        # Tier 1: Redis (fastest, may be stale)
        rankings = await self._get_from_redis(session_id, limit)
        if rankings:
            logger.debug(f"Redis cache hit for session {session_id}")
            return rankings

        # Tier 2: Materialized View (fresh within 30s, faster than direct)
        try:
            rankings = await self._get_from_materialized_view(session_id, limit)
            if rankings:
                logger.debug(f"MaterializedView hit for session {session_id}")
                # Warm Tier 1 for next request
                await self._warm_redis_cache(session_id, rankings)
                return rankings
        except Exception as e:
            logger.warning(f"MaterializedView failed: {e}")

        # Tier 3: Direct Query (slowest, guaranteed fresh/accurate)
        logger.debug(f"Direct query for session {session_id}")
        return await self._get_from_direct_query(session_id, limit)
```

### Redis Sorted Set Pattern

```python
# Pattern: Score-based ranking with O(log n) operations

async def update_team_score(
    self,
    session_id: str,
    team_id: str,
    pnl: Decimal
):
    """Update team P&L - fast score update."""
    key = f"leaderboard:{session_id}"

    # Add or update team score
    await self.redis_client.zadd(
        key,
        {team_id: float(pnl)}  # Score = P&L value
    )

    # Refresh TTL
    await self.redis_client.expire(key, 3600)

async def get_team_rank(
    self,
    session_id: str,
    team_id: str
) -> Optional[int]:
    """Get team's rank (0-indexed)."""
    key = f"leaderboard:{session_id}"

    # Reverse rank: 0 = highest score
    rank = await self.redis_client.zrevrank(key, team_id)
    return rank  # Will be None if team not in set
```

### Broadcast Pattern

```python
# Pattern: Room-scoped event broadcasting

async def broadcast_leaderboard_update(
    session_id: str,
    team_id: str,
    new_pnl: Decimal
):
    """Broadcast to all clients in session."""
    try:
        # Get updated ranking (optional context for message)
        rankings = await leaderboard_service.get_leaderboard(
            session_id, limit=1
        )

        # Determine if team moved to #1
        new_rank = 1 if rankings and rankings[0].team_id == team_id else None

        # Emit to room
        await sio.emit(
            "leaderboard:update",
            {
                "session_id": session_id,
                "team_id": team_id,
                "new_pnl": float(new_pnl),
                "new_rank": new_rank,
                "message": f"Team is now #{new_rank}!" if new_rank == 1 else None,
            },
            room=f"session:{session_id}"  # Only this session
        )

        logger.debug(f"Broadcasted leaderboard update for session {session_id}")

    except Exception as e:
        logger.error(f"Error broadcasting: {e}")
        # Don't raise - non-critical broadcast failure
```

### Materialized View Refresh Pattern

```python
# Pattern: Periodic refresh with error recovery

class LeaderboardRefreshTask:
    def __init__(self, interval: int = 30):
        self.interval = interval
        self.running = False

    async def start(self):
        """Background refresh loop."""
        self.running = True
        logger.info("Leaderboard refresh task started")

        while self.running:
            try:
                await self._refresh_view()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Leaderboard refresh failed: {e}")
                # Still sleep before retry - don't hammer DB
                await asyncio.sleep(self.interval)

    async def _refresh_view(self):
        """Execute refresh."""
        await postgres_client.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY team_leaderboard"
        )
        logger.debug("Materialized view refreshed")

    async def stop(self):
        """Graceful shutdown."""
        self.running = False
        logger.info("Leaderboard refresh task stopped")
```

---

## Code Review Checklist

### Phase 01 Specific Items

- [ ] Leaderboard queries use correct indexes (session_id, total_pnl DESC)
- [ ] Three-tier fallback logic present and tested
- [ ] Redis sorted set operations use correct key format
- [ ] Materialized view refresh task resilient to failures
- [ ] P&L aggregation includes only open positions (closed_at IS NULL)
- [ ] Rank conversion 0-indexed → 1-indexed correct
- [ ] Socket.IO room names follow `session:{session_id}` pattern
- [ ] Broadcast logic doesn't emit on every timer tick
- [ ] Database pool not exhausted (max_size reasonable)
- [ ] Pydantic models validate limit ≤ 100

### General Patterns

- [ ] No blocking calls in async context
- [ ] Connection cleanup guaranteed (with context managers)
- [ ] Specific exception handling (not bare `except`)
- [ ] Logging includes context (IDs, operation)
- [ ] Type hints on all public functions
- [ ] Error responses use ErrorCode enum
- [ ] SQL parameterized (no string interpolation)
- [ ] No N+1 queries (check loop queries)
- [ ] Tests mock external services
- [ ] No hardcoded values (use config)

---

## Performance Optimization Guidelines

### Hot Path Optimization

```python
# For get_leaderboard (called frequently):
# 1. Keep Tier 1 check fast (minimal Redis operations)
# 2. Avoid N+1: Get team_name/size in single query
# 3. Cache team metadata (name, size)

async def _get_from_redis(self, session_id: str, limit: int):
    # Single zrevrange call gets IDs + scores
    rankings = await self.redis_client.zrevrange(
        f"leaderboard:{session_id}", 0, limit - 1, withscores=True
    )

    # Convert to entries (N queries if not careful)
    entries = []
    for idx, (team_id, score) in enumerate(rankings):
        # Problem: N queries for team_name/size
        team_name = await self._get_team_name(team_id)
        team_size = await self._get_team_size(team_id)
        entries.append(...)

    # Solution: Batch load team metadata
    # (Future enhancement with in-memory cache)
```

### Cache-Friendly Keys

```python
# Good: Immutable keys
f"leaderboard:{session_id}"  # Simple, predictable

# Bad: Complex keys
f"leaderboard:{session_id}:{user_role}:{current_time}"  # Too specific, won't cache
```

---

**Document Status:**
- Status: Active
- Last Updated: 2025-12-31
- Owner: Code Review Team
- Visibility: Internal Team
