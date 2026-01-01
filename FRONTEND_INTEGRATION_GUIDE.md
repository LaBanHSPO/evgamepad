# Frontend Socket.IO Integration Guide

Complete guide for integrating the React frontend with the MT5 Trading & AI Advisor backend via Socket.IO.

---

## Table of Contents
1. [Overview](#overview)
2. [Setup & Configuration](#setup--configuration)
3. [Architecture](#architecture)
4. [Using the Hooks](#using-the-hooks)
5. [Example Components](#example-components)
6. [Testing Integration](#testing-integration)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What's Already Implemented ✅

**Backend (Ready to Use):**
- ✅ Socket.IO server on port 8686
- ✅ 14 events (5 trading + 9 advisor)
- ✅ Complete API with validation, caching, retry logic

**Frontend (Newly Implemented):**
- ✅ Socket.IO client installed (`socket.io-client@4.8.1`)
- ✅ SocketContext with session management
- ✅ 4 custom hooks for all backend features
- ✅ TypeScript types for all events
- ✅ Example components for trading & advisor

### File Structure

```
src/
├── context/
│   └── SocketContext.tsx          # Socket.IO connection management
├── hooks/
│   ├── useTrading.ts              # Trading operations hook
│   ├── useAdvisor.ts              # AI advisor features hook
│   ├── usePortfolioAnalysis.ts    # Portfolio analysis hook
│   └── useAccuracyTracking.ts     # Accuracy tracking & explainability
└── components/
    └── examples/
        ├── TradingExample.tsx     # Trading UI example
        └── AdvisorExample.tsx     # Advisor UI example
```

---

## Setup & Configuration

### 1. Environment Variables

Create `.env` file in frontend root:

```bash
# Socket.IO Backend URL (default: http://localhost:8686)
VITE_SOCKET_URL=http://localhost:8686
```

### 2. App Wrapper

The app is already wrapped with `SocketProvider` in `App.tsx`:

```tsx
import { SocketProvider } from '@/context/SocketContext';

const App = () => (
  <QueryClientProvider client={queryClient}>
    <SocketProvider>
      {/* Your app routes */}
    </SocketProvider>
  </QueryClientProvider>
);
```

### 3. Start the Backend

```bash
cd backend
python -m app.main
# Or: uvicorn app.main:asgi_app --host 0.0.0.0 --port 8686
```

Backend should be running on `http://localhost:8686`

### 4. Start the Frontend

```bash
npm run dev
```

Frontend will run on `http://localhost:5173` (Vite default)

---

## Architecture

### Connection Flow

```
Frontend (React)
    ↓
SocketContext (Manages connection)
    ↓
Socket.IO Client (socket.io-client)
    ↓ WebSocket
Backend (FastAPI + Socket.IO AsyncServer)
    ↓
Event Handlers (trading_events.py, advisor_events.py)
    ↓
Processors (command_processor.py, advisor_processor.py)
    ↓
MT5 Operations / AI Analysis
```

### State Management

**SocketContext provides:**
- `socket`: Socket.IO instance
- `isConnected`: Connection status
- `lastError`: Last error message
- `sessionId`: Backend session ID
- `sessionRecovered`: True if reconnected within 5 min

**Custom hooks manage:**
- Event emission
- Response handling
- Loading states
- Error handling
- Promise-based API

---

## Using the Hooks

### 1. Trading Operations (`useTrading`)

#### Import & Initialize

```tsx
import { useTrading } from '@/hooks/useTrading';

function TradingComponent() {
  const {
    isConnected,
    isLoggedIn,
    accountInfo,
    loading,
    error,
    login,
    buy,
    sell,
    modify,
    close,
    clearError,
  } = useTrading();
}
```

#### Login to MT5

```tsx
const handleLogin = async () => {
  try {
    const accountInfo = await login({
      account: 12345678,
      password: 'your_password',
      server: 'Broker-Server'
    });

    console.log('Logged in:', accountInfo);
    // {
    //   login: 12345678,
    //   name: "Account Name",
    //   balance: 10000.00,
    //   equity: 10050.50,
    //   leverage: 100,
    //   ...
    // }
  } catch (err) {
    console.error('Login failed:', err.message);
  }
};
```

#### Place Buy Order

```tsx
const handleBuy = async () => {
  try {
    const result = await buy({
      symbol: 'EURUSD',
      volume: 0.01,
      sl: 1.0950,  // Optional
      tp: 1.1050   // Optional
    });

    console.log('Order placed:', result);
    // {
    //   ticket: 123456789,
    //   price: 1.1000,
    //   volume: 0.01,
    //   timestamp: "2025-12-31T10:00:00Z"
    // }
  } catch (err) {
    console.error('Buy failed:', err.message);
  }
};
```

#### Place Sell Order

```tsx
const handleSell = async () => {
  try {
    const result = await sell({
      symbol: 'XAUUSD',
      volume: 0.5,
      sl: 2650.00,
      tp: 2600.00
    });

    console.log('Sell order:', result);
  } catch (err) {
    console.error('Sell failed:', err.message);
  }
};
```

#### Modify Position

```tsx
const handleModify = async () => {
  try {
    const result = await modify({
      ticket: 123456789,
      sl: 1.0960,  // New stop loss
      tp: 1.1040   // New take profit
    });

    console.log('Position modified:', result);
  } catch (err) {
    console.error('Modify failed:', err.message);
  }
};
```

#### Close Position

```tsx
const handleClose = async () => {
  try {
    const result = await close({
      ticket: 123456789,
      volume: 0.01  // Optional for partial close
    });

    console.log('Position closed:', result);
    // {
    //   close_price: 1.1025,
    //   profit: 25.00,
    //   volume_closed: 0.01
    // }
  } catch (err) {
    console.error('Close failed:', err.message);
  }
};
```

---

### 2. AI Advisor (`useAdvisor`)

#### Import & Initialize

```tsx
import { useAdvisor } from '@/hooks/useAdvisor';

function AdvisorComponent() {
  const {
    isConnected,
    loading,
    error,
    getTechnicalSummary,
    getMultiTimeframeAnalysis,
    getPatternScan,
    getRiskAnalysis,
    getRecommendation,
    clearError,
  } = useAdvisor();
}
```

#### Technical Analysis

```tsx
const handleTechnical = async () => {
  try {
    const result = await getTechnicalSummary({
      symbol: 'XAUUSD',
      timeframe: 'H1',
      indicators: ['sma', 'rsi', 'macd']  // Optional
    });

    console.log('Technical:', result);
    // {
    //   last_close: 2634.50,
    //   indicators: { rsi: 65.5, sma_20: 2630.25, ... },
    //   signals: { sma: "bullish", rsi: "neutral", ... },
    //   overall: { signal: "bullish", confidence: 75 },
    //   cached: false
    // }
  } catch (err) {
    console.error('Technical failed:', err.message);
  }
};
```

#### Multi-Timeframe Analysis

```tsx
const handleMultiTF = async () => {
  try {
    const result = await getMultiTimeframeAnalysis({
      symbol: 'XAUUSD',
      timeframes: ['H1', 'H4', 'D1']
    });

    console.log('Multi-TF:', result);
    // {
    //   alignment: {
    //     status: "strong_bullish",
    //     bullish_count: 3,
    //     bearish_count: 0,
    //     signals: [...]
    //   },
    //   power_zone: true
    // }
  } catch (err) {
    console.error('Multi-TF failed:', err.message);
  }
};
```

#### Pattern Scan

```tsx
const handlePatterns = async () => {
  try {
    const result = await getPatternScan({
      symbol: 'XAUUSD',
      timeframe: 'H1',
      include_sr: true
    });

    console.log('Patterns:', result);
    // {
    //   candlestick_patterns: [{ name: "Bullish Engulfing", ... }],
    //   chart_patterns: [{ name: "Double Bottom", ... }],
    //   support_resistance: {
    //     nearest_support: 2625.00,
    //     nearest_resistance: 2640.00,
    //     pivot: 2630.00
    //   }
    // }
  } catch (err) {
    console.error('Patterns failed:', err.message);
  }
};
```

#### Risk Analysis

```tsx
const handleRisk = async () => {
  try {
    const result = await getRiskAnalysis({
      symbol: 'XAUUSD',
      account_balance: 10000,
      entry_price: 2634.50,
      stop_loss: 2625.00,
      take_profit: 2645.00,
      risk_profile: 'moderate',  // conservative, moderate, aggressive
      timeframe: 'H1'
    });

    console.log('Risk:', result);
    // {
    //   risk_reward: { ratio: 1.11, recommendation: "acceptable" },
    //   position_sizing: { recommended_volume: 0.03 }
    // }
  } catch (err) {
    console.error('Risk failed:', err.message);
  }
};
```

#### AI Recommendation (LLM-Powered)

```tsx
const handleRecommendation = async () => {
  try {
    const result = await getRecommendation({
      symbol: 'XAUUSD',
      timeframe: 'H1',
      language: 'en',  // or 'vi'
      risk_profile: 'moderate'
    });

    console.log('AI Recommendation:', result);
    // {
    //   recommendation: {
    //     action: "BUY",
    //     confidence: 85,
    //     entry_zone: [2630, 2635],
    //     stop_loss: 2625,
    //     take_profit: [2645, 2650],
    //     reasoning: "..."
    //   },
    //   ai_summary: {
    //     market_context: "...",
    //     key_factors: [...],
    //     risks: [...]
    //   }
    // }
  } catch (err) {
    console.error('Recommendation failed:', err.message);
  }
};
```

---

### 3. Portfolio Analysis (`usePortfolioAnalysis`)

#### Import & Initialize

```tsx
import { usePortfolioAnalysis, type Position } from '@/hooks/usePortfolioAnalysis';

function PortfolioComponent() {
  const {
    result,
    isAnalyzing,
    error,
    analyzePortfolio,
    clearResult,
    clearError,
    isConnected
  } = usePortfolioAnalysis();
}
```

#### Analyze Portfolio

```tsx
const handlePortfolio = async () => {
  const positions: Position[] = [
    {
      symbol: 'XAUUSD',
      entry_price: 2630.50,
      current_price: 2634.00,  // Optional (fetched if not provided)
      position_size: 0.5,
      stop_loss: 2625.00,
      timeframe: 'H1'
    },
    {
      symbol: 'EURUSD',
      entry_price: 1.1000,
      position_size: 0.1,
      stop_loss: 1.0950,
      timeframe: 'H1'
    }
  ];

  try {
    const result = await analyzePortfolio(
      positions,
      10000,        // account balance
      'moderate',   // risk profile
      'en'          // language
    );

    console.log('Portfolio:', result);
    // {
    //   portfolio_health: {
    //     score: 75,
    //     status: "HEALTHY",
    //     total_risk_exposure: 5.5,
    //     positions_at_risk: 0
    //   },
    //   position_analysis: [...],
    //   ai_advice: {
    //     overall_assessment: "...",
    //     capital_preservation_tips: [...],
    //     risk_warnings: [...]
    //   }
    // }
  } catch (err) {
    console.error('Portfolio failed:', err.message);
  }
};
```

---

### 4. Accuracy Tracking (`useAccuracyTracking`)

#### Import & Initialize

```tsx
import { useAccuracyTracking } from '@/hooks/useAccuracyTracking';

function TrackingComponent() {
  const {
    isConnected,
    loading,
    error,
    recordOutcome,
    getAccuracyReport,
    getExplainability,
    clearError
  } = useAccuracyTracking();
}
```

#### Record Trade Outcome

```tsx
const handleRecordOutcome = async () => {
  try {
    const result = await recordOutcome({
      symbol: 'XAUUSD',
      timeframe: 'H1',
      signal: 'BUY',
      confidence: 85,
      entry_price: 2634.50,
      exit_price: 2640.20,
      stop_loss: 2625.50,
      take_profit: 2645.00,
      exit_reason: 'take_profit',
      entry_at: '2025-12-30T10:00:00Z',
      exit_at: '2025-12-30T14:30:00Z'
    });

    console.log('Outcome recorded:', result.outcome_id);
  } catch (err) {
    console.error('Record failed:', err.message);
  }
};
```

#### Get Accuracy Report

```tsx
const handleReport = async () => {
  try {
    const result = await getAccuracyReport({
      symbol: 'XAUUSD',  // Optional filter
      timeframe: 'H1',   // Optional filter
      signal: 'BUY',     // Optional filter
      days: 30           // Default 30
    });

    console.log('Accuracy report:', result);
    // {
    //   report: {
    //     total_trades: 50,
    //     wins: 35,
    //     losses: 15,
    //     win_rate_pct: 70.0,
    //     profit_factor: 2.33
    //   },
    //   best_performing: [...]
    // }
  } catch (err) {
    console.error('Report failed:', err.message);
  }
};
```

#### Get Explainability (Chain-of-Thought)

```tsx
const handleExplain = async () => {
  try {
    const result = await getExplainability({
      symbol: 'XAUUSD',
      timeframe: 'H1'
    });

    console.log('Explainability:', result);
    // {
    //   explainability: {
    //     steps: [
    //       { step: 1, name: "Trend Analysis", score: 2, max_score: 2, ... }
    //     ],
    //     total_score: 10,
    //     max_score: 12,
    //     confidence: 0.83,
    //     reasoning_summary: "..."
    //   }
    // }
  } catch (err) {
    console.error('Explain failed:', err.message);
  }
};
```

---

## Example Components

### Trading Example

Full example at: `src/components/examples/TradingExample.tsx`

**Features:**
- Login form with MT5 credentials
- Buy/Sell order form with SL/TP
- Modify position form
- Close position form
- Account info display
- Error handling

**Usage:**

```tsx
import { TradingExample } from '@/components/examples/TradingExample';

function Page() {
  return <TradingExample />;
}
```

### Advisor Example

Full example at: `src/components/examples/AdvisorExample.tsx`

**Features:**
- Technical analysis with results display
- Multi-timeframe analysis
- Pattern scan with S/R levels
- Risk analysis calculator
- AI recommendation with full details
- Portfolio analysis UI
- Tabbed interface for different features

**Usage:**

```tsx
import { AdvisorExample } from '@/components/examples/AdvisorExample';

function Page() {
  return <AdvisorExample />;
}
```

---

## Testing Integration

### 1. Check Backend Health

```bash
curl http://localhost:8686/health
```

Expected response:
```json
{
  "status": "healthy",
  "mt5_connected": true,
  "redis_connected": true,
  "db_connected": false,
  "accuracy_tracking_enabled": false,
  "connected_clients": 1
}
```

### 2. Test Frontend Connection

Add to any component:

```tsx
import { useSocket } from '@/context/SocketContext';

function TestComponent() {
  const { isConnected, sessionId, sessionRecovered } = useSocket();

  return (
    <div>
      <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
      <p>Session ID: {sessionId}</p>
      <p>Recovered: {sessionRecovered ? 'Yes' : 'No'}</p>
    </div>
  );
}
```

### 3. Monitor Console Logs

Open browser DevTools > Console. You should see:

```
[SocketContext] Connecting to: http://localhost:8686
[SocketContext] Socket.IO connected
[SocketContext] Backend connected event: { session_id: "...", ... }
```

### 4. Test Trading Operation

```tsx
const { buy } = useTrading();

const test = async () => {
  try {
    const result = await buy({
      symbol: 'EURUSD',
      volume: 0.01
    });
    console.log('Success:', result);
  } catch (err) {
    console.error('Failed:', err);
  }
};
```

### 5. Test Advisor Operation

```tsx
const { getTechnicalSummary } = useAdvisor();

const test = async () => {
  try {
    const result = await getTechnicalSummary({
      symbol: 'XAUUSD',
      timeframe: 'H1'
    });
    console.log('Technical:', result);
  } catch (err) {
    console.error('Failed:', err);
  }
};
```

---

## Troubleshooting

### Connection Issues

**Problem:** `Socket not connected` error

**Solutions:**
1. Check backend is running: `curl http://localhost:8686/health`
2. Check VITE_SOCKET_URL in `.env`
3. Check browser console for CORS errors
4. Verify WebSocket support in browser

**Problem:** Connection keeps reconnecting

**Solutions:**
1. Check backend logs for errors
2. Verify MT5 terminal is running
3. Check network firewall settings

### Event Not Received

**Problem:** Event emitted but no response

**Solutions:**
1. Check event name matches backend (e.g., `advisor_technical_summary` not `advisor:technical_summary`)
2. Verify payload structure matches backend expectations
3. Check backend logs for validation errors
4. Ensure event listeners are registered before emitting

### Type Errors

**Problem:** TypeScript errors with hook return types

**Solutions:**
1. Import types from hooks: `import { type TechnicalSummaryResult } from '@/hooks/useAdvisor'`
2. Use `any` temporarily for debugging: `const result: any = await getTechnicalSummary(...)`
3. Check hook file for exported types

### Performance Issues

**Problem:** Slow responses or timeouts

**Solutions:**
1. Check Redis caching is enabled
2. Use cached results when available (check `result.cached` field)
3. Reduce concurrent requests
4. Check network latency

### LLM Errors

**Problem:** AI features not working

**Solutions:**
1. Verify `ANTHROPIC_API_KEY` or `DEEPSEEK_API_KEY` in backend `.env`
2. Check API rate limits
3. Verify `DEFAULT_LLM_MODEL` setting
4. Check backend logs for API errors

### Database Errors

**Problem:** Accuracy tracking not working

**Solutions:**
1. Verify PostgreSQL is running
2. Check `ENABLE_ACCURACY_TRACKING=true` in backend `.env`
3. Verify database credentials in backend `.env`
4. Check database connection in health endpoint

---

## Best Practices

### 1. Error Handling

Always wrap hook calls in try-catch:

```tsx
try {
  const result = await buy({ symbol: 'EURUSD', volume: 0.01 });
  // Handle success
} catch (err) {
  console.error('Operation failed:', err);
  // Show user-friendly error message
}
```

### 2. Loading States

Use the `loading` state from hooks:

```tsx
const { buy, loading } = useTrading();

return (
  <Button onClick={handleBuy} disabled={loading}>
    {loading ? 'Processing...' : 'Buy'}
  </Button>
);
```

### 3. Connection Checking

Always check connection before operations:

```tsx
const { isConnected, buy } = useTrading();

const handleBuy = async () => {
  if (!isConnected) {
    alert('Not connected to server');
    return;
  }

  await buy({ symbol: 'EURUSD', volume: 0.01 });
};
```

### 4. Cleanup

Clear results and errors when appropriate:

```tsx
const { result, clearResult } = usePortfolioAnalysis();

useEffect(() => {
  return () => {
    clearResult();  // Cleanup on unmount
  };
}, [clearResult]);
```

### 5. Promise vs Callback

All hooks return Promises for modern async/await syntax:

```tsx
// Good ✅
const result = await buy({ symbol: 'EURUSD', volume: 0.01 });

// Avoid ❌
buy({ symbol: 'EURUSD', volume: 0.01 }).then(result => {
  // callback style
});
```

---

## Summary

**What You Have:**
- ✅ Complete Socket.IO integration
- ✅ 4 custom React hooks covering all backend features
- ✅ TypeScript types for all events
- ✅ Example components for reference
- ✅ Promise-based API
- ✅ Error handling and loading states
- ✅ Session management and reconnection

**Next Steps:**
1. Integrate hooks into your existing components
2. Add UI elements for trading and advisor features
3. Test thoroughly with real MT5 account (demo account recommended)
4. Monitor console logs for debugging
5. Implement error notifications (toast/alert)

**Resources:**
- Backend API Documentation: `backend/SOCKETIO_API_GUIDE.md`
- Backend Implementation Status: `backend/BACKEND_IMPLEMENTATION_STATUS.md`
- Socket.IO Quick Reference: `backend/SOCKETIO_QUICK_REFERENCE.md`

For questions or issues, check backend logs with `DEBUG=true` enabled.
