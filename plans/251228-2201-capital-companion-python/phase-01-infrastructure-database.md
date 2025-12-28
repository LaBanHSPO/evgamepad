# Phase 1: Infrastructure & Database Integration

**Duration**: Week 1
**Goal**: PostgreSQL + Redis operational, integrated with existing Python backend
**Status**: Not Started

---

## OVERVIEW

Integrate PostgreSQL and Redis into existing `backend/` Python application. Setup Docker Compose for local/production deployment. Extend backend configuration and lifespan management.

### Prerequisites
- Existing backend at `backend/` (FastAPI + Python-SocketIO)
- Docker + Docker Compose installed
- VPS provisioned (Hetzner CPX31 or equivalent)

---

## TASK BREAKDOWN

### Task 1.1: Create Docker Compose Configuration
**Estimated Effort**: 1-2 hours

**Files to Create**:
```yaml
# backend/docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: capital_companion_postgres
    environment:
      POSTGRES_DB: capital_companion
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/migrations:/docker-entrypoint-initdb.d:ro
    ports:
      - "${DB_PORT:-5432}:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - capital_companion_net

  redis:
    image: redis:7-alpine
    container_name: capital_companion_redis
    command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru --save ""
    volumes:
      - redis_data:/data
    ports:
      - "${REDIS_PORT:-6379}:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - capital_companion_net

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: capital_companion_backend
    ports:
      - "${SOCKETIO_PORT:-8000}:8000"
    environment:
      # Database
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=capital_companion
      - DB_USER=${DB_USER:-postgres}
      - DB_PASSWORD=${DB_PASSWORD:-changeme}

      # Redis
      - REDIS_HOST=redis
      - REDIS_PORT=6379

      # MT5 (existing)
      - MT5_ACCOUNT=${MT5_ACCOUNT}
      - MT5_PASSWORD=${MT5_PASSWORD}
      - MT5_SERVER=${MT5_SERVER}

      # Capital Companion
      - TWELVEDATA_KEY=${TWELVEDATA_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - VIENEU_TTS_URL=${VIENEU_TTS_URL}
      - NEWSAPI_KEY=${NEWSAPI_KEY}

      # Monitoring
      - SENTRY_DSN=${SENTRY_DSN:-}
      - LOGTAIL_TOKEN=${LOGTAIL_TOKEN:-}

      # Server Config
      - SOCKETIO_HOST=0.0.0.0
      - SOCKETIO_PORT=8000
      - DEBUG=${DEBUG:-false}

    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

    restart: unless-stopped

    volumes:
      - ./app:/app/app:ro
      - ./logs:/app/logs

    networks:
      - capital_companion_net

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  capital_companion_net:
    driver: bridge
```

**Update** `backend/.env.example`:
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=capital_companion
DB_USER=postgres
DB_PASSWORD=changeme

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# MT5 Trading (existing)
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=BrokerServer-Demo

# Capital Companion
TWELVEDATA_KEY=your_twelvedata_key
OPENAI_API_KEY=your_openai_key
VIENEU_TTS_URL=http://your-vieneu-server:5000/tts
NEWSAPI_KEY=your_newsapi_key

# Monitoring (optional)
SENTRY_DSN=
LOGTAIL_TOKEN=

# Server
SOCKETIO_HOST=0.0.0.0
SOCKETIO_PORT=8000
DEBUG=true
```

**Acceptance**:
- [ ] `docker-compose.yml` created
- [ ] `.env.example` updated with new variables
- [ ] Copy `.env.example` to `.env` and configure

---

### Task 1.2: Create Database Migration Scripts
**Estimated Effort**: 2-3 hours

**Files to Create**:
```sql
-- backend/db/migrations/001_initial_schema.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User Profiles Table
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT UNIQUE NOT NULL,
    risk_tolerance TEXT CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')) DEFAULT 'moderate',
    preferred_timeframes TEXT[] DEFAULT ARRAY['H4', 'D1'],
    watchlist TEXT[] DEFAULT ARRAY['XAUUSD', 'BTCUSD', 'ETHUSD'],
    voice_enabled BOOLEAN DEFAULT true,
    language TEXT DEFAULT 'vi',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alert History Table
CREATE TABLE alert_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    message TEXT NOT NULL,
    confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    reasoning JSONB,
    user_action TEXT CHECK (user_action IN ('acted', 'dismissed', 'ignored')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Voice Interactions Table
CREATE TABLE voice_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    transcript TEXT NOT NULL,
    response TEXT NOT NULL,
    intent TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_alert_history_user_id ON alert_history(user_id);
CREATE INDEX idx_alert_history_created_at ON alert_history(created_at DESC);
CREATE INDEX idx_alert_history_symbol ON alert_history(symbol);
CREATE INDEX idx_voice_interactions_user_id ON voice_interactions(user_id);
CREATE INDEX idx_voice_interactions_created_at ON voice_interactions(created_at DESC);
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE
    ON user_profiles FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert test user (for development)
INSERT INTO user_profiles (user_id, risk_tolerance, watchlist) VALUES
    ('test_user_1', 'moderate', ARRAY['XAUUSD', 'BTCUSD', 'ETHUSD']),
    ('test_user_2', 'aggressive', ARRAY['BTCUSD', 'ETHUSD', 'BNBUSD'])
ON CONFLICT (user_id) DO NOTHING;

-- Comments
COMMENT ON TABLE user_profiles IS 'User preferences and learning data for personalized Capital Companion experience';
COMMENT ON TABLE alert_history IS 'Historical record of all alerts sent to users with their responses';
COMMENT ON TABLE voice_interactions IS 'Voice conversation history for analysis and improvement';
```

**Acceptance**:
- [ ] SQL migration script created
- [ ] Schema includes all required tables
- [ ] Indexes created for performance
- [ ] Triggers for auto-updating timestamps
- [ ] Test data inserted

---

### Task 1.3: Create PostgreSQL Client Module
**Estimated Effort**: 3-4 hours

**File**: `backend/app/database/postgres_client.py`

```python
"""
PostgreSQL async client using asyncpg
"""
import asyncpg
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class PostgresClient:
    """Async PostgreSQL client with connection pooling"""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        min_size: int = 5,
        max_size: int = 20
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=60
            )
            logger.info(f"PostgreSQL pool created: {self.host}:{self.port}/{self.database}")

            # Test connection
            async with self.pool.acquire() as conn:
                version = await conn.fetchval('SELECT version()')
                logger.info(f"PostgreSQL version: {version}")

        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            raise

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool"""
        async with self.pool.acquire() as conn:
            yield conn

    async def is_healthy(self) -> bool:
        """Check if database is accessible"""
        try:
            if not self.pool:
                return False
            async with self.pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False

    # User Profile Operations
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user_id"""
        query = "SELECT * FROM user_profiles WHERE user_id = $1"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else None

    async def create_user_profile(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Create new user profile"""
        columns = ['user_id'] + list(kwargs.keys())
        values = [user_id] + list(kwargs.values())
        placeholders = ', '.join(f'${i+1}' for i in range(len(values)))

        query = f"""
            INSERT INTO user_profiles ({', '.join(columns)})
            VALUES ({placeholders})
            RETURNING *
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
            return dict(row)

    async def update_user_profile(self, user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update user profile"""
        if not kwargs:
            return await self.get_user_profile(user_id)

        set_clause = ', '.join(f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys()))
        query = f"""
            UPDATE user_profiles
            SET {set_clause}
            WHERE user_id = $1
            RETURNING *
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, *kwargs.values())
            return dict(row) if row else None

    # Alert History Operations
    async def create_alert(
        self,
        user_id: str,
        alert_type: str,
        symbol: str,
        message: str,
        confidence: float,
        reasoning: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create new alert record"""
        # Get internal user UUID
        user_profile = await self.get_user_profile(user_id)
        if not user_profile:
            raise ValueError(f"User {user_id} not found")

        query = """
            INSERT INTO alert_history (user_id, alert_type, symbol, message, confidence, reasoning)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                user_profile['id'],
                alert_type,
                symbol,
                message,
                confidence,
                reasoning
            )
            return dict(row)

    async def get_user_alerts(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's alert history"""
        user_profile = await self.get_user_profile(user_id)
        if not user_profile:
            return []

        query = """
            SELECT * FROM alert_history
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_profile['id'], limit, offset)
            return [dict(row) for row in rows]

    async def update_alert_action(self, alert_id: str, action: str) -> Optional[Dict[str, Any]]:
        """Update user action on alert (acted, dismissed, ignored)"""
        query = """
            UPDATE alert_history
            SET user_action = $1
            WHERE id = $2
            RETURNING *
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, action, alert_id)
            return dict(row) if row else None

    # Voice Interaction Operations
    async def create_voice_interaction(
        self,
        user_id: str,
        transcript: str,
        response: str,
        intent: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """Record voice interaction"""
        user_profile = await self.get_user_profile(user_id)
        if not user_profile:
            raise ValueError(f"User {user_id} not found")

        query = """
            INSERT INTO voice_interactions (user_id, transcript, response, intent, duration_ms)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                user_profile['id'],
                transcript,
                response,
                intent,
                duration_ms
            )
            return dict(row)

# Singleton instance
_postgres_client: Optional[PostgresClient] = None

def get_postgres_client() -> PostgresClient:
    """Get singleton PostgreSQL client instance"""
    global _postgres_client
    if _postgres_client is None:
        raise RuntimeError("PostgreSQL client not initialized")
    return _postgres_client

def init_postgres_client(host: str, port: int, database: str, user: str, password: str) -> PostgresClient:
    """Initialize singleton PostgreSQL client"""
    global _postgres_client
    _postgres_client = PostgresClient(host, port, database, user, password)
    return _postgres_client
```

**Acceptance**:
- [ ] PostgresClient class created with connection pooling
- [ ] CRUD operations for user_profiles
- [ ] CRUD operations for alert_history
- [ ] CRUD operations for voice_interactions
- [ ] Singleton pattern for global access
- [ ] Health check method

---

### Task 1.4: Create Redis Client Module
**Estimated Effort**: 2-3 hours

**File**: `backend/app/database/redis_client.py`

```python
"""
Redis async client wrapper
"""
import redis.asyncio as redis
import json
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

class RedisClient:
    """Async Redis client wrapper"""

    def __init__(self, host: str, port: int, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Create Redis connection"""
        try:
            self.client = await redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )

            # Test connection
            await self.client.ping()
            logger.info(f"Redis connected: {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis disconnected")

    async def is_healthy(self) -> bool:
        """Check if Redis is accessible"""
        try:
            if not self.client:
                return False
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    # Market Data Cache
    async def cache_market_data(self, symbol: str, data: Dict[str, Any], ttl: int = 5):
        """Cache market data with TTL"""
        key = f"market:{symbol}"
        await self.client.setex(key, ttl, json.dumps(data))

    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached market data"""
        key = f"market:{symbol}"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    # Sentiment Cache
    async def cache_sentiment(self, symbol: str, sentiment: Dict[str, Any], ttl: int = 900):
        """Cache sentiment data with TTL (15 minutes)"""
        key = f"sentiment:{symbol}"
        await self.client.setex(key, ttl, json.dumps(sentiment))

    async def get_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached sentiment data"""
        key = f"sentiment:{symbol}"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    # Pattern Analysis Cache
    async def cache_pattern(self, symbol: str, timeframe: str, pattern: Dict[str, Any], ttl: int = 300):
        """Cache pattern analysis with TTL (5 minutes)"""
        key = f"pattern:{symbol}:{timeframe}"
        await self.client.setex(key, ttl, json.dumps(pattern))

    async def get_pattern(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get cached pattern analysis"""
        key = f"pattern:{symbol}:{timeframe}"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    # Session Management
    async def set_session(self, user_id: str, session_data: Dict[str, Any], ttl: int = 3600):
        """Set user session data"""
        key = f"session:{user_id}"
        await self.client.setex(key, ttl, json.dumps(session_data))

    async def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        key = f"session:{user_id}"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    async def delete_session(self, user_id: str):
        """Delete user session"""
        key = f"session:{user_id}"
        await self.client.delete(key)

    # Rate Limiting
    async def check_rate_limit(self, user_id: str, limit: int = 100, window: int = 60) -> bool:
        """Check if user is within rate limit"""
        key = f"ratelimit:{user_id}"
        count = await self.client.incr(key)

        if count == 1:
            await self.client.expire(key, window)

        return count <= limit

    async def get_rate_limit_count(self, user_id: str) -> int:
        """Get current rate limit count"""
        key = f"ratelimit:{user_id}"
        count = await self.client.get(key)
        return int(count) if count else 0

# Singleton instance
_redis_client: Optional[RedisClient] = None

def get_redis_client() -> RedisClient:
    """Get singleton Redis client instance"""
    global _redis_client
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client

def init_redis_client(host: str, port: int, db: int = 0) -> RedisClient:
    """Initialize singleton Redis client"""
    global _redis_client
    _redis_client = RedisClient(host, port, db)
    return _redis_client
```

**Acceptance**:
- [ ] RedisClient class created
- [ ] Market data caching methods
- [ ] Sentiment caching methods
- [ ] Pattern caching methods
- [ ] Session management methods
- [ ] Rate limiting methods
- [ ] Singleton pattern for global access

---

### Task 1.5: Create Database Models (Pydantic)
**Estimated Effort**: 2 hours

**File**: `backend/app/database/models.py`

```python
"""
Pydantic models for database entities
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserProfile(BaseModel):
    """User profile model"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    risk_tolerance: str = 'moderate'
    preferred_timeframes: List[str] = Field(default_factory=lambda: ['H4', 'D1'])
    watchlist: List[str] = Field(default_factory=lambda: ['XAUUSD', 'BTCUSD', 'ETHUSD'])
    voice_enabled: bool = True
    language: str = 'vi'
    created_at: datetime
    updated_at: datetime

class UserProfileCreate(BaseModel):
    """User profile creation model"""
    user_id: str
    risk_tolerance: Optional[str] = 'moderate'
    preferred_timeframes: Optional[List[str]] = None
    watchlist: Optional[List[str]] = None
    voice_enabled: Optional[bool] = True
    language: Optional[str] = 'vi'

class UserProfileUpdate(BaseModel):
    """User profile update model"""
    risk_tolerance: Optional[str] = None
    preferred_timeframes: Optional[List[str]] = None
    watchlist: Optional[List[str]] = None
    voice_enabled: Optional[bool] = None

class AlertHistory(BaseModel):
    """Alert history model"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    alert_type: str
    symbol: str
    message: str
    confidence: float
    reasoning: Optional[dict] = None
    user_action: Optional[str] = None
    created_at: datetime

class AlertCreate(BaseModel):
    """Alert creation model"""
    user_id: str
    alert_type: str
    symbol: str
    message: str
    confidence: float
    reasoning: Optional[dict] = None

class VoiceInteraction(BaseModel):
    """Voice interaction model"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    transcript: str
    response: str
    intent: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime

class VoiceInteractionCreate(BaseModel):
    """Voice interaction creation model"""
    user_id: str
    transcript: str
    response: str
    intent: Optional[str] = None
    duration_ms: Optional[int] = None
```

**Acceptance**:
- [ ] Pydantic models for all database entities
- [ ] Create and Update models for mutations
- [ ] Type hints and validation

---

### Task 1.6: Extend Backend Configuration
**Estimated Effort**: 1 hour

**File**: `backend/app/config.py` (extend existing)

```python
# Add to existing config.py

class CapitalCompanionConfig:
    """Capital Companion specific configuration"""
    # Database
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', 5432))
    DB_NAME: str = os.getenv('DB_NAME', 'capital_companion')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')

    # Redis
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB: int = int(os.getenv('REDIS_DB', 0))

    # TwelveData
    TWELVEDATA_KEY: str = os.getenv('TWELVEDATA_KEY', '')

    # OpenAI
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')

    # VieNeu TTS
    VIENEU_TTS_URL: str = os.getenv('VIENEU_TTS_URL', '')

    # NewsAPI
    NEWSAPI_KEY: str = os.getenv('NEWSAPI_KEY', '')

    # Monitoring
    SENTRY_DSN: str = os.getenv('SENTRY_DSN', '')
    LOGTAIL_TOKEN: str = os.getenv('LOGTAIL_TOKEN', '')

# Merge with existing config
capital_config = CapitalCompanionConfig()
```

**Acceptance**:
- [ ] Configuration extended with database settings
- [ ] Environment variables for all external services
- [ ] Monitoring configuration added

---

### Task 1.7: Integrate Database into Backend Lifespan
**Estimated Effort**: 2-3 hours

**File**: `backend/app/main.py` (extend existing)

```python
# Update imports
from app.database.postgres_client import init_postgres_client, get_postgres_client
from app.database.redis_client import init_redis_client, get_redis_client
from app.config import capital_config

# Add to global instances
postgres_client = None
redis_client = None

# Update lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    Initialize and cleanup resources
    """
    global mt5_manager, session_manager, reconnection_manager, command_processor, cleanup_task
    global postgres_client, redis_client  # Add database clients

    logger.info("Starting Capital Companion Server...")

    # Initialize PostgreSQL
    try:
        postgres_client = init_postgres_client(
            host=capital_config.DB_HOST,
            port=capital_config.DB_PORT,
            database=capital_config.DB_NAME,
            user=capital_config.DB_USER,
            password=capital_config.DB_PASSWORD
        )
        await postgres_client.connect()
        logger.info("PostgreSQL initialized")
    except Exception as e:
        logger.error(f"PostgreSQL initialization failed: {e}")
        # Continue without database for health check access

    # Initialize Redis
    try:
        redis_client = init_redis_client(
            host=capital_config.REDIS_HOST,
            port=capital_config.REDIS_PORT,
            db=capital_config.REDIS_DB
        )
        await redis_client.connect()
        logger.info("Redis initialized")
    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")
        # Continue without Redis

    # ... existing MT5 initialization code ...

    # Store in app state
    app.state.postgres_client = postgres_client
    app.state.redis_client = redis_client

    yield

    # Shutdown
    logger.info("Shutting down server...")

    if postgres_client:
        await postgres_client.disconnect()

    if redis_client:
        await redis_client.disconnect()

    # ... existing MT5 shutdown code ...

# Update health check
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    postgres_healthy = await postgres_client.is_healthy() if postgres_client else False
    redis_healthy = await redis_client.is_healthy() if redis_client else False
    mt5_healthy = mt5_manager.is_connected() if mt5_manager else False

    overall_status = "healthy" if all([postgres_healthy, redis_healthy]) else "degraded"

    return {
        "status": overall_status,
        "services": {
            "postgres": postgres_healthy,
            "redis": redis_healthy,
            "mt5": mt5_healthy
        },
        "connected_clients": len(session_manager.sessions) if session_manager else 0
    }
```

**Acceptance**:
- [ ] PostgreSQL initialized on startup
- [ ] Redis initialized on startup
- [ ] Proper shutdown handling
- [ ] Enhanced health check with database status

---

### Task 1.8: Update Requirements
**Estimated Effort**: 15 minutes

**File**: `backend/requirements.txt` (extend)

```txt
# Existing dependencies
MetaTrader5==5.0.45; sys_platform == 'win32'
python-dotenv==1.0.1
python-json-logger>=2.0.70
pytest==7.4.0
pytest-asyncio==0.21.0
fastapi==0.104.0
python-socketio==5.10.0
uvicorn[standard]==0.24.0
numpy<2

# NEW: Database & Cache
asyncpg==0.30.0
redis==5.2.1

# NEW: Data validation
pydantic==2.10.6
pydantic-settings==2.7.0
```

**Acceptance**:
- [ ] New dependencies added to requirements.txt

---

### Task 1.9: Test Database Integration
**Estimated Effort**: 2-3 hours

**File**: `backend/tests/test_database.py` (create)

```python
"""
Test database integration
"""
import pytest
import asyncio
from app.database.postgres_client import PostgresClient
from app.database.redis_client import RedisClient

@pytest.mark.asyncio
async def test_postgres_connection():
    """Test PostgreSQL connection"""
    client = PostgresClient(
        host='localhost',
        port=5432,
        database='capital_companion',
        user='postgres',
        password='changeme'
    )

    await client.connect()
    assert await client.is_healthy()
    await client.disconnect()

@pytest.mark.asyncio
async def test_redis_connection():
    """Test Redis connection"""
    client = RedisClient(host='localhost', port=6379)

    await client.connect()
    assert await client.is_healthy()
    await client.disconnect()

@pytest.mark.asyncio
async def test_user_profile_crud():
    """Test user profile CRUD operations"""
    client = PostgresClient(
        host='localhost',
        port=5432,
        database='capital_companion',
        user='postgres',
        password='changeme'
    )

    await client.connect()

    # Create
    profile = await client.create_user_profile(
        user_id='test_user_123',
        risk_tolerance='aggressive'
    )
    assert profile['user_id'] == 'test_user_123'

    # Read
    profile = await client.get_user_profile('test_user_123')
    assert profile is not None

    # Update
    updated = await client.update_user_profile(
        'test_user_123',
        watchlist=['BTCUSD', 'ETHUSD']
    )
    assert 'BTCUSD' in updated['watchlist']

    await client.disconnect()
```

**Acceptance**:
- [ ] Tests pass for PostgreSQL connection
- [ ] Tests pass for Redis connection
- [ ] Tests pass for user profile CRUD

---

## DEPLOYMENT

### Local Development
```bash
# Start services
cd backend
docker-compose up -d postgres redis

# Run backend (without Docker)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

### Production (Docker Compose)
```bash
cd backend
docker-compose up -d
```

---

## ACCEPTANCE CRITERIA

- [ ] Docker Compose configuration created
- [ ] PostgreSQL container running
- [ ] Redis container running
- [ ] Database migration script executed successfully
- [ ] PostgresClient module created and tested
- [ ] RedisClient module created and tested
- [ ] Backend connects to both databases on startup
- [ ] Health check endpoint shows database status
- [ ] All unit tests pass

---

## VERIFICATION STEPS

1. **Start Services**:
   ```bash
   docker-compose up -d
   ```

2. **Check Container Health**:
   ```bash
   docker-compose ps
   # All should show "healthy"
   ```

3. **Verify Database**:
   ```bash
   docker exec -it capital_companion_postgres psql -U postgres -d capital_companion -c "\dt"
   # Should show: user_profiles, alert_history, voice_interactions
   ```

4. **Verify Redis**:
   ```bash
   docker exec -it capital_companion_redis redis-cli ping
   # Should return: PONG
   ```

5. **Start Backend**:
   ```bash
   python -m app.main
   ```

6. **Check Health Endpoint**:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "healthy", "services": {"postgres": true, "redis": true, ...}}
   ```

---

## NEXT PHASE

**Phase 2**: Market Data Service (TwelveData WebSocket integration)

See `phase-02-market-data-service.md`
