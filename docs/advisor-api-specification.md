# AI Trading Advisor - API Specification

## Overview

WebSocket-based (Socket.IO) API for real-time technical analysis and trading intelligence. All communication via Socket.IO events.

**Base URL:** ws://localhost:8000
**Namespace:** / (root)
**Version:** 1.0.0

---

## Authentication

Currently: No authentication required (development version)
Future: JWT tokens via handshake

---

## Request/Response Format

### Request Structure
```json
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "indicators": ["sma", "rsi"]
}
```

### Response Structure (Success)
```json
{
  "success": true,
  "data": {...}
}
```

### Response Structure (Error)
```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "message": "Description"
}
```

---

## Endpoints (Events)

### 1. Technical Summary

**Event Name:** `advisor:technical_summary`

**Purpose:** Calculate technical indicators for single timeframe

**Request Schema:**
```typescript
interface TechnicalSummaryRequest {
  symbol: string;              // Required. Alphanumeric, 1-20 chars, uppercase
  timeframe?: "M1" | "M5" | "M15" | "M30" | "H1" | "H4" | "D1" | "W1" | "MN1"; // Default: H1
  indicators?: [                // Optional. Default: all
    "sma" | "ema" | "rsi" | "macd" | "bb" | "atr" | "adx" | "stoch" | "obv"
  ];
}
```

**Response Schema (Success):**
```typescript
interface TechnicalSummaryResponse {
  success: true;
  data: {
    symbol: string;
    timeframe: string;
    last_close: number;
    last_time: string;          // ISO 8601
    candles: number;
    cached: boolean;
    computed_at: string;        // ISO 8601
    
    indicators: {
      sma_20?: number;
      sma_50?: number;
      sma_200?: number;
      ema_9?: number;
      ema_21?: number;
      ema_50?: number;
      rsi?: number;              // 0-100
      macd?: {
        macd: number;
        signal: number;
        histogram: number;
      };
      bollinger?: {
        upper: number;
        middle: number;
        lower: number;
      };
      atr?: number;
      atr_pct?: number;           // ATR as % of price
      adx?: {
        adx: number;
        plus_di: number;
        minus_di: number;
      };
      stochastic?: {
        k: number;                // 0-100
        d: number;                // 0-100
      };
      obv?: number;               // On-balance volume
    };
    
    signals: {
      rsi?: "oversold" | "overbought" | "neutral";
      macd?: "bullish" | "bearish" | "bullish_crossover" | "bearish_crossover";
      bollinger?: "upper_band" | "inside" | "lower_band";
      adx?: "no_trend" | "moderate_trend" | "strong_trend";
      trend?: "bullish" | "bearish" | "mixed";
    };
    
    overall: {
      signal: "bullish" | "bearish" | "neutral";
      confidence: number;         // 0-1
      bullish_signals: number;
      bearish_signals: number;
      neutral_signals: number;
      reasoning: object;          // Individual signals breakdown
    };
  };
}
```

**Example Request:**
```javascript
socket.emit('advisor:technical_summary', {
  symbol: 'XAUUSD',
  timeframe: 'H1',
  indicators: ['sma', 'rsi', 'macd']
});
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "last_close": 2105.50,
    "last_time": "2025-12-30T15:30:00",
    "candles": 100,
    "cached": false,
    "computed_at": "2025-12-30T15:35:12.123456",
    "indicators": {
      "sma_20": 2103.25,
      "sma_50": 2101.50,
      "sma_200": 2100.00,
      "rsi": 65.50,
      "macd": {
        "macd": 4.25,
        "signal": 3.50,
        "histogram": 0.75
      }
    },
    "signals": {
      "rsi": "overbought",
      "macd": "bullish_crossover",
      "trend": "bullish"
    },
    "overall": {
      "signal": "bullish",
      "confidence": 0.83,
      "bullish_signals": 3,
      "bearish_signals": 0,
      "neutral_signals": 1,
      "reasoning": {
        "rsi": "overbought",
        "macd": "bullish_crossover",
        "trend": "bullish"
      }
    }
  }
}
```

**Caching:**
- Cache Key: `indicators:{symbol}:{timeframe}`
- TTL: 60 seconds
- Cache hit indicated by `cached: true`

---

### 2. Multi-Timeframe Analysis

**Event Name:** `advisor:multi_timeframe`

**Purpose:** Analyze symbol across multiple timeframes with alignment

**Request Schema:**
```typescript
interface MultiTimeframeRequest {
  symbol: string;               // Required
  timeframes?: string[];        // Default: ["H1", "H4", "D1"]
  indicators?: string[];        // Optional
}
```

**Response Schema (Success):**
```typescript
interface MultiTimeframeResponse {
  success: true;
  data: {
    symbol: string;
    timeframes: {
      [timeframe: string]: TechnicalSummaryResponse['data'];
    };
    alignment: {
      status: "strong_bullish" | "strong_bearish" | "bullish_bias" | "bearish_bias" | "mixed";
      bullish_count: number;
      bearish_count: number;
      neutral_count?: number;
      signals: {
        timeframe: string;
        signal: string;
        confidence: number;
      }[];
    };
    power_zone: boolean;        // true if strong_bullish or strong_bearish
    computed_at: string;
  };
}
```

**Example Request:**
```javascript
socket.emit('advisor:multi_timeframe', {
  symbol: 'XAUUSD',
  timeframes: ['H1', 'H4', 'D1']
});
```

**Example Response (Partial):**
```json
{
  "success": true,
  "data": {
    "symbol": "XAUUSD",
    "timeframes": {
      "H1": {...},
      "H4": {...},
      "D1": {...}
    },
    "alignment": {
      "status": "bullish_bias",
      "bullish_count": 2,
      "bearish_count": 1,
      "signals": [
        {"timeframe": "H1", "signal": "bullish", "confidence": 0.83},
        {"timeframe": "H4", "signal": "bullish", "confidence": 0.75},
        {"timeframe": "D1", "signal": "bearish", "confidence": 0.60}
      ]
    },
    "power_zone": false,
    "computed_at": "2025-12-30T15:35:12.123456"
  }
}
```

**Alignment Status Interpretation:**
- `strong_bullish`: All timeframes agree bullish
- `strong_bearish`: All timeframes agree bearish
- `bullish_bias`: More bullish than bearish
- `bearish_bias`: More bearish than bullish
- `mixed`: Conflicting signals
- `power_zone`: true only for strong consensus

---

### 3. AI-Powered Recommendations (Phase 04)

**Event Name:** `advisor:recommendation`

**Status:** Phase 04 (implemented)

**Purpose:** Generate personalized trading recommendations using AI analysis and user risk profile

**Request Schema:**
```typescript
interface RecommendationRequest {
  symbol: string;                         // Required. Trading symbol
  timeframe?: string;                     // Default: "H1"
  language?: "vi" | "en";                 // Default: "vi" (Vietnamese)
  risk_profile?: "conservative" | "moderate" | "aggressive"; // Default: "moderate"
}
```

**Response Schema (Success):**
```typescript
interface RecommendationResponse {
  success: true;
  data: {
    symbol: string;
    timeframe: string;
    language: string;

    // Technical signal aggregation
    technical_signal: {
      signal: "bullish" | "bearish" | "neutral";
      strength: number;           // 0-1, confidence
      bullish_weight: number;
      bearish_weight: number;
      total_weight: number;
      raw_signals: object;
    };

    // Pattern signal aggregation (if Phase 02 data available)
    pattern_signal?: {
      signal: "bullish" | "bearish" | "neutral";
      confidence: number;         // 0-1
      bullish_patterns: number;
      bearish_patterns: number;
      strongest_pattern: string;
    };

    // Final recommendation
    overall_signal: {
      signal: "BUY" | "SELL" | "HOLD";
      strength: string;           // "strong_buy", "buy", "weak_buy", etc.
      confidence: number;         // 0-100%
      combined_score: number;     // -1 to 1
      risk_tolerance_applied: string;
    };

    // Trading targets based on ATR
    targets: {
      current_price: number;
      entry: number;
      stop_loss: number;
      take_profit: number;
      stop_loss_sr?: number;      // Support/resistance override
      take_profit_sr?: number;    // Support/resistance override
    };

    // AI-generated summary
    ai_summary: {
      summary: string;            // Natural language analysis
      signal: string;             // BUY/SELL/HOLD
      confidence: number;         // 0-100%
      reasoning: string;          // Explanation
      model: "claude" | "deepseek";
      cached: boolean;            // Whether from cache
      generated_at: string;       // ISO 8601
    };

    // Final recommendation text
    recommendation: {
      action: string;             // "MUA"/"BÁN"/"GIỮ" (vi) or "BUY"/"SELL"/"HOLD" (en)
      signal: string;
      confidence: number;
      confidence_text: string;
      entry: number;
      stop_loss: number;
      take_profit: number;
      summary: string;            // AI-generated
      reasoning: string;          // AI-generated
    };

    generated_at: string;         // ISO 8601
  };
}
```

**Example Request:**
```javascript
socket.emit('advisor:recommendation', {
  symbol: 'XAUUSD',
  timeframe: 'H1',
  language: 'vi',
  risk_profile: 'moderate'
});
```

**Example Response (Partial):**
```json
{
  "success": true,
  "data": {
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "language": "vi",

    "technical_signal": {
      "signal": "bullish",
      "strength": 0.75,
      "bullish_weight": 5.0,
      "bearish_weight": 1.5,
      "total_weight": 6.5
    },

    "overall_signal": {
      "signal": "BUY",
      "strength": "buy",
      "confidence": 68,
      "combined_score": 0.68,
      "risk_tolerance_applied": "moderate"
    },

    "targets": {
      "current_price": 2105.50,
      "entry": 2105.50,
      "stop_loss": 2098.25,
      "take_profit": 2123.75,
      "take_profit_sr": 2125.00
    },

    "ai_summary": {
      "summary": "Vàng (XAUUSD) hiện đang ở trạng thái tăng trưởng mạnh. RSI cho thấy tình trạng mua quá mức nhẹ, trong khi MACD duy trì tín hiệu tăng giá. Xu hướng tổng thể là tăng giá trên khung thời gian H1.",
      "signal": "BUY",
      "confidence": 72,
      "reasoning": "Các chỉ số kỹ thuật gần như đồng ý, xu hướng rõ ràng, hỗ trợ mối liên hệ mua.",
      "model": "claude",
      "cached": false,
      "generated_at": "2025-12-30T15:35:12.123456"
    },

    "recommendation": {
      "action": "MUA",
      "signal": "BUY",
      "confidence": 68,
      "confidence_text": "Độ tin cậy: 68%",
      "entry": 2105.50,
      "stop_loss": 2098.25,
      "take_profit": 2123.75,
      "summary": "Vàng hiện đang ở xu hướng tăng giá mạnh...",
      "reasoning": "Tín hiệu từ chỉ số kỹ thuật và AI phân tích..."
    },

    "generated_at": "2025-12-30T15:35:12.123456"
  }
}
```

**Latency:**
- First request (cache miss): 2-4 seconds (includes LLM call)
- Cached request: 200-300 milliseconds

**Caching:**
- AI Summary Cache Key: `ai_summary:{hash(symbol, timeframe, signals)}`
- TTL: 300 seconds (5 minutes)
- Cache hit indicated by `ai_summary.cached: true`

**Risk Profile Impact:**
```
Conservative:
  - Requires confirmation between technical and pattern signals
  - Wider stop loss (2.0x ATR), larger take profit (3.0x ATR)
  - Higher threshold for BUY/SELL signals

Moderate (default):
  - Balanced technical/pattern weights
  - Standard stop loss (1.5x ATR), take profit (2.5x ATR)
  - Medium threshold

Aggressive:
  - Doesn't require confirmation
  - Tight stop loss (1.0x ATR), rapid take profit (2.0x ATR)
  - Lower threshold for signals
```

---

### 4. Pattern Scan

**Event Name:** `advisor:pattern_scan`

**Status:** Phase 02-03 (implemented)

**Purpose:** Detect candlestick/chart patterns and support/resistance levels

**Request Schema:**
```typescript
interface PatternScanRequest {
  symbol: string;
  timeframe?: string;
  include_sr?: boolean;         // Include support/resistance
}
```

---

## Error Codes

### VALIDATION_ERROR (400)
Invalid input parameters. Symbol must be alphanumeric, 1-20 chars.

**Response:**
```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid symbol format (alphanumeric, max 20 chars)"
}
```

### MT5_ERROR (503)
Failed to fetch data from MetaTrader5 terminal.

**Causes:**
- Terminal not running/connected
- Invalid symbol
- Network issues
- Data unavailable for timeframe

**Response:**
```json
{
  "success": false,
  "error_code": "MT5_ERROR",
  "message": "Failed to fetch data for XAUUSD H1"
}
```

### INTERNAL_ERROR (500)
Server-side error during processing.

**Causes:**
- Calculation failure
- Unexpected data format
- System resource exhaustion

**Response:**
```json
{
  "success": false,
  "error_code": "INTERNAL_ERROR",
  "message": "Technical analysis failed: <details>"
}
```

### CACHE_ERROR (503 soft)
Redis cache unavailable. Request still processes without caching.

**Note:** Not returned to client; logged internally. System degrades gracefully.

---

## Client Implementation Examples

### JavaScript/Node.js

```javascript
const io = require('socket.io-client');

const socket = io('ws://localhost:8000');

socket.on('connect', () => {
  console.log('Connected');
  
  // Request technical summary
  socket.emit('advisor:technical_summary', {
    symbol: 'XAUUSD',
    timeframe: 'H1',
    indicators: ['sma', 'rsi', 'macd']
  });
});

// Listen for response
socket.on('advisor:technical_result', (response) => {
  if (response.success) {
    console.log('Indicators:', response.data.indicators);
    console.log('Overall Signal:', response.data.overall);
  }
});

// Listen for errors
socket.on('advisor:error', (error) => {
  console.error('Error:', error.error_code, error.message);
});
```

### Python

```python
import socketio
import asyncio

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('Connected')
    await sio.emit('advisor:technical_summary', {
        'symbol': 'XAUUSD',
        'timeframe': 'H1',
        'indicators': ['sma', 'rsi']
    })

@sio.event
async def advisor_technical_result(data):
    if data['success']:
        print('Indicators:', data['data']['indicators'])
        print('Signal:', data['data']['overall']['signal'])

@sio.event
async def advisor_error(data):
    print(f"Error: {data['error_code']} - {data['message']}")

async def main():
    await sio.connect('ws://localhost:8000')
    await sio.wait()

asyncio.run(main())
```

### React Hook

```typescript
import { useEffect, useRef } from 'react';
import io from 'socket.io-client';

export const useTechnicalAnalysis = () => {
  const socketRef = useRef(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    socketRef.current = io('ws://localhost:8000');

    socketRef.current.on('advisor:technical_result', (data) => {
      if (data.success) {
        setResult(data.data);
        setLoading(false);
      }
    });

    socketRef.current.on('advisor:error', (data) => {
      setError(data.message);
      setLoading(false);
    });

    return () => socketRef.current?.disconnect();
  }, []);

  const analyze = (symbol, timeframe, indicators) => {
    setLoading(true);
    socketRef.current.emit('advisor:technical_summary', {
      symbol,
      timeframe,
      indicators
    });
  };

  return { result, error, loading, analyze };
};
```

---

## Rate Limiting

**Current:** None (development)
**Future:** 
- 100 requests/minute per IP
- 1000 requests/minute per authenticated user

---

## Data Types Reference

### Numeric Precision
- Prices: 5 decimal places (e.g., 2105.50000)
- Percentages: 2 decimal places (e.g., 65.50)
- Confidence: 2 decimal places (e.g., 0.83)

### Timeframe Strings
- Minute: M1, M5, M15, M30
- Hour: H1, H4
- Day: D1
- Week: W1
- Month: MN1

### Symbol Format
- Alphanumeric: A-Z, 0-9
- Length: 1-20 characters
- Case: Auto-converted to uppercase

---

## Performance Guidelines

**Acceptable Response Times:**
- Cache hit: 20-50ms
- Single timeframe: 500-2000ms
- Multi-timeframe (3x): 800-2500ms

**Timeout Settings:**
- Default: 30 seconds
- For multi-timeframe: 60 seconds recommended

---

## Versioning

**Current Version:** 1.0.0
**API Version Header:** Implicit (no version in URL)
**Breaking Changes:** Will increment major version

---

## Status Codes Summary

| Code | Event | Meaning |
|------|-------|---------|
| 200 | success: true | Operation successful |
| 400 | VALIDATION_ERROR | Invalid input |
| 500 | INTERNAL_ERROR | Server error |
| 503 | MT5_ERROR | Data fetch failure |

---

## Future Extensions

- Streaming updates via WebSocket messages
- Batch requests for multiple symbols
- Historical data requests
- Pattern recognition events
- Alert subscription system

