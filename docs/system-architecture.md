# System Architecture - EV GamePad Multi-Player & Leaderboard Infrastructure

**Last Updated:** 2025-12-31
**Current Phase:** Phase 03 - Game Sessions & Teams Implementation (IN PROGRESS)
**Previous Phases:** Phase 01 (Leaderboard) COMPLETE, Phase 02 (MT5 Integration) COMPLETE

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
│  │  /game     - Sessions, teams, leaderboard (Phase 03)          │  │
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

## Phase 03: Game Sessions & Team Management

**Status:** IN PROGRESS (2025-12-31)
**Components:** GameService, TeamService, game_events.py

### Key Features

#### 1. Game Session Lifecycle

**States:** `waiting` → `active` → `completed`

```
/csv command (create_session)
  ├─ Creator starts new game session
  ├─ Session name must be unique
  ├─ Creator joins as first member
  └─ Status: waiting (awaiting more players)

User joins with /jsv command (join_session)
  ├─ Auto-assign to team via round-robin
  ├─ Allocate MT5 account from pool
  ├─ Check if min 4 players reached
  │
  └─ If >= 4 players:
      └─ Auto-start session (status = active)
         └─ Broadcast session:started event

/close command (close_session)
  ├─ Creator only can close
  ├─ Mark status = completed
  ├─ End time = NOW()
  └─ Release all MT5 accounts
```

**Command Handlers:** `game_events.py`
- `game:create_session` - /csv command
- `game:join_session` - /jsv command
- `game:leave_session` - Player cleanup
- `session:info` - Get session details

#### 2. Round-Robin Team Assignment

**Algorithm:**
```python
async def auto_assign_team(session_id, user_id, username, max_team_size):
    # Find team with fewest members
    team = await fetch("""
        SELECT team_id, team_name, COUNT(members) as member_count
        FROM teams
        WHERE session_id = $1
        GROUP BY team_id
        ORDER BY member_count ASC
        LIMIT 1
    """)

    if team.member_count < max_team_size:
        # Add to existing team
        return add_to_team(team.team_id, user_id)
    else:
        # Create new team with letter suffix (A, B, C...)
        team_name = f"{session_name}-{letter}"
        return create_team(session_id, team_name, user_id)
```

**Key Constraints:**
- Teams balanced by member count
- Max team size: 4-6 players (configurable per session)
- Team naming: `SessionName-A`, `SessionName-B`, etc.
- No duplicate team names per session

#### 3. MT5 Account Allocation on Join

**Flow:**
```
User joins session
  ↓
game:join_session handler
  ├─ Call mt5_integration_service.allocate_account(user_id, session_id)
  │  ├─ Lock available account with FOR UPDATE SKIP LOCKED
  │  ├─ Decrypt password
  │  ├─ Return MT5AccountAllocation
  │  │
  │  └─ If pool exhausted:
  │      └─ Return None (warn user, continue without account)
  │
  ├─ Emit game:session_joined to client
  └─ If emit fails: Release account (prevent leak)
```

**Critical Section:** Account release protection
- Try/catch wraps emit operation
- On emit failure: Release account to prevent leak
- Ensures pool consistency even on Socket.IO failures

**Status Tracking:** user_account_allocations table
- user_id → session_id → account_number mapping
- Linked to game_sessions for cleanup

#### 4. Auto-Start at Min Players (4)

**Trigger:**
```python
async def _check_start_session(session_id):
    player_count = await fetch("""
        SELECT COUNT(DISTINCT tm.user_id)
        FROM team_members tm
        JOIN teams t ON tm.team_id = t.team_id
        WHERE t.session_id = $1
    """)

    if player_count >= 4:
        # Transition: waiting → active
        await execute("""
            UPDATE game_sessions
            SET status = 'active', start_time = NOW()
            WHERE session_id = $1 AND status = 'waiting'
        """)

        # Broadcast start event
        await broadcast_session_start(session_id)
```

**Event:** `session:started` broadcast
- Room: `session:{session_id}`
- Payload: `{"message": "Game started! Trading is now active."}`

#### 5. Session Creator Controls

**Creator Privileges:**
- Can close session (mark completed)
- Only creator can execute /close command
- Other actions (view info, join teams) available to all

**Close Session (Future):**
```
/close command
  ├─ Verify user_id == creator_id
  ├─ Update status = completed, end_time = NOW()
  ├─ Release all MT5 accounts in session
  └─ Broadcast session:completed
```

### Database Schema (Phase 03)

**game_sessions**
```sql
session_id (UUID PK)
name (VARCHAR UNIQUE)
creator_id (VARCHAR)  -- User who created
status (VARCHAR)      -- waiting, active, completed
start_time, end_time (TIMESTAMP)
max_team_size (INT, default 6)
created_at (TIMESTAMP)
```

**teams**
```sql
team_id (UUID PK)
session_id (UUID FK)
team_name (VARCHAR)
created_at (TIMESTAMP)
```

**team_members**
```sql
member_id (UUID PK)
team_id (UUID FK)
user_id (VARCHAR)
username (VARCHAR)
joined_at (TIMESTAMP)
```

**user_account_allocations** (Phase 03 NEW)
```sql
allocation_id (UUID PK)
user_id (VARCHAR)
session_id (UUID FK)
account_number (INT)
allocated_at (TIMESTAMP)
released_at (TIMESTAMP)
```

### Socket.IO Events (Phase 03)

#### Create Session: `/csv` command
```json
← Request (client)
{
  "session_name": "MyGameSession",
  "user_id": "user_123",
  "max_team_size": 6
}

→ Response (server)
{
  "success": true,
  "session_id": "uuid",
  "account_allocated": {
    "account_number": 12345,
    "broker_server": "BrokerDemo"
  }
}
```

#### Join Session: `/jsv` command
```json
← Request (client)
{
  "session_name": "MyGameSession",
  "user_id": "user_456",
  "username": "Player456"
}

→ Response (server)
{
  "success": true,
  "session_id": "uuid",
  "team_id": "uuid",
  "team_name": "MyGameSession-A",
  "account_allocated": {
    "account_number": 12346,
    "broker_server": "BrokerDemo"
  }
}
```

#### Session Auto-Start
```json
→ Broadcast (when 4+ players join)
{
  "event": "session:started",
  "room": "session:{session_id}",
  "data": {
    "session_id": "uuid",
    "message": "Game started! Trading is now active."
  }
}
```

#### Session Info
```json
← Request
{
  "session_name": "MyGameSession"
}

→ Response
{
  "session": {
    "session_id": "uuid",
    "name": "MyGameSession",
    "status": "active",
    "creator_id": "user_123",
    "max_team_size": 6
  },
  "teams": [
    {"team_id": "id", "team_name": "MyGameSession-A"},
    {"team_id": "id", "team_name": "MyGameSession-B"}
  ],
  "player_count": 8
}
```

### Service Architecture

#### GameService (NEW)
**Responsibility:** Session lifecycle management
```python
class GameService:
    async create_session(name, creator_id, max_team_size) → GameSession
    async join_session(name, user_id, username) → {session, team, account_allocated}
    async leave_session(user_id) → None
    async get_session_by_name(name) → GameSession | None
    async complete_session(session_id) → None
    async _check_start_session(session_id) → None
```

**Key Behavior:**
- Validates unique session name
- Calls TeamService for auto-assignment
- Calls MT5IntegrationService for account allocation
- Auto-starts session if 4+ players

#### TeamService (NEW)
**Responsibility:** Team formation and member management
```python
class TeamService:
    async auto_assign_team(session_id, user_id, username, max_team_size) → Team
    async calculate_team_pnl(team_id) → Decimal
    async get_team_members(team_id) → List[TeamMember]
```

**Round-Robin Logic:**
- Finds team with fewest members
- Creates new team if all full
- Names teams alphabetically (Session-A, Session-B, etc.)

#### MT5IntegrationService (UPDATED Phase 03)
**New Methods:**
```python
async allocate_account(user_id, session_id) → MT5AccountAllocation | None
async release_account(user_id) → bool
```

**Changes from Phase 02:**
- Session-aware account tracking
- Bulk release on session close
- Account pool exhaustion handling

### Data Flow: Session Join

```
1. Client sends /jsv MyGameSession
   ↓
2. game:join_session handler receives
   ├─ Validates session exists
   ├─ Checks session not completed
   │
   └─ Calls GameService.join_session()
       ├─ TeamService.auto_assign_team()
       │  ├─ Finds team with fewest members
       │  └─ Adds user to team
       │
       ├─ MT5IntegrationService.allocate_account()
       │  ├─ Locks available account
       │  └─ Returns credentials
       │
       └─ _check_start_session()
           ├─ If 4+ players: status = active
           └─ Broadcast session:started
   │
3. Emit game:session_joined to client
   ├─ session_id
   ├─ team_id, team_name
   └─ MT5 account details

Total Latency: 50-200ms
```

### Performance Characteristics

**Session Operations:**
| Operation | Typical | 95th Percentile |
|-----------|---------|-----------------|
| Create session | 10-20ms | 50ms |
| Join session | 50-100ms | 200ms |
| Get session info | 20-50ms | 100ms |
| Auto-assign team | 5-15ms | 30ms |
| Account allocate | 10-30ms | 80ms |

**Scalability:**
- Max concurrent sessions: Limited by team count (50+ sessions × 2 teams × 6 players = 600+ users)
- Join rate: Can handle 10 joins/sec with team balancing
- Team queries optimized with GROUP BY + HAVING

### Error Handling

**Session Not Found:**
```
User tries to join non-existent session
  → Emit error: "Session '{name}' not found"
  → User can retry or create new session
```

**Session Completed:**
```
User tries to join completed session
  → Emit error: "Session already completed"
  → User directed to active sessions
```

**Account Pool Exhausted:**
```
MT5IntegrationService.allocate_account() returns None
  → Emit warning: "No MT5 account available - pool exhausted"
  → User can still join session without account
  → Account becomes available later when other user leaves
```

**Account Leak Prevention:**
```
try:
    emit("game:session_joined", {...})
except Exception:
    # CRITICAL: Release account on emit failure
    await mt5_integration_service.release_account(user_id)
    raise
```

### Testing Strategy (Phase 03)

**test_game_session_flow.py**
- Create → join (1 user, 4 users) → verify team assignment
- Verify auto-start at 4 players
- Verify account allocation + release
- Verify round-robin distribution

**Key Test Cases:**
1. Create session, verify unique name constraint
2. Join session, verify auto-team assignment
3. Join with 4+ players, verify auto-start
4. Leave session, verify account release
5. Account pool exhaustion, verify graceful degradation

---

**Document Status:**
- Status: Active
- Last Updated: 2025-12-31
- Owner: Architecture Team
- Visibility: Internal Team
