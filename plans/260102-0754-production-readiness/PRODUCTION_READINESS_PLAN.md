---
title: "EV GamePad Production Readiness Plan"
description: "Comprehensive phased roadmap from current state to production deployment"
status: pending
priority: P1
effort: 120h
branch: main
tags: [production, deployment, infrastructure, security, testing]
created: 2026-01-02
---

# EV GamePad Production Readiness Plan

**Date:** 2026-01-02
**Version:** 1.0
**Prepared by:** Planning Agent (planner-260102-0754)

---

## Executive Summary

EV GamePad is a real-time AI trading advisor platform with a functional MVP (Socket.IO backend on port 8686, React frontend with 80+ components, 14 Socket.IO events). The platform is **feature-complete for single-user trading and AI advisory** but **lacks production infrastructure**.

**Key Finding:** Core trading + advisor functionality works. Critical gaps exist in testing, CI/CD, deployment, security, and monitoring. Phase 3 multiplayer features (leaderboard, teams, achievements) are partially implemented but not production-ready.

**Recommendation:** Deploy MVP without Phase 3 multiplayer first. Prioritize production infrastructure (testing, CI/CD, monitoring, security) before adding multiplayer scale features.

---

## Table of Contents

1. [Current State Assessment](#1-current-state-assessment)
2. [Production Readiness Priorities](#2-production-readiness-priorities)
3. [Phased Implementation Plan](#3-phased-implementation-plan)
4. [Technical Implementation Details](#4-technical-implementation-details)
5. [Risk Assessment](#5-risk-assessment)
6. [Timeline & Effort Estimates](#6-timeline--effort-estimates)
7. [Open Questions](#7-open-questions)

---

## 1. Current State Assessment

### 1.1 What Works Today

#### Backend (Python/FastAPI + Socket.IO)
| Component | Status | Files | Notes |
|-----------|--------|-------|-------|
| Socket.IO Server | Working | `backend/app/main.py`, `sio.py` | Port 8686 |
| Trading Events | Working | 5 events: login, buy, sell, modify, close | `events/trading_events.py` |
| Advisor Events | Working | 9 events: technical, multi-TF, patterns, risk, recommendation, portfolio, explainability | `events/advisor_events.py` |
| MT5 Integration | Working | `mt5/connection_manager.py` | Windows-only, circuit breaker |
| Redis Caching | Working | `database/redis_client.py` | 60s/300s TTL |
| PostgreSQL | Working | `database/postgres_client.py` | asyncpg pool |
| LLM Integration | Working | Claude + DeepSeek fallback | `advisor/ai_summarizer.py` |
| Technical Analysis | Working | 10 indicators | `advisor/technical_analyzer.py` |
| Pattern Detection | Working | Candlestick + chart patterns | `advisor/pattern_detector.py` |
| Chain-of-Thought | Working | 5-step reasoning engine | `advisor/chain_of_thought_engine.py` |
| Accuracy Tracking | Working | Win rate, profit factor, Sharpe | `advisor/accuracy_tracker.py` |
| KOL Webhook | Working | REST API + Socket.IO broadcast | `routers/kol_router.py` |
| Session Manager | Working | WebSocket session tracking | `session_manager.py` |

#### Frontend (React/TypeScript)
| Component | Status | Files | Notes |
|-----------|--------|-------|-------|
| Socket.IO Client | Working | `context/SocketContext.tsx` | Auto-reconnect |
| Trading Hooks | Working | `hooks/useTrading.ts` (367 LOC) | 5 operations |
| Advisor Hooks | Working | `hooks/useAdvisor.ts` (443 LOC) | 5 features |
| Portfolio Hooks | Working | `hooks/usePortfolioAnalysis.ts` | Portfolio risk |
| Accuracy Hooks | Working | `hooks/useAccuracyTracking.ts` | Performance metrics |
| UI Components | Working | 80 React components | Radix + shadcn |
| Gamepad Support | Working | `hooks/useGamepad.ts` | Xbox controller |
| Pages | Working | 4 routes: Portfolio, Plan, Action, NotFound | React Router |

#### Database
| Table | Status | Migration | Notes |
|-------|--------|-----------|-------|
| game_sessions | Created | 001 | Multi-player sessions |
| teams | Created | 002 | Team registry |
| team_members | Created | 003 | Membership tracking |
| positions | Created | 004 | P&L tracking |
| team_leaderboard | Created | 005 | Materialized view |
| mt5_account_pool | Created | 006 | Account allocation |
| mt5_orders | Created | 007 | Order tracking |
| recommendation_outcomes | Created | 005 (app) | Accuracy tracking |
| kol_messages | Created | 006 (app) | KOL signals |

#### Existing Tests (Backend)
- 23 test files in `backend/tests/`
- Tests for: circuit breaker, command processor, connection, events, reconnection, trading ops
- Tests for: accuracy tracker, chain-of-thought, data provenance, MT5 history parser
- Tests for: leaderboard service, MT5 integration, game session flow
- **Missing:** Frontend tests, E2E tests, load tests

### 1.2 What's Incomplete (Phase 3 Multiplayer)

| Feature | Implementation | Status | Blocker |
|---------|---------------|--------|---------|
| Real-time Leaderboard | 80% | Partial | Redis + MatView working, broadcast untested at scale |
| Team Mechanics | 60% | Partial | Auto-assign works, scoring incomplete |
| Paper Trading Engine | 0% | Not Started | Requires slippage model |
| Achievement System | 0% | Not Started | Gamification logic needed |
| Matchmaking | 0% | Not Started | Elo algorithm needed |
| WebSocket Optimization | 20% | Partial | Room-based, needs msgpack + load test |

### 1.3 Critical Production Gaps

| Category | Gap | Severity | Impact |
|----------|-----|----------|--------|
| **Testing** | No frontend tests | Critical | Can't verify UI regressions |
| **Testing** | No E2E tests | Critical | Integration failures in prod |
| **Testing** | No load tests | High | Unknown scale limits |
| **CI/CD** | No GitHub Actions | Critical | Manual deployments |
| **CI/CD** | No automated testing | Critical | Bugs reach production |
| **Deployment** | No Dockerfile | Critical | Can't containerize |
| **Deployment** | No docker-compose | High | Local dev inconsistency |
| **Deployment** | No cloud config | High | No deployment target |
| **Security** | No HTTPS/TLS | Critical | Data in cleartext |
| **Security** | No JWT auth | Critical | Unauthenticated access |
| **Security** | No rate limiting | High | DDoS vulnerability |
| **Security** | No CORS config | High | XSS vulnerability |
| **Security** | Secrets in code/env | High | Credential exposure |
| **Monitoring** | No APM | High | Blind to performance |
| **Monitoring** | No error tracking | High | Silent failures |
| **Monitoring** | No structured logging | Medium | Debugging difficulty |
| **Reliability** | No health checks | Medium | Can't verify health |
| **Reliability** | No backup strategy | High | Data loss risk |
| **Documentation** | No API docs (OpenAPI) | Medium | Integration difficulty |
| **Documentation** | No runbooks | Medium | Ops difficulty |

---

## 2. Production Readiness Priorities

### 2.1 MVP First vs. Phase 3 First

**Recommendation: Deploy MVP without Phase 3 multiplayer**

Rationale:
1. Core trading + advisor features are complete and tested
2. Phase 3 multiplayer requires additional 155 hours of development
3. Production infrastructure gaps are more urgent than new features
4. MVP can validate market fit before investing in multiplayer
5. Multiplayer requires load testing infrastructure not yet built

### 2.2 Priority Matrix

| Priority | Category | Items | Effort | Rationale |
|----------|----------|-------|--------|-----------|
| P0 | Security | HTTPS, JWT auth, CORS | 16h | Cannot deploy without |
| P0 | CI/CD | GitHub Actions, linting | 8h | Prevent regressions |
| P0 | Deployment | Docker, docker-compose | 8h | Reproducible builds |
| P1 | Testing | Backend test coverage | 16h | Confidence in changes |
| P1 | Monitoring | Logging, health checks | 8h | Visibility into system |
| P1 | Security | Rate limiting, input validation | 8h | Defense in depth |
| P2 | Deployment | Cloud deployment | 16h | Production environment |
| P2 | Testing | E2E tests | 16h | Full integration coverage |
| P2 | Monitoring | APM, error tracking | 8h | Performance visibility |
| P3 | Scale | Load testing | 8h | Capacity planning |
| P3 | Reliability | Backups, DR | 8h | Data protection |
| P3 | Phase 3 | Multiplayer features | 155h | Deferred post-launch |

---

## 3. Phased Implementation Plan

### Phase 1: Core Production Infrastructure (Week 1-2)

**Goal:** Enable safe, automated deployments

#### 1.1 CI/CD Pipeline (8h)

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports: [6379:6379]
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: ev_gamepad_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: test
        ports: [5432:5432]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v --cov=backend/app

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - run: pnpm install
      - run: pnpm run lint
      - run: pnpm run build
```

**Deliverables:**
- `/.github/workflows/ci.yml` - Main CI workflow
- `/.github/workflows/deploy.yml` - Deployment workflow
- Badge in README showing build status

#### 1.2 Docker Configuration (8h)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Run with uvicorn
CMD ["uvicorn", "app.main:asgi_app", "--host", "0.0.0.0", "--port", "8686"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8686:8686"
    environment:
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - DEBUG=false
    depends_on:
      - redis
      - postgres
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8686/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ev_gamepad
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

**Deliverables:**
- `/backend/Dockerfile` - Backend container
- `/Dockerfile.frontend` - Frontend container with nginx
- `/docker-compose.yml` - Full stack orchestration
- `/docker-compose.dev.yml` - Development overrides
- `/.dockerignore` - Exclude unnecessary files

#### 1.3 Backend Testing Enhancement (16h)

**Current Coverage:** ~23 test files, focused on backend
**Target Coverage:** 80% line coverage

| Area | Current | Target | Effort |
|------|---------|--------|--------|
| Circuit Breaker | 90% | 95% | 1h |
| Trading Ops | 70% | 85% | 2h |
| Advisor Processor | 60% | 80% | 4h |
| Socket.IO Events | 50% | 80% | 4h |
| Database Layer | 40% | 75% | 3h |
| KOL Processor | 30% | 80% | 2h |

**New Test Files Needed:**
- `tests/test_advisor_events_integration.py` - Full event flow
- `tests/test_socket_io_connection.py` - Connection lifecycle
- `tests/test_database_migrations.py` - Migration verification
- `tests/test_kol_router.py` - REST API tests

#### 1.4 Monitoring Setup (8h)

**Structured Logging:**
```python
# backend/app/logging_config.py (enhancement)
import logging
from pythonjsonlogger import jsonlogger

def setup_logging(debug: bool = False):
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    return root_logger
```

**Health Check Enhancement:**
```python
@app.get("/health")
async def health_check():
    """Enhanced health check with component status."""
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "mt5": mt5_manager.is_connected() if mt5_manager else False,
            "redis": await redis_client.is_connected() if redis_client else False,
            "postgres": await db_pool_manager.is_connected() if db_pool_manager else False,
        },
        "metrics": {
            "connected_clients": len(session_manager.sessions) if session_manager else 0,
            "uptime_seconds": (datetime.utcnow() - start_time).total_seconds(),
        }
    }
    checks["status"] = "healthy" if all(checks["components"].values()) else "degraded"
    return checks
```

**Deliverables:**
- Enhanced structured JSON logging
- `/health` endpoint with component status
- `/metrics` endpoint for Prometheus (optional)
- Log rotation configuration

---

### Phase 2: Security & Reliability (Week 2-3)

**Goal:** Production-grade security posture

#### 2.1 Authentication (JWT) (8h)

**Strategy:** JWT tokens with refresh capability

```python
# backend/app/auth/jwt_handler.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from pydantic import BaseModel

class TokenData(BaseModel):
    user_id: str
    expires: datetime

def create_access_token(user_id: str, expires_delta: timedelta = timedelta(hours=1)):
    expire = datetime.utcnow() + expires_delta
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        config.JWT_SECRET_KEY,
        algorithm="HS256"
    )

def verify_token(token: str) -> TokenData:
    payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"])
    return TokenData(user_id=payload["sub"], expires=payload["exp"])
```

**Socket.IO Integration:**
```python
@sio.event
async def connect(sid, environ, auth):
    """Authenticate on connection."""
    if not auth or "token" not in auth:
        raise ConnectionRefusedError("Missing authentication token")

    try:
        token_data = verify_token(auth["token"])
        await session_manager.create_session(sid, token_data.user_id)
    except JWTError:
        raise ConnectionRefusedError("Invalid authentication token")
```

**Deliverables:**
- `/backend/app/auth/jwt_handler.py` - JWT utilities
- `/backend/app/auth/dependencies.py` - FastAPI dependencies
- Socket.IO authentication middleware
- Token refresh endpoint

#### 2.2 Rate Limiting (4h)

```python
# backend/app/middleware/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to FastAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Usage on routes
@router.post("/message")
@limiter.limit("100/minute")
async def receive_kol_message(request: Request, ...):
    pass
```

**Socket.IO Rate Limiting:**
```python
# Per-event rate limiting
from collections import defaultdict
import time

event_limits = defaultdict(lambda: {"count": 0, "reset": time.time()})

async def check_rate_limit(sid: str, event: str, limit: int = 60):
    key = f"{sid}:{event}"
    now = time.time()

    if now - event_limits[key]["reset"] > 60:
        event_limits[key] = {"count": 0, "reset": now}

    event_limits[key]["count"] += 1

    if event_limits[key]["count"] > limit:
        raise RateLimitError(f"Rate limit exceeded for {event}")
```

#### 2.3 CORS & Security Headers (4h)

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,  # ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.ALLOWED_HOSTS)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

#### 2.4 Input Validation Enhancement (4h)

**Current:** Pydantic validation on models
**Enhancement:** Additional sanitization

```python
# backend/app/validation.py
import re
from html import escape

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Escape special characters
    text = escape(text)
    # Truncate
    return text[:max_length]

def validate_symbol(symbol: str) -> str:
    """Validate trading symbol format."""
    if not re.match(r'^[A-Z0-9]{2,10}$', symbol):
        raise ValueError(f"Invalid symbol format: {symbol}")
    return symbol
```

#### 2.5 Environment & Secrets Management (4h)

**Current:** `.env` file with plaintext secrets
**Target:** Secure secret management

```bash
# .env.example (template only, no real values)
# Backend
SOCKETIO_HOST=0.0.0.0
SOCKETIO_PORT=8686
DEBUG=false

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ev_gamepad
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<generate-strong-password>

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=<generate-256-bit-key>
JWT_ALGORITHM=HS256

# LLM APIs
ANTHROPIC_API_KEY=<your-anthropic-key>
DEEPSEEK_API_KEY=<your-deepseek-key>

# MT5 (encrypted)
MT5_ENCRYPTION_KEY=<generate-fernet-key>

# KOL Webhook
KOL_WEBHOOK_API_KEY=<generate-api-key>
```

**Deliverables:**
- `/.env.example` - Template with instructions
- Update `.gitignore` to exclude all `.env*` except `.env.example`
- Secret rotation documentation

---

### Phase 3: Deployment & Monitoring (Week 3-4)

**Goal:** Production environment with observability

#### 3.1 Cloud Deployment (16h)

**Recommended Stack:** DigitalOcean (cost-effective for MVP)

| Service | Provider | Specification | Monthly Cost |
|---------|----------|---------------|--------------|
| App Server | DO Droplet | 2 vCPU, 4GB RAM | $24 |
| Database | DO Managed PostgreSQL | Basic 1GB | $15 |
| Redis | DO Managed Redis | 1GB | $15 |
| Storage | DO Spaces | 50GB | $5 |
| CDN | Cloudflare | Free tier | $0 |
| **Total** | | | **$59/month** |

**Alternative: AWS (scalable but higher cost)**

| Service | AWS Service | Specification | Monthly Cost |
|---------|-------------|---------------|--------------|
| App Server | ECS Fargate | 0.5 vCPU, 1GB | $20 |
| Database | RDS PostgreSQL | db.t3.micro | $25 |
| Redis | ElastiCache | cache.t3.micro | $15 |
| ALB | Application Load Balancer | Basic | $20 |
| **Total** | | | **$80/month** |

**Deployment Script:**
```bash
#!/bin/bash
# deploy.sh

# Build images
docker-compose build

# Push to registry
docker push $REGISTRY/ev-backend:$TAG
docker push $REGISTRY/ev-frontend:$TAG

# Deploy to server
ssh $SERVER "docker-compose pull && docker-compose up -d"

# Health check
curl -f https://$DOMAIN/health || exit 1
```

#### 3.2 E2E Testing (16h)

**Tool:** Playwright for frontend + pytest for backend

```typescript
// tests/e2e/trading.spec.ts
import { test, expect } from '@playwright/test';

test('complete trading flow', async ({ page }) => {
  // Connect to app
  await page.goto('http://localhost:3000');

  // Verify Socket.IO connection
  await expect(page.locator('[data-testid="connection-status"]')).toHaveText('Connected');

  // Execute trade
  await page.fill('[data-testid="symbol-input"]', 'EURUSD');
  await page.fill('[data-testid="volume-input"]', '0.01');
  await page.click('[data-testid="buy-button"]');

  // Verify order result
  await expect(page.locator('[data-testid="order-result"]')).toBeVisible();
});
```

**Backend E2E:**
```python
# tests/e2e/test_full_flow.py
import pytest
import socketio

@pytest.mark.asyncio
async def test_trading_flow():
    client = socketio.AsyncClient()
    await client.connect('http://localhost:8686')

    # Login
    result = await client.call('login', {'account': 12345, 'password': 'demo'})
    assert result['success']

    # Get technical analysis
    tech = await client.call('advisor_technical_summary', {'symbol': 'EURUSD', 'timeframe': 'H1'})
    assert 'indicators' in tech

    await client.disconnect()
```

#### 3.3 APM & Error Tracking (8h)

**Recommended:** Sentry (free tier for small teams)

```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=config.ENVIRONMENT,
)
```

**Frontend Sentry:**
```typescript
// src/main.tsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [
    Sentry.browserTracingIntegration(),
  ],
  tracesSampleRate: 0.1,
});
```

**Deliverables:**
- Sentry integration (backend + frontend)
- Error alerting to Slack/Discord
- Performance monitoring dashboard

---

### Phase 4: Scale & Performance (Week 4-5)

**Goal:** Validate capacity and optimize

#### 4.1 Load Testing (8h)

**Tool:** Locust for WebSocket load testing

```python
# tests/load/locustfile.py
from locust import User, task, between
import socketio

class WebSocketUser(User):
    wait_time = between(1, 3)

    def on_start(self):
        self.client = socketio.Client()
        self.client.connect('http://localhost:8686')

    @task(3)
    def get_technical_analysis(self):
        self.client.emit('advisor_technical_summary',
                        {'symbol': 'EURUSD', 'timeframe': 'H1'})

    @task(1)
    def get_recommendation(self):
        self.client.emit('advisor_recommendation',
                        {'symbol': 'XAUUSD', 'timeframe': 'H4'})

    def on_stop(self):
        self.client.disconnect()
```

**Targets:**
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Concurrent connections | 100 | Unknown | Untested |
| Requests/sec | 500 | Unknown | Untested |
| P95 latency | <2s | Unknown | Untested |
| Error rate | <1% | Unknown | Untested |

#### 4.2 Caching Optimization (4h)

**Current Cache TTLs:**
- Indicators: 60s
- Patterns: 300s
- AI responses: 300s
- CoT results: 300s

**Optimization:**
```python
# Adaptive TTL based on volatility
def get_cache_ttl(symbol: str, timeframe: str) -> int:
    base_ttl = {
        'M1': 30,
        'M5': 60,
        'M15': 120,
        'H1': 300,
        'H4': 600,
        'D1': 3600,
    }
    return base_ttl.get(timeframe, 300)
```

#### 4.3 Database Optimization (4h)

**Index Audit:**
```sql
-- Verify indexes exist
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('recommendation_outcomes', 'kol_messages', 'positions');

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_positions_user_session
ON positions(user_id, session_id) WHERE closed_at IS NULL;

CREATE INDEX CONCURRENTLY idx_recommendation_outcomes_created
ON recommendation_outcomes(created_at DESC);
```

**Connection Pool Tuning:**
```python
# Current: min_size=2, max_size=10
# Recommended for 100 users: min_size=5, max_size=20
```

#### 4.4 Backup & Recovery (4h)

**PostgreSQL Backup Strategy:**
```bash
#!/bin/bash
# backup.sh - Daily backup script

DATE=$(date +%Y%m%d)
BACKUP_DIR=/backups

# Dump database
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB \
  -F custom -f $BACKUP_DIR/ev_gamepad_$DATE.dump

# Upload to S3/Spaces
aws s3 cp $BACKUP_DIR/ev_gamepad_$DATE.dump s3://$BUCKET/backups/

# Retain last 30 days
find $BACKUP_DIR -name "*.dump" -mtime +30 -delete
```

**Recovery Procedure:**
```bash
# Restore from backup
pg_restore -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB \
  -c $BACKUP_DIR/ev_gamepad_$DATE.dump
```

---

## 4. Technical Implementation Details

### 4.1 File Structure Changes

```
ev-backend/
├── .github/
│   └── workflows/
│       ├── ci.yml           # NEW: CI pipeline
│       └── deploy.yml       # NEW: Deployment
├── backend/
│   ├── Dockerfile           # NEW: Backend container
│   ├── app/
│   │   ├── auth/            # NEW: Authentication
│   │   │   ├── jwt_handler.py
│   │   │   └── dependencies.py
│   │   ├── middleware/      # NEW: Middleware
│   │   │   ├── rate_limiter.py
│   │   │   └── security_headers.py
│   │   └── ...existing...
│   └── tests/
│       ├── e2e/             # NEW: E2E tests
│       │   └── test_full_flow.py
│       └── load/            # NEW: Load tests
│           └── locustfile.py
├── Dockerfile.frontend      # NEW: Frontend container
├── docker-compose.yml       # NEW: Orchestration
├── docker-compose.dev.yml   # NEW: Dev overrides
├── nginx.conf               # NEW: Frontend proxy
├── .env.example             # NEW: Template
└── tests/
    └── e2e/                 # NEW: Playwright tests
        └── trading.spec.ts
```

### 4.2 Configuration Changes

**New Environment Variables:**
```bash
# Security
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ALLOWED_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com

# Monitoring
SENTRY_DSN=
ENVIRONMENT=production

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

### 4.3 Database Schema Changes

**New: users table (for JWT auth)**
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_users_email ON users(email);
```

**Note:** If using external auth (OAuth/SSO), this table is optional.

### 4.4 API Changes

**New Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Authenticate, return JWT |
| `/auth/refresh` | POST | Refresh JWT token |
| `/health` | GET | Enhanced health check |
| `/metrics` | GET | Prometheus metrics |

**Socket.IO Auth Change:**
```typescript
// Frontend connection with auth
const socket = io('https://api.yourdomain.com', {
  auth: {
    token: localStorage.getItem('jwt_token')
  }
});
```

---

## 5. Risk Assessment

### 5.1 Critical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| MT5 unavailable on cloud | High | Critical | Deploy MT5 bridge on Windows VM, expose via API |
| Secrets leaked in git | Medium | Critical | Pre-commit hooks, secret scanning |
| DDoS attack | Medium | High | Cloudflare protection, rate limiting |
| Database corruption | Low | Critical | Daily backups, point-in-time recovery |
| JWT key compromise | Low | Critical | Key rotation procedure, short expiry |

### 5.2 Technical Debt

| Item | Location | Severity | Effort to Fix |
|------|----------|----------|---------------|
| Any types in frontend | `src/` | Medium | 4h |
| Demo data in components | `AIAnalysis.tsx`, `MarketOverview.tsx` | Medium | 2h |
| Incomplete accuracy tracking | `useAccuracyTracking.ts` | Low | 2h |
| Order recovery unclear | Socket.IO events | Medium | 4h |
| No graceful shutdown | `main.py` | Low | 2h |

### 5.3 Security Vulnerabilities

| Vulnerability | Current State | Fix |
|---------------|---------------|-----|
| No authentication | Anyone can connect | JWT implementation |
| Cleartext transmission | HTTP only | HTTPS/TLS |
| No rate limiting | Unlimited requests | slowapi + Redis |
| Prompt injection | Basic sanitization | Enhanced validation |
| CORS misconfiguration | Not set | Explicit origins |

---

## 6. Timeline & Effort Estimates

### 6.1 Detailed Timeline

```
Week 1 (Jan 2-8, 2026)
├── Day 1-2: CI/CD Pipeline (8h)
│   ├── GitHub Actions workflows
│   └── Test automation
├── Day 3-4: Docker Configuration (8h)
│   ├── Backend Dockerfile
│   ├── Frontend Dockerfile
│   └── docker-compose setup
└── Day 5-7: Testing Enhancement (16h)
    ├── Backend test coverage
    └── Test fixtures

Week 2 (Jan 9-15, 2026)
├── Day 1-2: Authentication (8h)
│   ├── JWT implementation
│   └── Socket.IO auth
├── Day 3: Rate Limiting (4h)
├── Day 4: Security Headers/CORS (4h)
├── Day 5: Input Validation (4h)
└── Day 6-7: Environment/Secrets (4h)

Week 3 (Jan 16-22, 2026)
├── Day 1-3: Cloud Deployment (16h)
│   ├── Infrastructure setup
│   ├── DNS/SSL configuration
│   └── Deployment automation
└── Day 4-7: E2E Testing (16h)
    ├── Playwright setup
    └── Test scenarios

Week 4 (Jan 23-29, 2026)
├── Day 1-2: APM/Error Tracking (8h)
├── Day 3-4: Load Testing (8h)
├── Day 5: Database Optimization (4h)
└── Day 6-7: Backup/Recovery (4h)

Week 5 (Jan 30 - Feb 5, 2026)
└── Buffer/Launch Preparation
    ├── Documentation finalization
    ├── Runbook creation
    └── Launch checklist
```

### 6.2 Effort Summary

| Phase | Description | Effort | Cumulative |
|-------|-------------|--------|------------|
| Phase 1 | Core Infrastructure | 40h | 40h |
| Phase 2 | Security & Reliability | 24h | 64h |
| Phase 3 | Deployment & Monitoring | 40h | 104h |
| Phase 4 | Scale & Performance | 16h | 120h |
| **Total** | | **120h** | |

### 6.3 Critical Path

```
CI/CD Setup → Docker → Tests → Auth → Rate Limit → Deploy → E2E → Launch
    8h    →   8h   →  16h  →  8h  →    4h    →  16h  →  16h → Ready

Minimum viable path: 76h (3 weeks)
With parallelization: 56h (2.5 weeks)
```

---

## 7. Open Questions

### 7.1 Deployment Decisions

| Question | Options | Recommendation | Rationale |
|----------|---------|----------------|-----------|
| Cloud provider? | AWS, GCP, Azure, DO | DigitalOcean | Cost-effective for MVP ($59/mo vs $80+) |
| Authentication? | JWT, OAuth, Session | JWT | Stateless, works with Socket.IO |
| MT5 on cloud? | Windows VM, Bridge API | Windows VM + API | MT5 requires Windows |

### 7.2 Architecture Decisions

| Question | Options | Recommendation | Rationale |
|----------|---------|----------------|-----------|
| Phase 3 timing? | Before launch, After launch | After launch | Validate MVP first |
| Real MT5 or demo? | Demo first, Real from start | Demo first | Lower risk during testing |
| Multi-tenant? | Single-tenant, Multi-tenant | Single-tenant initially | Simpler MVP |

### 7.3 Operational Decisions

| Question | Options | Recommendation | Rationale |
|----------|---------|----------------|-----------|
| On-call rotation? | Solo, Team rotation | Solo initially | Small team |
| Backup frequency? | Hourly, Daily, Weekly | Daily | Balance cost/risk |
| Log retention? | 7 days, 30 days, 90 days | 30 days | Cost vs debugging needs |

### 7.4 Unresolved Technical Questions

1. **MT5 Cloud Deployment:** How to run MT5 terminal on cloud (Windows only)?
   - Option A: Windows VM on Azure/AWS
   - Option B: MT5 bridge service exposing REST API
   - Option C: Remote desktop to on-premise Windows machine

2. **WebSocket Scaling:** How to scale Socket.IO beyond single instance?
   - Redis adapter for multi-node
   - Sticky sessions on load balancer
   - Consider Socket.IO cluster mode

3. **Frontend State Management:** Current hooks sufficient or need global state?
   - Current: React hooks (useState, useCallback)
   - Consider: TanStack Query for server state (already in deps)
   - Not needed: Redux/Zustand for MVP

4. **Secrets Management at Scale:** How to manage secrets in production?
   - Option A: Environment variables (current)
   - Option B: AWS Secrets Manager / DO Secrets
   - Option C: HashiCorp Vault (overkill for MVP)

---

## Next Steps

1. **Immediate (Today):**
   - Review and approve this plan
   - Decide on cloud provider (recommend DigitalOcean)
   - Decide on JWT vs OAuth authentication

2. **This Week:**
   - Begin Phase 1.1: CI/CD Pipeline
   - Create `.github/workflows/ci.yml`
   - Add test automation

3. **Parallel Track:**
   - Finalize deployment target
   - Set up cloud account
   - Plan MT5 cloud strategy

---

## Document Status

- **Status:** Pending Review
- **Created:** 2026-01-02
- **Author:** Planning Agent
- **Reviewer:** [Pending]
- **Approval:** [Pending]

---

## Appendix A: Quick Reference Commands

```bash
# Local development
docker-compose -f docker-compose.dev.yml up

# Run tests
pytest backend/tests/ -v --cov=backend/app

# Build production
docker-compose build

# Deploy
./deploy.sh production

# Health check
curl https://api.yourdomain.com/health

# Backup
./backup.sh
```

## Appendix B: Monitoring Dashboards

**Key Metrics to Track:**
- Socket.IO connections (current, peak)
- Request latency (P50, P95, P99)
- Cache hit rate
- Error rate by endpoint
- MT5 connection status
- Database connection pool utilization
- Redis memory usage

## Appendix C: Runbook Templates

See `/docs/runbooks/` (to be created) for:
- Incident response
- Deployment rollback
- Database recovery
- Secret rotation
- Scale-up procedures
