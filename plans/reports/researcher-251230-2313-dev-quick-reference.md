# Developer Quick Reference: Multiplayer Trading Features

**Date:** 2025-12-30
**Purpose:** Fast lookup during Phase 3 implementation

---

## Socket.IO Room/Namespace Hierarchy

```
/games (trading events)
  └─ room: game:{gameId}              # All players in game
  └─ room: team:{teamId}              # Team-specific events

/leaderboard (ranking updates)
  └─ room: lb:{gameId}:sharpe         # Sharpe leaderboard
  └─ room: lb:{gameId}:pnl            # P&L leaderboard
  └─ room: lb:{gameId}:consistency    # Win-rate leaderboard

/user (personal events)
  └─ room: user:{userId}              # Achievement unlocks, personal alerts
```

**Join Pattern:**
```javascript
socket.on('connect', () => {
  socket.emit('join_game', { game_id });
  socket.emit('subscribe_leaderboard', { game_id, metric: 'sharpe' });
});
```

---

## Key Metrics & Calculations

### Sharpe Ratio (Primary Ranking)
```
sharpe = (mean_daily_return - risk_free_rate) / std(daily_returns)
risk_free_rate = 2% annual / 252 trading days
lookback = 30 days minimum
```

### Team Score (Weighted)
```
team_score = (
  aggregate_pnl * 0.4 +
  aggregate_sharpe * 0.4 +
  consistency_bonus * 0.1 +
  collaboration_bonus * 0.1
)
```

### P&L Components
```
unrealized_pnl = (current_price - entry_price) * quantity
realized_pnl = sum(closed_trades_pnl)
total_pnl = unrealized_pnl + realized_pnl
pnl_pct = total_pnl / starting_balance
```

### Position Equity
```
cash = starting_balance - sum(open_positions_cost)
equity = cash + sum(open_positions_value)
```

---

## Slippage Calculation Formula

```python
slippage = base_spread + volume_impact + volatility_impact

base_spread = symbol_spread  # 0.1 pips for EURUSD, $0.01 for SPY
volume_impact = (order_qty / daily_volume) * 0.0005
volatility_impact = realized_volatility * 0.0001

fill_price = (bid if SELL else ask) + slippage_adjustment
```

**Examples:**
- EURUSD 100K lot, 50M daily vol, 10% vol: slippage ≈ 0.15 pips
- SPY 1000 shares, 100M daily vol, 20% vol: slippage ≈ $0.015

---

## API Endpoints (Phase 3)

### Leaderboard Endpoints

**GET /api/games/{gameId}/leaderboard**
```
Query params:
  metric=sharpe|pnl|consistency|custom
  limit=100
  offset=0

Response:
[
  {
    rank: 1,
    user_id: "uuid",
    username: "trader_john",
    pnl: 15000,
    pnl_pct: 15.0,
    sharpe: 2.1,
    win_rate: 0.65,
    trade_count: 42,
    max_drawdown: -5.2
  }
]
```

### Team Endpoints

**GET /api/teams/{teamId}/score**
```
Response:
{
  team_id: "uuid",
  aggregate_pnl: 25000,
  aggregate_sharpe: 1.8,
  member_count: 3,
  active_members: 3,
  consistency_bonus: 0.8,
  collaborative_bonus: 0.9,
  final_score: 42.5,
  rank: 5,
  calculated_at: "2025-12-30T15:30:00Z"
}
```

### Achievement Endpoints

**GET /api/users/{userId}/achievements**
```
Response:
[
  {
    badge: "five_day_streak",
    title: "5-Day Streak",
    unlocked_at: "2025-12-30T14:22:00Z",
    xp: 100,
    tier: "silver"
  }
]
```

**POST /api/achievements/{badge}/unlock** (Admin/System)
```
Body:
{
  user_id: "uuid",
  xp_awarded: 50,
  metadata: { reason: "pattern_match", pattern_type: "support_bounce" }
}
```

---

## WebSocket Events Reference

### Emit From Client

**Join Game:**
```javascript
socket.emit('join_game', {
  game_id: 'uuid',
  player_id: 'uuid'
});
```

**Subscribe to Leaderboard:**
```javascript
socket.emit('subscribe_leaderboard', {
  game_id: 'uuid',
  metric: 'sharpe',
  refresh_rate_ms: 5000
});
```

**Execute Trade:**
```javascript
socket.emit('trade:execute', {
  symbol: 'EURUSD',
  side: 'BUY',
  quantity: 10000,
  order_type: 'MARKET',
  stop_loss: 1.0850,
  take_profit: 1.1000
});
```

### Listen From Server

**Leaderboard Update:**
```javascript
socket.on('leaderboard:update', (data) => {
  console.log(data.rankings); // Array of rankings
  console.log(data.timestamp); // When calculated
  console.log(data.your_rank); // User's new rank
});
```

**Achievement Unlocked:**
```javascript
socket.on('achievement:unlocked', (data) => {
  // {
  //   badge: 'five_day_streak',
  //   title: '5-Day Streak',
  //   xp: 100,
  //   timestamp: '2025-12-30T14:22:00Z'
  // }
});
```

**Trade Executed:**
```javascript
socket.on('trade:executed', (data) => {
  // {
  //   order_id: 'uuid',
  //   status: 'FILLED',
  //   fill_price: 1.0875,
  //   slippage_pct: 0.15,
  //   total_equity: 115000,
  //   pnl: 5000
  // }
});
```

**Price Batch Update:**
```javascript
socket.on('prices:batch_update', (data) => {
  // {
  //   updates: [
  //     { symbol: 'EURUSD', price: 1.0875 },
  //     { symbol: 'SPY', price: 575.20 }
  //   ],
  //   timestamp: '2025-12-30T15:30:00.000Z'
  // }
});
```

---

## Database Query Patterns

### Get User's Current Equity
```sql
SELECT equity FROM daily_snapshots
WHERE participant_id = $1
ORDER BY snapshot_date DESC
LIMIT 1;
```

### Get User's Sharpe Ratio (30-day)
```sql
SELECT
  AVG(daily_return) as mean_return,
  STDDEV(daily_return) as std_dev
FROM daily_snapshots
WHERE participant_id = $1
  AND snapshot_date >= CURRENT_DATE - INTERVAL '30 days'
```

### Get Team Leaderboard
```sql
SELECT
  ts.team_id,
  t.team_name,
  ts.final_score,
  ROW_NUMBER() OVER (ORDER BY ts.final_score DESC) as rank
FROM team_scores ts
JOIN teams t ON ts.team_id = t.id
WHERE ts.game_id = $1
  AND ts.calculated_at = (
    SELECT MAX(calculated_at)
    FROM team_scores
    WHERE game_id = $1
  )
ORDER BY ts.final_score DESC;
```

### Get Open Positions for User
```sql
SELECT
  symbol,
  SUM(quantity) as total_qty,
  AVG(fill_price) as avg_entry_price,
  MAX(fill_price) as highest_price
FROM trades
WHERE participant_id = $1
  AND status = 'open'
GROUP BY symbol;
```

---

## Performance Targets

| Metric | Target | Current | Notes |
|--------|--------|---------|-------|
| Leaderboard API response | < 200ms | TBD | Cached via Redis |
| Leaderboard refresh | 5s | TBD | Material view |
| WebSocket price update latency | < 100ms | TBD | Batch 50/s |
| Achievement unlock notification | < 500ms | TBD | Real-time |
| Trade execution simulation | < 50ms | TBD | Depends on slippage complexity |
| 1000 concurrent WebSocket connections | 50MB RAM | TBD | Tuned via bufferutil |

---

## Common Debugging Patterns

### Check if User is in Game
```python
participant = await db.fetch("""
  SELECT * FROM game_participants
  WHERE user_id = $1 AND game_id = $2
""", user_id, game_id)
```

### Check Leaderboard Cache Hit
```python
cached = await redis_client.get(f"leaderboard:{game_id}:sharpe")
if cached:
    print("Cache HIT")
else:
    print("Cache MISS - recalculating...")
```

### Verify Slippage Calculation
```python
entry = 1.0875
qty = 10000
daily_vol = 50_000_000
volatility = 0.12

slippage = 0.0001 + (qty/daily_vol)*0.0005 + volatility*0.0001
fill_price = entry + slippage
print(f"Slippage: {slippage*10000:.1f} pips")  # 0.2 pips
```

### Monitor WebSocket Rooms
```python
@sio.event
async def on_connect(sid, environ):
    # Check room memberships
    rooms = sio.rooms(sid)
    print(f"User {sid} joined rooms: {rooms}")
```

---

## Common Gotchas

1. **Sharpe Calculation Edge Cases:**
   - Need ≥ 5 days of data (not just 1 trade)
   - Risk-free rate already annualized (adjust for lookback period)
   - If std_dev = 0, return 0 (not division error)

2. **Leaderboard Stale During Volatile Markets:**
   - Materialized view refresh may lag
   - Solution: Use Redis cache + incremental updates

3. **Team Score Calculation:**
   - Must account for members who've left
   - Aggregate returns = sum, not average
   - Sharpe of sum ≠ average of Sharpes

4. **Order Slippage:**
   - Market orders ALWAYS experience slippage
   - Limit orders: 0 slippage IF filled (or not filled)
   - Partial fills: update position gradually

5. **Achievement Duplicate Prevention:**
   - Check achievement:unlocked:{badge}:{user} in Redis
   - Set TTL = season end date
   - Prevents same badge twice

---

## Testing Helpers

### Create Test Game with 10 Players
```python
async def create_test_game():
    game = await db.create_game(
        game_type='solo',
        prize_pool=1000,
        season_start=datetime.now()
    )
    for i in range(10):
        user = await db.create_test_user(f'trader_{i}')
        await db.create_participant(
            game_id=game.id,
            user_id=user.id,
            starting_balance=100000
        )
    return game.id
```

### Simulate Trade Execution
```python
async def simulate_trade(participant_id, symbol, qty, side):
    market_data = await fetch_market_data(symbol)
    filled = await paper_trading_engine.execute_order(
        Order(symbol=symbol, qty=qty, side=side),
        market_data
    )
    await db.create_trade(participant_id, filled)
    await emit_to_game_socket(participant_id, 'trade:executed', filled)
```

### Check Leaderboard Ranking
```python
async def get_user_rank(game_id, user_id):
    rankings = await leaderboard_service.get_game_leaderboard(game_id, 'sharpe')
    for rank_item in rankings:
        if rank_item['user_id'] == user_id:
            return rank_item['rank']
    return None
```

---

## Configuration

**Environment Variables (backend/.env):**
```
REALISM_LEVEL=realistic|simplified  # Paper trading realism
LEADERBOARD_REFRESH_INTERVAL=5      # Seconds
ACHIEVEMENT_CHECK_INTERVAL=3600     # Seconds (nightly)
REDIS_TTL=300                        # Seconds
SOCKETIO_PING_INTERVAL=30000         # Milliseconds
SOCKETIO_PING_TIMEOUT=10000          # Milliseconds
```

---

**End of Quick Reference**
