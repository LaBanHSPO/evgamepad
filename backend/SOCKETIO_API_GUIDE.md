# Socket.IO API Guide - MT5 Trading & AI Advisor Backend

## Table of Contents
1. [Overview](#overview)
2. [Connection Setup](#connection-setup)
3. [Trading Events](#trading-events)
4. [AI Advisor Events](#ai-advisor-events)
5. [Error Handling](#error-handling)
6. [Response Formats](#response-formats)
7. [Frontend Integration Examples](#frontend-integration-examples)

---

## Overview

**Server URL:** `http://localhost:8686` (default)
**Protocol:** Socket.IO (AsyncServer with ASGI)
**CORS:** Enabled for all origins (adjust for production)

### Server Configuration
- **Ping Interval:** 25s (heartbeat)
- **Ping Timeout:** 60s (disconnect after no response)
- **Max Message Size:** 1MB (1,000,000 bytes)

### Health Check Endpoint
**HTTP GET** `/health`

Returns:
```json
{
  "status": "healthy|unhealthy",
  "mt5_connected": true,
  "redis_connected": true,
  "db_connected": true,
  "accuracy_tracking_enabled": true,
  "connected_clients": 5
}
```

---

## Connection Setup

### Client Connection

**Event:** `connect`
- Automatically triggered on successful connection
- Server response: `connected` event

**Server Response:**
```javascript
socket.on('connected', (data) => {
  // {
  //   message: "Connected to MT5 Trading Server",
  //   session_id: "socket_id_here",
  //   server_time: "2025-12-31T10:00:00.000Z"
  // }
})
```

### Session Recovery (Reconnection)

If client reconnects within TTL (5 minutes):

**Server Response:** `session_recovered` event
```javascript
socket.on('session_recovered', (data) => {
  // {
  //   message: "Session recovered",
  //   session_id: "socket_id",
  //   pending_orders: [],
  //   reconnected_at: "2025-12-31T10:05:00.000Z"
  // }
})
```

### Disconnection

**Event:** `disconnect`
- Session stored for 5 minutes for recovery
- Pending orders preserved

---

## Trading Events

All trading events implemented in: `app/events/trading_events.py`

### 1. Login to MT5 Account

**Event:** `login`

**Request Payload:**
```javascript
{
  "account": 12345678,      // Integer (required)
  "password": "your_pass",  // String (required)
  "server": "Broker-Server" // String (required)
}
```

**Success Response:** `login_result`
```javascript
{
  "success": true,
  "data": {
    "account_info": {
      "login": 12345678,
      "name": "Account Name",
      "server": "Broker-Server",
      "currency": "USD",
      "balance": 10000.00,
      "equity": 10050.50,
      "leverage": 100
    }
  }
}
```

**Error Response:** `error` event (see Error Handling section)

**Implementation:**
- Location: `app/events/trading_events.py:103`
- Validation: `app/validation.py:validate_login_command()`
- Updates session with login status

---

### 2. Place Buy Order

**Event:** `buy`

**Request Payload:**
```javascript
{
  "symbol": "EURUSD",   // String (required)
  "volume": 0.01,       // Float (required, max 100 lots)
  "sl": 1.0950,         // Float (optional, stop loss)
  "tp": 1.1050          // Float (optional, take profit)
}
```

**Success Response:** `order_result`
```javascript
{
  "success": true,
  "data": {
    "command_id": "uuid-here",
    "ticket": 123456789,
    "symbol": "EURUSD",
    "volume": 0.01,
    "price": 1.1000,
    "sl": 1.0950,
    "tp": 1.1050,
    "timestamp": "2025-12-31T10:00:00.000Z"
  }
}
```

**Implementation:**
- Location: `app/events/trading_events.py:156`
- Processor: `app/processors/command_processor.py:process_buy_order()`
- Trading Ops: `app/mt5/trading_operations.py:place_buy_market()`
- Includes circuit breaker protection
- Automatic retry on transient errors (max 3 retries)

---

### 3. Place Sell Order

**Event:** `sell`

**Request Payload:**
```javascript
{
  "symbol": "XAUUSD",
  "volume": 0.5,
  "sl": 2650.00,    // Optional
  "tp": 2600.00     // Optional
}
```

**Success Response:** `order_result` (same format as buy)

**Implementation:**
- Location: `app/events/trading_events.py:187`
- Processor: `app/processors/command_processor.py:process_sell_order()`
- Trading Ops: `app/mt5/trading_operations.py:place_sell_market()`

---

### 4. Modify Position (SL/TP)

**Event:** `modify`

**Request Payload:**
```javascript
{
  "ticket": 123456789,  // Integer (required)
  "sl": 1.0960,         // Float (optional)
  "tp": 1.1040          // Float (optional)
  // Note: Must provide at least one of sl or tp
}
```

**Success Response:** `modify_result`
```javascript
{
  "success": true,
  "data": {
    "command_id": "uuid-here",
    "ticket": 123456789,
    "sl": 1.0960,
    "tp": 1.1040,
    "modified_at": "2025-12-31T10:05:00.000Z"
  }
}
```

**Implementation:**
- Location: `app/events/trading_events.py:217`
- Processor: `app/processors/command_processor.py:process_modify_position()`
- Trading Ops: `app/mt5/trading_operations.py:modify_position()`

---

### 5. Close Position

**Event:** `close`

**Request Payload:**
```javascript
{
  "ticket": 123456789,  // Integer (required)
  "volume": 0.01        // Float (optional, for partial close)
}
```

**Success Response:** `close_result`
```javascript
{
  "success": true,
  "data": {
    "command_id": "uuid-here",
    "ticket": 123456789,
    "close_ticket": 987654321,
    "close_price": 1.1025,
    "volume_closed": 0.01,
    "profit": 25.00,
    "closed_at": "2025-12-31T10:10:00.000Z"
  }
}
```

**Implementation:**
- Location: `app/events/trading_events.py:246`
- Processor: `app/processors/command_processor.py:process_close_position()`
- Trading Ops: `app/mt5/trading_operations.py:close_position()`

---

## AI Advisor Events

All advisor events implemented in: `app/events/advisor_events.py`

### 1. Technical Summary

**Event:** `advisor_technical_summary`

**Request Payload:**
```javascript
{
  "symbol": "XAUUSD",                    // String (required, alphanumeric max 20 chars)
  "timeframe": "H1",                     // String (required: M1, M5, M15, M30, H1, H4, D1, W1, MN1)
  "indicators": ["sma", "rsi", "macd"]   // Array (optional, specific indicators)
}
```

**Success Response:** `advisor:technical_result`
```javascript
{
  "success": true,
  "data": {
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "last_close": 2634.50,
    "indicators": {
      "sma_20": 2630.25,
      "sma_50": 2625.10,
      "rsi": 65.5,
      "macd": {
        "macd": 2.5,
        "signal": 1.8,
        "histogram": 0.7
      },
      "atr": 12.5
    },
    "signals": {
      "sma": "bullish",
      "rsi": "neutral",
      "macd": "bullish"
    },
    "overall": {
      "signal": "bullish",
      "confidence": 75,
      "strength": "moderate"
    },
    "cached": false,
    "computed_at": "2025-12-31T10:00:00.000Z"
  }
}
```

**Implementation:**
- Location: `app/events/advisor_events.py:32`
- Processor: `app/processors/advisor_processor.py:process_technical_summary()`
- Analyzer: `app/advisor/technical_analyzer.py`
- **Caching:** Redis 60s TTL

---

### 2. Multi-Timeframe Analysis

**Event:** `advisor_multi_timeframe`

**Request Payload:**
```javascript
{
  "symbol": "XAUUSD",
  "timeframes": ["H1", "H4", "D1"]  // Array of timeframes
}
```

**Success Response:** `advisor:multi_timeframe_result`
```javascript
{
  "success": true,
  "data": {
    "symbol": "XAUUSD",
    "timeframes": {
      "H1": { /* technical data */ },
      "H4": { /* technical data */ },
      "D1": { /* technical data */ }
    },
    "alignment": {
      "status": "strong_bullish",  // strong_bullish, strong_bearish, bullish_bias, bearish_bias, mixed
      "bullish_count": 3,
      "bearish_count": 0,
      "signals": [
        { "timeframe": "H1", "signal": "bullish", "confidence": 75 },
        { "timeframe": "H4", "signal": "bullish", "confidence": 80 },
        { "timeframe": "D1", "signal": "bullish", "confidence": 85 }
      ]
    },
    "power_zone": true,  // true if strong alignment
    "computed_at": "2025-12-31T10:00:00.000Z"
  }
}
```

**Implementation:**
- Location: `app/events/advisor_events.py:94`
- Processor: `app/processors/advisor_processor.py:process_multi_timeframe()`

---

### 3. Pattern Scan

**Event:** `advisor_pattern_scan`

**Request Payload:**
```javascript
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "include_sr": true  // Boolean (optional, default true)
}
```

**Success Response:** `advisor:pattern_result`
```javascript
{
  "success": true,
  "data": {
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "last_price": 2634.50,
    "candlestick_patterns": [
      {
        "name": "Bullish Engulfing",
        "signal": "bullish",
        "strength": "strong",
        "index": 98
      }
    ],
    "chart_patterns": [
      {
        "name": "Double Bottom",
        "type": "reversal",
        "signal": "bullish",
        "confidence": 80
      }
    ],
    "support_resistance": {
      "pivot": 2630.00,
      "support_levels": [2625.00, 2620.00, 2615.00],
      "resistance_levels": [2640.00, 2645.00, 2650.00],
      "nearest_support": 2625.00,
      "nearest_resistance": 2640.00
    },
    "cached": false,
    "computed_at": "2025-12-31T10:00:00.000Z"
  }
}
```

**Implementation:**
- Location: `app/events/advisor_events.py:135`
- Processor: `app/processors/advisor_processor.py:process_pattern_scan()`
- Pattern Detector: `app/advisor/pattern_detector.py`
- S/R Calculator: `app/advisor/support_resistance.py`
- **Caching:** Redis 300s TTL

---

### 4. Risk Analysis

**Event:** `advisor_risk_analysis`

**Request Payload:**
```javascript
{
  "symbol": "XAUUSD",         // String (optional, for ATR calculation)
  "account_balance": 10000,   // Float (required)
  "entry_price": 2634.50,     // Float (required)
  "stop_loss": 2625.00,       // Float (required)
  "take_profit": 2645.00,     // Float (required)
  "risk_profile": "moderate", // String (optional: conservative, moderate, aggressive)
  "timeframe": "H1"           // String (optional, for ATR)
}
```

**Success Response:** `advisor:risk_result`
```javascript
{
  "success": true,
  "data": {
    "symbol": "XAUUSD",
    "risk_reward": {
      "risk_amount": 9.50,
      "reward_amount": 10.50,
      "ratio": 1.11,
      "recommendation": "acceptable"
    },
    "position_sizing": {
      "max_volume": 0.05,
      "recommended_volume": 0.03,
      "risk_percentage": 2.0
    },
    "recommendation": {
      "action": "proceed",
      "notes": "Risk-reward ratio acceptable for moderate profile"
    },
    "computed_at": "2025-12-31T10:00:00.000Z"
  }
}
```

**Implementation:**
- Location: `app/events/advisor_events.py:193`
- Processor: `app/processors/advisor_processor.py:process_risk_analysis()`
- Risk Analyzer: `app/advisor/risk_analyzer.py`

---

### 5. AI Recommendation (Full Analysis)

**Event:** `advisor_recommendation`

**Request Payload:**
```javascript
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "language": "vi",           // String (optional: vi, en)
  "risk_profile": "moderate"  // String (optional)
}
```

**Success Response:** `advisor:recommendation_result`
```javascript
{
  "success": true,
  "data": {
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "language": "vi",
    "recommendation": {
      "action": "BUY",
      "confidence": 85,
      "entry_zone": [2630.00, 2635.00],
      "stop_loss": 2625.00,
      "take_profit": [2645.00, 2650.00],
      "reasoning": "Strong bullish alignment across timeframes..."
    },
    "ai_summary": {
      "market_context": "Gold showing strong upward momentum...",
      "key_factors": ["Technical alignment", "Support holding", "Volume confirmation"],
      "risks": ["Resistance at 2650", "Overbought RSI on lower timeframes"],
      "personalized_advice": "Based on your moderate risk profile..."
    },
    "provenance": {
      "data_sources": ["MT5 OHLCV", "Technical Indicators"],
      "model_used": "claude-3-5-sonnet",
      "generated_at": "2025-12-31T10:00:00.000Z"
    }
  }
}
```

**Implementation:**
- Location: `app/events/advisor_events.py:275`
- Processor: `app/processors/advisor_processor.py:process_recommendation()`
- Recommendation Engine: `app/advisor/recommendation_engine.py`
- AI Summarizer: `app/advisor/ai_summarizer.py`

---

### 6. Portfolio Analysis (Phase 5.4)

**Event:** `advisor_portfolio_analysis`

**Request Payload:**
```javascript
{
  "positions": [
    {
      "symbol": "XAUUSD",
      "entry_price": 2630.50,
      "current_price": 2634.00,  // Optional, fetched if not provided
      "position_size": 0.5,
      "stop_loss": 2625.00,      // Optional
      "timeframe": "H1"
    },
    // ... more positions
  ],
  "account_balance": 10000,
  "risk_profile": "conservative",  // conservative, moderate, aggressive
  "language": "vi"                 // vi, en
}
```

**Success Response:** `advisor:portfolio_result`
```javascript
{
  "success": true,
  "data": {
    "portfolio_health": {
      "score": 75,                    // 0-100
      "status": "HEALTHY",            // HEALTHY, CAUTION, DANGER
      "total_risk_exposure": 5.5,     // Percentage of account
      "current_drawdown": 2.3,
      "positions_at_risk": 0
    },
    "position_analysis": [
      {
        "symbol": "XAUUSD",
        "entry_price": 2630.50,
        "current_price": 2634.00,
        "pnl_pct": 0.13,
        "pnl_amount": 1.75,
        "r_multiple": 0.37,
        "distance_to_stop_pct": 0.34,
        "risk_status": "safe",         // safe, caution, approaching_stop, danger
        "recommendation": "HOLD",      // HOLD, REDUCE, CLOSE
        "technical_signal": "bullish",
        "technical_confidence": 75
      }
    ],
    "ai_advice": {
      "overall_assessment": "Portfolio in good health...",
      "capital_preservation_tips": [
        "Consider tightening stop on EURUSD position",
        "Reduce exposure on correlated pairs"
      ],
      "risk_warnings": [],
      "opportunities": ["XAUUSD showing continuation potential"],
      "model_used": "claude-3-5-sonnet",
      "language": "vi"
    },
    "cached": false,
    "computed_at": "2025-12-31T10:00:00.000Z"
  }
}
```

**Implementation:**
- Location: `app/events/advisor_events.py:334`
- Processor: `app/processors/advisor_processor.py:process_portfolio_analysis()`
- AI Advice: `app/advisor/ai_summarizer.py:generate_portfolio_advice()`
- **Caching:** Redis 300s TTL

---

### 7. Explainability (Chain-of-Thought)

**Event:** `advisor_explain_recommendation`

**Request Payload:**
```javascript
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "recommendation_id": "optional-uuid"  // Optional
}
```

**Success Response:** `advisor:explanation_result`
```javascript
{
  "success": true,
  "data": {
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "explainability": {
      "steps": [
        {
          "step": 1,
          "name": "Trend Analysis",
          "score": 2,
          "max_score": 2,
          "reasoning": "SMA(20) > SMA(50), clear uptrend",
          "data_used": ["sma_20", "sma_50"]
        },
        // ... more steps
      ],
      "total_score": 10,
      "max_score": 12,
      "confidence": 0.83,
      "recommendation": "BUY",
      "reasoning_summary": "Strong bullish setup based on...",
      "risks_identified": ["Resistance at 2650", "Overbought RSI"],
      "data_gaps": []
    },
    "provenance": {
      "data_sources": ["MT5", "Technical Indicators"],
      "timestamp": "2025-12-31T10:00:00.000Z"
    }
  }
}
```

**Implementation:**
- Location: `app/events/advisor_events.py:402`
- Chain-of-Thought Engine: `app/advisor/chain_of_thought_engine.py`
- **Feature Flag:** `ENABLE_EXPLAINABILITY=true`

---

### 8. Record Trade Outcome (Accuracy Tracking)

**Event:** `advisor_record_outcome`

**Request Payload:**
```javascript
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "signal": "BUY",                      // BUY, SELL, HOLD
  "confidence": 85,
  "entry_price": 2634.50,
  "exit_price": 2640.20,
  "stop_loss": 2625.50,                 // Optional
  "take_profit": 2645.00,               // Optional
  "exit_reason": "take_profit",         // manual, stop_loss, take_profit
  "entry_at": "2025-12-30T10:00:00Z",   // Optional (ISO 8601)
  "exit_at": "2025-12-30T14:30:00Z"     // Optional (ISO 8601)
}
```

**Success Response:** `advisor:outcome_recorded`
```javascript
{
  "success": true,
  "outcome_id": "uuid-here",
  "message": "Trade outcome recorded successfully"
}
```

**Implementation:**
- Location: `app/events/advisor_events.py:493`
- Accuracy Tracker: `app/advisor/accuracy_tracker.py:record_outcome()`
- **Requires:** PostgreSQL database + `ENABLE_ACCURACY_TRACKING=true`

---

### 9. Accuracy Report

**Event:** `advisor_accuracy_report`

**Request Payload:**
```javascript
{
  "symbol": "XAUUSD",   // Optional (filter by symbol)
  "timeframe": "H1",    // Optional (filter by timeframe)
  "signal": "BUY",      // Optional (filter by signal: BUY, SELL, HOLD)
  "days": 30            // Optional (default 30, max 365)
}
```

**Success Response:** `advisor:accuracy_result`
```javascript
{
  "success": true,
  "data": {
    "report": {
      "period_days": 30,
      "symbol": "XAUUSD",
      "timeframe": "H1",
      "signal": "BUY",
      "total_trades": 50,
      "wins": 35,
      "losses": 15,
      "break_evens": 0,
      "win_rate_pct": 70.0,
      "avg_pnl_pct": 2.5,
      "profit_factor": 2.33,
      "recommendation": "Excellent - High confidence trades"
    },
    "best_performing": [
      {
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "signal": "BUY",
        "win_rate_pct": 75.0,
        "total_trades": 20
      }
    ]
  }
}
```

**Implementation:**
- Location: `app/events/advisor_events.py:629`
- Accuracy Tracker: `app/advisor/accuracy_tracker.py`
- **Requires:** PostgreSQL database + `ENABLE_ACCURACY_TRACKING=true`

---

## Error Handling

All errors emitted via `error` or `advisor:error` events.

### Error Response Format
```javascript
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid symbol format (alphanumeric, max 20 chars)",
  "details": { /* optional additional info */ }
}
```

### Error Codes (ErrorCode enum)
- `VALIDATION_ERROR`: Invalid input parameters
- `MT5_NOT_CONNECTED`: MT5 terminal not connected
- `MT5_ERROR`: MT5 operation failed (includes retcode)
- `POSITION_NOT_FOUND`: Position ticket not found
- `INTERNAL_ERROR`: Server internal error

### Error Event Handlers

**For Trading Errors:**
```javascript
socket.on('error', (errorData) => {
  console.error('Trading error:', errorData)
  // {
  //   success: false,
  //   error_code: "MT5_ERROR",
  //   message: "MT5 Error 10004: Requote",
  //   details: { retcode: 10004, symbol: "EURUSD", volume: 0.01 }
  // }
})
```

**For Advisor Errors:**
```javascript
socket.on('advisor:error', (errorData) => {
  console.error('Advisor error:', errorData)
})
```

---

## Response Formats

### Success Response Structure
```javascript
{
  "success": true,
  "data": { /* response data */ }
}
```

### Error Response Structure
```javascript
{
  "success": false,
  "error_code": "ERROR_CODE_HERE",
  "message": "Human readable error message",
  "details": { /* optional context */ }
}
```

### Common Data Types

**Timeframes:** `M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`, `W1`, `MN1`

**Signals:** `bullish`, `bearish`, `neutral`

**Risk Profiles:** `conservative`, `moderate`, `aggressive`

**Languages:** `vi` (Vietnamese), `en` (English)

---

## Frontend Integration Examples

### Basic Setup (Socket.IO Client)

```javascript
import { io } from 'socket.io-client'

const socket = io('http://localhost:8686', {
  transports: ['websocket'],
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000
})

// Connection handlers
socket.on('connected', (data) => {
  console.log('Connected:', data)
})

socket.on('session_recovered', (data) => {
  console.log('Session recovered:', data)
})

socket.on('disconnect', () => {
  console.log('Disconnected')
})
```

### Trading Operations Example

```javascript
// Login
socket.emit('login', {
  account: 12345678,
  password: 'your_password',
  server: 'Broker-Server'
})

socket.on('login_result', (result) => {
  if (result.success) {
    console.log('Logged in:', result.data.account_info)
  }
})

// Place Buy Order
socket.emit('buy', {
  symbol: 'EURUSD',
  volume: 0.01,
  sl: 1.0950,
  tp: 1.1050
})

socket.on('order_result', (result) => {
  if (result.success) {
    console.log('Order placed:', result.data.ticket)
  }
})

// Modify Position
socket.emit('modify', {
  ticket: 123456789,
  sl: 1.0960,
  tp: 1.1040
})

socket.on('modify_result', (result) => {
  if (result.success) {
    console.log('Position modified:', result.data)
  }
})

// Close Position
socket.emit('close', {
  ticket: 123456789,
  volume: 0.01  // Optional for partial close
})

socket.on('close_result', (result) => {
  if (result.success) {
    console.log('Position closed, profit:', result.data.profit)
  }
})

// Error handling
socket.on('error', (error) => {
  console.error('Trading error:', error.message)
})
```

### AI Advisor Example

```javascript
// Technical Summary
socket.emit('advisor_technical_summary', {
  symbol: 'XAUUSD',
  timeframe: 'H1'
})

socket.on('advisor:technical_result', (result) => {
  if (result.success) {
    const { overall, indicators } = result.data
    console.log('Signal:', overall.signal, 'Confidence:', overall.confidence)
    console.log('RSI:', indicators.rsi)
  }
})

// Multi-Timeframe Analysis
socket.emit('advisor_multi_timeframe', {
  symbol: 'XAUUSD',
  timeframes: ['H1', 'H4', 'D1']
})

socket.on('advisor:multi_timeframe_result', (result) => {
  if (result.success) {
    const { alignment, power_zone } = result.data
    console.log('Alignment:', alignment.status)
    console.log('Power Zone:', power_zone)
  }
})

// AI Recommendation
socket.emit('advisor_recommendation', {
  symbol: 'XAUUSD',
  timeframe: 'H1',
  language: 'en',
  risk_profile: 'moderate'
})

socket.on('advisor:recommendation_result', (result) => {
  if (result.success) {
    const { recommendation, ai_summary } = result.data
    console.log('Action:', recommendation.action)
    console.log('Confidence:', recommendation.confidence)
    console.log('AI Summary:', ai_summary.market_context)
  }
})

// Portfolio Analysis
socket.emit('advisor_portfolio_analysis', {
  positions: [
    {
      symbol: 'XAUUSD',
      entry_price: 2630.50,
      current_price: 2634.00,
      position_size: 0.5,
      stop_loss: 2625.00,
      timeframe: 'H1'
    }
  ],
  account_balance: 10000,
  risk_profile: 'moderate',
  language: 'en'
})

socket.on('advisor:portfolio_result', (result) => {
  if (result.success) {
    const { portfolio_health, ai_advice } = result.data
    console.log('Portfolio Score:', portfolio_health.score)
    console.log('Status:', portfolio_health.status)
    console.log('AI Advice:', ai_advice.overall_assessment)
  }
})

// Error handling for advisor
socket.on('advisor:error', (error) => {
  console.error('Advisor error:', error.message)
})
```

### React Hook Example

```jsx
import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'

function useTradingSocket() {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const [sessionId, setSessionId] = useState(null)

  useEffect(() => {
    const newSocket = io('http://localhost:8686', {
      transports: ['websocket'],
      reconnection: true
    })

    newSocket.on('connected', (data) => {
      setConnected(true)
      setSessionId(data.session_id)
    })

    newSocket.on('session_recovered', (data) => {
      setConnected(true)
      setSessionId(data.session_id)
    })

    newSocket.on('disconnect', () => {
      setConnected(false)
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [])

  const login = (account, password, server) => {
    return new Promise((resolve, reject) => {
      socket.emit('login', { account, password, server })

      socket.once('login_result', (result) => {
        if (result.success) {
          resolve(result.data)
        } else {
          reject(result)
        }
      })

      socket.once('error', (error) => {
        reject(error)
      })
    })
  }

  const placeBuyOrder = (symbol, volume, sl, tp) => {
    return new Promise((resolve, reject) => {
      socket.emit('buy', { symbol, volume, sl, tp })

      socket.once('order_result', (result) => {
        if (result.success) {
          resolve(result.data)
        } else {
          reject(result)
        }
      })

      socket.once('error', (error) => {
        reject(error)
      })
    })
  }

  const getTechnicalSummary = (symbol, timeframe) => {
    return new Promise((resolve, reject) => {
      socket.emit('advisor_technical_summary', { symbol, timeframe })

      socket.once('advisor:technical_result', (result) => {
        if (result.success) {
          resolve(result.data)
        } else {
          reject(result)
        }
      })

      socket.once('advisor:error', (error) => {
        reject(error)
      })
    })
  }

  return {
    socket,
    connected,
    sessionId,
    login,
    placeBuyOrder,
    getTechnicalSummary
  }
}

export default useTradingSocket
```

---

## Implementation Status Summary

### Trading Events (READY ✅)
- ✅ `login` - MT5 account login
- ✅ `buy` - Place buy market order
- ✅ `sell` - Place sell market order
- ✅ `modify` - Modify position SL/TP
- ✅ `close` - Close position (full/partial)

### AI Advisor Events (READY ✅)
- ✅ `advisor_technical_summary` - Technical indicators analysis
- ✅ `advisor_multi_timeframe` - Multi-timeframe alignment
- ✅ `advisor_pattern_scan` - Candlestick & chart patterns + S/R
- ✅ `advisor_risk_analysis` - Risk/reward & position sizing
- ✅ `advisor_recommendation` - Full AI recommendation with LLM
- ✅ `advisor_portfolio_analysis` - Portfolio risk management (Phase 5.4)
- ✅ `advisor_explain_recommendation` - Chain-of-thought explainability (Phase 5.1)
- ✅ `advisor_record_outcome` - Record trade outcomes (Phase 5.2)
- ✅ `advisor_accuracy_report` - Performance metrics (Phase 5.2)

### Supporting Infrastructure (READY ✅)
- ✅ Circuit breaker protection for MT5 operations
- ✅ Automatic retry logic (max 3 retries with exponential backoff)
- ✅ Session management with auto-reconnection (5 min TTL)
- ✅ Redis caching for performance
- ✅ PostgreSQL for accuracy tracking (Phase 5.2)
- ✅ Data provenance tracking (Phase 5.3)
- ✅ Background MT5 history sync (5-minute intervals)

---

## Environment Variables

Required for full functionality:

```bash
# MT5 Connection
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=Broker-Server
MT5_CONN_TIMEOUT=30.0
MT5_HEALTH_INTERVAL=5.0

# Server
SOCKETIO_HOST=0.0.0.0
SOCKETIO_PORT=8686
DEBUG=false

# Redis (for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# LLM APIs (for AI features)
ANTHROPIC_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
DEFAULT_LLM_MODEL=claude  # or deepseek

# PostgreSQL (for accuracy tracking)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ev_gamepad
DB_USER=postgres
DB_PASSWORD=your_password

# Feature Flags
ENABLE_EXPLAINABILITY=true
ENABLE_PROVENANCE_TRACKING=true
ENABLE_ACCURACY_TRACKING=true
```

---

## Notes

1. **All functions are implemented and ready to use**
2. **Caching:** Technical summaries cached for 60s, patterns for 300s
3. **Retry Logic:** Automatic retry for transient MT5 errors (max 3 attempts)
4. **Circuit Breaker:** Protects against MT5 terminal failures
5. **Session Recovery:** Reconnecting clients within 5 min recover their session
6. **Background Tasks:** MT5 history sync runs every 5 minutes (when accuracy tracking enabled)
7. **Data Validation:** All inputs validated before processing
8. **Error Responses:** Consistent error format across all events

---

## Support & Documentation

- Backend Code: `app/events/`, `app/processors/`, `app/advisor/`
- Tests: `tests/` (unit tests with pytest)
- Health Check: `GET /health`
- Logs: Check server logs for detailed execution traces

For issues or questions, check server logs with `DEBUG=true` enabled.
