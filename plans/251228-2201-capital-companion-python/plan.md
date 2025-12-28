# Capital Companion Production Implementation Plan (Python Backend)

**Project**: Capital Companion - Production-Ready Gold & Crypto Voice Trading Companion
**Date**: 2025-12-28
**Backend**: Extend existing Python backend (FastAPI + Python-SocketIO)
**Target**: 100-1000 concurrent users (Public beta)
**Cost**: $174/month operational budget

---

## EXECUTIVE SUMMARY

Extend existing Python backend (`backend/`) to transform Monitor 1 CAPITAL COMPANION from UI prototype into production-ready Vietnamese voice trading companion for Gold and Cryptocurrency markets.

### Current Backend State
- ✅ FastAPI + Python-SocketIO (AsyncServer) configured
- ✅ MT5 trading integration (connection manager, trading operations)
- ✅ Session management + reconnection handling
- ✅ Command processor pattern
- ✅ Health check endpoint
- ✅ Cleanup tasks + circuit breaker
- ❌ No market data service (TwelveData)
- ❌ No voice processing (Whisper + VieNeu-TTS)
- ❌ No AI analysis (pattern recognition, sentiment)
- ❌ No database (PostgreSQL) or cache (Redis)
- ❌ No Capital Companion Socket.IO events

### Target State (Extending Existing Backend)
- ✅ **Keep**: MT5 trading functionality (separate concern)
- ✅ **Add**: TwelveData WebSocket service (market data)
- ✅ **Add**: Voice service (Whisper API + VieNeu-TTS client)
- ✅ **Add**: AI services (pattern analyzer, sentiment analyzer, alert generator)
- ✅ **Add**: PostgreSQL client (asyncpg) + Redis client (redis-py)
- ✅ **Add**: Background jobs (APScheduler)
- ✅ **Add**: Capital Companion Socket.IO events
- ✅ **Update**: Configuration, health check, logging

---

## TECHNICAL ARCHITECTURE

### Extended Backend Stack

**Existing** (Keep):
- Python 3.11+
- FastAPI 0.104.0
- Python-SocketIO 5.10.0
- Uvicorn 0.24.0
- MT5 integration (trading)

**New Dependencies** (Add):
```txt
# Market Data
websockets==12.0  # TwelveData WebSocket client

# Voice Processing
aiohttp==3.10.11  # VieNeu-TTS HTTP client
httpx==0.28.1  # Whisper API client

# Database & Cache
asyncpg==0.30.0  # PostgreSQL async driver
redis==5.2.1  # Redis client

# AI & Analysis
ta==0.11.0  # Technical Analysis library (RSI, SMA, MACD)
vaderSentiment==3.3.2  # Sentiment analysis

# Background Jobs
APScheduler==3.11.0  # Cron-like job scheduler

# Monitoring
sentry-sdk==2.21.0  # Error tracking
logtail-python==0.2.9  # Log aggregation
prometheus-client==0.21.1  # Metrics

# Utilities
pydantic==2.10.6  # Data validation
pydantic-settings==2.7.0  # Settings management
```

**Infrastructure** (Self-Hosted):
- VPS: Hetzner CPX31 (8GB RAM, 4 vCPU) - $20/mo
- PostgreSQL 16 (self-hosted)
- Redis 7 (self-hosted)
- Docker + Docker Compose
- Nginx (reverse proxy, SSL)
- Supervisor or PM2 equivalent

**External Services**:
- TwelveData Pro WebSocket ($79/mo)
- OpenAI Whisper API ($0.006/min)
- VieNeu-TTS (own server - $0)
- NewsAPI (free tier - 100 req/day)

---

## EXTENDED FILE STRUCTURE

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # Extend: Add Capital Companion services
│   ├── sio.py                      # Keep: Socket.IO server config
│   ├── config.py                   # Extend: Add new env variables
│   ├── logging_config.py           # Extend: Add Sentry + Logtail
│   │
│   ├── mt5/                        # Keep: Existing MT5 trading
│   │   ├── connection_manager.py
│   │   ├── trading_operations.py
│   │   ├── circuit_breaker.py
│   │   └── error_handler.py
│   │
│   ├── capital_companion/          # NEW: Capital Companion services
│   │   ├── __init__.py
│   │   ├── market_data_service.py  # TwelveData WebSocket client
│   │   ├── voice_service.py        # Whisper + VieNeu-TTS
│   │   ├── pattern_analyzer.py     # Technical analysis
│   │   ├── sentiment_analyzer.py   # News sentiment
│   │   ├── alert_generator.py      # Proactive alerts
│   │   └── personalization.py      # Learning engine
│   │
│   ├── database/                   # NEW: Database layer
│   │   ├── __init__.py
│   │   ├── postgres_client.py      # PostgreSQL connection pool
│   │   ├── redis_client.py         # Redis client wrapper
│   │   └── models.py               # Database models (user_profiles, alert_history, etc.)
│   │
│   ├── events/                     # Extend: Add Capital Companion events
│   │   ├── trading_events.py       # Keep: MT5 trading events
│   │   ├── market_events.py        # NEW: Market data events
│   │   ├── voice_events.py         # NEW: Voice interaction events
│   │   └── alert_events.py         # NEW: Alert events
│   │
│   ├── processors/                 # Keep: Command processor pattern
│   │   ├── command_processor.py    # Keep: MT5 command processor
│   │   └── intent_processor.py     # NEW: Voice intent classifier
│   │
│   ├── jobs/                       # NEW: Background jobs
│   │   ├── __init__.py
│   │   ├── pattern_analysis_job.py # Pattern detection (every 5 min)
│   │   ├── sentiment_update_job.py # Sentiment update (every 15 min)
│   │   └── alert_check_job.py      # Alert generation (every 30s)
│   │
│   ├── tasks/                      # Keep: Existing cleanup task
│   │   └── cleanup_task.py
│   │
│   ├── models/                     # Extend: Add Capital Companion models
│   │   ├── responses.py            # Keep: MT5 responses
│   │   ├── market_data.py          # NEW: Market data types
│   │   ├── voice.py                # NEW: Voice types
│   │   └── alerts.py               # NEW: Alert types
│   │
│   ├── utils/                      # NEW: Utility modules
│   │   ├── confidence_scorer.py    # Confidence calculation
│   │   └── vietnamese_responses.py # Vietnamese text templates
│   │
│   ├── session_manager.py          # Keep: Session management
│   ├── reconnection_manager.py     # Keep: Reconnection handling
│   └── validation.py               # Keep: Input validation
│
├── db/                             # NEW: Database scripts
│   ├── migrations/
│   │   └── 001_initial_schema.sql
│   └── seeds/
│       └── test_users.sql
│
├── requirements.txt                # Extend: Add new dependencies
├── Dockerfile                      # Update: Multi-service container
├── docker-compose.yml              # NEW: PostgreSQL + Redis + Backend
├── .env.example                    # Extend: Add new env vars
└── README.md                       # Update: Capital Companion docs
```

---

## IMPLEMENTATION PHASES

### Phase 1: Infrastructure & Database (Week 1)
**Goal**: PostgreSQL + Redis operational, integrated with backend

**Tasks**:
1. Provision VPS (Hetzner CPX31 or equivalent)
2. Install Docker + Docker Compose
3. Create `docker-compose.yml` (PostgreSQL + Redis + Backend)
4. Create PostgreSQL schemas (`db/migrations/001_initial_schema.sql`)
5. Create `app/database/postgres_client.py` (asyncpg connection pool)
6. Create `app/database/redis_client.py` (Redis client wrapper)
7. Create `app/database/models.py` (Pydantic models for user profiles, alerts, etc.)
8. Update `app/config.py` (add database connection strings)
9. Extend `app/main.py` lifespan (initialize database + Redis)
10. Add database health check to `/health` endpoint

**Files Created/Modified**:
- `docker-compose.yml` (NEW)
- `db/migrations/001_initial_schema.sql` (NEW)
- `app/database/postgres_client.py` (NEW)
- `app/database/redis_client.py` (NEW)
- `app/database/models.py` (NEW)
- `app/config.py` (EXTEND)
- `app/main.py` (EXTEND)
- `requirements.txt` (EXTEND: asyncpg, redis)

**Acceptance**:
- [ ] PostgreSQL accessible from backend
- [ ] Redis responding to SET/GET commands
- [ ] Backend connects to both on startup
- [ ] Health check shows database status

**Details**: See `phase-01-infrastructure-database.md`

---

### Phase 2: Market Data Service (Week 2)
**Goal**: Real-time Gold + Crypto prices via TwelveData WebSocket

**Tasks**:
1. Install `websockets` library
2. Create `app/capital_companion/market_data_service.py`
   - TwelveData WebSocket client (connect, subscribe, handle messages)
   - Redis caching (5s TTL)
   - Broadcast to Socket.IO clients
3. Create `app/events/market_events.py`
   - `market:subscribe` event (client subscribes to symbols)
   - `market:unsubscribe` event
4. Create `app/models/market_data.py` (MarketUpdate, MarketSubscription types)
5. Integrate into `app/main.py` lifespan (start market data service)
6. Update `requirements.txt` (add websockets, twelvedata config)
7. Test with frontend (SocketContext already exists)

**Files Created/Modified**:
- `app/capital_companion/market_data_service.py` (NEW)
- `app/events/market_events.py` (NEW)
- `app/models/market_data.py` (NEW)
- `app/main.py` (EXTEND)
- `requirements.txt` (EXTEND: websockets)

**Acceptance**:
- [ ] Frontend receives real-time XAUUSD, BTCUSD, ETHUSD prices
- [ ] Prices update every 5 seconds
- [ ] Latency < 1 second from TwelveData → UI
- [ ] WebSocket auto-reconnects on disconnect

**Details**: See `phase-02-market-data-service.md`

---

### Phase 3: Voice Interaction (Week 3)
**Goal**: Vietnamese voice conversation (Whisper + VieNeu-TTS)

**Tasks**:
1. Install `httpx`, `aiohttp` libraries
2. Create `app/capital_companion/voice_service.py`
   - `transcribe(audio_buffer)` → Whisper API
   - `synthesize(text)` → VieNeu-TTS server
3. Create `app/processors/intent_processor.py`
   - Keyword matching for Vietnamese commands
   - Intent classification (query_price, analyze_chart, get_alerts)
4. Create `app/utils/vietnamese_responses.py`
   - Response templates in Vietnamese
5. Create `app/events/voice_events.py`
   - `voice:start`, `voice:audio`, `voice:stop` events
   - Audio streaming logic
6. Create `app/models/voice.py` (VoiceTranscription, VoiceResponse types)
7. Store voice interactions in PostgreSQL
8. Test roundtrip latency (<4s target)

**Files Created/Modified**:
- `app/capital_companion/voice_service.py` (NEW)
- `app/processors/intent_processor.py` (NEW)
- `app/utils/vietnamese_responses.py` (NEW)
- `app/events/voice_events.py` (NEW)
- `app/models/voice.py` (NEW)
- `requirements.txt` (EXTEND: httpx, aiohttp)

**Acceptance**:
- [ ] User speaks "Giá vàng bao nhiêu?"
- [ ] Atlas responds "Giá vàng hiện tại $2,105.50, tăng 2.3% hôm nay"
- [ ] Roundtrip latency < 4 seconds
- [ ] Voice quality acceptable

**Details**: See `phase-03-voice-interaction.md`

---

### Phase 4: AI Pattern Recognition (Week 4)
**Goal**: Technical analysis with confidence scores

**Tasks**:
1. Install `ta` library (Technical Analysis)
2. Create `app/capital_companion/pattern_analyzer.py`
   - Fetch historical data (TwelveData REST API)
   - Calculate RSI, SMA, MACD, Bollinger Bands
   - Detect patterns (divergence, crossover, breakout)
   - Calculate confidence scores
3. Create `app/jobs/pattern_analysis_job.py`
   - APScheduler job (runs every 5 minutes)
   - Analyze all symbols in watchlists
   - Cache results in Redis
4. Create `app/utils/confidence_scorer.py`
   - Multi-factor confidence calculation
5. Store pattern analysis in PostgreSQL
6. Emit patterns via Socket.IO to frontend

**Files Created/Modified**:
- `app/capital_companion/pattern_analyzer.py` (NEW)
- `app/jobs/pattern_analysis_job.py` (NEW)
- `app/utils/confidence_scorer.py` (NEW)
- `app/main.py` (EXTEND: start APScheduler)
- `requirements.txt` (EXTEND: ta, APScheduler)

**Acceptance**:
- [ ] Atlas detects bullish divergence on BTCUSD H4
- [ ] Alert: "Bitcoin: Phân kỳ tăng giá H4 (Độ tin cậy: 82%)"
- [ ] User taps alert → shows reasoning (RSI, SMA values)

**Details**: See `phase-04-pattern-recognition.md`

---

### Phase 5: Sentiment Analysis (Week 5)
**Goal**: News-based market sentiment

**Tasks**:
1. Install `vaderSentiment` library
2. Create `app/capital_companion/sentiment_analyzer.py`
   - Fetch news (NewsAPI)
   - Analyze sentiment (VADER)
   - Aggregate scores (Fear/Neutral/Greed)
3. Create `app/jobs/sentiment_update_job.py`
   - APScheduler job (runs every 15 minutes)
   - Cache sentiment in Redis (15 min TTL)
4. Integrate sentiment into voice responses
5. Emit sentiment updates via Socket.IO

**Files Created/Modified**:
- `app/capital_companion/sentiment_analyzer.py` (NEW)
- `app/jobs/sentiment_update_job.py` (NEW)
- `app/utils/vietnamese_responses.py` (EXTEND)
- `requirements.txt` (EXTEND: vaderSentiment)

**Acceptance**:
- [ ] Sentiment updates every 15 minutes
- [ ] Atlas: "Tâm lý thị trường Bitcoin: Tham lam (65%)"
- [ ] Frontend shows Fear/Greed gauge

**Details**: See `phase-05-sentiment-analysis.md`

---

### Phase 6: Personalized Learning (Week 6)
**Goal**: User preference learning

**Tasks**:
1. Create user profile CRUD endpoints (FastAPI routes)
2. Track alert interactions (acted, dismissed, ignored)
3. Create `app/capital_companion/personalization.py`
   - Learning algorithms (pattern frequency, success rate)
   - Alert filtering logic
4. Update alert generation to respect user preferences
5. Create personalized dashboard endpoint

**Files Created/Modified**:
- `app/capital_companion/personalization.py` (NEW)
- `app/main.py` (EXTEND: add FastAPI routes)
- `app/database/models.py` (EXTEND)

**Acceptance**:
- [ ] User dismisses 3 RSI alerts → Atlas stops sending RSI alerts
- [ ] User profitable on H4 breakouts → Atlas prioritizes H4 alerts
- [ ] Atlas: "Chào buổi sáng! Mô hình H4 vàng bạn thích đang hình thành"

**Details**: See `phase-06-personalized-learning.md`

---

### Phase 7: Proactive Alert System (Week 7)
**Goal**: Multi-source proactive alerts

**Tasks**:
1. Create `app/capital_companion/alert_generator.py`
   - Combine patterns + sentiment + risk warnings
   - Personalization filtering
2. Create `app/jobs/alert_check_job.py`
   - APScheduler job (runs every 30 seconds)
   - Check all users' watchlists
3. Create `app/events/alert_events.py`
   - `alert:new` event
   - Alert history tracking
4. Create `app/models/alerts.py` (Alert, AlertReasoning types)
5. Emit alerts via Socket.IO

**Files Created/Modified**:
- `app/capital_companion/alert_generator.py` (NEW)
- `app/jobs/alert_check_job.py` (NEW)
- `app/events/alert_events.py` (NEW)
- `app/models/alerts.py` (NEW)

**Acceptance**:
- [ ] User has XAUUSD on watchlist → Atlas alerts breakout within 30s
- [ ] Sentiment shifts Fear→Greed → Atlas notifies
- [ ] All alerts include confidence + reasoning

**Details**: See `phase-07-proactive-alerts.md`

---

### Phase 8: Production Hardening (Week 8)
**Goal**: Ready for 100-1000 users

**Tasks**:
1. Setup Nginx reverse proxy + SSL (Let's Encrypt)
2. Configure Supervisor/systemd for backend process management
3. Implement rate limiting (per-user quotas)
4. Add Sentry error tracking
5. Add Logtail log aggregation
6. Setup Grafana Cloud + Prometheus metrics
7. Configure PostgreSQL backups (daily, 7-day retention)
8. Load testing (1000 concurrent WebSocket connections)
9. Security audit (SQL injection, XSS, secrets exposure)
10. Write operational runbook

**Files Created/Modified**:
- `nginx/nginx.conf` (NEW)
- `supervisor/capital-companion.conf` (NEW)
- `app/logging_config.py` (EXTEND: Sentry + Logtail)
- `app/main.py` (EXTEND: Prometheus metrics)
- `requirements.txt` (EXTEND: sentry-sdk, logtail-python, prometheus-client)

**Acceptance**:
- [ ] 1000 concurrent WebSocket connections stable
- [ ] 99% uptime over 7 days
- [ ] All errors tracked in Sentry
- [ ] Voice latency p95 < 4 seconds
- [ ] Database backup tested (restore successful)

**Details**: See `phase-08-production-hardening.md`

---

## DATABASE SCHEMA (PostgreSQL)

```sql
-- User Profiles
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT UNIQUE NOT NULL,
  risk_tolerance TEXT CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),
  preferred_timeframes TEXT[],
  watchlist TEXT[],
  voice_enabled BOOLEAN DEFAULT true,
  language TEXT DEFAULT 'vi',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alert History
CREATE TABLE alert_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id),
  alert_type TEXT NOT NULL,
  symbol TEXT NOT NULL,
  message TEXT NOT NULL,
  confidence NUMERIC(3,2),
  reasoning JSONB,
  user_action TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Voice Interactions
CREATE TABLE voice_interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id),
  transcript TEXT NOT NULL,
  response TEXT NOT NULL,
  intent TEXT,
  duration_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_alert_history_user_id ON alert_history(user_id);
CREATE INDEX idx_alert_history_created_at ON alert_history(created_at DESC);
CREATE INDEX idx_voice_interactions_user_id ON voice_interactions(user_id);
CREATE INDEX idx_voice_interactions_created_at ON voice_interactions(created_at DESC);
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

---

## DOCKER COMPOSE CONFIGURATION

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: capital_companion
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend (Capital Companion + MT5)
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=capital_companion
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - TWELVEDATA_KEY=${TWELVEDATA_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - VIENEU_TTS_URL=${VIENEU_TTS_URL}
      - NEWSAPI_KEY=${NEWSAPI_KEY}
      - SENTRY_DSN=${SENTRY_DSN}
      - LOGTAIL_TOKEN=${LOGTAIL_TOKEN}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./backend:/app
      - ./logs:/app/logs

volumes:
  postgres_data:
  redis_data:
```

---

## SUCCESS METRICS

### Functional
- [ ] Market data latency < 1 second (p95)
- [ ] Voice response latency < 4 seconds (p95)
- [ ] Pattern detection accuracy > 60% (30-day)
- [ ] Confidence calibration (70% confident = 70% accurate)

### Reliability
- [ ] Uptime > 99%
- [ ] WebSocket reconnection success > 95%
- [ ] Zero data loss during reconnections
- [ ] TwelveData connection uptime > 99%

### User Engagement
- [ ] DAU > 30% of total users
- [ ] Avg voice interactions > 5/day/user
- [ ] Alert action rate > 20%
- [ ] Day-30 retention > 40%

### Trust
- [ ] All alerts include confidence scores
- [ ] All recommendations include reasoning
- [ ] Risk warnings on high volatility
- [ ] NPS > 40

---

## OPERATIONAL COST

| Service | Monthly Cost |
|---------|-------------|
| Hetzner CPX31 VPS | $20 |
| TwelveData Pro | $79 |
| Whisper API (10k min) | $60 |
| VieNeu-TTS | $0 (own server) |
| Domain + SSL | $10 |
| Backup Storage | $5 |
| **TOTAL** | **$174** |

**Break-even**: $0.17/user/month (1000 users)

---

## RISK MITIGATION

### Risk 1: TwelveData Downtime
**Mitigation**: Fallback to REST API polling

### Risk 2: Whisper Rate Limits
**Mitigation**: Queue requests, upgrade tier

### Risk 3: VPS Failure
**Mitigation**: Automated backups, failover VPS (Phase 9)

### Risk 4: Data Loss
**Mitigation**: Daily PostgreSQL backups to off-server storage

### Risk 5: Memory Pressure
**Mitigation**: Monitor via Prometheus, async processing

---

## NEXT STEPS

1. **Review Plan** - Confirm approach fits existing backend
2. **Setup VPS** - Provision Hetzner server
3. **Phase 1** - Database integration (PostgreSQL + Redis)
4. **Sequential Execution** - Complete phases 1-8 in order

**Detailed Phases**:
- `phase-01-infrastructure-database.md`
- `phase-02-market-data-service.md`
- `phase-03-voice-interaction.md`
- `phase-04-pattern-recognition.md`
- `phase-05-sentiment-analysis.md`
- `phase-06-personalized-learning.md`
- `phase-07-proactive-alerts.md`
- `phase-08-production-hardening.md`

**Reference**:
- Brainstorm: `plans/reports/brainstorm-251228-2143-capital-companion-production-adjusted.md`
- MT5 Plan: `plans/20251221-mt5-socketio-trading-server/plan.md`
- Existing Backend: `backend/`

---

## VALIDATION SUMMARY

**Date**: 2025-12-28
**Validated By**: User
**Status**: Approved with confirmed decisions

### Validated Decisions

1. **Architecture: Keep Monolith** ✓
   - Decision: MT5 trading and Capital Companion remain in same Python process
   - Rationale: Simpler deployment, shared Socket.IO server, isolated modules
   - Alternative rejected: Separate services (adds deployment complexity)

2. **NewsAPI Rate Limit: Reduce Check Frequency** ✓
   - Decision: Sentiment updates every 1 hour (96 req/day)
   - Rationale: Stays within free tier (100 req/day), news sentiment doesn't need 15-min granularity
   - Impact: Phase 5 sentiment_update_job.py interval changed from 15min → 60min
   - Alternative rejected: Paid tier ($449/mo) deemed unnecessary for MVP

3. **Timeline: Sequential Phases** ✓
   - Decision: Execute phases 1-8 sequentially (8 weeks)
   - Rationale: Safer for solo developer, easier validation between phases
   - Alternative rejected: Parallel phases (Phase 2+3 or Phase 4-7) require larger team

4. **TwelveData Downtime: REST Fallback Acceptable** ✓
   - Decision: 5-30 second downtime tolerance during WebSocket reconnection
   - Rationale: REST fallback in market_data_service.py handles gaps, users tolerate brief delays
   - Alternative rejected: Dual WebSocket providers (adds $199/mo for Polygon.io)

5. **Personalization: Auto-Filter After 3 Dismissals** ✓
   - Decision: System implicitly learns user preferences
   - Rationale: Reduces alert noise, users can re-enable in settings
   - Implementation: personalization.py tracks dismissals, auto-adds to filtered_patterns

6. **Background Jobs: APScheduler Sufficient** ✓
   - Decision: APScheduler for all background jobs (<1000 users)
   - Rationale: Simpler than Celery, adequate for target scale, runs in same process
   - Alternative rejected: Celery + Redis (production-grade but overkill for MVP)

7. **Voice Interaction Cost: 30-60 Seconds Expected** ✓
   - Decision: Budget remains $60/mo (10k min)
   - Rationale: Quick queries ("What's gold price?", "Any alerts?") not in-depth analysis
   - No usage limits needed at current scale

8. **Deployment: Supervisor Process Management** ✓
   - Decision: Use Supervisor for production VPS
   - Rationale: Simple, widely adopted for Python apps, plan already includes config
   - Alternative rejected: systemd (requires different config), Docker Swarm (overkill for single VPS)

### Implementation Adjustments

**Phase 5 Change**:
```python
# backend/app/jobs/sentiment_update_job.py
# OLD: scheduler.add_job(update_all_sentiment, 'interval', minutes=15)
# NEW: scheduler.add_job(update_all_sentiment, 'interval', minutes=60)
```

**Redis TTL Adjustment**:
```python
# sentiment_analyzer.py
# Increase TTL to match new check frequency
await redis.cache_sentiment(symbol, data, ttl=3600)  # Was: 900s (15min)
```

### Confirmed Risks

- **TwelveData WebSocket**: 5-30s downtime acceptable, REST fallback mitigates
- **Whisper Rate Limits**: Queue requests, monitor usage, upgrade if exceeded
- **VPS Single Point of Failure**: Daily backups mitigate, Phase 9 failover VPS if scaling beyond 1000 users
- **NewsAPI Free Tier**: Hourly updates sufficient for news-based sentiment

### Action Items

1. ✅ Plan validated and approved
2. ⬜ Update Phase 5 documentation with 60-min interval
3. ⬜ Provision Hetzner VPS CPX31
4. ⬜ Begin Phase 1: Infrastructure & Database

---

**Plan Status**: Validated and approved for implementation
**Architecture**: Python monolithic backend extension (not Node.js rewrite)
**Estimated Timeline**: 8 weeks (sequential execution)
**Operational Cost**: $174/month (within budget)
