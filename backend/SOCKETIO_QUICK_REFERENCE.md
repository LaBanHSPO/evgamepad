# Socket.IO API Quick Reference

**Server:** `http://localhost:8686`
**Health Check:** `GET /health`

---

## Connection Events

| Event | Direction | Data |
|-------|-----------|------|
| `connect` | → Server | Auto |
| `connected` | ← Server | `{ message, session_id, server_time }` |
| `session_recovered` | ← Server | `{ message, session_id, pending_orders, reconnected_at }` |
| `disconnect` | → Server | Auto |

---

## Trading Events

### Login
```javascript
socket.emit('login', { account: 12345678, password: "pass", server: "Broker" })
socket.on('login_result', (result) => { /* account_info */ })
```

### Buy Order
```javascript
socket.emit('buy', { symbol: "EURUSD", volume: 0.01, sl: 1.0950, tp: 1.1050 })
socket.on('order_result', (result) => { /* ticket, price, volume */ })
```

### Sell Order
```javascript
socket.emit('sell', { symbol: "XAUUSD", volume: 0.5, sl: 2650, tp: 2600 })
socket.on('order_result', (result) => { /* ticket, price, volume */ })
```

### Modify Position
```javascript
socket.emit('modify', { ticket: 123456789, sl: 1.0960, tp: 1.1040 })
socket.on('modify_result', (result) => { /* ticket, sl, tp */ })
```

### Close Position
```javascript
socket.emit('close', { ticket: 123456789, volume: 0.01 })  // volume optional
socket.on('close_result', (result) => { /* ticket, price, profit */ })
```

### Error Handling
```javascript
socket.on('error', (error) => { /* error_code, message, details */ })
```

---

## AI Advisor Events

### Technical Summary
```javascript
socket.emit('advisor_technical_summary', {
  symbol: "XAUUSD",
  timeframe: "H1",
  indicators: ["sma", "rsi", "macd"]  // optional
})
socket.on('advisor:technical_result', (result) => {
  /* indicators, signals, overall */
})
```

### Multi-Timeframe Analysis
```javascript
socket.emit('advisor_multi_timeframe', {
  symbol: "XAUUSD",
  timeframes: ["H1", "H4", "D1"]
})
socket.on('advisor:multi_timeframe_result', (result) => {
  /* alignment, power_zone, signals */
})
```

### Pattern Scan
```javascript
socket.emit('advisor_pattern_scan', {
  symbol: "XAUUSD",
  timeframe: "H1",
  include_sr: true  // optional, default true
})
socket.on('advisor:pattern_result', (result) => {
  /* candlestick_patterns, chart_patterns, support_resistance */
})
```

### Risk Analysis
```javascript
socket.emit('advisor_risk_analysis', {
  symbol: "XAUUSD",
  account_balance: 10000,
  entry_price: 2634.50,
  stop_loss: 2625.00,
  take_profit: 2645.00,
  risk_profile: "moderate",  // conservative, moderate, aggressive
  timeframe: "H1"
})
socket.on('advisor:risk_result', (result) => {
  /* risk_reward, position_sizing, recommendation */
})
```

### AI Recommendation
```javascript
socket.emit('advisor_recommendation', {
  symbol: "XAUUSD",
  timeframe: "H1",
  language: "en",  // vi, en
  risk_profile: "moderate"
})
socket.on('advisor:recommendation_result', (result) => {
  /* recommendation, ai_summary, provenance */
})
```

### Portfolio Analysis
```javascript
socket.emit('advisor_portfolio_analysis', {
  positions: [
    {
      symbol: "XAUUSD",
      entry_price: 2630.50,
      current_price: 2634.00,  // optional
      position_size: 0.5,
      stop_loss: 2625.00,
      timeframe: "H1"
    }
  ],
  account_balance: 10000,
  risk_profile: "moderate",
  language: "en"
})
socket.on('advisor:portfolio_result', (result) => {
  /* portfolio_health, position_analysis, ai_advice */
})
```

### Explainability (Chain-of-Thought)
```javascript
socket.emit('advisor_explain_recommendation', {
  symbol: "XAUUSD",
  timeframe: "H1"
})
socket.on('advisor:explanation_result', (result) => {
  /* explainability: steps, total_score, confidence, reasoning */
})
```

### Record Trade Outcome
```javascript
socket.emit('advisor_record_outcome', {
  symbol: "XAUUSD",
  timeframe: "H1",
  signal: "BUY",  // BUY, SELL, HOLD
  confidence: 85,
  entry_price: 2634.50,
  exit_price: 2640.20,
  stop_loss: 2625.50,
  take_profit: 2645.00,
  exit_reason: "take_profit",  // manual, stop_loss, take_profit
  entry_at: "2025-12-30T10:00:00Z",  // optional ISO 8601
  exit_at: "2025-12-30T14:30:00Z"    // optional ISO 8601
})
socket.on('advisor:outcome_recorded', (result) => {
  /* outcome_id, message */
})
```

### Accuracy Report
```javascript
socket.emit('advisor_accuracy_report', {
  symbol: "XAUUSD",   // optional
  timeframe: "H1",    // optional
  signal: "BUY",      // optional: BUY, SELL, HOLD
  days: 30            // optional, default 30
})
socket.on('advisor:accuracy_result', (result) => {
  /* report: win_rate_pct, profit_factor, total_trades, etc. */
})
```

### Advisor Error Handling
```javascript
socket.on('advisor:error', (error) => {
  /* error_code, message, details */
})
```

---

## Quick Constants

### Timeframes
`M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`, `W1`, `MN1`

### Signals
`bullish`, `bearish`, `neutral`

### Risk Profiles
`conservative` (1% risk), `moderate` (2%), `aggressive` (3%)

### Languages
`vi` (Vietnamese), `en` (English)

### Exit Reasons
`manual`, `stop_loss`, `take_profit`

### Error Codes
- `VALIDATION_ERROR` - Invalid input
- `MT5_NOT_CONNECTED` - MT5 not connected
- `MT5_ERROR` - MT5 operation failed
- `POSITION_NOT_FOUND` - Position not found
- `INTERNAL_ERROR` - Server error

---

## Complete Event List

| Event | Type | Response Event | Caching |
|-------|------|----------------|---------|
| `login` | Trading | `login_result` | - |
| `buy` | Trading | `order_result` | - |
| `sell` | Trading | `order_result` | - |
| `modify` | Trading | `modify_result` | - |
| `close` | Trading | `close_result` | - |
| `advisor_technical_summary` | Advisor | `advisor:technical_result` | 60s |
| `advisor_multi_timeframe` | Advisor | `advisor:multi_timeframe_result` | Per-TF |
| `advisor_pattern_scan` | Advisor | `advisor:pattern_result` | 300s |
| `advisor_risk_analysis` | Advisor | `advisor:risk_result` | - |
| `advisor_recommendation` | Advisor | `advisor:recommendation_result` | 300s |
| `advisor_portfolio_analysis` | Advisor | `advisor:portfolio_result` | 300s |
| `advisor_explain_recommendation` | Advisor | `advisor:explanation_result` | - |
| `advisor_record_outcome` | Advisor | `advisor:outcome_recorded` | - |
| `advisor_accuracy_report` | Advisor | `advisor:accuracy_result` | - |

**Total Events:** 14 (5 trading + 9 advisor)

---

## Response Structure

### Success
```json
{
  "success": true,
  "data": { /* response data */ }
}
```

### Error
```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "message": "Human readable error",
  "details": { /* optional */ }
}
```

---

## Implementation Files

| Component | File |
|-----------|------|
| Trading Events | `app/events/trading_events.py` |
| Advisor Events | `app/events/advisor_events.py` |
| Trading Processor | `app/processors/command_processor.py` |
| Advisor Processor | `app/processors/advisor_processor.py` |
| MT5 Operations | `app/mt5/trading_operations.py` |
| Technical Analysis | `app/advisor/technical_analyzer.py` |
| Pattern Detection | `app/advisor/pattern_detector.py` |
| Risk Analysis | `app/advisor/risk_analyzer.py` |
| AI Recommendations | `app/advisor/recommendation_engine.py` |
| Explainability | `app/advisor/chain_of_thought_engine.py` |
| Accuracy Tracking | `app/advisor/accuracy_tracker.py` |

---

## Full Documentation

- **Comprehensive API Guide:** `SOCKETIO_API_GUIDE.md`
- **Implementation Status:** `BACKEND_IMPLEMENTATION_STATUS.md`
- **Setup Instructions:** `README.md`
- **Environment Variables:** `ENV_VARIABLES_PHASE_5_2.md`

---

**Status:** ✅ All functions implemented and ready to use
**Testing:** Run with `DEBUG=true` for detailed logs
**Health Check:** `curl http://localhost:8686/health`
