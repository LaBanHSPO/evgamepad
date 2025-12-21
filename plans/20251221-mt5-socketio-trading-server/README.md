# MT5 Socket.IO Trading Server - Implementation Plan

**Created**: 2025-12-21
**Status**: Ready for Implementation

---

## Plan Overview

Comprehensive implementation plan for secure, reliable Python Socket.IO server enabling MT5 trading automation with real-time bidirectional communication.

### Quick Links
- **[Main Plan](./plan.md)** - Complete specification & architecture
- **[Phase 1](./phase-01-mt5-foundation.md)** - MT5 Integration Foundation
- **[Research Reports](./research/)** - Technical research findings

---

## Implementation Phases

### Phase 1: MT5 Foundation & Integration ✅ Ready
- MT5 connection manager with health monitoring
- Trading operations (buy/sell/modify/close)
- Error handling with retry logic
- Configuration management

**Acceptance**: Orders execute on demo account with full logging

---

### Phase 2: Socket.IO Server Setup
- FastAPI + python-socketio integration
- Event handlers (login, buy, sell, modify, close)
- Command validation
- Session management

**Acceptance**: Clients connect and receive acknowledgments

---

### Phase 3: Command Integration
- Wire Socket.IO events to MT5 operations
- Response formatting
- Logging enhancement
- Request ID tracking

**Acceptance**: All commands execute MT5 operations successfully

---

### Phase 4: Reliability & Error Handling
- Circuit breaker pattern
- Reconnection logic with state recovery
- Error classification
- Comprehensive testing

**Acceptance**: Survives network drops and MT5 crashes

---

### Phase 5: Production Readiness
- Docker configuration
- Health checks
- Metrics (optional)
- Documentation

**Acceptance**: Deployable via Docker, documented API

---

## Technology Stack

- **Language**: Python 3.11+
- **MT5 Integration**: MetaTrader5 package (official)
- **Communication**: python-socketio + ASGI
- **Server Framework**: FastAPI
- **Runtime**: uvicorn (ASGI server)
- **Testing**: pytest + pytest-asyncio

---

## Core Requirements

1. **MT5 Operations**
   - Login to MT5 account
   - Place buy/sell market orders
   - Modify position TP/SL
   - Close positions

2. **Communication**
   - Real-time Socket.IO (WebSocket-based)
   - Bidirectional command/response
   - Auto-reconnection support

3. **Reliability**
   - Connection health monitoring
   - Error handling with retry logic
   - State recovery after disconnect

4. **Security**
   - VPN-only access (no auth layer initially)
   - MT5 credentials via environment variables

5. **Logging**
   - Development-focused verbose output
   - Structured JSON formatting
   - Full command trace

---

## Research Findings

### MT5 Python Integration
- Terminal must be running with algo trading enabled
- Package requires terminal-side DLL bindings
- Synchronous API (wrap in async for Socket.IO)
- Connection health monitoring essential
- Circuit breaker prevents hammering broken connections

**See**: [MT5 Research Report](./research/researcher-251221-mt5-python-integration.md)

### Socket.IO Architecture
- **Recommendation**: python-socketio + ASGI (not Flask-SocketIO)
- 10-100x better concurrency vs thread-based models
- Native async/await for trading workflows
- Redis pub/sub for horizontal scaling
- Message acknowledgments prevent loss

**See**: [Socket.IO Research Report](./research/researcher-20251221-socketio-trading-server.md)

---

## Getting Started

### Prerequisites
1. MetaTrader5 terminal installed
2. Demo or live account configured
3. Algo trading enabled (Tools > Options > Advisors)
4. Python 3.11+ installed
5. VPN access configured

### Quick Start
```bash
# Clone/navigate to backend directory
cd backend

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with MT5 credentials

# Run server
python -m app.main
```

Server runs on http://0.0.0.0:5000

---

## API Overview

### Socket.IO Events (Client → Server)

**`login`** - Authenticate MT5 account
```json
{ "account": 12345678, "password": "***", "server": "Broker-Demo" }
```

**`buy`** - Market buy order
```json
{ "symbol": "EURUSD", "volume": 0.01, "sl": 1.0800, "tp": 1.0900 }
```

**`sell`** - Market sell order
```json
{ "symbol": "EURUSD", "volume": 0.01, "sl": 1.0900, "tp": 1.0800 }
```

**`modify`** - Modify position TP/SL
```json
{ "ticket": 123456, "sl": 1.0810, "tp": 1.0910 }
```

**`close`** - Close position
```json
{ "ticket": 123456, "volume": 0.01 }
```

### Responses (Server → Client)

**`order_result`** - Success
```json
{ "success": true, "ticket": 123456, "price": 1.0850 }
```

**`error`** - Failure
```json
{ "success": false, "code": "INSUFFICIENT_MARGIN", "message": "..." }
```

---

## File Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI + Socket.IO entry point
│   ├── config.py                  # Configuration
│   ├── logging_config.py          # Logging setup
│   ├── mt5/
│   │   ├── connection_manager.py  # MT5 lifecycle
│   │   ├── trading_operations.py  # Orders/positions
│   │   ├── circuit_breaker.py     # Fault tolerance
│   │   └── error_handler.py       # Error mapping
│   ├── events/
│   │   └── trading_events.py      # Socket.IO handlers
│   ├── processors/
│   │   └── command_processor.py   # Event routing
│   └── models/
│       ├── commands.py            # Command schemas
│       └── responses.py           # Response schemas
├── tests/
│   ├── test_connection_manager.py
│   ├── test_trading_operations.py
│   └── test_events.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

---

## Success Criteria

### Functional
- ✅ Connect to MT5 terminal successfully
- ✅ Place buy/sell orders with confirmation
- ✅ Modify position TP/SL correctly
- ✅ Close positions on command
- ✅ Socket.IO clients connect/disconnect cleanly
- ✅ All errors logged with stack traces

### Reliability
- ✅ Server recovers from MT5 terminal crash
- ✅ Client reconnection resumes session
- ✅ Circuit breaker prevents cascading failures
- ✅ Order placement latency < 200ms (p99)

### Developer Experience
- ✅ Setup time < 30 minutes
- ✅ All tests pass
- ✅ Documentation covers common scenarios

---

## Next Steps

1. Review plan.md for complete architecture
2. Review phase-01-mt5-foundation.md for first implementation
3. Setup development environment
4. Implement Phase 1 (MT5 integration)
5. Test on MT5 demo account
6. Proceed to Phase 2 (Socket.IO server)

---

## Questions?

See **Unresolved Questions** in main plan:
- MT5 terminal hosting strategy
- Order state persistence approach
- Multi-client/multi-account handling
- Position tracking strategy

---

**Plan Status**: ✅ Ready for Implementation
**First Phase**: Phase 1 - MT5 Foundation & Integration
