# Frontend Integration - Quick Start

Get up and running with Socket.IO integration in 5 minutes.

---

## 1. Environment Setup

Create `.env` in frontend root:

```bash
VITE_SOCKET_URL=http://localhost:8686
```

## 2. Start Backend

```bash
cd backend
python -m app.main
```

**Verify:** Visit `http://localhost:8686/health`

## 3. Start Frontend

```bash
npm run dev
```

**Verify:** Open browser to `http://localhost:5173`

---

## 4. Quick Usage Examples

### Trading Operations

```tsx
import { useTrading } from '@/hooks/useTrading';

function MyComponent() {
  const { buy, sell, login, isConnected } = useTrading();

  // Login
  const handleLogin = async () => {
    await login({
      account: 12345678,
      password: 'your_pass',
      server: 'Broker-Server'
    });
  };

  // Buy Order
  const handleBuy = async () => {
    const result = await buy({
      symbol: 'EURUSD',
      volume: 0.01,
      sl: 1.0950,
      tp: 1.1050
    });
    console.log('Ticket:', result.ticket);
  };

  return (
    <button onClick={handleBuy} disabled={!isConnected}>
      Place Buy Order
    </button>
  );
}
```

### AI Advisor

```tsx
import { useAdvisor } from '@/hooks/useAdvisor';

function MyComponent() {
  const { getTechnicalSummary, getRecommendation } = useAdvisor();

  // Technical Analysis
  const handleAnalysis = async () => {
    const result = await getTechnicalSummary({
      symbol: 'XAUUSD',
      timeframe: 'H1'
    });
    console.log('Signal:', result.overall.signal);
    console.log('RSI:', result.indicators.rsi);
  };

  // AI Recommendation
  const handleRecommendation = async () => {
    const result = await getRecommendation({
      symbol: 'XAUUSD',
      timeframe: 'H1',
      language: 'en'
    });
    console.log('Action:', result.recommendation.action);
    console.log('Confidence:', result.recommendation.confidence);
  };

  return (
    <>
      <button onClick={handleAnalysis}>Get Technical</button>
      <button onClick={handleRecommendation}>Get AI Rec</button>
    </>
  );
}
```

### Portfolio Analysis

```tsx
import { usePortfolioAnalysis } from '@/hooks/usePortfolioAnalysis';

function MyComponent() {
  const { analyzePortfolio } = usePortfolioAnalysis();

  const handleAnalyze = async () => {
    const result = await analyzePortfolio(
      [
        {
          symbol: 'XAUUSD',
          entry_price: 2630.50,
          position_size: 0.5,
          stop_loss: 2625.00,
          timeframe: 'H1'
        }
      ],
      10000,  // account balance
      'moderate',
      'en'
    );
    console.log('Health Score:', result.portfolio_health.score);
    console.log('Status:', result.portfolio_health.status);
  };

  return <button onClick={handleAnalyze}>Analyze Portfolio</button>;
}
```

---

## 5. View Examples

Import and use the example components:

```tsx
import { TradingExample } from '@/components/examples/TradingExample';
import { AdvisorExample } from '@/components/examples/AdvisorExample';

function Page() {
  return (
    <div>
      <TradingExample />
      <AdvisorExample />
    </div>
  );
}
```

---

## 6. Check Connection

```tsx
import { useSocket } from '@/context/SocketContext';

function ConnectionStatus() {
  const { isConnected, sessionId } = useSocket();

  return (
    <div>
      <p>Status: {isConnected ? '✅ Connected' : '❌ Disconnected'}</p>
      <p>Session: {sessionId}</p>
    </div>
  );
}
```

---

## Complete Hook Reference

### useTrading
- `login(credentials)` → AccountInfo
- `buy(order)` → OrderResult
- `sell(order)` → OrderResult
- `modify(request)` → ModifyResult
- `close(request)` → CloseResult

### useAdvisor
- `getTechnicalSummary(request)` → TechnicalResult
- `getMultiTimeframeAnalysis(request)` → MultiTimeframeResult
- `getPatternScan(request)` → PatternResult
- `getRiskAnalysis(request)` → RiskResult
- `getRecommendation(request)` → RecommendationResult

### usePortfolioAnalysis
- `analyzePortfolio(positions, balance, risk, lang)` → PortfolioResult

### useAccuracyTracking
- `recordOutcome(outcome)` → RecordResult
- `getAccuracyReport(filters)` → AccuracyReport
- `getExplainability(request)` → ExplainabilityResult

---

## Common Patterns

### Error Handling

```tsx
try {
  const result = await buy({ symbol: 'EURUSD', volume: 0.01 });
  // Success
} catch (err) {
  console.error('Failed:', err.message);
  alert('Operation failed');
}
```

### Loading States

```tsx
const { buy, loading } = useTrading();

<Button disabled={loading}>
  {loading ? 'Processing...' : 'Buy'}
</Button>
```

### Connection Check

```tsx
const { buy, isConnected } = useTrading();

if (!isConnected) {
  alert('Not connected to server');
  return;
}

await buy({ symbol: 'EURUSD', volume: 0.01 });
```

---

## Troubleshooting

**Connection Issues:**
```bash
# Check backend health
curl http://localhost:8686/health

# Check browser console for:
[SocketContext] Connecting to: http://localhost:8686
[SocketContext] Backend connected event: {...}
```

**Event Not Received:**
- Verify event name matches backend
- Check payload structure
- Look for errors in backend logs

**Type Errors:**
```tsx
import { type TechnicalSummaryResult } from '@/hooks/useAdvisor';
```

---

## Full Documentation

- **Complete Guide:** `FRONTEND_INTEGRATION_GUIDE.md`
- **Backend API:** `backend/SOCKETIO_API_GUIDE.md`
- **Implementation Status:** `FRONTEND_INTEGRATION_SUMMARY.md`

---

## Need Help?

1. Check browser console for `[SocketContext]` logs
2. Check backend logs: `DEBUG=true python -m app.main`
3. Visit health endpoint: `http://localhost:8686/health`
4. Review example components in `src/components/examples/`

---

**You're ready to build!** 🚀
