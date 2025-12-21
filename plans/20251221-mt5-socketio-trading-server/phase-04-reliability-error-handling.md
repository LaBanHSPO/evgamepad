# Phase 4: Reliability & Error Handling

**Status**: Ready after Phase 3
**Dependencies**: Phase 1, 2, 3 completed
**Prerequisites**: End-to-end command flow working

---

## OBJECTIVES

Production-grade reliability with:
- Circuit breaker pattern for MT5 failures
- Client reconnection with session recovery
- Comprehensive error classification
- Pending order tracking across reconnections
- Order reconciliation after network issues
- Resilient connection management

---

## DELIVERABLES

### 1. Circuit Breaker (`app/mt5/circuit_breaker.py`)

**Responsibilities**:
- Prevent hammering broken MT5 connection
- Track failure rate
- Auto-recovery after timeout
- State machine (CLOSED → OPEN → HALF_OPEN)

**Implementation**:
```python
# app/mt5/circuit_breaker.py
import logging
import time
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failed, rejecting requests
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    """
    Circuit breaker pattern for MT5 operations
    Prevents cascading failures from broken MT5 connection
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        recovery_timeout: float = 5.0
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Failures before opening circuit
            timeout: Seconds to wait before attempting recovery
            recovery_timeout: Timeout for recovery attempts
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout

        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker: recovered to CLOSED")

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker: OPEN (failures: {self.failure_count})"
                )

    def can_execute(self) -> bool:
        """Check if operation can proceed"""

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout expired to attempt recovery
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.failure_count = 0
                logger.info("Circuit breaker: attempting HALF_OPEN recovery")
                return True
            return False

        # HALF_OPEN: allow single attempt
        return True

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            RuntimeError: If circuit is open
            Exception: From executed function
        """
        if not self.can_execute():
            raise RuntimeError(
                f"Circuit breaker is {self.state.value} - operation rejected"
            )

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def get_state(self) -> str:
        """Get current state string"""
        return self.state.value

    def reset(self):
        """Reset circuit breaker"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        logger.info("Circuit breaker reset")
```

---

### 2. Reconnection Logic (`app/reconnection_manager.py`)

**Responsibilities**:
- Detect client reconnections
- Restore session state
- Resend pending acknowledgments
- Track reconnection history

**Implementation**:
```python
# app/reconnection_manager.py
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class ReconnectionManager:
    """
    Manage client reconnection and session recovery
    """

    def __init__(self, session_ttl: int = 300):
        """
        Initialize reconnection manager

        Args:
            session_ttl: Session time-to-live in seconds (default 5 minutes)
        """
        self.session_ttl = session_ttl
        self.disconnected_sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def store_disconnected_session(self, sid: str, session_data: Dict[str, Any]):
        """
        Store session data when client disconnects

        Args:
            sid: Session ID
            session_data: Session state to preserve
        """
        with self._lock:
            self.disconnected_sessions[sid] = {
                'data': session_data,
                'disconnected_at': datetime.utcnow(),
                'pending_orders': session_data.get('pending_orders', {}),
                'reconnection_count': 0,
            }
            logger.info(f"Session {sid} stored for recovery (TTL: {self.session_ttl}s)")

    def recover_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to recover session data

        Args:
            sid: Session ID

        Returns:
            Session data if found and not expired, None otherwise
        """
        with self._lock:
            if sid not in self.disconnected_sessions:
                logger.debug(f"No stored session for {sid}")
                return None

            stored = self.disconnected_sessions[sid]
            disconnected_at = stored['disconnected_at']

            # Check expiration
            if datetime.utcnow() - disconnected_at > timedelta(seconds=self.session_ttl):
                logger.warning(f"Session {sid} expired (TTL exceeded)")
                del self.disconnected_sessions[sid]
                return None

            # Recover session
            logger.info(f"Recovering session {sid}")
            stored['reconnection_count'] += 1
            return stored['data']

    def cleanup_expired_sessions(self):
        """Remove expired disconnected sessions"""
        with self._lock:
            now = datetime.utcnow()
            expired = []

            for sid, stored in self.disconnected_sessions.items():
                disconnected_at = stored['disconnected_at']
                if now - disconnected_at > timedelta(seconds=self.session_ttl):
                    expired.append(sid)

            for sid in expired:
                logger.info(f"Cleaning up expired session {sid}")
                del self.disconnected_sessions[sid]

            return len(expired)

    def get_pending_orders(self, sid: str) -> List[Dict[str, Any]]:
        """
        Get pending orders for session

        Args:
            sid: Session ID

        Returns:
            List of pending orders
        """
        with self._lock:
            if sid in self.disconnected_sessions:
                pending = self.disconnected_sessions[sid].get('pending_orders', {})
                return list(pending.values())
            return []

    def remove_session(self, sid: str):
        """Remove session from storage"""
        with self._lock:
            if sid in self.disconnected_sessions:
                del self.disconnected_sessions[sid]
                logger.debug(f"Removed stored session {sid}")
```

---

### 3. Enhanced Connection Manager (`app/mt5/connection_manager.py`)

**Update**: Add circuit breaker integration

```python
# app/mt5/connection_manager.py
# ... (existing imports)

from app.mt5.circuit_breaker import CircuitBreaker

class MT5ConnectionManager:
    """MT5 connection lifecycle with circuit breaker protection"""

    def __init__(self, check_interval=5.0, timeout=30.0):
        # ... existing initialization ...

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=30.0
        )

    def execute_with_circuit_breaker(self, func, *args, **kwargs):
        """
        Execute MT5 operation with circuit breaker protection

        Args:
            func: MT5 function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            RuntimeError: If circuit is open or operation fails
        """
        if not self.is_connected():
            raise RuntimeError("MT5 not connected")

        try:
            return self.circuit_breaker.execute(func, *args, **kwargs)
        except RuntimeError as e:
            if "Circuit breaker is open" in str(e):
                logger.error("Circuit breaker OPEN - refusing MT5 operations")
            raise
```

---

### 4. Update Command Processor (`app/processors/command_processor.py`)

**Changes**: Add circuit breaker protection and reconnection handling

```python
# app/processors/command_processor.py
# ... (existing code)

async def process_buy_order(
    self,
    sid: str,
    symbol: str,
    volume: float,
    sl: Optional[float] = None,
    tp: Optional[float] = None
) -> Dict[str, Any]:
    """Process buy market order with circuit breaker protection"""
    command_id = str(uuid.uuid4())
    logger.info(f"[{command_id}] Processing BUY order: {symbol} {volume} lots (client: {sid})")

    try:
        # Track command
        self.pending_commands[command_id] = {
            'type': 'buy',
            'symbol': symbol,
            'volume': volume,
            'client_id': sid,
            'started_at': datetime.utcnow(),
        }

        # Execute with circuit breaker protection
        def execute_order():
            return self.trading_ops.place_buy_market(
                symbol=symbol,
                volume=volume,
                sl=sl,
                tp=tp
            )

        result = await asyncio.to_thread(
            self.mt5_manager.execute_with_circuit_breaker,
            execute_order
        )

        logger.info(
            f"[{command_id}] BUY order executed: "
            f"Ticket={result['ticket']}, Price={result['price']}"
        )

        del self.pending_commands[command_id]

        return success_response({
            'command_id': command_id,
            'ticket': result['ticket'],
            'symbol': symbol,
            'volume': result['volume'],
            'price': result['price'],
            'sl': sl,
            'tp': tp,
            'timestamp': result['timestamp'],
        })

    except RuntimeError as e:
        # Circuit breaker open or MT5 connection error
        logger.error(f"[{command_id}] BUY order failed: {e}")
        del self.pending_commands[command_id]

        if "Circuit breaker is open" in str(e):
            return error_response(
                ErrorCode.MT5_NOT_CONNECTED,
                "MT5 service temporarily unavailable (circuit breaker open)"
            )
        else:
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))

    except Exception as e:
        logger.exception(f"[{command_id}] BUY order failed unexpectedly")
        del self.pending_commands[command_id]
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Order execution failed: {str(e)}"
        )

# ... (similar updates for sell, modify, close)
```

---

### 5. Update Event Handlers for Reconnection (`app/events/trading_events.py`)

**Changes**: Detect reconnection and recover session

```python
# app/events/trading_events.py
# ... (existing imports)

from app.reconnection_manager import ReconnectionManager

# Global reconnection manager
reconnection_manager = None

@sio.event
async def connect(sid: str, environ: Dict[str, Any]):
    """Handle client connection with reconnection detection"""
    remote_addr = environ.get('REMOTE_ADDR', 'unknown')
    logger.info(f"Client {sid} connecting from {remote_addr}")

    # Attempt session recovery
    recovered_session = reconnection_manager.recover_session(sid)

    if recovered_session:
        # Reconnection detected
        logger.info(f"Reconnection detected for {sid}")

        # Restore session
        session_manager.create_session(sid, recovered_session)

        # Notify client of recovery
        await sio.emit('session_recovered', {
            'message': 'Session recovered',
            'session_id': sid,
            'pending_orders': reconnection_manager.get_pending_orders(sid),
            'reconnected_at': datetime.utcnow().isoformat(),
        }, to=sid)
    else:
        # New connection
        logger.info(f"New client {sid} connected from {remote_addr}")

        # Initialize fresh session
        session_manager.create_session(sid, {
            'connected_at': datetime.utcnow(),
            'remote_addr': remote_addr,
            'mt5_logged_in': False,
            'pending_orders': {},
        })

        # Send welcome
        await sio.emit('connected', {
            'message': 'Connected to MT5 Trading Server',
            'session_id': sid,
            'server_time': datetime.utcnow().isoformat(),
        }, to=sid)

@sio.event
async def disconnect(sid: str):
    """Handle client disconnection with session preservation"""
    logger.info(f"Client {sid} disconnected")

    # Get session for preservation
    session = session_manager.get_session(sid)
    if session:
        # Store for recovery
        reconnection_manager.store_disconnected_session(sid, session)

        # Log pending orders
        pending = session.get('pending_orders', {})
        if pending:
            logger.warning(
                f"Client {sid} disconnected with {len(pending)} pending orders - "
                f"session stored for recovery"
            )

    # Remove from active sessions
    session_manager.remove_session(sid)
```

---

### 6. Error Code Extensions (`app/models/responses.py`)

**Update**: Add new error codes

```python
# app/models/responses.py

class ErrorCode(Enum):
    """Standardized error codes"""
    # ... existing codes ...
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    RECONNECTION_FAILED = "RECONNECTION_FAILED"
    ORDER_RECONCILIATION_FAILED = "ORDER_RECONCILIATION_FAILED"
```

---

### 7. Cleanup Task (`app/tasks/cleanup_task.py`)

**New**: Background task to cleanup expired sessions

```python
# app/tasks/cleanup_task.py
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class CleanupTask:
    """Background task for periodic cleanup"""

    def __init__(self, reconnection_manager, interval: int = 60):
        """
        Initialize cleanup task

        Args:
            reconnection_manager: ReconnectionManager instance
            interval: Cleanup interval in seconds
        """
        self.reconnection_manager = reconnection_manager
        self.interval = interval
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def run(self):
        """Run cleanup loop"""
        self.running = True
        logger.info(f"Cleanup task started (interval: {self.interval}s)")

        while self.running:
            try:
                await asyncio.sleep(self.interval)

                # Cleanup expired sessions
                expired_count = self.reconnection_manager.cleanup_expired_sessions()
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions")

            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.exception("Error in cleanup task")

    def start(self):
        """Start cleanup task"""
        if not self.task:
            self.task = asyncio.create_task(self.run())
            logger.info("Cleanup task scheduled")

    async def stop(self):
        """Stop cleanup task"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            logger.info("Cleanup task stopped")
```

---

### 8. Update Main Application (`app/main.py`)

**Changes**: Initialize reconnection manager and cleanup task

```python
# app/main.py
# ... (existing imports)

from app.reconnection_manager import ReconnectionManager
from app.tasks.cleanup_task import CleanupTask

# Global instances
# ... existing ...
reconnection_manager = None
cleanup_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global mt5_manager, session_manager, command_processor, reconnection_manager, cleanup_task

    logger.info("Starting MT5 Socket.IO Trading Server...")

    # ... existing initialization ...

    # Initialize reconnection manager
    reconnection_manager = ReconnectionManager(session_ttl=300)  # 5 minutes
    logger.info("Reconnection manager initialized")

    # Start cleanup task
    cleanup_task = CleanupTask(reconnection_manager, interval=60)
    cleanup_task.start()

    # Make available to events
    trading_events.reconnection_manager = reconnection_manager
    # ... rest ...

    yield

    # Shutdown
    logger.info("Shutting down server...")

    # Stop cleanup task
    if cleanup_task:
        await cleanup_task.stop()

    # ... existing shutdown ...
```

---

## IMPLEMENTATION STEPS

### Step 1: Circuit Breaker
1. Implement `app/mt5/circuit_breaker.py`
2. Update `app/mt5/connection_manager.py`
3. Add unit tests

### Step 2: Reconnection Manager
1. Implement `app/reconnection_manager.py`
2. Update event handlers for reconnection
3. Test session recovery

### Step 3: Update Command Processor
1. Add circuit breaker protection
2. Update error handling
3. Test failure scenarios

### Step 4: Cleanup Task
1. Implement `app/tasks/cleanup_task.py`
2. Initialize in main app
3. Test expiration cleanup

### Step 5: Comprehensive Testing
1. Test circuit breaker triggering
2. Test reconnection scenarios
3. Test session recovery
4. Test cleanup task

---

## ACCEPTANCE CRITERIA

- [ ] Circuit breaker opens after 5 failures
- [ ] Circuit breaker recovers after timeout
- [ ] Client reconnection restores session
- [ ] Pending orders tracked across reconnections
- [ ] Session expires after TTL
- [ ] Cleanup task removes expired sessions
- [ ] All error codes properly handled
- [ ] Server survives MT5 terminal crash
- [ ] Network drops don't lose orders

---

## TESTING CHECKLIST

### Circuit Breaker Tests
1. Force 5 MT5 failures → verify circuit opens
2. Wait 30 seconds → verify half-open state
3. Successful operation → verify circuit closes
4. Circuit open → verify operations rejected

### Reconnection Tests
1. Connect client → disconnect → reconnect within 5 min → verify session recovered
2. Place order → disconnect → reconnect → verify order status preserved
3. Disconnect for > 5 min → reconnect → verify new session created
4. Multiple reconnections → verify state maintained

### Cleanup Tests
1. Create disconnected session → wait > TTL → verify cleanup
2. Check logs for cleanup task activity
3. Verify no memory leaks from expired sessions

### Error Handling Tests
1. MT5 terminal crash → verify circuit breaker opens
2. Network timeout → verify retry logic
3. Invalid position ticket → verify POSITION_NOT_FOUND
4. Insufficient margin → verify ORDER_REJECTED

---

## EXPECTED OUTPUT

### Circuit Breaker Triggered
```
2025-12-21 10:00:00 - WARNING - Circuit breaker: OPEN (failures: 5)
2025-12-21 10:00:01 - ERROR - Circuit breaker OPEN - refusing MT5 operations
```

Client receives:
```json
{
  "success": false,
  "code": "MT5_NOT_CONNECTED",
  "message": "MT5 service temporarily unavailable (circuit breaker open)"
}
```

### Reconnection Recovery
```
2025-12-21 10:05:00 - INFO - Client abc123 connecting from 192.168.1.100
2025-12-21 10:05:00 - INFO - Reconnection detected for abc123
2025-12-21 10:05:00 - INFO - Recovering session abc123
```

Client receives:
```json
{
  "message": "Session recovered",
  "session_id": "abc123",
  "pending_orders": [...],
  "reconnected_at": "2025-12-21T10:05:00Z"
}
```

### Cleanup Task
```
2025-12-21 11:00:00 - INFO - Cleanup task started (interval: 60s)
2025-12-21 11:01:00 - INFO - Cleaned up 2 expired sessions
```

---

## FILES TO CREATE

1. `app/mt5/circuit_breaker.py` (~150 lines)
2. `app/reconnection_manager.py` (~120 lines)
3. `app/tasks/__init__.py` (empty)
4. `app/tasks/cleanup_task.py` (~80 lines)
5. `tests/test_circuit_breaker.py` (~100 lines)
6. `tests/test_reconnection.py` (~120 lines)

**Modified Files**:
1. `app/mt5/connection_manager.py` (add circuit breaker)
2. `app/processors/command_processor.py` (add protection)
3. `app/events/trading_events.py` (add reconnection)
4. `app/main.py` (initialize managers)
5. `app/models/responses.py` (add error codes)

**Total New LOC**: ~570 lines

---

## PHASE 4 COMPLETION CRITERIA

Before moving to Phase 5:
- ✅ Circuit breaker prevents cascading failures
- ✅ Reconnection works within TTL window
- ✅ Session state persists across disconnects
- ✅ Cleanup task removes expired data
- ✅ All error scenarios handled gracefully
- ✅ Integration tests pass for reliability
- ✅ Server uptime > 99% in stress testing
- ✅ No memory leaks from pending operations

---

## PERFORMANCE TARGETS

- **Circuit breaker reaction time**: < 1 second
- **Reconnection time**: < 5 seconds
- **Session recovery**: < 100ms
- **Cleanup interval**: 60 seconds
- **Session TTL**: 300 seconds (5 minutes)
- **Max pending commands**: 100 per client

---

## NEXT PHASE

After Phase 4 completion → **Phase 5: Production Readiness**
- Docker deployment configuration
- Health check enhancements
- Prometheus metrics
- API documentation
- Deployment guide
