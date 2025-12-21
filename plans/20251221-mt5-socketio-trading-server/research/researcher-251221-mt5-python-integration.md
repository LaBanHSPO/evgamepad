# MetaTrader5 Python Integration Research Report
**Date**: 2025-12-21
**Topic**: MT5 Python Package Integration for Automated Trading
**Focus**: Production-Ready Server-Side Implementation Patterns

---

## Executive Summary

MetaTrader5 (MT5) Python package provides robust bindings to automate trading via the MetaTrader5 terminal. Core findings: package requires active MT5 terminal with algorithmic trading enabled; supports synchronous order operations; production systems need comprehensive connection/reconnection management, state validation, and error recovery patterns.

---

## 1. MT5 Python Package Capabilities

### 1.1 Installation & Setup Requirements

**Package Details:**
- **Package Name**: `MetaTrader5`
- **PyPI URL**: https://pypi.org/project/MetaTrader5/
- **Supported Platforms**: Windows, Linux (via Wine/WSL), macOS (via parallel.desktop or Docker)
- **Python Versions**: 3.6+
- **Dependencies**: Windows DLL bindings (32/64-bit architecture matching)

**Installation:**
```bash
pip install MetaTrader5
```

**System Requirements:**
- MetaTrader5 terminal installed and running
- Terminal must have algorithmic trading enabled (Tools > Options > Advisors tab)
- At least one account configured
- Stable network connection to broker server

### 1.2 Connection & Initialization Patterns

**Basic Initialization Sequence:**
```python
import MetaTrader5 as mt5
import time

class MT5Manager:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.connected = False
        self.account_info = None

    def initialize(self):
        """Initialize MT5 connection with validation."""
        if not mt5.initialize():
            error = mt5.last_error()
            raise ConnectionError(f"MT5 init failed: {error}")

        # Verify connection
        if not mt5.terminal_info():
            raise RuntimeError("MT5 terminal not responding")

        self.connected = True
        self._validate_state()

    def shutdown(self):
        """Graceful shutdown."""
        if self.connected:
            mt5.shutdown()
            self.connected = False

    def _validate_state(self):
        """Validate terminal state is operational."""
        term_info = mt5.terminal_info()
        if not term_info:
            raise RuntimeError("Terminal info unavailable")

        if not term_info.connected:
            raise RuntimeError("Terminal not connected to broker")

        if term_info.trade_allowed is False:
            raise RuntimeError("Trading disabled in terminal")
```

**Terminal Connection States:**
- `terminal_info().connected` - Connection to broker active
- `terminal_info().trade_allowed` - Algorithmic trading enabled
- `terminal_info().community_connected` - MQL5 community connection

### 1.3 Account Login Methods

**Account Information Retrieval:**
```python
def login_and_verify(self, account_id, password=None, server=None):
    """
    Login to specific account.

    Args:
        account_id: Account number (integer)
        password: Account password (optional, uses terminal session if not provided)
        server: Server name (optional, uses configured account if not provided)

    Returns:
        AccountInfo object if successful
    """
    try:
        if not mt5.terminal_info():
            raise RuntimeError("Terminal offline")

        # If credentials provided, switch account
        if password and server:
            if not mt5.login(account_id, password, server):
                error = mt5.last_error()
                raise AuthenticationError(f"Login failed: {error}")

        # Verify logged-in account
        account = mt5.account_info()
        if not account:
            raise RuntimeError("Could not retrieve account info")

        if account.login != account_id:
            raise RuntimeError(f"Account mismatch: expected {account_id}, got {account.login}")

        self.account_info = account
        return account

    except Exception as e:
        raise LoginError(f"Account login failed: {str(e)}")

def get_account_info(self):
    """Retrieve current account details."""
    account = mt5.account_info()
    if not account:
        raise RuntimeError("Account info unavailable")

    return {
        'login': account.login,
        'name': account.name,
        'server': account.server,
        'currency': account.currency,
        'balance': account.balance,
        'equity': account.equity,
        'margin': account.margin,
        'margin_free': account.margin_free,
        'margin_level': account.margin_level,
        'profit': account.profit,
        'leverage': account.leverage,
        'trade_allowed': account.trade_allowed,
        'trade_mode': account.trade_mode,  # 'DEMO', 'REAL', 'CONTEST'
    }
```

**Account Info Structure:**
```python
# AccountInfo fields available
account.login          # Account number
account.name           # Account owner name
account.server         # Broker server
account.currency       # Account currency (USD, EUR, etc.)
account.balance        # Account balance
account.equity         # Equity = balance + profit/loss
account.margin         # Margin used
account.margin_free    # Available margin
account.margin_level   # Margin level percentage
account.profit         # Current profit/loss
account.leverage       # Account leverage (e.g., 100:1)
account.trade_allowed  # Boolean: trading enabled
account.trade_mode     # Account mode: 'DEMO'/'REAL'/'CONTEST'
```

---

## 2. Order Operations

### 2.1 Market Order Placement (Buy/Sell)

**Market Order Structure & Execution:**
```python
import MetaTrader5 as mt5
from enum import Enum

class OrderType(Enum):
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP

class OrderFiller(Enum):
    """Order filling policy"""
    FOK = mt5.ORDER_FILLING_FOK        # Fill or Kill
    IOC = mt5.ORDER_FILLING_IOC        # Immediate or Cancel
    RETURN = mt5.ORDER_FILLING_RETURN  # Return remaining

class OrderTimeframe(Enum):
    """Order validity"""
    GTC = mt5.ORDER_TIME_GTC           # Good Till Cancelled
    DAY = mt5.ORDER_TIME_DAY           # Day order
    SPECIFIED = mt5.ORDER_TIME_SPECIFIED  # Expires at time

def place_market_order(self, symbol, volume, order_type,
                      price=None, sl=None, tp=None,
                      comment="", filling_policy=OrderFiller.IOC):
    """
    Place market order with proper error handling.

    Args:
        symbol: Trading pair (e.g., 'EURUSD')
        volume: Position size in lots
        order_type: BUY or SELL
        price: Entry price (None = market price)
        sl: Stop loss price
        tp: Take profit price
        comment: Order comment
        filling_policy: Fill or Kill / Immediate or Cancel

    Returns:
        OrderResult object with ticket number
    """

    if not self.connected:
        raise RuntimeError("MT5 not connected")

    # Validate inputs
    if volume <= 0:
        raise ValueError("Volume must be positive")

    # Get symbol info
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        raise ValueError(f"Symbol {symbol} not found")

    if not symbol_info.visible:
        # Try to enable symbol
        if not mt5.symbol_select(symbol, True):
            raise ValueError(f"Cannot enable symbol {symbol}")
        symbol_info = mt5.symbol_info(symbol)

    # Get current market price
    if price is None:
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            raise RuntimeError(f"Cannot get tick for {symbol}")

        price = tick.ask if order_type == OrderType.BUY else tick.bid

    # Build request
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': volume,
        'type': order_type.value,
        'price': price,
        'deviation': 20,  # Max slippage in points
        'comment': comment,
        'type_filling': filling_policy.value,
    }

    # Add SL/TP if provided
    if sl:
        request['sl'] = sl
    if tp:
        request['tp'] = tp

    # Execute order
    result = mt5.order_send(request)

    if not result:
        error = mt5.last_error()
        raise OrderError(f"Order send failed: {error}")

    # Validate result
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise OrderError(
            f"Order rejected (code {result.retcode}): {result.comment}"
        )

    return {
        'ticket': result.order,
        'price': result.price,
        'volume': result.volume,
        'timestamp': result.timestamp,
    }

def place_buy_market(self, symbol, volume, sl=None, tp=None, comment=""):
    """Convenience: Market buy."""
    return self.place_market_order(
        symbol, volume, OrderType.BUY,
        sl=sl, tp=tp, comment=comment
    )

def place_sell_market(self, symbol, volume, sl=None, tp=None, comment=""):
    """Convenience: Market sell."""
    return self.place_market_order(
        symbol, volume, OrderType.SELL,
        sl=sl, tp=tp, comment=comment
    )
```

**Market Order Result Codes:**
```
TRADE_RETCODE_DONE (10009)        ✓ Order accepted
TRADE_RETCODE_REQUOTE (10016)     Market quote changed, retry
TRADE_RETCODE_REJECT (10017)      Order rejected
TRADE_RETCODE_CANCEL (10018)      Order cancelled
TRADE_RETCODE_PLACED (10019)      Pending order placed
TRADE_RETCODE_DONE_PARTIAL (10010) Partial fill
TRADE_RETCODE_ERROR (10015)       Generic error
```

### 2.2 Pending Orders

**Limit/Stop Order Placement:**
```python
def place_pending_order(self, symbol, volume, order_type,
                       entry_price, sl=None, tp=None,
                       expiry_time=None, comment=""):
    """
    Place pending limit or stop order.

    Args:
        order_type: BUY_LIMIT, SELL_LIMIT, BUY_STOP, SELL_STOP
        entry_price: Price to trigger order
        expiry_time: Unix timestamp when order expires (None = GTC)
    """

    request = {
        'action': mt5.TRADE_ACTION_PENDING,
        'symbol': symbol,
        'volume': volume,
        'type': order_type.value,
        'price': entry_price,
        'comment': comment,
        'type_time': mt5.ORDER_TIME_GTC if not expiry_time else mt5.ORDER_TIME_SPECIFIED,
    }

    if expiry_time:
        request['expiration'] = expiry_time

    if sl:
        request['sl'] = sl
    if tp:
        request['tp'] = tp

    result = mt5.order_send(request)

    if result.retcode not in [mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED]:
        raise OrderError(f"Pending order failed: {result.comment}")

    return {'ticket': result.order, 'price': entry_price}
```

---

## 3. Position Management

### 3.1 Position Modification (TP/SL Changes)

**Position Update Operations:**
```python
def modify_position(self, ticket, new_sl=None, new_tp=None, comment=None):
    """
    Modify SL/TP of existing position.

    Args:
        ticket: Position ticket number
        new_sl: New stop loss (None = keep current)
        new_tp: New take profit (None = keep current)

    Returns:
        Dict with modification result
    """

    # Get position details
    position = mt5.positions_get(ticket=ticket)
    if not position or len(position) == 0:
        raise ValueError(f"Position {ticket} not found")

    pos = position[0]

    # Use existing values if not changing
    sl = new_sl if new_sl is not None else pos.sl
    tp = new_tp if new_tp is not None else pos.tp

    # Validate changes
    if new_sl is not None and new_tp is not None:
        if pos.type == mt5.ORDER_TYPE_BUY:
            if new_sl >= pos.price_open:
                raise ValueError("SL must be below entry for BUY")
            if new_tp <= pos.price_open:
                raise ValueError("TP must be above entry for BUY")
        else:  # SELL
            if new_sl <= pos.price_open:
                raise ValueError("SL must be above entry for SELL")
            if new_tp >= pos.price_open:
                raise ValueError("TP must be below entry for SELL")

    # Build modification request
    request = {
        'action': mt5.TRADE_ACTION_SLTP,
        'position': ticket,
        'sl': sl,
        'tp': tp,
    }

    if comment:
        request['comment'] = comment

    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise PositionError(f"Modification failed: {result.comment}")

    return {
        'ticket': ticket,
        'new_sl': sl,
        'new_tp': tp,
        'modified_at': time.time(),
    }

def modify_sl(self, ticket, new_sl):
    """Modify only stop loss."""
    return self.modify_position(ticket, new_sl=new_sl)

def modify_tp(self, ticket, new_tp):
    """Modify only take profit."""
    return self.modify_position(ticket, new_tp=new_tp)

def get_position(self, ticket):
    """Retrieve position details."""
    positions = mt5.positions_get(ticket=ticket)
    if not positions:
        return None

    pos = positions[0]
    return {
        'ticket': pos.ticket,
        'symbol': pos.symbol,
        'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
        'volume': pos.volume,
        'price_open': pos.price_open,
        'current_price': pos.price_current,
        'sl': pos.sl,
        'tp': pos.tp,
        'profit': pos.profit,
        'profit_pct': (pos.profit / (pos.volume * pos.price_open * 100)) * 100,
        'time_open': pos.time,
        'comment': pos.comment,
    }

def get_all_positions(self, symbol=None):
    """Get all open positions, optionally filtered by symbol."""
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return []

    return [
        {
            'ticket': pos.ticket,
            'symbol': pos.symbol,
            'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
            'volume': pos.volume,
            'price_open': pos.price_open,
            'current_price': pos.price_current,
            'sl': pos.sl,
            'tp': pos.tp,
            'profit': pos.profit,
            'time_open': pos.time,
        }
        for pos in positions
    ]
```

### 3.2 Position Closing

**Close Position Operations:**
```python
def close_position(self, ticket, volume=None, comment=""):
    """
    Close position fully or partially.

    Args:
        ticket: Position ticket number
        volume: Volume to close (None = full close)
        comment: Close comment

    Returns:
        Closure result dict
    """

    # Get position
    position = mt5.positions_get(ticket=ticket)
    if not position:
        raise ValueError(f"Position {ticket} not found")

    pos = position[0]
    close_volume = volume if volume else pos.volume

    if close_volume <= 0 or close_volume > pos.volume:
        raise ValueError(f"Invalid close volume: {close_volume}")

    # Get current price
    tick = mt5.symbol_info_tick(pos.symbol)
    if not tick:
        raise RuntimeError(f"Cannot get tick for {pos.symbol}")

    # Close at market
    close_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'position': ticket,
        'symbol': pos.symbol,
        'volume': close_volume,
        'type': mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
        'price': close_price,
        'deviation': 20,
        'comment': comment or f'Close position {ticket}',
        'type_filling': mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise PositionError(f"Close failed: {result.comment}")

    return {
        'ticket': ticket,
        'close_ticket': result.order,
        'close_price': close_price,
        'volume_closed': close_volume,
        'profit': pos.profit,
        'closed_at': time.time(),
    }

def close_all_positions(self, symbol=None):
    """Close all open positions, optionally by symbol."""
    positions = mt5.positions_get(symbol=symbol)
    closed = []

    for pos in positions:
        try:
            result = self.close_position(pos.ticket)
            closed.append(result)
        except Exception as e:
            print(f"Failed to close {pos.ticket}: {e}")

    return closed
```

---

## 4. Error Handling Patterns

### 4.1 Error Codes & Recovery

**MT5 Error Code Categories:**
```python
class MT5ErrorHandler:
    """Centralized error handling for MT5 operations."""

    # Retriable errors (temporary issues)
    RETRIABLE_CODES = {
        mt5.TRADE_RETCODE_REQUOTE,      # Quote changed, retry
        mt5.TRADE_RETCODE_TIMEOUT,      # Timeout, retry
        mt5.TRADE_RETCODE_INVALID_PRICE, # Price invalid, refresh tick
    }

    # Terminal errors (unrecoverable)
    TERMINAL_CODES = {
        mt5.TRADE_RETCODE_REJECT,       # Order rejected
        mt5.TRADE_RETCODE_INVALID_VOLUME, # Bad volume
        mt5.TRADE_RETCODE_INVALID_STOPS,  # SL/TP invalid
    }

    @staticmethod
    def is_retriable(retcode):
        return retcode in MT5ErrorHandler.RETRIABLE_CODES

    @staticmethod
    def get_error_message(retcode):
        """Get human-readable error message."""
        messages = {
            mt5.TRADE_RETCODE_DONE: "Order executed successfully",
            mt5.TRADE_RETCODE_REQUOTE: "Market quote changed, retry order",
            mt5.TRADE_RETCODE_REJECT: "Order rejected by broker",
            mt5.TRADE_RETCODE_CANCEL: "Order cancelled",
            mt5.TRADE_RETCODE_PLACED: "Pending order placed",
            mt5.TRADE_RETCODE_DONE_PARTIAL: "Partial fill",
            mt5.TRADE_RETCODE_ERROR: "Generic trade error",
            mt5.TRADE_RETCODE_TIMEOUT: "Operation timeout",
            mt5.TRADE_RETCODE_INVALID_PRICE: "Invalid price",
            mt5.TRADE_RETCODE_INVALID_STOPS: "Invalid SL/TP",
            mt5.TRADE_RETCODE_INVALID_VOLUME: "Invalid volume",
        }
        return messages.get(retcode, f"Unknown error code: {retcode}")

def order_with_retry(self, request, max_retries=3, retry_delay=1.0):
    """
    Send order with automatic retry on retriable errors.

    Args:
        request: Order request dict
        max_retries: Max retry attempts
        retry_delay: Delay between retries (seconds)

    Returns:
        Order result
    """

    for attempt in range(max_retries):
        try:
            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return result

            if not MT5ErrorHandler.is_retriable(result.retcode):
                raise OrderError(
                    f"Order rejected: {MT5ErrorHandler.get_error_message(result.retcode)}"
                )

            if attempt < max_retries - 1:
                print(f"Retriable error {result.retcode}, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                continue
            else:
                raise OrderError(f"Order failed after {max_retries} retries")

        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)

    raise OrderError("Order failed: max retries exceeded")
```

---

## 5. Reliability Patterns

### 5.1 Connection State Management

**Connection Health Monitoring:**
```python
import threading
import time
from enum import Enum
from typing import Callable, Optional

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

class MT5ConnectionManager:
    """
    Manages MT5 connection lifecycle with health monitoring.
    Thread-safe connection state management.
    """

    def __init__(self, check_interval=5.0, timeout=30.0):
        self.state = ConnectionState.DISCONNECTED
        self.check_interval = check_interval
        self.timeout = timeout
        self._lock = threading.RLock()
        self._health_thread = None
        self._stop_monitoring = False
        self.on_disconnect = None  # Callback on disconnect
        self.on_reconnect = None   # Callback on reconnect

    def connect(self):
        """Initialize MT5 connection."""
        with self._lock:
            if self.state == ConnectionState.CONNECTED:
                return True

            self.state = ConnectionState.CONNECTING

            try:
                if not mt5.initialize():
                    self.state = ConnectionState.FAILED
                    return False

                if not mt5.terminal_info():
                    mt5.shutdown()
                    self.state = ConnectionState.FAILED
                    return False

                self.state = ConnectionState.CONNECTED
                self._start_health_check()
                return True

            except Exception as e:
                print(f"Connection error: {e}")
                self.state = ConnectionState.FAILED
                return False

    def disconnect(self):
        """Graceful disconnect."""
        with self._lock:
            self._stop_monitoring = True
            if self._health_thread:
                self._health_thread.join(timeout=2)

            if self.state != ConnectionState.DISCONNECTED:
                mt5.shutdown()
                self.state = ConnectionState.DISCONNECTED

    def is_connected(self):
        """Check if actively connected."""
        with self._lock:
            return self.state == ConnectionState.CONNECTED

    def _start_health_check(self):
        """Start background health monitoring thread."""
        if self._health_thread:
            return

        self._stop_monitoring = False
        self._health_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True,
            name="MT5-HealthCheck"
        )
        self._health_thread.start()

    def _health_check_loop(self):
        """Periodically check connection health."""
        while not self._stop_monitoring:
            time.sleep(self.check_interval)

            with self._lock:
                if self._stop_monitoring:
                    break

                if not self._is_terminal_healthy():
                    self._handle_disconnect()

    def _is_terminal_healthy(self):
        """Check terminal connectivity."""
        try:
            term_info = mt5.terminal_info()
            if not term_info or not term_info.connected:
                return False
            return True
        except:
            return False

    def _handle_disconnect(self):
        """Handle unexpected disconnect."""
        prev_state = self.state
        self.state = ConnectionState.RECONNECTING

        if self.on_disconnect:
            try:
                self.on_disconnect()
            except:
                pass

        if self._attempt_reconnect():
            if self.on_reconnect:
                try:
                    self.on_reconnect()
                except:
                    pass
        else:
            self.state = ConnectionState.FAILED

    def _attempt_reconnect(self, max_attempts=3):
        """Attempt reconnection with backoff."""
        for attempt in range(max_attempts):
            try:
                # Re-initialize
                if not mt5.initialize():
                    raise RuntimeError("Re-initialization failed")

                if not mt5.terminal_info():
                    raise RuntimeError("Terminal check failed")

                self.state = ConnectionState.CONNECTED
                print(f"Reconnected after {attempt + 1} attempts")
                return True

            except Exception as e:
                print(f"Reconnection attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    time.sleep(2 ** attempt)

        return False
```

### 5.2 Thread Safety & Synchronization

**Thread-Safe Order Queue:**
```python
import queue
from threading import Lock
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class OrderRequest:
    """Order request to be executed."""
    request_dict: Dict[str, Any]
    callback: Optional[Callable] = None
    retry_count: int = 0
    max_retries: int = 3

class OrderExecutor:
    """
    Thread-safe order execution engine.
    Processes orders from queue sequentially to avoid race conditions.
    """

    def __init__(self, manager: MT5ConnectionManager):
        self.manager = manager
        self.queue = queue.Queue()
        self._executor_thread = None
        self._stop_executor = False
        self._processing = False

    def start(self):
        """Start order processing thread."""
        if self._executor_thread:
            return

        self._stop_executor = False
        self._executor_thread = threading.Thread(
            target=self._process_orders,
            daemon=True,
            name="MT5-OrderExecutor"
        )
        self._executor_thread.start()

    def stop(self):
        """Stop executor and wait for queue to drain."""
        self._stop_executor = True
        if self._executor_thread:
            self._executor_thread.join(timeout=5)

    def queue_order(self, request: Dict, callback: Optional[Callable] = None):
        """Queue order for execution."""
        order_req = OrderRequest(
            request_dict=request,
            callback=callback
        )
        self.queue.put(order_req)

    def _process_orders(self):
        """Main order processing loop."""
        while not self._stop_executor:
            try:
                # Wait for order with timeout to allow graceful shutdown
                order = self.queue.get(timeout=1.0)
                self._execute_order(order)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Executor error: {e}")

    def _execute_order(self, order: OrderRequest):
        """Execute single order with retry logic."""

        if not self.manager.is_connected():
            print(f"Order {order.request_dict['comment']} discarded: not connected")
            return

        self._processing = True

        try:
            result = mt5.order_send(order.request_dict)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                if order.callback:
                    order.callback(result, None)
                return

            # Check if retriable
            if MT5ErrorHandler.is_retriable(result.retcode) and \
               order.retry_count < order.max_retries:
                order.retry_count += 1
                print(f"Retrying order (attempt {order.retry_count})...")
                time.sleep(1.0)
                self.queue.put(order)  # Re-queue
            else:
                error = OrderError(f"Order failed: {result.comment}")
                if order.callback:
                    order.callback(None, error)

        except Exception as e:
            if order.callback:
                order.callback(None, e)

        finally:
            self._processing = False
```

### 5.3 Reconnection Strategies

**Automatic Reconnection with Circuit Breaker:**
```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failed too many times, reject immediately
    HALF_OPEN = "half_open"  # Attempting recovery

class CircuitBreaker:
    """
    Circuit breaker pattern for MT5 operations.
    Prevents hammering broken connections.
    """

    def __init__(self,
                 failure_threshold=5,
                 timeout=60,
                 recovery_timeout=5):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            print("Circuit breaker: recovered to CLOSED")

    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"Circuit breaker: OPEN (failures: {self.failure_count})")

    def can_execute(self):
        """Check if operation can proceed."""

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout expired to attempt recovery
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.failure_count = 0
                print("Circuit breaker: attempting HALF_OPEN recovery")
                return True
            return False

        # HALF_OPEN: allow single attempt
        return True

    def get_state_str(self):
        return self.state.value

class RobustMT5Manager(MT5ConnectionManager):
    """MT5 manager with circuit breaker protection."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=30
        )

    def execute_order_safe(self, request, max_retries=3):
        """Execute order with circuit breaker protection."""

        if not self.circuit_breaker.can_execute():
            raise RuntimeError(
                f"Circuit breaker is {self.circuit_breaker.get_state_str()}"
            )

        try:
            result = self.order_with_retry(request, max_retries)
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise
```

---

## 6. Best Practices

### 6.1 Initialization & Shutdown Sequences

**Production-Ready Application Template:**
```python
import signal
import atexit
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionMT5App:
    """
    Production-grade MT5 trading application with
    proper lifecycle management.
    """

    def __init__(self):
        self.connection = MT5ConnectionManager()
        self.executor = OrderExecutor(self.connection)
        self.running = False

    def start(self):
        """Start trading application."""
        try:
            logger.info("Starting MT5 trading application...")

            # 1. Initialize connection
            if not self.connection.connect():
                raise RuntimeError("Failed to connect to MT5")

            logger.info("MT5 connected successfully")

            # 2. Verify account
            account = mt5.account_info()
            if not account:
                raise RuntimeError("Cannot access account")

            logger.info(
                f"Logged in: {account.name} "
                f"({account.server}) - Balance: {account.balance}"
            )

            # 3. Start order executor
            self.executor.start()

            # 4. Setup signal handlers
            signal.signal(signal.SIGINT, self._on_signal)
            signal.signal(signal.SIGTERM, self._on_signal)

            # 5. Setup exit handler
            atexit.register(self.shutdown)

            self.running = True
            logger.info("Application started successfully")

            return True

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            self.shutdown()
            return False

    def shutdown(self):
        """Graceful shutdown."""
        if not self.running:
            return

        logger.info("Shutting down...")

        try:
            # 1. Stop accepting new orders
            self.running = False

            # 2. Wait for in-flight orders
            logger.info("Waiting for pending orders to complete...")
            timeout = time.time() + 10  # 10 second timeout
            while self.executor._processing and time.time() < timeout:
                time.sleep(0.1)

            # 3. Close all positions
            logger.info("Closing all open positions...")
            self._close_all_positions()

            # 4. Stop executor
            self.executor.stop()

            # 5. Disconnect
            self.connection.disconnect()
            logger.info("Application shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def _close_all_positions(self):
        """Close all positions before shutdown."""
        try:
            positions = mt5.positions_get()
            if not positions:
                return

            for pos in positions:
                try:
                    close_order = {
                        'action': mt5.TRADE_ACTION_DEAL,
                        'position': pos.ticket,
                        'symbol': pos.symbol,
                        'volume': pos.volume,
                        'type': mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                        'deviation': 50,  # Higher deviation for shutdown
                        'comment': 'Shutdown close',
                        'type_filling': mt5.ORDER_FILLING_IOC,
                    }

                    tick = mt5.symbol_info_tick(pos.symbol)
                    if tick:
                        close_order['price'] = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

                    result = mt5.order_send(close_order)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        logger.info(f"Closed position {pos.ticket}")

                except Exception as e:
                    logger.error(f"Failed to close position {pos.ticket}: {e}")

        except Exception as e:
            logger.error(f"Error closing positions: {e}")

    def _on_signal(self, signum, frame):
        """Signal handler for graceful shutdown."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown()
        exit(0)

# Usage
if __name__ == "__main__":
    app = ProductionMT5App()

    if app.start():
        try:
            # Main trading loop
            while app.running:
                # Place trades, monitor positions, etc.
                time.sleep(1)
        except KeyboardInterrupt:
            app.shutdown()
```

### 6.2 Position/Order State Synchronization

**State Reconciliation Pattern:**
```python
class PositionReconciler:
    """
    Reconciles local order tracking with MT5 actual state.
    Handles discrepancies from network issues, terminal crashes, etc.
    """

    def __init__(self, manager):
        self.manager = manager
        self.local_orders = {}  # ticket -> order_data
        self._lock = threading.RLock()

    def track_order(self, ticket, order_data):
        """Track placed order."""
        with self._lock:
            self.local_orders[ticket] = {
                'data': order_data,
                'created': time.time(),
                'confirmed': False,
            }

    def reconcile(self):
        """
        Reconcile local tracking with actual MT5 positions.
        Returns reconciliation report.
        """
        with self._lock:
            mt5_positions = {
                pos.ticket: pos for pos in mt5.positions_get()
            }

            report = {
                'synced': [],
                'missing': [],
                'unexpected': [],
                'discrepancies': []
            }

            # Check tracked positions exist in MT5
            for ticket, local_data in self.local_orders.items():
                if ticket in mt5_positions:
                    # Verify SL/TP match
                    mt5_pos = mt5_positions[ticket]
                    if local_data['data'].get('sl') != mt5_pos.sl or \
                       local_data['data'].get('tp') != mt5_pos.tp:
                        report['discrepancies'].append({
                            'ticket': ticket,
                            'issue': 'SL/TP mismatch',
                            'local': {
                                'sl': local_data['data'].get('sl'),
                                'tp': local_data['data'].get('tp'),
                            },
                            'actual': {
                                'sl': mt5_pos.sl,
                                'tp': mt5_pos.tp,
                            }
                        })
                    else:
                        report['synced'].append(ticket)
                else:
                    # Position closed or unknown
                    report['missing'].append(ticket)

            # Check for unexpected positions (opened outside system)
            for ticket in mt5_positions:
                if ticket not in self.local_orders:
                    report['unexpected'].append(ticket)

            return report

    def verify_order_complete(self, ticket, timeout=5):
        """Wait for order to appear in MT5 (not just queued)."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            position = mt5.positions_get(ticket=ticket)
            if position:
                return True
            time.sleep(0.2)

        return False
```

### 6.3 Common Pitfalls & Solutions

**Common Issues & Solutions:**

| Issue | Cause | Solution |
|-------|-------|----------|
| `initialize()` returns False | Terminal offline, algo trading disabled | Verify terminal running, check Tools > Options > Advisors |
| No connection even after init | Network issue, broker server down | Check terminal connection status manually, verify network |
| Order always rejected | Insufficient margin, invalid price/stops | Validate margin before order, get fresh tick for price |
| Position not found | Race condition between close and query | Wait 100ms after close before querying |
| SL/TP modification fails | Trying to set invalid levels | Validate levels before modification (SL below entry for BUY) |
| Hanging on order_send() | Broker timeout, network latency | Add timeout wrapper, implement async pattern |
| Wrong account accessed | Multiple accounts configured | Explicit login() or verify account_info().login |
| Terminal crashes | Unstable terminal version, memory issues | Use latest MT5 build, monitor terminal process |

**Timeout Wrapper Pattern:**
```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def execute_with_timeout(func, timeout_seconds=5):
    """Execute function with timeout (Unix only)."""

    # Set alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        return func()
    finally:
        signal.alarm(0)  # Cancel alarm

# Usage
try:
    result = execute_with_timeout(
        lambda: mt5.order_send(request),
        timeout_seconds=5
    )
except TimeoutError:
    print("Order send timed out")
```

---

## 7. Integration with Server Architecture

### 7.1 Async Wrapper for Server Use

**FastAPI Integration Example:**
```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio

app = FastAPI()

# Global MT5 manager
mt5_manager = RobustMT5Manager()

@app.on_event("startup")
async def startup():
    """Initialize MT5 on server start."""
    if not mt5_manager.connect():
        raise RuntimeError("Failed to connect to MT5")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    mt5_manager.disconnect()

@app.post("/api/trade/market-order")
async def place_market_order(
    symbol: str,
    volume: float,
    direction: str,  # "buy" or "sell"
    sl: float = None,
    tp: float = None,
):
    """Place market order endpoint."""

    if not mt5_manager.is_connected():
        raise HTTPException(status_code=503, detail="MT5 not connected")

    try:
        order_type = OrderType.BUY if direction.lower() == "buy" else OrderType.SELL

        result = await asyncio.to_thread(
            mt5_manager.place_market_order,
            symbol=symbol,
            volume=volume,
            order_type=order_type,
            sl=sl,
            tp=tp
        )

        return JSONResponse({
            'status': 'success',
            'ticket': result['ticket'],
            'price': result['price'],
        })

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/positions")
async def get_positions(symbol: str = None):
    """Get all open positions."""

    if not mt5_manager.is_connected():
        raise HTTPException(status_code=503, detail="MT5 not connected")

    try:
        positions = await asyncio.to_thread(
            mt5_manager.get_all_positions,
            symbol=symbol
        )
        return {'positions': positions}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 8. Testing Strategies

**Unit Testing with Mocking:**
```python
import unittest
from unittest.mock import Mock, patch, MagicMock

class TestMT5Manager(unittest.TestCase):

    def setUp(self):
        """Setup test fixtures."""
        self.manager = MT5ConnectionManager()

    @patch('MetaTrader5.initialize')
    @patch('MetaTrader5.terminal_info')
    def test_initialize_success(self, mock_terminal, mock_init):
        """Test successful initialization."""
        mock_init.return_value = True
        mock_terminal.return_value = MagicMock(connected=True)

        result = self.manager.connect()

        self.assertTrue(result)
        self.assertEqual(self.manager.state, ConnectionState.CONNECTED)

    @patch('MetaTrader5.order_send')
    def test_order_placement(self, mock_order_send):
        """Test order placement."""
        mock_result = MagicMock()
        mock_result.retcode = mt5.TRADE_RETCODE_DONE
        mock_result.order = 12345
        mock_order_send.return_value = mock_result

        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': 'EURUSD',
            'volume': 1.0,
        }

        result = mt5.order_send(request)
        self.assertEqual(result.retcode, mt5.TRADE_RETCODE_DONE)
```

---

## 9. Configuration Management

**Config Template (environment-based):**
```python
import os
from dataclasses import dataclass

@dataclass
class MT5Config:
    """MT5 Configuration from environment."""

    # Connection
    ACCOUNT_NUMBER: int = int(os.getenv('MT5_ACCOUNT', '0'))
    ACCOUNT_PASSWORD: str = os.getenv('MT5_PASSWORD', '')
    BROKER_SERVER: str = os.getenv('MT5_SERVER', '')

    # Timing
    CONNECTION_TIMEOUT: float = float(os.getenv('MT5_CONN_TIMEOUT', '30'))
    ORDER_TIMEOUT: float = float(os.getenv('MT5_ORDER_TIMEOUT', '5'))
    HEALTH_CHECK_INTERVAL: float = float(os.getenv('MT5_HEALTH_INTERVAL', '5'))

    # Retry
    MAX_ORDER_RETRIES: int = int(os.getenv('MT5_MAX_RETRIES', '3'))
    RETRY_DELAY: float = float(os.getenv('MT5_RETRY_DELAY', '1'))

    # Circuit breaker
    CIRCUIT_BREAKER_THRESHOLD: int = int(os.getenv('MT5_CB_THRESHOLD', '5'))
    CIRCUIT_BREAKER_TIMEOUT: float = float(os.getenv('MT5_CB_TIMEOUT', '60'))

    # Trading
    DEFAULT_SLIPPAGE: float = float(os.getenv('MT5_SLIPPAGE', '20'))
    ORDER_FILLING: str = os.getenv('MT5_FILLING', 'IOC')  # FOK, IOC, RETURN

# Usage
config = MT5Config()
manager = RobustMT5Manager(
    check_interval=config.HEALTH_CHECK_INTERVAL,
    timeout=config.CONNECTION_TIMEOUT
)
```

---

## 10. Monitoring & Logging

**Structured Logging:**
```python
import logging
import json
from datetime import datetime

class MT5EventLogger:
    """Structured logging for MT5 events."""

    def __init__(self, log_file='mt5_events.jsonl'):
        self.log_file = log_file

    def log_event(self, event_type, data):
        """Log event in JSON format."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'data': data,
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def log_order(self, order_type, symbol, volume, result):
        """Log order placement."""
        self.log_event('order_placed', {
            'order_type': order_type,
            'symbol': symbol,
            'volume': volume,
            'ticket': result.get('ticket'),
            'price': result.get('price'),
            'success': result.get('success', False),
        })

    def log_connection(self, state, error=None):
        """Log connection state change."""
        self.log_event('connection_state', {
            'state': state,
            'error': error,
        })

    def log_error(self, error_type, error_msg, context=None):
        """Log error."""
        self.log_event('error', {
            'error_type': error_type,
            'error_msg': error_msg,
            'context': context,
        })

# Usage
logger = MT5EventLogger()

try:
    result = manager.place_market_order(...)
    logger.log_order('BUY', 'EURUSD', 1.0, result)
except Exception as e:
    logger.log_error('OrderError', str(e), {'symbol': 'EURUSD'})
```

---

## Key Dependencies & Versions

- **MetaTrader5**: Latest stable (pip install MetaTrader5)
- **Python**: 3.7+ (3.9+ recommended)
- **Optional**: FastAPI for REST API, asyncio for async patterns, redis for state sharing across instances

---

## Unresolved Questions

1. **MT5 License for Production**: Does the MT5 platform/broker impose licensing restrictions for automated trading via Python?

2. **State Synchronization Across Instances**: For distributed trading systems, how to maintain consistent position state across multiple Python processes?

3. **Real-time Market Data**: Should dedicated MT5 data streaming be implemented or is order flow sufficient for monitoring?

4. **Backtesting**: Does MetaTrader5 Python package support backtesting/paper trading, or only live/demo accounts?

5. **Rate Limiting**: Are there documented rate limits for order_send() calls per second/minute?

---

## Summary

MetaTrader5 Python provides direct trading automation but requires:
- Terminal dependency (online MT5 required)
- Comprehensive error handling (retry logic, circuit breakers)
- Connection health monitoring (background threads, state machines)
- Proper lifecycle management (graceful init/shutdown)
- Synchronization patterns (state reconciliation, thread safety)

Production systems should employ: circuit breakers, connection managers, order queues, health monitoring, comprehensive logging, and proper timeout handling.
