# Phase 01: Leaderboard Infrastructure

**Priority:** P1 (CRITICAL - Foundation for all features)
**Status:** Done
**Effort:** 40 hours (2 weeks)
**Completed:** 2025-12-31 23:59
**Dependencies:** PostgreSQL, Redis, Socket.IO server

## Context Links

- **Brainstorm:** `/plans/reports/brainstorm-251230-2302-multiplayer-trading-game.md`
- **Research:** `/plans/reports/INDEX-MULTIPLAYER-RESEARCH.md`
- **Existing Redis Client:** `backend/app/database/redis_client.py`
- **Existing Socket.IO:** `backend/app/sio.py`

## Overview

Build real-time leaderboard system with sub-50ms update latency using three-tier caching architecture. Enables `/top` command for instant ranking queries with session-based team scores.

**Goal:** Operational leaderboard with Redis sorted sets, PostgreSQL materialized views, Socket.IO real-time broadcasts.

## Key Insights

1. **Three-Tier Caching Critical** - Redis → Materialized View → Direct query for fault tolerance
2. **O(log n) Updates** - Redis sorted sets provide optimal performance at scale
3. **Materialized Views** - 30-second refresh balances freshness with DB load
4. **Room-Based Broadcasting** - Socket.IO rooms prevent broadcast storms
5. **Atomic Operations** - Redis ZADD atomic to prevent race conditions

## Requirements

### Functional
- [ ] Real-time team score updates (< 50ms)
- [ ] `/top` command shows top 10 teams + my rank
- [ ] Session-scoped leaderboards (isolated per game)
- [ ] Automatic rank calculation
- [ ] Broadcast updates to all session participants

### Non-Functional
- [ ] Sub-50ms leaderboard read (Tier 1 Redis cache)
- [ ] Sub-200ms `/top` command response
- [ ] Support 10+ concurrent game sessions
- [ ] Graceful degradation (fallback to Tier 2/3)
- [ ] 99.9% cache hit rate for active sessions

## Architecture

### Three-Tier Caching Strategy

```
┌─────────────────────────────────────────────────────┐
│ Tier 1: Redis Sorted Set (< 50ms, 1-hour TTL)      │
│  Key: leaderboard:{session_id}                      │
│  Members: team_id → score (total P&L)               │
│  Operations: ZADD, ZREVRANGE, ZREVRANK, ZSCORE      │
└─────────────────────────────────────────────────────┘
                      ↓ (cache miss)
┌─────────────────────────────────────────────────────┐
│ Tier 2: PostgreSQL Materialized View (< 200ms)     │
│  View: team_leaderboard                             │
│  Refresh: CONCURRENTLY every 30 seconds             │
│  Fallback: Redis unavailable                        │
└─────────────────────────────────────────────────────┘
                      ↓ (view stale)
┌─────────────────────────────────────────────────────┐
│ Tier 3: Direct Query (< 500ms, guaranteed fresh)   │
│  Query: SUM(positions.pnl) GROUP BY team            │
│  Fallback: Materialized view outdated               │
└─────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Player action → P&L change
2. Update position in DB
3. Calculate new team P&L
4. ZADD to Redis leaderboard:{session_id}
5. Broadcast via Socket.IO to session:{session_id} room
6. All clients receive real-time update
```

## Related Code Files

### Files to CREATE

1. **`backend/app/database/postgres_client.py`** - PostgreSQL connection pool
   - asyncpg connection pool setup
   - Connection lifecycle management
   - Query helpers

2. **`backend/app/models/game_models.py`** - Game session data models
   - GameSession (Pydantic model)
   - Team (Pydantic model)
   - TeamMember (Pydantic model)
   - LeaderboardEntry (Pydantic model)

3. **`backend/app/services/leaderboard_service.py`** - Core leaderboard logic
   - Three-tier caching implementation
   - Redis operations (ZADD, ZREVRANGE, ZREVRANK)
   - Materialized view queries
   - Fallback logic

4. **`backend/app/events/game_events.py`** - Socket.IO game events
   - `leaderboard:get` handler
   - `leaderboard:update` broadcaster
   - `game:create` event
   - `game:join` event

5. **`backend/app/processors/command_processor.py`** - Enhanced with `/top` command
   - Parse `/top` command
   - Call LeaderboardService
   - Return formatted response

6. **`backend/app/tasks/leaderboard_refresh_task.py`** - Background refresh
   - Refresh materialized view every 30s
   - Update Redis from DB for warmup

### Files to MODIFY

1. **`backend/app/sio.py`** - Add game event handlers
   - Import game_events module
   - Register event handlers
   - Create session rooms

2. **`backend/app/database/redis_client.py`** - Add leaderboard methods
   - `zadd_leaderboard()` helper
   - `zrevrange_leaderboard()` helper
   - `zrevrank_leaderboard()` helper

3. **`backend/app/main.py`** - Register background tasks
   - Start leaderboard refresh task
   - Initialize PostgreSQL pool
   - Health check endpoints

### Database Migrations

1. **`migrations/001_create_game_sessions.sql`** - Game session schema
2. **`migrations/002_create_teams.sql`** - Teams schema
3. **`migrations/003_create_team_members.sql`** - Team members schema
4. **`migrations/004_create_materialized_view.sql`** - Leaderboard view

## Implementation Steps

### Week 1: Database & Core Service (20h)

#### Step 1.1: PostgreSQL Schema (4h)

1. Create migration files in `migrations/` directory

**Migration 001:**
```sql
-- migrations/001_create_game_sessions.sql
CREATE TABLE game_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    creator_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'waiting',  -- waiting, active, completed
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    max_team_size INT DEFAULT 6,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN ('waiting', 'active', 'completed'))
);

CREATE INDEX idx_game_sessions_status ON game_sessions(status);
CREATE INDEX idx_game_sessions_name ON game_sessions(name);
```

**Migration 002:**
```sql
-- migrations/002_create_teams.sql
CREATE TABLE teams (
    team_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    team_name VARCHAR(50) NOT NULL,
    total_pnl DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_team_per_session UNIQUE(session_id, team_name)
);

CREATE INDEX idx_teams_session ON teams(session_id);
```

**Migration 003:**
```sql
-- migrations/003_create_team_members.sql
CREATE TABLE team_members (
    member_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(team_id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_user_per_session UNIQUE(team_id, user_id)
);

CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);
```

**Migration 004:**
```sql
-- migrations/004_create_materialized_view.sql
CREATE MATERIALIZED VIEW team_leaderboard AS
SELECT
    t.session_id,
    t.team_id,
    t.team_name,
    COALESCE(SUM(p.pnl), 0) as total_pnl,
    COUNT(DISTINCT tm.user_id) as team_size,
    NOW() as computed_at
FROM teams t
JOIN team_members tm ON t.team_id = tm.team_id
LEFT JOIN positions p ON tm.user_id = p.user_id AND p.session_id = t.session_id
WHERE p.closed_at IS NULL  -- Only open positions
GROUP BY t.session_id, t.team_id, t.team_name;

CREATE UNIQUE INDEX idx_team_leaderboard_pk ON team_leaderboard(session_id, team_id);
CREATE INDEX idx_team_leaderboard_pnl ON team_leaderboard(session_id, total_pnl DESC);
```

2. Run migrations
```bash
psql -U postgres -d ev_gamepad < migrations/001_create_game_sessions.sql
psql -U postgres -d ev_gamepad < migrations/002_create_teams.sql
psql -U postgres -d ev_gamepad < migrations/003_create_team_members.sql
psql -U postgres -d ev_gamepad < migrations/004_create_materialized_view.sql
```

#### Step 1.2: PostgreSQL Client (3h)

Create `backend/app/database/postgres_client.py`:

```python
"""PostgreSQL connection pool and query helpers."""
import asyncpg
from typing import Optional, List, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class PostgresClient:
    """Async PostgreSQL client with connection pooling."""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Create connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                min_size=5,
                max_size=20,
                command_timeout=60,
            )
            logger.info("PostgreSQL pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise

    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL pool closed")

    async def execute(self, query: str, *args) -> str:
        """Execute query without returning results."""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch single row."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

# Global instance
postgres_client = PostgresClient()
```

Add to `backend/app/config.py`:
```python
# PostgreSQL settings
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ev_gamepad")
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
```

#### Step 1.3: Data Models (2h)

Create `backend/app/models/game_models.py`:

```python
"""Game session and leaderboard data models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class GameSession(BaseModel):
    """Game session model."""
    session_id: str
    name: str
    creator_id: str
    status: str  # waiting, active, completed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_team_size: int = 6
    created_at: datetime

class Team(BaseModel):
    """Team model."""
    team_id: str
    session_id: str
    team_name: str
    total_pnl: Decimal = Decimal("0")
    created_at: datetime

class TeamMember(BaseModel):
    """Team member model."""
    member_id: str
    team_id: str
    user_id: str
    username: str
    joined_at: datetime

class LeaderboardEntry(BaseModel):
    """Leaderboard entry model."""
    rank: int
    team_id: str
    team_name: str
    total_pnl: Decimal
    team_size: int

class LeaderboardResponse(BaseModel):
    """Response for /top command."""
    rankings: List[LeaderboardEntry]
    my_rank: Optional[LeaderboardEntry] = None
    total_teams: int
```

#### Step 1.4: Leaderboard Service - Core Logic (6h)

Create `backend/app/services/leaderboard_service.py`:

```python
"""Real-time leaderboard service with three-tier caching."""
import logging
from typing import List, Optional, Dict
from decimal import Decimal
from app.database.redis_client import redis_client
from app.database.postgres_client import postgres_client
from app.models.game_models import LeaderboardEntry, LeaderboardResponse

logger = logging.getLogger(__name__)

class LeaderboardService:
    """Three-tier leaderboard: Redis → Materialized View → Direct Query."""

    async def update_team_score(
        self,
        session_id: str,
        team_id: str,
        pnl: Decimal
    ):
        """
        Update team score in Redis leaderboard.
        O(log n) complexity via sorted set.
        """
        key = f"leaderboard:{session_id}"

        # Update Redis sorted set (Tier 1)
        await redis_client.zadd(key, {team_id: float(pnl)})
        await redis_client.expire(key, 3600)  # 1 hour TTL

        logger.debug(f"Updated leaderboard for session {session_id}, team {team_id}: {pnl}")

    async def get_leaderboard(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[LeaderboardEntry]:
        """
        Get top N teams with ranks.
        Tier 1 (Redis) → Tier 2 (Mat View) → Tier 3 (Direct)
        """
        # Tier 1: Try Redis (fastest)
        rankings = await self._get_from_redis(session_id, limit)
        if rankings:
            return rankings

        # Tier 2: Materialized View (fallback)
        try:
            rankings = await self._get_from_materialized_view(session_id, limit)
            if rankings:
                # Warm Redis cache
                await self._warm_redis_cache(session_id, rankings)
                return rankings
        except Exception as e:
            logger.warning(f"Materialized view failed: {e}")

        # Tier 3: Direct Query (guaranteed fresh)
        return await self._get_from_direct_query(session_id, limit)

    async def get_my_rank(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[LeaderboardEntry]:
        """Get my team's rank in session."""
        # Find my team
        team_id = await self._get_user_team(session_id, user_id)
        if not team_id:
            return None

        # Get rank from Redis
        key = f"leaderboard:{session_id}"
        rank = await redis_client.zrevrank(key, team_id)
        score = await redis_client.zscore(key, team_id)

        if rank is None:
            # Fallback to DB
            return await self._get_rank_from_db(session_id, team_id)

        # Get team name
        team_name = await self._get_team_name(team_id)
        team_size = await self._get_team_size(team_id)

        return LeaderboardEntry(
            rank=rank + 1,  # 0-indexed → 1-indexed
            team_id=team_id,
            team_name=team_name,
            total_pnl=Decimal(str(score)),
            team_size=team_size
        )

    # ==================== Tier 1: Redis ====================

    async def _get_from_redis(
        self,
        session_id: str,
        limit: int
    ) -> Optional[List[LeaderboardEntry]]:
        """Tier 1: Get leaderboard from Redis sorted set."""
        key = f"leaderboard:{session_id}"

        # Get top N teams with scores
        rankings = await redis_client.zrevrange(
            key, 0, limit - 1, withscores=True
        )

        if not rankings:
            logger.debug(f"Redis cache miss for session {session_id}")
            return None

        # Convert to LeaderboardEntry
        entries = []
        for idx, (team_id, score) in enumerate(rankings):
            team_name = await self._get_team_name(team_id)
            team_size = await self._get_team_size(team_id)

            entries.append(LeaderboardEntry(
                rank=idx + 1,
                team_id=team_id,
                team_name=team_name,
                total_pnl=Decimal(str(score)),
                team_size=team_size
            ))

        logger.debug(f"Redis cache hit for session {session_id}")
        return entries

    # ==================== Tier 2: Materialized View ====================

    async def _get_from_materialized_view(
        self,
        session_id: str,
        limit: int
    ) -> Optional[List[LeaderboardEntry]]:
        """Tier 2: Get leaderboard from materialized view."""
        query = """
            SELECT team_id, team_name, total_pnl, team_size
            FROM team_leaderboard
            WHERE session_id = $1
            ORDER BY total_pnl DESC
            LIMIT $2
        """

        rows = await postgres_client.fetch(query, session_id, limit)

        if not rows:
            return None

        entries = [
            LeaderboardEntry(
                rank=idx + 1,
                team_id=str(row["team_id"]),
                team_name=row["team_name"],
                total_pnl=row["total_pnl"],
                team_size=row["team_size"]
            )
            for idx, row in enumerate(rows)
        ]

        logger.debug(f"Materialized view hit for session {session_id}")
        return entries

    # ==================== Tier 3: Direct Query ====================

    async def _get_from_direct_query(
        self,
        session_id: str,
        limit: int
    ) -> List[LeaderboardEntry]:
        """Tier 3: Direct query (guaranteed fresh, slowest)."""
        query = """
            SELECT
                t.team_id,
                t.team_name,
                COALESCE(SUM(p.pnl), 0) as total_pnl,
                COUNT(DISTINCT tm.user_id) as team_size
            FROM teams t
            JOIN team_members tm ON t.team_id = tm.team_id
            LEFT JOIN positions p ON tm.user_id = p.user_id
                AND p.session_id = t.session_id
                AND p.closed_at IS NULL
            WHERE t.session_id = $1
            GROUP BY t.team_id, t.team_name
            ORDER BY total_pnl DESC
            LIMIT $2
        """

        rows = await postgres_client.fetch(query, session_id, limit)

        entries = [
            LeaderboardEntry(
                rank=idx + 1,
                team_id=str(row["team_id"]),
                team_name=row["team_name"],
                total_pnl=row["total_pnl"],
                team_size=row["team_size"]
            )
            for idx, row in enumerate(rows)
        ]

        logger.debug(f"Direct query for session {session_id}")
        return entries

    # ==================== Helper Methods ====================

    async def _get_user_team(self, session_id: str, user_id: str) -> Optional[str]:
        """Find which team the user belongs to."""
        query = """
            SELECT tm.team_id
            FROM team_members tm
            JOIN teams t ON tm.team_id = t.team_id
            WHERE t.session_id = $1 AND tm.user_id = $2
        """
        row = await postgres_client.fetchrow(query, session_id, user_id)
        return str(row["team_id"]) if row else None

    async def _get_team_name(self, team_id: str) -> str:
        """Get team name from database."""
        query = "SELECT team_name FROM teams WHERE team_id = $1"
        row = await postgres_client.fetchrow(query, team_id)
        return row["team_name"] if row else "Unknown Team"

    async def _get_team_size(self, team_id: str) -> int:
        """Get team member count."""
        query = "SELECT COUNT(*) FROM team_members WHERE team_id = $1"
        count = await postgres_client.fetchval(query, team_id)
        return count or 0

    async def _warm_redis_cache(
        self,
        session_id: str,
        entries: List[LeaderboardEntry]
    ):
        """Warm Redis cache from DB results."""
        key = f"leaderboard:{session_id}"

        # Build score mapping
        mapping = {entry.team_id: float(entry.total_pnl) for entry in entries}

        # Bulk update Redis
        if mapping:
            await redis_client.zadd(key, mapping)
            await redis_client.expire(key, 3600)
            logger.debug(f"Warmed Redis cache for session {session_id}")

    async def _get_rank_from_db(
        self,
        session_id: str,
        team_id: str
    ) -> Optional[LeaderboardEntry]:
        """Get rank from DB when Redis unavailable."""
        query = """
            WITH ranked_teams AS (
                SELECT
                    team_id,
                    team_name,
                    total_pnl,
                    team_size,
                    ROW_NUMBER() OVER (ORDER BY total_pnl DESC) as rank
                FROM team_leaderboard
                WHERE session_id = $1
            )
            SELECT * FROM ranked_teams WHERE team_id = $2
        """
        row = await postgres_client.fetchrow(query, session_id, team_id)

        if not row:
            return None

        return LeaderboardEntry(
            rank=row["rank"],
            team_id=str(row["team_id"]),
            team_name=row["team_name"],
            total_pnl=row["total_pnl"],
            team_size=row["team_size"]
        )

# Global instance
leaderboard_service = LeaderboardService()
```

#### Step 1.5: Background Refresh Task (3h)

Create `backend/app/tasks/leaderboard_refresh_task.py`:

```python
"""Background task to refresh materialized view."""
import asyncio
import logging
from app.database.postgres_client import postgres_client

logger = logging.getLogger(__name__)

class LeaderboardRefreshTask:
    """Refresh materialized view every 30 seconds."""

    def __init__(self, interval: int = 30):
        self.interval = interval
        self.running = False

    async def start(self):
        """Start background refresh loop."""
        self.running = True
        logger.info("Leaderboard refresh task started")

        while self.running:
            try:
                await self._refresh_view()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Leaderboard refresh failed: {e}")
                await asyncio.sleep(self.interval)

    async def stop(self):
        """Stop background refresh."""
        self.running = False
        logger.info("Leaderboard refresh task stopped")

    async def _refresh_view(self):
        """Refresh materialized view concurrently."""
        query = "REFRESH MATERIALIZED VIEW CONCURRENTLY team_leaderboard"
        await postgres_client.execute(query)
        logger.debug("Materialized view refreshed")

# Global instance
leaderboard_refresh_task = LeaderboardRefreshTask()
```

Update `backend/app/main.py`:
```python
from app.tasks.leaderboard_refresh_task import leaderboard_refresh_task
from app.database.postgres_client import postgres_client

@app.on_event("startup")
async def startup_event():
    # Initialize PostgreSQL
    await postgres_client.initialize()

    # Start leaderboard refresh
    asyncio.create_task(leaderboard_refresh_task.start())

@app.on_event("shutdown")
async def shutdown_event():
    await leaderboard_refresh_task.stop()
    await postgres_client.close()
```

#### Step 1.6: Unit Tests (2h)

Create `backend/tests/test_leaderboard_service.py`:

```python
"""Tests for leaderboard service."""
import pytest
from decimal import Decimal
from app.services.leaderboard_service import leaderboard_service

@pytest.mark.asyncio
async def test_update_team_score(redis_client, postgres_client):
    """Test team score update in Redis."""
    session_id = "test-session-1"
    team_id = "team-1"
    pnl = Decimal("1500.50")

    await leaderboard_service.update_team_score(session_id, team_id, pnl)

    # Verify Redis update
    score = await redis_client.zscore(f"leaderboard:{session_id}", team_id)
    assert score == float(pnl)

@pytest.mark.asyncio
async def test_get_leaderboard_redis_tier(redis_client):
    """Test leaderboard fetch from Redis (Tier 1)."""
    session_id = "test-session-2"

    # Pre-populate Redis
    await redis_client.zadd(f"leaderboard:{session_id}", {
        "team-1": 2000.0,
        "team-2": 1500.0,
        "team-3": 1000.0
    })

    rankings = await leaderboard_service.get_leaderboard(session_id, limit=10)

    assert len(rankings) == 3
    assert rankings[0].rank == 1
    assert rankings[0].total_pnl == Decimal("2000.0")

@pytest.mark.asyncio
async def test_get_my_rank(redis_client, postgres_client):
    """Test getting user's team rank."""
    session_id = "test-session-3"
    user_id = "user-1"
    team_id = "team-1"

    # Setup test data
    # ... (insert session, team, team_member)

    # Add to Redis
    await redis_client.zadd(f"leaderboard:{session_id}", {team_id: 1800.0})

    my_rank = await leaderboard_service.get_my_rank(session_id, user_id)

    assert my_rank is not None
    assert my_rank.rank == 1
    assert my_rank.total_pnl == Decimal("1800.0")
```

### Week 2: Socket.IO Integration & Commands (20h)

#### Step 2.1: Socket.IO Event Handlers (5h)

Create `backend/app/events/game_events.py`:

```python
"""Socket.IO event handlers for game sessions and leaderboard."""
import logging
from app.sio import sio
from app.services.leaderboard_service import leaderboard_service

logger = logging.getLogger(__name__)

@sio.on("leaderboard:get")
async def handle_get_leaderboard(sid, data):
    """
    Client requests leaderboard via /top command.

    Request:
    {
        "session_id": "uuid",
        "limit": 10  # optional, default 10
    }

    Response:
    {
        "rankings": [
            {"rank": 1, "team_name": "Team Alpha", "total_pnl": 2500.00, ...},
            ...
        ],
        "my_rank": {"rank": 3, "team_name": "My Team", ...},
        "total_teams": 5
    }
    """
    try:
        session_id = data.get("session_id")
        limit = data.get("limit", 10)
        user_id = data.get("user_id")  # From auth context

        # Get rankings
        rankings = await leaderboard_service.get_leaderboard(session_id, limit)

        # Get my rank
        my_rank = await leaderboard_service.get_my_rank(session_id, user_id)

        # Total teams
        total_teams = await leaderboard_service.get_total_teams(session_id)

        await sio.emit("leaderboard:result", {
            "rankings": [r.dict() for r in rankings],
            "my_rank": my_rank.dict() if my_rank else None,
            "total_teams": total_teams
        }, room=sid)

        logger.info(f"Leaderboard sent to {sid} for session {session_id}")

    except Exception as e:
        logger.error(f"Error handling leaderboard:get: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

@sio.on("leaderboard:subscribe")
async def handle_subscribe_leaderboard(sid, data):
    """Subscribe to real-time leaderboard updates for a session."""
    try:
        session_id = data.get("session_id")

        # Join session room for broadcasts
        sio.enter_room(sid, f"session:{session_id}")

        logger.info(f"Client {sid} subscribed to session {session_id}")

        await sio.emit("leaderboard:subscribed", {
            "session_id": session_id,
            "message": "Subscribed to real-time updates"
        }, room=sid)

    except Exception as e:
        logger.error(f"Error handling leaderboard:subscribe: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

async def broadcast_leaderboard_update(session_id: str, team_id: str, new_pnl: Decimal):
    """
    Broadcast leaderboard update to all clients in session.
    Called after P&L change.
    """
    try:
        # Get updated rank
        rankings = await leaderboard_service.get_leaderboard(session_id, limit=1)

        if rankings and rankings[0].team_id == team_id:
            # Team is now #1
            await sio.emit("leaderboard:update", {
                "session_id": session_id,
                "team_id": team_id,
                "new_pnl": float(new_pnl),
                "new_rank": 1,
                "message": f"{rankings[0].team_name} is now #1!"
            }, room=f"session:{session_id}")
        else:
            # Regular update
            await sio.emit("leaderboard:update", {
                "session_id": session_id,
                "team_id": team_id,
                "new_pnl": float(new_pnl)
            }, room=f"session:{session_id}")

        logger.debug(f"Broadcasted leaderboard update for session {session_id}")

    except Exception as e:
        logger.error(f"Error broadcasting leaderboard update: {e}")
```

Update `backend/app/sio.py`:
```python
from app.events import game_events

# Event handlers automatically registered via decorators
```

#### Step 2.2: `/top` Command Implementation (4h)

Update `backend/app/processors/command_processor.py`:

```python
from app.services.leaderboard_service import leaderboard_service

class CommandProcessor:
    """Parse and execute chat commands."""

    COMMANDS = {
        "csv": "create_server",
        "jsv": "join_server",
        "top": "show_leaderboard"  # NEW
    }

    async def show_leaderboard(self, user_id: str, args: str):
        """
        Handle /top command.

        Usage: /top [limit]
        Example: /top 10
        """
        # Parse limit (default 10)
        limit = 10
        if args:
            try:
                limit = int(args.strip())
                limit = max(1, min(limit, 50))  # Clamp 1-50
            except ValueError:
                return {
                    "type": "error",
                    "message": "Invalid limit. Usage: /top [1-50]"
                }

        # Get user's current session
        session_id = await self._get_user_session(user_id)
        if not session_id:
            return {
                "type": "error",
                "message": "You are not in an active session. Use /jsv <ServerName> to join."
            }

        # Get leaderboard
        rankings = await leaderboard_service.get_leaderboard(session_id, limit)
        my_rank = await leaderboard_service.get_my_rank(session_id, user_id)

        # Format response
        return {
            "type": "leaderboard",
            "session_id": session_id,
            "rankings": [r.dict() for r in rankings],
            "my_rank": my_rank.dict() if my_rank else None,
            "message": self._format_leaderboard_message(rankings, my_rank)
        }

    def _format_leaderboard_message(
        self,
        rankings: List[LeaderboardEntry],
        my_rank: Optional[LeaderboardEntry]
    ) -> str:
        """Format leaderboard as text message."""
        lines = ["🏆 **Leaderboard** 🏆\n"]

        for entry in rankings:
            medal = "🥇" if entry.rank == 1 else "🥈" if entry.rank == 2 else "🥉" if entry.rank == 3 else "  "
            lines.append(
                f"{medal} #{entry.rank}. {entry.team_name} - "
                f"${entry.total_pnl:,.2f} ({entry.team_size} players)"
            )

        if my_rank:
            lines.append(f"\n**Your Team:** #{my_rank.rank} - ${my_rank.total_pnl:,.2f}")

        return "\n".join(lines)
```

#### Step 2.3: Redis Helper Methods (2h)

Update `backend/app/database/redis_client.py`:

```python
class RedisClient:
    # ... existing methods ...

    async def zadd(self, key: str, mapping: Dict[str, float]):
        """Add members to sorted set."""
        return await self.client.zadd(key, mapping)

    async def zrevrange(
        self,
        key: str,
        start: int,
        stop: int,
        withscores: bool = False
    ):
        """Get members by reverse rank (highest first)."""
        return await self.client.zrevrange(key, start, stop, withscores=withscores)

    async def zrevrank(self, key: str, member: str) -> Optional[int]:
        """Get reverse rank of member (0 = highest)."""
        return await self.client.zrevrank(key, member)

    async def zscore(self, key: str, member: str) -> Optional[float]:
        """Get score of member."""
        return await self.client.zscore(key, member)

    async def zcard(self, key: str) -> int:
        """Get total number of members in sorted set."""
        return await self.client.zcard(key)
```

#### Step 2.4: Integration Tests (5h)

Create `backend/tests/test_leaderboard_integration.py`:

```python
"""End-to-end leaderboard integration tests."""
import pytest
from decimal import Decimal
import socketio

@pytest.mark.asyncio
async def test_top_command_flow(command_processor, test_session):
    """Test complete /top command flow."""
    user_id = "test-user-1"
    session_id = test_session["session_id"]

    # Join session first
    # ... (setup test session and team)

    # Execute /top command
    result = await command_processor.parse_message(user_id, "/top")

    assert result["type"] == "leaderboard"
    assert "rankings" in result
    assert "my_rank" in result

@pytest.mark.asyncio
async def test_realtime_leaderboard_broadcast(sio_client):
    """Test real-time leaderboard updates via Socket.IO."""
    # Connect client
    await sio_client.connect("http://localhost:8000")

    # Subscribe to session
    await sio_client.emit("leaderboard:subscribe", {
        "session_id": "test-session"
    })

    # Wait for subscription confirmation
    response = await sio_client.receive()
    assert response[0] == "leaderboard:subscribed"

    # Simulate P&L change
    # ... (trigger leaderboard update)

    # Wait for broadcast
    update = await sio_client.receive()
    assert update[0] == "leaderboard:update"
    assert "new_pnl" in update[1]

@pytest.mark.asyncio
async def test_three_tier_caching_fallback(leaderboard_service, redis_client):
    """Test cache tier fallback mechanism."""
    session_id = "test-session"

    # Tier 1: Redis should work
    rankings = await leaderboard_service.get_leaderboard(session_id, 10)
    assert rankings  # From Redis

    # Flush Redis
    await redis_client.delete(f"leaderboard:{session_id}")

    # Tier 2: Should fallback to materialized view
    rankings = await leaderboard_service.get_leaderboard(session_id, 10)
    assert rankings  # From DB
```

#### Step 2.5: Documentation (2h)

Create `backend/docs/leaderboard-api.md`:

```markdown
# Leaderboard API Documentation

## Socket.IO Events

### Client → Server

**leaderboard:get**
Request leaderboard data.

**leaderboard:subscribe**
Subscribe to real-time updates for a session.

### Server → Client

**leaderboard:result**
Leaderboard data response.

**leaderboard:update**
Real-time score update broadcast.

**leaderboard:subscribed**
Subscription confirmation.

## Chat Commands

**`/top [limit]`**
Show leaderboard with optional limit (default 10, max 50).

## Performance

- Redis read: < 50ms
- Materialized view: < 200ms
- Direct query: < 500ms
- WebSocket broadcast: < 100ms
```

#### Step 2.6: Load Testing (2h)

Create `backend/tests/load/test_leaderboard_performance.py`:

```python
"""Load tests for leaderboard performance."""
import asyncio
import time
from decimal import Decimal

async def test_concurrent_updates():
    """Test 100 concurrent score updates."""
    tasks = []

    for i in range(100):
        task = leaderboard_service.update_team_score(
            "test-session",
            f"team-{i % 10}",  # 10 teams
            Decimal(str(1000 + i))
        )
        tasks.append(task)

    start = time.time()
    await asyncio.gather(*tasks)
    duration = time.time() - start

    print(f"100 updates in {duration:.2f}s ({duration*10:.1f}ms avg)")
    assert duration < 1.0  # Should complete in < 1 second

async def test_leaderboard_read_performance():
    """Test read latency under load."""
    times = []

    for _ in range(1000):
        start = time.time()
        await leaderboard_service.get_leaderboard("test-session", 10)
        times.append(time.time() - start)

    avg = sum(times) / len(times)
    p95 = sorted(times)[int(len(times) * 0.95)]

    print(f"Avg: {avg*1000:.1f}ms, P95: {p95*1000:.1f}ms")
    assert p95 < 0.05  # P95 < 50ms
```

## Todo Checklist

### Week 1: Database & Core Service
- [ ] Create database migration files (001-004)
- [ ] Run migrations on PostgreSQL
- [ ] Implement PostgresClient with connection pooling
- [ ] Add PostgreSQL config to settings
- [ ] Create game_models.py data models
- [ ] Implement LeaderboardService core logic
- [ ] Add three-tier caching (Redis → Mat View → Direct)
- [ ] Implement background refresh task
- [ ] Update main.py startup/shutdown events
- [ ] Write unit tests for LeaderboardService

### Week 2: Socket.IO & Commands
- [ ] Create game_events.py Socket.IO handlers
- [ ] Implement leaderboard:get event
- [ ] Implement leaderboard:subscribe event
- [ ] Add broadcast_leaderboard_update function
- [ ] Update sio.py to register game events
- [ ] Extend CommandProcessor with /top command
- [ ] Add leaderboard message formatting
- [ ] Enhance RedisClient with sorted set methods
- [ ] Write integration tests
- [ ] Create API documentation
- [ ] Run load tests and validate performance

## Success Criteria

### Functional
- [ ] `/top` command returns top 10 teams with ranks
- [ ] Real-time updates broadcast to all session participants
- [ ] Team scores update within 5 seconds of P&L change
- [ ] Leaderboard persists across server restarts (materialized view)

### Performance
- [ ] Redis read latency < 50ms (P95)
- [ ] `/top` command response < 200ms (P95)
- [ ] Support 10 concurrent sessions with 100 teams total
- [ ] Materialized view refresh every 30 seconds
- [ ] WebSocket broadcast < 100ms latency

### Reliability
- [ ] Graceful fallback from Redis → Mat View → Direct Query
- [ ] No data loss during Redis flush
- [ ] Materialized view refresh doesn't block reads
- [ ] Connection pool handles 50+ concurrent queries

## Risk Assessment

### Technical Risks

**Risk: Redis Unavailable** (MEDIUM)
- Impact: Tier 1 cache down, fallback to Tier 2/3
- Mitigation: Materialized view ready, direct query fallback
- Recovery: Auto-reconnect, warm cache on restore

**Risk: Materialized View Refresh Locks** (LOW)
- Impact: View temporarily unreadable
- Mitigation: REFRESH CONCURRENTLY (no read locks)
- Recovery: Direct query fallback

**Risk: WebSocket Connection Loss** (MEDIUM)
- Impact: Clients miss real-time updates
- Mitigation: Client-side reconnection, state resync
- Recovery: Re-subscribe on reconnect

### Data Risks

**Risk: Race Condition on Score Updates** (LOW)
- Impact: Stale leaderboard data
- Mitigation: Redis atomic ZADD operations
- Recovery: 30s materialized view refresh corrects

**Risk: PostgreSQL Connection Pool Exhaustion** (LOW)
- Impact: Queries timeout
- Mitigation: Pool size 20, connection timeout 60s
- Recovery: Queue requests, scale pool if needed

## Security Considerations

- **Session Isolation:** Each leaderboard scoped by session_id
- **Input Validation:** Limit parameter clamped to 1-50
- **SQL Injection:** Parameterized queries via asyncpg
- **DoS Prevention:** Rate limit /top command (future)
- **Data Access:** User can only see their session's leaderboard

## Next Steps

After Phase 1 completion:

1. **Phase 2:** MT5 Integration Service (requires leaderboard for P&L updates)
2. **Phase 3:** Game Sessions & Teams (requires leaderboard for team scoring)
3. **Operations:** Monitor Redis memory usage, tune TTLs
4. **Optimization:** Consider Redis Cluster for scale beyond 10 sessions

## Unresolved Questions

1. **Materialized View Refresh Interval:** 30s optimal or adjust based on usage patterns?
2. **Redis Memory Management:** Max memory policy for leaderboard keys?
3. **Leaderboard History:** Should we archive historical leaderboards per session?
4. **Rank Notifications:** Send notification when team rank changes significantly?
5. **Leaderboard UI:** CLI-only or React dashboard component needed for MVP?
