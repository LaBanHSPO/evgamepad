# MT5 Socket.IO Trading Server Implementation Plan
**Date**: 2025-12-21
**Status**: Draft
**Type**: Greenfield Implementation

---

## 1. EXECUTIVE SUMMARY

### Objective
Build secure, reliable Python Socket.IO server for MT5 trading automation with real-time bidirectional communication over VPN.

### Core Requirements
- **Login to MT5**: Account authentication & terminal connection management
- **Trading Operations**: Buy/sell market orders, modify TP/SL, close positions
- **Communication**: Socket.IO (WebSocket-based) for real-time command/response
- **Security Model**: VPN-only access (no authentication layer initially)
- **Reliability**: Auto-reconnection, error handling, state recovery
- **Logging**: Development-focused verbose debug output

### Technology Stack
- **MT5 Integration**: MetaTrader5 Python package (official bindings)
- **Communication Protocol**: python-socketio + ASGI (FastAPI)
- **Server Runtime**: uvicorn (ASGI server)
- **State Management**: In-memory (Redis optional for future scaling)
- **Logging**: Python logging module with JSON formatting

### Success Criteria
- ✅ Server accepts Socket.IO connections from VPN clients
- ✅ Server connects to MT5 terminal and authenticates account
- ✅ Buy/sell orders execute successfully with confirmation
- ✅ TP/SL modifications apply correctly
- ✅ Positions close on command
- ✅ Reconnection after network drop recovers session
- ✅ All errors logged with stack traces for debugging

---

## 2. SYSTEM ARCHITECTURE

### Component Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Client (VPN Network)                     │
│                 Socket.IO Client (JavaScript)               │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket (Socket.IO Protocol)
                         │ Commands: login, buy, sell, modify, close
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Python Socket.IO Server (ASGI)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  FastAPI + python-socketio                           │  │
│  │  - Event handlers (login, buy, sell, modify, close)  │  │
│  │  - Command validation & routing                      │  │
│  │  - Error handling & logging                          │  │
│  │  - Session state management                          │  │
│  └──────────────┬──────────────────────────────────────┬┘  │
│                 │                                       │   │
│      ┌──────────▼─────────┐                 ┌──────────▼──────────┐
│      │ MT5 Connection     │                 │  Session Manager    │
│      │ Manager            │                 │  - Client states    │
│      │ - Initialize()     │                 │  - Pending orders   │
│      │ - Health monitor   │                 │  - Reconnect logic  │
│      │ - Circuit breaker  │                 │                     │
│      └──────────┬─────────┘                 └─────────────────────┘
│                 │                                                  │
└─────────────────┼──────────────────────────────────────────────────┘
                  │ MetaTrader5 Python API
                  │
┌─────────────────▼────────────────────────────────────────────┐
│               MetaTrader5 Terminal                           │
│  - Must be running with algo trading enabled                 │
│  - Connected to broker server                                │
│  - Account logged in                                         │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow - Order Placement Example
```
Client                Socket.IO Server          MT5 Manager          MT5 Terminal
  │                          │                       │                     │
  ├─ emit('buy_order')─────>│                       │                     │
  │  {symbol, volume, sl, tp}│                       │                     │
  │                          │                       │                     │
  │                          ├─ validate_command()   │                     │
  │                          ├─ process_buy()────────>                     │
  │                          │                       ├─ place_market_order()
  │                          │                       │                     │
  │                          │                       ├───mt5.order_send()─>│
  │                          │                       │                     │
  │                          │                       │<── result (ticket)──┤
  │                          │                       │                     │
  │                          │<─ return result ──────┤                     │
  │                          │                       │                     │
  │<── emit('order_result')──┤                       │                     │
  │    {success, ticket, price}                     │                     │
```

---

## 3. IMPLEMENTATION PHASES

### Phase 1: Foundation & MT5 Integration
**Goal**: Establish MT5 connection and basic order execution
**Duration**: Core implementation only

#### Deliverables
1. **MT5 Connection Manager** (`app/mt5/connection_manager.py`)
   - Initialize MT5 terminal connection
   - Account login & verification
   - Health monitoring with background thread
   - Graceful shutdown sequence

2. **Trading Operations Module** (`app/mt5/trading_operations.py`)
   - `place_market_order(symbol, volume, order_type, sl, tp)`
   - `modify_position(ticket, new_sl, new_tp)`
   - `close_position(ticket, volume)`
   - Error handling with retry logic

3. **Configuration Management** (`app/config.py`)
   - Environment-based configuration
   - MT5 account credentials (via .env)
   - Connection parameters (timeout, retry limits)

4. **Testing**
   - Manual MT5 terminal setup verification
   - Unit tests for connection manager (mocked MT5)
   - Integration test: place test order on demo account

#### Acceptance Criteria
- [ ] MT5 initializes and connects successfully
- [ ] Can place buy/sell market orders with SL/TP
- [ ] Can modify existing position TP/SL
- [ ] Can close positions
- [ ] All operations log debug output
- [ ] Connection survives MT5 terminal restart (with reconnection)

---

### Phase 2: Socket.IO Server Setup
**Goal**: Establish real-time communication infrastructure

#### Deliverables
1. **Socket.IO Server** (`app/main.py`)
   - FastAPI + python-socketio integration
   - ASGI application setup
   - Connection/disconnection event handlers
   - Error event handling

2. **Event Handlers** (`app/events/trading_events.py`)
   - `on_login(sid, data)` - MT5 account login
   - `on_buy(sid, data)` - Market buy order
   - `on_sell(sid, data)` - Market sell order
   - `on_modify(sid, data)` - Modify TP/SL
   - `on_close(sid, data)` - Close position

3. **Command Validation** (`app/validation.py`)
   - Input schema validation (symbol, volume, price)
   - Required field checks
   - Data type validation

4. **Session Management** (`app/session_manager.py`)
   - Track connected clients
   - Store pending orders per session
   - Cleanup on disconnect

#### Acceptance Criteria
- [ ] Server starts on port 5000 (configurable)
- [ ] Clients can connect via Socket.IO
- [ ] Server logs all connection/disconnection events
- [ ] Commands emit acknowledgment responses
- [ ] Invalid commands return structured errors

---

### Phase 3: Command Integration
**Goal**: Wire Socket.IO events to MT5 operations

#### Deliverables
1. **Command Processor** (`app/processors/command_processor.py`)
   - Route events to MT5 operations
   - Async execution (non-blocking)
   - Result/error propagation to client

2. **Response Formatting** (`app/responses.py`)
   - Structured success responses
   - Error response with codes & details
   - Order result schema

3. **Logging Enhancement** (`app/logging_config.py`)
   - JSON structured logging
   - Request ID tracking (per command)
   - Client ID correlation

#### Acceptance Criteria
- [ ] `buy` command places MT5 order, returns ticket
- [ ] `sell` command places MT5 order, returns ticket
- [ ] `modify` command updates position TP/SL
- [ ] `close` command closes position
- [ ] All errors return structured error responses
- [ ] Logs contain full command trace (request → MT5 → response)

---

### Phase 4: Reliability & Error Handling
**Goal**: Production-grade error recovery and reconnection

#### Deliverables
1. **Circuit Breaker** (`app/mt5/circuit_breaker.py`)
   - Prevent hammering broken MT5 connection
   - Auto-recovery after timeout

2. **Reconnection Logic**
   - Client reconnection detection
   - Pending order recovery
   - Session state restoration

3. **Error Classification** (`app/errors.py`)
   - Define error codes (INVALID_SYMBOL, INSUFFICIENT_MARGIN, etc.)
   - Retriable vs terminal errors
   - User-friendly error messages

4. **Comprehensive Testing**
   - Reconnection test (disconnect/reconnect client)
   - MT5 terminal crash recovery
   - Network latency simulation
   - Error scenario coverage

#### Acceptance Criteria
- [ ] Server recovers from MT5 terminal crash
- [ ] Client reconnection resumes session
- [ ] Circuit breaker opens after 5 MT5 failures
- [ ] All error codes documented
- [ ] Pending orders tracked across reconnections

---

### Phase 5: Production Readiness
**Goal**: Deployment-ready server with monitoring

#### Deliverables
1. **Docker Configuration**
   - Dockerfile (Python 3.11-slim base)
   - docker-compose.yml (optional Redis for future)
   - Environment variables template

2. **Health Checks** (`/health` endpoint)
   - Server status
   - MT5 connection status
   - Connected clients count

3. **Metrics** (optional Prometheus)
   - Orders placed counter
   - Errors counter by type
   - Command latency histogram

4. **Documentation**
   - API reference (Socket.IO events & payloads)
   - Setup guide (MT5 terminal configuration)
   - Client integration examples

#### Acceptance Criteria
- [ ] Server runs in Docker container
- [ ] Health endpoint returns 200 OK when healthy
- [ ] README.md with setup instructions
- [ ] Client can connect from separate machine over VPN

---

## 4. FILE STRUCTURE

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI + Socket.IO entry point
│   ├── config.py                  # Configuration from env vars
│   ├── logging_config.py          # Structured logging setup
│   │
│   ├── mt5/
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # MT5 connection lifecycle
│   │   ├── trading_operations.py  # Order/position operations
│   │   ├── circuit_breaker.py     # Fault tolerance
│   │   └── error_handler.py       # MT5 error code mapping
│   │
│   ├── events/
│   │   ├── __init__.py
│   │   └── trading_events.py      # Socket.IO event handlers
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   └── command_processor.py   # Event → MT5 operation routing
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── commands.py            # Command data classes
│   │   └── responses.py           # Response schemas
│   │
│   ├── validation.py              # Input validation
│   ├── session_manager.py         # Client session tracking
│   └── errors.py                  # Error codes & classes
│
├── tests/
│   ├── __init__.py
│   ├── test_connection_manager.py
│   ├── test_trading_operations.py
│   ├── test_command_processor.py
│   └── test_events.py
│
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 5. API SPECIFICATION

### Socket.IO Events

#### Client → Server

**1. `login`** - Authenticate MT5 account
```json
{
  "account": 12345678,
  "password": "your_password",
  "server": "BrokerServer-Demo"
}
```
Response:
```json
{
  "success": true,
  "account_info": {
    "login": 12345678,
    "name": "Account Name",
    "balance": 10000.00,
    "equity": 10000.00,
    "currency": "USD"
  }
}
```

**2. `buy`** - Place buy market order
```json
{
  "symbol": "EURUSD",
  "volume": 0.01,
  "sl": 1.0800,
  "tp": 1.0900
}
```
Response:
```json
{
  "success": true,
  "ticket": 123456789,
  "price": 1.0850,
  "volume": 0.01,
  "timestamp": "2025-12-21T10:30:00Z"
}
```

**3. `sell`** - Place sell market order
```json
{
  "symbol": "EURUSD",
  "volume": 0.01,
  "sl": 1.0900,
  "tp": 1.0800
}
```

**4. `modify`** - Modify position TP/SL
```json
{
  "ticket": 123456789,
  "sl": 1.0810,
  "tp": 1.0910
}
```
Response:
```json
{
  "success": true,
  "ticket": 123456789,
  "new_sl": 1.0810,
  "new_tp": 1.0910
}
```

**5. `close`** - Close position
```json
{
  "ticket": 123456789,
  "volume": 0.01  // optional, full close if omitted
}
```
Response:
```json
{
  "success": true,
  "ticket": 123456789,
  "close_price": 1.0860,
  "profit": 10.00,
  "closed_at": "2025-12-21T10:35:00Z"
}
```

#### Server → Client

**`order_result`** - Order execution result
```json
{
  "success": true,
  "command_id": "uuid",
  "ticket": 123456789,
  "price": 1.0850
}
```

**`error`** - Error notification
```json
{
  "success": false,
  "code": "INSUFFICIENT_MARGIN",
  "message": "Not enough margin to place order",
  "details": {
    "required": 100.0,
    "available": 50.0
  }
}
```

---

## 6. ERROR CODES

| Code | Description | Retriable | Action |
|------|-------------|-----------|--------|
| `VALIDATION_ERROR` | Missing/invalid fields | No | Fix request payload |
| `MT5_NOT_CONNECTED` | MT5 terminal offline | Yes | Wait for reconnection |
| `INVALID_SYMBOL` | Symbol not found | No | Check symbol name |
| `INSUFFICIENT_MARGIN` | Not enough margin | No | Reduce volume or add funds |
| `ORDER_REJECTED` | Broker rejected order | No | Check account restrictions |
| `POSITION_NOT_FOUND` | Position doesn't exist | No | Verify ticket number |
| `TIMEOUT` | Operation timed out | Yes | Retry command |
| `INTERNAL_ERROR` | Server error | Maybe | Check logs, contact support |

---

## 7. CONFIGURATION

### Environment Variables (.env)
```bash
# MT5 Configuration
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=BrokerServer-Demo

# Server Configuration
SOCKETIO_HOST=0.0.0.0
SOCKETIO_PORT=5000
DEBUG=true

# MT5 Connection
MT5_CONN_TIMEOUT=30
MT5_HEALTH_INTERVAL=5
MT5_MAX_RETRIES=3
MT5_RETRY_DELAY=1

# Circuit Breaker
MT5_CB_THRESHOLD=5
MT5_CB_TIMEOUT=60

# Trading
MT5_SLIPPAGE=20
MT5_FILLING=IOC
```

---

## 8. DEPLOYMENT

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start MT5 terminal (must be running)
# Enable algo trading: Tools > Options > Advisors > Allow automated trading

# Run server
python -m app.main

# Server runs on http://0.0.0.0:5000
```

### Docker
```bash
# Build image
docker build -t mt5-socketio-server .

# Run container
docker run -p 5000:5000 \
  --env-file .env \
  mt5-socketio-server
```

### VPN Requirements
- Server must be accessible via VPN
- Clients connect using VPN IP address
- No public internet exposure required
- Firewall: Allow port 5000 TCP (configurable)

---

## 9. TESTING STRATEGY

### Unit Tests
- Mock MT5 package (`unittest.mock`)
- Test connection manager state machine
- Test order validation logic
- Test error handling paths

### Integration Tests
- Connect to MT5 demo account
- Place real test orders (small volume)
- Verify order execution
- Test reconnection scenarios

### Manual Testing Checklist
- [ ] Start server, verify health endpoint
- [ ] Connect client via Socket.IO
- [ ] Place buy order → verify in MT5 terminal
- [ ] Place sell order → verify in MT5 terminal
- [ ] Modify position TP/SL → verify update
- [ ] Close position → verify closure
- [ ] Disconnect client → reconnect → verify session recovery
- [ ] Restart MT5 terminal → verify reconnection
- [ ] Send invalid command → verify error response
- [ ] Check logs for all operations

---

## 10. SECURITY CONSIDERATIONS

### Current (VPN-Only)
- **Access Control**: VPN provides network-level security
- **No Authentication**: Socket.IO accepts any connection from VPN
- **Credential Storage**: MT5 credentials in .env file (server-side)
- **Logging**: Full debug logs (may contain sensitive data)

### Future Enhancements (Not in Scope)
- JWT authentication on Socket.IO connect
- Per-user API keys
- Role-based access control (RBAC)
- Rate limiting per client
- Audit logging (who placed which orders)
- Encrypted credentials (vault integration)

---

## 11. MONITORING & OBSERVABILITY

### Logging
- **Format**: JSON structured logs
- **Fields**: timestamp, level, client_id, command_id, action, result
- **Output**: Console (stdout) for Docker log collection
- **Log Levels**: DEBUG (development), INFO (production)

### Health Checks
- `/health` endpoint returns:
  ```json
  {
    "status": "healthy",
    "mt5_connected": true,
    "connected_clients": 2,
    "uptime_seconds": 3600
  }
  ```

### Metrics (Optional - Phase 5)
- `socketio_connected_clients` (gauge)
- `orders_placed_total` (counter)
- `errors_total` (counter by error_code)
- `command_latency_ms` (histogram)

---

## 12. DEPENDENCIES

### Core
```
python = "^3.11"
fastapi = "^0.104.0"
python-socketio = "^5.10.0"
uvicorn = "^0.24.0"
MetaTrader5 = "^5.0.45"
python-dotenv = "^1.0.0"
```

### Development
```
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
flake8 = "^6.1.0"
```

### Optional
```
redis = "^5.0.0"  # For multi-instance scaling
prometheus-client = "^0.18.0"  # For metrics
python-json-logger = "^2.0.0"  # For structured logging
```

---

## 13. RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|------|--------|------------|
| MT5 terminal crashes | Orders fail | Circuit breaker, auto-reconnection, health monitoring |
| Network latency spikes | Timeout errors | Configurable timeouts, retry logic, client-side timeout handling |
| Concurrent order conflicts | Race conditions | Sequential order queue (Phase 4) |
| Memory leak from pending orders | Server crash | TTL cleanup task, max pending limit |
| VPN connection loss | Client disconnect | Socket.IO auto-reconnect, session recovery |
| MT5 API rate limits | Order rejection | Per-minute throttling (future enhancement) |

---

## 14. UNRESOLVED QUESTIONS

1. **MT5 Terminal Hosting**: Should MT5 run on same machine as server or separate?
   - Same machine: Simpler setup, single point of failure
   - Separate: More resilient, requires network access

2. **Order State Persistence**: Should pending orders be stored in database or in-memory?
   - In-memory: Faster, lost on restart
   - Database: Survives restart, adds complexity

3. **Multi-Client Handling**: Should one server handle multiple MT5 accounts?
   - Single account: Simpler, one server per account
   - Multi-account: More complex, shared infrastructure

4. **Position Tracking**: Should server track all positions or query MT5 on-demand?
   - Track locally: Faster lookups, sync complexity
   - Query MT5: Always current, slower

5. **Partial Fills**: How to notify client of partial order fills?
   - Poll positions endpoint
   - Real-time broadcast via Socket.IO

---

## 15. SUCCESS METRICS

### Functional
- ✅ 100% command success rate on demo account
- ✅ Order placement latency < 200ms (p99)
- ✅ Zero lost orders during reconnection
- ✅ All error scenarios logged correctly

### Reliability
- ✅ Server uptime > 99% (excludes planned restarts)
- ✅ Reconnection success rate > 95%
- ✅ Circuit breaker triggers prevent cascading failures

### Developer Experience
- ✅ Setup time < 30 minutes
- ✅ All tests pass in CI
- ✅ Documentation covers all common scenarios

---

## 16. NEXT STEPS

After plan approval:
1. Setup project structure (`backend/app/` directories)
2. Create `requirements.txt` with dependencies
3. Implement Phase 1 (MT5 connection manager)
4. Test MT5 integration on demo account
5. Proceed to Phase 2 (Socket.IO server)

**Estimated Timeline**: Implementation-only (no estimates provided per project guidelines)

---

## APPENDIX A: MT5 Terminal Setup

### Prerequisites
1. Download & install MetaTrader5 from broker
2. Login to demo/live account
3. Enable algorithmic trading:
   - Tools > Options > Advisors tab
   - Check "Allow algorithmic trading"
   - Check "Allow DLL imports" (for Python bindings)

### Verify Installation
```python
import MetaTrader5 as mt5

if mt5.initialize():
    print("MT5 version:", mt5.version())
    print("Terminal info:", mt5.terminal_info())
    mt5.shutdown()
else:
    print("MT5 initialization failed")
```

---

## APPENDIX B: Client Example (JavaScript)

```javascript
const io = require('socket.io-client');

const socket = io('http://vpn-server-ip:5000');

socket.on('connect', () => {
  console.log('Connected to MT5 server');

  // Login to MT5
  socket.emit('login', {
    account: 12345678,
    password: 'password',
    server: 'BrokerServer-Demo'
  });
});

socket.on('order_result', (data) => {
  console.log('Order result:', data);
});

socket.on('error', (err) => {
  console.error('Error:', err);
});

// Place buy order
socket.emit('buy', {
  symbol: 'EURUSD',
  volume: 0.01,
  sl: 1.0800,
  tp: 1.0900
});
```

---

## REFERENCES

- MetaTrader5 Python Documentation: https://www.mql5.com/en/docs/integration/python_metatrader5
- python-socketio Documentation: https://python-socketio.readthedocs.io/
- FastAPI Documentation: https://fastapi.tiangolo.com/

---

**Plan Status**: Ready for implementation
**Review Required**: Architecture, security model, error handling strategy
