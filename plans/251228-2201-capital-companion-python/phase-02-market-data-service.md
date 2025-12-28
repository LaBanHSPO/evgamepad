# Phase 2: Market Data Service (TwelveData WebSocket)

**Duration**: Week 2
**Goal**: Real-time Gold + Crypto prices via TwelveData WebSocket
**Prerequisites**: Phase 1 complete (PostgreSQL + Redis operational)
**Status**: Not Started

---

## OVERVIEW

Integrate TwelveData WebSocket for real-time market data (XAUUSD, BTCUSD, ETHUSD, BNBUSD). Cache prices in Redis, broadcast to Socket.IO clients, handle reconnection.

### Dependencies
- TwelveData Pro account ($79/mo)
- `websockets` Python library
- Redis client (from Phase 1)

---

## TASK BREAKDOWN

### Task 2.1: Install WebSocket Library
**Estimated Effort**: 15 minutes

**Update** `backend/requirements.txt`:
```txt
# Add to existing requirements
websockets==12.0
aiohttp==3.10.11  # For HTTP fallback
```

**Install**:
```bash
pip install websockets aiohttp
```

**Acceptance**:
- [ ] `websockets` library installed
- [ ] Import test passes: `import websockets`

---

### Task 2.2: Create Market Data Service
**Estimated Effort**: 4-5 hours

**File**: `backend/app/capital_companion/market_data_service.py`

```python
"""
TwelveData WebSocket client for real-time market data
"""
import asyncio
import websockets
import json
import logging
from typing import List, Optional, Callable
from app.database.redis_client import get_redis_client
from app.config import capital_config

logger = logging.getLogger(__name__)

class MarketDataService:
    """TwelveData WebSocket client with auto-reconnection"""

    def __init__(self, symbols: List[str], api_key: str):
        self.symbols = symbols
        self.api_key = api_key
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.reconnect_delay = 5
        self.on_update_callback: Optional[Callable] = None

    def set_update_callback(self, callback: Callable):
        """Set callback for market data updates"""
        self.on_update_callback = callback

    async def connect(self):
        """Connect to TwelveData WebSocket"""
        ws_url = f"wss://ws.twelvedata.com/v1/quotes/price?apikey={self.api_key}"

        try:
            self.ws = await websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=10
            )
            logger.info(f"TwelveData WebSocket connected: {ws_url}")

            # Subscribe to symbols
            await self._subscribe()

        except Exception as e:
            logger.error(f"Failed to connect to TwelveData WebSocket: {e}")
            raise

    async def _subscribe(self):
        """Subscribe to symbols"""
        if not self.ws:
            return

        subscribe_msg = {
            "action": "subscribe",
            "params": {
                "symbols": ",".join(self.symbols)
            }
        }

        await self.ws.send(json.dumps(subscribe_msg))
        logger.info(f"Subscribed to symbols: {self.symbols}")

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)

            # Check message type
            if data.get("event") == "subscribe-status":
                logger.info(f"Subscription status: {data}")
                return

            if data.get("event") == "price":
                # Market data update
                symbol = data.get("symbol")
                price = float(data.get("price", 0))
                timestamp = data.get("timestamp")

                market_update = {
                    "symbol": symbol,
                    "price": price,
                    "timestamp": timestamp
                }

                # Cache in Redis (5s TTL)
                redis_client = get_redis_client()
                await redis_client.cache_market_data(symbol, market_update, ttl=5)

                # Trigger callback (broadcast to Socket.IO)
                if self.on_update_callback:
                    await self.on_update_callback(market_update)

                logger.debug(f"Market update: {symbol} = ${price}")

        except Exception as e:
            logger.error(f"Error handling message: {e}, message: {message}")

    async def start(self):
        """Start WebSocket listener with auto-reconnect"""
        self.running = True

        while self.running:
            try:
                await self.connect()

                # Listen for messages
                async for message in self.ws:
                    await self._handle_message(message)

            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
                if self.running:
                    logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                    await asyncio.sleep(self.reconnect_delay)

            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if self.running:
                    logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                    await asyncio.sleep(self.reconnect_delay)

    async def stop(self):
        """Stop WebSocket listener"""
        self.running = False
        if self.ws:
            await self.ws.close()
            logger.info("TwelveData WebSocket closed")

    async def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.ws is not None and self.ws.open

    async def get_cached_price(self, symbol: str) -> Optional[dict]:
        """Get cached price from Redis"""
        redis_client = get_redis_client()
        return await redis_client.get_market_data(symbol)

# Singleton instance
_market_data_service: Optional[MarketDataService] = None

def get_market_data_service() -> MarketDataService:
    """Get singleton market data service"""
    global _market_data_service
    if _market_data_service is None:
        raise RuntimeError("Market data service not initialized")
    return _market_data_service

def init_market_data_service(symbols: List[str], api_key: str) -> MarketDataService:
    """Initialize singleton market data service"""
    global _market_data_service
    _market_data_service = MarketDataService(symbols, api_key)
    return _market_data_service
```

**Acceptance**:
- [ ] MarketDataService class created
- [ ] WebSocket connection with auto-reconnect
- [ ] Symbol subscription logic
- [ ] Message handling with Redis caching
- [ ] Callback mechanism for broadcasts
- [ ] Singleton pattern

---

### Task 2.3: Create Market Data Types
**Estimated Effort**: 1 hour

**File**: `backend/app/models/market_data.py`

```python
"""
Market data types and models
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MarketUpdate(BaseModel):
    """Real-time market data update"""
    symbol: str
    price: float
    timestamp: str

class MarketSubscription(BaseModel):
    """Client subscription to symbols"""
    symbols: List[str] = Field(min_length=1, max_length=10)

class MarketDataCache(BaseModel):
    """Cached market data"""
    symbol: str
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    timestamp: datetime
```

**Acceptance**:
- [ ] Pydantic models for market data
- [ ] Validation for symbol subscriptions

---

### Task 2.4: Create Market Events Handler
**Estimated Effort**: 2-3 hours

**File**: `backend/app/events/market_events.py`

```python
"""
Socket.IO events for market data
"""
import logging
from socketio import AsyncServer
from app.sio import sio
from app.capital_companion.market_data_service import get_market_data_service
from app.session_manager import SessionManager
from app.models.market_data import MarketSubscription, MarketUpdate
from pydantic import ValidationError

logger = logging.getLogger(__name__)

# Global references (injected from main.py)
session_manager: SessionManager = None

@sio.event
async def market_subscribe(sid, data):
    """
    Client subscribes to market data for specific symbols

    Event: market:subscribe
    Payload: {
        "symbols": ["XAUUSD", "BTCUSD", "ETHUSD"]
    }
    """
    try:
        # Validate input
        subscription = MarketSubscription(**data)

        # Store subscription in session
        if session_manager:
            session = session_manager.get_session(sid)
            if session:
                session['market_symbols'] = subscription.symbols
                logger.info(f"Client {sid} subscribed to: {subscription.symbols}")

                # Send current cached prices
                market_service = get_market_data_service()
                for symbol in subscription.symbols:
                    cached = await market_service.get_cached_price(symbol)
                    if cached:
                        await sio.emit('market:update', cached, room=sid)

                await sio.emit('market:subscribe_success', {
                    'symbols': subscription.symbols
                }, room=sid)
            else:
                await sio.emit('error', {
                    'message': 'Session not found'
                }, room=sid)

    except ValidationError as e:
        logger.error(f"Invalid market subscription: {e}")
        await sio.emit('error', {
            'message': 'Invalid subscription data',
            'details': str(e)
        }, room=sid)
    except Exception as e:
        logger.error(f"Error in market_subscribe: {e}")
        await sio.emit('error', {
            'message': 'Subscription failed'
        }, room=sid)

@sio.event
async def market_unsubscribe(sid, data):
    """
    Client unsubscribes from market data

    Event: market:unsubscribe
    Payload: {
        "symbols": ["XAUUSD"]
    }
    """
    try:
        subscription = MarketSubscription(**data)

        if session_manager:
            session = session_manager.get_session(sid)
            if session and 'market_symbols' in session:
                # Remove symbols from subscription
                current = set(session.get('market_symbols', []))
                current -= set(subscription.symbols)
                session['market_symbols'] = list(current)

                logger.info(f"Client {sid} unsubscribed from: {subscription.symbols}")
                await sio.emit('market:unsubscribe_success', {
                    'symbols': subscription.symbols
                }, room=sid)

    except Exception as e:
        logger.error(f"Error in market_unsubscribe: {e}")

async def broadcast_market_update(update: dict):
    """
    Broadcast market update to all subscribed clients
    Called by MarketDataService callback
    """
    symbol = update['symbol']

    # Get all sessions subscribed to this symbol
    if session_manager:
        for sid, session in session_manager.sessions.items():
            subscribed_symbols = session.get('market_symbols', [])
            if symbol in subscribed_symbols:
                await sio.emit('market:update', update, room=sid)
```

**Acceptance**:
- [ ] `market:subscribe` event handler
- [ ] `market:unsubscribe` event handler
- [ ] Broadcast function for market updates
- [ ] Session-based symbol tracking
- [ ] Error handling

---

### Task 2.5: Integrate into Backend Startup
**Estimated Effort**: 2 hours

**Update** `backend/app/main.py`:

```python
# Add imports
from app.capital_companion.market_data_service import (
    init_market_data_service,
    get_market_data_service
)
from app.events import market_events

# Add global instance
market_data_service = None

# Update lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    global postgres_client, redis_client, market_data_service
    # ... existing initialization ...

    # Initialize Market Data Service
    try:
        market_data_service = init_market_data_service(
            symbols=['XAUUSD', 'BTCUSD', 'ETHUSD', 'BNBUSD'],
            api_key=capital_config.TWELVEDATA_KEY
        )

        # Set broadcast callback
        market_data_service.set_update_callback(market_events.broadcast_market_update)

        # Start WebSocket listener
        asyncio.create_task(market_data_service.start())
        logger.info("Market data service started")

    except Exception as e:
        logger.error(f"Market data service initialization failed: {e}")

    # Inject dependencies into events
    market_events.session_manager = session_manager

    # Store in app state
    app.state.market_data_service = market_data_service

    yield

    # Shutdown
    if market_data_service:
        await market_data_service.stop()

    # ... existing shutdown code ...

# Update health check
@app.get("/health")
async def health_check():
    market_connected = await market_data_service.is_connected() if market_data_service else False

    return {
        "status": overall_status,
        "services": {
            "postgres": postgres_healthy,
            "redis": redis_healthy,
            "mt5": mt5_healthy,
            "twelvedata": market_connected  # Add TwelveData status
        },
        "connected_clients": len(session_manager.sessions) if session_manager else 0
    }
```

**Acceptance**:
- [ ] Market data service initialized on startup
- [ ] WebSocket listener runs in background task
- [ ] Broadcast callback connected
- [ ] Health check includes TwelveData status

---

### Task 2.6: Update Frontend Integration
**Estimated Effort**: 2 hours

**Update** `src/context/SocketContext.tsx`:

```typescript
// Add market data event listeners
useEffect(() => {
  if (!socket) return;

  // Market data update
  socket.on('market:update', (data: { symbol: string; price: number; timestamp: string }) => {
    console.log('Market update:', data);
    // Update state or dispatch to context
  });

  // Subscription success
  socket.on('market:subscribe_success', (data: { symbols: string[] }) => {
    console.log('Subscribed to:', data.symbols);
  });

  return () => {
    socket.off('market:update');
    socket.off('market:subscribe_success');
  };
}, [socket]);

// Subscribe to symbols
const subscribeToMarket = (symbols: string[]) => {
  socket?.emit('market:subscribe', { symbols });
};
```

**Update** `src/pages/Monitor1.tsx`:

```typescript
const { socket } = useSocket();

useEffect(() => {
  // Subscribe to market data on mount
  if (socket) {
    socket.emit('market:subscribe', {
      symbols: ['XAUUSD', 'BTCUSD', 'ETHUSD']
    });
  }
}, [socket]);
```

**Acceptance**:
- [ ] Frontend subscribes to market data on mount
- [ ] Market updates received and logged
- [ ] Real-time prices displayed in UI

---

### Task 2.7: Create REST API Fallback
**Estimated Effort**: 2 hours

**File**: `backend/app/capital_companion/market_data_service.py` (extend)

```python
import aiohttp

class MarketDataService:
    # ... existing code ...

    async def fetch_rest_api(self, symbol: str) -> Optional[dict]:
        """
        Fallback: Fetch price via REST API if WebSocket fails
        """
        url = "https://api.twelvedata.com/price"
        params = {
            "symbol": symbol,
            "apikey": self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data.get('price', 0))

                        market_update = {
                            "symbol": symbol,
                            "price": price,
                            "timestamp": data.get('timestamp', str(asyncio.get_event_loop().time()))
                        }

                        # Cache in Redis
                        redis_client = get_redis_client()
                        await redis_client.cache_market_data(symbol, market_update, ttl=5)

                        return market_update

        except Exception as e:
            logger.error(f"REST API fallback failed for {symbol}: {e}")
            return None

    async def get_price(self, symbol: str) -> Optional[dict]:
        """
        Get price (cached or fetch from API)
        """
        # Try cache first
        cached = await self.get_cached_price(symbol)
        if cached:
            return cached

        # Fallback to REST API
        return await self.fetch_rest_api(symbol)
```

**Acceptance**:
- [ ] REST API fallback implemented
- [ ] Fallback used when WebSocket down
- [ ] Redis caching for REST responses

---

### Task 2.8: Add Market Data Endpoint
**Estimated Effort**: 1 hour

**Update** `backend/app/main.py`:

```python
from fastapi import HTTPException

@app.get("/api/market/{symbol}")
async def get_market_price(symbol: str):
    """
    Get current market price for symbol
    """
    if not market_data_service:
        raise HTTPException(status_code=503, detail="Market data service unavailable")

    price_data = await market_data_service.get_price(symbol.upper())
    if not price_data:
        raise HTTPException(status_code=404, detail=f"Price not found for {symbol}")

    return price_data

@app.get("/api/market")
async def get_all_market_prices():
    """
    Get all cached market prices
    """
    if not market_data_service:
        raise HTTPException(status_code=503, detail="Market data service unavailable")

    symbols = market_data_service.symbols
    prices = {}

    for symbol in symbols:
        price_data = await market_data_service.get_cached_price(symbol)
        if price_data:
            prices[symbol] = price_data

    return prices
```

**Acceptance**:
- [ ] REST endpoint for single symbol price
- [ ] REST endpoint for all prices
- [ ] Proper error handling

---

### Task 2.9: Testing
**Estimated Effort**: 3 hours

**File**: `backend/tests/test_market_data.py`

```python
import pytest
import asyncio
from app.capital_companion.market_data_service import MarketDataService

@pytest.mark.asyncio
async def test_market_data_connection():
    """Test TwelveData WebSocket connection"""
    service = MarketDataService(
        symbols=['BTCUSD'],
        api_key='test_key'
    )

    # Note: This requires valid API key and will fail without it
    # Use mocking for CI/CD
    # await service.connect()
    # assert await service.is_connected()
    # await service.stop()

@pytest.mark.asyncio
async def test_rest_api_fallback():
    """Test REST API fallback"""
    service = MarketDataService(
        symbols=['BTCUSD'],
        api_key='test_key'
    )

    # Test fallback (requires valid API key)
    # price = await service.fetch_rest_api('BTCUSD')
    # assert price is not None
    # assert 'price' in price

@pytest.mark.asyncio
async def test_cached_price():
    """Test Redis caching"""
    from app.database.redis_client import init_redis_client

    redis_client = init_redis_client('localhost', 6379)
    await redis_client.connect()

    # Cache test data
    test_data = {
        'symbol': 'BTCUSD',
        'price': 50000.0,
        'timestamp': '2025-01-01T00:00:00Z'
    }
    await redis_client.cache_market_data('BTCUSD', test_data, ttl=5)

    # Retrieve
    cached = await redis_client.get_market_data('BTCUSD')
    assert cached is not None
    assert cached['price'] == 50000.0

    await redis_client.disconnect()
```

**Manual Testing**:
```bash
# Start backend
python -m app.main

# In another terminal, test WebSocket events
python
>>> import socketio
>>> sio = socketio.AsyncClient()
>>> await sio.connect('http://localhost:8000')
>>> await sio.emit('market:subscribe', {'symbols': ['BTCUSD', 'XAUUSD']})
>>> # Should receive market:update events
```

**Acceptance**:
- [ ] Unit tests pass
- [ ] Manual Socket.IO test successful
- [ ] Frontend receives real-time updates

---

## VERIFICATION STEPS

1. **Start Backend**:
   ```bash
   python -m app.main
   ```

2. **Check Logs**:
   ```
   Should see: "TwelveData WebSocket connected"
   Should see: "Subscribed to symbols: ['XAUUSD', 'BTCUSD', 'ETHUSD', 'BNBUSD']"
   Should see: "Market update: BTCUSD = $..."
   ```

3. **Test Health Endpoint**:
   ```bash
   curl http://localhost:8000/health
   # "twelvedata": true
   ```

4. **Test REST API**:
   ```bash
   curl http://localhost:8000/api/market/BTCUSD
   # {"symbol": "BTCUSD", "price": ..., "timestamp": "..."}
   ```

5. **Test Frontend**:
   - Open Monitor 1
   - Check browser console for "Market update:" logs
   - Verify prices update every 5 seconds

---

## ACCEPTANCE CRITERIA

- [ ] TwelveData WebSocket connects successfully
- [ ] Symbols subscribed (XAUUSD, BTCUSD, ETHUSD, BNBUSD)
- [ ] Market updates received and cached in Redis (5s TTL)
- [ ] Socket.IO events broadcast to subscribed clients
- [ ] Frontend receives real-time price updates
- [ ] Auto-reconnection works after disconnect
- [ ] REST API fallback functional
- [ ] Health check shows TwelveData status
- [ ] Latency < 1 second from TwelveData → UI

---

## NEXT PHASE

**Phase 3**: Voice Interaction (Whisper + VieNeu-TTS)

See `phase-03-voice-interaction.md`
