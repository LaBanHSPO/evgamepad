# System Architecture - AI Trading Advisor Module

## Module Context

The AI Trading Advisor is an integrated module within EV GamePad backend providing real-time technical analysis and AI-powered recommendations. Phase 01-03 provide technical analysis, pattern recognition, and risk assessment. Phase 04 adds Claude/DeepSeek LLM integration for AI-generated summaries and personalized recommendations with semantic caching.

---

## High-Level Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         EV GamePad Backend                                 │
│                                                                             │
│  ┌──────────────────┐               ┌─────────────────────────────────┐   │
│  │   Socket.IO      │               │ LLM Services (Phase 04)         │   │
│  │   Server         │               │ - Claude 3.7 Sonnet (primary)   │   │
│  │  (Port 8000)     │               │ - DeepSeek (fallback)           │   │
│  └────────┬─────────┘               └─────────────────────────────────┘   │
│           │                                   ↑                           │
│           │ WebSocket Events                  │ API Calls                 │
│           ↓                                   │                           │
│  ┌──────────────────────────────────────────────────────┐                 │
│  │  Advisor Events Layer                                │                 │
│  │  (app/events/advisor_events.py)                      │                 │
│  │  - technical_summary, multi_timeframe, pattern_scan  │                 │
│  │  - recommendation ⬅ Phase 04 NEW                     │                 │
│  │  - risk_analysis                                     │                 │
│  └────────┬─────────────────────────────────────────────┘                 │
│           │                                                              │
│           ↓                                                              │
│  ┌──────────────────────────────────────────────────────┐                 │
│  │  Advisor Processor (app/processors/advisor_processor) │                 │
│  │  - process_technical_summary, process_multi_timeframe │                 │
│  │  - process_pattern_scan, process_risk_analysis        │                 │
│  │  - process_recommendation ⬅ Phase 04 NEW             │                 │
│  └─┬────────────────────────────────────────────────────┘                 │
│   │                                                                        │
│   ├─ Technical Analysis Chain (Phase 1-3)                                 │
│   │  ├─ Data Fetcher → Technical Analyzer                                │
│   │  ├─ Pattern Detector → Support/Resistance                             │
│   │  └─ Risk Analyzer                                                     │
│   │                                                                        │
│   └─ AI Recommendations Chain (Phase 04) ⬅ NEW                           │
│      ├─ AI Summarizer (app/advisor/ai_summarizer.py)                    │
│      │  ├─ Claude API integration                                         │
│      │  ├─ DeepSeek fallback                                              │
│      │  └─ Semantic caching via Redis                                     │
│      └─ Recommendation Engine (app/advisor/recommendation_engine.py)     │
│         ├─ Aggregate technical signals                                    │
│         ├─ Aggregate pattern signals                                      │
│         ├─ Calculate overall signal + targets                             │
│         └─ Format final recommendation                                    │
│                                                                            │
│  ┌────────────────────────────────────────────────────────┐              │
│  │  Redis Cache (app/database/redis_client.py)            │              │
│  │  - Indicators cache (60s TTL)                          │              │
│  │  - Pattern cache (300s TTL)                            │              │
│  │  - AI Summary cache (300s TTL) ⬅ Phase 04 NEW         │              │
│  └─────────────────────────────────────────────────────────┘              │
│                      ↓ ↑                                                   │
│  ┌─────────────────────────────────────────────────────────┐              │
│  │  MT5 Terminal (Market Data)  │  Redis Server            │              │
│  │  (Windows/WSL)               │  (localhost:6379)        │              │
│  └─────────────────────────────────────────────────────────┘              │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Descriptions

### 1. Socket.IO Events (`advisor_events.py`)

**Responsibilities:**
- WebSocket event listening
- Input validation and sanitization
- Error response formatting
- Response routing back to client

**Key Functions:**
- `advisor_technical_summary(sid, data)` - Single timeframe analysis
- `advisor_multi_timeframe(sid, data)` - Multiple timeframe analysis
- `advisor_pattern_scan(sid, data)` - Pattern detection (Phase 02)

**Validation:**
```python
def validate_symbol(symbol: str) -> bool:
    return bool(re.match(r'^[A-Z0-9]{1,20}$', symbol))
```

**Error Handling:**
- Catches all exceptions
- Emits `advisor:error` event with ErrorCode
- Logs exception details

---

### 2. Advisor Processor (`advisor_processor.py`)

**Responsibilities:**
- Central orchestration point
- Cache hit/miss decision logic
- Component coordination
- Data transformation

**Core Methods:**

#### `process_technical_summary()`
```
1. Check Redis cache
2. If hit: add cached=true, return
3. If miss: fetch OHLCV
4. Run technical analyzer
5. Cache result (60s TTL)
6. Return with cached=false
```

#### `process_multi_timeframe()`
```
1. For each timeframe:
   - Call process_technical_summary()
   - Extract overall signal
2. Calculate alignment:
   - Count bullish/bearish/neutral
   - Determine status (strong/bias/mixed)
   - Set power_zone flag
3. Return combined results
```

#### `process_pattern_scan()` (Phase 02)
```
1. Check patterns cache (5min TTL)
2. Fetch 200 candles (more data for patterns)
3. Run pattern detector
4. Calculate S/R levels
5. Cache result
6. Return with cached flag
```

**Dependency Injection:**
```python
def __init__(self, mt5_manager, redis_client=None):
    self.data_fetcher = DataFetcher(mt5_manager)
    self.analyzer = TechnicalAnalyzer()
    self.pattern_detector = PatternDetector()  # Phase 02
    self.sr_calculator = SupportResistanceCalculator()  # Phase 02
    self.redis_client = redis_client
```

---

### 3. Data Fetcher (`data_fetcher.py`)

**Responsibilities:**
- MT5 terminal communication
- OHLCV data extraction
- Pandas DataFrame construction
- Multi-timeframe concurrent requests

**Architecture Decisions:**
- Async wrapper around MT5 (blocking)
- Uses `asyncio.to_thread()` to avoid blocking event loop
- Concurrent requests via `asyncio.gather()`

**Timeframe Mapping:**
```python
MT5_TIMEFRAMES = {
    "M1": 1, "M5": 5, "M15": 15, "M30": 30,
    "H1": 60, "H4": 240, "D1": 1440,
    "W1": 10080, "MN1": 43200
}
```

**Thread Pool Pattern:**
```python
def _fetch():
    rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)
    return rates

rates = await asyncio.to_thread(_fetch)
```

**Error Handling:**
```python
try:
    import MetaTrader5 as mt5
except ImportError:
    logger.error("MetaTrader5 not available on this platform")
    return None  # Graceful degradation
```

---

### 4. Technical Analyzer (`technical_analyzer.py`)

**Responsibilities:**
- Indicator calculation via pandas-ta
- Signal generation from indicator values
- Overall signal aggregation

**Indicator Categories:**

| Category | Indicators | Method |
|----------|-----------|--------|
| Trend | SMA, EMA | Moving average crossovers |
| Momentum | RSI, MACD, Stochastic | Extreme values, crossovers |
| Volatility | Bollinger Bands, ATR | Price bands, range |
| Trend Strength | ADX | +DI/-DI comparison |
| Volume | OBV | Cumulative volume |

**Signal Generation Logic:**

```
RSI Signals:
- < 30: oversold (bullish)
- > 70: overbought (bearish)
- 30-70: neutral

MACD Signals:
- MACD > Signal: bullish
- MACD < Signal: bearish
- Crossover detection: bullish/bearish_crossover

Bollinger Signals:
- Price >= Upper: upper_band (bearish)
- Price <= Lower: lower_band (bullish)
- In between: inside (neutral)

ADX Signals:
- < 20: no_trend
- 20-40: moderate_trend
- >= 40: strong_trend

Trend Signal:
- Price > EMA21 > EMA50: bullish
- Price < EMA21 < EMA50: bearish
- Else: mixed
```

**Overall Signal Aggregation:**
```python
confidence = max(bullish_count, bearish_count) / total_signals

if bullish_count > bearish_count:
    signal = "bullish"
elif bearish_count > bullish_count:
    signal = "bearish"
else:
    signal = "neutral"
```

**Numerical Precision:**
```python
# Prices: 5 decimals
round(value, 5)

# RSI/Stochastic: 2 decimals (0-100 scale)
round(value, 2)

# Confidence: 2 decimals (0-1 scale)
round(confidence, 2)
```

---

### 5. Redis Cache (`redis_client.py`)

**Responsibilities:**
- Async Redis operations
- Connection pooling
- Data serialization/deserialization
- Health checking

**Key Design:**
- Uses `redis.asyncio` for async I/O
- JSON serialization for complex objects
- TTL-based expiration

**Cache Keys:**
- Indicators: `indicators:{symbol}:{timeframe}`
- Patterns: `patterns:{symbol}:{timeframe}` (Phase 02)

**Methods:**

```python
async def get_indicators(symbol, timeframe) -> Optional[Dict]:
    key = f"indicators:{symbol}:{timeframe}"
    data = await self._client.get(key)
    return json.loads(data) if data else None

async def set_indicators(symbol, timeframe, data, ttl=60) -> bool:
    key = f"indicators:{symbol}:{timeframe}"
    await self._client.setex(key, ttl, json.dumps(data))
    return True

async def is_connected() -> bool:
    return await self._client.ping()
```

**Connection Lifecycle:**
```python
async def connect():
    self._client = redis.Redis(...)
    await self._client.ping()  # Verify

async def disconnect():
    await self._client.close()
```

**Graceful Degradation:**
```python
if not self._client:
    return None  # Cache miss treated same as request without cache
```

---

## Data Flow Sequences

### Sequence: Technical Summary (Cache Miss)

```
Client: emit advisor:technical_summary
  ↓
EventHandler: validate_symbol() → validate timeframe
  ↓
AdvisorProcessor: process_technical_summary()
  ├─ redis_client.get_indicators() → None
  ├─ data_fetcher.fetch_ohlcv(XAUUSD, H1, 100)
  │   └─ MT5: copy_rates_from_pos() [blocking, in thread pool]
  ├─ analyzer.calculate_indicators(df)
  │   └─ For each indicator category:
  │       ├─ ta.sma/ema/rsi/etc()
  │       └─ Generate signals
  ├─ analyzer.get_overall_signal()
  ├─ redis_client.set_indicators() [60s TTL]
  └─ Return response {cached: false, ...}
  ↓
EventHandler: emit advisor:technical_result
  ↓
Client: receive response
```

**Total Time:** 500-2000ms (MT5 dominant)

---

### Sequence: Technical Summary (Cache Hit)

```
Client: emit advisor:technical_summary
  ↓
EventHandler: validate_symbol()
  ↓
AdvisorProcessor: process_technical_summary()
  └─ redis_client.get_indicators(XAUUSD, H1) → {indicators, signals, ...}
  ├─ Add cached=true, computed_at (original timestamp)
  └─ Return response
  ↓
EventHandler: emit advisor:technical_result
  ↓
Client: receive response
```

**Total Time:** 20-50ms (Redis network round-trip)

---

### Sequence: Multi-Timeframe Analysis

```
Client: emit advisor:multi_timeframe (H1, H4, D1)
  ↓
AdvisorProcessor: process_multi_timeframe(symbol, [H1, H4, D1])
  ├─ await process_technical_summary(symbol, H1)
  ├─ await process_technical_summary(symbol, H4)  } asyncio.gather
  └─ await process_technical_summary(symbol, D1)  } concurrent
  ↓
  Calculate alignment:
  ├─ Extract each overall.signal
  ├─ Count: bullish=2, bearish=1, neutral=0
  ├─ Determine: bullish_bias
  └─ Set: power_zone=false
  ↓
Return {timeframes: {...}, alignment: {...}}
  ↓
Client: receive response
```

**Total Time:** 600-2500ms (concurrent timeframe requests, serial aggregation)

---

## Integration Points

### With MT5 Terminal
- **Connection:** Via MetaTrader5 Python API
- **Data:** OHLCV rates (open, high, low, close, tick_volume)
- **Frequency:** On-demand (no streaming)
- **Error Handling:** Graceful None return on import failure

### With Socket.IO Server
- **Transport:** WebSocket + fallbacks
- **Events:** Custom `advisor:*` namespace events
- **Sessions:** Per-client SID tracking
- **Error Response:** `advisor:error` event

### With Redis
- **Connection:** Async connection pool
- **Serialization:** JSON (with proper typing)
- **Reliability:** Non-critical (graceful degradation)
- **Monitoring:** Health check via ping()

### With Pydantic Models
- **Request Validation:** TechnicalSummaryRequest
- **Response Structure:** TechnicalSummaryResponse
- **Type Safety:** Full type hints

---

## Configuration Parameters

**Indicator Defaults** (customizable via `TechnicalAnalyzer(params={})`):
```python
{
    "sma_periods": [20, 50, 200],
    "ema_periods": [9, 21, 50],
    "rsi_period": 14,
    "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
    "bb_period": 20, "bb_std": 2,
    "atr_period": 14,
    "adx_period": 14,
    "stoch_k": 14, "stoch_d": 3,
}
```

**Cache Configuration**:
- Indicators: 60s TTL
- Patterns (Phase 02): 300s TTL
- Connection: localhost:6379 (configurable via env)

**Data Fetcher Configuration**:
- Default candles: 100
- Max concurrent requests: asyncio limit

---

## Scaling Considerations

### Single Node (Current)
- Redis: In-memory (~1MB per 100 cached results)
- CPU: MT5 blocking calls bottleneck
- Memory: DataFrame allocation for OHLCV

### Multi-Node (Future)
- Redis: Shared cache for all nodes
- Load Balancer: Route to any node
- MT5: Single terminal access (potential bottleneck)

### Optimization Opportunities
- Batch OHLCV requests for multiple symbols
- Pre-compute common analysis combinations
- Implement pattern detection caching
- Stream updates via WebSocket instead of pull

---

## Error Propagation

```
MT5 Error (no data)
  ↓
DataFetcher: return None
  ↓
AdvisorProcessor: error_response(MT5_ERROR, "Failed to fetch...")
  ↓
EventHandler: emit advisor:error
  ↓
Client: handle error

Validation Error (bad symbol)
  ↓
EventHandler: validate_symbol() fails
  ↓
EventHandler: emit advisor:error (VALIDATION_ERROR)
  ↓
Client: handle error

Redis Error (connection lost)
  ↓
RedisClient: log warning, return None
  ↓
AdvisorProcessor: proceeds without caching (degraded mode)
  ↓
Client: receives response normally (no error emitted)
```

---

## Phase 04 Components (AI Recommendations)

### 6. AI Summarizer (`ai_summarizer.py`)

**Responsibilities:**
- Generate natural language technical analysis summaries
- Support Claude 3.7 Sonnet (primary) and DeepSeek (fallback)
- Implement semantic caching for cost optimization
- Support Vietnamese and English output

**Key Features:**
```python
async def generate_summary(
    self,
    analysis_data: Dict[str, Any],
    language: str = "vi",  # Vietnamese or English
    use_cache: bool = True,
    model: Optional[str] = None  # "claude" or "deepseek"
) -> Dict[str, Any]:
    """
    Returns:
    {
        "summary": "Technical analysis in natural language",
        "signal": "BUY/SELL/HOLD",
        "confidence": 75,  # 0-100
        "reasoning": "Brief explanation",
        "model": "claude",
        "language": "vi",
        "cached": True/False,
        "generated_at": "ISO 8601"
    }
    """
```

**Semantic Caching Strategy:**
- Cache key: Hash of symbol, timeframe, RSI signal, trend, price bucket
- TTL: 300s (5 minutes for summary cache)
- Cost reduction: ~75% with typical usage patterns
- Hit rate tracking via response metadata

**Prompt Engineering:**
- Few-shot examples in both Vietnamese and English
- Structured JSON output format
- Risk profile context integration
- Fallback parsing for JSON extraction failures

---

### 7. Recommendation Engine (`recommendation_engine.py`)

**Responsibilities:**
- Aggregate technical, pattern, and support/resistance signals
- Apply user risk profile weighting
- Generate entry/exit targets using ATR
- Produce final formatted recommendations

**Signal Aggregation Logic:**

```
Technical Signal (weighted):
  - Trend: 2.0x weight
  - MACD: 1.5x weight
  - RSI: 1.0x weight
  - Bollinger: 0.8x weight
  - ADX: 0.7x weight

Pattern Signal (if available):
  - Candlestick patterns: 1.0x weight
  - Chart patterns: 2.0x weight (stronger)

Overall Signal Calculation:
  combined_score = (tech_score * risk_weight) + (pattern_score * risk_weight)

  Risk Weighting:
  - Conservative: tech 0.7, pattern 0.3, confirmation required
  - Moderate: tech 0.6, pattern 0.4
  - Aggressive: tech 0.5, pattern 0.5
```

**Signal Strength Enum:**
```python
STRONG_BUY, BUY, WEAK_BUY, HOLD, WEAK_SELL, SELL, STRONG_SELL
```

**Target Calculation (ATR-based):**
```
ATR Multipliers by Risk Tolerance:
- Conservative: SL = 2.0x ATR, TP = 3.0x ATR
- Moderate: SL = 1.5x ATR, TP = 2.5x ATR
- Aggressive: SL = 1.0x ATR, TP = 2.0x ATR

For BUY signal:
- Entry: Current price
- Stop Loss: Entry - (ATR * multiplier)
- Take Profit: Entry + (ATR * multiplier)

With Support/Resistance overrides:
- Use nearest S/R if available and more favorable
```

---

### 8. User Profile Model (`user_profile.py`)

**Data Structure:**
```python
UserProfile:
  - user_id: str
  - risk_tolerance: "conservative" | "moderate" | "aggressive"
  - preferred_timeframes: List[str]  # ["H1", "H4", "D1"]
  - preferred_indicators: List[str]  # ["RSI", "MACD", "SMA"]
  - watchlist: List[str]
  - max_position_risk: float  # 0.005 to 0.10 (0.5% to 10%)
  - language: "vi" | "en"
  - created_at, updated_at: datetime
```

---

## Data Flow: AI Recommendation Request (Phase 04)

```
Client: emit advisor:recommendation {
  symbol: "XAUUSD",
  timeframe: "H1",
  language: "vi",
  risk_profile: "moderate"
}
  ↓
EventHandler: validate_symbol() → validate_timeframe()
  ↓
AdvisorProcessor: process_recommendation()
  ├─ Step 1: Get technical analysis
  │  └─ process_technical_summary() ← Cache hit/miss
  │
  ├─ Step 2: Get pattern analysis (with S/R)
  │  └─ process_pattern_scan(include_sr=True)
  │
  ├─ Step 3: Build user profile
  │  └─ {risk_tolerance, preferred_timeframe}
  │
  ├─ Step 4: AI Summarization
  │  ├─ Check semantic cache (hash key)
  │  ├─ If hit: return cached AI summary
  │  └─ If miss:
  │     ├─ Build LLM prompt with technical data
  │     ├─ Call Claude API (primary)
  │     ├─ On failure: fallback to DeepSeek
  │     ├─ Parse JSON response
  │     └─ Cache result for 5 minutes
  │
  ├─ Step 5: Generate Recommendation
  │  ├─ Aggregate technical signals (weighted)
  │  ├─ Aggregate pattern signals
  │  ├─ Calculate overall signal (risk-adjusted)
  │  ├─ Determine entry/stop/target levels
  │  └─ Format final recommendation
  │
  └─ Step 6: Return combined result
     ├─ overall_signal: {signal, strength, confidence}
     ├─ targets: {entry, stop_loss, take_profit}
     ├─ ai_summary: {summary, reasoning, cached flag}
     └─ recommendation: {action, confidence_text, targets}
  ↓
EventHandler: emit advisor:recommendation_result
  ↓
Client: receive complete recommendation
```

**Latency Profile (Phase 04):**
- AI summary cache hit: ~200-300ms (local Redis + parse)
- AI summary cache miss: ~1.5-3s (LLM API call + cache)
- Full recommendation with all components: ~2-4s first request

---

## Error Handling (Phase 04)

```
LLM API Error (Claude/DeepSeek down):
  ↓
AISummarizer catches exception
  ↓
Returns fallback response:
  {
    "error": "API error message",
    "summary": "Unable to generate AI summary",
    "signal": "HOLD",
    "confidence": 0,
    "reasoning": "AI service unavailable"
  }
  ↓
RecommendationEngine continues with technical + pattern signals only
  ↓
Client receives complete recommendation (without AI summary)

Invalid JSON from LLM:
  ↓
AISummarizer fallback parsing
  ↓
Extracts BUY/SELL/HOLD from text if possible
  ↓
Returns partially parsed result

Cache Errors:
  ↓
AISummarizer logs warning, continues without cache
  ↓
Makes full LLM request (no cost savings but still functional)
```

---

## Cost Optimization (Phase 04)

**Semantic Caching Impact:**
- Average prompt: ~400 tokens
- Average response: ~100 tokens
- Claude cost per call: ~$0.015 (input) + $0.0006 (output)
- With 75% cache hit rate: ~$0.005 per call effective

**Monthly Cost Estimate (1000 analyses):**
- Without caching: ~$16/month
- With 75% caching: ~$4/month
- DeepSeek fallback savings: Minimal (only used on errors)

**Optimization Strategies:**
1. Round prices to nearest 10 for more cache hits
2. Batch similar timeframes to leverage pattern cache
3. Pre-warm cache with popular symbol/timeframe combinations
4. Monitor cache hit rates via logging

---

## Integration Points (Phase 04)

### With LLM Services:
- **Claude API:** `anthropic` Python package, HTTP/2 protocol
- **DeepSeek:** OpenAI-compatible API endpoint
- **Auth:** API keys via environment variables (ANTHROPIC_API_KEY, DEEPSEEK_API_KEY)
- **Latency:** 500-2000ms typical for LLM response

### With User Profile:
- Stored in application memory (future: PostgreSQL)
- Retrieved per recommendation request
- Risk tolerance drives signal weighting and target sizing

### With Redis Cache:
- Key format: `ai_summary:{hash(symbol, tf, signals, price_bucket)}`
- Separate from indicator cache (different TTL)
- JSON serialization for complex objects

---

## Future Architecture Changes (Phase 02+)

1. **Pattern Detection Module**
   - Candlestick pattern matcher
   - Chart pattern detector
   - ML-based pattern recognition

2. **Support & Resistance Module**
   - Pivot point calculator
   - Fibonacci levels
   - Volume profile

3. **Caching Enhancement**
   - Cache invalidation on market events
   - Prediction-based pre-computation
   - Distributed cache (Redis cluster)

4. **Streaming**
   - WebSocket push updates (on market tick)
   - Subscription model (subscribe to symbol/TF)
   - Efficient delta updates

