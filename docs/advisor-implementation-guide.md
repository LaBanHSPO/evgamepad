# AI Trading Advisor - Implementation Guide

## Quick Start

### Prerequisites
- Python 3.8+
- MetaTrader5 terminal (Windows only)
- Redis server running
- pip packages installed

### Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Start Redis Server**
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis-server

# Windows (if installed via WSL/Docker)
redis-server
```

3. **Verify MT5 Terminal**
- Launch MetaTrader5 client
- Ensure account is logged in
- Check terminal is responsive

4. **Run Backend**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Test Connection**
```bash
# In browser console or JavaScript
const socket = io('http://localhost:8000');
socket.emit('advisor:technical_summary', {
  symbol: 'XAUUSD',
  timeframe: 'H1'
});
socket.on('advisor:technical_result', console.log);
```

---

## Architecture Walkthrough

### Request Flow

1. **Client Initiates Request**
   ```javascript
   socket.emit('advisor:technical_summary', {
     symbol: 'XAUUSD',
     timeframe: 'H1',
     indicators: ['sma', 'rsi']
   });
   ```

2. **Socket.IO Event Handler** (`app/events/advisor_events.py`)
   ```python
   @sio.event
   async def advisor_technical_summary(sid: str, data: Dict[str, Any]):
       # Validation
       symbol = data.get('symbol', '').upper()
       if not validate_symbol(symbol):
           await sio.emit('advisor:error', ...)
           return
       
       # Route to processor
       result = await advisor_processor.process_technical_summary(
           sid, symbol, timeframe, indicators
       )
       await sio.emit('advisor:technical_result', result, to=sid)
   ```

3. **Advisor Processor** (`app/processors/advisor_processor.py`)
   ```python
   async def process_technical_summary(self, sid, symbol, timeframe, indicators):
       # Check cache
       if self.redis_client:
           cached = await self.redis_client.get_indicators(symbol, timeframe)
           if cached:
               cached['cached'] = True
               return success_response(cached)
       
       # Fetch data
       df = await self.data_fetcher.fetch_ohlcv(symbol, timeframe, count=100)
       
       # Analyze
       result = self.analyzer.calculate_indicators(df, indicators)
       result['overall'] = self.analyzer.get_overall_signal(result)
       
       # Cache
       if self.redis_client:
           await self.redis_client.set_indicators(symbol, timeframe, result, ttl=60)
       
       return success_response(result)
   ```

4. **Data Fetcher** (`app/advisor/data_fetcher.py`)
   ```python
   async def fetch_ohlcv(self, symbol, timeframe, count=100):
       try:
           import MetaTrader5 as mt5
       except ImportError:
           return None  # Graceful on non-Windows
       
       tf_minutes = MT5_TIMEFRAMES.get(timeframe.upper())
       mt5_tf = tf_map[tf_minutes]
       
       # Run MT5 (blocking) in thread pool
       def _fetch():
           return mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)
       
       rates = await asyncio.to_thread(_fetch)
       
       # Convert to DataFrame
       df = pd.DataFrame(rates)
       df['time'] = pd.to_datetime(df['time'], unit='s')
       return df[['time', 'open', 'high', 'low', 'close', 'volume']]
   ```

5. **Technical Analyzer** (`app/advisor/technical_analyzer.py`)
   ```python
   def calculate_indicators(self, df, indicators=None):
       result = {
           'candles': len(df),
           'last_close': float(df['close'].iloc[-1]),
           'indicators': {},
           'signals': {},
       }
       
       # SMA
       if 'sma' in indicators:
           for period in self.params['sma_periods']:
               sma = ta.sma(df['close'], length=period)
               result['indicators'][f'sma_{period}'] = round(float(sma.iloc[-1]), 5)
       
       # RSI with signals
       if 'rsi' in indicators:
           rsi = ta.rsi(df['close'], length=self.params['rsi_period'])
           rsi_val = float(rsi.iloc[-1])
           result['indicators']['rsi'] = round(rsi_val, 2)
           
           if rsi_val < 30:
               result['signals']['rsi'] = 'oversold'
           elif rsi_val > 70:
               result['signals']['rsi'] = 'overbought'
       
       # Overall signal aggregation
       result['overall'] = self.get_overall_signal(result)
       
       return result
   ```

6. **Redis Cache** (`app/database/redis_client.py`)
   ```python
   async def set_indicators(self, symbol, timeframe, data, ttl=60):
       key = f"indicators:{symbol}:{timeframe}"
       await self._client.setex(key, ttl, json.dumps(data))
   ```

7. **Response to Client**
   ```javascript
   socket.on('advisor:technical_result', (response) => {
     // response = {
     //   success: true,
     //   data: {
     //     symbol: 'XAUUSD',
     //     indicators: {...},
     //     signals: {...},
     //     overall: {...}
     //   }
     // }
   });
   ```

---

## Code Organization

```
backend/
├── app/
│   ├── advisor/                    # Advisor modules
│   │   ├── technical_analyzer.py  # Indicator calculation
│   │   ├── data_fetcher.py         # MT5 data retrieval
│   │   ├── pattern_detector.py     # Phase 02 (stub)
│   │   └── support_resistance.py   # Phase 02 (stub)
│   │
│   ├── database/
│   │   └── redis_client.py         # Cache wrapper
│   │
│   ├── events/
│   │   └── advisor_events.py       # Socket.IO events
│   │
│   ├── processors/
│   │   └── advisor_processor.py    # Orchestration
│   │
│   ├── models/
│   │   └── advisor_models.py       # Pydantic models
│   │
│   ├── config.py                   # Configuration
│   └── main.py                     # Entry point
│
└── tests/
    └── test_technical_analyzer.py  # Unit tests
```

---

## Common Tasks

### Adding a New Indicator

1. **Update TechnicalAnalyzer** (app/advisor/technical_analyzer.py)
   ```python
   def calculate_indicators(self, df, indicators=None):
       # Add to your indicator list
       if "roc" in indicators:  # Rate of Change
           roc = ta.roc(df['close'], length=self.params["roc_period"])
           result["indicators"]["roc"] = round(float(roc.iloc[-1]), 5)
   ```

2. **Update Default Parameters**
   ```python
   DEFAULT_PARAMS = {
       # ... existing ...
       "roc_period": 12,  # New parameter
   }
   ```

3. **Add Signal Logic** (optional)
   ```python
   if "roc" in indicators:
       roc_val = result["indicators"]["roc"]
       if roc_val > 0:
           result["signals"]["roc"] = "bullish"
       elif roc_val < 0:
           result["signals"]["roc"] = "bearish"
   ```

4. **Update Tests** (tests/test_technical_analyzer.py)
   ```python
   def test_calculate_roc(self, sample_ohlcv_data):
       analyzer = TechnicalAnalyzer()
       result = analyzer.calculate_indicators(sample_ohlcv_data, indicators=['roc'])
       
       assert 'roc' in result['indicators']
       assert result['indicators']['roc'] is not None
   ```

5. **Update API Documentation** (docs/advisor-api-specification.md)
   - Add to indicators list
   - Document range/meaning
   - Provide example response

---

### Adding a New Event Handler

1. **Create Event Handler** (app/events/advisor_events.py)
   ```python
   @sio.event
   async def advisor_new_analysis(sid: str, data: Dict[str, Any]):
       """New analysis endpoint."""
       logger.info(f"New analysis from {sid}")
       
       try:
           symbol = data.get('symbol', '').upper()
           
           if not validate_symbol(symbol):
               await sio.emit('advisor:error', 
                   error_response(ErrorCode.VALIDATION_ERROR, "..."), 
                   to=sid)
               return
           
           result = await advisor_processor.process_new_analysis(sid, symbol)
           await sio.emit('advisor:new_result', result, to=sid)
           
       except Exception as e:
           logger.exception(f"Failed: {e}")
           await sio.emit('advisor:error', 
               error_response(ErrorCode.INTERNAL_ERROR, str(e)), 
               to=sid)
   ```

2. **Add Processor Method** (app/processors/advisor_processor.py)
   ```python
   async def process_new_analysis(self, sid: str, symbol: str):
       """Process new analysis."""
       logger.info(f"[{sid}] Processing new analysis: {symbol}")
       
       # Your logic here
       
       return success_response({
           "symbol": symbol,
           "result": "..."
       })
   ```

3. **Update Client Code**
   ```javascript
   socket.emit('advisor:new_analysis', { symbol: 'XAUUSD' });
   socket.on('advisor:new_result', (response) => {
       if (response.success) {
           console.log(response.data);
       }
   });
   ```

---

### Debugging Tips

**1. Check Redis Connection**
```python
import asyncio
from app.database.redis_client import RedisClient

async def test_redis():
    redis = RedisClient()
    connected = await redis.connect()
    print(f"Redis connected: {connected}")
    
    # Test set/get
    await redis.set_indicators('TEST', 'H1', {'test': 'data'})
    data = await redis.get_indicators('TEST', 'H1')
    print(f"Cached data: {data}")
    
    await redis.disconnect()

asyncio.run(test_redis())
```

**2. Check MT5 Connection**
```python
import MetaTrader5 as mt5

# Verify terminal is connected
if mt5.initialize():
    print("MT5 Connected")
    
    # Test fetching data
    rates = mt5.copy_rates_from_pos('XAUUSD', mt5.TIMEFRAME_H1, 0, 100)
    print(f"Fetched {len(rates)} candles")
    
    mt5.shutdown()
else:
    print("MT5 NOT connected - ensure terminal is open")
```

**3. Test Indicator Calculation**
```python
import pandas as pd
from app.advisor.technical_analyzer import TechnicalAnalyzer

# Create sample data
df = pd.DataFrame({
    'time': pd.date_range('2024-01-01', periods=100, freq='H'),
    'open': [2100 + i*0.5 for i in range(100)],
    'high': [2102 + i*0.5 for i in range(100)],
    'low': [2098 + i*0.5 for i in range(100)],
    'close': [2101 + i*0.5 for i in range(100)],
    'volume': [1000000]*100
})

analyzer = TechnicalAnalyzer()
result = analyzer.calculate_indicators(df, indicators=['sma', 'rsi'])
print(result)
```

**4. View Logs**
```bash
# Run with debug logging
python -m uvicorn app.main:app --reload --log-level debug

# Or add to your script
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Performance Optimization

### 1. Cache Strategy
- Request same symbol/timeframe within 60s → cache hit
- Different timeframe → separate cache key
- Clear cache: `redis-cli FLUSHDB` (dev only)

### 2. Concurrent Requests
- Multi-timeframe uses `asyncio.gather()` for concurrency
- Limits: MT5 terminal responsiveness
- Future: Implement batch MT5 queries

### 3. Data Reduction
- Request specific indicators only (not all 9)
- Reduce candle count if possible (100 is standard)
- Use multi-timeframe to avoid repeat single-TF requests

### 4. Caching Tuning
- Increase TTL for slower markets
- Decrease TTL for fast markets
- Use Redis MONITOR to watch cache traffic

---

## Testing

### Run Unit Tests
```bash
pytest tests/test_technical_analyzer.py -v
```

### Coverage Report
```bash
pytest tests/test_technical_analyzer.py --cov=app.advisor --cov-report=html
open htmlcov/index.html
```

### Integration Test (Manual)
```bash
# Terminal 1: Start server
python -m uvicorn app.main:app --reload

# Terminal 2: Python test script
import asyncio
from app.advisor.technical_analyzer import TechnicalAnalyzer
from app.advisor.data_fetcher import DataFetcher
import pandas as pd

async def test():
    # Test with mock data
    df = pd.DataFrame({
        'time': pd.date_range('2024-01-01', periods=100, freq='H'),
        'close': range(100),
        'volume': [1000]*100,
        'open': range(100),
        'high': range(100),
        'low': range(100)
    })
    
    analyzer = TechnicalAnalyzer()
    result = analyzer.calculate_indicators(df)
    print(result['overall'])

asyncio.run(test())
```

---

## Deployment Checklist

- [ ] All unit tests passing
- [ ] Redis server running in production
- [ ] MetaTrader5 terminal open on server machine
- [ ] Environment variables configured
- [ ] Logging configured for production
- [ ] Error handling tested (network failures)
- [ ] Cache TTL tuned for market conditions
- [ ] API documented for clients
- [ ] Performance benchmarks recorded
- [ ] Monitoring/alerting configured

---

## Troubleshooting

### "MetaTrader5 not available on this platform"
- MT5 library only works on Windows
- Non-Windows environments: returns None → MT5_ERROR response
- Solution: Use Windows server or mock data for testing

### Redis connection timeout
- Check Redis service: `redis-cli ping` (should return PONG)
- Check Redis config: host/port correct?
- Check firewall: Redis port 6379 accessible?

### Slow indicator calculation
- Reduce candle count
- Request fewer indicators
- Check system resources

### Socket.IO connection issues
- Check CORS configuration
- Verify WebSocket protocol supported
- Check firewall/proxy rules

---

## Phase 04: AI Recommendations Implementation

### New Files

**1. AI Summarizer** (`app/advisor/ai_summarizer.py`)
```python
from app.advisor.ai_summarizer import AISummarizer

# Initialize
ai_summarizer = AISummarizer(
    anthropic_api_key=config.ANTHROPIC_API_KEY,
    deepseek_api_key=config.DEEPSEEK_API_KEY,
    default_model="claude",
    redis_client=redis_client
)

# Generate summary
result = await ai_summarizer.generate_summary(
    analysis_data={
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "last_price": 2105.50,
        "indicators": {...},
        "signals": {...},
        "risk_profile": "moderate"
    },
    language="vi",  # Vietnamese or English
    use_cache=True,
    model="claude"  # or "deepseek"
)

# Result
{
    "summary": "Natural language analysis...",
    "signal": "BUY",
    "confidence": 75,
    "reasoning": "Explanation...",
    "model": "claude",
    "cached": True/False,
    "generated_at": "ISO 8601"
}
```

**2. Recommendation Engine** (`app/advisor/recommendation_engine.py`)
```python
from app.advisor.recommendation_engine import RecommendationEngine

# Initialize
rec_engine = RecommendationEngine(ai_summarizer=ai_summarizer)

# Generate recommendation
recommendation = await rec_engine.generate_recommendation(
    symbol="XAUUSD",
    technical_data=tech_result,
    pattern_data=pattern_result,
    sr_data=sr_result,
    user_profile={
        "risk_tolerance": "moderate",
        "preferred_timeframe": "H1"
    },
    language="vi"
)

# Result includes:
# - technical_signal: {signal, strength, weights}
# - pattern_signal: {signal, confidence, patterns}
# - overall_signal: {signal, strength, confidence, score}
# - targets: {entry, stop_loss, take_profit}
# - ai_summary: {summary, signal, confidence, reasoning}
# - recommendation: {action, confidence, entry, SL, TP}
```

**3. User Profile** (`app/models/user_profile.py`)
```python
from app.models.user_profile import UserProfile, RiskTolerance

profile = UserProfile(
    user_id="user123",
    risk_tolerance=RiskTolerance.MODERATE,
    preferred_timeframes=["H1", "H4", "D1"],
    preferred_indicators=["RSI", "MACD", "SMA"],
    watchlist=["XAUUSD", "EURUSD"],
    max_position_risk=0.02,  # 2%
    language="vi"
)
```

### Configuration

Update `.env` file:
```bash
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...
DEFAULT_LLM_MODEL=claude  # or deepseek

# Redis (for semantic caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

Update `app/config.py`:
```python
ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')
DEEPSEEK_API_KEY: str = os.getenv('DEEPSEEK_API_KEY', '')
DEFAULT_LLM_MODEL: str = os.getenv('DEFAULT_LLM_MODEL', 'claude')
```

### WebSocket Event Handler

```javascript
// Request recommendation
socket.emit('advisor:recommendation', {
  symbol: 'XAUUSD',
  timeframe: 'H1',
  language: 'vi',
  risk_profile: 'moderate'
});

// Listen for result
socket.on('advisor:recommendation_result', (result) => {
  console.log('Signal:', result.data.overall_signal.signal);
  console.log('Confidence:', result.data.overall_signal.confidence);
  console.log('Entry:', result.data.targets.entry);
  console.log('Stop Loss:', result.data.targets.stop_loss);
  console.log('Take Profit:', result.data.targets.take_profit);
  console.log('AI Summary:', result.data.ai_summary.summary);
  console.log('Cached:', result.data.ai_summary.cached);
});

// Handle errors
socket.on('advisor:error', (error) => {
  console.error('Error:', error.message);
});
```

### Cost Optimization Notes

**Semantic Caching Performance:**
- Cache hit rate: ~75% with typical usage
- Cache key: Hash of `{symbol, timeframe, RSI signal, trend, price_bucket}`
- TTL: 300 seconds (5 minutes)
- Cost savings: ~75% reduction in LLM API calls

**Cost Tracking:**
- Every LLM call is logged
- Monitor cache hit rate in logs: `cached: true/false`
- Estimated costs:
  - Without caching: ~$16/month (1000 analyses)
  - With 75% caching: ~$4/month

**Model Selection:**
- Use Claude (primary) for high-quality analysis
- Fallback to DeepSeek if Claude unavailable
- Configure via DEFAULT_LLM_MODEL env var

### Production Considerations

1. **API Key Management:**
   - Store API keys in secure vault (not git)
   - Rotate keys regularly
   - Monitor API usage quota

2. **Rate Limiting:**
   - Implement per-user rate limits
   - Monitor LLM API rate limits (Claude: 100k tokens/min)
   - Queue requests if approaching limits

3. **Monitoring:**
   - Log all LLM calls with request/response size
   - Track cache hit rates
   - Alert on LLM API errors
   - Monitor latency per component

4. **Error Resilience:**
   - LLM failures don't block recommendation
   - Returns technical-only recommendation if AI unavailable
   - Graceful degradation preserved

5. **Performance:**
   - First request (cache miss): 2-4 seconds expected
   - Cached request: 200-300 milliseconds
   - Parallel execution of technical/pattern analysis
   - Timeout: 10 seconds max per request

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.4.0 | Dec 30, 2025 | Phase 04 - AI Recommendations (Claude/DeepSeek + semantic caching) |
| 1.3.0 | Dec 30, 2025 | Phase 03 - Risk Analysis |
| 1.2.0 | Dec 30, 2025 | Phase 02 - Pattern Recognition & Support/Resistance |
| 1.0.0 | Dec 30, 2025 | Phase 01 - Technical Analysis |

---

## References

- [Technical Analyzer Code](../app/advisor/technical_analyzer.py)
- [API Specification](./advisor-api-specification.md)
- [System Architecture](./system-architecture-advisor.md)
- [pandas-ta Documentation](https://github.com/twopirllc/pandas-ta)
- [MetaTrader5 API](https://www.mql5.com/en/docs/python_api)

