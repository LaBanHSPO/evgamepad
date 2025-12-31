# EV GamePad - Project Overview & Product Development Requirements (PDR)

**Date:** 2025-12-31
**Status:** Phase 5.2 (Accuracy Tracking System)
**Version:** 1.0.1

---

## Executive Summary

**EV GamePad** is an intelligent AI trading advisor platform providing real-time technical analysis, pattern recognition, risk assessment, AI-powered portfolio management advice, and accuracy tracking. The system combines MetaTrader5 market data, advanced technical indicators, Claude/DeepSeek LLM integration, and PostgreSQL-backed performance analytics to help traders make better trading decisions with capital preservation as the primary goal.

**Phase 5.2 (Current):** Accuracy Tracking System - enabling automated trade outcome recording (manual + MT5 auto-detection), performance metrics generation (win rate, profit factor, Sharpe ratio), and identification of best-performing trading configurations.

---

## Project Vision

Create the most intelligent, user-friendly trading advisor that:
1. Analyzes market conditions in real-time
2. Identifies trading opportunities with confidence scoring
3. Manages portfolio risk with capital preservation focus
4. Provides natural language advisory in user's preferred language
5. Caches recommendations to reduce costs while maintaining freshness

---

## Phase Overview

### Phase 01: Technical Analysis Engine (Completed)
- Single-symbol, single-timeframe technical indicator calculation
- RSI, MACD, Bollinger Bands, ATR, ADX, Stochastic, OBV
- Moving averages (SMA, EMA)
- Signal generation from indicators
- Redis caching (60s TTL)

### Phase 02: Pattern Recognition & S/R (Completed)
- Candlestick pattern detection (Hammer, Engulfing, etc.)
- Chart pattern detection (Head & Shoulders, Double Tops, etc.)
- Support/Resistance level calculation (Pivot, Fibonacci, Swing)
- Pattern-based signal generation
- Pattern result caching (300s TTL)

### Phase 03: Risk Analysis (Completed)
- Position sizing calculation
- Risk/reward ratio assessment
- Account-based position sizing (Kelly Criterion-inspired)
- ATR-based stop-loss/take-profit targets
- Temporal risk evaluation

### Phase 04: Portfolio Analysis & AI Risk Advisory (Completed)
- Multi-position analysis in parallel
- Portfolio health scoring (0-100)
- Per-position risk status assessment
- LLM-powered capital preservation advice (Claude/DeepSeek)
- Semantic caching for AI responses
- Multi-language support (Vietnamese/English)

### Phase 5.1: Chain-of-Thought Reasoning & Explainability (Completed)
- Data provenance tracking for all signals
- Chain-of-thought reasoning engine (5-step breakdown)
- Point-based scoring system (0-12 points)
- Explainability models (Pydantic schemas)
- Socket.IO event: `advisor:explain_recommendation`
- Feature flag: `ENABLE_EXPLAINABILITY`
- Redis caching for CoT results (300s TTL)

### Phase 5.2: Accuracy Tracking System (Current)
- Manual and automatic trade outcome recording
- MT5 auto-detection of closed positions (5-minute sync)
- Performance metrics: win rate, profit factor, Sharpe ratio, avg P/L
- Best-performing configuration identification
- PostgreSQL integration with materialized views
- Socket.IO events: `advisor:record_outcome`, `advisor:accuracy_report`
- Per-user accuracy tracking support
- Exit reason classification (take_profit, stop_loss, manual, timeout)

### Future Phases

#### Phase 05: Advanced ML Integration
- Custom neural network for entry signal prediction
- ML pattern classification (replaces rule-based)
- Backtesting framework

#### Phase 06: Mobile App
- React Native iOS/Android app
- Push notifications for portfolio alerts
- Offline mode with syncing

#### Phase 07: Webhook Alerts & Automation
- Alert system for risk thresholds
- Position auto-closing on danger status
- Webhook integration with MT5

---

## Current Feature Set (Phase 5.2)

### Accuracy Tracking (Phase 5.2)
- **Manual Outcome Recording:** Record trade results via `advisor:record_outcome` event
- **MT5 Auto-Detection:** Automatic sync of closed positions every 5 minutes
- **Matching Algorithm:** 3-factor scoring (symbol, price tolerance ±0.1%, time window ±5min)
- **Exit Reason Detection:** Classify exits as take_profit, stop_loss, manual, or unknown
- **Performance Metrics:**
  - Win rate (% of winning trades)
  - Profit factor (wins/losses ratio)
  - Sharpe ratio (return-to-volatility)
  - Average P/L % (per-trade and by outcome)
  - Best/worst trades
  - Average hold time
- **Configuration Analysis:** Find top-performing symbol/timeframe/signal combinations
- **Per-User Tracking:** Filter metrics by user ID
- **Time-Based Filtering:** Query any date range (default: 30 days)

### Technical Analysis
- **Supported Timeframes:** M1, M5, M15, M30, H1, H4, D1, W1, MN1
- **Indicators:** SMA (20/50/200), EMA (9/21/50), RSI, MACD, Bollinger Bands, ATR, ADX, Stochastic, OBV
- **Signal Types:** Bullish, Bearish, Neutral
- **Confidence:** 0-1 scale based on signal agreement

### Pattern Recognition
- **Candlestick Patterns:** 15+ patterns with bias and strength
- **Chart Patterns:** Head & Shoulders, Double Top/Bottom, Triangles
- **S/R Levels:** Pivot points, Fibonacci, Swing-based
- **Pattern Caching:** 5-minute TTL

### Risk Analysis
- **Position Sizing:** Fixed risk, Kelly Criterion, Account percentage methods
- **Risk Metrics:** Risk/reward ratio, distance to stop-loss, drawdown
- **Risk Profiles:** Conservative, Moderate, Aggressive
- **R-Multiple Calculation:** Current reward vs. defined risk

### Portfolio Management (Phase 04)
- **Portfolio Health Score:** 0-100 with HEALTHY/CAUTION/DANGER status
- **Per-Position Analysis:** P&L, R-Multiple, risk status, recommendation
- **Risk Exposure Tracking:** Total portfolio risk as % of account
- **AI Advisory:** Capital preservation focused recommendations
- **Language Support:** Vietnamese, English
- **Cache Strategy:** Deterministic hashing for 5-minute caching

### AI Integration
- **Primary Model:** Claude 3.5 Sonnet (Anthropic)
- **Fallback Model:** DeepSeek (OpenAI-compatible)
- **Features:** Technical summary, portfolio advice, recommendations
- **Caching:** Semantic caching with MD5-based keys
- **Temperature:** 0.3 (low variance, consistent recommendations)

---

## Architecture Overview

```
User Interface (React/TypeScript)
    ↓
Socket.IO WebSocket Connection
    ↓
Backend Server (FastAPI/Starlette)
    ├─ Event Handler Layer (Input validation)
    │  ├─ advisor:record_outcome → AccuracyTracker
    │  └─ advisor:accuracy_report → AccuracyTracker
    ├─ Processor Layer (Business logic)
    ├─ Advisor Components Layer (Analysis)
    │  ├─ Data Fetcher (MT5 integration)
    │  ├─ Technical Analyzer (Indicator calculation)
    │  ├─ Pattern Detector (Pattern recognition)
    │  ├─ Support/Resistance (S/R calculation)
    │  ├─ Risk Analyzer (Risk metrics)
    │  ├─ AI Summarizer (LLM integration)
    │  ├─ Recommendation Engine (Signal aggregation)
    │  ├─ AccuracyTracker (Phase 5.2 - Performance metrics)
    │  └─ MT5HistoryParser (Phase 5.2 - Auto-detection)
    ├─ Cache Layer (Redis)
    ├─ Database Layer (PostgreSQL - Phase 5.2)
    │  ├─ recommendation_outcomes table
    │  └─ recommendation_accuracy materialized view
    └─ Market Data (MT5 Terminal)
```

---

## Data Models

### Request/Response: Accuracy Tracking (Phase 5.2)

**Record Outcome Request:**
```typescript
interface RecordOutcomeRequest {
  symbol: string;              // "XAUUSD"
  timeframe: string;           // "H1"
  signal: "BUY" | "SELL" | "HOLD";
  confidence: number;          // 0-100
  entry_price: number;         // 2634.50
  exit_price: number;          // 2640.20
  stop_loss?: number;          // 2625.50
  take_profit?: number;        // 2645.00
  exit_reason: "take_profit" | "stop_loss" | "manual" | "timeout";
  entry_at?: string;           // ISO 8601 timestamp
  exit_at?: string;            // ISO 8601 timestamp
  recommendation_id?: string;  // UUID link to original recommendation
}
```

**Accuracy Report Request:**
```typescript
interface AccuracyReportRequest {
  symbol?: string;             // Filter by symbol
  timeframe?: string;          // Filter by timeframe
  signal?: "BUY" | "SELL" | "HOLD";  // Filter by signal
  days?: number;               // Analysis period (default: 30)
  user_id?: string;            // Filter by user
}
```

**Accuracy Metrics Response:**
```typescript
interface AccuracyMetrics {
  period_days: number;
  symbol: string | null;
  timeframe: string | null;
  signal: string | null;
  total_trades: number;
  wins: number;
  losses: number;
  break_evens: number;
  win_rate_pct: number;        // 0-100%
  avg_pnl_pct: number;         // Average P/L %
  avg_win_pct: number;         // Avg winning trade %
  avg_loss_pct: number;        // Avg losing trade %
  profit_factor: number;       // Wins/losses ratio
  sharpe_ratio: number | null; // Return-to-volatility
  best_trade_pct: number;      // Best trade %
  worst_trade_pct: number;     // Worst trade %
  avg_hold_hours: number;      // Average hold duration
  recommendation: string;      // "Excellent" / "Good" / "Acceptable" / "Avoid"
}
```

**Best Performing Configurations:**
```typescript
interface BestPerformingConfig {
  symbol: string;
  timeframe: string;
  signal: "BUY" | "SELL" | "HOLD";
  total_trades: number;
  win_rate_pct: number;
  avg_pnl_pct: number;
  profit_factor: number;
}
```

### Request: Portfolio Analysis

```typescript
interface PositionInput {
  symbol: string;              // "XAUUSD"
  entry_price: number;         // 2100.50
  current_price?: number;      // 2095.00 (auto-fetched if missing)
  position_size: number;       // 0.5
  stop_loss?: number;          // 2090.00 (default 2% below entry)
  timeframe?: string;          // "H1"
}

interface PortfolioAnalysisRequest {
  positions: PositionInput[];
  account_balance: number;
  risk_profile?: "conservative" | "moderate" | "aggressive";
  language?: "vi" | "en";
}
```

### Response: Portfolio Analysis

```typescript
interface PortfolioHealth {
  score: number;                          // 0-100
  status: "HEALTHY" | "CAUTION" | "DANGER";
  total_risk_exposure: number;            // % of account
  current_drawdown: number;               // % max loss
  positions_at_risk: number;              // count
}

interface PositionAnalysis {
  symbol: string;
  pnl_pct: number;
  pnl_amount: number;
  r_multiple: number;
  risk_status: "safe" | "caution" | "approaching_stop" | "danger";
  recommendation: "HOLD" | "REDUCE" | "CLOSE";
  technical_signal: "bullish" | "bearish" | "neutral";
  distance_to_stop_pct: number;
}

interface AIAdvice {
  summary: string;
  overall_risk: "LOW" | "MODERATE" | "HIGH";
  priority_actions: string[];
  reasoning: string;
  confidence: number;
  model: "claude" | "deepseek";
  cached: boolean;
}

interface PortfolioAnalysisResponse {
  portfolio_health: PortfolioHealth;
  position_analysis: PositionAnalysis[];
  ai_advice: AIAdvice;
  cached: boolean;
  computed_at: string;  // ISO 8601
}
```

---

## Requirements & Acceptance Criteria

### Functional Requirements

**FR-0: Accuracy Tracking (Phase 5.2)**
- Record manual trade outcomes with entry/exit prices, P/L, exit reason
- Auto-detect closed positions from MT5 history (5-minute background sync)
- Match MT5 deals to advisor recommendations (80%+ confidence threshold)
- Calculate accuracy metrics: win rate, profit factor, Sharpe ratio
- Query metrics by symbol, timeframe, signal, date range, user_id
- Identify best-performing configurations (min 10 trades, ordered by win_rate + profit_factor)
- **Acceptance:** <2s query latency, 100% match accuracy for matched deals, <5% false positives

**FR-1: Real-Time Technical Analysis**
- Calculate technical indicators from MT5 OHLCV data
- Support 9 indicators (SMA, EMA, RSI, MACD, BB, ATR, ADX, Stochastic, OBV)
- Generate bullish/bearish/neutral signals
- **Acceptance:** Indicators match TradingView calculations within 0.1%

**FR-2: Pattern Recognition**
- Detect 15+ candlestick patterns
- Detect chart patterns (H&S, Double Top, Triangles)
- Calculate S/R levels from 3 methods
- **Acceptance:** Patterns detected within 5 candles of human identification

**FR-3: Portfolio Analysis**
- Analyze 1-10 positions in parallel
- Calculate portfolio health score (0-100)
- Generate per-position risk assessment
- **Acceptance:** Analysis completes in <5 seconds

**FR-4: AI Risk Advisory**
- Generate natural language advice using Claude/DeepSeek
- Capital preservation focus
- Multi-language support (VI, EN)
- **Acceptance:** Advice includes 3+ actionable items

**FR-5: Caching System**
- Cache technical indicators (60s)
- Cache patterns (300s)
- Cache AI responses (300s)
- **Acceptance:** Cache hit rate >60% in normal usage

**FR-6: WebSocket API**
- Real-time Socket.IO communication
- Request/response validation
- Error responses with error codes
- **Acceptance:** All endpoints documented in API spec

### Non-Functional Requirements

**NFR-1: Performance**
- Portfolio analysis (cache miss): <5 seconds
- Portfolio analysis (cache hit): <200ms
- Technical analysis (cache miss): <2 seconds
- Technical analysis (cache hit): <100ms
- **Acceptance:** 95th percentile latency within targets

**NFR-2: Scalability**
- Support 100 concurrent WebSocket connections
- Handle 1000 analyses/hour
- Redis memory usage <500MB
- **Acceptance:** Load test with 100 concurrent users

**NFR-3: Reliability**
- 99.5% uptime (MT5 connection available)
- Graceful degradation (fallback LLM if Claude down)
- Error recovery without data loss
- **Acceptance:** All error codes documented, fallback tested

**NFR-4: Security**
- Input validation on all endpoints
- Prompt injection prevention (text sanitization)
- No sensitive data in logs
- **Acceptance:** OWASP Top 10 checklist passed

**NFR-5: Observability**
- Structured JSON logging
- Session-based request tracking
- Performance metrics (latency, cache hit rate)
- **Acceptance:** Debug logs show request lifecycle

**NFR-6: Cost Efficiency**
- Semantic caching reduces LLM calls 70%+
- Price bucketing improves cache hit rate
- Batch indicator requests
- **Acceptance:** Cost per analysis <$0.01 with caching

---

## Technical Stack

### Backend
- **Framework:** FastAPI + Starlette (async Python)
- **WebSocket:** python-socketio
- **Data Validation:** Pydantic
- **Data Processing:** Pandas, pandas-ta
- **LLM Integration:** Anthropic SDK, OpenAI SDK (DeepSeek)
- **Caching:** Redis async client
- **Database:** PostgreSQL (asyncpg) - Phase 5.2
- **Market Data:** MetaTrader5 Python API
- **Logging:** python-json-logger
- **Testing:** pytest, pytest-asyncio

### Frontend
- **Framework:** React 18 + TypeScript
- **WebSocket:** socket.io-client
- **UI Components:** Tailwind CSS, Lucide React
- **State Management:** React Hooks (useState, useCallback)
- **Build:** Vite (fast development builds)

### Infrastructure
- **Backend:** Linux/WSL (Python 3.9+)
- **Market Data:** MetaTrader5 Terminal (Windows/WSL)
- **Cache:** Redis (localhost:6379)
- **Database:** PostgreSQL 14+ (localhost:5432) - Phase 5.2
- **API Keys:** Environment variables (.env)

---

## Development Roadmap

### Q1 2025 (Current)
- [x] Phase 04: Portfolio Analysis
- [x] AI Risk Advisory (Claude/DeepSeek)
- [ ] Semantic caching optimization
- [ ] Mobile app wireframes

### Q2 2025
- [ ] Phase 05: ML-based entry signals
- [ ] Backtesting framework
- [ ] Advanced risk metrics (VaR, Sharpe Ratio)
- [ ] Multi-account support

### Q3 2025
- [ ] Phase 06: Mobile app (React Native)
- [ ] Push notifications
- [ ] Offline sync

### Q4 2025
- [ ] Phase 07: Webhook integration
- [ ] Auto-close on danger status
- [ ] Alert subscriptions
- [ ] Production deployment

---

## Success Metrics

### User-Facing
- Portfolio health score widely adopted (>80% of analyses)
- AI advice confidence >75% average
- Cache hit rate >60%
- API response time <2 seconds (95th percentile)

### Business
- Cost per analysis <$0.01 (with caching)
- Monthly active users growing >20%
- Advisor accuracy improving with feedback loop

### Technical
- Test coverage >80%
- Zero data loss incidents
- Availability >99.5%
- Documentation completeness 100%

---

## Risk Assessment

### Technical Risks

**Risk:** LLM API Downtime
- **Impact:** High (advisories unavailable)
- **Mitigation:** Fallback to DeepSeek; cached responses; graceful degradation
- **Status:** Implemented

**Risk:** MT5 Terminal Disconnection
- **Impact:** Medium (technical analysis unavailable)
- **Mitigation:** Circuit breaker; reconnection manager; cached data use
- **Status:** Implemented

**Risk:** Cache Invalidation Issues
- **Impact:** Medium (stale advice)
- **Mitigation:** Deterministic caching; TTL-based expiry; cache hit logging
- **Status:** Implemented

### Operational Risks

**Risk:** Inaccurate Portfolio Health Scoring
- **Impact:** High (user makes wrong decisions)
- **Mitigation:** Thorough testing; formula documentation; confidence metadata
- **Status:** Mitigated

**Risk:** Prompt Injection in AI Advice
- **Impact:** Medium (erroneous advice)
- **Mitigation:** Text sanitization; prompt templates; rate limiting
- **Status:** Implemented

---

## Constraints

### Technical Constraints
- Python 3.9+ required (type hints)
- MetaTrader5 requires Windows/WSL (not macOS)
- Redis instance required (development: localhost:6379)
- API keys required for Claude/DeepSeek

### Business Constraints
- Single-account support (Phase 05 for multi-account)
- English/Vietnamese only (Phase 05+ for other languages)
- No mobile app yet (planned Phase 06)
- Manual position entry (no API integration yet)

### Regulatory Constraints
- No investment advice (advisory only)
- User agrees they make own decisions
- Disclaimer required in UI
- No guarantees on accuracy

---

## Dependencies & Integration Points

### External APIs
- **Anthropic Claude API** (primary LLM)
- **DeepSeek API** (fallback LLM)
- **MetaTrader5 Terminal** (market data)
- **Redis** (caching)

### Internal Modules
- `app/advisor/*` - Technical analysis & AI
- `app/events/*` - WebSocket event handlers
- `app/processors/*` - Business logic
- `app/database/*` - Caching

### Data Dependencies
- OHLCV data from MT5 (required)
- User positions (required)
- Account balance (required)
- API keys in environment (required)

---

## Testing Strategy

### Unit Tests
- Technical indicator calculations (pandas-ta validation)
- Pydantic model validation
- Cache key generation
- Health score calculations

### Integration Tests
- Event handler → Processor → Component flow
- Redis cache read/write
- LLM API integration (mock + real)
- Error handling + fallback behavior

### End-to-End Tests
- Full portfolio analysis request/response
- Multi-position parallel processing
- LLM response parsing
- Cache hit/miss scenarios

### Performance Tests
- Portfolio analysis latency (target: <5s)
- Cache hit rate (target: >60%)
- Concurrent connection handling
- Memory usage under load

---

## Documentation Requirements

### For Developers
- API specification (endpoints, request/response)
- System architecture (components, data flow)
- Code standards (naming, style, patterns)
- Testing guide (how to run tests, add new tests)

### For Users
- User guide (how to use portfolio analysis)
- Risk profile explanation
- Cache behavior documentation
- Disclaimer & limitations

### For Operations
- Deployment guide
- Configuration reference
- Monitoring dashboard setup
- Troubleshooting guide

---

## Acceptance Criteria for Phase 5.2

- [x] AccuracyTracker class with record_outcome() method
- [x] MT5HistoryParser class with sync_closed_positions() method
- [x] PostgreSQL schema: recommendation_outcomes table (19 columns)
- [x] Materialized view: recommendation_accuracy
- [x] RecordOutcomeRequest Pydantic model
- [x] AccuracyReportRequest Pydantic model
- [x] AccuracyMetrics response model
- [x] BestPerformingConfig model
- [x] Pool manager for connection pooling
- [x] 3-factor matching algorithm (symbol, price, time)
- [x] Exit reason classification (take_profit, stop_loss, manual, unknown)
- [x] Win rate, profit factor, Sharpe ratio calculation
- [x] Socket.IO event handler (advisor:record_outcome)
- [x] Socket.IO event handler (advisor:accuracy_report)
- [x] Database migration script (005_recommendation_outcomes.sql)
- [x] Auto-refresh materialized view on outcome record
- [x] Background sync task (5-minute interval)
- [x] Per-user accuracy filtering
- [x] Time-based query filtering (default: 30 days)
- [x] Unit tests for accuracy tracker (22 tests)
- [x] Unit tests for MT5 history parser (13 tests)
- [x] Setup guide (ENV_VARIABLES_PHASE_5_2.md)
- [x] API documentation (Socket.IO events)
- [x] Codebase summary update
- [x] Project overview PDR update
- [x] System architecture update

---

## Acceptance Criteria for Phase 04 (Previous)

- [x] PortfolioAnalysisRequest Pydantic model
- [x] PortfolioAnalysisResponse complete with all fields
- [x] Portfolio health score calculation (0-100)
- [x] Per-position analysis (P&L, R-Multiple, risk status)
- [x] AI advice generation (Claude/DeepSeek fallback)
- [x] Semantic caching (deterministic MD5 keys)
- [x] Multi-language support (VI, EN)
- [x] Socket.IO event handler (advisor:portfolio_analysis)
- [x] Error handling with proper error codes
- [x] Frontend component integration (PositionInputForm, AIRiskAdvisoryPanel)
- [x] React hook (usePortfolioAnalysis)
- [x] API documentation (endpoint spec, examples)
- [x] System architecture documentation
- [x] Code standards documentation
- [x] Unit tests for portfolio analysis
- [x] Integration tests for full flow

---

## Next Steps (Post Phase 5.2)

1. **Performance Optimization:** Profile and optimize bottlenecks
2. **User Feedback:** Collect feedback on health score algorithm
3. **ML Integration:** Begin Phase 05 (ML-based entry signals)
4. **Mobile Wireframes:** Design mobile app interface
5. **Marketing Materials:** Create product demo/documentation

---

## Glossary

- **Portfolio Health Score:** 0-100 metric indicating portfolio safety
- **Risk Exposure:** Total portfolio risk as % of account balance (target: <2%)
- **R-Multiple:** Current reward/risk ratio for a position
- **Distance to Stop:** Percentage gap between current price and stop-loss
- **Semantic Caching:** LLM response caching based on input similarity
- **Risk Status:** Position safety classification (safe/caution/danger)
- **Capital Preservation:** Primary goal: protect account balance first
- **Drawdown:** Largest peak-to-trough loss in portfolio P&L

---

## Appendix: Configuration

### Environment Variables

```bash
# LLM Configuration
ANTHROPIC_API_KEY=sk-ant-...        # Claude API key
DEEPSEEK_API_KEY=sk-...             # DeepSeek API key
DEFAULT_LLM_MODEL=claude            # Primary model (claude/deepseek)

# Backend Configuration
DEBUG=false                         # Debug mode
LOG_LEVEL=INFO                      # Logging level
SOCKET_IO_PORT=8000                 # Server port

# Redis Configuration
REDIS_URL=redis://localhost:6379    # Redis connection

# MT5 Configuration
MT5_ACCOUNT=12345                   # Trading account number
MT5_PASSWORD=password               # Account password
MT5_SERVER=MetaQuotes-Demo          # Server name

# Cache Configuration
CACHE_TTL_INDICATORS=60             # Indicator cache (seconds)
CACHE_TTL_PATTERNS=300              # Pattern cache (seconds)
CACHE_TTL_PORTFOLIO=300             # Portfolio cache (seconds)
```

---

**Document Status:** Complete for Phase 04
**Last Updated:** 2025-12-30
**Next Review:** 2025-03-30 (Post Phase 05 kickoff)
