# EV GamePad - Codebase Summary

**Generated:** 2025-12-30
**Version:** Phase 04 (Portfolio Analysis & AI Risk Advisory)
**Total Files:** 160
**Total Tokens:** ~298K

---

## Project Overview

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

**Portfolio Analysis (NEW):**
- `app/processors/advisor_processor.py` - `process_portfolio_analysis()` method
  - Per-position technical + risk analysis
  - Portfolio health scoring (0-100)
  - LLM-powered capital preservation advice

### 4. API & Events (WebSocket)

**Event Layer:**
- `app/events/advisor_events.py` - Socket.IO event handlers
  - `advisor:technical_summary` - Single timeframe analysis
  - `advisor:multi_timeframe` - Multiple timeframe analysis
  - `advisor:pattern_scan` - Pattern detection
  - `advisor:risk_analysis` - Risk metrics
  - `advisor:recommendation` - AI-powered recommendation
  - `advisor:portfolio_analysis` - **NEW** Portfolio analysis + AI advisory

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

**Integration:**
- `src/pages/Portfolio.tsx` - Main portfolio analysis page
  - Combines form + results display
  - Manages loading/error states
  - Sends `advisor:portfolio_analysis` event to backend

### State Management

- **React Hooks:** `useState`, `useCallback` for local state
- **Socket.IO Integration:** Direct event emission/listening
- **Type Safety:** Full TypeScript interfaces for requests/responses

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
│   │   └── redis_client.py          # Redis caching + portfolio methods
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
│   ├── PositionInputForm.tsx        # Position input + account balance form (NEW)
│   └── AIRiskAdvisoryPanel.tsx      # Portfolio health + AI advisory display (NEW)
├── hooks/
│   └── usePortfolioAnalysis.ts      # Socket.IO integration + state management (NEW)
├── pages/
│   └── Portfolio.tsx                # Portfolio analysis page (updated)
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
- `lucide-react` - Icons
- `tailwindcss` - Styling

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
- **Architecture:** `./system-architecture-advisor.md`
- **Code Standards:** `./code-standards.md`
- **Implementation Guide:** `./advisor-implementation-guide.md`

---

**Last Updated:** 2025-12-30
**Maintainer:** Backend Team
**Status:** Phase 04 (Portfolio Analysis Complete)
