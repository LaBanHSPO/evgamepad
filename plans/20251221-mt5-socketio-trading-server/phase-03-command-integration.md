# Phase 3: Command Integration

**Status**: Ready after Phase 2
**Dependencies**: Phase 1 (MT5 Foundation) + Phase 2 (Socket.IO Server)
**Prerequisites**: Server handles events with placeholder responses

---

## OBJECTIVES

Wire Socket.IO events to MT5 operations with:
- Command processor routing layer
- Async execution (non-blocking)
- Response formatting
- Enhanced structured logging
- Request ID tracking for tracing

---

## DELIVERABLES

### 1. Command Processor (`app/processors/command_processor.py`)

**Responsibilities**:
- Route Socket.IO events to MT5 operations
- Execute commands asynchronously
- Handle errors and propagate to client
- Track command lifecycle
- Generate unique command IDs

**Implementation**:
```python
# app/processors/command_processor.py
import logging
import uuid
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from app.mt5.trading_operations import TradingOperations
from app.mt5.connection_manager import MT5ConnectionManager
from app.models.responses import ErrorCode, error_response, success_response

logger = logging.getLogger(__name__)

class CommandProcessor:
    """
    Central command processing layer
    Routes Socket.IO events to MT5 operations
    """

    def __init__(self, mt5_manager: MT5ConnectionManager):
        self.mt5_manager = mt5_manager
        self.trading_ops = TradingOperations(mt5_manager)
        self.pending_commands: Dict[str, Dict[str, Any]] = {}

    async def process_buy_order(
        self,
        sid: str,
        symbol: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process buy market order

        Args:
            sid: Socket.IO session ID
            symbol: Trading symbol
            volume: Order volume in lots
            sl: Stop loss price (optional)
            tp: Take profit price (optional)

        Returns:
            Success response with order details or error response
        """
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

            # Execute on MT5 (blocking call, wrapped in async)
            result = await asyncio.to_thread(
                self.trading_ops.place_buy_market,
                symbol=symbol,
                volume=volume,
                sl=sl,
                tp=tp
            )

            # Success
            logger.info(
                f"[{command_id}] BUY order executed: "
                f"Ticket={result['ticket']}, Price={result['price']}"
            )

            # Cleanup
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

        except ValueError as e:
            # Validation error (invalid symbol, etc.)
            logger.warning(f"[{command_id}] BUY order validation failed: {e}")
            del self.pending_commands[command_id]
            return error_response(
                ErrorCode.VALIDATION_ERROR,
                str(e)
            )

        except RuntimeError as e:
            # MT5 connection error
            logger.error(f"[{command_id}] BUY order failed (MT5 error): {e}")
            del self.pending_commands[command_id]
            return error_response(
                ErrorCode.MT5_NOT_CONNECTED,
                str(e)
            )

        except Exception as e:
            # Generic error
            logger.exception(f"[{command_id}] BUY order failed unexpectedly")
            del self.pending_commands[command_id]
            return error_response(
                ErrorCode.INTERNAL_ERROR,
                f"Order execution failed: {str(e)}"
            )

    async def process_sell_order(
        self,
        sid: str,
        symbol: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process sell market order"""
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing SELL order: {symbol} {volume} lots (client: {sid})")

        try:
            self.pending_commands[command_id] = {
                'type': 'sell',
                'symbol': symbol,
                'volume': volume,
                'client_id': sid,
                'started_at': datetime.utcnow(),
            }

            result = await asyncio.to_thread(
                self.trading_ops.place_sell_market,
                symbol=symbol,
                volume=volume,
                sl=sl,
                tp=tp
            )

            logger.info(
                f"[{command_id}] SELL order executed: "
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

        except ValueError as e:
            logger.warning(f"[{command_id}] SELL order validation failed: {e}")
            del self.pending_commands[command_id]
            return error_response(ErrorCode.VALIDATION_ERROR, str(e))

        except RuntimeError as e:
            logger.error(f"[{command_id}] SELL order failed (MT5 error): {e}")
            del self.pending_commands[command_id]
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))

        except Exception as e:
            logger.exception(f"[{command_id}] SELL order failed unexpectedly")
            del self.pending_commands[command_id]
            return error_response(
                ErrorCode.INTERNAL_ERROR,
                f"Order execution failed: {str(e)}"
            )

    async def process_modify_position(
        self,
        sid: str,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process modify position TP/SL"""
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing MODIFY: Ticket={ticket} (client: {sid})")

        try:
            self.pending_commands[command_id] = {
                'type': 'modify',
                'ticket': ticket,
                'client_id': sid,
                'started_at': datetime.utcnow(),
            }

            result = await asyncio.to_thread(
                self.trading_ops.modify_position,
                ticket=ticket,
                new_sl=sl,
                new_tp=tp
            )

            logger.info(
                f"[{command_id}] Position modified: "
                f"Ticket={ticket}, SL={result['new_sl']}, TP={result['new_tp']}"
            )

            del self.pending_commands[command_id]

            return success_response({
                'command_id': command_id,
                'ticket': ticket,
                'sl': result['new_sl'],
                'tp': result['new_tp'],
                'modified_at': result['modified_at'],
            })

        except ValueError as e:
            logger.warning(f"[{command_id}] MODIFY validation failed: {e}")
            del self.pending_commands[command_id]
            return error_response(ErrorCode.POSITION_NOT_FOUND, str(e))

        except RuntimeError as e:
            logger.error(f"[{command_id}] MODIFY failed (MT5 error): {e}")
            del self.pending_commands[command_id]
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))

        except Exception as e:
            logger.exception(f"[{command_id}] MODIFY failed unexpectedly")
            del self.pending_commands[command_id]
            return error_response(
                ErrorCode.INTERNAL_ERROR,
                f"Modify failed: {str(e)}"
            )

    async def process_close_position(
        self,
        sid: str,
        ticket: int,
        volume: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process close position"""
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing CLOSE: Ticket={ticket} (client: {sid})")

        try:
            self.pending_commands[command_id] = {
                'type': 'close',
                'ticket': ticket,
                'client_id': sid,
                'started_at': datetime.utcnow(),
            }

            result = await asyncio.to_thread(
                self.trading_ops.close_position,
                ticket=ticket,
                volume=volume
            )

            logger.info(
                f"[{command_id}] Position closed: "
                f"Ticket={ticket}, Price={result['close_price']}, Profit={result['profit']}"
            )

            del self.pending_commands[command_id]

            return success_response({
                'command_id': command_id,
                'ticket': ticket,
                'close_ticket': result['close_ticket'],
                'close_price': result['close_price'],
                'volume_closed': result['volume_closed'],
                'profit': result['profit'],
                'closed_at': result['closed_at'],
            })

        except ValueError as e:
            logger.warning(f"[{command_id}] CLOSE validation failed: {e}")
            del self.pending_commands[command_id]
            return error_response(ErrorCode.POSITION_NOT_FOUND, str(e))

        except RuntimeError as e:
            logger.error(f"[{command_id}] CLOSE failed (MT5 error): {e}")
            del self.pending_commands[command_id]
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))

        except Exception as e:
            logger.exception(f"[{command_id}] CLOSE failed unexpectedly")
            del self.pending_commands[command_id]
            return error_response(
                ErrorCode.INTERNAL_ERROR,
                f"Close failed: {str(e)}"
            )

    def get_pending_commands(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending commands (for debugging)"""
        return self.pending_commands.copy()
```

**Key Features**:
- Unique command IDs for tracing
- Async execution via `asyncio.to_thread()`
- Structured error handling by exception type
- Command lifecycle tracking
- Comprehensive logging with command ID

---

### 2. Update Event Handlers (`app/events/trading_events.py`)

**Changes**: Replace placeholder responses with command processor calls

**Updated Event Handlers**:
```python
# app/events/trading_events.py
# ... (keep existing imports and connection handlers)

from app.processors.command_processor import CommandProcessor

# Global command processor (initialized in main.py)
command_processor = None

@sio.event
async def buy(sid: str, data: Dict[str, Any]):
    """Handle buy market order"""
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

        # Process via command processor
        result = await command_processor.process_buy_order(
            sid=sid,
            symbol=data['symbol'],
            volume=data['volume'],
            sl=data.get('sl'),
            tp=data.get('tp')
        )

        # Emit result
        await sio.emit('order_result', result, to=sid)

    except Exception as e:
        logger.exception(f"Buy order handler failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Order failed: {str(e)}"
        ), to=sid)

@sio.event
async def sell(sid: str, data: Dict[str, Any]):
    """Handle sell market order"""
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

        # Process via command processor
        result = await command_processor.process_sell_order(
            sid=sid,
            symbol=data['symbol'],
            volume=data['volume'],
            sl=data.get('sl'),
            tp=data.get('tp')
        )

        # Emit result
        await sio.emit('order_result', result, to=sid)

    except Exception as e:
        logger.exception(f"Sell order handler failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Order failed: {str(e)}"
        ), to=sid)

@sio.event
async def modify(sid: str, data: Dict[str, Any]):
    """Handle modify position"""
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

        # Process via command processor
        result = await command_processor.process_modify_position(
            sid=sid,
            ticket=data['ticket'],
            sl=data.get('sl'),
            tp=data.get('tp')
        )

        # Emit result
        await sio.emit('modify_result', result, to=sid)

    except Exception as e:
        logger.exception(f"Modify handler failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Modify failed: {str(e)}"
        ), to=sid)

@sio.event
async def close(sid: str, data: Dict[str, Any]):
    """Handle close position"""
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

        # Process via command processor
        result = await command_processor.process_close_position(
            sid=sid,
            ticket=data['ticket'],
            volume=data.get('volume')
        )

        # Emit result
        await sio.emit('close_result', result, to=sid)

    except Exception as e:
        logger.exception(f"Close handler failed for {sid}")
        await sio.emit('error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Close failed: {str(e)}"
        ), to=sid)
```

---

### 3. Update Main Application (`app/main.py`)

**Changes**: Initialize command processor

```python
# app/main.py
# ... (existing imports)

from app.processors.command_processor import CommandProcessor
from app.events import trading_events

# Global instances
mt5_manager = None
session_manager = None
command_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global mt5_manager, session_manager, command_processor

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

    # Initialize command processor
    command_processor = CommandProcessor(mt5_manager)
    logger.info("Command processor initialized")

    # Store in app state
    app.state.mt5_manager = mt5_manager
    app.state.session_manager = session_manager
    app.state.command_processor = command_processor

    # Make available to events module
    trading_events.command_processor = command_processor
    trading_events.session_manager = session_manager

    yield

    # Shutdown
    logger.info("Shutting down server...")
    if mt5_manager:
        mt5_manager.disconnect()
    logger.info("Server shutdown complete")

# ... rest of main.py ...
```

---

### 4. Enhanced Logging Configuration (`app/logging_config.py`)

**Update**: Add JSON structured logging for production

```python
# app/logging_config.py
import logging
import sys
from typing import Optional

def setup_logging(debug: bool = False, json_format: bool = False):
    """
    Setup logging configuration

    Args:
        debug: Enable debug level logging
        json_format: Use JSON structured logging
    """
    level = logging.DEBUG if debug else logging.INFO

    if json_format:
        # JSON structured logging for production
        try:
            from pythonjsonlogger import jsonlogger

            handler = logging.StreamHandler(sys.stdout)
            formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
            handler.setFormatter(formatter)

            logging.basicConfig(
                level=level,
                handlers=[handler]
            )
        except ImportError:
            # Fallback to standard logging
            logging.basicConfig(
                level=level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
    else:
        # Standard logging for development
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.INFO)
    logging.getLogger('engineio').setLevel(logging.INFO)

    return logging.getLogger(__name__)
```

---

## IMPLEMENTATION STEPS

### Step 1: Create Command Processor
1. Create `app/processors/__init__.py` (empty)
2. Implement `app/processors/command_processor.py`
3. Add unit tests

### Step 2: Update Event Handlers
1. Modify `app/events/trading_events.py`
2. Replace placeholders with processor calls
3. Update error handling

### Step 3: Update Main Application
1. Initialize command processor in `app/main.py`
2. Pass to events module
3. Test startup sequence

### Step 4: Enhanced Logging
1. Update `app/logging_config.py`
2. Add JSON formatter support
3. Update `requirements.txt` for `python-json-logger`

### Step 5: Testing
Create `tests/test_command_processor.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.processors.command_processor import CommandProcessor

@pytest.mark.asyncio
async def test_process_buy_order_success():
    """Test successful buy order processing"""
    # Mock MT5 manager
    mock_manager = Mock()
    mock_manager.is_connected.return_value = True

    processor = CommandProcessor(mock_manager)

    # Mock trading operations
    with patch.object(processor.trading_ops, 'place_buy_market') as mock_buy:
        mock_buy.return_value = {
            'ticket': 123456,
            'price': 1.0850,
            'volume': 0.01,
            'timestamp': '2025-12-21T10:00:00Z'
        }

        result = await processor.process_buy_order(
            sid='test_client',
            symbol='EURUSD',
            volume=0.01,
            sl=1.0800,
            tp=1.0900
        )

        assert result['success'] is True
        assert result['ticket'] == 123456
        assert 'command_id' in result

@pytest.mark.asyncio
async def test_process_buy_order_validation_error():
    """Test buy order with validation error"""
    mock_manager = Mock()
    processor = CommandProcessor(mock_manager)

    # Mock trading operations to raise ValueError
    with patch.object(processor.trading_ops, 'place_buy_market') as mock_buy:
        mock_buy.side_effect = ValueError("Invalid symbol")

        result = await processor.process_buy_order(
            sid='test_client',
            symbol='INVALID',
            volume=0.01
        )

        assert result['success'] is False
        assert result['code'] == 'VALIDATION_ERROR'
```

---

## ACCEPTANCE CRITERIA

- [ ] Command processor routes events to MT5 operations
- [ ] Buy orders execute successfully on MT5
- [ ] Sell orders execute successfully on MT5
- [ ] Position modifications apply correctly
- [ ] Position closures work correctly
- [ ] All commands return structured responses
- [ ] Errors are caught and formatted properly
- [ ] Command IDs appear in all logs
- [ ] Async execution doesn't block server
- [ ] All unit tests pass

---

## TESTING CHECKLIST

### Integration Tests
1. Start server with MT5 terminal running
2. Connect client via Socket.IO
3. Send `buy` order → verify execution in MT5
4. Check logs for command ID tracing
5. Send `sell` order → verify execution
6. Send `modify` for existing position → verify update
7. Send `close` for position → verify closure
8. Send invalid symbol → verify error response
9. Disconnect MT5 terminal → verify error handling
10. Reconnect MT5 → verify recovery

### Error Scenarios
- [ ] Invalid symbol → VALIDATION_ERROR
- [ ] Insufficient margin → ORDER_REJECTED
- [ ] MT5 disconnected → MT5_NOT_CONNECTED
- [ ] Position not found → POSITION_NOT_FOUND
- [ ] Invalid TP/SL → VALIDATION_ERROR

---

## EXPECTED OUTPUT

### Successful Buy Order
```
2025-12-21 10:00:00 - INFO - Buy order from abc123: EURUSD 0.01
2025-12-21 10:00:00 - INFO - [cmd-uuid-123] Processing BUY order: EURUSD 0.01 lots (client: abc123)
2025-12-21 10:00:01 - INFO - [cmd-uuid-123] BUY order executed: Ticket=123456, Price=1.0850
```

Client receives:
```json
{
  "success": true,
  "command_id": "cmd-uuid-123",
  "ticket": 123456,
  "symbol": "EURUSD",
  "volume": 0.01,
  "price": 1.0850,
  "sl": 1.0800,
  "tp": 1.0900,
  "timestamp": "2025-12-21T10:00:01Z"
}
```

### Error Handling
```
2025-12-21 10:01:00 - INFO - [cmd-uuid-456] Processing BUY order: INVALID 0.01 lots
2025-12-21 10:01:00 - WARNING - [cmd-uuid-456] BUY order validation failed: Symbol INVALID not found
```

Client receives:
```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "message": "Symbol INVALID not found",
  "details": {}
}
```

---

## FILES TO MODIFY/CREATE

**New Files**:
1. `app/processors/__init__.py` (empty)
2. `app/processors/command_processor.py` (~300 lines)
3. `tests/test_command_processor.py` (~150 lines)

**Modified Files**:
1. `app/events/trading_events.py` (update event handlers)
2. `app/main.py` (initialize command processor)
3. `app/logging_config.py` (add JSON logging support)
4. `requirements.txt` (add python-json-logger)

**Total New LOC**: ~450 lines

---

## PHASE 3 COMPLETION CRITERIA

Before moving to Phase 4:
- ✅ All commands execute MT5 operations
- ✅ Buy/sell orders confirmed in MT5 terminal
- ✅ Position modifications visible in MT5
- ✅ Position closures confirmed
- ✅ Error handling tested for all scenarios
- ✅ Command IDs traceable in logs
- ✅ Integration tests pass on demo account
- ✅ No blocking operations in event loop

---

## NEXT PHASE

After Phase 3 completion → **Phase 4: Reliability & Error Handling**
- Circuit breaker implementation
- Reconnection logic with state recovery
- Comprehensive error classification
- Session persistence (optional)
