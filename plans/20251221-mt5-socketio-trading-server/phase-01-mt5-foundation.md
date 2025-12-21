# Phase 1: MT5 Foundation & Integration

**Status**: Ready
**Dependencies**: None
**Prerequisites**: MT5 terminal installed with algo trading enabled

---

## OBJECTIVES

Build robust MT5 integration layer with:
- Connection management with health monitoring
- Trading operations (buy/sell/modify/close)
- Error handling with retry logic
- Configuration via environment variables

---

## DELIVERABLES

### 1. MT5 Connection Manager (`app/mt5/connection_manager.py`)

**Responsibilities**:
- Initialize MT5 terminal connection
- Validate terminal state (connected, trading enabled)
- Background health monitoring thread
- Auto-reconnection on disconnect
- Graceful shutdown

**Key Methods**:
```python
class MT5ConnectionManager:
    def __init__(self, check_interval=5.0, timeout=30.0)
    def connect() -> bool
    def disconnect()
    def is_connected() -> bool
    def login_account(account_id, password, server) -> AccountInfo
    def get_account_info() -> dict
    def _health_check_loop()  # Background thread
    def _attempt_reconnect(max_attempts=3) -> bool
```

**Features**:
- Thread-safe state management (RLock)
- Health check every 5 seconds
- Exponential backoff reconnection (1s, 2s, 4s)
- Disconnect/reconnect callbacks

---

### 2. Trading Operations Module (`app/mt5/trading_operations.py`)

**Responsibilities**:
- Market order placement (buy/sell)
- Position modification (TP/SL changes)
- Position closing (full/partial)
- Order validation & error handling

**Key Methods**:
```python
class TradingOperations:
    def __init__(self, connection_manager: MT5ConnectionManager)

    # Order placement
    def place_market_order(symbol, volume, order_type, sl=None, tp=None) -> dict
    def place_buy_market(symbol, volume, sl=None, tp=None) -> dict
    def place_sell_market(symbol, volume, sl=None, tp=None) -> dict

    # Position management
    def modify_position(ticket, new_sl=None, new_tp=None) -> dict
    def close_position(ticket, volume=None) -> dict
    def get_position(ticket) -> dict
    def get_all_positions(symbol=None) -> list

    # Validation
    def _validate_symbol(symbol) -> bool
    def _get_market_price(symbol, order_type) -> float
```

**Features**:
- Automatic symbol enablement if not visible
- Fresh tick prices for market orders
- SL/TP validation (must be correct side of entry)
- Retry logic for retriable errors (REQUOTE, TIMEOUT)
- Structured result dictionaries

---

### 3. Error Handler (`app/mt5/error_handler.py`)

**Responsibilities**:
- Map MT5 error codes to human-readable messages
- Classify errors (retriable vs terminal)
- Provide retry logic

**Key Components**:
```python
class MT5ErrorHandler:
    RETRIABLE_CODES = {
        TRADE_RETCODE_REQUOTE,
        TRADE_RETCODE_TIMEOUT,
        TRADE_RETCODE_INVALID_PRICE,
    }

    @staticmethod
    def is_retriable(retcode: int) -> bool

    @staticmethod
    def get_error_message(retcode: int) -> str

    @staticmethod
    def order_with_retry(request, max_retries=3, retry_delay=1.0)
```

**Error Codes to Handle**:
- `10009` TRADE_RETCODE_DONE - Success
- `10016` TRADE_RETCODE_REQUOTE - Retry with new quote
- `10017` TRADE_RETCODE_REJECT - Terminal error
- `10018` TRADE_RETCODE_CANCEL - Order cancelled
- `10015` TRADE_RETCODE_ERROR - Generic error

---

### 4. Configuration (`app/config.py`)

**Responsibilities**:
- Load environment variables
- Provide type-safe configuration access
- Validation of required settings

**Configuration Schema**:
```python
@dataclass
class MT5Config:
    # MT5 Credentials (optional for auto-login)
    ACCOUNT_NUMBER: int = 0
    ACCOUNT_PASSWORD: str = ""
    BROKER_SERVER: str = ""

    # Connection
    CONNECTION_TIMEOUT: float = 30.0
    HEALTH_CHECK_INTERVAL: float = 5.0

    # Retry
    MAX_ORDER_RETRIES: int = 3
    RETRY_DELAY: float = 1.0

    # Trading
    DEFAULT_SLIPPAGE: float = 20.0  # Points
    ORDER_FILLING: str = "IOC"  # IOC, FOK, RETURN
```

**Environment Variables** (.env.example):
```bash
MT5_ACCOUNT=0
MT5_PASSWORD=
MT5_SERVER=

MT5_CONN_TIMEOUT=30
MT5_HEALTH_INTERVAL=5
MT5_MAX_RETRIES=3
MT5_RETRY_DELAY=1

MT5_SLIPPAGE=20
MT5_FILLING=IOC
```

---

### 5. Logging Configuration (`app/logging_config.py`)

**Setup**:
```python
import logging
import sys

def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    return logging.getLogger(__name__)
```

---

## IMPLEMENTATION STEPS

### Step 1: Project Setup
```bash
mkdir -p backend/app/mt5 backend/tests
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << EOF
MetaTrader5==5.0.45
python-dotenv==1.0.0
pytest==7.4.0
pytest-asyncio==0.21.0
EOF

pip install -r requirements.txt
```

### Step 2: Implement Connection Manager
Create `app/mt5/connection_manager.py` with:
- State machine (DISCONNECTED → CONNECTING → CONNECTED)
- Initialize MT5 with validation
- Background health check thread
- Reconnection logic with exponential backoff
- Callbacks for disconnect/reconnect events

### Step 3: Implement Trading Operations
Create `app/mt5/trading_operations.py` with:
- Market order placement (buy/sell)
- Position modification (TP/SL)
- Position closing
- Symbol validation
- Tick price fetching

### Step 4: Implement Error Handler
Create `app/mt5/error_handler.py` with:
- Error code mapping
- Retriable check
- Retry wrapper

### Step 5: Configuration
Create `app/config.py`:
- Load from environment variables
- Provide defaults
- Validation

### Step 6: Testing
Create `tests/test_connection_manager.py`:
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.mt5.connection_manager import MT5ConnectionManager

@pytest.fixture
def mock_mt5():
    with patch('MetaTrader5.initialize') as mock_init, \
         patch('MetaTrader5.terminal_info') as mock_term, \
         patch('MetaTrader5.shutdown') as mock_shutdown:

        mock_init.return_value = True
        mock_term.return_value = MagicMock(connected=True, trade_allowed=True)

        yield {
            'init': mock_init,
            'term': mock_term,
            'shutdown': mock_shutdown
        }

def test_connect_success(mock_mt5):
    manager = MT5ConnectionManager()
    assert manager.connect() is True
    assert manager.is_connected() is True

def test_connect_failure(mock_mt5):
    mock_mt5['init'].return_value = False
    manager = MT5ConnectionManager()
    assert manager.connect() is False
```

Create `tests/test_trading_operations.py`:
```python
import pytest
from unittest.mock import Mock, MagicMock
from app.mt5.trading_operations import TradingOperations

def test_place_buy_market():
    # Mock connection manager
    conn = Mock()
    conn.is_connected.return_value = True

    ops = TradingOperations(conn)

    # Mock MT5 responses
    with patch('MetaTrader5.symbol_info') as mock_symbol, \
         patch('MetaTrader5.symbol_info_tick') as mock_tick, \
         patch('MetaTrader5.order_send') as mock_order:

        mock_symbol.return_value = MagicMock(visible=True)
        mock_tick.return_value = MagicMock(ask=1.0850, bid=1.0848)
        mock_order.return_value = MagicMock(
            retcode=10009,  # TRADE_RETCODE_DONE
            order=123456,
            price=1.0850,
            volume=0.01
        )

        result = ops.place_buy_market('EURUSD', 0.01, sl=1.0800, tp=1.0900)

        assert result['ticket'] == 123456
        assert result['price'] == 1.0850
```

---

## ACCEPTANCE CRITERIA

- [ ] Connection manager initializes MT5 successfully
- [ ] Health check thread detects disconnections
- [ ] Auto-reconnection works after MT5 restart
- [ ] Can place buy market orders
- [ ] Can place sell market orders
- [ ] Can modify position TP/SL
- [ ] Can close positions
- [ ] Error codes mapped correctly
- [ ] Retry logic works for REQUOTE errors
- [ ] All unit tests pass
- [ ] Manual test on demo account succeeds

---

## TESTING CHECKLIST

### Manual Testing
1. Start MT5 terminal (demo account)
2. Enable algo trading in settings
3. Run connection manager test:
   ```python
   from app.mt5.connection_manager import MT5ConnectionManager

   manager = MT5ConnectionManager()
   if manager.connect():
       print("Connected!")
       print(manager.get_account_info())
       manager.disconnect()
   ```

4. Test order placement:
   ```python
   from app.mt5.trading_operations import TradingOperations

   ops = TradingOperations(manager)

   # Buy order
   result = ops.place_buy_market('EURUSD', 0.01, sl=1.0800, tp=1.0900)
   print("Order placed:", result)

   # Verify in MT5 terminal
   # Modify
   ops.modify_position(result['ticket'], new_tp=1.0920)

   # Close
   ops.close_position(result['ticket'])
   ```

5. Test reconnection:
   - Start manager with health check
   - Close MT5 terminal
   - Observe logs (should detect disconnect)
   - Restart MT5 terminal
   - Observe logs (should reconnect)

---

## EXPECTED OUTPUT

### Successful Connection
```
2025-12-21 10:00:00 - MT5ConnectionManager - INFO - Initializing MT5 connection...
2025-12-21 10:00:01 - MT5ConnectionManager - INFO - MT5 connected successfully
2025-12-21 10:00:01 - MT5ConnectionManager - INFO - Account: 12345678 (BrokerServer-Demo)
2025-12-21 10:00:01 - MT5ConnectionManager - INFO - Balance: 10000.00 USD
2025-12-21 10:00:01 - MT5ConnectionManager - INFO - Starting health check thread
```

### Order Placement
```
2025-12-21 10:01:00 - TradingOperations - INFO - Placing buy order: EURUSD 0.01 lots
2025-12-21 10:01:00 - TradingOperations - DEBUG - Symbol: EURUSD, Tick: Ask=1.0850, Bid=1.0848
2025-12-21 10:01:01 - TradingOperations - INFO - Order executed: Ticket=123456, Price=1.0850
```

### Error Handling
```
2025-12-21 10:02:00 - TradingOperations - WARNING - REQUOTE error, retrying in 1s...
2025-12-21 10:02:01 - TradingOperations - INFO - Order executed on retry: Ticket=123457
```

---

## FILES TO CREATE

1. `app/__init__.py` (empty)
2. `app/mt5/__init__.py` (empty)
3. `app/mt5/connection_manager.py` (~250 lines)
4. `app/mt5/trading_operations.py` (~200 lines)
5. `app/mt5/error_handler.py` (~80 lines)
6. `app/config.py` (~50 lines)
7. `app/logging_config.py` (~30 lines)
8. `tests/__init__.py` (empty)
9. `tests/test_connection_manager.py` (~100 lines)
10. `tests/test_trading_operations.py` (~150 lines)
11. `requirements.txt`
12. `.env.example`
13. `README.md` (Phase 1 setup instructions)

**Total LOC**: ~860 lines (implementation) + ~250 lines (tests)

---

## NEXT PHASE

After Phase 1 completion → **Phase 2: Socket.IO Server Setup**
