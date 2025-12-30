---
title: "AI Trading Advisor - Technical Analysis Engine"
description: "Extend Capital Companion with full technical analysis, pattern recognition, risk management, and personalized AI recommendations"
status: in-progress
priority: P1
effort: 32h
branch: main
tags: [ai, trading, technical-analysis, advisor, python, socketio]
created: 2025-12-30
validated: 2025-12-30
phase-01-completed: 2025-12-30
phase-02-completed: 2025-12-30
phase-03-completed: 2025-12-30
phase-04-completed: 2025-12-30
---

# AI Trading Advisor Implementation Plan

## Executive Summary

Extend existing Python backend (`backend/app/`) to transform Capital Companion into a production-ready AI trading advisor with full technical analysis capabilities. The system will provide comprehensive market analysis, pattern recognition, support/resistance calculations, risk management, and personalized recommendations via Socket.IO events.

**Key Decisions Made:**
1. **Library:** `pandas-ta` (ease of install, 150+ indicators, 60 candlestick patterns)
2. **LLM:** DeepSeek for summaries (cost), ChatGPT (GPT-4) for recommendations (quality) - configurable
3. **Data Source:** Hybrid MT5 (primary price) + TwelveData (volume validation) - tick accuracy + market confirmation
4. **Caching:** Redis with 1min TTL for computed indicators
5. **Volume Validation:** Compare MT5 broker volume vs TwelveData market volume (detect fake pumps)
6. **Pattern Detection:** Rule-based (Phase 1-2), ML optional (Phase 3+)
7. **Risk Management:** Hard limits enforced (not advisory)
8. **Vietnamese:** LLM-native (ship and iterate)

**Example User Flow:**
```
User: "Get Technical Summary for XAUUSD"
→ System fetches OHLCV from MT5 (tick-level price accuracy)
→ System fetches volume from TwelveData (market-wide volume comparison)
→ Volume analysis: Compares MT5 broker volume vs TwelveData market volume
→ Computes: SMA/EMA, RSI, MACD, Bollinger, ATR, Volume Profile (cached 1min)
→ Detects: Candlestick patterns, S/R levels, trend, volume divergence
→ Calculates: Position size with hard limit enforcement, stop loss, R/R ratio
→ LLM generates: DeepSeek for summary, ChatGPT for recommendation (user preference)
→ Returns: Structured analysis + volume confirmation + Vietnamese recommendation
```

---

## Technical Architecture

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│              Socket.IO Client (existing SocketContext)           │
└─────────────────────────────────────────┬───────────────────────┘
                                          │
                    Socket.IO Events (advisor:*)
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Python Backend (FastAPI + SocketIO)          │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │   MT5 Module   │  │ Advisor Module │  │  Session Manager │   │
│  │   (existing)   │  │    (NEW)       │  │    (existing)    │   │
│  └───────┬────────┘  └───────┬────────┘  └──────────────────┘   │
│          │                   │                                   │
│          │    ┌──────────────┴──────────────┐                   │
│          │    │         advisor/            │                   │
│          │    ├── technical_analyzer.py     │ ← pandas-ta       │
│          │    ├── pattern_detector.py       │ ← candlestick     │
│          │    ├── risk_analyzer.py          │ ← position sizing │
│          │    ├── ai_summarizer.py          │ ← Claude/DeepSeek │
│          │    └── recommendation_engine.py  │ ← personalized    │
│          │    └──────────────┬──────────────┘                   │
│          │                   │                                   │
│          ▼                   ▼                                   │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────┐  │
│  │    MT5      │      │    Redis    │      │   PostgreSQL    │  │
│  │  Terminal   │      │   (cache)   │      │  (user prefs)   │  │
│  └─────────────┘      └─────────────┘      └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### New Directory Structure

```
backend/app/
├── advisor/                          # NEW: AI Trading Advisor
│   ├── __init__.py
│   ├── technical_analyzer.py         # Indicators: SMA, EMA, RSI, MACD, BB, ATR
│   ├── pattern_detector.py           # Candlestick + Chart patterns
│   ├── support_resistance.py         # S/R levels, Fibonacci, pivot points
│   ├── risk_analyzer.py              # Position sizing, R/R, drawdown
│   ├── ai_summarizer.py              # LLM integration (Claude/DeepSeek)
│   ├── recommendation_engine.py      # Personalized advice generation
│   └── data_fetcher.py               # OHLCV data from MT5/TwelveData
│
├── events/
│   ├── trading_events.py             # KEEP: existing MT5 events
│   └── advisor_events.py             # NEW: advisor:* Socket.IO events
│
├── models/
│   ├── responses.py                  # KEEP: existing response models
│   ├── advisor_models.py             # NEW: TechnicalSummary, Pattern, Risk
│   └── user_profile.py               # NEW: User risk profile, preferences
│
├── database/                         # NEW: Database layer
│   ├── __init__.py
│   ├── postgres_client.py            # PostgreSQL async client
│   ├── redis_client.py               # Redis cache wrapper
│   └── schemas.py                    # SQL schemas for user data
│
└── processors/
    ├── command_processor.py          # KEEP: existing MT5 processor
    └── advisor_processor.py          # NEW: Advisor command routing
```

### New Socket.IO Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `advisor:technical_summary` | Client → Server | Request full technical analysis |
| `advisor:technical_result` | Server → Client | Return analysis results |
| `advisor:pattern_scan` | Client → Server | Scan for chart/candlestick patterns |
| `advisor:pattern_result` | Server → Client | Return detected patterns |
| `advisor:risk_analysis` | Client → Server | Calculate risk metrics |
| `advisor:risk_result` | Server → Client | Return position sizing, R/R |
| `advisor:recommendation` | Client → Server | Get personalized advice |
| `advisor:recommendation_result` | Server → Client | Return LLM-generated recommendation |
| `advisor:error` | Server → Client | Error response for advisor events |

### Database Schema Additions

```sql
-- User analysis preferences (extends existing user_profiles)
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS
  risk_vr NUMERIC(4,3) DEFAULT 0.02,                    -- Value at Risk (2%)
  preferred_indicators TEXT[] DEFAULT '{RSI,MACD,SMA}',
  preferred_timeframes TEXT[] DEFAULT '{H1,H4,D1}',
  max_position_risk NUMERIC(3,2) DEFAULT 0.02,          -- 2% per trade
  analysis_language TEXT DEFAULT 'vi';

-- Analysis history (for learning)
CREATE TABLE IF NOT EXISTS analysis_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id),
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  analysis_type TEXT NOT NULL,                          -- summary, pattern, risk
  signal TEXT,                                          -- BUY, SELL, HOLD
  confidence NUMERIC(3,2),
  reasoning JSONB,
  user_feedback TEXT,                                   -- accepted, ignored, rejected
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pattern detection cache
CREATE TABLE IF NOT EXISTS pattern_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  pattern_type TEXT NOT NULL,
  pattern_data JSONB NOT NULL,
  confidence NUMERIC(3,2),
  detected_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  UNIQUE(symbol, timeframe, pattern_type)
);

-- Recommendation tracking
CREATE TABLE IF NOT EXISTS recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id),
  symbol TEXT NOT NULL,
  recommendation TEXT NOT NULL,                         -- BUY, SELL, HOLD
  entry_price NUMERIC(20,8),
  stop_loss NUMERIC(20,8),
  take_profit NUMERIC(20,8),
  position_size NUMERIC(20,8),
  confidence NUMERIC(3,2),
  reasoning TEXT,
  outcome TEXT,                                         -- profit, loss, pending
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_analysis_history_user_symbol ON analysis_history(user_id, symbol);
CREATE INDEX idx_pattern_cache_symbol_tf ON pattern_cache(symbol, timeframe);
CREATE INDEX idx_recommendations_user ON recommendations(user_id, created_at DESC);
```

---

## Implementation Phases

### Phase 1: Technical Analysis Engine (8h) - DONE
**Completed:** 2025-12-30

**Goal:** Core indicator calculations with pandas-ta + Redis caching + Volume validation

**Deliverables:**
- [x] `backend/app/advisor/technical_analyzer.py` - 10 indicators (SMA, EMA, RSI, MACD, BB, ATR, ADX, Stochastic, OBV)
- [x] `backend/app/advisor/data_fetcher.py` - MT5 primary OHLCV data fetcher
- [x] `backend/app/database/redis_client.py` - Redis client with 60s cache TTL
- [x] `backend/app/events/advisor_events.py` - `advisor:technical_summary`, `advisor:multi_timeframe` events
- [x] `backend/app/models/advisor_models.py` - Response models for technical analysis
- [x] `backend/app/processors/advisor_processor.py` - Event processor routing
- [x] `backend/app/config.py` - Updated with Redis config
- [x] `backend/app/main.py` - Integrated advisor events
- [x] `tests/test_technical_analyzer.py` - Unit tests for indicators
- [x] `backend/requirements.txt` - Updated dependencies

**Completion Details:**
- Redis caching: 60s TTL (adjusted from 5min for fresher data)
- Technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, ADX, Stochastic, OBV
- Socket.IO events: `advisor:technical_summary`, `advisor:multi_timeframe`
- Tests: All unit tests written and passing
- Code review: Critical issues fixed, production-ready

**Volume Validation Logic:** (Deferred to Phase 2)
- Will integrate TwelveData volume comparison in pattern detection phase
- Placeholder for MT5 broker volume comparison logic

**Details:** See `phase-01-technical-analysis-engine.md`

---

### Phase 2: Pattern Recognition & S/R (8h)
**Goal:** Candlestick patterns, chart patterns, support/resistance levels

**Deliverables:**
- `advisor/pattern_detector.py` - 60+ candlestick patterns via pandas-ta
- `advisor/support_resistance.py` - Pivot points, Fibonacci, swing H/L
- `events/advisor_events.py` - `advisor:pattern_scan` event
- Multi-timeframe alignment logic

**Details:** See `phase-02-pattern-recognition-sr.md`

---

### Phase 3: Risk Analyzer & Position Sizing (6h) - DONE
**Completed:** 2025-12-30

**Goal:** Risk management calculations for professional trading

**Deliverables:**
- [x] `advisor/risk_analyzer.py` - Fixed fractional, Kelly, ATR-based sizing
- [x] Stop loss calculations based on S/R, ATR
- [x] R/R ratio evaluation
- [x] `events/advisor_events.py` - `advisor:risk_analysis` event
- [x] `models/advisor_models.py` - Risk analysis models
- [x] `tests/test_risk_analyzer.py` - 20 unit tests (all passing)

**Completion Details:**
- Position sizing: Fixed Fractional, Kelly Criterion, ATR-based
- Risk/Reward calculator with recommendations
- Stop loss optimization (ATR + S/R methods)
- Risk profiles: Conservative (1%), Moderate (2%), Aggressive (3%)
- Hard limit enforcement (max 10% position size)
- Comprehensive test coverage: 20/20 tests passing
- Code review: Production-ready

**Details:** See `phase-03-risk-analyzer.md`
**Report:** See `plans/reports/implementation-251230-1559-phase-03-risk-analyzer.md`

---

### Phase 4: AI Summarizer & Recommendations (10h) - DONE
**Completed:** 2025-12-30

**Goal:** LLM-powered analysis summaries and personalized advice

**Deliverables:**
- [x] `advisor/ai_summarizer.py` - Claude/DeepSeek integration
- [x] `advisor/recommendation_engine.py` - User profile-aware recommendations
- [x] `models/user_profile.py` - Risk profile, preferences
- [x] `events/advisor_events.py` - `advisor:recommendation` event
- [x] Vietnamese language support
- [x] Semantic caching for cost optimization
- [x] `tests/test_phase_04_ai_recommendations.py` - 42 unit tests (all passing)

**Completion Details:**
- Claude 3.7 Sonnet + DeepSeek integration with semantic caching
- Personalized recommendations based on user risk profile (conservative/moderate/aggressive)
- Vietnamese + English bilingual support
- Error resilience with graceful degradation (HOLD signal on LLM failures)
- Position sizing with ATR-based targets
- Comprehensive test coverage: 42/42 tests passing (100%)
- Code review: Production-ready, no critical issues

**Details:** See `phase-04-ai-recommendations.md`
**Report:** See `plans/reports/code-review-251230-1650-phase-04-ai-recommendations.md`

---

## Success Metrics

### Technical
- [ ] Indicator computation latency < 500ms (cached < 50ms)
- [ ] Pattern detection accuracy > 85% (backtested)
- [ ] S/R level accuracy within 0.5% of actual bounces
- [ ] LLM response latency < 3s (cached < 200ms)

### Functional
- [ ] All 4 Socket.IO events operational
- [ ] 10+ indicators available (SMA, EMA, RSI, MACD, BB, ATR, ADX, OBV, MFI, Stochastic)
- [ ] 20+ candlestick patterns detected
- [ ] Position sizing for 3 risk profiles (conservative, moderate, aggressive)

### User Experience
- [ ] Vietnamese summaries grammatically correct
- [ ] Confidence scores correlate with accuracy (70% confident = 70% hit rate)
- [ ] Recommendations include clear reasoning

### Cost
- [ ] LLM costs < $50/month (1000 analyses)
- [ ] Semantic cache hit rate > 70%

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| pandas-ta missing patterns | Medium | Fallback to TA-Lib for specific patterns |
| LLM hallucinations | High | Validate signals against computed indicators before output |
| Redis downtime | Medium | Fallback to in-memory cache (LRU dict) |
| MT5 data gaps | Medium | Use TwelveData as secondary data source |
| Vietnamese quality | Low | Review and template common phrases |

---

## Dependencies

### New Python Packages
```txt
# Technical Analysis
pandas-ta==0.3.14b     # 150+ indicators, 60 candlestick patterns
pandas==2.0.3          # Data manipulation
numpy==1.24.3          # Numerical operations

# LLM Integration
anthropic==0.40.0      # Claude API
openai==1.58.1         # DeepSeek (OpenAI-compatible)

# Caching
redis==5.2.1           # Redis client (already in plan)

# Database
asyncpg==0.30.0        # PostgreSQL (already in plan)
```

### External Services
- DeepSeek API ($0.70/2M tokens) - Technical summaries
- ChatGPT API (GPT-4: $2.50/$10 per MTok) - Recommendations
- MT5 Terminal (broker data) - Primary OHLCV (tick-level price)
- TwelveData Pro ($79/mo) - Volume comparison/validation
- Redis (self-hosted) - Indicator cache (1min TTL)
- PostgreSQL (self-hosted) - User profiles, history

---

## Next Steps

1. Review and approve plan
2. Begin Phase 1: Technical Analysis Engine
3. Sequential execution through Phase 4
4. Integration testing with frontend

---

## Phase Files

- `phase-01-technical-analysis-engine.md`
- `phase-02-pattern-recognition-sr.md`
- `phase-03-risk-analyzer.md`
- `phase-04-ai-recommendations.md`

---

## References

- Research: `plans/251230-1417-ai-trading-advisor/research/researcher-01-technical-analysis.md`
- Architecture: `plans/reports/researcher-251230-1418-ai-trading-advisor-architecture.md`
- Base Plan: `plans/251228-2201-capital-companion-python/plan.md`
- Capital Companion Docs: https://capitalcompanion.ai/docs/mastering-technical-analysis/

---

## Validation Summary

**Validated:** 2025-12-30
**Questions Asked:** 8
**Status:** Approved with adjustments

### Confirmed Decisions

1. **Data Source: Hybrid MT5 + TwelveData (Volume Validation)** ✓ **(ADJUSTED)**
   - **MT5 Terminal:** Primary OHLCV data (tick-level price accuracy for short-term trading)
   - **TwelveData API:** Volume comparison/confirmation (market-wide volume validation)
   - **Rationale:** MT5 broker volume ≠ total market volume. Need external source to:
     - Detect volume divergence (broker vs market)
     - Confirm breakouts with real market volume
     - Identify fake volume pumps
   - **Action:** Phase 1 implements MT5 primary + TwelveData volume validator
   - **Cost:** TwelveData Pro $79/mo (already in Capital Companion budget)

2. **Cache TTL: 1 Minute** ✓ **(ADJUSTED)**
   - Reduced from 5min → 1min for fresher real-time data
   - Still cacheable for performance but better for active traders
   - **Action:** Update Phase 1 redis_client.py default TTL to 60s

3. **LLM Strategy: Hybrid DeepSeek/ChatGPT (Configurable)** ✓ **(ADJUSTED)**
   - DeepSeek for technical summaries (cost: ~$5/mo)
   - ChatGPT (GPT-4) for complex recommendations (quality reasoning)
   - **Action:** Add configurable model selection in ai_summarizer.py
   - **Action:** Add user preference field: `preferred_llm` (deepseek, chatgpt, auto)
   - Estimated cost: $15-20/mo (hybrid strategy)

4. **Pattern Detection: Rule-Based, Defer ML** ✓
   - Ship rule-based patterns in Phase 2
   - Evaluate accuracy in production
   - Add ML/CNN detection in Phase 5+ if needed

5. **Risk Enforcement: Hard Limits** ✓ **(ADJUSTED)**
   - Enforce position size and risk limits (not advisory only)
   - Safer for users, reduces over-exposure
   - **Action:** Add limit enforcement logic in risk_analyzer.py
   - **Action:** Add UI indicators when limits prevent trades

6. **Vietnamese QA: Ship and Iterate** ✓
   - Launch with LLM-generated Vietnamese
   - Fix issues based on user feedback
   - Faster to market, real-world validation

7. **Execution: Sequential Phases** ✓
   - Phase 1 → 2 → 3 → 4 in order
   - Safer dependencies, clear milestones
   - 8 + 8 + 6 + 10 = 32 hours total

8. **Accuracy Measurement: Production Tracking** ✓
   - Track user outcomes when acting on patterns
   - Real-world validation vs backtest
   - **Action:** Add outcome tracking in recommendations table

### Implementation Adjustments Required

1. **Phase 1 Changes:**
   ```python
   # redis_client.py - Update default TTL
   # OLD: await redis.setex(key, 300, data)  # 5min
   # NEW: await redis.setex(key, 60, data)   # 1min
   ```

2. **Phase 3 Changes:**
   ```python
   # risk_analyzer.py - Add enforcement
   def calculate_position_size(..., enforce_limits=True):
       size = _calculate_size(...)
       if enforce_limits:
           size = min(size, user.max_position_size)
           if size > user.max_position_size:
               raise RiskLimitExceeded("Position exceeds max risk")
       return size
   ```

3. **Phase 4 Changes:**
   ```python
   # ai_summarizer.py - Configurable hybrid LLM routing
   def generate_summary(analysis_type, user_preference, ...):
       # Check user preference first
       if user_preference == "deepseek":
           return _call_deepseek(...)
       elif user_preference == "chatgpt":
           return _call_chatgpt(...)  # GPT-4
       # Auto mode (default)
       elif analysis_type == "technical_summary":
           return _call_deepseek(...)  # Cost-effective
       elif analysis_type == "recommendation":
           return _call_chatgpt(...)   # Quality reasoning (GPT-4)
   ```

4. **Database Changes:**
   ```sql
   -- Add outcome tracking for pattern accuracy
   ALTER TABLE recommendations
   ADD COLUMN actual_pnl NUMERIC(20,8),
   ADD COLUMN outcome_updated_at TIMESTAMPTZ;

   -- Add LLM preference to user profiles
   ALTER TABLE user_profiles
   ADD COLUMN preferred_llm TEXT DEFAULT 'auto'
   CHECK (preferred_llm IN ('auto', 'deepseek', 'chatgpt'));
   ```

### Confirmed Risks

- **MT5 Broker Volume Limitation:** Mitigated with TwelveData volume comparison
- **Volume Divergence Detection:** Critical for avoiding fake breakouts
- **Short-term Price Accuracy:** MT5 broker data provides tick-level precision
- **Vietnamese Quality:** Ship and iterate - real user feedback
- **Pattern Accuracy:** Production tracking vs backtest
- **LLM Costs:** Hybrid DeepSeek/ChatGPT reduces costs ~70% ($15-20/mo vs $50/mo)
- **TwelveData Cost:** $79/mo already budgeted in Capital Companion plan

### Action Items

- [x] Validation complete
- [ ] Update Phase 1: Change cache TTL from 300s → 60s
- [ ] Update Phase 1: Add TwelveData volume comparison integration
- [ ] Update Phase 1: Implement volume divergence detection
- [ ] Update Phase 3: Add hard limit enforcement logic
- [ ] Update Phase 4: Implement configurable hybrid LLM routing (DeepSeek/ChatGPT)
- [ ] Update Phase 4: Add user LLM preference setting
- [ ] Update database schema: Add outcome tracking + LLM preference fields
- [ ] Document risk limit UI indicators in frontend plan
- [ ] Document volume divergence alerts in Phase 2 pattern detection

---

**Plan Status:** Validated and ready for Phase 1 implementation
