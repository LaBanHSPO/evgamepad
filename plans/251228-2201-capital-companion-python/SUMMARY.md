# Capital Companion Implementation Summary

**Status**: Planning Complete
**Total Phases**: 8 (Phase 3 expanded to AI Trading Advisor)
**Estimated Timeline**: 9-10 weeks
**Architecture**: Python Backend Extension

---

## PHASE COMPLETION STATUS

| Phase | Name | Status | Documentation |
|-------|------|--------|---------------|
| 1 | Infrastructure & Database | ⬜ Not Started | `phase-01-infrastructure-database.md` |
| 2 | Market Data Service | ⬜ Not Started | `phase-02-market-data-service.md` |
| **3** | **AI Trading Advisor** | ⬜ Not Started | **`phase-03-ai-trading-advisor.md`** |
| 3-old | Voice Interaction (LLM) | Superseded | `phase-03-voice-interaction-llm.md` |
| 4 | AI Pattern Recognition | ⬜ Merged into Phase 3 | Integrated into AI Advisor |
| 5 | Sentiment Analysis | ⬜ Merged into Phase 3 | Integrated into AI Advisor |
| 6 | Personalized Learning | ⬜ Not Started | See below (Phase 6-8) |
| 7 | Proactive Alerts | ⬜ Not Started | See below (Phase 6-8) |
| 8 | Production Hardening | ⬜ Not Started | See below (Phase 6-8) |

---

## PHASE 3 CHANGES (AI Trading Advisor)

**NEW**: Phase 3 expanded from simple voice intent extraction to comprehensive AI Trading Advisor:

| Feature | Old Phase 3 | New Phase 3 |
|---------|-------------|-------------|
| LLM Role | Function-calling classifier | Analytical reasoner with RAG |
| Data Sources | Market data only | Sentiment + News + KOL + Patterns + Multi-TF |
| Memory | Single-turn | Multi-turn conversation |
| Response | Static templates | Streaming + Chain-of-Thought |
| Legal | None | Mandatory disclaimers + audit |
| Cost | $8-35/mo | $50-150/mo |
| Duration | 2 weeks | 3 weeks |

**Key Files**:
- `ai_advisor_service.py` - Core reasoning chain
- `data_aggregator.py` - Multi-source data aggregation
- `sentiment_service.py` - Aggregated sentiment
- `kol_service.py` - KOL signals from Twitter
- `multiframe_service.py` - M5 to D1 trend analysis
- `memory_manager.py` - Conversation context
- `legal_compliance.py` - Disclaimers + audit trail

**Phases 4-5 Merged**: Pattern recognition and sentiment analysis now integrated into Phase 3's Data Aggregation Layer.

---

## PHASE 4: AI PATTERN RECOGNITION (Week 4)

### Goal
Implement technical analysis engine with RSI, SMA, MACD, Bollinger Bands. Detect patterns (bullish divergence, crossovers, breakouts) with confidence scores.

### Key Files to Create
- `backend/app/capital_companion/pattern_analyzer.py`
- `backend/app/jobs/pattern_analysis_job.py`
- `backend/app/utils/confidence_scorer.py`
- `backend/requirements.txt` (add: `ta==0.11.0`, `APScheduler==3.11.0`)

### Core Logic
```python
# Pattern Analyzer Service
class PatternAnalyzer:
    async def analyze(symbol: str, timeframe: str = 'H4'):
        # Fetch historical data from TwelveData
        df = await fetch_historical(symbol, timeframe, outputsize=100)

        # Calculate indicators
        df['rsi'] = RSI(df['close'], period=14)
        df['sma_20'] = SMA(df['close'], period=20)
        df['macd'] = MACD(df['close'])
        df['bb_upper'], df['bb_lower'] = BollingerBands(df['close'])

        # Detect patterns
        patterns = []
        if df['rsi'][-1] < 30 and df['close'][-1] > df['sma_20'][-1]:
            patterns.append({
                'type': 'bullish_divergence',
                'strength': 0.8
            })

        # Calculate confidence
        confidence = calculate_confidence(patterns, data_recency, volatility)

        # Cache in Redis (5 min TTL)
        await redis.cache_pattern(symbol, timeframe, {
            'patterns': patterns,
            'confidence': confidence
        }, ttl=300)

        return patterns, confidence
```

### Background Job
```python
# APScheduler job (every 5 minutes)
scheduler.add_job(
    analyze_all_symbols,
    'interval',
    minutes=5
)
```

### Acceptance Criteria
- [ ] RSI, SMA, MACD, BB calculated correctly
- [ ] Patterns detected (divergence, crossover, breakout)
- [ ] Confidence scores (0-1 scale)
- [ ] Results cached in Redis (5 min TTL)
- [ ] Background job runs every 5 minutes
- [ ] Alerts sent via Socket.IO when pattern detected

---

## PHASE 5: SENTIMENT ANALYSIS (Week 5)

### Goal
Analyze market sentiment via NewsAPI + VADER. Classify as Fear/Neutral/Greed with confidence.

### Key Files to Create
- `backend/app/capital_companion/sentiment_analyzer.py`
- `backend/app/jobs/sentiment_update_job.py`
- `backend/requirements.txt` (add: `vaderSentiment==3.3.2`)

### Core Logic
```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.newsapi_key = os.getenv('NEWSAPI_KEY')

    async def analyze(symbol: str):
        # Map symbol to keywords
        keywords = {'XAUUSD': 'gold price', 'BTCUSD': 'bitcoin'}[symbol]

        # Fetch news (NewsAPI free tier: 100 req/day)
        news = await fetch_news(keywords, pageSize=10)

        # Analyze sentiment
        scores = []
        for article in news:
            text = f"{article['title']} {article['description']}"
            score = self.analyzer.polarity_scores(text)['compound']
            scores.append(score)

        avg_score = sum(scores) / len(scores)

        # Classify
        if avg_score > 0.5:
            sentiment = 'Greed'
        elif avg_score < -0.5:
            sentiment = 'Fear'
        else:
            sentiment = 'Neutral'

        # Cache (15 min TTL)
        await redis.cache_sentiment(symbol, {
            'sentiment': sentiment,
            'score': avg_score,
            'sources': len(news)
        }, ttl=900)

        return sentiment, avg_score
```

### Background Job
Run every 60 minutes to stay within NewsAPI free tier (100 req/day). With 4 symbols, hourly checks = 96 req/day (within limit).

### Acceptance Criteria
- [ ] NewsAPI integration (free tier)
- [ ] VADER sentiment scoring
- [ ] Fear/Neutral/Greed classification
- [ ] Cached in Redis (60 min TTL)
- [ ] Background job every 60 minutes
- [ ] Integrated into voice responses

---

## PHASE 6: PERSONALIZED LEARNING (Week 6)

### Goal
Track user preferences (alert interactions, successful patterns, risk tolerance). Adapt recommendations.

### Key Files to Create
- `backend/app/capital_companion/personalization.py`
- FastAPI routes for user profile CRUD

### Core Logic
```python
class PersonalizationEngine:
    async def learn_from_alert_action(user_id: str, alert_id: str, action: str):
        # Track: acted, dismissed, ignored
        await postgres.update_alert_action(alert_id, action)

        # If dismissed 3+ times for same pattern type, stop sending
        dismissed_count = await postgres.count_dismissed_by_type(
            user_id, alert_type='rsi_oversold'
        )
        if dismissed_count >= 3:
            # Update user profile to filter this pattern
            await postgres.update_user_profile(user_id,
                filtered_patterns=['rsi_oversold']
            )

    async def should_send_alert(user_id: str, alert: Alert) -> bool:
        # Check user preferences
        profile = await postgres.get_user_profile(user_id)

        # Filter by dismissed patterns
        if alert.type in profile['filtered_patterns']:
            return False

        # Prioritize successful patterns
        if alert.pattern in profile['successful_patterns']:
            alert.confidence *= 1.2  # Boost confidence

        return True
```

### Acceptance Criteria
- [ ] Alert interaction tracking (acted, dismissed, ignored)
- [ ] Pattern frequency analysis
- [ ] Auto-filter dismissed patterns (3+ dismissals)
- [ ] Prioritize successful patterns
- [ ] User profile CRUD endpoints
- [ ] Dashboard showing learned preferences

---

## PHASE 7: PROACTIVE ALERTS (Week 7)

### Goal
Generate alerts from multiple sources (patterns + sentiment + risk). Send via Socket.IO with confidence + reasoning.

### Key Files to Create
- `backend/app/capital_companion/alert_generator.py`
- `backend/app/jobs/alert_check_job.py`
- `backend/app/events/alert_events.py`
- `backend/app/models/alerts.py`

### Core Logic
```python
class AlertGenerator:
    async def generate_alerts(user_id: str):
        alerts = []
        profile = await postgres.get_user_profile(user_id)

        for symbol in profile['watchlist']:
            # Check pattern alerts
            pattern = await redis.get_pattern(symbol, 'H4')
            if pattern and pattern['confidence'] > 0.7:
                alert = {
                    'type': 'pattern',
                    'symbol': symbol,
                    'message': f"{symbol}: {pattern['patterns'][0]['description']}",
                    'confidence': pattern['confidence'],
                    'reasoning': pattern['patterns']
                }

                # Apply personalization filter
                if await personalization.should_send_alert(user_id, alert):
                    alerts.append(alert)

            # Check sentiment shift
            sentiment = await redis.get_sentiment(symbol)
            if sentiment and abs(sentiment['score']) > 0.8:
                alerts.append({
                    'type': 'sentiment',
                    'symbol': symbol,
                    'message': f"{symbol} sentiment: {sentiment['sentiment']}",
                    'confidence': 0.6
                })

        # Send alerts via Socket.IO
        for alert in alerts:
            await sio.emit('alert:new', alert, room=user_socket_id)
            await postgres.create_alert(user_id, **alert)

        return alerts
```

### Background Job
```python
# Run every 30 seconds
scheduler.add_job(
    check_all_users_alerts,
    'interval',
    seconds=30
)
```

### Acceptance Criteria
- [ ] Multi-source alert generation (patterns + sentiment + risk)
- [ ] Personalization filtering applied
- [ ] Alerts include confidence + reasoning
- [ ] Socket.IO `alert:new` event
- [ ] Alert history tracked in database
- [ ] Background job every 30s

---

## PHASE 8: PRODUCTION HARDENING (Week 8)

### Goal
Production-ready deployment: monitoring, security, backups, load testing.

### Tasks

#### 8.1 Nginx Reverse Proxy + SSL
```nginx
# /etc/nginx/sites-available/capital-companion
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/capital-companion;
        try_files $uri /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
    }

    # Socket.IO
    location /socket.io/ {
        proxy_pass http://localhost:8000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 8.2 Supervisor Process Management
```ini
# /etc/supervisor/conf.d/capital-companion.conf
[program:capital-companion]
command=/app/venv/bin/python -m app.main
directory=/app/backend
user=app
autostart=true
autorestart=true
stderr_logfile=/var/log/capital-companion/err.log
stdout_logfile=/var/log/capital-companion/out.log
environment=PATH="/app/venv/bin"
```

#### 8.3 Sentry Error Tracking
```python
# backend/app/logging_config.py
import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=0.1,
    integrations=[AsyncioIntegration()]
)
```

#### 8.4 Prometheus Metrics
```python
# backend/app/main.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

ws_connections = Gauge('websocket_connections', 'Active WebSocket connections')
voice_latency = Histogram('voice_latency_ms', 'Voice processing latency')
market_updates = Counter('market_updates_total', 'Market data updates')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### 8.5 PostgreSQL Backups
```bash
#!/bin/bash
# /etc/cron.daily/postgres-backup.sh

BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup
pg_dump capital_companion | gzip > $BACKUP_DIR/capital_companion_$DATE.sql.gz

# Retain 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

#### 8.6 Rate Limiting
```python
# backend/app/main.py
from fastapi import Request, HTTPException

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    redis_client = get_redis_client()

    if not await redis_client.check_rate_limit(client_ip, limit=100, window=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return await call_next(request)
```

#### 8.7 Load Testing
```bash
# Install locust
pip install locust

# locustfile.py
from locust import User, task, between
import socketio

class CapitalCompanionUser(User):
    wait_time = between(1, 5)

    def on_start(self):
        self.sio = socketio.Client()
        self.sio.connect('http://localhost:8000')

    @task
    def subscribe_market(self):
        self.sio.emit('market:subscribe', {'symbols': ['BTCUSD']})

    @task
    def query_price(self):
        self.sio.emit('voice:start')
        # Simulate voice interaction

# Run: locust -f locustfile.py --users 1000 --spawn-rate 10
```

### Acceptance Criteria
- [ ] Nginx SSL configured (Let's Encrypt)
- [ ] Supervisor manages backend process
- [ ] Sentry error tracking operational
- [ ] Logtail log aggregation configured
- [ ] Prometheus metrics endpoint `/metrics`
- [ ] Grafana dashboards created
- [ ] PostgreSQL daily backups (7-day retention)
- [ ] Rate limiting (100 req/min per IP)
- [ ] Load test: 1000 concurrent WebSocket connections stable
- [ ] Security audit passed (SQL injection, XSS, secrets)
- [ ] Operational runbook documented

---

## FINAL DELIVERABLES

### Backend
- ✅ PostgreSQL + Redis integration
- ✅ TwelveData WebSocket (real-time market data)
- ✅ Voice service (Whisper + VieNeu-TTS)
- ✅ AI pattern recognition (RSI, SMA, MACD, BB)
- ✅ Sentiment analysis (NewsAPI + VADER)
- ✅ Personalization engine
- ✅ Proactive alert system
- ✅ Production monitoring (Sentry + Logtail + Prometheus)

### Frontend
- ✅ Real-time market data display
- ✅ Vietnamese voice interaction UI
- ✅ Pattern alert notifications
- ✅ Sentiment gauge
- ✅ Personalized dashboard

### Infrastructure
- ✅ Docker Compose (PostgreSQL + Redis + Backend)
- ✅ Nginx reverse proxy + SSL
- ✅ Supervisor process management
- ✅ Automated backups
- ✅ Monitoring dashboards

---

## COST SUMMARY (Monthly)

| Service | Cost |
|---------|------|
| Hetzner VPS (8GB) | $20 |
| TwelveData Pro | $79 |
| Whisper API (10k min) | $60 |
| VieNeu-TTS | $0 (own server) |
| Domain + SSL | $10 |
| Backup Storage | $5 |
| **TOTAL** | **$174** |

**Break-even**: $0.17/user/month (1000 users)

---

## NEXT ACTIONS

1. ✅ **Plan Complete** - All 8 phases documented
2. ⬜ **Review Plan** - Stakeholder approval
3. ⬜ **Provision VPS** - Hetzner CPX31
4. ⬜ **Start Phase 1** - Database integration
5. ⬜ **Sequential Execution** - Phases 1-8 in order

**Ready to implement!**
