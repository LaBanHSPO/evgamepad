# EV GamePad - System Architecture

**Date:** 2025-12-31
**Version:** Phase 5.4 + Phase 1 KOL Updates MVP
**Scope:** Backend (FastAPI), Frontend (React/TypeScript), Database (PostgreSQL + Redis)

---

## System Overview

EV GamePad is a real-time AI trading advisor platform with multi-layer caching, explainability, and accuracy tracking. The system is divided into five main layers:

1. **API & Events Layer** - WebSocket-based real-time communication
2. **Application Logic Layer** - Technical analysis, AI integration, risk metrics
3. **Data Access Layer** - PostgreSQL (persistent), Redis (cache)
4. **Integration Layer** - MT5 connection, LLM APIs (Claude/DeepSeek)
5. **Frontend Layer** - React components with Socket.IO client

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (React/TypeScript)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Portfolio Analysis → Risk Advisory → Chain-of-Thought    │  │
│  │ Accuracy Metrics → Data Provenance → Chart Overlay       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ↑ Socket.IO ↓                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Event Handlers (advisor_events.py)                       │  │
│  │ - portfolio_analysis, explain_recommendation, etc.       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Processors & Analyzers                                   │  │
│  │ - advisor_processor: portfolio health, position analysis │  │
│  │ - technical_analyzer: indicators (SMA, EMA, RSI, etc)    │  │
│  │ - chain_of_thought_engine: reasoning breakdown (5 steps) │  │
│  │ - data_provenance_tracker: source metadata tracking      │  │
│  │ - accuracy_tracker: win rate, profit factor, Sharpe      │  │
│  │ - mt5_history_parser: auto-detect trade outcomes         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ AI Integration Layer                                     │  │
│  │ - ai_summarizer: Claude 3.5 Sonnet + DeepSeek fallback  │  │
│  │ - recommendation_engine: signal aggregation              │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Data Access Layer                                        │  │
│  │ - pool_manager: PostgreSQL async connection pool         │  │
│  │ - redis_client: async Redis client + cache methods       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        │                              │
        ↓                              ↓
    PostgreSQL              Redis (Cache)
    (Persistent)            (Session)
```

---

## Database Schema

### Overview

The system uses PostgreSQL for persistent storage with two main data domains:

1. **Trade Accuracy Tracking** - `recommendation_outcomes` table + materialized view
2. **KOL Trading Signals** - `kol_messages` table with deduplication (Phase 1)

### Migration Files

- **Location:** `backend/app/database/migrations/`
- **Execution:** `psql -d ev_gamepad -f 00X_table_name.sql`
- **Verification:** `psql -d ev_gamepad -f verify_00X_table_name.sql`

### 1. recommendation_outcomes Table (Phase 5.2)

**Purpose:** Store trade outcomes from manual user submission or MT5 auto-detection.

**Schema:**

```
┌─────────────────────────────────────────────────────┐
│           recommendation_outcomes                   │
├─────────────────────────────────────────────────────┤
│ id (UUID, PK)                                       │
│ user_id (VARCHAR, FK)                              │
│ recommendation_id (UUID, FK)                       │
│ symbol (VARCHAR 20)                                │
│ timeframe (VARCHAR 10)                             │
│ signal (VARCHAR 20): STRONG_BUY, BUY, HOLD, SELL   │
│ entry_price (NUMERIC)                              │
│ current_price (NUMERIC)                            │
│ exit_price (NUMERIC)                               │
│ pnl_amount (NUMERIC)                               │
│ pnl_percent (NUMERIC)                              │
│ outcome (VARCHAR 20): WIN, LOSS, BREAKEVEN         │
│ exit_reason (VARCHAR 50): take_profit, stop_loss   │
│ hold_duration_minutes (INT)                        │
│ confidence_score (NUMERIC 0.0-1.0)                 │
│ notes (TEXT)                                       │
│ created_at, updated_at (TIMESTAMPTZ)               │
│ metadata (JSONB)                                   │
├─────────────────────────────────────────────────────┤
│ Indexes:                                            │
│ - (symbol, timeframe) - quick symbol queries        │
│ - (signal, outcome) - performance analysis          │
│ - created_at DESC - time-based reports              │
│ - user_id - per-user accuracy metrics               │
├─────────────────────────────────────────────────────┤
│ View: recommendation_accuracy (Materialized)       │
│ - Aggregates: win_count, loss_count, win_rate      │
│ - Aggregates: avg_pnl, profit_factor, sharpe       │
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- Manual submission via API: `advisor:record_outcome` event
- Auto-detection: MT5HistoryParser syncs closed trades every 5 minutes
- Matching algorithm: symbol exact, price within ±0.1%, time within ±5 min
- Materialized view for fast reporting (refresh via trigger)

---

### 2. kol_messages Table (Phase 1 - KOL Updates MVP)

**Purpose:** Store real-time KOL trading signals received via Zalo webhook with automatic deduplication.

**Schema:**

```
┌─────────────────────────────────────────────────────┐
│              kol_messages                           │
├─────────────────────────────────────────────────────┤
│ id (UUID, PK)                                       │
│    DEFAULT: gen_random_uuid()                       │
│    Purpose: Unique row identifier                   │
├─────────────────────────────────────────────────────┤
│ kol_id (VARCHAR 100, NOT NULL)                      │
│    Example: "trader_pro_vn", "crypto_guru"          │
│    Purpose: KOL source identifier                   │
├─────────────────────────────────────────────────────┤
│ kol_name (VARCHAR 200, NOT NULL)                    │
│    Example: "Trader Pro VN", "Crypto Guru"          │
│    Purpose: Display name for UI/reports             │
├─────────────────────────────────────────────────────┤
│ message_text (TEXT, NOT NULL)                       │
│    Example: "Buy XAU at 2650.5, TP 2670, SL 2640"   │
│    Purpose: Raw trading signal content              │
├─────────────────────────────────────────────────────┤
│ message_hash (VARCHAR 32, NOT NULL, UNIQUE)         │
│    Type: MD5 hash                                   │
│    Hashed: kol_id|timestamp|message_text            │
│    Purpose: Deduplication key (prevents duplicates) │
├─────────────────────────────────────────────────────┤
│ zalo_message_id (VARCHAR 255, NULLABLE)             │
│    Purpose: External webhook message ID             │
├─────────────────────────────────────────────────────┤
│ received_at (TIMESTAMPTZ, NOT NULL)                 │
│    DEFAULT: NOW()                                   │
│    Purpose: Webhook receipt timestamp               │
├─────────────────────────────────────────────────────┤
│ created_at (TIMESTAMPTZ, NOT NULL)                  │
│    DEFAULT: NOW()                                   │
│    Purpose: Row creation timestamp                  │
├─────────────────────────────────────────────────────┤
│ updated_at (TIMESTAMPTZ, NOT NULL)                  │
│    DEFAULT: NOW()                                   │
│    Trigger: update_kol_messages_updated_at (BEFORE) │
│    Purpose: Row last modified timestamp             │
├─────────────────────────────────────────────────────┤
│ metadata (JSONB, NULLABLE)                          │
│    Example: {"zalo_user_id": "123", "source":       │
│              "webhook", "confidence": 0.95}         │
│    Purpose: Additional Zalo/source metadata         │
├─────────────────────────────────────────────────────┤
│ Indexes (Performance):                              │
├─────────────────────────────────────────────────────┤
│ 1. idx_kol_messages_received_at                     │
│    - Column: received_at DESC                       │
│    - Use: Recent signal queries (time-ordered)      │
│    - Query: SELECT * FROM kol_messages              │
│             WHERE received_at > NOW() - '24h'       │
├─────────────────────────────────────────────────────┤
│ 2. idx_kol_messages_kol_id                          │
│    - Columns: (kol_id, received_at DESC)            │
│    - Use: KOL-specific signal history               │
│    - Query: SELECT * FROM kol_messages              │
│             WHERE kol_id = $1 ORDER BY received_at  │
├─────────────────────────────────────────────────────┤
│ 3. idx_kol_messages_hash                            │
│    - Column: message_hash                           │
│    - Use: Deduplication lookup (fast UNIQUE check)  │
│    - Query: SELECT id FROM kol_messages             │
│             WHERE message_hash = $1                 │
├─────────────────────────────────────────────────────┤
│ Constraints:                                        │
├─────────────────────────────────────────────────────┤
│ - PRIMARY KEY: id                                   │
│ - UNIQUE: message_hash (enforces deduplication)     │
│ - NOT NULL: kol_id, kol_name, message_text,         │
│             message_hash, received_at, created_at   │
│             updated_at                              │
├─────────────────────────────────────────────────────┤
│ Trigger:                                            │
├─────────────────────────────────────────────────────┤
│ - update_kol_messages_updated_at                    │
│   Event: BEFORE UPDATE                              │
│   Action: SET NEW.updated_at = NOW()                │
│   Function: update_updated_at_column()              │
└─────────────────────────────────────────────────────┘
```

**Deduplication Strategy:**

The `message_hash` column uses MD5 hashing to prevent duplicate messages:

```
Hash Input:   MD5(kol_id + '|' + timestamp + '|' + message_text)
Example:      MD5('trader_pro_vn|2025-12-31T10:30:00|Buy XAU 2650')
              → 'a7c3e8f2d4b1a9e6c2f8a3d7e9b1c4f0'
```

When a webhook sends the same signal twice:
1. First insert: Hash stored in database, message saved
2. Duplicate attempt: UNIQUE constraint violation on `message_hash_key`
3. Application: Catch PostgreSQL error and discard duplicate (idempotent)

**Performance Characteristics:**

- **Insert:** O(1) - single row + hash index update
- **Dedup Check:** O(log n) - B-tree index lookup on message_hash
- **Time-Range Query:** O(log n + k) - received_at index, k = result rows
- **KOL Filter:** O(log n + k) - composite index (kol_id, received_at)

---

## Caching Strategy (Redis)

### Cache Layers

**L1: Direct Cache** (Indicators & Temporary Data)
- Key: `indicators:{symbol}:{timeframe}`
- TTL: 60 seconds
- Purpose: Real-time indicator updates
- Data: TechnicalIndicators object (SMA, EMA, RSI, MACD, Bollinger Bands, etc.)

**L2: Semantic Cache** (AI Responses)
- Key: Hash of (technical_state + risk_profile + language)
- TTL: 300 seconds (5 minutes)
- Purpose: Reduce LLM API calls for similar requests
- Cache Hit Rate Target: >60%

**L3: Pattern & S/R Cache**
- Key: `patterns:{symbol}:{timeframe}`
- TTL: 300 seconds
- Purpose: Candlestick pattern detection results

### Cache Invalidation

- **Automatic TTL Expiry:** Redis cleans up expired keys
- **Manual Invalidation:** Clear specific keys on symbol/timeframe updates
- **Broadcast:** System-wide cache clear on major config changes

---

## Data Flow: Portfolio Analysis

### Sequence Diagram

```
Client                FastAPI              Redis          PostgreSQL       LLM
  │                     │                    │                 │           │
  ├─ portfolio_analysis ─→                                                  │
  │                     │                                                   │
  │                     ├─ Fetch Positions & Account Balance               │
  │                     │                                                   │
  │                     ├─ Parallel Position Analysis (asyncio.gather)     │
  │                     │ ├─ Fetch current price (MT5)                     │
  │                     │ ├─ Calculate technical signals (SMA, EMA, RSI)    │
  │                     │ ├─ Fetch from Redis cache ←───────┤              │
  │                     │ │ (miss: compute & cache)                        │
  │                     │ ├─ Calculate P&L, R-multiple                     │
  │                     │ └─ Determine position risk status                │
  │                     │                                                   │
  │                     ├─ Calculate Portfolio Health                      │
  │                     │ ├─ Total risk exposure                           │
  │                     │ ├─ Max drawdown                                  │
  │                     │ └─ Health score (0-100)                          │
  │                     │                                                   │
  │                     ├─ Check semantic cache ←─────────┤                │
  │                     │ (key: hash of health + risk + positions)         │
  │                     │                                                   │
  │                     ├─ If cache miss: Call LLM ─────────────────────→ │
  │                     │ (with position summaries + health metrics)        │
  │                     │                                                   │
  │                     │ ← LLM response (overall_risk, priority_actions)  │
  │                     │                                                   │
  │                     ├─ Store in Redis semantic cache ─→                │
  │                     │ (TTL: 300s)                                      │
  │                     │                                                   │
  │                     ├─ Build PortfolioAnalysisResponse                 │
  │                     │ ├─ portfolio_health                              │
  │                     │ ├─ position_analysis (array)                     │
  │                     │ ├─ ai_advice                                     │
  │                     │ └─ metadata (cached: bool, computed_at: ts)       │
  │                     │                                                   │
  │ ← portfolio_result ─┤                                                  │
  │                     │                                                   │
```

---

## API & WebSocket Events

### Event: advisor:portfolio_analysis

**Request:**
```json
{
  "positions": [
    {
      "symbol": "EURUSD",
      "entry_price": 1.0850,
      "current_price": 1.0920,
      "size": 1.0,
      "stop_loss": 1.0800
    }
  ],
  "account_balance": 10000,
  "risk_profile": "moderate",
  "language": "en"
}
```

**Response:**
```json
{
  "portfolio_health": {
    "score": 75,
    "status": "HEALTHY",
    "risk_exposure": 0.05,
    "max_drawdown": -2.5,
    "positions_at_risk": 1
  },
  "position_analysis": [
    {
      "symbol": "EURUSD",
      "pnl_pct": 0.81,
      "risk_status": "safe",
      "recommendation": "HOLD"
    }
  ],
  "ai_advice": {
    "overall_risk": "LOW",
    "priority_actions": ["Monitor EURUSD for take profit"],
    "reasoning": "Portfolio appears healthy with positive P&L..."
  },
  "metadata": {
    "cached": false,
    "computed_at": "2025-12-31T10:30:45.123Z"
  }
}
```

### Event: advisor:explain_recommendation

**Request:**
```json
{
  "symbol": "EURUSD",
  "timeframe": "H1"
}
```

**Response:**
```json
{
  "cot_reasoning": {
    "steps": [
      {
        "category": "TREND",
        "analysis": "SMA 21 above SMA 50, uptrend confirmed",
        "points": 3,
        "confidence": 0.95
      },
      ...
    ],
    "recommendation": "BUY",
    "confidence": 0.82
  },
  "provenance": {
    "data_sources": [
      {
        "source": "MT5",
        "type": "price",
        "age_minutes": 1,
        "cache_hit": false,
        "confidence": 0.98
      }
    ],
    "freshness_status": "All data fresh (< 1min)"
  }
}
```

---

## Integration Points

### MT5 Connection

- **Module:** `app/mt5/connection_manager.py`
- **Async Wrapper:** `app/advisor/data_fetcher.py`
- **Circuit Breaker:** Automatic fault tolerance on repeated failures
- **Data:** OHLCV candles for technical analysis

### LLM APIs

**Claude 3.5 Sonnet (Primary)**
- API: `app/advisor/ai_summarizer.py::_get_anthropic_client()`
- Models: claude-3-5-sonnet-20241022
- Timeout: 30 seconds

**DeepSeek (Fallback)**
- API: `app/advisor/ai_summarizer.py::_get_openai_client()`
- Models: deepseek-chat
- Timeout: 30 seconds

### Zalo Webhook (Phase 1)

- **Endpoint:** `POST /api/webhook/zalo/kol-signals` (to be implemented Phase 2)
- **Input:** KOL trading signal from Zalo message
- **Processing:** Extract signal → compute hash → insert into `kol_messages`
- **Deduplication:** UNIQUE constraint on `message_hash` prevents duplicates

---

## Deployment Architecture

### Development

```
localhost:8000  FastAPI dev server
localhost:6379  Redis (in-memory cache)
localhost:5432  PostgreSQL (persistent storage)
```

### Production

```
Cloudflare Workers  API gateway + load balancing
PostgreSQL Cloud    Managed database (backups, replicas)
Redis Cloud         Managed cache (HA, auto-failover)
MT5 Terminal        Windows/WSL (on-premises for now)
```

---

## Security Considerations

1. **Input Validation:** All requests validated via Pydantic before processing
2. **SQL Injection:** N/A (using parameterized queries via asyncpg)
3. **Prompt Injection:** Sanitization in `ai_summarizer.py` before LLM calls
4. **Rate Limiting:** Recommended for production deployment
5. **API Keys:** Never commit `.env` files; use environment variables
6. **WebSocket Auth:** Placeholder for JWT integration

---

## Performance SLOs

| Metric | Target | Notes |
|--------|--------|-------|
| Portfolio Analysis Latency | <5s | P95, including LLM call |
| Cache Hit Rate | >60% | Semantic cache effectiveness |
| LLM API Latency | <3s | P95, excluding network overhead |
| Database Query | <100ms | P95, for indexed lookups |
| WebSocket Roundtrip | <1s | Client → Server → Client |
| MT5 Connection Uptime | >99% | Circuit breaker tolerance |

---

## Monitoring & Observability

### Structured Logging

**Format:** JSON via `python-json-logger`
**Fields:**
- timestamp (ISO 8601)
- level (INFO, WARNING, ERROR)
- service (backend module name)
- operation (function name)
- duration_ms (execution time)
- session_id (user/request ID)
- error (exception message if applicable)

### Metrics to Track

1. Portfolio analysis latency distribution
2. Cache hit rate by key type
3. LLM API failures and retry counts
4. MT5 connection state changes
5. Database query performance (slow query log)
6. WebSocket connection lifecycle

### Alerting Thresholds

- Portfolio analysis latency > 10s: Warn
- Cache hit rate < 30%: Investigate (potential cache configuration issue)
- MT5 connection down > 5min: Critical alert
- LLM API error rate > 10%: Warn
- PostgreSQL connection pool exhaustion: Critical alert

---

## Future Architecture Enhancements

1. **Microservices Split:** Separate technical analysis → recommendation → explanation services
2. **Message Queue:** RabbitMQ/Kafka for async processing + event streaming
3. **Time-Series DB:** InfluxDB for high-frequency indicator caching
4. **Graph Database:** Neo4j for signal correlation analysis
5. **ML Training Pipeline:** Separate training service for accuracy model updates
6. **API Gateway:** Kong/Tyk for advanced rate limiting + authentication
7. **Service Mesh:** Istio for inter-service communication + observability

---

**Last Updated:** 2025-12-31
**Maintainer:** Architecture + Backend Team
**Status:** Phase 5.4 (Integration) + Phase 1 (Database Layer)
