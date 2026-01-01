# Phase 3: Multiplayer Feature Implementation Roadmap

**Research Summary Date:** 2025-12-30
**Target Phase:** 2026-01-24 → 2026-03-15 (Phase 3 in project roadmap)
**Scope:** Game multiplayer integration, leaderboard system, team mechanics, achievement system

---

## Quick Reference: Tech Stack Recommendations

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Real-time Events | Socket.IO v4 + msgpack parser | Industry standard, proven at 100K+ participants |
| Leaderboard DB | PostgreSQL materialized views | Fast rankings, cached computation |
| In-memory Ranking | Redis sorted sets | O(log n) rank lookups, ZADD for updates |
| Achievement Engine | Async job queue (Celery/Bull) | Non-blocking, complex check logic |
| Paper Trading Engine | Asyncio + numpy (Python) | Parallel trade execution, fast slippage calc |
| Team Scoring | FastAPI endpoint + cached computations | Leverage existing backend |
| UI Updates | React + TanStack Query | Optimistic updates, real-time sync |

---

## Implementation Breakdown

### Sprint 1: Leaderboard Infrastructure (Weeks 1-2)

#### 1.1 Database Schema (PostgreSQL)

```sql
-- Games table (created in Phase 1)
CREATE TABLE games (
  id UUID PRIMARY KEY,
  game_type VARCHAR(50), -- 'solo', 'team', 'tournament'
  status VARCHAR(20), -- 'setup', 'active', 'finished'
  created_at TIMESTAMP,
  season_start TIMESTAMP,
  season_end TIMESTAMP,
  prize_pool DECIMAL,
  participant_count INT
);

-- Players in game
CREATE TABLE game_participants (
  id UUID PRIMARY KEY,
  game_id UUID REFERENCES games(id),
  user_id UUID REFERENCES users(id),
  team_id UUID, -- NULL if solo
  starting_balance DECIMAL DEFAULT 100000,
  status VARCHAR(20), -- 'active', 'blown_up', 'finished'
  joined_at TIMESTAMP,
  UNIQUE(game_id, user_id)
);

-- Trade history (created in Phase 1, extended)
CREATE TABLE trades (
  id UUID PRIMARY KEY,
  participant_id UUID REFERENCES game_participants(id),
  symbol VARCHAR(20),
  side VARCHAR(4), -- 'BUY', 'SELL'
  quantity INT,
  entry_price DECIMAL,
  fill_price DECIMAL, -- WITH slippage
  slippage_amount DECIMAL,
  exit_price DECIMAL NULL,
  pnl DECIMAL NULL,
  status VARCHAR(20), -- 'open', 'closed', 'partial'
  created_at TIMESTAMP,
  closed_at TIMESTAMP NULL,
  INDEX idx_participant_time (participant_id, created_at)
);

-- Daily snapshots for Sharpe calculation
CREATE TABLE daily_snapshots (
  id UUID PRIMARY KEY,
  participant_id UUID,
  game_id UUID,
  snapshot_date DATE,
  balance DECIMAL,
  equity DECIMAL,
  unrealized_pnl DECIMAL,
  daily_return DECIMAL, -- (equity - prev_equity) / prev_equity
  max_drawdown DECIMAL,
  INDEX idx_participant_date (participant_id, snapshot_date)
);

-- Materialized view for fast ranking
CREATE MATERIALIZED VIEW leaderboard_rankings AS
SELECT
  game_id,
  participant_id,
  user_id,
  starting_balance,
  equity,
  total_pnl,
  pnl_pct,
  sharpe_ratio,
  win_rate,
  trade_count,
  days_active,
  RANK() OVER (PARTITION BY game_id ORDER BY sharpe_ratio DESC) as rank_sharpe,
  RANK() OVER (PARTITION BY game_id ORDER BY total_pnl DESC) as rank_pnl,
  updated_at
WITH DATA;

-- Index for refreshes
CREATE INDEX idx_leaderboard_game ON leaderboard_rankings(game_id, rank_sharpe);
```

#### 1.2 Leaderboard Service (Python/FastAPI)

```python
# backend/app/services/leaderboard_service.py

from decimal import Decimal
from sqlalchemy import func, desc
from app.database import db
from app.models import GameParticipant, DailySnapshot
from app.cache import redis_client

class LeaderboardService:
    async def get_game_leaderboard(self, game_id: str, metric: str = 'sharpe'):
        """
        Get leaderboard for game. Metrics: sharpe, pnl, consistency, custom
        """
        cache_key = f"leaderboard:{game_id}:{metric}"
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        # Query materialized view (pre-computed rankings)
        rankings = await db.fetch(f"""
            SELECT
              rank_{metric} as rank,
              participant_id,
              user_id,
              total_pnl,
              sharpe_ratio,
              win_rate,
              trade_count
            FROM leaderboard_rankings
            WHERE game_id = $1
            ORDER BY rank_{metric}
            LIMIT 100
        """, game_id)

        result = [dict(r) for r in rankings]

        # Cache for 5 seconds (balance freshness vs. DB load)
        await redis_client.set(cache_key, json.dumps(result), ex=5)
        return result

    async def calculate_sharpe_ratio(self, participant_id: str, lookback_days: int = 30):
        """
        Calculate Sharpe ratio from daily snapshots
        Formula: (mean_return - risk_free_rate) / std(returns)
        """
        snapshots = await db.fetch("""
            SELECT daily_return FROM daily_snapshots
            WHERE participant_id = $1
            AND snapshot_date >= NOW() - INTERVAL '$2 days'
            ORDER BY snapshot_date
        """, participant_id, lookback_days)

        if len(snapshots) < 5:
            return None  # Insufficient data

        returns = [Decimal(s['daily_return']) for s in snapshots]
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = float(variance) ** 0.5

        risk_free_rate = Decimal(0.02) / 252  # 2% annual

        sharpe = (mean_return - risk_free_rate) / std_dev if std_dev > 0 else 0
        return float(sharpe)

    async def recalculate_materialized_view(self, game_id: str):
        """
        Refresh materialized view. Called on trade execution.
        """
        await db.execute("""
            REFRESH MATERIALIZED VIEW CONCURRENTLY leaderboard_rankings
        """)

        # Invalidate cache
        for metric in ['sharpe', 'pnl', 'consistency']:
            await redis_client.delete(f"leaderboard:{game_id}:{metric}")

        # Broadcast to clients
        await emit_to_game(game_id, 'leaderboard:refresh')
```

#### 1.3 Socket.IO Integration

```python
# backend/app/events/leaderboard_events.py

@sio.on('leaderboard:subscribe')
async def on_leaderboard_subscribe(sid, data):
    """
    Client subscribes to leaderboard updates
    data: { game_id: str, metric: 'sharpe'|'pnl' }
    """
    game_id = data['game_id']
    metric = data.get('metric', 'sharpe')

    # Add to room for broadcasting
    sio.enter_room(sid, f"leaderboard:{game_id}:{metric}")

    # Send current ranking
    leaderboard = await leaderboard_service.get_game_leaderboard(game_id, metric)
    await sio.emit('leaderboard:update', {
        'game_id': game_id,
        'metric': metric,
        'rankings': leaderboard,
        'timestamp': datetime.now().isoformat()
    }, to=sid)

@sio.on('trade:executed')
async def on_trade_executed(sid, data):
    """
    Trade completed. Trigger leaderboard refresh.
    """
    trade = parse_trade_data(data)
    participant = await db.get_participant(trade.participant_id)
    game_id = participant.game_id

    # Recalculate rankings asynchronously
    await leaderboard_service.recalculate_materialized_view(game_id)

    # Broadcast updated leaderboard
    leaderboard = await leaderboard_service.get_game_leaderboard(game_id, 'sharpe')
    await sio.emit('leaderboard:update', {
        'game_id': game_id,
        'rankings': leaderboard
    }, to=f"leaderboard:{game_id}:sharpe")
```

### Sprint 2: Paper Trading Engine (Weeks 2-3)

#### 2.1 Order Execution with Slippage

```python
# backend/app/services/paper_trading_engine.py

import numpy as np
from datetime import datetime
from decimal import Decimal

class PaperTradingEngine:
    def __init__(self, realism_level: str = 'realistic'):
        self.realism = realism_level
        self.execution_delays = {
            'simplified': 0,
            'realistic': 10,  # ms
            'advanced': 50    # ms
        }

    async def execute_order(self, order: Order, market_data: MarketData):
        """
        Execute paper trade with optional slippage.
        """
        if self.realism == 'simplified':
            return self._execute_simplified(order, market_data)
        else:
            return self._execute_realistic(order, market_data)

    def _execute_realistic(self, order: Order, market_data: MarketData):
        """
        Realistic execution with spread + volume impact + volatility impact
        """
        bid, ask = market_data.bid_ask_spread

        # Base spread (depends on liquidity tier)
        base_spread = self._get_base_spread(order.symbol)

        # Volume impact: large orders get worse prices
        daily_volume = market_data.daily_volume
        volume_ratio = order.quantity / daily_volume
        volume_impact = volume_ratio * 0.0005  # 0.05% per 1% of daily volume

        # Volatility impact: volatile symbols = wider spreads
        volatility = market_data.realized_volatility
        volatility_impact = volatility * 0.0001

        total_slippage = base_spread + volume_impact + volatility_impact

        if order.side == 'BUY':
            fill_price = ask + (total_slippage / 2)  # Assume mid-slippage
        else:
            fill_price = bid - (total_slippage / 2)

        return {
            'status': 'FILLED',
            'order_id': order.id,
            'fill_price': float(fill_price),
            'quantity': order.quantity,
            'cost': float(fill_price * order.quantity),
            'slippage_amount': float(total_slippage * order.quantity),
            'slippage_pct': float(total_slippage),
            'execution_time': datetime.now().isoformat(),
            'execution_delay_ms': self.execution_delays[self.realism]
        }

    def _get_base_spread(self, symbol: str) -> float:
        """
        Base spread depends on symbol liquidity tier
        """
        spreads = {
            'EURUSD': 0.0001,   # 1 pip
            'SPY': 0.01,         # 1 cent
            'NVDA': 0.02,        # 2 cents (more volatile)
        }
        return spreads.get(symbol, 0.001)  # Default 0.1%

    async def update_position(self, trade: ExecutedTrade):
        """
        Update participant's open position and P&L
        """
        participant = await db.get_participant(trade.participant_id)

        # Calculate new position metrics
        position_value = trade.fill_price * trade.quantity
        cost_basis = await self._get_cost_basis(trade.participant_id, trade.symbol)
        unrealized_pnl = position_value - cost_basis

        # Update participant equity
        participant.equity = participant.cash + sum(position.unrealized_pnl)

        await db.update_participant(participant)
        await emit_to_participant(participant.user_id, 'position:update', {
            'symbol': trade.symbol,
            'quantity': trade.quantity,
            'avg_price': cost_basis / trade.quantity,
            'current_price': trade.fill_price,
            'unrealized_pnl': float(unrealized_pnl),
            'unrealized_pnl_pct': float(unrealized_pnl / cost_basis),
            'total_equity': float(participant.equity)
        })
```

#### 2.2 Daily P&L Snapshot Calculation

```python
# backend/app/services/pnl_snapshot_service.py

class PnLSnapshotService:
    async def take_daily_snapshot(self, game_id: str):
        """
        Run daily (e.g., 5 PM market close) to calculate day's returns.
        """
        participants = await db.get_game_participants(game_id)

        for participant in participants:
            # Get open positions
            open_positions = await db.get_open_positions(participant.id)

            # Mark-to-market equity
            equity = participant.cash + sum(pos.current_value for pos in open_positions)

            # Get previous day's equity
            prev_snapshot = await db.get_latest_snapshot_before(
                participant.id,
                datetime.now().date()
            )
            prev_equity = prev_snapshot.equity if prev_snapshot else participant.starting_balance

            daily_return = (equity - prev_equity) / prev_equity if prev_equity > 0 else 0

            # Save snapshot
            snapshot = DailySnapshot(
                participant_id=participant.id,
                game_id=game_id,
                snapshot_date=datetime.now().date(),
                balance=participant.cash,
                equity=equity,
                unrealized_pnl=equity - participant.starting_balance,
                daily_return=daily_return,
                max_drawdown=await self._calculate_drawdown(participant.id)
            )
            await db.create(snapshot)

        # Recalculate Sharpe ratios + materialize view
        await leaderboard_service.recalculate_materialized_view(game_id)
```

### Sprint 3: Team Mechanics & Scoring (Weeks 3-4)

#### 3.1 Team Data Model

```sql
CREATE TABLE teams (
  id UUID PRIMARY KEY,
  game_id UUID REFERENCES games(id),
  team_name VARCHAR(100),
  captain_id UUID REFERENCES users(id),
  created_at TIMESTAMP,
  status VARCHAR(20) -- 'formation', 'active', 'finished'
);

CREATE TABLE team_members (
  id UUID PRIMARY KEY,
  team_id UUID REFERENCES teams(id),
  user_id UUID REFERENCES users(id),
  role VARCHAR(50), -- 'captain', 'member', 'strategist'
  joined_at TIMESTAMP,
  UNIQUE(team_id, user_id)
);

CREATE TABLE team_scores (
  id UUID PRIMARY KEY,
  team_id UUID REFERENCES teams(id),
  game_id UUID REFERENCES games(id),
  calculated_at TIMESTAMP,
  aggregate_pnl DECIMAL,
  aggregate_sharpe DECIMAL,
  member_count INT,
  active_members INT,
  consistency_bonus DECIMAL,
  collaborative_bonus DECIMAL,
  final_score DECIMAL,
  rank INT,
  INDEX idx_team_game (team_id, game_id)
);
```

#### 3.2 Team Scoring Algorithm

```python
# backend/app/services/team_scoring_service.py

class TeamScoringService:
    async def calculate_team_score(self, team_id: str, period='current'):
        """
        Multi-factor team scoring:
        - Aggregate P&L (40%)
        - Aggregate Sharpe (40%)
        - Consistency bonus (10%)
        - Collaboration bonus (10%)
        """
        members = await db.get_team_members(team_id)
        team = await db.get_team(team_id)

        # Calculate period start/end
        if period == 'current':
            period_start = team.created_at
            period_end = datetime.now()
        else:
            # Other periods: 'week', 'month', etc.
            period_start, period_end = self._get_period_range(period)

        # 1. Calculate aggregate P&L
        aggregate_pnl = 0
        individual_pnls = []
        for member in members:
            participant = await db.get_participant(member.user_id, team.game_id)
            pnl = participant.equity - participant.starting_balance
            aggregate_pnl += pnl
            individual_pnls.append(pnl)

        # 2. Calculate aggregate Sharpe
        combined_returns = await self._get_combined_returns(members, period_start, period_end)
        aggregate_sharpe = self._calculate_sharpe(combined_returns)

        # 3. Consistency bonus (penalize high variance)
        individual_sharpes = [
            await self._calculate_member_sharpe(m, period_start, period_end)
            for m in members
        ]
        sharpe_variance = np.var(individual_sharpes)
        consistency_bonus = max(0, 1.0 - (sharpe_variance * 0.5))

        # 4. Collaboration bonus (% of members trading)
        active_members = sum(1 for m in members if await self._is_member_active(m, period_end))
        collaboration_ratio = active_members / len(members)
        collaboration_bonus = collaboration_ratio * 0.5

        # Final score
        final_score = (
            (aggregate_pnl / 100000) * 0.4 +  # P&L normalized to starting balance
            (aggregate_sharpe * 0.5) * 0.4 +   # Sharpe normalized
            consistency_bonus * 0.1 +
            collaboration_bonus * 0.1
        )

        # Persist
        score = TeamScore(
            team_id=team_id,
            game_id=team.game_id,
            aggregate_pnl=aggregate_pnl,
            aggregate_sharpe=aggregate_sharpe,
            member_count=len(members),
            active_members=active_members,
            consistency_bonus=consistency_bonus,
            collaborative_bonus=collaboration_bonus,
            final_score=final_score,
            calculated_at=datetime.now()
        )
        await db.create(score)

        return score

    async def _get_combined_returns(self, members, start_date, end_date):
        """
        Aggregate daily returns across all team members
        """
        combined = {}
        for member in members:
            snapshots = await db.fetch("""
                SELECT snapshot_date, daily_return FROM daily_snapshots
                WHERE participant_id = $1
                AND snapshot_date BETWEEN $2 AND $3
            """, member.user_id, start_date, end_date)

            for snap in snapshots:
                date = snap['snapshot_date']
                combined[date] = combined.get(date, 0) + snap['daily_return']

        return list(combined.values())
```

### Sprint 4: Achievement System (Weeks 4-5)

#### 4.1 Achievement Detection Engine

```python
# backend/app/services/achievement_engine.py

class AchievementEngine:
    async def on_trade_executed(self, trade: ExecutedTrade):
        """
        Triggered after trade execution. Checks for pattern-based achievements.
        """
        achievements = []

        # Check pattern type
        pattern_type = await self._detect_pattern(trade)
        if pattern_type:
            if pattern_type == 'support_bounce':
                achievements.append({
                    'badge': 'support_bounce_master',
                    'type': 'pattern',
                    'xp': 50,
                    'title': 'Support Bounce Expert',
                    'description': 'Entered at support level'
                })

            elif pattern_type == 'overbought_reversal':
                achievements.append({
                    'badge': 'overbought_reversal',
                    'type': 'pattern',
                    'xp': 50,
                    'title': 'Overbought Trader',
                    'description': 'Caught overbought reversal'
                })

        # Emit unlocked achievements
        for ach in achievements:
            await self._unlock_achievement(trade.participant_id, ach)

    async def check_daily_achievements(self, participant_id: str):
        """
        Run nightly (after market close). Checks consistency, risk, etc.
        """
        achievements = []

        # 1. Check 5-day profitable streak
        if await self._check_consecutive_profitable_days(participant_id, 5):
            achievements.append({
                'badge': 'five_day_streak',
                'type': 'consistency',
                'xp': 100,
                'title': '5-Day Streak',
                'description': '5 consecutive profitable days'
            })

        # 2. Check weekly consistency (60%+ win rate)
        if await self._check_weekly_win_rate(participant_id, 0.6):
            achievements.append({
                'badge': 'consistent_trader',
                'type': 'consistency',
                'xp': 75,
                'title': 'Consistent Trader',
                'description': '>60% win rate this week'
            })

        # 3. Check risk discipline (no trades > 2% daily loss)
        if await self._check_risk_discipline(participant_id):
            achievements.append({
                'badge': 'risk_manager',
                'type': 'risk',
                'xp': 50,
                'title': 'Risk Manager',
                'description': 'No daily loss > 2%'
            })

        # 4. Check progress toward monthly badges
        monthly_progress = await self._get_monthly_achievement_progress(participant_id)
        if monthly_progress['consistency'] >= 0.5:  # 50% progress
            achievements.append({
                'badge': 'monthly_consistent_progress',
                'type': 'progress',
                'xp': 25,
                'title': 'Consistency Progress',
                'progress': monthly_progress['consistency']
            })

        for ach in achievements:
            await self._unlock_achievement(participant_id, ach)

    async def _unlock_achievement(self, participant_id: str, achievement: dict):
        """
        Award achievement and emit notification
        """
        user = await db.get_user_by_participant(participant_id)

        # Save to DB
        ach_record = Achievement(
            user_id=user.id,
            badge_name=achievement['badge'],
            xp_awarded=achievement['xp'],
            unlocked_at=datetime.now()
        )
        await db.create(ach_record)

        # Update user XP
        user.total_xp += achievement['xp']
        await db.update(user)

        # Emit to client
        await emit_to_participant(participant_id, 'achievement:unlocked', {
            'badge': achievement['badge'],
            'title': achievement['title'],
            'description': achievement['description'],
            'xp': achievement['xp'],
            'timestamp': datetime.now().isoformat()
        })

        # Broadcast to game (for public achievements)
        if achievement['type'] in ['consistency', 'milestone']:
            game_id = await db.get_game_id_for_participant(participant_id)
            await emit_to_game(game_id, 'achievement:public', {
                'user': user.username,
                'badge': achievement['badge'],
                'type': achievement['type']
            })

    async def _detect_pattern(self, trade: ExecutedTrade) -> str:
        """
        Detect if trade matches a pattern (integration with Phase 2.2)
        """
        # Query phase 2.2 pattern detector
        pattern = await self.pattern_detector.detect_pattern(
            symbol=trade.symbol,
            entry_price=trade.fill_price,
            entry_time=trade.created_at,
            lookback_bars=50
        )
        return pattern.name if pattern else None
```

#### 4.2 Frontend Achievement Display

```jsx
// frontend/src/components/AchievementUnlock.tsx

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSocket } from '@/hooks/useSocket';

export function AchievementUnlock() {
  const [achievements, setAchievements] = useState([]);
  const socket = useSocket();

  useEffect(() => {
    socket.on('achievement:unlocked', (data) => {
      const newAch = {
        id: Date.now(),
        ...data
      };
      setAchievements(prev => [...prev, newAch]);

      // Auto-remove after 5s
      setTimeout(() => {
        setAchievements(prev => prev.filter(a => a.id !== newAch.id));
      }, 5000);
    });

    return () => socket.off('achievement:unlocked');
  }, [socket]);

  return (
    <AnimatePresence>
      {achievements.map(ach => (
        <motion.div
          key={ach.id}
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          className="fixed top-4 right-4 bg-gradient-to-r from-yellow-400 to-orange-400
                     rounded-lg p-4 shadow-xl text-white font-bold"
        >
          <div className="text-lg">🎖️ {ach.title}</div>
          <div className="text-sm opacity-90">{ach.description}</div>
          <div className="text-sm mt-2">+{ach.xp} XP</div>
        </motion.div>
      ))}
    </AnimatePresence>
  );
}
```

### Sprint 5: Real-time Synchronization & Testing (Weeks 5-6)

#### 5.1 Real-time Update Patterns

```python
# backend/app/events/game_events.py

@sio.event
async def on_price_update(sid, data):
    """
    Price update from market feed. Broadcast to all game participants.
    Batch updates: send every 100ms instead of per-tick.
    """
    symbol = data['symbol']
    price = data['price']
    timestamp = data['timestamp']

    # Cache current price
    await redis_client.set(f"price:{symbol}", price, ex=60)

    # Add to batch queue
    await price_batch_queue.put({
        'symbol': symbol,
        'price': price,
        'timestamp': timestamp
    })

async def broadcast_price_updates():
    """
    Batch broadcaster: aggregates price updates and broadcasts every 100ms
    """
    while True:
        batch = []
        timeout = time.time() + 0.1  # 100ms window

        # Collect updates for 100ms
        while time.time() < timeout:
            try:
                update = await asyncio.wait_for(
                    price_batch_queue.get(),
                    timeout=0.01
                )
                batch.append(update)
            except asyncio.TimeoutError:
                break

        if batch:
            # Broadcast to all games
            await sio.emit('prices:batch_update', {
                'updates': batch,
                'timestamp': datetime.now().isoformat()
            })

# Register broadcaster on startup
@app.on_event("startup")
async def startup():
    asyncio.create_task(broadcast_price_updates())
```

#### 5.2 Load Testing Configuration

```python
# tests/load_test_leaderboard.py

import asyncio
from locust import HttpUser, task, between

class LeaderboardLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_leaderboard(self):
        game_id = 'test-game-001'
        self.client.get(f'/api/games/{game_id}/leaderboard?metric=sharpe')

    @task(3)
    def subscribe_leaderboard_socket(self):
        # WebSocket subscription
        pass

class PriceUpdateLoadTest:
    async def simulate_price_updates(self, num_symbols=100, update_rate=50):
        """
        Simulate 50 updates/sec per symbol (realistic market)
        """
        for i in range(num_symbols):
            asyncio.create_task(
                self._simulate_symbol_updates(f'SYM{i}', update_rate)
            )

    async def _simulate_symbol_updates(self, symbol, rate):
        interval = 1 / rate
        while True:
            price = random.uniform(100, 200)
            await sio.emit('price:update', {
                'symbol': symbol,
                'price': price,
                'timestamp': datetime.now().isoformat()
            })
            await asyncio.sleep(interval)

# Run with: locust -f tests/load_test_leaderboard.py --host=http://localhost:8000
```

---

## Database Optimization Recommendations

1. **Indexing Strategy:**
   - `trades(participant_id, created_at)` - Fast trade lookups
   - `daily_snapshots(participant_id, snapshot_date)` - Sharpe calculation
   - `leaderboard_rankings(game_id, rank_sharpe)` - Leaderboard queries

2. **Materialized View Refresh:**
   - Refresh after every 50 trades in a game
   - OR refresh on a 5-second interval
   - Use `REFRESH MATERIALIZED VIEW CONCURRENTLY` to avoid locks

3. **Connection Pooling:**
   - Min connections: 5
   - Max connections: 20
   - Timeout: 30 seconds

---

## Redis Cache Strategy

| Key Pattern | TTL | Use Case |
|-------------|-----|----------|
| `leaderboard:{game_id}:{metric}` | 5s | Leaderboard queries |
| `price:{symbol}` | 60s | Current prices |
| `participant:{id}:equity` | 10s | P&L display |
| `achievement:unlocked:{user_id}` | 3600s | Prevent duplicate awards |

---

## Integration Checklist

- [ ] PostgreSQL schema deployed (Sprint 1)
- [ ] Leaderboard service tested with 1000+ participants (Sprint 1)
- [ ] Paper trading engine handles slippage correctly (Sprint 2)
- [ ] Daily P&L snapshots running on schedule (Sprint 2)
- [ ] Team scoring algorithm tested with 50+ teams (Sprint 3)
- [ ] Achievement detection working for 10+ badge types (Sprint 4)
- [ ] Real-time updates (< 500ms latency) confirmed (Sprint 5)
- [ ] Load test: 10K concurrent WebSocket connections (Sprint 5)
- [ ] Integration with Phase 2.1 technical advisor (ongoing)
- [ ] Integration with Phase 2.2 pattern detection (pending Phase 2.2)

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Leaderboard stale due to slow DB refresh | High | Medium | Materialized view + Redis cache |
| WebSocket connection churn at 1000+ users | Medium | High | Exponential backoff, room-based scoping |
| Slippage model unrealistic | Medium | Low | Validate against QuantConnect/Fintokei |
| Achievement inflation (everyone gets badges) | High | Low | Season-based resets, tiered difficulty |
| Team scoring computation bottleneck | Low | Medium | Pre-compute daily, cache for 1 hour |

---

## Next Steps Post-Phase 3

1. **Phase 3.5 - Dashboard UI** (2-3 weeks)
   - Real-time leaderboard widget
   - Team scoreboard
   - Achievement progress tracking
   - P&L chart with daily snapshots

2. **Phase 3.6 - Mobile Optimization**
   - Responsive leaderboard
   - Native push notifications for achievements
   - Optimized WebSocket for mobile connectivity

3. **Integration with Phase 2.2-2.4**
   - Surface advisor recommendations in team chat
   - Pattern detection achievements
   - AI-powered team suggestions

---

**End of Roadmap**
