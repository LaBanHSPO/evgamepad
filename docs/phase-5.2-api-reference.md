# Phase 5.2 - Accuracy Tracking System API Reference

**Date:** 2025-12-31
**Phase:** 5.2 - Accuracy Tracking System
**Version:** 1.0.0

---

## Overview

Phase 5.2 introduces automated trade outcome tracking and performance analytics. The system provides:

1. **Manual Outcome Recording** - Record trade results via Socket.IO events
2. **MT5 Auto-Detection** - Automatic sync of closed positions (5-minute background sync)
3. **Performance Metrics** - Win rate, profit factor, Sharpe ratio, and more
4. **Configuration Analysis** - Find best-performing symbol/timeframe/signal combinations
5. **Per-User Tracking** - Filter metrics by user, symbol, timeframe, and date range

---

## Socket.IO Events

### 1. Record Outcome Event

**Event Name:** `advisor:record_outcome`

**Purpose:** Manually record a trade outcome

**Request Payload:**
```json
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "signal": "BUY",
  "confidence": 85,
  "entry_price": 2634.50,
  "exit_price": 2640.20,
  "stop_loss": 2625.50,
  "take_profit": 2645.00,
  "exit_reason": "take_profit",
  "entry_at": "2025-12-31T10:30:00Z",
  "exit_at": "2025-12-31T14:45:00Z",
  "recommendation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| symbol | string | Yes | Trading symbol (e.g., XAUUSD, EURUSD) |
| timeframe | string | Yes | Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1) |
| signal | string | Yes | BUY, SELL, or HOLD |
| confidence | number | Yes | Confidence score 0-100 |
| entry_price | number | Yes | Entry price (must be > 0) |
| exit_price | number | Yes | Exit price (must be > 0) |
| stop_loss | number | No | Stop loss price |
| take_profit | number | No | Take profit price |
| exit_reason | string | Yes | take_profit, stop_loss, manual, or timeout |
| entry_at | string (ISO 8601) | No | Entry timestamp (defaults to now) |
| exit_at | string (ISO 8601) | No | Exit timestamp (defaults to now) |
| recommendation_id | string (UUID) | No | Link to original recommendation |

**Response (Success):**
```json
{
  "success": true,
  "outcome_id": "a1b2c3d4-e5f6-4a8b-9c0d-1e2f3a4b5c6d",
  "message": "Outcome recorded successfully"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Whether operation succeeded |
| outcome_id | string (UUID) | ID of created outcome record |
| message | string | Status message |

**Response (Error):**
```json
{
  "success": false,
  "message": "Invalid signal: MAYBE (must be BUY, SELL, or HOLD)"
}
```

**Calculated Metrics (Automatic):**

The system automatically calculates:
- **P/L:** `exit_price - entry_price` (for BUY), `entry_price - exit_price` (for SELL)
- **P/L %:** `(P/L / entry_price) * 100`
- **Outcome:**
  - "win" if P/L% > 0.1%
  - "loss" if P/L% < -0.1%
  - "break_even" if abs(P/L%) <= 0.1%
- **Matched Prediction:** Boolean indicating if price moved as predicted
- **Held Duration:** `exit_at - entry_at` in days/hours/minutes

**Example Usage (JavaScript):**
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
}, (response) => {
  if (response.success) {
    console.log('Outcome recorded:', response.outcome_id);
  } else {
    console.error('Error:', response.message);
  }
});
```

**Error Cases:**

1. **Validation Error - Invalid Signal:**
   ```json
   {"success": false, "message": "Invalid signal: MAYBE"}
   ```

2. **Validation Error - Invalid Price:**
   ```json
   {"success": false, "message": "Entry price must be > 0"}
   ```

3. **Validation Error - Invalid Confidence:**
   ```json
   {"success": false, "message": "Confidence must be between 0 and 100"}
   ```

4. **Database Error:**
   ```json
   {"success": false, "message": "Failed to record outcome: connection timeout"}
   ```

---

### 2. Accuracy Report Event

**Event Name:** `advisor:accuracy_report`

**Purpose:** Get accuracy metrics and performance statistics

**Request Payload:**
```json
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "signal": "BUY",
  "days": 30,
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| symbol | string | No | Filter by symbol (e.g., XAUUSD) |
| timeframe | string | No | Filter by timeframe (M1, M5, H1, H4, D1, etc.) |
| signal | string | No | Filter by signal (BUY, SELL, HOLD) |
| days | number | No | Analysis period in days (default: 30, max: 365) |
| user_id | string (UUID) | No | Filter by user ID |

**Response (Success with data):**
```json
{
  "success": true,
  "data": {
    "period_days": 30,
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "signal": "BUY",
    "total_trades": 50,
    "wins": 35,
    "losses": 15,
    "break_evens": 0,
    "win_rate_pct": 70.0,
    "avg_pnl_pct": 2.5,
    "avg_win_pct": 4.2,
    "avg_loss_pct": 1.8,
    "profit_factor": 2.33,
    "sharpe_ratio": 1.39,
    "best_trade_pct": 12.5,
    "worst_trade_pct": -5.2,
    "avg_hold_hours": 4.5,
    "recommendation": "Excellent - High confidence trades",
    "best_performing_configs": [
      {
        "symbol": "XAUUSD",
        "timeframe": "H4",
        "signal": "BUY",
        "total_trades": 25,
        "win_rate_pct": 76.0,
        "avg_pnl_pct": 3.2,
        "profit_factor": 2.8
      }
    ]
  }
}
```

**Response Fields (Metrics):**

| Field | Type | Description |
|-------|------|-------------|
| period_days | number | Analysis period in days |
| symbol | string\|null | Filtered symbol |
| timeframe | string\|null | Filtered timeframe |
| signal | string\|null | Filtered signal |
| total_trades | number | Total number of closed trades |
| wins | number | Number of winning trades |
| losses | number | Number of losing trades |
| break_evens | number | Number of break-even trades |
| win_rate_pct | number | % of trades that were wins (0-100) |
| avg_pnl_pct | number | Average P/L % across all trades |
| avg_win_pct | number | Average P/L % for winning trades |
| avg_loss_pct | number | Average P/L % for losing trades (absolute) |
| profit_factor | number | Ratio of total wins to total losses |
| sharpe_ratio | number\|null | Return-to-volatility ratio |
| best_trade_pct | number | Best single trade P/L % |
| worst_trade_pct | number | Worst single trade P/L % |
| avg_hold_hours | number | Average hold duration in hours |
| recommendation | string | Performance assessment text |
| best_performing_configs | array | Top 10 symbol/timeframe/signal combos |

**Recommendation Levels:**

| Win Rate | Profit Factor | Recommendation |
|----------|---------------|-----------------|
| >= 70% | >= 2.0 | Excellent - High confidence trades |
| >= 60% | >= 1.5 | Good - Reliable performance |
| >= 50% | Any | Acceptable - Use with caution |
| < 50% | Any | Avoid - Poor historical performance |

**Response (Success with no data):**
```json
{
  "success": true,
  "data": {
    "period_days": 30,
    "symbol": "GBPJPY",
    "timeframe": null,
    "signal": null,
    "total_trades": 0,
    "message": "No trades recorded for this period"
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "Invalid timeframe: XYZ (must be M1, M5, M15, M30, H1, H4, D1, W1, MN1)"
}
```

**Example Usage (JavaScript):**
```javascript
// Get report for XAUUSD BUY signals over 30 days
socket.emit('advisor:accuracy_report', {
  symbol: 'XAUUSD',
  signal: 'BUY',
  days: 30
}, (response) => {
  if (response.success) {
    const metrics = response.data;
    console.log(`Win Rate: ${metrics.win_rate_pct}%`);
    console.log(`Profit Factor: ${metrics.profit_factor}`);
    console.log(`Recommendation: ${metrics.recommendation}`);

    // Display best-performing configs
    metrics.best_performing_configs.forEach(config => {
      console.log(`${config.symbol} ${config.timeframe} ${config.signal}: ${config.win_rate_pct}% WR`);
    });
  } else {
    console.error('Error:', response.message);
  }
});

// Get report for all trades (all symbols, timeframes, signals)
socket.emit('advisor:accuracy_report', {
  days: 90
}, (response) => {
  if (response.success) {
    console.log(`Total trades (90d): ${response.data.total_trades}`);
  }
});
```

**Query Combinations:**

```javascript
// By symbol only (all timeframes, signals)
{ symbol: 'XAUUSD', days: 30 }

// By symbol and timeframe (all signals)
{ symbol: 'XAUUSD', timeframe: 'H1', days: 30 }

// By symbol and signal (all timeframes)
{ symbol: 'XAUUSD', signal: 'BUY', days: 30 }

// By all three dimensions
{ symbol: 'XAUUSD', timeframe: 'H1', signal: 'BUY', days: 30 }

// For specific user
{ user_id: 'user-uuid', days: 30 }

// All trades in period
{ days: 90 }

// Specific date range (use days to set window)
{ symbol: 'EURUSD', days: 365 }  // Last 1 year
```

**Error Cases:**

1. **Invalid Timeframe:**
   ```json
   {"success": false, "message": "Invalid timeframe: XYZ"}
   ```

2. **Invalid Signal:**
   ```json
   {"success": false, "message": "Invalid signal: MAYBE"}
   ```

3. **Invalid Days Range:**
   ```json
   {"success": false, "message": "Days must be between 1 and 365"}
   ```

4. **Database Connection Error:**
   ```json
   {"success": false, "message": "Failed to fetch accuracy report: connection timeout"}
   ```

---

## Database Schema

### recommendation_outcomes Table

Stores all trade outcome records.

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Primary key, auto-generated |
| recommendation_id | UUID | Yes | Link to original recommendation |
| user_id | UUID | Yes | User ID for per-user tracking |
| symbol | TEXT | No | Trading symbol |
| timeframe | TEXT | No | Timeframe (M1, M5, H1, etc.) |
| signal | TEXT | No | BUY, SELL, or HOLD |
| confidence | NUMERIC(5,2) | Yes | 0-100 confidence score |
| entry_price | NUMERIC(20,8) | No | Entry price |
| exit_price | NUMERIC(20,8) | Yes | Exit price |
| stop_loss | NUMERIC(20,8) | Yes | Stop loss price |
| take_profit | NUMERIC(20,8) | Yes | Take profit price |
| outcome | TEXT | Yes | win, loss, break_even, or pending |
| pnl | NUMERIC(20,8) | Yes | Profit/loss in units |
| pnl_pct | NUMERIC(6,2) | Yes | P/L as percentage |
| held_duration | INTERVAL | Yes | Time from entry to exit |
| matched_prediction | BOOLEAN | Yes | Did price move as predicted? |
| exit_reason | TEXT | Yes | take_profit, stop_loss, manual, timeout, pending |
| provenance | JSONB | Yes | Data source metadata |
| notes | TEXT | Yes | User notes |
| created_at | TIMESTAMPTZ | No | Record creation time |
| updated_at | TIMESTAMPTZ | No | Last update time |
| entry_at | TIMESTAMPTZ | Yes | Entry timestamp |
| exit_at | TIMESTAMPTZ | Yes | Exit timestamp |

**Constraints:**

- `signal` IN ('BUY', 'SELL', 'HOLD')
- `confidence` BETWEEN 0 AND 100
- `outcome` IN ('win', 'loss', 'break_even', 'pending')
- `exit_reason` IN ('take_profit', 'stop_loss', 'manual', 'timeout', 'pending')

**Indexes:**

- `idx_rec_outcomes_symbol_tf` ON (symbol, timeframe)
- `idx_rec_outcomes_signal` ON (signal, outcome)
- `idx_rec_outcomes_created_at` ON (created_at DESC)
- `idx_rec_outcomes_user_id` ON (user_id) WHERE user_id IS NOT NULL

### recommendation_accuracy Materialized View

Pre-aggregated accuracy metrics by symbol, timeframe, and signal.

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| symbol | TEXT | Trading symbol |
| timeframe | TEXT | Timeframe |
| signal | TEXT | Signal type |
| total_trades | INTEGER | Total outcomes |
| wins | INTEGER | Count of wins |
| losses | INTEGER | Count of losses |
| break_evens | INTEGER | Count of break-evens |
| win_rate_pct | NUMERIC | Win rate percentage |
| avg_pnl_pct | NUMERIC | Average P/L % |
| avg_win_pct | NUMERIC | Avg winning trade % |
| avg_loss_pct | NUMERIC | Avg losing trade % |
| profit_factor | NUMERIC | Wins/losses ratio |
| avg_hold_hours | NUMERIC | Average hold duration |
| last_updated | TIMESTAMPTZ | Last refresh time |

**Refresh:** Automatically refreshed after each outcome record (via trigger)

---

## Configuration

### Environment Variables

```bash
# Phase 5.2: Accuracy Tracking System
ENABLE_ACCURACY_TRACKING=true         # Enable/disable feature

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

### Setup Steps

1. **Install PostgreSQL:**
   ```bash
   # macOS
   brew install postgresql@14
   brew services start postgresql@14

   # Linux
   sudo apt-get install postgresql-14
   sudo systemctl start postgresql
   ```

2. **Create Database:**
   ```bash
   psql -U postgres -c "CREATE DATABASE ev_gamepad;"
   ```

3. **Run Migration:**
   ```bash
   psql -U postgres -d ev_gamepad -f backend/app/database/migrations/005_recommendation_outcomes.sql
   ```

4. **Update .env:**
   ```bash
   ENABLE_ACCURACY_TRACKING=true
   DB_PASSWORD=your_password
   ```

5. **Restart Backend:**
   Server will initialize accuracy tracking on startup

---

## Performance Characteristics

### Query Performance

- **Record Outcome:** ~50-100ms (includes index update + view refresh)
- **Accuracy Report (cache miss):** ~200-500ms
- **Best Configs Query:** ~100-300ms

### Database Indexes

Query performance optimized by indexes:
- Symbol + timeframe combination: O(log n)
- Signal + outcome filtering: O(log n)
- Time-based queries: O(log n) via created_at DESC index

### Materialized View

- View refreshes on every outcome record
- Refresh time: ~50-200ms (depends on total rows)
- Queries hit pre-aggregated view for <50ms response

---

## Best Practices

### Recording Outcomes

1. **Record immediately after position closes** - Minimize data staleness
2. **Use correct exit_reason** - Improves analysis accuracy
3. **Link recommendation_id when available** - Enables recommendation tracking
4. **Include timestamps** - Allows accurate hold duration calculation

### Querying Reports

1. **Start with broad queries** - No filters to get overall performance
2. **Drill down by symbol/timeframe** - Find best-performing setups
3. **Use appropriate date range** - 30 days for recent performance, 90+ for trends
4. **Compare configurations** - Use best_performing_configs to optimize

### Interpreting Metrics

| Metric | Good Range | Concern |
|--------|-----------|---------|
| Win Rate | >60% | <50% indicates random entry |
| Profit Factor | >1.5 | <1.0 means losing money |
| Sharpe Ratio | >1.0 | <0.5 indicates high volatility |
| Avg Hold | 2-48 hours | <1 hour = scalping, >72 hours = position holding |

---

## Troubleshooting

### Database Connection Error

**Symptom:** "connection refused on localhost:5432"

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL
brew services start postgresql@14  # macOS
sudo systemctl start postgresql   # Linux
```

### Migration Not Applied

**Symptom:** Table "recommendation_outcomes" does not exist

**Solution:**
```bash
# Run migration manually
psql -U postgres -d ev_gamepad -f backend/app/database/migrations/005_recommendation_outcomes.sql

# Verify table exists
psql -U postgres -d ev_gamepad -c "\dt recommendation_outcomes"
```

### Slow Queries

**Symptom:** Accuracy report takes >1 second

**Solution:**
1. Check if materialized view is stale (last_updated timestamp)
2. Manually refresh: `psql -c "REFRESH MATERIALIZED VIEW recommendation_accuracy"`
3. Check for missing indexes: `psql -c "\d+ recommendation_outcomes"`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-31 | Initial release - Phase 5.2 |

---

**API Reference Status:** Complete
**Last Updated:** 2025-12-31
**Next Review:** 2026-01-15
