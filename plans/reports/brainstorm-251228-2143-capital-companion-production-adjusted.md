# Capital Companion Production Readiness Brainstorm (Adjusted)

**Date**: 2025-12-28 (Updated: 21:43)
**Context**: Monitor 1 - CAPITAL COMPANION
**Goal**: Transform prototype into production-ready Gold & Crypto trading companion
**Target**: 100-1000 users (Public beta scale)
**Architecture**: Self-hosted Monolith (No serverless/third-party services)

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

### Confirmed Requirements
- **Markets**: Gold (XAU/USD) + Cryptocurrency (BTC, ETH, major alts)
- **Voice**: Whisper OpenAI (STT) + VieNeu-TTS on own server (Vietnamese)
- **Backend**: Monolithic Node.js server with Socket.IO
- **Data Source**: TwelveData WebSocket (5s delay acceptable)
- **Infrastructure**: Self-hosted PostgreSQL + Redis (no cloud services)
- **AI Capabilities**: Pattern recognition, sentiment analysis, personalized learning, proactive alerts
- **Trust Model**: Confidence scores, explainability, risk warnings
- **Scale**: 100-1000 concurrent users (public beta)
- **Monitoring**: Free tier tools only

---

## CHOSEN ARCHITECTURE

### Monolithic Backend (Node.js)

**Selected**: **Option A - Monolithic Backend**

**Structure**: Single Node.js application handles all responsibilities:
- WebSocket connections (Socket.IO)
- Market data ingestion (TwelveData WebSocket client)
- Voice processing (Whisper API + VieNeu-TTS server proxy)
- AI analysis (pattern recognition, sentiment)
- Alert generation
- User session management
- Database operations (PostgreSQL)
- Cache operations (Redis)

**Why Monolith?**
- ✅ Simpler deployment (single service, single Docker container)
- ✅ Lower operational overhead (no service mesh, no inter-process communication)
- ✅ Easier debugging (single codebase, unified logging)
- ✅ No inter-service latency (all in-memory)
- ✅ Adequate for 100-1000 concurrent users
- ✅ Full control over infrastructure (self-hosted)
- ✅ No vendor lock-in

**Trade-offs Accepted**:
- ❌ Harder to scale individual components independently
- ❌ All components share CPU/memory resources
- ❌ AI inference may block WebSocket handling (mitigated by worker threads)

**Scaling Strategy** (when needed):
- Vertical scaling: Upgrade server specs (4GB → 8GB → 16GB RAM)
- Horizontal scaling: Add load balancer + multiple monolith instances + shared Redis
- At >5000 users: Consider splitting AI analysis to separate service

---

## MARKET DATA PIPELINE

### TwelveData WebSocket Integration

**Selected**: **TwelveData Pro with WebSocket**

**Data Flow**:
```
TwelveData WebSocket → Monolith Backend → Redis Cache → Socket.IO → Frontend
```

**Implementation**:
```javascript
// backend/services/market-data-service.js
const WebSocket = require('ws');
const redis = require('./redis-client');

class MarketDataService {
  constructor() {
    this.ws = null;
    this.symbols = ['XAUUSD', 'BTCUSD', 'ETHUSD', 'BNBUSD'];
  }

  connect() {
    const wsUrl = `wss://ws.twelvedata.com/v1/quotes/price?apikey=${process.env.TWELVEDATA_KEY}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.on('open', () => {
      console.log('TwelveData WebSocket connected');
      // Subscribe to symbols
      this.ws.send(JSON.stringify({
        action: 'subscribe',
        params: {
          symbols: this.symbols.join(',')
        }
      }));
    });

    this.ws.on('message', async (data) => {
      const update = JSON.parse(data);

      // Cache in Redis (5s TTL)
      await redis.setex(
        `market:${update.symbol}`,
        5,
        JSON.stringify({
          symbol: update.symbol,
          price: update.price,
          timestamp: Date.now()
        })
      );

      // Broadcast to all connected clients
      global.io.emit('market:update', {
        symbol: update.symbol,
        price: update.price,
        timestamp: Date.now()
      });
    });

    this.ws.on('error', (err) => {
      console.error('TwelveData WebSocket error:', err);
    });

    this.ws.on('close', () => {
      console.warn('TwelveData WebSocket closed, reconnecting in 5s...');
      setTimeout(() => this.connect(), 5000);
    });
  }
}

module.exports = new MarketDataService();
```

**Features**:
- Real-time price updates (5s delay acceptable)
- Automatic reconnection on disconnect
- Redis caching (reduce client polling)
- Broadcast to all Socket.IO clients

**Cost**: $79/month (TwelveData Pro plan)

---

## VOICE INTERACTION ARCHITECTURE

### Server-Side Proxy (Chosen)

**Flow**:
```
Browser MediaRecorder → WebSocket (audio stream) → Backend → Whisper API
Whisper transcription → AI Processing → Response text
Response text → VieNeu-TTS Server → Audio stream → WebSocket → Browser
```

**Implementation**:

#### 1. Speech-to-Text (Whisper API)
```javascript
// backend/services/voice-service.js
const FormData = require('form-data');
const axios = require('axios');

class VoiceService {
  async transcribe(audioBuffer) {
    const formData = new FormData();
    formData.append('file', audioBuffer, {
      filename: 'audio.webm',
      contentType: 'audio/webm'
    });
    formData.append('model', 'whisper-1');
    formData.append('language', 'vi'); // Vietnamese

    const response = await axios.post(
      'https://api.openai.com/v1/audio/transcriptions',
      formData,
      {
        headers: {
          'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
          ...formData.getHeaders()
        }
      }
    );

    return response.data.text;
  }

  async synthesize(text) {
    // Call your VieNeu-TTS server
    const response = await axios.post(
      process.env.VIENEU_TTS_URL,
      { text, voice: 'vi-VN-female' },
      { responseType: 'arraybuffer' }
    );

    return response.data; // Audio buffer
  }
}

module.exports = new VoiceService();
```

#### 2. WebSocket Handler
```javascript
// backend/socket-handlers/voice-handler.js
const voiceService = require('../services/voice-service');

module.exports = (socket) => {
  let audioChunks = [];

  socket.on('voice:start', () => {
    audioChunks = [];
    socket.emit('voice:listening');
  });

  socket.on('voice:audio', (chunk) => {
    audioChunks.push(chunk);
  });

  socket.on('voice:stop', async () => {
    try {
      // Concatenate audio chunks
      const audioBuffer = Buffer.concat(audioChunks);

      // Transcribe via Whisper
      const transcription = await voiceService.transcribe(audioBuffer);
      socket.emit('voice:transcription', { text: transcription });

      // Process intent (AI logic)
      const response = await processIntent(transcription, socket.userId);

      // Synthesize response via VieNeu-TTS
      const audioResponse = await voiceService.synthesize(response.text);

      // Stream audio back to client
      socket.emit('voice:audio', audioResponse);
      socket.emit('voice:complete');

    } catch (err) {
      console.error('Voice processing error:', err);
      socket.emit('voice:error', { message: 'Xin lỗi, tôi không hiểu' });
    }
  });
};
```

**Why Server-Side?**
- ✅ API keys secured (not exposed to frontend)
- ✅ Centralized billing/monitoring
- ✅ Can cache common TTS phrases (reduce API costs)
- ✅ Integrates with AI logic seamlessly

**Cost**:
- Whisper: $0.006/minute
- VieNeu-TTS: $0 (own server)

---

## PRODUCTION INFRASTRUCTURE (SELF-HOSTED)

### Server Specifications

**Recommended VPS**:
- **Provider**: Hetzner, DigitalOcean, Vultr, or Contabo
- **Specs**: 4 vCPU, 8GB RAM, 160GB SSD
- **Cost**: ~$20-40/month
- **Location**: Singapore (low latency to Vietnam)

**Why 8GB RAM?**
- Node.js monolith: ~1-2GB
- PostgreSQL: ~2GB
- Redis: ~1GB
- TwelveData WebSocket connections: ~500MB
- OS + buffers: ~1.5GB
- Headroom for spikes: ~2GB

---

### Database: Self-Hosted PostgreSQL

**Setup**:
```bash
# Install PostgreSQL 16
sudo apt install postgresql-16 postgresql-contrib

# Create database
sudo -u postgres createdb capital_companion
sudo -u postgres createuser capital_user -P

# Grant permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE capital_companion TO capital_user;"
```

**Schema**:
```sql
-- User profiles
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT UNIQUE NOT NULL,
  risk_tolerance TEXT CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),
  preferred_timeframes TEXT[],
  watchlist TEXT[],
  voice_enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alert history
CREATE TABLE alert_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id),
  alert_type TEXT,
  symbol TEXT,
  message TEXT,
  confidence NUMERIC(3,2),
  user_action TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Voice interactions
CREATE TABLE voice_interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id),
  transcript TEXT,
  response TEXT,
  intent TEXT,
  duration_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_alert_history_user_id ON alert_history(user_id);
CREATE INDEX idx_alert_history_created_at ON alert_history(created_at DESC);
CREATE INDEX idx_voice_interactions_user_id ON voice_interactions(user_id);
```

**Backup Strategy**:
```bash
# Daily backup cron job (3 AM)
0 3 * * * pg_dump capital_companion | gzip > /backup/capital_companion_$(date +\%Y\%m\%d).sql.gz

# Retention: Keep 7 days
find /backup -name "capital_companion_*.sql.gz" -mtime +7 -delete
```

**Connection Pooling** (via pg-pool):
```javascript
// backend/db/pool.js
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'capital_companion',
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 20, // Max connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

module.exports = pool;
```

**Cost**: $0 (included in VPS)

---

### Caching: Self-Hosted Redis

**Setup**:
```bash
# Install Redis 7
sudo apt install redis-server

# Configure for production
sudo vim /etc/redis/redis.conf
# Set: maxmemory 1gb
# Set: maxmemory-policy allkeys-lru
# Set: save "" (disable persistence for cache-only usage)

# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

**Use Cases**:
```javascript
// backend/services/redis-client.js
const redis = require('redis');

const client = redis.createClient({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379
});

client.on('error', (err) => console.error('Redis error:', err));
client.connect();

module.exports = {
  // Market data cache
  async cacheMarketData(symbol, data, ttl = 5) {
    await client.setEx(`market:${symbol}`, ttl, JSON.stringify(data));
  },

  async getMarketData(symbol) {
    const data = await client.get(`market:${symbol}`);
    return data ? JSON.parse(data) : null;
  },

  // Sentiment cache
  async cacheSentiment(symbol, sentiment, ttl = 900) {
    await client.setEx(`sentiment:${symbol}`, ttl, JSON.stringify(sentiment));
  },

  // Rate limiting
  async checkRateLimit(userId, limit = 100, window = 60) {
    const key = `ratelimit:${userId}`;
    const count = await client.incr(key);
    if (count === 1) {
      await client.expire(key, window);
    }
    return count <= limit;
  }
};
```

**Cost**: $0 (included in VPS)

---

## MONITORING & OBSERVABILITY (FREE TIER)

### Selected Tools (All Free)

#### 1. Error Tracking: Sentry (Free Tier)
- **Limit**: 5,000 events/month
- **Features**: Error tracking, stack traces, release tracking
- **Setup**:
```javascript
// backend/app.js
const Sentry = require('@sentry/node');

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1 // Sample 10% of transactions
});

// Error handler
app.use(Sentry.Handlers.errorHandler());
```

#### 2. Log Aggregation: Logtail (Free Tier)
- **Limit**: 1GB logs/month
- **Features**: Centralized logging, search, alerts
- **Setup**:
```javascript
// backend/utils/logger.js
const { createLogger, transports, format } = require('winston');
const { Logtail } = require('@logtail/node');

const logtail = new Logtail(process.env.LOGTAIL_TOKEN);

const logger = createLogger({
  level: 'info',
  format: format.combine(
    format.timestamp(),
    format.errors({ stack: true }),
    format.json()
  ),
  transports: [
    new transports.Console(),
    logtail.winston
  ]
});

module.exports = logger;
```

#### 3. Uptime Monitoring: UptimeRobot (Free)
- **Limit**: 50 monitors
- **Features**: HTTP/HTTPS checks every 5 minutes, email alerts
- **Setup**: Monitor `https://yourdomain.com/health`

#### 4. Metrics Dashboard: Grafana Cloud (Free Tier)
- **Limit**: 10k series, 14 days retention
- **Features**: Custom dashboards, Prometheus metrics
- **Metrics to Track**:
  - WebSocket connection count
  - Market data update latency
  - Voice processing latency (STT + TTS roundtrip)
  - Redis cache hit rate
  - PostgreSQL query performance
  - Error rates by type

**Setup**:
```javascript
// backend/metrics/prometheus.js
const client = require('prom-client');

// Custom metrics
const wsConnectionsGauge = new client.Gauge({
  name: 'websocket_connections_total',
  help: 'Number of active WebSocket connections'
});

const voiceLatencyHistogram = new client.Histogram({
  name: 'voice_processing_latency_ms',
  help: 'Voice processing latency in milliseconds',
  buckets: [100, 500, 1000, 2000, 5000]
});

const marketUpdateCounter = new client.Counter({
  name: 'market_updates_total',
  help: 'Total market data updates received',
  labelNames: ['symbol']
});

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType);
  res.end(await client.register.metrics());
});
```

#### 5. Self-Hosted Monitoring: PM2 (Free)
- **Features**: Process monitoring, auto-restart, CPU/memory tracking
- **Setup**:
```bash
# Install PM2
npm install -g pm2

# Start application
pm2 start backend/app.js --name capital-companion -i 2 # 2 instances

# Monitor
pm2 monit

# Logs
pm2 logs capital-companion
```

**Total Monitoring Cost**: $0/month

---

## AI INTELLIGENCE IMPLEMENTATION

### 1. Pattern Recognition (Rule-Based)

**Library**: `pandas-ta` (Technical Analysis library for Node.js via Python bridge)

**Alternative**: `technicalindicators` (Pure JavaScript)

```javascript
// backend/services/pattern-analyzer.js
const { RSI, SMA, MACD, BollingerBands } = require('technicalindicators');
const redis = require('./redis-client');

class PatternAnalyzer {
  async analyze(symbol, timeframe = 'H4') {
    // Fetch historical data from TwelveData
    const historicalData = await this.fetchHistoricalData(symbol, timeframe);

    // Calculate indicators
    const rsi = RSI.calculate({
      values: historicalData.close,
      period: 14
    });

    const sma20 = SMA.calculate({
      values: historicalData.close,
      period: 20
    });

    const macd = MACD.calculate({
      values: historicalData.close,
      fastPeriod: 12,
      slowPeriod: 26,
      signalPeriod: 9,
      SimpleMAOscillator: false,
      SimpleMASignal: false
    });

    // Detect patterns
    const patterns = this.detectPatterns({
      price: historicalData.close,
      rsi: rsi[rsi.length - 1],
      sma20: sma20[sma20.length - 1],
      macd: macd[macd.length - 1]
    });

    // Calculate confidence
    const confidence = this.calculateConfidence(patterns);

    // Cache result
    await redis.cacheMarketData(`pattern:${symbol}:${timeframe}`, {
      patterns,
      confidence,
      timestamp: Date.now()
    }, 300); // 5 min TTL

    return { patterns, confidence };
  }

  detectPatterns(indicators) {
    const patterns = [];

    // Bullish divergence
    if (indicators.rsi < 30 && indicators.price > indicators.sma20) {
      patterns.push({
        type: 'bullish_divergence',
        strength: 0.8,
        description: 'RSI oversold but price above SMA20'
      });
    }

    // MACD crossover
    if (indicators.macd.MACD > indicators.macd.signal) {
      patterns.push({
        type: 'macd_bullish_crossover',
        strength: 0.7,
        description: 'MACD crossed above signal line'
      });
    }

    // Overbought warning
    if (indicators.rsi > 70) {
      patterns.push({
        type: 'overbought',
        strength: 0.6,
        description: 'RSI overbought condition'
      });
    }

    return patterns;
  }

  calculateConfidence(patterns) {
    if (patterns.length === 0) return 0;

    const avgStrength = patterns.reduce((sum, p) => sum + p.strength, 0) / patterns.length;
    const dataRecency = 1.0; // Fresh data from TwelveData
    const volatilityPenalty = 0.9; // Assume normal volatility

    return Math.min(avgStrength * dataRecency * volatilityPenalty, 1.0);
  }

  async fetchHistoricalData(symbol, timeframe) {
    // TwelveData time series API
    const response = await axios.get('https://api.twelvedata.com/time_series', {
      params: {
        symbol,
        interval: timeframe.toLowerCase(),
        outputsize: 100,
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    const values = response.data.values;
    return {
      close: values.map(v => parseFloat(v.close)),
      high: values.map(v => parseFloat(v.high)),
      low: values.map(v => parseFloat(v.low)),
      volume: values.map(v => parseFloat(v.volume))
    };
  }
}

module.exports = new PatternAnalyzer();
```

---

### 2. Sentiment Analysis (NewsAPI + VADER)

**Free Tier**: NewsAPI (100 requests/day)

```javascript
// backend/services/sentiment-analyzer.js
const axios = require('axios');
const Sentiment = require('sentiment');
const redis = require('./redis-client');

class SentimentAnalyzer {
  constructor() {
    this.sentiment = new Sentiment();
  }

  async analyze(symbol) {
    // Check cache first
    const cached = await redis.get(`sentiment:${symbol}`);
    if (cached) return JSON.parse(cached);

    // Map symbol to search keywords
    const keywords = this.getKeywords(symbol);

    // Fetch news (NewsAPI free tier)
    const news = await this.fetchNews(keywords);

    // Analyze sentiment
    const sentimentScores = news.map(article => {
      const result = this.sentiment.analyze(article.title + ' ' + article.description);
      return result.score;
    });

    const avgScore = sentimentScores.reduce((a, b) => a + b, 0) / sentimentScores.length;

    const result = {
      symbol,
      sentiment: avgScore > 0.5 ? 'Greed' : avgScore < -0.5 ? 'Fear' : 'Neutral',
      score: avgScore,
      sources: news.length,
      timestamp: Date.now()
    };

    // Cache for 15 minutes
    await redis.cacheSentiment(symbol, result, 900);

    return result;
  }

  getKeywords(symbol) {
    const map = {
      'XAUUSD': 'gold price',
      'BTCUSD': 'bitcoin',
      'ETHUSD': 'ethereum'
    };
    return map[symbol] || symbol;
  }

  async fetchNews(keywords) {
    const response = await axios.get('https://newsapi.org/v2/everything', {
      params: {
        q: keywords,
        language: 'en',
        sortBy: 'publishedAt',
        pageSize: 10,
        apiKey: process.env.NEWSAPI_KEY
      }
    });

    return response.data.articles;
  }
}

module.exports = new SentimentAnalyzer();
```

**Cost**: $0 (free tier, 100 req/day = ~3 symbols × 30 checks/day)

---

### 3. Proactive Alert Generator

**Background Job** (runs every 30 seconds):

```javascript
// backend/jobs/alert-generator.js
const cron = require('node-cron');
const patternAnalyzer = require('../services/pattern-analyzer');
const sentimentAnalyzer = require('../services/sentiment-analyzer');
const db = require('../db/pool');

class AlertGenerator {
  start() {
    // Run every 30 seconds
    cron.schedule('*/30 * * * * *', async () => {
      await this.checkAlerts();
    });
  }

  async checkAlerts() {
    // Get all users with watchlists
    const users = await db.query('SELECT id, user_id, watchlist FROM user_profiles WHERE watchlist IS NOT NULL');

    for (const user of users.rows) {
      for (const symbol of user.watchlist) {
        const alerts = await this.generateAlertsForSymbol(symbol, user);

        for (const alert of alerts) {
          // Send alert via WebSocket
          const socketId = global.userSockets[user.user_id];
          if (socketId) {
            global.io.to(socketId).emit('alert:new', alert);
          }

          // Log alert history
          await db.query(
            'INSERT INTO alert_history (user_id, alert_type, symbol, message, confidence) VALUES ($1, $2, $3, $4, $5)',
            [user.id, alert.type, alert.symbol, alert.message, alert.confidence]
          );
        }
      }
    }
  }

  async generateAlertsForSymbol(symbol, user) {
    const alerts = [];

    // Check pattern recognition
    const patterns = await patternAnalyzer.analyze(symbol);
    if (patterns.confidence > 0.7) {
      alerts.push({
        type: 'pattern',
        symbol,
        message: `${symbol}: ${patterns.patterns[0].description}`,
        confidence: patterns.confidence,
        reasoning: patterns.patterns[0]
      });
    }

    // Check sentiment shift (every 15 min to save API quota)
    const now = Date.now();
    if (now % 900000 < 30000) { // Check once per 15 min window
      const sentiment = await sentimentAnalyzer.analyze(symbol);
      if (Math.abs(sentiment.score) > 0.8) {
        alerts.push({
          type: 'sentiment',
          symbol,
          message: `${symbol} sentiment: ${sentiment.sentiment} (${sentiment.sources} sources)`,
          confidence: 0.6
        });
      }
    }

    return alerts;
  }
}

module.exports = new AlertGenerator();
```

---

## SYSTEM ARCHITECTURE DIAGRAM (FINAL)

```
┌───────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React + Vite)                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │CapitalCompanion  │  │  Market Panels   │  │   Voice UI     │  │
│  │ - Voice controls │  │  - Price charts  │  │   - Waveform   │  │
│  │ - Chat history   │  │  - Indicators    │  │   - Talk btn   │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬───────┘  │
└───────────┼──────────────────────┼──────────────────────┼─────────┘
            │                      │                      │
            │         WebSocket (Socket.IO)               │
            ▼                      ▼                      ▼
┌────────────────────────────────────────────────────────────────────┐
│              MONOLITHIC BACKEND (Node.js)                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Socket.IO Server                          │ │
│  │  - WebSocket connection management                           │ │
│  │  - Real-time market data push                                │ │
│  │  - Voice stream handling                                     │ │
│  │  - Alert broadcasting                                        │ │
│  └────────┬─────────────────────┬───────────────┬──────────────┘ │
│           │                     │               │                 │
│  ┌────────▼─────────┐  ┌────────▼────────┐  ┌──▼──────────────┐ │
│  │ Market Data Svc  │  │  Voice Service  │  │  AI Engine      │ │
│  │ - TwelveData WS  │  │  - Whisper API  │  │  - Patterns     │ │
│  │ - Price updates  │  │  - VieNeu-TTS   │  │  - Sentiment    │ │
│  │ - Historical     │  │  - STT/TTS      │  │  - Alerts       │ │
│  └────────┬─────────┘  └────────┬────────┘  └──┬──────────────┘ │
│           │                     │               │                 │
│  ┌────────▼─────────────────────▼───────────────▼──────────────┐ │
│  │              Background Jobs (node-cron)                     │ │
│  │  - Alert generator (every 30s)                               │ │
│  │  - Sentiment updater (every 15min)                           │ │
│  │  - Database cleanup (daily)                                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────┬───────────────────────────┬─────────────────────────┘
             │                           │
             ▼                           ▼
┌────────────────────────┐  ┌────────────────────────────────┐
│  PostgreSQL (Self-host)│  │   Redis (Self-host)            │
│  - User profiles       │  │   - Market data cache (5s TTL) │
│  - Alert history       │  │   - Sentiment cache (15m TTL)  │
│  - Voice interactions  │  │   - Session state              │
│  - Connection pool     │  │   - Rate limiting              │
└────────────────────────┘  └────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  TwelveData      │  │  Whisper API     │  │  VieNeu-TTS     │ │
│  │  (WebSocket)     │  │  (OpenAI)        │  │  (Own server)   │ │
│  │  $79/mo          │  │  $0.006/min      │  │  $0             │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐  │
│  │  NewsAPI         │  │  Monitoring (Free Tier)              │  │
│  │  (Free 100/day)  │  │  - Sentry, Logtail, UptimeRobot      │  │
│  │  $0              │  │  - Grafana Cloud, PM2                │  │
│  └──────────────────┘  └──────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## DEPLOYMENT ARCHITECTURE

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Main application
  backend:
    build: ./backend
    ports:
      - "3000:3000"
      - "8000:8000" # Socket.IO port
    environment:
      - NODE_ENV=production
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=capital_companion
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - TWELVEDATA_KEY=${TWELVEDATA_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - VIENEU_TTS_URL=${VIENEU_TTS_URL}
      - NEWSAPI_KEY=${NEWSAPI_KEY}
      - SENTRY_DSN=${SENTRY_DSN}
      - LOGTAIL_TOKEN=${LOGTAIL_TOKEN}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    volumes:
      - ./backend/logs:/app/logs

  # PostgreSQL
  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=capital_companion
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/db/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Nginx (reverse proxy)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Nginx Configuration

```nginx
# nginx/nginx.conf
upstream backend {
  server backend:3000;
}

upstream websocket {
  server backend:8000;
}

server {
  listen 80;
  server_name yourdomain.com;

  # Redirect to HTTPS
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  server_name yourdomain.com;

  ssl_certificate /etc/nginx/ssl/cert.pem;
  ssl_certificate_key /etc/nginx/ssl/key.pem;

  # Frontend (static files)
  location / {
    root /var/www/frontend;
    try_files $uri /index.html;
  }

  # API
  location /api/ {
    proxy_pass http://backend/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # WebSocket
  location /socket.io/ {
    proxy_pass http://websocket/socket.io/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 86400;
  }
}
```

---

## UPDATED COST ANALYSIS

### Monthly Operational Costs (Self-Hosted)

| Item | Provider | Cost |
|------|----------|------|
| **VPS Server** (8GB RAM, 4 vCPU) | Hetzner CPX31 | $20 |
| **TwelveData Pro** (WebSocket + API) | TwelveData | $79 |
| **Whisper API** (10k min/mo) | OpenAI | $60 |
| **VieNeu-TTS** | Own server | $0 |
| **PostgreSQL** | Self-hosted | $0 |
| **Redis** | Self-hosted | $0 |
| **NewsAPI** | Free tier | $0 |
| **Monitoring** (Sentry, Logtail, etc.) | Free tiers | $0 |
| **Domain + SSL** | Cloudflare | $10 |
| **Backup Storage** (50GB) | Hetzner | $5 |
| **TOTAL** | | **$174/month** |

**Break-even**: $174 ÷ 1000 users = **$0.17/user/month**

**Monetization Target**: $5-10/month subscription = 20-60x margin

---

## IMPLEMENTATION PHASES

### Phase 1: Infrastructure Setup (Week 1)
**Goal**: Production server ready with database, cache, monitoring

**Tasks**:
1. Provision VPS (Hetzner CPX31 or equivalent)
2. Install Docker + Docker Compose
3. Setup PostgreSQL (create schemas, indexes)
4. Setup Redis (configure maxmemory, persistence off)
5. Configure Nginx (reverse proxy, SSL via Let's Encrypt)
6. Setup monitoring (Sentry, Logtail, UptimeRobot, Grafana)
7. Deploy backend skeleton (Socket.IO server)

**Acceptance**:
- [ ] VPS accessible via SSH
- [ ] PostgreSQL accepting connections
- [ ] Redis responding to commands
- [ ] Nginx serving HTTPS
- [ ] Health check endpoint returning 200 OK

---

### Phase 2: Market Data Pipeline (Week 2)
**Goal**: Real-time Gold + Crypto prices in frontend

**Tasks**:
1. Setup TwelveData account + API key
2. Implement TwelveData WebSocket client
3. Create MarketDataService (connect, subscribe, broadcast)
4. Implement Redis caching (5s TTL)
5. Create Socket.IO handlers (market:subscribe, market:update)
6. Update frontend to consume real-time data
7. Add error handling + auto-reconnection

**Acceptance**:
- [ ] Frontend displays live XAUUSD, BTCUSD, ETHUSD prices
- [ ] Prices update every 5 seconds
- [ ] Latency < 1 second from TwelveData → UI
- [ ] WebSocket reconnects automatically on disconnect

---

### Phase 3: Voice Interaction (Week 3)
**Goal**: Functional Vietnamese voice conversation

**Tasks**:
1. Implement VoiceService (Whisper API integration)
2. Implement VieNeu-TTS client (HTTP calls to your server)
3. Create Socket.IO voice handlers (voice:start, voice:audio, voice:stop)
4. Implement intent classifier (keyword matching)
   - "giá vàng" → query_price
   - "phân tích bitcoin" → analyze_chart
5. Create response generator (Vietnamese text)
6. Frontend: Add voice recording (MediaRecorder API)
7. Frontend: Add voice playback (Web Audio API)

**Acceptance**:
- [ ] User clicks "TALK", speaks "Giá vàng bao nhiêu?"
- [ ] Atlas responds: "Giá vàng hiện tại $2,105.50, tăng 2.3% hôm nay"
- [ ] Roundtrip latency < 4 seconds
- [ ] Voice quality acceptable (Vietnamese pronunciation)

---

### Phase 4: AI Pattern Recognition (Week 4)
**Goal**: Atlas detects chart patterns and generates alerts

**Tasks**:
1. Install `technicalindicators` library
2. Implement PatternAnalyzer service
   - Fetch historical data (TwelveData API)
   - Calculate RSI, SMA, MACD, Bollinger Bands
   - Detect patterns (divergence, crossover, breakout)
3. Implement confidence scoring
4. Create background job (analyze every 5 minutes)
5. Store results in Redis (5 min TTL)
6. Frontend: Display pattern alerts

**Acceptance**:
- [ ] Atlas detects bullish divergence on BTCUSD H4
- [ ] Alert shown: "Bitcoin: Phân kỳ tăng giá H4 (Độ tin cậy: 82%)"
- [ ] User taps alert → shows reasoning (RSI, SMA values)

---

### Phase 5: Sentiment Analysis (Week 5)
**Goal**: Atlas tracks market mood via news

**Tasks**:
1. Setup NewsAPI account (free tier)
2. Implement SentimentAnalyzer service
   - Fetch news for Gold/BTC/ETH
   - Analyze sentiment (VADER library)
   - Aggregate scores
3. Create background job (runs every 15 min)
4. Cache results in Redis (15 min TTL)
5. Integrate sentiment into voice responses
6. Frontend: Display sentiment indicator

**Acceptance**:
- [ ] Sentiment updates every 15 minutes
- [ ] Atlas mentions: "Tâm lý thị trường Bitcoin: Tham lam (65%)"
- [ ] Frontend shows Fear/Greed gauge

---

### Phase 6: Personalized Learning (Week 6)
**Goal**: Atlas learns user preferences

**Tasks**:
1. Create user profile management API
2. Track alert interactions (acted, dismissed, ignored)
3. Track voice command frequency
4. Implement personalization logic
   - Skip dismissed pattern types
   - Prioritize user's profitable patterns
5. Create personalized dashboard
6. Store learning data in PostgreSQL

**Acceptance**:
- [ ] User dismisses 3 RSI alerts → Atlas stops sending RSI alerts
- [ ] User profitable on H4 breakouts → Atlas prioritizes H4 alerts
- [ ] Atlas greets: "Chào buổi sáng! Mô hình H4 vàng bạn thích đang hình thành"

---

### Phase 7: Proactive Alert System (Week 7)
**Goal**: Atlas notifies user of opportunities/risks

**Tasks**:
1. Implement AlertGenerator background job (every 30s)
   - Check user watchlists for pattern matches
   - Check sentiment shifts
   - Check risk warnings (approaching SL)
2. Implement alert personalization (filter by user preferences)
3. Create alert history tracking
4. Frontend: Alert notification UI
5. Add confidence scores to all alerts

**Acceptance**:
- [ ] User has XAUUSD on watchlist → Atlas alerts breakout within 30s
- [ ] Sentiment shifts Fear→Greed → Atlas notifies
- [ ] All alerts include confidence percentage + reasoning

---

### Phase 8: Production Hardening (Week 8)
**Goal**: Ready for 100-1000 users

**Tasks**:
1. Load testing (simulate 1000 concurrent WebSocket connections)
2. Implement rate limiting (per-user API quotas)
3. Add comprehensive error handling
4. Setup automated backups (PostgreSQL daily, 7-day retention)
5. Configure PM2 cluster mode (multi-instance)
6. Security audit (SQL injection, XSS, API key exposure)
7. Create user onboarding flow
8. Write operational runbook

**Acceptance**:
- [ ] 1000 concurrent WebSocket connections stable
- [ ] 99% uptime over 7 days
- [ ] All errors tracked in Sentry
- [ ] Voice latency p95 < 4 seconds
- [ ] Database backup tested (restore successful)

---

## SUCCESS METRICS

### Functional
- ✅ Market data latency < 1 second
- ✅ Voice response latency p95 < 4 seconds
- ✅ Pattern detection accuracy > 60% (validated over 30 days)
- ✅ Confidence score calibration (70% confident = 70% accurate)

### Reliability
- ✅ Uptime > 99% (excludes planned maintenance)
- ✅ WebSocket reconnection success rate > 95%
- ✅ Zero data loss during reconnections
- ✅ TwelveData WebSocket uptime > 99%

### User Engagement
- ✅ Daily active users > 30% of total users
- ✅ Average voice interactions > 5/day/user
- ✅ Alert action rate > 20% (user acts on 1 in 5 alerts)
- ✅ User retention day-30 > 40%

### Trust & Transparency
- ✅ All alerts include confidence scores
- ✅ All recommendations include reasoning
- ✅ Risk warnings shown on high-volatility periods
- ✅ User satisfaction (NPS) > 40

---

## RISKS & MITIGATIONS

### Risk 1: TwelveData WebSocket Downtime
**Impact**: No market data → App useless
**Mitigation**: Implement fallback to REST API polling (every 5s)

### Risk 2: Whisper API Rate Limits
**Impact**: Voice interaction fails
**Mitigation**: Queue voice requests, show "processing..." message, upgrade to paid tier

### Risk 3: VPS Single Point of Failure
**Impact**: Server crash → App down
**Mitigation**: Setup health checks, auto-restart via PM2, backup VPS for failover (Phase 9)

### Risk 4: PostgreSQL Data Loss
**Impact**: User profiles, alerts lost
**Mitigation**: Daily automated backups to off-server storage (Hetzner Storage Box)

### Risk 5: High Memory Usage (AI Inference)
**Impact**: Node.js OOM crash
**Mitigation**: Monitor memory via PM2, use worker threads for AI, scale vertically if needed

---

## UNRESOLVED QUESTIONS

✅ **All resolved!**

1. ~~Language~~ → Vietnamese ✓
2. ~~Data latency~~ → 5s delay acceptable ✓
3. ~~VieNeu-TTS access~~ → Own server, no cost ✓
4. ~~Alert delivery~~ → WebSocket-only MVP ✓
5. ~~Multi-device~~ → Single device MVP ✓
6. ~~Architecture~~ → Monolith ✓
7. ~~Infrastructure~~ → Self-hosted ✓
8. ~~Monitoring~~ → Free tier ✓

---

## NEXT STEPS

**Option 1: Create Detailed Implementation Plan**
Run `/plan` to generate:
- Task-by-task breakdown for all 8 phases
- File structure with code scaffolding
- Database migration scripts
- Docker configurations
- Testing checklist
- Deployment runbook

**Option 2: Start Phase 1 Immediately**
Begin infrastructure setup:
- Provision VPS
- Setup PostgreSQL + Redis
- Configure Nginx + SSL
- Deploy monitoring tools

**Your decision?**
