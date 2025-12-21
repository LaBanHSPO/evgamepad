# MT5 SocketIO Server - Phase 1

## Overview
Phase 1 implements the foundation for the MT5 SocketIO Trading Server, including:
- Connection management with health checks and auto-reconnection
- Trading operations (Buy, Sell, Modify, Close)
- Error handling with retry logic
- Configuration management

## Setup

### Prerequisites
- Windows OS (required for MetaTrader5 Python package)
- MetaTrader 5 Terminal installed
- Python 3.11+

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Environment:
   ```bash
   copy .env.example .env
   # Edit .env with your MT5 account credentials
   ```

## Running Tests

To run the unit tests:
```bash
pytest tests/
```

Note: The tests use mocks and can run on non-Windows systems if `MetaTrader5` is mocked in `sys.modules` (handled in `tests/conftest.py`).

## Usage Example

```python
import asyncio
from app.mt5.connection_manager import MT5ConnectionManager
from app.mt5.trading_operations import TradingOperations

async def main():
    manager = MT5ConnectionManager()
    if manager.connect():
        ops = TradingOperations(manager)
        
        # Place buy order
        result = await ops.place_buy_market("EURUSD", 0.01)
        print(result)
        
        manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```
