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

4. Setup PostgreSQL (Phase 01 & 02):
   ```bash
   # Run database migrations
   psql -U postgres -d ev_gamepad -f migrations/001_create_game_sessions.sql
   psql -U postgres -d ev_gamepad -f migrations/002_create_teams.sql
   psql -U postgres -d ev_gamepad -f migrations/003_create_team_members.sql
   psql -U postgres -d ev_gamepad -f migrations/004_create_positions_table.sql
   psql -U postgres -d ev_gamepad -f migrations/005_create_materialized_view.sql
   psql -U postgres -d ev_gamepad -f migrations/006_create_mt5_account_pool.sql
   psql -U postgres -d ev_gamepad -f migrations/007_create_mt5_orders.sql
   psql -U postgres -d ev_gamepad -f migrations/008_add_mt5_ticket_to_positions.sql
   ```

## MT5 Account Pool Setup (Phase 02)

Phase 02 introduces account pool management for multi-player trading.

### Prerequisites
- 10 MT5 demo accounts from your broker
- PostgreSQL database configured
- Redis server running

### Setup Steps

1. **Generate Encryption Key**:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Add to `.env`**:
   ```
   MT5_ENCRYPTION_KEY=your_generated_key_here
   ```

3. **Create Account Configuration**:
   ```bash
   # Copy example and edit with your accounts
   cp scripts/accounts.example.json scripts/accounts.json
   # Edit scripts/accounts.json with real credentials
   ```

4. **Provision Account Pool**:
   ```bash
   python scripts/setup_mt5_account_pool.py --accounts scripts/accounts.json
   ```

### Verify Pool Status

Check account pool in database:
```sql
SELECT
    account_number,
    status,
    health_status,
    allocated_to_user_id,
    expiry_date
FROM mt5_account_pool
ORDER BY account_number;
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
