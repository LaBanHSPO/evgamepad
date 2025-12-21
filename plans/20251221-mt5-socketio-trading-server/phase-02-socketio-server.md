# Phase 2: Socket.IO Server Setup

**Status**: Ready after Phase 1
**Dependencies**: Phase 1 (MT5 Foundation) completed
**Prerequisites**: MT5 connection manager tested and working

---

## OBJECTIVES

Establish real-time communication infrastructure with:
- FastAPI + python-socketio server
- Event handlers for trading commands
- Input validation & sanitization
- Session state management
- Connection lifecycle handling

---

## DELIVERABLES

### 1. Socket.IO Server (`app/main.py`)

**Responsibilities**:
- Initialize FastAPI application
- Configure python-socketio AsyncServer
- Setup ASGI application wrapper
- Define lifespan events
- Configure CORS (VPN network)

**Implementation**:
```python
# app/main.py
from fastapi import FastAPI
from python_socketio import AsyncServer, ASGIApp
from contextlib import asynccontextmanager
import logging

from app.config import Config
from app.logging_config import setup_logging
from app.mt5.connection_manager import MT5ConnectionManager
from app.session_manager import SessionManager

# Initialize logging
logger = setup_logging(Config.DEBUG)

# Global instances
mt5_manager = None
session_manager = None

# Socket.IO Server Configuration
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # VPN network - adjust for production
    ping_interval=25,          # Heartbeat every 25s
    ping_timeout=60,           # Disconnect after 60s no response
    max_http_buffer_size=1e6,  # 1MB max message size
    logger=logger,
    engineio_logger=logger if Config.DEBUG else False,
)

# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global mt5_manager, session_manager

    logger.info("Starting MT5 Socket.IO Trading Server...")

    # Initialize MT5 connection
    mt5_manager = MT5ConnectionManager(
        check_interval=Config.MT5_HEALTH_INTERVAL,
        timeout=Config.MT5_CONN_TIMEOUT
    )

    if not mt5_manager.connect():
        logger.error("Failed to connect to MT5 terminal")
        raise RuntimeError("MT5 connection failed")

    logger.info("MT5 connection established")

    # Initialize session manager
    session_manager = SessionManager()

    # Store in app state
    app.state.mt5_manager = mt5_manager
    app.state.session_manager = session_manager

    yield

    # Shutdown
    logger.info("Shutting down server...")
    if mt5_manager:
        mt5_manager.disconnect()
    logger.info("Server shutdown complete")

app = FastAPI(
    title="MT5 Trading Server",
    version="1.0.0",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if mt5_manager and mt5_manager.is_connected() else "unhealthy",
        "mt5_connected": mt5_manager.is_connected() if mt5_manager else False,
        "connected_clients": len(session_manager.sessions) if session_manager else 0,
    }

# Wrap with Socket.IO
asgi_app = ASGIApp(sio, app)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        asgi_app,
        host=Config.SOCKETIO_HOST,
        port=Config.SOCKETIO_PORT,
        log_level="debug" if Config.DEBUG else "info"
    )
```

**Key Features**:
- Async context manager for startup/shutdown
- Global MT5 manager instance
- Health check endpoint
- Configurable ping/timeout
- Proper logging integration

---

### 2. Event Handlers (`app/events/trading_events.py`)

**Responsibilities**:
- Handle Socket.IO connection/disconnection
- Register trading command handlers
- Validate incoming commands
- Emit responses and errors

**Implementation**:
```python
# app/events/trading_events.py
import logging
from typing import Dict, Any
from datetime import datetime

from app.main import sio, mt5_manager, session_manager
from app.validation import (
    validate_login_command,
    validate_order_command,
    validate_modify_command,
    validate_close_command,
)
from app.models.responses import (
    success_response,
    error_response,
    ErrorCode,
)

logger = logging.getLogger(__name__)

# ============================================================================
# CONNECTION LIFECYCLE
# ============================================================================

@sio.event
async def connect(sid: str, environ: Dict[str, Any]):
    """Handle client connection"""
    remote_addr = environ.get('REMOTE_ADDR', 'unknown')
    logger.info(f"Client {sid} connected from {remote_addr}")

    # Initialize session
    session_manager.create_session(sid, {
        'connected_at': datetime.utcnow(),
        'remote_addr': remote_addr,
        'mt5_logged_in': False,
        'pending_orders': {},
    })

    # Send welcome message
    await sio.emit('connected', {
        'message': 'Connected to MT5 Trading Server',
        'session_id': sid,
        'server_time': datetime.utcnow().isoformat(),
    }, to=sid)

@sio.event
async def disconnect(sid: str):
    """Handle client disconnection"""
    logger.info(f"Client {sid} disconnected")

    # Cleanup session
    session = session_manager.get_session(sid)
    if session:
        pending = session.get('pending_orders', {})
        if pending:
            logger.warning(f"Client {sid} disconnected with {len(pending)} pending orders")

    session_manager.remove_session(sid)

# ============================================================================
# TRADING COMMANDS
# ============================================================================

@sio.event
async def login(sid: str, data: Dict[str, Any]):
    """
    Handle MT5 login command

    Payload:
        {
            "account": 12345678,
            "password": "password",
            "server": "BrokerServer-Demo"
        }
    """
    logger.info(f"Login request from {sid}")

    try:
        # Validate
        is_valid, error_msg = validate_login_command(data)
        if not is_valid:
            await sio.emit('error', error_response(
                ErrorCode.VALIDATION_ERROR,
                error_msg
            ), to=sid)
            return

        # Login to MT5
        account_info = mt5_manager.login_account(
            data['account'],
            data['password'],
            data['server']
        )

        # Update session
        session = session_manager.get_session(sid)
        if session:
            session['mt5_logged_in'] = True
            session['account'] = data['account']

        # Send success
        await sio.emit('login_result', success_response({
            'account_info': {
                'login': account_info.login,
                'name': account_info.name,
                'server': account_info.server,
                'currency': account_info.currency,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'leverage': account_info.leverage,
            }
        }), to=sid)

        logger.info(f"Client {sid} logged in as {data['account']}")

    except Exception as e:
        logger.exception(f"Login failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Login failed: {str(e)}"
        ), to=sid)

@sio.event
async def buy(sid: str, data: Dict[str, Any]):
    """
    Handle buy market order

    Payload:
        {
            "symbol": "EURUSD",
            "volume": 0.01,
            "sl": 1.0800,  // optional
            "tp": 1.0900   // optional
        }
    """
    logger.info(f"Buy order from {sid}: {data.get('symbol')} {data.get('volume')}")

    try:
        # Validate
        is_valid, error_msg = validate_order_command(data)
        if not is_valid:
            await sio.emit('error', error_response(
                ErrorCode.VALIDATION_ERROR,
                error_msg
            ), to=sid)
            return

        # Check MT5 login
        session = session_manager.get_session(sid)
        if not session or not session.get('mt5_logged_in'):
            await sio.emit('error', error_response(
                ErrorCode.MT5_NOT_CONNECTED,
                "Not logged in to MT5"
            ), to=sid)
            return

        # Place order via MT5 manager
        # (Will be implemented in Phase 3 - Command Integration)
        # For now, emit placeholder response
        await sio.emit('order_result', success_response({
            'ticket': 0,  # Placeholder
            'symbol': data['symbol'],
            'volume': data['volume'],
            'message': 'Phase 2: Event handler registered, MT5 integration pending'
        }), to=sid)

    except Exception as e:
        logger.exception(f"Buy order failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Order failed: {str(e)}"
        ), to=sid)

@sio.event
async def sell(sid: str, data: Dict[str, Any]):
    """
    Handle sell market order

    Payload:
        {
            "symbol": "EURUSD",
            "volume": 0.01,
            "sl": 1.0900,  // optional
            "tp": 1.0800   // optional
        }
    """
    logger.info(f"Sell order from {sid}: {data.get('symbol')} {data.get('volume')}")

    try:
        # Validate
        is_valid, error_msg = validate_order_command(data)
        if not is_valid:
            await sio.emit('error', error_response(
                ErrorCode.VALIDATION_ERROR,
                error_msg
            ), to=sid)
            return

        # Check MT5 login
        session = session_manager.get_session(sid)
        if not session or not session.get('mt5_logged_in'):
            await sio.emit('error', error_response(
                ErrorCode.MT5_NOT_CONNECTED,
                "Not logged in to MT5"
            ), to=sid)
            return

        # Placeholder (Phase 3)
        await sio.emit('order_result', success_response({
            'ticket': 0,
            'symbol': data['symbol'],
            'volume': data['volume'],
            'message': 'Phase 2: Event handler registered'
        }), to=sid)

    except Exception as e:
        logger.exception(f"Sell order failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Order failed: {str(e)}"
        ), to=sid)

@sio.event
async def modify(sid: str, data: Dict[str, Any]):
    """
    Handle modify position TP/SL

    Payload:
        {
            "ticket": 123456,
            "sl": 1.0810,  // optional
            "tp": 1.0910   // optional
        }
    """
    logger.info(f"Modify request from {sid}: ticket={data.get('ticket')}")

    try:
        # Validate
        is_valid, error_msg = validate_modify_command(data)
        if not is_valid:
            await sio.emit('error', error_response(
                ErrorCode.VALIDATION_ERROR,
                error_msg
            ), to=sid)
            return

        # Placeholder (Phase 3)
        await sio.emit('modify_result', success_response({
            'ticket': data['ticket'],
            'sl': data.get('sl'),
            'tp': data.get('tp'),
            'message': 'Phase 2: Event handler registered'
        }), to=sid)

    except Exception as e:
        logger.exception(f"Modify failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Modify failed: {str(e)}"
        ), to=sid)

@sio.event
async def close(sid: str, data: Dict[str, Any]):
    """
    Handle close position

    Payload:
        {
            "ticket": 123456,
            "volume": 0.01  // optional, full close if omitted
        }
    """
    logger.info(f"Close request from {sid}: ticket={data.get('ticket')}")

    try:
        # Validate
        is_valid, error_msg = validate_close_command(data)
        if not is_valid:
            await sio.emit('error', error_response(
                ErrorCode.VALIDATION_ERROR,
                error_msg
            ), to=sid)
            return

        # Placeholder (Phase 3)
        await sio.emit('close_result', success_response({
            'ticket': data['ticket'],
            'volume': data.get('volume', 'full'),
            'message': 'Phase 2: Event handler registered'
        }), to=sid)

    except Exception as e:
        logger.exception(f"Close failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Close failed: {str(e)}"
        ), to=sid)
```

**Key Features**:
- Connection/disconnection lifecycle
- Session initialization
- Command validation before processing
- Error handling with structured responses
- Placeholders for MT5 integration (Phase 3)

---

### 3. Input Validation (`app/validation.py`)

**Responsibilities**:
- Validate command structure
- Check required fields
- Validate data types
- Range validation

**Implementation**:
```python
# app/validation.py
from typing import Dict, Any, Tuple

def validate_login_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate login command payload"""
    required = ['account', 'password', 'server']

    # Check required fields
    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Type validation
    if not isinstance(data['account'], int):
        return False, "Account must be an integer"

    if not isinstance(data['password'], str) or not data['password']:
        return False, "Password must be a non-empty string"

    if not isinstance(data['server'], str) or not data['server']:
        return False, "Server must be a non-empty string"

    return True, ""

def validate_order_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate buy/sell order command"""
    required = ['symbol', 'volume']

    # Check required fields
    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Symbol validation
    if not isinstance(data['symbol'], str) or not data['symbol']:
        return False, "Symbol must be a non-empty string"

    # Volume validation
    try:
        volume = float(data['volume'])
        if volume <= 0:
            return False, "Volume must be positive"
        if volume > 100:  # Sanity check
            return False, "Volume exceeds maximum (100 lots)"
    except (ValueError, TypeError):
        return False, "Volume must be a number"

    # Optional: SL/TP validation
    if 'sl' in data:
        try:
            float(data['sl'])
        except (ValueError, TypeError):
            return False, "SL must be a number"

    if 'tp' in data:
        try:
            float(data['tp'])
        except (ValueError, TypeError):
            return False, "TP must be a number"

    return True, ""

def validate_modify_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate modify position command"""
    required = ['ticket']

    # Check required fields
    if 'ticket' not in data:
        return False, "Missing required field: ticket"

    # Ticket validation
    try:
        int(data['ticket'])
    except (ValueError, TypeError):
        return False, "Ticket must be an integer"

    # At least one modification
    if 'sl' not in data and 'tp' not in data:
        return False, "Must provide at least one of: sl, tp"

    # SL/TP validation
    if 'sl' in data:
        try:
            float(data['sl'])
        except (ValueError, TypeError):
            return False, "SL must be a number"

    if 'tp' in data:
        try:
            float(data['tp'])
        except (ValueError, TypeError):
            return False, "TP must be a number"

    return True, ""

def validate_close_command(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate close position command"""
    required = ['ticket']

    if 'ticket' not in data:
        return False, "Missing required field: ticket"

    # Ticket validation
    try:
        int(data['ticket'])
    except (ValueError, TypeError):
        return False, "Ticket must be an integer"

    # Optional volume validation
    if 'volume' in data:
        try:
            volume = float(data['volume'])
            if volume <= 0:
                return False, "Volume must be positive"
        except (ValueError, TypeError):
            return False, "Volume must be a number"

    return True, ""
```

---

### 4. Session Manager (`app/session_manager.py`)

**Responsibilities**:
- Track connected clients
- Store session metadata
- Manage pending orders
- Cleanup on disconnect

**Implementation**:
```python
# app/session_manager.py
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class SessionManager:
    """Manage Socket.IO client sessions"""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def create_session(self, sid: str, initial_data: Dict[str, Any] = None):
        """Create new session for client"""
        with self._lock:
            self.sessions[sid] = initial_data or {}
            logger.debug(f"Session created: {sid}")

    def get_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        with self._lock:
            return self.sessions.get(sid)

    def update_session(self, sid: str, data: Dict[str, Any]):
        """Update session data"""
        with self._lock:
            if sid in self.sessions:
                self.sessions[sid].update(data)
                logger.debug(f"Session updated: {sid}")

    def remove_session(self, sid: str):
        """Remove session"""
        with self._lock:
            if sid in self.sessions:
                del self.sessions[sid]
                logger.debug(f"Session removed: {sid}")

    def add_pending_order(self, sid: str, order_id: str, order_data: Dict[str, Any]):
        """Track pending order for session"""
        with self._lock:
            session = self.sessions.get(sid)
            if session:
                if 'pending_orders' not in session:
                    session['pending_orders'] = {}
                session['pending_orders'][order_id] = {
                    'data': order_data,
                    'timestamp': datetime.utcnow(),
                }

    def remove_pending_order(self, sid: str, order_id: str):
        """Remove pending order"""
        with self._lock:
            session = self.sessions.get(sid)
            if session and 'pending_orders' in session:
                session['pending_orders'].pop(order_id, None)

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all sessions (for debugging)"""
        with self._lock:
            return self.sessions.copy()
```

---

### 5. Response Models (`app/models/responses.py`)

**Responsibilities**:
- Standardized response format
- Error code enumeration
- Helper functions

**Implementation**:
```python
# app/models/responses.py
from enum import Enum
from typing import Dict, Any, Optional

class ErrorCode(Enum):
    """Standardized error codes"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MT5_NOT_CONNECTED = "MT5_NOT_CONNECTED"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    INSUFFICIENT_MARGIN = "INSUFFICIENT_MARGIN"
    ORDER_REJECTED = "ORDER_REJECTED"
    POSITION_NOT_FOUND = "POSITION_NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"

def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create success response"""
    return {
        'success': True,
        **data
    }

def error_response(
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create error response"""
    return {
        'success': False,
        'code': code.value,
        'message': message,
        'details': details or {}
    }
```

---

## IMPLEMENTATION STEPS

### Step 1: Update Configuration
Add Socket.IO settings to `app/config.py`:
```python
@dataclass
class Config:
    # ... existing MT5 config ...

    # Socket.IO Server
    SOCKETIO_HOST: str = os.getenv('SOCKETIO_HOST', '0.0.0.0')
    SOCKETIO_PORT: int = int(os.getenv('SOCKETIO_PORT', '5000'))
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
```

### Step 2: Install Dependencies
Update `requirements.txt`:
```
# Existing
MetaTrader5==5.0.45
python-dotenv==1.0.0

# New for Phase 2
fastapi==0.104.0
python-socketio==5.10.0
uvicorn[standard]==0.24.0
```

Install:
```bash
pip install -r requirements.txt
```

### Step 3: Implement Files
Create in order:
1. `app/models/__init__.py` (empty)
2. `app/models/responses.py`
3. `app/validation.py`
4. `app/session_manager.py`
5. `app/events/__init__.py` (empty)
6. `app/events/trading_events.py`
7. `app/main.py`

### Step 4: Testing
Create `tests/test_events.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_connect_event():
    """Test client connection"""
    # Mock sio and session_manager
    from app.events import trading_events

    sid = "test_client_1"
    environ = {'REMOTE_ADDR': '192.168.1.100'}

    # Call connect handler
    await trading_events.connect(sid, environ)

    # Verify session created
    # (assertions depend on session_manager implementation)

@pytest.mark.asyncio
async def test_login_validation():
    """Test login command validation"""
    from app.validation import validate_login_command

    # Valid
    valid, msg = validate_login_command({
        'account': 12345678,
        'password': 'test',
        'server': 'Demo'
    })
    assert valid is True

    # Invalid - missing field
    valid, msg = validate_login_command({
        'account': 12345678,
        'password': 'test'
    })
    assert valid is False
    assert 'server' in msg
```

### Step 5: Manual Testing
```bash
# Terminal 1: Start server
python -m app.main

# Terminal 2: Test with Python client
python test_client.py
```

**Test Client** (`test_client.py`):
```python
import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')

@sio.event
def connected(data):
    print('Server welcome:', data)

@sio.event
def login_result(data):
    print('Login result:', data)

@sio.event
def error(data):
    print('Error:', data)

sio.connect('http://localhost:5000')

# Test login
sio.emit('login', {
    'account': 12345678,
    'password': 'password',
    'server': 'BrokerServer-Demo'
})

time.sleep(5)
sio.disconnect()
```

---

## ACCEPTANCE CRITERIA

- [ ] Server starts on configured port (default 5000)
- [ ] Clients can connect via Socket.IO
- [ ] Connection event creates session
- [ ] Disconnection event cleans up session
- [ ] `/health` endpoint returns correct status
- [ ] `login` event validates input
- [ ] `buy` event validates input
- [ ] `sell` event validates input
- [ ] `modify` event validates input
- [ ] `close` event validates input
- [ ] Invalid commands return structured errors
- [ ] All events emit responses
- [ ] Logs show connection/command activity

---

## TESTING CHECKLIST

### Manual Tests
1. Start server: `python -m app.main`
2. Check health: `curl http://localhost:5000/health`
3. Connect client via Socket.IO
4. Send `login` with valid data → receive `login_result`
5. Send `login` with invalid data → receive `error`
6. Send `buy` command → receive `order_result` (placeholder)
7. Send `sell` command → receive `order_result` (placeholder)
8. Send `modify` command → receive `modify_result` (placeholder)
9. Send `close` command → receive `close_result` (placeholder)
10. Disconnect client → verify session cleanup

---

## EXPECTED OUTPUT

### Server Startup
```
2025-12-21 10:00:00 - INFO - Starting MT5 Socket.IO Trading Server...
2025-12-21 10:00:01 - INFO - MT5 connection established
2025-12-21 10:00:01 - INFO - Application startup complete
2025-12-21 10:00:01 - INFO - Uvicorn running on http://0.0.0.0:5000
```

### Client Connection
```
2025-12-21 10:01:00 - INFO - Client abc123 connected from 192.168.1.100
2025-12-21 10:01:00 - DEBUG - Session created: abc123
```

### Command Handling
```
2025-12-21 10:01:30 - INFO - Login request from abc123
2025-12-21 10:01:31 - INFO - Client abc123 logged in as 12345678

2025-12-21 10:02:00 - INFO - Buy order from abc123: EURUSD 0.01
2025-12-21 10:02:00 - DEBUG - Validation passed: buy command
```

---

## FILES TO CREATE

1. `app/events/__init__.py` (empty)
2. `app/events/trading_events.py` (~300 lines)
3. `app/models/__init__.py` (empty)
4. `app/models/responses.py` (~40 lines)
5. `app/validation.py` (~120 lines)
6. `app/session_manager.py` (~80 lines)
7. `app/main.py` (~100 lines)
8. `tests/test_events.py` (~100 lines)
9. `test_client.py` (testing utility, ~40 lines)

**Total LOC**: ~780 lines (implementation) + ~140 lines (tests/utils)

---

## PHASE 2 COMPLETION CRITERIA

Before moving to Phase 3:
- ✅ All unit tests pass
- ✅ Server starts without errors
- ✅ Client can connect/disconnect
- ✅ All events registered and responding
- ✅ Validation catches invalid inputs
- ✅ Health endpoint accessible
- ✅ Logs show all activity

---

## NEXT PHASE

After Phase 2 completion → **Phase 3: Command Integration**
- Wire event handlers to MT5 operations
- Replace placeholder responses with real MT5 calls
- Implement command processor
- Add comprehensive logging
