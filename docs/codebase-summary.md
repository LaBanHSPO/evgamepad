# EV GamePad - Codebase Summary

**Last Updated:** 2025-12-31
**Version:** Phase 03 - Game Sessions & Teams (IN PROGRESS)
**Token Count:** 399,137 tokens (Repomix Full Pack)
**Total Files:** 188 files
**Generated:** 2025-12-31
**Version:** Phase 5.4 + Phase 1 KOL Updates MVP (Integration & Testing + Database Layer)
**Total Files:** 181 (added KOL Messages migration + Phase 1 database schema)
**Total Tokens:** ~440K (repomix: ~150K tokens from 115 files)

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
- `leaderboard_service.py` - Three-tier leaderboard (Redis → MaterializedView → Direct) (Phase 01)
- `game_service.py` - Session lifecycle management (NEW Phase 03)
- `team_service.py` - Team formation & scoring (NEW Phase 03)
- `mt5_integration_service.py` - Account pool management (UPDATED Phase 03)

**Core Responsibilities:**
- Leaderboard: Real-time rank calculations with fallback caching strategy
- Game: Session creation, joining, auto-start on 4+ players
- Team: Round-robin assignment, team member tracking, P&L aggregation
- MT5: Account allocation with session awareness, pool management

#### **Event Handlers** (`app/events/`)
- `game_events.py` - Socket.IO game & leaderboard events (UPDATED Phase 03)
- `advisor_events.py` - Technical analysis events
- `trading_events.py` - Trading order/position events

**Phase 03 Events:**
```
Game Session Management:
├─ game:create_session - /csv command (create new session)
├─ game:join_session - /jsv command (join with auto-team assignment)
├─ game:leave_session - Leave and release MT5 account
├─ session:info - Get session details & teams
└─ session:started - Broadcast when 4+ players join

Leaderboard:
├─ leaderboard:get - Request rankings for session
├─ leaderboard:result - Response with rankings
├─ leaderboard:subscribe - Subscribe to real-time updates
└─ leaderboard:update - Broadcast rank change
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

## Phase 03: Game Sessions & Teams Implementation (CURRENT)

### New Components

**Services:**
- `GameService` - Session lifecycle (create, join, leave, complete)
- `TeamService` - Round-robin team assignment, member tracking, P&L calculation

**Key Features:**
1. **Session Lifecycle:** waiting → active → completed
2. **Commands:**
   - `/csv` - Create session (/csv SessionName MaxTeamSize)
   - `/jsv` - Join session (/jsv SessionName Username)
   - `/close` - End session (creator only) [Future]
3. **Auto-Start:** Session transitions to active when 4+ players join
4. **Round-Robin:** Users auto-assigned to balanced teams (max 6 players per team)
5. **MT5 Allocation:** Each user gets dedicated MT5 account on join
6. **Team Naming:** SessionName-A, SessionName-B, etc.

**Database Changes:**
- Added `creator_id` to `game_sessions` table
- Added `user_account_allocations` tracking
- Session status enum: waiting, active, completed

**Event Handlers in game_events.py:**
- `game:create_session` - Handles /csv command
- `game:join_session` - Handles /jsv with auto-team assignment
- `game:leave_session` - Cleanup and account release
- `session:info` - Query session details
- `broadcast_session_start` - Notify when session auto-starts

**Testing:**
- `test_game_session_flow.py` - Integration tests for session lifecycle

### Data Flows

**Create Session (/csv):**
```
Client: /csv MySession 6
  → game:create_session handler
  → Create game_sessions row
  → Create first team (MySession-A)
  → Add creator as team member
  → Allocate MT5 account
  → Emit game:session_created
```

**Join Session (/jsv):**
```
Client: /jsv MySession Player1
  → game:join_session handler
  → Validate session exists & not completed
  → TeamService.auto_assign_team()
    ├─ Find team with fewest members
    └─ Create new team if all full
  → MT5IntegrationService.allocate_account()
  → _check_start_session()
    └─ If 4+ players: status = active, broadcast session:started
  → Emit game:session_joined
```

### Performance

| Operation | Typical | 95th |
|-----------|---------|------|
| Create session | 10-20ms | 50ms |
| Join session | 50-100ms | 200ms |
| Auto-assign team | 5-15ms | 30ms |
| Account allocate | 10-30ms | 80ms |

### Scalability

- Max concurrent sessions: 50+ with 2-3 teams each = 600+ users
- Join throughput: 10 joins/sec
- Team balancing via GROUP BY + HAVING (efficient)

---

## Next Phase Considerations (Phase 04+)

### Phase 04: Advanced Features
- Private leaderboards (seasons, brackets)
- P&L bonus multipliers based on team size
- Streak tracking (win/loss streaks)
- Session history and replay

### Phase 05: ML Integration
- Recommendation-based P&L boost
- Predictive team performance ranking
- Dynamic difficulty scaling
- Optimal trade timing suggestions

### Future Enhancements
- Tournament mode with elimination brackets
- Cross-session seasonal leaderboards
- Team roster management (invite/remove)
- Account sharing (multiple users → one MT5 account)

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
EV GamePad is a real-time AI trading advisor backend built with Python (FastAPI/Starlette) and React/TypeScript frontend. It provides:

1. **Real-time Technical Analysis** - Multi-timeframe indicator calculation, pattern recognition, support/resistance
2. **AI Recommendations** - Claude/DeepSeek LLM integration with capital preservation focus
3. **Portfolio Analysis** - Per-position risk metrics + portfolio-wide health scoring
4. **Semantic Caching** - Redis-based cache for technical indicators and AI responses

---

## Core Architecture Layers

### 1. Backend Stack

**Framework & Server:**
- `FastAPI` with `Starlette` WebSocket support
- `Socket.IO` (python-socketio) for real-time event-driven communication
- Async-first design with `asyncio`

**Key Modules:**
- `app/main.py` - Server initialization, Socket.IO setup, MT5 manager injection
- `app/sio.py` - Socket.IO singleton instance
- `app/config.py` - Configuration (API keys, timeframes, cache settings)

**Data & Market Integration:**
- MT5 Terminal wrapper (Windows/WSL) - OHLCV data feed
- `app/advisor/data_fetcher.py` - Async data fetching from MT5
- `app/mt5/connection_manager.py` - MT5 connection lifecycle
- `app/mt5/circuit_breaker.py` - Fault tolerance for MT5 operations

### 2. Technical Analysis Pipeline (Phase 01-03)

**Indicator Calculation:**
- `app/advisor/technical_analyzer.py` - SMA, EMA, RSI, MACD, Bollinger Bands, ATR, ADX, Stochastic, OBV
- `app/models/advisor_models.py` - Pydantic models for responses

**Pattern Recognition:**
- `app/advisor/pattern_detector.py` - Candlestick patterns (Hammer, Engulfing, etc.)
- `app/advisor/chart_pattern_detector.py` - Chart patterns (Head & Shoulders, Double Top, etc.)

**Support & Resistance:**
- `app/advisor/support_resistance.py` - Fibonacci, Pivot, Swing-based S/R levels
- `app/advisor/swing_utils.py` - Swing high/low detection

**Risk Analysis:**
- `app/advisor/risk_analyzer.py` - Position sizing, risk/reward calculation, ATR-based stops

### 3. AI Integration (Phase 04)

**LLM Services:**
- `app/advisor/ai_summarizer.py` - Claude 3.5 Sonnet + DeepSeek integration
  - Technical summary generation
  - Portfolio advice with capital preservation focus
  - Semantic caching for responses

**Recommendation Engine:**
- `app/advisor/recommendation_engine.py` - Aggregates technical signals + AI summary

**Portfolio Analysis:**
- `app/processors/advisor_processor.py` - `process_portfolio_analysis()` method
  - Per-position technical + risk analysis
  - Portfolio health scoring (0-100)
  - LLM-powered capital preservation advice

### 4. Explainability Layer (Phase 5.1)

**Data Provenance Tracking:**
- `app/advisor/data_provenance_tracker.py` - Source tracking for all signals
  - DataSource enum: MT5, TwelveData, pandas-ta, Claude API, DeepSeek, Redis cache
  - DataType enum: price, volume, indicator, pattern, llm_summary, risk_metric
  - ValidationStatus: validated, unvalidated, conflicting, stale
  - Metadata: fetched_at, cache_hit, confidence (0.0-1.0), raw_value, computed_value

**Chain-of-Thought Engine:**
- `app/advisor/chain_of_thought_engine.py` - Transparent reasoning breakdown
  - 5-step analysis: Trend (3pts), Momentum (3pts), Volume (2pts), Pattern (2pts), Risk (2pts)
  - Point-based scoring: 0-12 total, maps to confidence 0.0-1.0
  - Recommendation actions: STRONG_BUY, BUY, WEAK_BUY, HOLD, WEAK_SELL, SELL, STRONG_SELL
  - Output: ReasoningStep list + summary + risks + data gaps

**Explainability Models:**
- `app/models/explainability_models.py` - Pydantic request/response schemas
  - ExplainRecommendationRequest
  - ChainOfThoughtResponse
  - ExplainRecommendationResponse
  - ProvenanceMetadata

### 5. Accuracy Tracking System (Phase 5.2 - NEW)

**Core Tracking Module:**
- `app/advisor/accuracy_tracker.py` - Performance metrics tracking
  - `AccuracyTracker` class: Record outcomes, generate reports, find best-performing configs
  - Calculates: win rate, profit factor, Sharpe ratio, avg P/L, best/worst trades
  - Database integration: PostgreSQL via asyncpg connection pool
  - Materialized view refresh for fast queries
  - Support for filtering by symbol, timeframe, signal, user_id

**MT5 Auto-Detection:**
- `app/advisor/mt5_history_parser.py` - Automatic outcome detection from MT5
  - `MT5HistoryParser` class: Sync closed positions every 5 minutes
  - Match deals to recommendations using 3-factor scoring (symbol, price, time)
  - Determine exit reason: take_profit, stop_loss, manual, unknown
  - Process and auto-record outcomes without manual input
  - Matching criteria: symbol exact, price within ±0.1%, time within ±5 minutes

**Database Layer:**
- `app/database/pool_manager.py` - PostgreSQL connection pool management
  - Async pool initialization and cleanup
  - Connection parameters from environment variables
  - Min/max pool size configuration
  - Health check integration

**Data Models:**
- `app/models/accuracy_models.py` - Request/response schemas
  - RecordOutcomeRequest: Manual outcome submission
  - AccuracyReportRequest: Query parameters for reports
  - AccuracyMetrics: Response containing performance stats
  - BestPerformingConfig: Top-performing symbol/timeframe/signal combinations
  - OutcomeRecordResponse, AccuracyReportResponse: API responses

**Database Schema:**
- `app/database/migrations/005_recommendation_outcomes.sql` - PostgreSQL migration
  - `recommendation_outcomes` table: Stores all trade outcomes
  - 19 columns: IDs, trade details, prices, outcomes, P/L metrics, timestamps
  - Materialized view: `recommendation_accuracy` for aggregated metrics
  - Indexes on: symbol+timeframe, signal+outcome, created_at, user_id
  - Auto-update trigger for timestamps
  - Refresh function for materialized view

**KOL Messages Storage (Phase 1 - KOL Updates MVP):**
- `app/database/migrations/006_kol_messages.sql` - KOL trading signals storage
  - `kol_messages` table: Real-time trading signals from KOL sources via Zalo webhook
  - 9 columns: id (UUID), kol_id, kol_name, message_text, message_hash, zalo_message_id, received_at, created_at, updated_at, metadata (JSONB)
  - Deduplication: UNIQUE constraint on `message_hash` (MD5 hash of kol_id|timestamp|message)
  - Performance indexes:
    - `idx_kol_messages_received_at` - Descending on received_at for time-based queries
    - `idx_kol_messages_kol_id` - Composite on (kol_id, received_at DESC) for KOL-specific queries
    - `idx_kol_messages_hash` - Hash-based deduplication lookup
  - Auto-update trigger on `updated_at` column via `update_updated_at_column()` function

### 6. API & Events (WebSocket)

**Event Layer:**
- `app/events/advisor_events.py` - Socket.IO event handlers
  - `advisor:technical_summary` - Single timeframe analysis
  - `advisor:multi_timeframe` - Multiple timeframe analysis
  - `advisor:pattern_scan` - Pattern detection
  - `advisor:risk_analysis` - Risk metrics
  - `advisor:recommendation` - AI-powered recommendation
  - `advisor:portfolio_analysis` - Portfolio analysis + AI advisory (Phase 04)
  - `advisor:explain_recommendation` - Chain-of-thought explanation (Phase 5.1)
  - `advisor:record_outcome` - Record trade outcome (Phase 5.2)
  - `advisor:accuracy_report` - Get accuracy metrics report (Phase 5.2)
  - `advisor:explain_recommendation` - **NEW** Trigger CoT + provenance explanation (Phase 5.3 Frontend)
  - `advisor:explanation_result` - **NEW** Return CoT reasoning + data freshness info (Phase 5.3 Frontend)

**Data Models:**
- `PortfolioAnalysisRequest` - User position input + account balance
- `PortfolioAnalysisResponse` - Health metrics + position analysis + AI advice
- `PortfolioHealth` - Score (0-100), status (HEALTHY/CAUTION/DANGER), risk metrics
- `PositionAnalysis` - Per-position metrics: P&L, R-Multiple, distance to stop, risk status, recommendation

### 5. Caching Strategy (Redis)

**Redis Client:**
- `app/database/redis_client.py` - Redis wrapper with async support

**Cache Keys & TTL:**
- `indicators:{symbol}:{timeframe}` - 60s TTL
- `patterns:{symbol}:{timeframe}` - 300s TTL (5 min)
- `ai_summary:{hash}` - 300s TTL (semantic cache)
- `portfolio_advice:{hash}` - 300s TTL (semantic cache)
- `portfolio_analysis:{hash}` - 300s TTL (semantic cache)
- `cot:{symbol}:{timeframe}:{score_hash}` - 300s TTL (Phase 5.1 chain-of-thought)

**Cache Hit Logic:**
- Technical indicators cached by symbol + timeframe
- AI summaries cached by symbol + timeframe + RSI signal + trend + price bucket
- Portfolio advice cached by risk exposure + drawdown + health score + risk profile + positions hash

---

## Frontend Architecture

### React Components

**New Components (Phase 04):**
- `src/components/PositionInputForm.tsx` - Position entry form (symbol, entry, current, size, stop loss)
- `src/components/AIRiskAdvisoryPanel.tsx` - Portfolio health display + AI advisory results
- `src/hooks/usePortfolioAnalysis.ts` - Socket.IO event handling + state management

**Explainability Components (Phase 5.1):**
- `src/components/advisor/ChainOfThoughtViewer.tsx` - 5-step reasoning breakdown with scoring

**New Visual Dashboard Components (Phase 5.3):**
- `src/components/advisor/IndicatorOverlayChart.tsx` - TradingView-style chart with toggleable technical indicators
  - Uses Recharts for responsive visualization (alternative to lightweight-charts)
  - Displays: candlestick price, EMA 21/50, SMA 200, Bollinger Bands, Volume
  - Support/Resistance reference lines (colored dashed lines)
  - Real-time updates via Socket.IO `advisor:technical_result` event
  - Mock OHLCV generation from technical data (production: use MT5 feeds)
  - Controls: Indicator toggle buttons with color indicators
  - Responsive sizing with chart metadata display

- `src/components/advisor/ChainOfThoughtViewer.tsx` - Step-by-step reasoning display
  - 5 reasoning steps with category icons (trend, momentum, volume, pattern, risk)
  - Point-based scoring visualization (color-coded: green ≥80%, orange ≥50%, red <50%)
  - Confidence percentage per step
  - Recommendation color-coding (green=BUY, red=SELL, orange=HOLD)
  - Risk identification section with shield alert icon
  - Data gaps section for transparency
  - Indicators used per step (optional field)

- `src/components/advisor/AccuracyMetricsPanel.tsx` - Historical performance statistics
  - 30-day (configurable) period analysis
  - 4-metric grid display:
    - Total trades count
    - Win rate % with W/L breakdown (color-coded: green ≥70%, orange ≥60%, red <60%)
    - Avg P/L % with trending icons (green=up, red=down)
    - Profit factor with quality assessment (Excellent ≥2.0, Good ≥1.5, Fair ≥1.0, Poor <1.0)
  - Optional additional stats: Avg Win, Avg Loss, Avg Hold Hours
  - Recommendation assessment box with primary color background
  - Error/no-data states with appropriate messaging
  - Socket.IO integration: `advisor:accuracy_report` event

- `src/components/advisor/ProvenanceTimeline.tsx` - Data source freshness tracker
  - Source icon mapping (MT5=Database, TwelveData=Cloud, pandas-ta=Activity, LLM=Bot, Redis=RefreshCw)
  - Cache hit rate progress bar (green color when >0%)
  - Per-source freshness indicators:
    - Data point count
    - Cache hits ratio
    - Average confidence %
    - Age of oldest data (color-coded: green <1min, orange <5min, yellow <1hr, red >1hr)
  - Overall data freshness status with emoji indicators:
    - ✅ All data fresh (< 1min)
    - ✅ Freshness acceptable (< 5min)
    - ⚠️ May be stale (< 1hr)
    - ❌ Requires refresh (> 1hr)

**Integration with CapitalCompanionPanel:**
- `src/components/CapitalCompanionPanel.tsx` - Updated with explainability tab/view
  - Three view modes: 'chat' | 'pinned' | 'explainability'
  - Explainability toggle button ("Show/Hide Details")
  - Explainability section displays in sequence:
    1. IndicatorOverlayChart (chart with toggles)
    2. ChainOfThoughtViewer (reasoning breakdown)
    3. AccuracyMetricsPanel (performance stats)
    4. ProvenanceTimeline (data sources freshness)
  - Socket.IO event: `advisor:explain_recommendation` - request explanation
  - Socket.IO event: `advisor:explanation_result` - receive CoT + provenance data

**Error Boundary Component (Phase 5.4 - NEW):**
- `src/components/ErrorBoundary.tsx` - React error boundary for crash prevention
  - Class component implementation (required for error boundaries)
  - Catches rendering errors from child components
  - Prevents cascade failures across UI
  - Features:
    - User-friendly fallback UI with "Try Again" button
    - Optional error callback for custom error reporting
    - Development mode: Shows full error stack trace + component stack
    - Production mode: Shows generic error message
  - Higher-order component wrapper: `withErrorBoundary(Component, fallback?, onError?)`
  - Usage: Wrap critical components to isolate failures
  - Styled with danger colors (AlertTriangle icon, red text)
  - No TypeScript 'any' types (fully typed)
  - State management:
    - `cotData` - chain-of-thought reasoning data
    - `provenanceData` - data source freshness info
    - `showExplainability` - UI toggle state
    - `currentSymbol`, `currentTimeframe` - context for chart

**Integration:**
- `src/pages/Portfolio.tsx` - Main portfolio analysis page
  - Combines form + results display
  - Manages loading/error states
  - Sends `advisor:portfolio_analysis` event to backend

### Context & Connection Management (Phase 5.4)

**Socket Context:**
- `src/context/SocketContext.tsx` - Global Socket.IO connection provider
  - Singleton connection instance
  - Reconnection logic with exponential backoff
    - Start: 1s delay
    - Max: 10s delay with 50% jitter
    - Attempts: 10 maximum
  - Connection state: `isConnected`, `lastError`
  - Graceful degradation: Works without connected state
  - Auto-reconnect on server-side disconnects
  - Manual control: Respects user-initiated disconnects

### State Management

- **React Hooks:** `useState`, `useCallback` for local state
- **Socket.IO Integration:** Event-driven via context provider
- **Type Safety:** Full TypeScript interfaces for requests/responses
- **Memory Management:** Proper cleanup with useEffect return functions

---

## Data Flow: Portfolio Analysis (NEW)

```
User Input (Frontend)
    │
    ├─ PositionInputForm collects:
    │  ├─ Positions (symbol, entry, current, size, stop)
    │  ├─ Account Balance
    │  └─ Risk Profile (conservative/moderate/aggressive)
    │
    ↓
advisor:portfolio_analysis (Socket.IO event)
    │
    ↓
advisor_processor.process_portfolio_analysis()
    │
    ├─ Step 1: Parallel Position Analysis
    │  ├─ Fetch current price (if missing)
    │  ├─ Calculate technical signal (RSI, trend, etc.)
    │  ├─ Calculate P&L metrics (pnl_pct, pnl_amount)
    │  ├─ Calculate R-Multiple (reward/risk)
    │  ├─ Determine risk status (safe/caution/approaching_stop/danger)
    │  └─ Generate recommendation (HOLD/REDUCE/CLOSE)
    │
    ├─ Step 2: Portfolio Health Calculation
    │  ├─ Total risk exposure (sum of position risks / account balance)
    │  ├─ Max drawdown (worst performing position)
    │  ├─ Positions at risk count
    │  ├─ Health score = 100 - penalties
    │  └─ Status (HEALTHY/CAUTION/DANGER)
    │
    ├─ Step 3: LLM Portfolio Advice
    │  ├─ Check Redis cache (semantic hash)
    │  ├─ If hit: return cached advice
    │  ├─ If miss: call Claude/DeepSeek with:
    │  │  ├─ Position summaries
    │  │  ├─ Portfolio health metrics
    │  │  ├─ Risk profile
    │  │  └─ Language preference
    │  ├─ LLM returns:
    │  │  ├─ overall_risk (LOW/MODERATE/HIGH)
    │  │  ├─ priority_actions (array of strings)
    │  │  ├─ reasoning
    │  │  └─ confidence
    │  └─ Cache result in Redis (300s)
    │
    └─ Step 4: Build Response
       ├─ portfolio_health object
       ├─ position_analysis array
       ├─ ai_advice object
       └─ metadata (cached, computed_at)

advisor:portfolio_result (Socket.IO event - Response)
    │
    ↓
AIRiskAdvisoryPanel (Frontend)
    │
    ├─ Display Portfolio Health Score + Status
    ├─ Show Risk Metrics (exposure, drawdown, positions at risk)
    ├─ Display AI Summary + Reasoning
    ├─ List Priority Actions (capital preservation focus)
    ├─ Per-position warnings + recommendations
    └─ Cache indicator + AI model info
```

---

## File Structure

```
backend/
├── app/
│   ├── advisor/                     # Technical analysis & AI modules
│   │   ├── technical_analyzer.py    # Indicator calculation
│   │   ├── pattern_detector.py      # Candlestick patterns
│   │   ├── chart_pattern_detector.py
│   │   ├── support_resistance.py    # S/R levels
│   │   ├── risk_analyzer.py         # Risk metrics
│   │   ├── ai_summarizer.py         # Claude/DeepSeek integration
│   │   ├── recommendation_engine.py # Signal aggregation
│   │   └── data_fetcher.py          # MT5 data fetching
│   ├── database/
│   │   ├── redis_client.py          # Redis caching + portfolio methods
│   │   ├── pool_manager.py          # PostgreSQL async connection pool
│   │   └── migrations/
│   │       ├── 005_recommendation_outcomes.sql  # Trade outcomes table + materialized view
│   │       ├── 006_kol_messages.sql            # KOL messages table + deduplication
│   ├── events/
│   │   └── advisor_events.py        # Socket.IO event handlers (incl. advisor:portfolio_analysis)
│   ├── models/
│   │   ├── advisor_models.py        # Pydantic models (PortfolioAnalysisRequest/Response, etc.)
│   │   └── responses.py             # Generic response format
│   ├── processors/
│   │   └── advisor_processor.py     # process_portfolio_analysis() + other processors
│   ├── mt5/
│   │   ├── connection_manager.py    # MT5 connection
│   │   └── circuit_breaker.py       # Fault tolerance
│   ├── config.py                    # Configuration
│   ├── main.py                      # Server entry point
│   └── logging_config.py
│
src/                                # React Frontend
├── components/
│   ├── advisor/                     # Advisor-specific components (Phase 5.1+)
│   │   ├── IndicatorOverlayChart.tsx      # Technical indicator visualization (Phase 5.3)
│   │   ├── ChainOfThoughtViewer.tsx       # 5-step reasoning display (Phase 5.1)
│   │   ├── AccuracyMetricsPanel.tsx       # Performance statistics (Phase 5.3)
│   │   └── ProvenanceTimeline.tsx         # Data freshness tracker (Phase 5.3)
│   ├── PositionInputForm.tsx        # Position input + account balance form (Phase 04)
│   ├── AIRiskAdvisoryPanel.tsx      # Portfolio health + AI advisory display (Phase 04)
│   └── CapitalCompanionPanel.tsx    # Main advisor panel with explainability (updated Phase 5.3)
├── hooks/
│   └── usePortfolioAnalysis.ts      # Socket.IO integration + state management (Phase 04)
├── context/
│   └── SocketContext.tsx            # Socket.IO client provider + hooks
├── pages/
│   └── Portfolio.tsx                # Portfolio analysis page
└── types/                           # TypeScript interfaces

docs/
├── advisor-api-specification.md     # API endpoint documentation (updated)
├── system-architecture-advisor.md   # Architecture diagrams (updated)
├── codebase-summary.md              # This file (NEW)
├── code-standards.md                # Code conventions (NEW)
└── project-overview-pdr.md          # PDR document (NEW)
```

---

## Key Design Decisions

### 1. Async-First Backend
- All I/O operations are async (`asyncio.gather()` for parallel position analysis)
- Socket.IO allows real-time response streaming
- No blocking operations in event handlers

### 2. Capital Preservation Philosophy (Portfolio Advice)
- LLM is instructed to prioritize CAPITAL PRESERVATION over profits
- AI identifies positions requiring immediate action
- Recommendations focus on closing/reducing high-risk positions

### 3. Two-Layer Caching
- **L1: Indicator Cache** - Direct Redis storage (60s TTL)
- **L2: Semantic Cache** - Hash-based caching for AI responses with similar inputs (300s TTL)
  - Reduces LLM API calls
  - Deterministic keys based on technical state + risk profile

### 4. Graceful Degradation
- If Claude unavailable: fallback to DeepSeek
- If both LLMs unavailable: return structured fallback advice
- If MT5 connection fails: return cached data or error response

### 5. Validation-First Architecture
- Pydantic models enforce request validation
- Symbol format: `[A-Z0-9]{1,20}` (case-insensitive input, uppercase output)
- Timeframe whitelist: M1, M5, M15, M30, H1, H4, D1, W1, MN1

---

## Dependencies

**Backend:**
- `fastapi` - Web framework
- `python-socketio` - WebSocket library
- `pydantic` - Data validation
- `pandas` - OHLCV data manipulation
- `anthropic` - Claude API
- `openai` - DeepSeek API (OpenAI-compatible)
- `redis` - Async Redis client
- `python-json-logger` - Structured logging
- `MetaTrader5` - MT5 connection (Python package)

**Frontend:**
- `react` - UI framework
- `typescript` - Type safety
- `socket.io-client` - WebSocket client
- `lucide-react` - Icons (used in Phase 5.3 components)
- `recharts` - Chart visualization (Phase 5.3: IndicatorOverlayChart)
- `tailwindcss` - Styling
- `sonner` - Toast notifications

---

## Testing

**Test Files:**
- `tests/test_portfolio_analysis.py` - Portfolio analysis unit tests
- `tests/test_phase_04_ai_recommendations.py` - AI summarizer tests
- `tests/test_technical_analyzer.py` - Technical analysis tests
- `tests/test_events.py` - Event handler tests

**Coverage:**
- Model validation
- Processor logic (indicator calculation, portfolio metrics)
- Cache hit/miss scenarios
- Error handling + fallback behavior
- LLM response parsing

---

## Performance Considerations

### Time Complexity
- Single position analysis: O(1) - direct calculations
- Portfolio analysis: O(n) where n = number of positions (parallelized)
- Indicator calculation: O(m) where m = number of candles

### Space Complexity
- OHLCV data: 100-200 candles * 5 fields * 8 bytes = ~5-10KB per symbol
- Cache storage: ~1KB per technical indicator result
- Redis TTL management: automatic cleanup

### Optimization Techniques
1. **Parallel Position Analysis** - `asyncio.gather()` processes positions concurrently
2. **Semantic Caching** - Reduces redundant LLM calls by ~70% (estimated)
3. **Price Bucketing** - Cache key rounds prices to nearest 10 to reduce misses
4. **Lazy Initialization** - LLM clients initialized only on first use

---

## Configuration Management

**Environment Variables (`.env`):**
```bash
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...
DEFAULT_LLM_MODEL=claude  # or deepseek
REDIS_URL=redis://localhost:6379
MT5_ACCOUNT=12345
MT5_PASSWORD=...
MT5_SERVER=MetaQuotes-Demo
```

**Timeframe Mapping:**
```python
MT5_TIMEFRAMES = {
    'M1': TIMEFRAME_M1,   # 1 minute
    'H1': TIMEFRAME_H1,   # 1 hour
    'D1': TIMEFRAME_D1,   # 1 day
    # ... etc
}
```

---

## Error Handling Strategy

**Frontend:**
- Socket.IO error event listener
- Fallback UI states (loading, error, empty)
- User-friendly error messages

**Backend:**
- Pydantic `ValidationError` caught in events
- Try-catch around LLM calls with fallback
- Redis cache failures logged but non-blocking
- MT5 circuit breaker trips on repeated failures

**Error Codes:**
```python
class ErrorCode(Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MT5_ERROR = "MT5_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    LLM_ERROR = "LLM_ERROR"
```

---

## Monitoring & Observability

**Structured Logging:**
- JSON format via `python-json-logger`
- Includes: timestamp, level, session ID, operation, duration
- Searchable via log aggregation tools

**Metrics to Track:**
- Portfolio analysis latency (target: <5s)
- Cache hit rate (target: >60%)
- LLM API latency (target: <3s)
- MT5 connection uptime (target: >99%)

---

## Security Considerations

1. **Input Validation** - All user inputs validated via Pydantic
2. **Rate Limiting** - Recommended to add to production deployment
3. **API Key Management** - Never commit `.env` files
4. **SQL Injection Prevention** - N/A (no SQL), but prompt injection sanitization added
5. **WebSocket Authentication** - Placeholder for JWT integration

---

## Future Enhancements

1. **Multi-Account Support** - Per-user portfolio analysis
2. **Position History** - Track position changes over time
3. **ML Model Integration** - Custom ML predictions for entry signals
4. **Webhook Integration** - Alert positions entering danger zone
5. **Mobile App** - React Native wrapper for iOS/Android
6. **Advanced Risk Metrics** - VaR, Sharpe Ratio, Drawdown duration
7. **Voice Advisory** - Text-to-speech for AI recommendations

---

## Quick Reference

### Common Tasks

**Add New Indicator:**
1. Implement calculation in `technical_analyzer.py`
2. Add Pydantic field in `advisor_models.TechnicalIndicators`
3. Update event handler in `advisor_events.py` to accept indicator name

**Update Cache TTL:**
- Edit `redis_client.py` or inline `setex()` calls
- Consider cache invalidation strategy

**Change LLM Provider:**
- Edit `ai_summarizer.py` `_get_anthropic_client()` or `_get_openai_client()`
- Update prompt templates if needed
- Test fallback behavior

**Adjust Portfolio Health Scoring:**
- Edit `advisor_processor._calculate_portfolio_health()` formula
- Rerun tests to ensure expected score ranges

---

## Support & Documentation Links

- **API Spec:** `./advisor-api-specification.md`
- **Architecture:** `./system-architecture.md`
- **Code Standards:** `./code-standards.md`
- **Implementation Guide:** `./advisor-implementation-guide.md`
- **KOL Database Schema:** See system-architecture.md → Database Schema section

---

**Last Updated:** 2025-12-31
**Maintainer:** Backend + Frontend Team
**Status:** Phase 5.4 (Integration & Testing) + Phase 1 (Database Layer Complete)
