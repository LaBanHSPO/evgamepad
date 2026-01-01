# Phase 5.2 Environment Variables

## PostgreSQL Database Configuration

Add these variables to your `.env` file to enable accuracy tracking:

```bash
# Phase 5.2: Accuracy Tracking System
ENABLE_ACCURACY_TRACKING=false  # Set to 'true' to enable

# PostgreSQL Connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ev_gamepad
DB_USER=postgres
DB_PASSWORD=your_password_here

# Connection Pool Settings
DB_MIN_POOL_SIZE=2
DB_MAX_POOL_SIZE=10
```

## Setup Instructions

1. **Install PostgreSQL** (if not already installed):
   ```bash
   # macOS
   brew install postgresql@14
   brew services start postgresql@14

   # Ubuntu/Debian
   sudo apt-get install postgresql-14
   sudo systemctl start postgresql
   ```

2. **Create Database**:
   ```bash
   psql -U postgres -c "CREATE DATABASE ev_gamepad;"
   ```

3. **Run Migration**:
   ```bash
   psql -U postgres -d ev_gamepad -f backend/app/database/migrations/005_recommendation_outcomes.sql
   ```

4. **Install asyncpg** (if not in requirements.txt):
   ```bash
   pip install asyncpg
   ```

5. **Update `.env`**:
   ```bash
   ENABLE_ACCURACY_TRACKING=true
   DB_PASSWORD=your_actual_password
   ```

6. **Restart Server**:
   The accuracy tracking system will initialize automatically on startup.

## Verification

Check health endpoint to verify database connection:
```bash
curl http://localhost:8686/health
```

Expected response:
```json
{
  "status": "healthy",
  "mt5_connected": true,
  "redis_connected": true,
  "db_connected": true,
  "accuracy_tracking_enabled": true,
  "connected_clients": 0
}
```

## Background Tasks

When enabled, the system will:
- Sync MT5 closed positions every 5 minutes
- Auto-detect trade outcomes from MT5 history
- Refresh accuracy materialized view on each outcome record
- Track performance metrics by symbol/timeframe/signal

## Socket.IO Events

### Record Outcome
```javascript
socket.emit('advisor:record_outcome', {
  symbol: 'XAUUSD',
  timeframe: 'H1',
  signal: 'BUY',
  confidence: 85,
  entry_price: 2634.50,
  exit_price: 2640.20,
  stop_loss: 2625.50,
  take_profit: 2645.00,
  exit_reason: 'take_profit'
});
```

### Get Accuracy Report
```javascript
socket.emit('advisor:accuracy_report', {
  symbol: 'XAUUSD',
  timeframe: 'H1',
  days: 30
});
```
