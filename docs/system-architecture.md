# System Architecture - EV GamePad Multi-Player & Leaderboard Infrastructure

**Last Updated:** 2025-12-31
**Current Phase:** Phase 01 - Leaderboard Infrastructure (COMPLETE)
**Next Phase:** Phase 02 - Game Control Integration

---

## High-Level System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Client Application                            │
│  (Web/Mobile - Socket.IO Client)                                      │
└────────────┬─────────────────────────────────────────────────────────┘
             │
             │ WebSocket (Socket.IO)
             ↓
┌────────────────────────────────────────────────────────────────────────┐
│                    EV GamePad Backend Server                           │
│                     (FastAPI + Socket.IO)                             │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Socket.IO Namespaces & Events                                  │  │
│  │                                                                 │  │
│  │  /trading - Order placement, position management              │  │
│  │  /advisor  - Technical analysis, recommendations              │  │
│  │  /game     - Leaderboard, session management (Phase 01 NEW)   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              │                                         │
│  ┌───────────────────────────┼───────────────────────────────────┐   │
│  │                           ↓                                   │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │ Processors (Orchestration)                          │    │   │
│  │  │                                                      │    │   │
│  │  │ CommandProcessor  - MT5 order routing              │    │   │
│  │  │ AdvisorProcessor  - Technical analysis pipeline    │    │   │
│  │  │ GameProcessor     - Leaderboard logic (Phase 01)   │    │   │
│  │  └───────────┬────────────┬─────────────────────┬──────┘    │   │
│  │              │            │                     │           │   │
│  │    ┌─────────▼─┐  ┌──────▼──────┐  ┌───────────▼──────┐    │   │
│  │    │ MT5 Bridge│  │   Advisor   │  │ Leaderboard      │    │   │
│  │    │           │  │   Services  │  │ Services         │    │   │
│  │    └─────────┬─┘  └──────┬──────┘  └───────────┬──────┘    │   │
│  └────────────────────────────┼──────────────────────────────┘   │
│                               │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐   │
│  │                           ↓                               │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │ Data & Cache Layer                               │    │   │
│  │  │                                                   │    │   │
│  │  │ PostgreSQL        Redis          MT5 Terminal    │    │   │
│  │  │ (Persistent)      (Hot Cache)    (Live Data)     │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  └────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 01: Leaderboard Infrastructure Components

### 1. Data Model Layer

#### Game Session & Team Structure
```python
GameSession
├─ session_id (UUID)
├─ name (unique identifier)
├─ creator_id (organizer)
├─ status (waiting → active → completed)
└─ max_team_size (6 members typical)

Team
├─ team_id (UUID)
├─ session_id (FK)
├─ team_name
└─ created_at

TeamMember
├─ member_id (UUID)
├─ team_id (FK)
├─ user_id (application user)
├─ username
└─ joined_at
```

#### Trading Position Tracking
```python
Position
├─ position_id (UUID)
├─ session_id (FK)
├─ user_id (trader)
├─ ticket (MT5 position ID)
├─ symbol (e.g., XAUUSD)
├─ type (buy/sell)
├─ volume, open_price, close_price
├─ pnl (computed at close)
├─ opened_at, closed_at (timestamps)
└─ sl, tp (stop loss, take profit)
```

#### Leaderboard Response
```python
LeaderboardEntry
├─ rank (1, 2, 3, ...)
├─ team_id
├─ team_name
├─ total_pnl (sum of member positions)
├─ team_size (member count)

LeaderboardResponse
├─ rankings (List[LeaderboardEntry])
├─ my_rank (Optional[LeaderboardEntry])
└─ total_teams (int)
```

---

### 2. Three-Tier Caching Architecture

#### Tier 1: Redis Sorted Sets (Real-Time Cache)

**Purpose:** Sub-50ms leaderboard reads for hot sessions
**Technology:** Redis sorted sets with scores = P&L values
**Key Format:** `leaderboard:{session_id}`
**TTL:** 1 hour (3600s)
**Complexity:** O(log n) for all operations

**Operations:**
```python
# Update a team's P&L
zadd(key="leaderboard:session_uuid", mapping={"team_id": 2500.00})

# Get top 10 teams with scores
zrevrange(key, 0, 9, withscores=True)
  → [("team_1", 5000.0), ("team_2", 4500.0), ...]

# Get team's rank (0-indexed)
zrevrank(key, "team_id")

# Get team's score
zscore(key, "team_id")

# Set TTL
expire(key, 3600)
```

**Cache Invalidation:**
- Immediate: zadd on P&L update
- Expiration: 1-hour TTL
- Warm-up: From Tier 2 on fallback

**Failure Mode:** Returns empty/null → Falls back to Tier 2

---

#### Tier 2: PostgreSQL Materialized View (Consistency Cache)

**Purpose:** Guaranteed fresh data within 30 seconds, survives Redis failure
**Technology:** Materialized view, refreshed every 30 seconds
**Refresh Strategy:** Non-concurrent refresh (maintains index)
**Time-to-Freshness:** 0-30 seconds

**Schema:**
```sql
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
LEFT JOIN positions p ON tm.user_id = p.user_id
    AND p.session_id = t.session_id
    AND p.closed_at IS NULL
GROUP BY t.session_id, t.team_id, t.team_name;
```

**Indexes:**
- Primary: `(session_id, team_id)` - Unique
- Secondary: `(session_id, total_pnl DESC)` - For ranking

**Refresh Task:**
```python
class LeaderboardRefreshTask:
    async def _refresh_view():
        await postgres_client.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY team_leaderboard"
        )
```

**Query Path:** When Tier 1 miss
```sql
SELECT team_id, team_name, total_pnl, team_size
FROM team_leaderboard
WHERE session_id = $1
ORDER BY total_pnl DESC
LIMIT $2
```

**Performance:** 100-300ms (includes warm-up to Redis)

---

#### Tier 3: Direct Query (Accuracy Guarantee)

**Purpose:** Ultimate fallback when Tiers 1-2 unavailable
**Technology:** Real-time aggregation from source tables
**Use Case:** Materialized view corruption, critical accuracy needed
**Performance Impact:** 500-1000ms (full table scan + join + aggregate)

**Query Path:**
```sql
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
```

**Optimization Indexes:**
- `teams(session_id)`
- `team_members(team_id)`
- `positions(session_id, user_id, closed_at)`

---

### 3. LeaderboardService - Core Orchestration

**Responsibility:** Implement three-tier logic, abstract tiers from callers

```python
class LeaderboardService:

    async def get_leaderboard(session_id: str, limit: int = 10):
        """Main entry point - implements three-tier fallback."""

        # Tier 1: Try Redis
        rankings = await self._get_from_redis(session_id, limit)
        if rankings:
            return rankings  # Cache hit, fast path

        # Tier 2: Try Materialized View
        try:
            rankings = await self._get_from_materialized_view(session_id, limit)
            if rankings:
                await self._warm_redis_cache(session_id, rankings)
                return rankings  # Warm Tier 1, return
        except Exception as e:
            logger.warning(f"Materialized view failed: {e}")

        # Tier 3: Direct Query (guaranteed)
        return await self._get_from_direct_query(session_id, limit)

    async def update_team_score(session_id: str, team_id: str, pnl: Decimal):
        """Update Redis immediately on P&L change."""
        key = f"leaderboard:{session_id}"
        await self.redis_client.zadd(key, {team_id: float(pnl)})
        await self.redis_client.expire(key, 3600)  # Refresh TTL

    async def get_my_rank(session_id: str, user_id: str):
        """Get user's team rank - uses Redis primarily."""
        team_id = await self._get_user_team(session_id, user_id)
        if not team_id:
            return None

        # Try Redis first (fast path)
        key = f"leaderboard:{session_id}"
        rank = await self.redis_client.zrevrank(key, team_id)
        score = await self.redis_client.zscore(key, team_id)

        if rank is not None:
            return LeaderboardEntry(
                rank=rank + 1,  # Convert 0-indexed to 1-indexed
                team_id=team_id,
                team_name=await self._get_team_name(team_id),
                total_pnl=Decimal(str(score)),
                team_size=await self._get_team_size(team_id)
            )

        # Fallback to DB
        return await self._get_rank_from_db(session_id, team_id)
```

---

### 4. Socket.IO Event Handlers (Game Events)

#### Event: `/top` command (Get Leaderboard)

**Client → Server:**
```json
emit("leaderboard:get", {
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "limit": 10,
  "user_id": "user_123"
})
```

**Server → Client:**
```json
emit("leaderboard:result", {
  "rankings": [
    {
      "rank": 1,
      "team_id": "uuid",
      "team_name": "Team Alpha",
      "total_pnl": 5000.00,
      "team_size": 3
    },
    {
      "rank": 2,
      "team_id": "uuid",
      "team_name": "Team Beta",
      "total_pnl": 4500.00,
      "team_size": 2
    }
  ],
  "my_rank": {
    "rank": 5,
    "team_id": "my_uuid",
    "team_name": "My Team",
    "total_pnl": 2000.00,
    "team_size": 1
  },
  "total_teams": 8
})
```

#### Event: Real-Time Updates (Subscribe)

**Client → Server (Subscribe):**
```json
emit("leaderboard:subscribe", {
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
})
```

**Server → Client (Broadcast on rank change):**
```json
emit("leaderboard:update", {
  "session_id": "550e8400...",
  "team_id": "team_id_uuid",
  "new_pnl": 5500.00,
  "new_rank": 1,
  "message": "Team Alpha is now #1!"
})
```

**Implementation:**
```python
@sio.on("leaderboard:subscribe")
async def handle_subscribe_leaderboard(sid, data):
    session_id = data.get("session_id")
    sio.enter_room(sid, f"session:{session_id}")  # Room-scoped

async def broadcast_leaderboard_update(session_id: str, team_id: str, new_pnl: Decimal):
    """Called after P&L change - broadcasts to all in session."""
    await sio.emit(
        "leaderboard:update",
        {...},
        room=f"session:{session_id}"  # Only this session's clients
    )
```

---

### 5. Database Integration

#### PostgreSQL Connection Pool

```python
class PostgresClient:

    async def initialize(self):
        """Create async connection pool."""
        self.pool = await asyncpg.create_pool(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            database=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            min_size=5,       # Minimum connections
            max_size=20,      # Maximum connections
            command_timeout=60,
        )

    async def fetch(self, query: str, *args):
        """Fetch multiple rows."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch single row."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch single value."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute(self, query: str, *args):
        """Execute without returning results."""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
```

**Pool Sizing:** 5-20 connections handles 50-100 concurrent users

#### Migration Files

- `001_create_game_sessions.sql` - Session management
- `002_create_teams.sql` - Team registry
- `003_create_team_members.sql` - Membership tracking
- `004_create_positions_table.sql` - Position tracking for P&L
- `005_create_materialized_view.sql` - Leaderboard Tier 2

---

### 6. Background Task: Leaderboard Refresh

**Purpose:** Keep materialized view fresh (< 30s staleness)

```python
class LeaderboardRefreshTask:

    async def start(self):
        """Background loop - runs continuously."""
        self.running = True

        while self.running:
            try:
                await self._refresh_view()
                await asyncio.sleep(30)  # Every 30 seconds
            except Exception as e:
                logger.error(f"Refresh failed: {e}")
                await asyncio.sleep(30)  # Still retry after delay

    async def _refresh_view(self):
        """Refresh materialized view concurrently."""
        await postgres_client.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY team_leaderboard"
        )
```

**Lifecycle in main.py:**
```python
# Startup
leaderboard_refresh_task = LeaderboardRefreshTask()
asyncio.create_task(leaderboard_refresh_task.start())

# Shutdown
await leaderboard_refresh_task.stop()
```

---

## Data Flow: Complete P&L Update Lifecycle

```
1. Trading Position Closes in MT5 Terminal
   └─ Ticket #12345 XAUUSD sold at 2050.00

2. MT5 Order Fill Event
   └─ TradingOperations detects position close

3. CommandProcessor.process_close_position()
   ├─ Calculate P&L = (close_price - open_price) * volume
   └─ Store in positions table
       position_id: uuid
       user_id: trader_1
       session_id: session_uuid
       pnl: 250.00  ← User's P&L
       closed_at: NOW()

4. LeaderboardService.update_team_score()
   ├─ Find team by user_id + session_id
   ├─ Aggregate team P&L
   │  SELECT SUM(pnl) FROM positions
   │  WHERE session_id = X AND user_id IN team_members
   └─ Update Redis (Tier 1)
       zadd("leaderboard:session_uuid", {"team_5": 2500.00})
       expire(key, 3600)  ← Refresh TTL

5. broadcast_leaderboard_update()
   ├─ Get updated rankings
   ├─ Determine new rank
   └─ Emit leaderboard:update event
       room: "session:session_uuid"  ← All clients in session
       message: "Team Omega is now #1!"

6. Client Receives Update
   └─ UI refreshes leaderboard display
```

**Total Latency:** 100-200ms (Redis-dominated)

---

## Integration with Technical Analysis

The leaderboard infrastructure coexists with the advisor module:

```
Socket.IO Events:
├─ /trading namespace
│  ├─ buy_market, sell_market, close_position
│  └─ [Triggers P&L updates → Leaderboard]
│
├─ /advisor namespace
│  ├─ technical_summary
│  ├─ multi_timeframe
│  └─ recommendation
│
└─ /game namespace (Phase 01 NEW)
   ├─ leaderboard:get
   ├─ leaderboard:subscribe
   └─ [Broadcasts: leaderboard:update]
```

**P&L Path:**
```
Position Close (MT5)
  → CommandProcessor
  → TradingOperations
  → positions table
  → LeaderboardService
  → Redis + MaterializedView
  → broadcast_leaderboard_update()
  → Socket.IO emit to session
```

---

## Configuration & Deployment

### Environment Setup (Phase 01)

```bash
# PostgreSQL
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=evgamepad
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=<secret>

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379

# MT5
export MT5_HOST=localhost
export MT5_PORT=9090
```

### Startup Sequence (main.py)

```python
@app.on_event("startup")
async def startup_event():
    # 1. Initialize PostgreSQL pool
    await postgres_client.initialize()

    # 2. Initialize Redis client
    redis_client = RedisClient(config.REDIS_HOST, config.REDIS_PORT)
    await redis_client.connect()

    # 3. Inject Redis into leaderboard service
    leaderboard_service.redis_client = redis_client

    # 4. Start background refresh task
    leaderboard_refresh_task = LeaderboardRefreshTask()
    asyncio.create_task(leaderboard_refresh_task.start())

    # 5. Register Socket.IO event handlers
    # (game_events.py imported at module level)

@app.on_event("shutdown")
async def shutdown_event():
    await postgres_client.close()
    await redis_client.disconnect()
    await leaderboard_refresh_task.stop()
```

---

## Performance Characteristics

### Response Time SLOs

| Operation | Target | Typical | 95th Percentile |
|-----------|--------|---------|-----------------|
| Get top 10 (Redis hit) | < 50ms | 25-40ms | 60ms |
| Get top 10 (MatView hit) | < 300ms | 100-200ms | 350ms |
| Get top 10 (Direct query) | < 1s | 500-800ms | 1100ms |
| Update score | < 50ms | 10-30ms | 80ms |
| Get my rank | < 100ms | 30-60ms | 120ms |
| Broadcast to 100 clients | < 500ms | 200-300ms | 600ms |

### Scalability Limits (Single Node)

**PostgreSQL:**
- Max concurrent queries: 20 (pool size)
- Max sessions: 1000 (without pooling limits)
- Query time: < 500ms per user for top 10

**Redis:**
- Sorted set members: Millions
- Leaderboard operations: O(log n)
- Max throughput: 100k ops/sec

**Memory Usage:**
- PostgreSQL pool: ~50MB
- Redis (per session): ~1KB × teams
- Materialized view: ~10MB

---

## Error Handling & Resilience

### Cache Failures (Graceful Degradation)

```
Tier 1 (Redis) fails
  ↓ [Fallback to Tier 2]
Tier 2 (MatView) fails
  ↓ [Fallback to Tier 3]
Tier 3 (Direct query) fails
  ↓ [Return error to client with retry hint]
```

### Database Connection Loss

```python
try:
    result = await postgres_client.fetch(query, args)
except asyncpg.exceptions.PostgresError as e:
    logger.error(f"Database error: {e}")
    # Return 500 with retry hint to client
    await sio.emit("error", {
        "code": "DATABASE_ERROR",
        "message": "Service temporarily unavailable",
        "retry_after": 5
    }, room=sid)
```

### Redis Connection Loss

```python
if not self._client:
    logger.warning("Redis unavailable, falling back to DB")
    return await self._get_from_materialized_view(...)
```

---

## Monitoring & Observability

### Key Metrics

1. **Leaderboard Cache Hit Rate**
   ```
   (Redis hits) / (total requests)
   Target: > 70%
   ```

2. **P&L Update Latency**
   ```
   Time from position close → broadcast
   Target: < 200ms
   ```

3. **Materialized View Staleness**
   ```
   NOW() - computed_at
   Target: < 30s
   ```

4. **PostgreSQL Connection Pool Utilization**
   ```
   Active connections / pool size
   Target: < 80%
   ```

### Logging

```python
logger.info(f"Leaderboard sent to {sid} for session {session_id}")
logger.debug(f"Redis cache hit for session {session_id}")
logger.debug(f"Materialized view hit for session {session_id}")
logger.debug(f"Direct query for session {session_id}")
logger.error(f"Leaderboard refresh failed: {e}")
```

---

## Future Enhancements (Phase 02+)

1. **Seasonal Leaderboards**
   - Reset ranks weekly/monthly
   - Archive historical rankings

2. **Private Leaderboards**
   - Within tournament brackets
   - Friend-only competitions

3. **P&L Multipliers**
   - Bonus scaling by team size
   - Difficulty modifiers

4. **Streak Tracking**
   - Win/loss streaks
   - Consecutive top 3 finishes

5. **Predictive Caching**
   - Pre-warm popular sessions
   - Cache popular symbol/timeframe combinations

---

**Document Status:**
- Status: Active
- Last Updated: 2025-12-31
- Owner: Architecture Team
- Visibility: Internal Team
