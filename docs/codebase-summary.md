# EV GamePad - Codebase Summary

**Last Updated:** 2025-12-31
**Version:** Phase 01 - Leaderboard Infrastructure
**Token Count:** 70,718 tokens (70% of context)
**Total Files:** 60 files

---

## Project Overview

EV GamePad combines real-time MT5 trading with multiplayer game mechanics and AI-powered analysis. Phase 01 introduces the leaderboard infrastructure supporting multi-player trading competitions with real-time rankings.

---

## Directory Structure & Module Breakdown

### Core Backend (`/backend/app/`)

#### **Database Layer** (`app/database/`)
- `postgres_client.py` - Async PostgreSQL connection pool (NEW Phase 01)
- `redis_client.py` - Redis cache client with sorted set operations (UPDATED Phase 01)

**Phase 01 Additions:**
- PostgreSQL support with asyncpg
- Redis sorted set operations: zadd, zrevrank, zscore, zrevrange, zcard, expire
- 1-hour TTL for leaderboard keys

#### **Data Models** (`app/models/`)
- `game_models.py` - Game session, team, leaderboard models (NEW Phase 01)
- `advisor_models.py` - Technical analysis response models
- `user_profile.py` - User preferences and risk profiles
- `responses.py` - Standard error/success response structures

**Phase 01 Models:**
```python
GameSession - session_id, status, creator_id, max_team_size
Team - team_id, team_name, total_pnl
TeamMember - member_id, user_id, username
LeaderboardEntry - rank, team_id, team_name, total_pnl, team_size
LeaderboardResponse - rankings, my_rank, total_teams
```

#### **Services** (`app/services/`)
- `leaderboard_service.py` - Three-tier leaderboard (Redis → MaterializedView → Direct) (NEW Phase 01)

**Core Responsibility:** Real-time rank calculations with fallback caching strategy.

#### **Event Handlers** (`app/events/`)
- `game_events.py` - Socket.IO leaderboard events (NEW Phase 01)
- `advisor_events.py` - Technical analysis events
- `trading_events.py` - Trading order/position events

**Phase 01 Events:**
```
leaderboard:get - Request rankings for session
leaderboard:result - Response with rankings
leaderboard:subscribe - Subscribe to real-time updates
leaderboard:update - Broadcast rank change
```

#### **Background Tasks** (`app/tasks/`)
- `leaderboard_refresh_task.py` - Materialized view refresh every 30s (NEW Phase 01)
- `cleanup_task.py` - Session/position cleanup

#### **AI Advisor** (`app/advisor/`)
- `technical_analyzer.py` - 10 technical indicators (SMA, EMA, RSI, MACD, etc.)
- `data_fetcher.py` - MT5 OHLCV data retrieval
- `pattern_detector.py` - Candlestick pattern recognition
- `support_resistance.py` - S/R level calculation
- `risk_analyzer.py` - Risk management calculations
- `ai_summarizer.py` - LLM integration (Claude/DeepSeek)
- `recommendation_engine.py` - Final recommendation aggregation

#### **Processors** (`app/processors/`)
- `advisor_processor.py` - Technical analysis orchestration
- `command_processor.py` - MT5 command routing (UPDATED Phase 01 for /top)

#### **MT5 Integration** (`app/mt5/`)
- `connection_manager.py` - MT5 terminal connection pooling
- `trading_operations.py` - Place orders, close positions
- `circuit_breaker.py` - Fault tolerance for MT5 operations
- `error_handler.py` - Error classification and recovery

#### **Configuration & Infrastructure**
- `config.py` - Environment configuration
- `logging_config.py` - Structured logging setup
- `main.py` - FastAPI + Socket.IO startup (UPDATED Phase 01)
- `sio.py` - Socket.IO server initialization
- `session_manager.py` - User session tracking
- `validation.py` - Input validation utilities

---

## Database Schema (Phase 01)

### Tables

**game_sessions**
```
session_id (UUID PK)
name (VARCHAR UNIQUE)
creator_id (VARCHAR)
status (VARCHAR) - waiting, active, completed
start_time, end_time (TIMESTAMP)
max_team_size (INT)
created_at (TIMESTAMP)
```

**teams**
```
team_id (UUID PK)
session_id (UUID FK → game_sessions)
team_name (VARCHAR)
created_at (TIMESTAMP)
```

**team_members**
```
member_id (UUID PK)
team_id (UUID FK → teams)
user_id (VARCHAR)
username (VARCHAR)
joined_at (TIMESTAMP)
```

**positions** (NEW Phase 01)
```
position_id (UUID PK)
session_id (UUID FK)
user_id (VARCHAR)
ticket (BIGINT)
symbol (VARCHAR)
type (VARCHAR) - buy, sell
volume (DECIMAL)
open_price, close_price (DECIMAL)
sl, tp (DECIMAL)
pnl (DECIMAL)
opened_at, closed_at (TIMESTAMP)
```

### Materialized View (NEW Phase 01)

**team_leaderboard** - Refreshed every 30 seconds
```
session_id, team_id, team_name
total_pnl (SUM of open positions P&L)
team_size (COUNT of distinct members)
computed_at (TIMESTAMP)
```

---

## Three-Tier Leaderboard Caching Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Client Request (/top command)                          │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  Tier 1: Redis      │ ← Fastest (< 50ms)
        │  Sorted Sets        │   O(log n) lookup
        │ leaderboard:{sid}   │   1-hour TTL
        └──────────┬──────────┘
                   │ (miss)
        ┌──────────▼──────────────────┐
        │ Tier 2: Materialized View   │ ← Medium (100-300ms)
        │ team_leaderboard view       │   Fresh within 30s
        │ Refreshed every 30 seconds  │
        └──────────┬──────────────────┘
                   │ (miss)
        ┌──────────▼──────────────────┐
        │ Tier 3: Direct Query        │ ← Slow (500-1000ms)
        │ Live aggregate from tables  │   Always accurate
        │ SUM(pnl) per team           │
        └──────────┬──────────────────┘
                   │
        ┌──────────▼──────────┐
        │ Response to Client  │
        └─────────────────────┘
```

**Cache Invalidation Strategy:**
- P&L update → Update Redis sorted set immediately
- Refresh task → Refresh materialized view every 30s
- Subscribe room → Broadcast updates to session subscribers

---

## Socket.IO Events (Game & Leaderboard)

### Leaderboard Events

**leaderboard:get** - Client requests rankings
```json
{
  "session_id": "uuid",
  "limit": 10,
  "user_id": "user_identifier"
}
```

**leaderboard:result** - Response with rankings
```json
{
  "rankings": [
    {"rank": 1, "team_id": "id", "team_name": "Alpha", "total_pnl": 2500.00, "team_size": 3}
  ],
  "my_rank": {"rank": 3, "team_id": "id", "team_name": "My Team", ...},
  "total_teams": 5
}
```

**leaderboard:subscribe** - Real-time updates
```json
{"session_id": "uuid"}
```

**leaderboard:update** - Broadcast rank change
```json
{
  "session_id": "uuid",
  "team_id": "id",
  "new_pnl": 2500.00,
  "new_rank": 1,
  "message": "Team Alpha is now #1!"
}
```

---

## /top Command Flow

```
Client: /top [limit] [session_id]
  ↓
CommandProcessor.process_top_command()
  ├─ Validate session_id
  ├─ Parse limit (default 10, max 100)
  │
  └─ LeaderboardService.get_leaderboard(session_id, limit)
      ├─ Try Redis (Tier 1) → O(log n) sorted set
      ├─ Try MaterializedView (Tier 2) → Warm Redis
      └─ Fall back to Direct Query (Tier 3)
  │
  ├─ LeaderboardService.get_my_rank(session_id, user_id)
  ├─ LeaderboardService.get_total_teams(session_id)
  │
  └─ Emit leaderboard:result
      {rankings, my_rank, total_teams}
```

**Performance Targets:**
- Cache hit: 20-50ms
- Cache miss: 200-800ms

---

## Codebase Statistics

### File Distribution

**By Module:**
- Advisor (technical analysis): 9 files, ~25%
- MT5 Integration: 4 files, ~12%
- Database: 2 files, ~8%
- Game/Leaderboard: 5 files, ~15% (Phase 01 NEW)
- Configuration: 6 files, ~18%
- Other: ~20 files, ~22%

**Top Modified Files:**
1. `app/advisor/technical_analyzer.py` - 2,892 tokens
2. `tests/test_technical_analyzer.py` - 3,076 tokens
3. `app/models/advisor_models.py` - ~1,500 tokens
4. `app/services/leaderboard_service.py` - ~1,800 tokens (Phase 01)
5. `app/database/postgres_client.py` - ~300 tokens (Phase 01)

**Test Coverage:**
- `tests/test_technical_analyzer.py` - Indicator validation
- `tests/test_volume_validator.py` - Volume analysis
- Integration tests for leaderboard (Phase 01)

---

## Key Dependencies

### Python Packages
- **FastAPI** - Web framework
- **python-socketio** - WebSocket communication
- **asyncpg** - PostgreSQL async driver (NEW Phase 01)
- **redis** - Redis async client (UPDATED Phase 01)
- **pandas-ta** - Technical analysis indicators
- **pandas** - Data manipulation
- **MetaTrader5** - MT5 terminal API

### External Services
- **MT5 Terminal** - Price data source
- **PostgreSQL** - User/game data (NEW Phase 01)
- **Redis** - Real-time leaderboard cache (UPDATED Phase 01)
- **TwelveData API** - Volume validation
- **Claude API** - AI recommendations
- **DeepSeek API** - Fallback summarization

---

## Configuration

### Environment Variables (Phase 01)

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=evgamepad
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<secret>

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# MT5
MT5_HOST=localhost
MT5_PORT=9090

# API Keys
ANTHROPIC_API_KEY=<secret>
DEEPSEEK_API_KEY=<secret>
TWELVEDATA_API_KEY=<secret>
```

---

## Data Flow: Complete P&L Update

```
1. Trading Position Closed in MT5
   ↓
2. CommandProcessor detects close
   ├─ Calculate P&L
   ├─ Store in positions table
   │
   └─ LeaderboardService.update_team_score()
       ├─ Update Redis sorted set (immediate)
       └─ Expire key in 1 hour
   │
3. game_events.broadcast_leaderboard_update()
   ├─ Get updated rankings
   ├─ Emit leaderboard:update to session room
   │
   └─ Client displays new rank
```

**Latency:** 100-200ms (Redis dominated)

---

## Performance Characteristics

### Leaderboard Operations

| Operation | Tier 1 (Redis) | Tier 2 (MatView) | Tier 3 (Direct) |
|-----------|---|---|---|
| Get Top N | 20-50ms | 100-300ms | 500-1000ms |
| Get My Rank | 10-30ms | 50-150ms | 200-500ms |
| Update Score | 5-10ms | - | - |
| Complexity | O(log n) | O(n) scan | O(n) aggregate |

### Cache Hit Rates (Expected)
- Tier 1 (Redis): 70-80% (popular sessions)
- Tier 2 (MatView): 95%+ (refreshed every 30s)
- Tier 3 (Direct): Fallback only

---

## Architecture Patterns

### 1. Three-Tier Caching
Combines speed, freshness, and reliability:
- Speed: Redis for hot reads
- Freshness: Materialized view refreshed every 30s
- Reliability: Direct query as ultimate fallback

### 2. Async/Await Throughout
- Non-blocking PostgreSQL queries via asyncpg
- Non-blocking Redis operations
- Concurrent multi-timeframe analysis (advisor)

### 3. Dependency Injection
- LeaderboardService accepts optional RedisClient
- AdvisorProcessor accepts DataFetcher, TechnicalAnalyzer
- Enables testing without external services

### 4. Event-Driven Updates
- Socket.IO events for real-time broadcasts
- Subscription model for session-scoped updates
- Fire-and-forget with exception handling

### 5. Circuit Breaker Pattern
- Protects MT5 connection from cascading failures
- Automatic fallback on repeated errors
- Graceful degradation for unavailable services

---

## Critical Sections for Code Review

### Phase 01 Critical Files

1. **leaderboard_service.py**
   - Three-tier cache logic
   - P&L aggregation queries
   - Edge cases: empty rankings, missing users

2. **postgres_client.py**
   - Connection pool initialization
   - Error handling for connection failures
   - Command timeout configuration

3. **redis_client.py sorted set methods**
   - zadd, zrevrank, zscore consistency
   - TTL management
   - Null/empty case handling

4. **game_events.py**
   - Event validation
   - Room-based broadcasting
   - Session scope isolation

5. **Migrations 001-005**
   - Foreign key relationships
   - Materialized view performance indexes
   - Cascade delete semantics

---

## Next Phase Considerations

### Phase 02: Game Control Integration
- Game controller input mapping
- Real-time position sync
- Haptic feedback on trades

### Phase 03: Advanced Features
- Private/leaderboards (seasons, brackets)
- P&L bonus multipliers
- Streak tracking

### Phase 04: AI Integration
- Recommendation-based P&L boost
- ML prediction of team performance
- Dynamic difficulty scaling

---

## References

- [System Architecture - Leaderboard](./system-architecture.md)
- [Code Standards](./code-standards.md)
- [Project Roadmap](./project-roadmap.md)
- [Technical Analysis Architecture](./system-architecture-advisor.md)

---

**Document Status:**
- Status: Active
- Last Updated: 2025-12-31
- Owner: Project Team
- Visibility: Internal
