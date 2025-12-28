# Capital Companion Production Readiness Brainstorm

**Date**: 2025-12-28
**Context**: Monitor 1 - CAPITAL COMPANION
**Goal**: Transform prototype into production-ready Gold & Crypto trading companion
**Target**: 100-1000 users (Public beta scale)

---

## PROBLEM STATEMENT

Transform CAPITAL COMPANION from UI prototype with mock data into **trustworthy, helpful, easy-to-use voice trading companion** for Gold & Cryptocurrency markets.

### Current State
- ✅ UI/UX design complete (Monitor1.tsx, CapitalCompanionPanel.tsx)
- ✅ WebSocket infrastructure (SocketContext, Socket.IO client)
- ✅ Backend server planned (MT5 trading server architecture)
- ❌ Mock data only, no real market feeds
- ❌ No voice interaction (Whisper + VieNeu-TTS planned)
- ❌ No AI intelligence (pattern recognition, sentiment, learning)
- ❌ No trust mechanisms (confidence scores, explainability, warnings)

### Requirements Recap
- **Markets**: Gold (XAU/USD) + Cryptocurrency (BTC, ETH, major alts)
- **Voice**: Whisper OpenAI (STT) + VieNeu-TTS (TTS)
- **Backend**: Existing WebSocket server (Socket.IO)
- **AI Capabilities**: Pattern recognition, sentiment analysis, personalized learning, proactive alerts
- **Trust Model**: Confidence scores, explainability, risk warnings
- **Scale**: 100-1000 concurrent users (public beta)

---

## EVALUATED APPROACHES

### 1. Architecture Pattern: Monolith vs Microservices

#### Option A: Monolithic Backend (Recommended)
**Structure**: Single Node.js/Python server handles all responsibilities

**Pros**:
- Simpler deployment (one service)
- Lower operational overhead
- Easier debugging (single codebase)
- No inter-service latency
- Adequate for 100-1000 users

**Cons**:
- Harder to scale individual components
- All components share resources

**When it fails**: Need >5000 concurrent users or AI inference becomes CPU bottleneck

---

#### Option B: Microservices Architecture
**Structure**: Separate services (API Gateway, Market Data, AI Analysis, Voice Processing, User State)

**Pros**:
- Scale components independently
- Technology flexibility (Python AI, Node.js API)
- Fault isolation

**Cons**:
- Complex deployment (Docker Compose/Kubernetes)
- Network latency between services
- Distributed tracing needed
- Over-engineered for beta scale

**When it fails**: Team lacks DevOps expertise or deployment budget is limited

---

#### Option C: Hybrid - Serverless Functions + Persistent WebSocket (BEST)
**Structure**:
- Cloudflare Workers/AWS Lambda for stateless ops (market data fetch, AI analysis)
- Persistent Node.js server for WebSocket connections & voice streaming
- Redis/Upstash for shared state

**Pros**:
- Cost-efficient (pay-per-use for AI/data)
- Auto-scaling for spiky loads
- Simple WebSocket server (only handles realtime)
- Best of both worlds

**Cons**:
- Cold start latency on functions (mitigated by warm pools)
- Need state management layer (Redis)
- Slightly more complex than monolith

**Recommendation**: **Option C (Hybrid)** - Balances cost, scalability, and complexity for beta scale

---

### 2. Market Data Pipeline: Real-Time Architecture

#### Current Challenge
Mock data → Need Gold (XAU/USD) + Crypto (BTC, ETH, alts) with:
- Real-time price updates (< 1s latency)
- Historical data for pattern analysis
- High availability (99%+ uptime)
- Cost-effective for beta scale

---

#### Option A: Direct Exchange APIs
**Providers**: Binance WebSocket (crypto), OANDA/MT5 (gold)

**Data Flow**:
```
Binance WS → Backend → Redis Cache → WebSocket → Frontend
OANDA API → Backend → Redis Cache → WebSocket → Frontend
```

**Pros**:
- Free tier available
- Low latency (direct connection)
- Full control over data

**Cons**:
- Must handle multiple APIs
- Rate limits (need careful throttling)
- Requires fallback for downtime

**Cost**: $0 (free tier), but limited to 1-2 users testing

---

#### Option B: Aggregated Data Services (Recommended)
**Providers**: CoinGecko API (crypto), Alpha Vantage (gold), TwelveData (both)

**Data Flow**:
```
TwelveData WebSocket → Backend Aggregator → Redis → Clients
```

**Pros**:
- Unified API for both markets
- Higher rate limits
- Reliability guarantees
- Historical data included

**Cons**:
- Cost: ~$50-100/month for beta scale
- Slight latency vs direct exchange

**Cost**:
- TwelveData Pro: $79/mo (5000 req/min, WebSocket support)
- CoinGecko Pro: $129/mo (500 calls/min)

**Recommendation**: **TwelveData Pro** - Best cost/reliability balance

---

#### Option C: Hybrid - Free Tier + Premium Fallback
**Strategy**: Use free APIs (Binance, CoinGecko free tier), fall back to paid when rate-limited

**Pros**:
- Minimize costs during beta
- Graceful degradation

**Cons**:
- Complex error handling
- Inconsistent data quality

**When to use**: Bootstrapping with <$50/month budget

---

### 3. Voice Interaction: Whisper + VieNeu-TTS Integration

#### Architecture Options

#### Option A: Client-Side Processing
**Flow**: Browser MediaRecorder → Whisper API → Backend → VieNeu-TTS API → Browser Audio

**Pros**:
- Reduces backend load
- Lower latency (direct browser → API)

**Cons**:
- Exposes API keys (need proxy)
- User pays for bandwidth

---

#### Option B: Server-Side Proxy (Recommended)
**Flow**:
```
Browser → WebSocket (audio stream) → Backend → Whisper API → AI Processing
AI Response → VieNeu-TTS → WebSocket (audio stream) → Browser playback
```

**Pros**:
- API keys secured
- Centralized billing/monitoring
- Can cache common phrases (TTS)
- Integrates with AI logic

**Cons**:
- Backend bandwidth cost
- Need audio streaming infrastructure

**Implementation**:
1. **STT (Speech-to-Text)**:
   - Browser captures audio via `MediaRecorder` (WebM/Opus codec)
   - Stream chunks via WebSocket to backend
   - Backend batches chunks → Whisper API
   - Return transcription to frontend

2. **TTS (Text-to-Speech)**:
   - AI generates response text
   - Backend calls VieNeu-TTS API
   - Stream audio back via WebSocket
   - Browser plays via `Audio()` API

**Cost Estimate** (1000 users, avg 10 interactions/day):
- Whisper: $0.006/minute → ~$180/month (10k minutes)
- VieNeu-TTS: Pricing unknown (assume similar to ElevenLabs ~$0.30/1k chars) → ~$300/month

**Recommendation**: **Option B** - Required for API security and AI integration

---

### 4. AI Intelligence: Pattern Recognition + Sentiment + Learning

#### Core AI Capabilities Breakdown

#### 4.1 Pattern Recognition
**Requirement**: Detect support/resistance, chart patterns, trends

**Approach Options**:
- **Rule-Based (KISS)**: Technical indicators library (TA-Lib, pandas-ta)
  - Pros: Fast, predictable, no AI costs
  - Cons: Limited to predefined patterns
  - **Recommended for MVP**

- **ML-Based**: Train models on historical patterns (TensorFlow, Prophet)
  - Pros: Discovers novel patterns
  - Cons: Requires training data, inference costs, accuracy uncertainty
  - **Phase 2 enhancement**

**Implementation**:
```python
# Backend service
from pandas_ta import sma, rsi, bbands

def analyze_chart(symbol, timeframe):
    df = get_historical_data(symbol, timeframe)
    df['rsi'] = rsi(df['close'], length=14)
    df['sma_20'] = sma(df['close'], length=20)

    signals = {
        'trend': 'bullish' if df['close'].iloc[-1] > df['sma_20'].iloc[-1] else 'bearish',
        'rsi_condition': 'overbought' if df['rsi'].iloc[-1] > 70 else 'oversold' if df['rsi'].iloc[-1] < 30 else 'neutral',
        'confidence': calculate_confidence(df)  # Custom scoring
    }
    return signals
```

---

#### 4.2 Sentiment Analysis
**Requirement**: News monitoring, social media trends, market mood

**Data Sources**:
- **News**: NewsAPI, CryptoPanic, Benzinga
- **Social**: Twitter API (X Premium), Reddit (r/cryptocurrency, r/wallstreetbets)
- **On-Chain**: Glassnode (whale activity), LunarCrush (social metrics)

**Approach**:
1. **Keyword Extraction**: Track mentions of Gold/BTC in news/social
2. **Sentiment Scoring**: Use pre-trained models (VADER, FinBERT)
3. **Aggregation**: Weight by source credibility + recency

**Implementation**:
```javascript
// Serverless function (runs every 5 minutes)
export default async function analyzeSentiment() {
  const news = await fetchNews('BTC', lastHour);
  const tweets = await fetchTweets('#Bitcoin', lastHour);

  const sentimentScores = [
    ...news.map(n => nlp.analyze(n.title).sentiment),
    ...tweets.map(t => nlp.analyze(t.text).sentiment)
  ];

  const avgSentiment = sentimentScores.reduce((a,b) => a+b) / sentimentScores.length;

  return {
    sentiment: avgSentiment > 0.1 ? 'Greed' : avgSentiment < -0.1 ? 'Fear' : 'Neutral',
    confidence: calculateConfidence(sentimentScores),
    sources: sentimentScores.length
  };
}
```

**Cost**: NewsAPI Pro ($449/mo), Twitter API Premium ($5000/mo) → **Too expensive for beta**

**Alternative (Recommended)**:
- Free tier NewsAPI (100 req/day) + Reddit API (free)
- Run every 15 minutes instead of real-time
- Cost: $0

---

#### 4.3 Personalized Learning
**Requirement**: Learn user's risk tolerance, trading style, preferences

**Approach**:
- **User Profile Database**: Store user preferences (Firestore, Supabase)
- **Interaction Tracking**: Log all voice commands, trades, feedback
- **Adaptation Logic**: Adjust recommendations based on history

**Example**:
```typescript
interface UserProfile {
  userId: string;
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  preferredTimeframes: string[];  // ['H1', 'H4', 'D1']
  successfulPatterns: string[];   // Patterns user acted on profitably
  ignoredAlerts: string[];        // Alerts user dismissed
  averageHoldTime: number;        // In hours
}

function personalizeAlert(alert: Alert, profile: UserProfile): Alert {
  // Skip patterns user consistently ignores
  if (profile.ignoredAlerts.includes(alert.patternType)) {
    return null;
  }

  // Adjust language for risk tolerance
  if (profile.riskTolerance === 'conservative' && alert.risk > 0.5) {
    alert.message = `⚠️ HIGH RISK: ${alert.message}`;
  }

  return alert;
}
```

---

#### 4.4 Proactive Alerts
**Requirement**: Notify user without being asked

**Trigger Conditions**:
1. **Price Breakout**: Breaks key support/resistance
2. **Sentiment Shift**: Fear↔Greed index changes
3. **Volume Spike**: Unusual trading volume
4. **News Event**: Major announcement detected
5. **User Pattern Match**: Matches historical successful trade setup

**Implementation**:
```javascript
// Background job (runs every 30s)
async function checkAlertConditions(userId) {
  const user = await getUser(userId);
  const positions = await getUserPositions(userId);

  const alerts = [];

  // Check price breakouts
  for (const symbol of user.watchlist) {
    const breakout = await detectBreakout(symbol);
    if (breakout) {
      alerts.push({
        type: 'breakout',
        symbol,
        message: `${symbol} breaking ${breakout.level} resistance!`,
        confidence: breakout.strength,
        action: 'Consider entry'
      });
    }
  }

  // Check open position risks
  for (const pos of positions) {
    const risk = await calculateRisk(pos);
    if (risk.stopLossProximity < 0.02) {  // Within 2% of SL
      alerts.push({
        type: 'risk_warning',
        symbol: pos.symbol,
        message: `${pos.symbol} approaching stop loss`,
        confidence: 1.0,
        action: 'Review position'
      });
    }
  }

  return alerts;
}
```

---

### 5. Trust & Reliability Mechanisms

#### 5.1 Confidence Scores
**Implementation**: Every AI output includes confidence percentage

**Calculation Formula**:
```python
def calculate_confidence(analysis):
    factors = {
        'data_recency': 1.0 if data_age < 60s else 0.5,  # Fresh data = higher confidence
        'signal_strength': rsi_divergence_magnitude,      # Strong signal = higher
        'historical_accuracy': model_accuracy_on_similar, # Past performance
        'volatility_penalty': 1.0 - (current_volatility / avg_volatility)  # High vol = lower
    }

    confidence = (
        factors['data_recency'] * 0.3 +
        factors['signal_strength'] * 0.3 +
        factors['historical_accuracy'] * 0.2 +
        factors['volatility_penalty'] * 0.2
    )

    return min(max(confidence, 0.0), 1.0)  # Clamp 0-100%
```

**UI Display**:
```typescript
<Alert confidence={0.85}>
  <ConfidenceBadge>High Confidence: 85%</ConfidenceBadge>
  <AlertMessage>BTC bullish divergence on H4</AlertMessage>
</Alert>
```

---

#### 5.2 Explainability
**Requirement**: Show WHY Atlas recommends something

**Example Output**:
```
Atlas: I recommend taking profit on your Gold position.

Why?
✓ Target price reached ($2,100 - your TP level)
✓ RSI overbought on H4 timeframe (78.3)
✓ Bearish divergence forming (lower highs on price, higher highs on RSI)
✓ Your risk/reward achieved (2.5:1)

Data sources: OANDA (price), TradingView (indicators)
Confidence: 82% (high signal strength, fresh data)
```

**Implementation**:
```typescript
interface Recommendation {
  action: string;
  symbol: string;
  confidence: number;
  reasoning: {
    factors: Array<{
      indicator: string;
      value: number;
      threshold: number;
      sentiment: 'bullish' | 'bearish' | 'neutral';
    }>;
    dataSources: string[];
    timestamp: Date;
  };
}
```

---

#### 5.3 Risk Warnings
**Mandatory Warnings**:
1. **High Volatility**: "⚠️ Gold volatility 2x normal - expect wider spreads"
2. **Low Liquidity**: "⚠️ Low volume detected - slippage risk high"
3. **Conflicting Signals**: "⚠️ Mixed signals - H1 bullish, H4 bearish"
4. **Uncertainty**: "⚠️ Low confidence (45%) - wait for confirmation"
5. **News Risk**: "⚠️ FOMC announcement in 30min - high impact event"

**Implementation**:
```python
def check_risk_warnings(analysis):
    warnings = []

    if analysis['volatility'] > analysis['avg_volatility'] * 2:
        warnings.append({
            'severity': 'high',
            'type': 'volatility',
            'message': f"Volatility {analysis['volatility']:.1%} (2x normal)"
        })

    if analysis['confidence'] < 0.6:
        warnings.append({
            'severity': 'medium',
            'type': 'uncertainty',
            'message': f"Low confidence ({analysis['confidence']:.0%}) - wait for confirmation"
        })

    return warnings
```

---

### 6. Production Infrastructure

#### Database: User State & History

**Options**:
- **Supabase (Recommended)**: PostgreSQL + Realtime subscriptions + Auth
  - Pros: Built-in auth, real-time, generous free tier
  - Cons: Vendor lock-in
  - Cost: Free (up to 500MB), then $25/mo

- **Firebase/Firestore**: NoSQL, Google Cloud
  - Pros: Real-time, offline support, easy mobile integration
  - Cons: Expensive at scale, NoSQL limitations

- **Self-Hosted PostgreSQL**: Full control
  - Cons: Must manage backups, scaling, security

**Recommendation**: **Supabase** - Best DX and cost for beta

---

#### Caching Layer: Redis/Upstash

**Use Cases**:
- Market data cache (reduce API calls)
- User session state (WebSocket reconnection)
- Rate limiting (per-user API quotas)
- Voice TTS cache (common phrases)

**Providers**:
- **Upstash Redis**: Serverless, pay-per-request
  - Cost: Free tier (10k commands/day), then $0.2/100k
  - Recommended for serverless architecture

- **Redis Cloud**: Managed Redis
  - Cost: $5/mo (30MB free tier)

**Recommendation**: **Upstash** - Aligns with serverless functions

---

#### Monitoring & Observability

**Critical Metrics**:
- WebSocket connection count
- Voice processing latency (STT + TTS roundtrip)
- AI analysis latency (market data → recommendation)
- Error rates by type (API failures, TTS errors, data gaps)
- User engagement (alerts sent, voice interactions, trades)

**Tools**:
- **Sentry**: Error tracking ($26/mo for 50k errors)
- **Logtail**: Log aggregation (free tier 1GB/mo)
- **Uptime Robot**: Uptime monitoring (free)
- **Grafana Cloud**: Metrics dashboards (free tier)

**Recommendation**: Start with free tiers, add Sentry Pro when hitting limits

---

## RECOMMENDED SOLUTION (FINAL ARCHITECTURE)

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│  ┌────────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ CapitalCompanion   │  │  Market Panels  │  │ Voice UI     │ │
│  │ - Voice interaction│  │  - Price charts │  │ - Waveform   │ │
│  │ - Chat history     │  │  - Indicators   │  │ - Controls   │ │
│  └─────────┬──────────┘  └────────┬────────┘  └──────┬───────┘ │
└────────────┼────────────────────────┼──────────────────┼─────────┘
             │                        │                  │
             │     WebSocket (Socket.IO)                 │
             ▼                        ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│               BACKEND (Node.js + WebSocket Server)              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Socket.IO Server (Persistent Connections)               │  │
│  │  - Voice stream handling (Whisper + VieNeu-TTS)          │  │
│  │  - Real-time market data push                            │  │
│  │  - User session management                               │  │
│  └────────┬───────────────────────────┬────────────┬─────────┘  │
│           │                           │            │            │
│  ┌────────▼────────┐  ┌───────────────▼─────┐  ┌───▼────────┐  │
│  │ Voice Processor │  │ Market Data Manager │  │ AI Engine  │  │
│  │ - STT queue     │  │ - WebSocket clients │  │ - Patterns │  │
│  │ - TTS cache     │  │ - Data normalization│  │ - Alerts   │  │
│  └────────┬────────┘  └───────────────┬─────┘  └───┬────────┘  │
└───────────┼────────────────────────────┼────────────┼───────────┘
            │                            │            │
            │     ┌──────────────────────┼────────────┘
            │     │                      │
            ▼     ▼                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SERVERLESS FUNCTIONS                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │ Market Data    │  │ Sentiment      │  │ Alert Generator    │ │
│  │ Fetcher        │  │ Analyzer       │  │ (Cron: every 30s)  │ │
│  │ (TwelveData)   │  │ (NewsAPI)      │  │ - Pattern checks   │ │
│  └────────┬───────┘  └────────┬───────┘  └───────────┬────────┘ │
└───────────┼──────────────────────┼───────────────────────┼───────┘
            │                      │                       │
            ▼                      ▼                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ TwelveData    │  │ Whisper API │  │ VieNeu-TTS           │  │
│  │ (Market data) │  │ (OpenAI)    │  │ (Vietnamese TTS)     │  │
│  └───────────────┘  └─────────────┘  └──────────────────────┘  │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ NewsAPI       │  │ Supabase    │  │ Upstash Redis        │  │
│  │ (Sentiment)   │  │ (Database)  │  │ (Cache/State)        │  │
│  └───────────────┘  └─────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

### Technology Stack (Final)

**Frontend**:
- React + TypeScript
- Socket.IO Client
- MediaRecorder API (voice capture)
- Web Audio API (TTS playback)
- TradingView Lightweight Charts (price charts)

**Backend (Persistent Server)**:
- Node.js + Express + Socket.IO
- Audio streaming (WebSocket binary frames)
- Redis client (session state)

**Serverless Functions** (Cloudflare Workers / AWS Lambda):
- Market data fetcher (TypeScript)
- Sentiment analyzer (Python + VADER)
- Alert generator (TypeScript)
- Technical analysis (Python + pandas-ta)

**Database & State**:
- Supabase PostgreSQL (user profiles, trade history, alerts)
- Upstash Redis (market data cache, session state)

**External APIs**:
- TwelveData Pro ($79/mo) - Market data
- Whisper API ($0.006/min) - Speech-to-text
- VieNeu-TTS (pricing TBD) - Text-to-speech
- NewsAPI Free (100 req/day) - Sentiment data

---

### Data Models

#### User Profile (Supabase)
```sql
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT UNIQUE NOT NULL,
  risk_tolerance TEXT CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),
  preferred_timeframes TEXT[],  -- ['H1', 'H4', 'D1']
  watchlist TEXT[],             -- ['XAUUSD', 'BTCUSD', 'ETHUSD']
  voice_enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE alert_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id),
  alert_type TEXT,              -- 'breakout', 'pattern', 'sentiment', 'risk'
  symbol TEXT,
  message TEXT,
  confidence NUMERIC(3,2),      -- 0.00 - 1.00
  user_action TEXT,             -- 'acted', 'dismissed', 'ignored'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE voice_interactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES user_profiles(id),
  transcript TEXT,              -- User's spoken command
  response TEXT,                -- Atlas's response
  intent TEXT,                  -- 'query_price', 'analyze_chart', 'get_alerts'
  duration_ms INTEGER,          -- Processing time
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Market Data Cache (Redis)
```typescript
// Key pattern: market:{symbol}:{timeframe}
{
  "symbol": "XAUUSD",
  "timeframe": "H4",
  "price": 2105.50,
  "change_24h": 0.023,  // 2.3%
  "indicators": {
    "rsi": 65.2,
    "sma_20": 2098.30,
    "bb_upper": 2110.00,
    "bb_lower": 2095.00
  },
  "pattern": "bullish_divergence",
  "confidence": 0.78,
  "updated_at": 1735421400
}

// Key pattern: sentiment:{symbol}
{
  "symbol": "BTCUSD",
  "sentiment": "Greed",
  "score": 0.65,  // -1 to 1 scale
  "sources": 45,
  "top_keywords": ["rally", "breakout", "bullish"],
  "updated_at": 1735421400,
  "ttl": 900  // 15 minutes
}
```

---

### API Endpoints (Backend Server)

#### WebSocket Events (Socket.IO)

**Client → Server**:
```typescript
// Voice interaction
socket.emit('voice:start')  // Start listening
socket.emit('voice:audio', audioChunk)  // Stream audio
socket.emit('voice:stop')   // Stop, process transcription

// Market queries
socket.emit('market:subscribe', { symbols: ['XAUUSD', 'BTCUSD'] })
socket.emit('market:unsubscribe', { symbols: ['XAUUSD'] })

// Alert preferences
socket.emit('alerts:config', {
  types: ['breakout', 'pattern'],
  minConfidence: 0.7
})
```

**Server → Client**:
```typescript
// Voice responses
socket.on('voice:transcription', { text: "What's the price of gold?" })
socket.on('voice:audio', audioChunk)  // TTS audio stream
socket.on('voice:complete', { duration: 3500 })

// Market updates (real-time push)
socket.on('market:update', {
  symbol: 'XAUUSD',
  price: 2105.50,
  change: 0.023,
  timestamp: 1735421400
})

// Proactive alerts
socket.on('alert:new', {
  id: 'uuid',
  type: 'breakout',
  symbol: 'BTCUSD',
  message: 'BTC breaking $98,000 resistance!',
  confidence: 0.85,
  action: 'Consider entry',
  reasoning: {
    factors: [
      { indicator: 'price', value: 98150, threshold: 98000, sentiment: 'bullish' },
      { indicator: 'volume', value: 125000, threshold: 80000, sentiment: 'bullish' }
    ]
  }
})
```

---

### Implementation Phases

#### Phase 1: Market Data Pipeline (Week 1)
**Goal**: Replace mock data with real Gold/Crypto feeds

**Tasks**:
1. Setup TwelveData account + API keys
2. Create serverless function `market-data-fetcher`
   - Fetch XAUUSD, BTCUSD, ETHUSD every 5s
   - Store in Upstash Redis (5s TTL)
3. Backend WebSocket server subscribes to Redis
4. Push updates to connected clients
5. Update CapitalCompanionPanel to display real data

**Acceptance**:
- [ ] Frontend shows live Gold/BTC prices
- [ ] Updates every 5 seconds
- [ ] Latency < 1s from exchange to UI

---

#### Phase 2: Voice Interaction (Week 2)
**Goal**: Functional voice conversation with Atlas

**Tasks**:
1. Setup Whisper API + VieNeu-TTS accounts
2. Implement voice streaming in backend:
   - Receive audio chunks via WebSocket
   - Batch → Whisper API → transcription
3. Create intent classifier (simple keyword matching):
   - "price of gold" → query_price
   - "analyze bitcoin" → analyze_chart
4. Implement TTS response:
   - Generate text response
   - Call VieNeu-TTS → audio stream
   - Stream to client via WebSocket
5. UI: Add voice waveform visualization

**Acceptance**:
- [ ] User clicks "TALK", speaks "What's the price of gold?"
- [ ] Atlas responds with voice: "Gold is currently $2,105.50, up 2.3% today"
- [ ] Roundtrip latency < 3 seconds

---

#### Phase 3: AI Intelligence - Pattern Recognition (Week 3)
**Goal**: Atlas detects chart patterns and alerts user

**Tasks**:
1. Create serverless function `pattern-analyzer`:
   - Fetch historical data (TwelveData)
   - Calculate indicators (pandas-ta: RSI, SMA, MACD)
   - Detect patterns (bullish divergence, breakout, etc.)
2. Store analysis results in Redis
3. Backend generates alerts when patterns detected
4. Push alerts to frontend via WebSocket
5. Add confidence scores to all alerts

**Acceptance**:
- [ ] Atlas detects bullish divergence on BTC H4
- [ ] Alert shown in UI: "BTC bullish divergence on H4 (Confidence: 82%)"
- [ ] User clicks alert → shows reasoning (RSI divergence, price action)

---

#### Phase 4: Sentiment Analysis (Week 4)
**Goal**: Atlas tracks market mood and news

**Tasks**:
1. Create serverless function `sentiment-analyzer`:
   - Fetch news (NewsAPI free tier)
   - Analyze sentiment (VADER library)
   - Aggregate score
2. Run every 15 minutes (cron job)
3. Store in Redis
4. Atlas mentions sentiment in voice responses:
   - "BTC sentiment is Greed (65%) based on 45 news sources"

**Acceptance**:
- [ ] Sentiment updates every 15 minutes
- [ ] Atlas incorporates sentiment in recommendations
- [ ] UI shows sentiment indicator (Fear/Greed)

---

#### Phase 5: Personalized Learning (Week 5)
**Goal**: Atlas learns user preferences

**Tasks**:
1. Setup Supabase database
2. Track user interactions:
   - Which alerts acted on vs dismissed
   - Voice commands frequency
   - Preferred symbols/timeframes
3. Implement personalization logic:
   - Skip patterns user ignores
   - Prioritize user's successful patterns
   - Adjust language for risk tolerance
4. Show personalized dashboard

**Acceptance**:
- [ ] User dismisses 3 RSI alerts → Atlas stops sending RSI alerts
- [ ] User profitable on H4 breakouts → Atlas prioritizes H4 breakout alerts
- [ ] Atlas greets: "Morning! Your favorite Gold H4 setup is forming"

---

#### Phase 6: Proactive Alerts (Week 6)
**Goal**: Atlas notifies user of opportunities

**Tasks**:
1. Create serverless function `alert-generator` (runs every 30s):
   - Check user watchlist for patterns
   - Check open positions for risk warnings
   - Check sentiment shifts
2. Generate personalized alerts
3. Push via WebSocket + optional browser notification
4. Track alert accuracy (Phase 7 enhancement)

**Acceptance**:
- [ ] User has Gold on watchlist → Atlas alerts breakout
- [ ] User has open BTC position → Atlas warns approaching stop loss
- [ ] Sentiment shifts Fear→Greed → Atlas notifies

---

#### Phase 7: Trust Mechanisms (Week 7)
**Goal**: Build user trust through transparency

**Tasks**:
1. Add confidence scores to all AI outputs
2. Implement explainability:
   - Show reasoning for each recommendation
   - List data sources
   - Display indicator values
3. Add risk warnings:
   - High volatility warnings
   - Low confidence disclaimers
   - Conflicting signals alerts
4. Track historical accuracy (Phase 8)

**Acceptance**:
- [ ] Every alert shows confidence percentage
- [ ] User can tap "Why?" → sees reasoning with indicator values
- [ ] Atlas shows warning when confidence < 60%

---

#### Phase 8: Production Hardening (Week 8)
**Goal**: Ready for 100-1000 users

**Tasks**:
1. Add monitoring (Sentry, Logtail)
2. Implement rate limiting (per-user quotas)
3. Add error handling & retries
4. Setup auto-scaling (serverless already handles)
5. Create user onboarding flow
6. Add billing (if needed)
7. Security audit (API keys, SQL injection, XSS)
8. Load testing (simulate 1000 concurrent users)

**Acceptance**:
- [ ] 99% uptime over 7 days
- [ ] All errors tracked in Sentry
- [ ] 1000 concurrent WebSocket connections stable
- [ ] Voice latency p95 < 4 seconds

---

## IMPLEMENTATION CONSIDERATIONS

### Security Risks

**Risk 1: API Key Exposure**
- **Mitigation**: Never expose keys to frontend, use backend proxy

**Risk 2: Voice Data Privacy**
- **Mitigation**: Don't store raw audio, only transcriptions (encrypted at rest)

**Risk 3: SQL Injection / XSS**
- **Mitigation**: Use parameterized queries (Supabase client), sanitize inputs

**Risk 4: DDoS on WebSocket**
- **Mitigation**: Cloudflare WebSocket protection, rate limiting per IP

---

### Cost Analysis (Monthly, Public Beta Scale)

| Service | Usage | Cost |
|---------|-------|------|
| TwelveData Pro | 5000 req/min | $79 |
| Whisper API | 10k minutes (1000 users × 10 min/day) | $60 |
| VieNeu-TTS | 300k chars | ~$90 (estimated) |
| Supabase | 500MB DB | $0 (free tier) |
| Upstash Redis | 100M commands | $20 |
| Cloudflare Workers | 10M requests | $5 |
| Sentry | 50k errors | $26 |
| Hosting (Node.js) | 1 VPS (4GB RAM) | $20 (Hetzner) |
| **Total** | | **~$300/month** |

**Revenue Requirement**: $300 ÷ 1000 users = **$0.30/user/month** to break even

**Monetization Options**:
- Freemium: Free tier (5 alerts/day), Pro tier ($10/mo unlimited)
- Subscription only: $5-15/month (benchmark: TradingView $12.95/mo)

---

### Unresolved Questions

1. **VieNeu-TTS Pricing**: Need exact pricing model (per-character? per-request?)
   - **Action**: Contact VieNeu support for beta pricing

2. **Vietnamese Language Support**: Should Atlas speak Vietnamese or English?
   - **Decision needed**: Affects TTS selection (VieNeu-TTS supports Vietnamese natively)

3. **Real-Time vs Delayed Data**: TwelveData offers delayed data (free) vs real-time (paid)
   - **Recommendation**: Start with 5s delayed (acceptable for swing trading), upgrade if users demand tick data

4. **Alert Notification Channel**: WebSocket only or also push notifications?
   - **Recommendation**: Phase 1 = WebSocket only, Phase 2 = add browser push notifications (Web Push API)

5. **Multi-Device Sync**: Should user access Atlas from phone + desktop simultaneously?
   - **Complexity**: Need session management across devices
   - **Recommendation**: MVP = single device, Phase 3 = multi-device

---

## SUCCESS METRICS

### Functional Metrics
- ✅ Voice response latency p95 < 4 seconds
- ✅ Market data latency < 1 second
- ✅ Alert accuracy > 60% (tracked over 30 days)
- ✅ Confidence score calibration (70% confident alerts should be 70% accurate)

### User Engagement
- ✅ Daily active users > 30% of total users
- ✅ Average voice interactions > 5/day/user
- ✅ Alert action rate > 20% (user acts on 1 in 5 alerts)
- ✅ User retention day-30 > 40%

### Reliability
- ✅ Uptime > 99% (excludes planned maintenance)
- ✅ WebSocket reconnection success rate > 95%
- ✅ Zero data loss during reconnections

### Trust & Transparency
- ✅ All alerts include confidence scores
- ✅ All recommendations include reasoning
- ✅ Risk warnings shown on high-volatility periods
- ✅ User satisfaction (NPS) > 40

---

## NEXT STEPS

**Immediate Actions** (Before Implementation):
1. ✅ **Get VieNeu-TTS pricing** → Contact provider for beta access pricing
2. ✅ **Setup TwelveData account** → Confirm WebSocket support for XAUUSD + crypto
3. ✅ **Language decision** → Confirm if Atlas speaks Vietnamese or English
4. ⬜ **Design voice UX flow** → Wireframe conversation flows (happy path + error cases)
5. ⬜ **Create database schema** → Finalize Supabase table designs

**Ready to Proceed?**
Would you like me to create a detailed implementation plan using `/plan` slash command?

This will generate:
- Detailed task breakdown per phase
- File structure with code scaffolding
- API integration guides
- Testing strategy
- Deployment checklist

**Options**:
A. **Yes, create full implementation plan** (recommended)
B. **Clarify remaining questions first** (if unresolved questions block you)
C. **Start Phase 1 only** (market data pipeline, defer voice/AI)
