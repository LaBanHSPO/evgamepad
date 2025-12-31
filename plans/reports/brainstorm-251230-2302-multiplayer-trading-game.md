# Brainstorming Session: Multi-Player Trading Game with Real-Time Dashboard

**Date:** 2025-12-30 (Updated: 2025-12-31)
**Session Type:** Solution Architecture & Product Design
**Status:** Updated - MT5 Demo Account Architecture
**Branch:** `feat/multi-player-feature-with-dashboard`

---

## Problem Statement

Transform EV GamePad from single-player AI trading advisor into **cooperative multi-player trading game** where:
- Friends compete in teams via chat commands (`/csv PanServer`, `/jsv PanServer`)
- Real-time dashboard shows rankings, team scores, P&L, orders
- Live market hours with real MT5 demo account execution
- Achievement system & badges for engagement
- Leaderboard updates in real-time (`/top` command)

---

## User Requirements (Validated)

### Core Gameplay
- **Mode:** Cooperative team-based competition (not PvP)
- **Team Size:** 4-6 players per team (medium teams)
- **Trading:** Real MT5 demo accounts (authentic broker execution, spreads, requotes)
- **Scale:** 5-10 concurrent players (friends/testing phase)
- **Time:** Real-time during live market hours
- **Engagement:** Real-time leaderboard + achievement/badge system

### Command Interface
- `/csv <ServerName>` - **Create** new game server
- `/jsv <ServerName>` - **Join** existing game server
- `/top` - View leaderboard (my rank + team scores)

### Winning Criteria
- **Primary:** Total team P&L (aggregate profit)
- Team with highest combined balance wins

### Execution Model
- **Real MT5 Execution:** Authentic broker spreads, requotes, rejections, order fills
- **Account Management:** Pre-provisioned demo account pool (5-10 accounts)
- **Manual Operations:** Admin creates/renews accounts via broker web portal
- **Fault Tolerance:** Pause sessions during MT5 downtime (no fallback)

---

## Research Foundation

**Comprehensive Research Completed:** 6 professional documents (3,496 lines / 120+ pages)

Research covers:
1. Multiplayer trading platforms (TradingView, BullRush, Stock Market Tycoon analysis)
2. Real-time dashboard architecture (WebSocket patterns, Socket.IO performance)
3. Team-based mechanics (matchmaking, scoring algorithms)
4. Achievement systems (dopamine loops, 83% engagement improvement)
5. ~~Paper trading infrastructure~~ → MT5 demo account integration (real execution)

**Research Location:** `/plans/reports/INDEX-MULTIPLAYER-RESEARCH.md` (START HERE)

---

## Recommended Solution Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                   EV GamePad Multi-Player System                     │
│                                                                       │
│  ┌──────────────┐         ┌────────────────┐      ┌──────────────┐  │
│  │   Chat UI    │◄────────┤  Socket.IO     │─────►│ Game Rooms   │  │
│  │  (/csv /jsv) │  events │  Server        │      │ (Redis pub)  │  │
│  └──────────────┘         └────────┬───────┘      └──────────────┘  │
│                                    │                                 │
│  ┌──────────────┐                  │              ┌──────────────┐  │
│  │  Dashboard   │◄─────────────────┴──────────────┤ Leaderboard  │  │
│  │  (/top cmd)  │  real-time updates              │   Service    │  │
│  └──────────────┘                                 └──────┬───────┘  │
│                                                           │          │
│  ┌──────────────────────────────────────────────────────┴───────┐  │
│  │          MT5 Integration Service (Real Execution)             │  │
│  │  - Account pool manager    - Order routing to MT5             │  │
│  │  - Position synchronization- Real broker execution            │  │
│  │  - Balance tracking        - Health monitoring                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                    │                                 │
│  ┌────────────────────────────────┴──────────────────────────────┐ │
│  │              PostgreSQL Database                               │ │
│  │  - Game sessions    - Teams        - Players                  │ │
│  │  - MT5 accounts     - Orders       - Achievements             │ │
│  │  - Account pool     - Positions    - Leaderboard              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Redis Cache Layer                                 │ │
│  │  - Real-time leaderboard (sorted sets)                         │ │
│  │  - Session state        - Team scores                          │ │
│  │  - Achievement progress - MT5 account allocation              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────┐              ┌──────────────────────┐
│  MT5 Terminal   │              │  Achievement Engine  │
│  (Market Data)  │              │  (Async Background)  │
└─────────────────┘              └──────────────────────┘
```

---

## Core Components Breakdown

### 1. Game Session Management

**Responsibilities:**
- Create game servers (`/csv <name>`)
- Join game servers (`/jsv <name>`)
- Team formation (4-6 players per team)
- Session lifecycle (start, active, completed)

**Database Schema:**
```sql
CREATE TABLE game_sessions (
    session_id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    creator_id UUID NOT NULL,
    status VARCHAR(20) DEFAULT 'waiting',  -- waiting, active, completed
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    max_team_size INT DEFAULT 6,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE teams (
    team_id UUID PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(session_id),
    team_name VARCHAR(50),
    total_pnl DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE team_members (
    member_id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(team_id),
    user_id UUID NOT NULL,
    username VARCHAR(50),
    joined_at TIMESTAMP DEFAULT NOW()
);
```

**Socket.IO Events:**
```python
# Client → Server
@sio.on("game:create")
async def create_game_session(sid, data):
    # data = {"name": "PanServer", "max_team_size": 6}
    session = await GameService.create_session(data["name"], sid)
    await sio.emit("game:created", session, room=sid)

@sio.on("game:join")
async def join_game_session(sid, data):
    # data = {"name": "PanServer", "username": "player1"}
    team = await GameService.join_session(data["name"], sid, data["username"])
    await sio.emit("game:joined", team, room=sid)
    # Broadcast to all session participants
    await sio.emit("game:player_joined", {...}, room=f"session:{session_id}")
```

---

### 2. MT5 Integration Service (Real Execution)

**Responsibilities:**
- MT5 demo account pool management (5-10 pre-provisioned accounts)
- Account allocation on player join (assign available account from pool)
- Order routing to MT5 via MetaTrader5 Python library
- Position synchronization (poll MT5 positions → update database)
- Balance tracking (real-time equity, margin, P&L from MT5)
- Health monitoring (detect MT5 disconnections, pause sessions)

**Architecture:**
```python
import MetaTrader5 as mt5
from typing import Dict, Optional, List
import asyncio

class MT5IntegrationService:
    """
    Real MT5 demo account integration.
    Manages account pool, routes orders to MT5, syncs positions.
    """

    def __init__(self, redis_client, db_pool):
        self.redis = redis_client
        self.db = db_pool
        self.mt5_initialized = False

    async def initialize(self):
        """Initialize MT5 connection."""
        if not mt5.initialize():
            raise Exception(f"MT5 initialization failed: {mt5.last_error()}")
        self.mt5_initialized = True
        logger.info("MT5 connection established")

    async def allocate_account(self, user_id: str, session_id: str) -> Dict:
        """
        Allocate available MT5 demo account from pool.

        Returns:
        {
            "account_id": "uuid",
            "mt5_login": 12345678,
            "mt5_server": "Broker-Demo",
            "status": "allocated"
        }
        """
        # Step 1: Find available account from pool
        account = await self.db.fetchrow("""
            SELECT account_id, mt5_login, mt5_password, mt5_server
            FROM mt5_account_pool
            WHERE status = 'available'
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)

        if not account:
            raise Exception("No available MT5 accounts in pool")

        # Step 2: Mark as allocated in database
        await self.db.execute("""
            UPDATE mt5_account_pool
            SET status = 'allocated',
                allocated_to_user = $1,
                allocated_to_session = $2,
                allocated_at = NOW()
            WHERE account_id = $3
        """, user_id, session_id, account["account_id"])

        # Step 3: Login to MT5 account
        authorized = mt5.login(
            login=account["mt5_login"],
            password=account["mt5_password"],
            server=account["mt5_server"]
        )

        if not authorized:
            raise Exception(f"MT5 login failed: {mt5.last_error()}")

        # Step 4: Cache allocation in Redis (fast lookup)
        await self.redis.hset(
            f"user:{user_id}:mt5",
            mapping={
                "account_id": str(account["account_id"]),
                "mt5_login": account["mt5_login"],
                "mt5_server": account["mt5_server"]
            }
        )

        logger.info(f"Allocated MT5 account {account['mt5_login']} to user {user_id}")
        return {
            "account_id": str(account["account_id"]),
            "mt5_login": account["mt5_login"],
            "mt5_server": account["mt5_server"],
            "status": "allocated"
        }

    async def execute_order(
        self,
        user_id: str,
        symbol: str,
        order_type: str,  # market, limit, stop
        side: str,        # buy, sell
        volume: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Route order to MT5 for real execution.

        Returns:
        {
            "order_id": 123456789,  # MT5 order ticket
            "status": "filled" | "partial" | "rejected",
            "filled_volume": 0.5,
            "avg_fill_price": 2645.32,
            "comment": "MT5 execution",
            "retcode": 10009  # TRADE_RETCODE_DONE
        }
        """

        # Step 1: Get user's MT5 account
        account_info = await self.redis.hgetall(f"user:{user_id}:mt5")
        if not account_info:
            raise Exception("No MT5 account allocated to user")

        # Step 2: Login to user's MT5 account
        mt5.login(
            login=int(account_info[b"mt5_login"]),
            password=await self._get_account_password(account_info[b"account_id"]),
            server=account_info[b"mt5_server"].decode()
        )

        # Step 3: Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if side == "buy" else mt5.ORDER_TYPE_SELL,
            "price": price or mt5.symbol_info_tick(symbol).ask,
            "deviation": 10,  # Max price deviation in points
            "magic": 234000,  # Magic number for identification
            "comment": f"EV GamePad - {user_id[:8]}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or Cancel
        }

        # Step 4: Send order to MT5
        result = mt5.order_send(request)

        # Step 5: Store order in database
        await self.db.execute("""
            INSERT INTO mt5_orders (
                user_id, session_id, mt5_order_id, symbol, side, volume,
                requested_price, executed_price, status, retcode, comment
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, user_id, await self._get_user_session(user_id), result.order,
             symbol, side, volume, price, result.price,
             "filled" if result.retcode == 10009 else "rejected",
             result.retcode, result.comment)

        # Step 6: Update leaderboard with P&L change
        await self._sync_position_pnl(user_id)

        return {
            "order_id": result.order,
            "status": "filled" if result.retcode == 10009 else "rejected",
            "filled_volume": result.volume,
            "avg_fill_price": result.price,
            "comment": result.comment,
            "retcode": result.retcode
        }

    async def sync_positions(self, user_id: str) -> List[Dict]:
        """
        Sync positions from MT5 to database.
        Called periodically (every 5 seconds) to update P&L.
        """
        # Get user's MT5 account
        account_info = await self.redis.hgetall(f"user:{user_id}:mt5")

        # Login to MT5
        mt5.login(
            login=int(account_info[b"mt5_login"]),
            password=await self._get_account_password(account_info[b"account_id"]),
            server=account_info[b"mt5_server"].decode()
        )

        # Fetch open positions from MT5
        positions = mt5.positions_get()

        # Update database with current positions
        for pos in positions:
            await self.db.execute("""
                INSERT INTO positions (user_id, mt5_position_id, symbol, side, volume,
                                       open_price, current_price, pnl)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (mt5_position_id) DO UPDATE
                SET current_price = $7, pnl = $8
            """, user_id, pos.ticket, pos.symbol,
                 "buy" if pos.type == 0 else "sell", pos.volume,
                 pos.price_open, pos.price_current, pos.profit)

        # Update team leaderboard
        await self._update_team_pnl(user_id)

        return [{"symbol": p.symbol, "pnl": p.profit} for p in positions]

    async def release_account(self, user_id: str):
        """
        Release MT5 account back to pool when player leaves session.
        """
        account_info = await self.redis.hgetall(f"user:{user_id}:mt5")

        if account_info:
            # Close all positions
            await self._close_all_positions(account_info[b"mt5_login"])

            # Mark account as available
            await self.db.execute("""
                UPDATE mt5_account_pool
                SET status = 'available',
                    allocated_to_user = NULL,
                    allocated_to_session = NULL,
                    released_at = NOW()
                WHERE account_id = $1
            """, account_info[b"account_id"].decode())

            # Clear Redis cache
            await self.redis.delete(f"user:{user_id}:mt5")

            logger.info(f"Released MT5 account {account_info[b'mt5_login']} from user {user_id}")

    async def health_check(self) -> Dict:
        """
        Monitor MT5 connection health.
        If MT5 unavailable, pause all active sessions.
        """
        if not mt5.terminal_info():
            logger.error("MT5 terminal disconnected!")
            await self._pause_all_sessions()
            return {"status": "down", "error": "MT5 terminal disconnected"}

        account_info = mt5.account_info()
        return {
            "status": "up",
            "balance": account_info.balance,
            "equity": account_info.equity,
            "margin_free": account_info.margin_free
        }
```

**Database Schema:**
```sql
-- MT5 Account Pool (Pre-provisioned demo accounts)
CREATE TABLE mt5_account_pool (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mt5_login BIGINT UNIQUE NOT NULL,           -- MT5 account login number
    mt5_password VARCHAR(100) NOT NULL,         -- Encrypted password
    mt5_server VARCHAR(100) NOT NULL,           -- Broker server name
    status VARCHAR(20) DEFAULT 'available',     -- available, allocated, expired
    allocated_to_user UUID,
    allocated_to_session UUID,
    allocated_at TIMESTAMP,
    released_at TIMESTAMP,
    expires_at TIMESTAMP,                        -- Demo account expiry date
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN ('available', 'allocated', 'expired'))
);

CREATE INDEX idx_mt5_pool_status ON mt5_account_pool(status) WHERE status = 'available';

-- MT5 Orders (Real orders executed on MT5)
CREATE TABLE mt5_orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID REFERENCES game_sessions(session_id),
    mt5_order_id BIGINT NOT NULL,               -- MT5 order ticket number
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(10),                     -- market, limit, stop
    side VARCHAR(10),                           -- buy, sell
    volume DECIMAL(10,2),
    requested_price DECIMAL(15,5),
    executed_price DECIMAL(15,5),
    status VARCHAR(20),                         -- filled, partial, rejected
    retcode INT,                                -- MT5 return code (10009 = success)
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    executed_at TIMESTAMP
);

CREATE INDEX idx_mt5_orders_user ON mt5_orders(user_id, created_at DESC);

-- Positions (Synced from MT5)
CREATE TABLE positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID REFERENCES game_sessions(session_id),
    mt5_position_id BIGINT UNIQUE NOT NULL,     -- MT5 position ticket
    symbol VARCHAR(20),
    side VARCHAR(10),                           -- buy, sell
    volume DECIMAL(10,2),
    open_price DECIMAL(15,5),
    current_price DECIMAL(15,5),
    pnl DECIMAL(15,2),                          -- Real P&L from MT5
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    last_synced_at TIMESTAMP DEFAULT NOW()      -- Last sync from MT5
);

CREATE INDEX idx_positions_user ON positions(user_id) WHERE closed_at IS NULL;
CREATE INDEX idx_positions_session ON positions(session_id);
```

---

### 3. Real-Time Leaderboard System

**Responsibilities:**
- Real-time rank updates (sub-second latency)
- Team score aggregation
- `/top` command response
- Efficient ranking algorithm (O(log n) updates)

**Three-Tier Caching Architecture:**
```
Tier 1: Redis Sorted Set (real-time, < 50ms)
  ├─ Key: leaderboard:{session_id}
  └─ Members: team_id with score (total P&L)

Tier 2: PostgreSQL Materialized View (30s refresh)
  ├─ Aggregates P&L from positions table
  └─ Fallback if Redis unavailable

Tier 3: Direct Query (fallback, ~500ms)
  └─ Real-time calculation from positions table
```

**Implementation:**
```python
class LeaderboardService:
    """
    Real-time leaderboard with three-tier caching.
    """

    def __init__(self, redis_client, db_pool):
        self.redis = redis_client
        self.db = db_pool

    async def update_team_score(self, session_id: str, team_id: str, pnl: float):
        """
        Update team score in real-time.
        O(log n) complexity via Redis sorted set.
        """
        key = f"leaderboard:{session_id}"
        await self.redis.zadd(key, {team_id: pnl})
        await self.redis.expire(key, 3600)  # 1 hour TTL

        # Broadcast update to all session participants
        await sio.emit("leaderboard:update", {
            "session_id": session_id,
            "team_id": team_id,
            "pnl": pnl,
            "rank": await self.get_team_rank(session_id, team_id)
        }, room=f"session:{session_id}")

    async def get_leaderboard(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        Get top N teams with ranks.
        Tier 1 (Redis) → Tier 2 (Materialized View) → Tier 3 (Direct Query)
        """
        # Tier 1: Try Redis
        key = f"leaderboard:{session_id}"
        rankings = await self.redis.zrevrange(key, 0, limit - 1, withscores=True)

        if rankings:
            return [
                {
                    "rank": idx + 1,
                    "team_id": team_id.decode(),
                    "pnl": score,
                    "team_name": await self._get_team_name(team_id.decode())
                }
                for idx, (team_id, score) in enumerate(rankings)
            ]

        # Tier 2: Materialized View
        try:
            return await self._get_from_materialized_view(session_id, limit)
        except Exception as e:
            logger.warning(f"Materialized view failed: {e}")

        # Tier 3: Direct Query (fallback)
        return await self._get_from_direct_query(session_id, limit)

    async def get_my_rank(self, session_id: str, user_id: str) -> Dict:
        """
        Get my team's rank in session.
        """
        # Find my team
        team_id = await self._get_user_team(session_id, user_id)

        # Get rank from Redis
        key = f"leaderboard:{session_id}"
        rank = await self.redis.zrevrank(key, team_id)
        score = await self.redis.zscore(key, team_id)

        return {
            "rank": rank + 1 if rank is not None else None,
            "team_id": team_id,
            "pnl": score,
            "total_teams": await self.redis.zcard(key)
        }
```

**Materialized View (PostgreSQL):**
```sql
CREATE MATERIALIZED VIEW team_leaderboard AS
SELECT
    t.session_id,
    t.team_id,
    t.team_name,
    SUM(p.pnl) as total_pnl,
    COUNT(DISTINCT tm.user_id) as team_size,
    NOW() as computed_at
FROM teams t
JOIN team_members tm ON t.team_id = tm.team_id
LEFT JOIN positions p ON tm.user_id = p.user_id AND p.session_id = t.session_id
GROUP BY t.session_id, t.team_id, t.team_name;

CREATE INDEX idx_team_leaderboard_session ON team_leaderboard(session_id, total_pnl DESC);

-- Refresh every 30 seconds via background job
REFRESH MATERIALIZED VIEW CONCURRENTLY team_leaderboard;
```

**Socket.IO Events:**
```python
@sio.on("leaderboard:get")
async def get_leaderboard(sid, data):
    """
    Client requests leaderboard via /top command.
    """
    session_id = data.get("session_id")
    limit = data.get("limit", 10)

    rankings = await LeaderboardService.get_leaderboard(session_id, limit)
    my_rank = await LeaderboardService.get_my_rank(session_id, user_id)

    await sio.emit("leaderboard:result", {
        "rankings": rankings,
        "my_rank": my_rank
    }, room=sid)
```

---

### 4. Achievement & Badge System

**Responsibilities:**
- Detect achievement patterns (real-time + deferred)
- Award badges (visual rewards)
- Track progress (unlock progression)
- Engagement optimization (dopamine loops)

**Achievement Types:**

| Category | Achievement | Criteria | Type |
|----------|-------------|----------|------|
| Profit | First Blood | First profitable trade | Real-time |
| Profit | Profit Streak | 5 consecutive profitable trades | Real-time |
| Profit | Profit Milestone | Reach 10% gain | Deferred (daily) |
| Consistency | Steady Eddie | 7 days trading, volatility < 5% | Deferred |
| Risk | Risk Master | Never exceed 2% risk per trade | Deferred |
| Volume | Day Trader | 20+ trades in one day | Real-time |
| Team | Team Player | Help teammate (shared analysis) | Real-time |
| Social | Trash Talker | Send 100 chat messages | Real-time |

**Implementation:**
```python
class AchievementEngine:
    """
    Two-phase achievement detection:
    - Real-time: Fast pattern checks (< 10ms)
    - Deferred: Complex analysis (nightly batch)
    """

    async def check_real_time_achievements(self, user_id: str, event: Dict):
        """
        Check fast achievements on every trade/action.
        """
        if event["type"] == "trade_executed":
            # First Blood
            if event["pnl"] > 0:
                is_first = await self._is_first_profitable_trade(user_id)
                if is_first:
                    await self._award_badge(user_id, "first_blood")

            # Profit Streak
            streak = await self._get_profit_streak(user_id)
            if streak >= 5:
                await self._award_badge(user_id, "profit_streak")

            # Day Trader
            trades_today = await self._get_trades_today(user_id)
            if trades_today >= 20:
                await self._award_badge(user_id, "day_trader")

    async def check_deferred_achievements(self, user_id: str):
        """
        Run nightly for complex analysis.
        Executed via Celery/background task.
        """
        # Steady Eddie (7 days, low volatility)
        stats = await self._get_7day_stats(user_id)
        if stats["days_active"] >= 7 and stats["volatility"] < 0.05:
            await self._award_badge(user_id, "steady_eddie")

        # Risk Master
        if stats["max_risk_per_trade"] <= 0.02:  # Never exceeded 2%
            await self._award_badge(user_id, "risk_master")
```

**Database Schema:**
```sql
CREATE TABLE achievements (
    achievement_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    badge_icon_url VARCHAR(255),
    category VARCHAR(50),
    points INT DEFAULT 10
);

CREATE TABLE user_achievements (
    user_achievement_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    achievement_id VARCHAR(50) REFERENCES achievements(achievement_id),
    unlocked_at TIMESTAMP DEFAULT NOW(),
    session_id UUID
);

CREATE TABLE achievement_progress (
    progress_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    achievement_id VARCHAR(50),
    current_value INT,
    target_value INT,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### 5. Chat Command Interface

**Command Parser:**
```python
class CommandParser:
    """
    Parse chat commands: /csv, /jsv, /top
    """

    COMMANDS = {
        "csv": "create_server",
        "jsv": "join_server",
        "top": "show_leaderboard"
    }

    async def parse_message(self, user_id: str, message: str):
        """
        Parse message and route to appropriate handler.

        Examples:
        - "/csv PanServer" → create_server("PanServer")
        - "/jsv PanServer" → join_server("PanServer")
        - "/top" → show_leaderboard()
        """
        if not message.startswith("/"):
            return None  # Not a command

        parts = message.split(" ", 1)
        command = parts[0][1:]  # Remove '/'
        args = parts[1] if len(parts) > 1 else None

        if command not in self.COMMANDS:
            return {"error": f"Unknown command: /{command}"}

        handler = self.COMMANDS[command]
        return await getattr(self, handler)(user_id, args)

    async def create_server(self, user_id: str, server_name: str):
        """Handle /csv <ServerName>"""
        session = await GameService.create_session(server_name, user_id)
        return {
            "type": "server_created",
            "session": session,
            "message": f"✅ Server '{server_name}' created! Share with friends: /jsv {server_name}"
        }

    async def join_server(self, user_id: str, server_name: str):
        """Handle /jsv <ServerName>"""
        team = await GameService.join_session(server_name, user_id)
        return {
            "type": "server_joined",
            "team": team,
            "message": f"✅ Joined '{server_name}'! Team: {team['team_name']}"
        }

    async def show_leaderboard(self, user_id: str, args: str):
        """Handle /top"""
        session_id = await self._get_user_session(user_id)
        rankings = await LeaderboardService.get_leaderboard(session_id, limit=10)
        my_rank = await LeaderboardService.get_my_rank(session_id, user_id)

        return {
            "type": "leaderboard",
            "rankings": rankings,
            "my_rank": my_rank
        }
```

**Socket.IO Integration:**
```python
@sio.on("chat:message")
async def handle_chat_message(sid, data):
    """
    Handle chat messages and route commands.
    """
    user_id = await get_user_from_sid(sid)
    message = data["message"]

    # Check if command
    result = await CommandParser().parse_message(user_id, message)

    if result:
        # Command executed
        await sio.emit("command:result", result, room=sid)
    else:
        # Normal chat message
        session_id = await get_user_session(user_id)
        await sio.emit("chat:message", {
            "user_id": user_id,
            "username": data["username"],
            "message": message,
            "timestamp": datetime.now().isoformat()
        }, room=f"session:{session_id}")
```

---

## Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Backend | FastAPI + Socket.IO (existing) | Leverage current infrastructure |
| Database | PostgreSQL (existing) | ACID compliance, materialized views |
| Cache | Redis (existing) | Sorted sets for O(log n) leaderboard |
| Real-time | Socket.IO v4 + msgpack | Industry standard, 100K+ concurrent users |
| MT5 Integration | MetaTrader5 Python library | Real broker execution, authentic spreads |
| Achievement Queue | Celery (optional) | Async deferred achievement checks |
| Frontend | React + Socket.IO client | Real-time dashboard updates |

---

## Operational Requirements & Limitations

### MT5 Demo Account Management

**Pre-Provisioning (Manual Process):**
1. **Account Creation:**
   - Admin creates 5-10 demo accounts via broker web portal
   - Record credentials (login, password, server) in encrypted vault
   - Insert into `mt5_account_pool` table
   - Set expiry dates (typically 30-90 days from broker)

2. **Account Pool Maintenance:**
   - Monitor expiry dates weekly
   - Renew expiring accounts manually (2-3 weeks before expiry)
   - Replace expired accounts with new registrations
   - Keep minimum 2 spare accounts always available

3. **Session Capacity:**
   - Hard limit: 5-10 concurrent players (account pool size)
   - If pool exhausted, new players cannot join
   - Display "No Available Accounts" error to users

**Manual Operations Checklist:**

```markdown
## Weekly Tasks (30 min/week)
- [ ] Check `mt5_account_pool` expiry dates
- [ ] Renew accounts expiring within 14 days
- [ ] Verify all accounts can login successfully
- [ ] Check for broker policy changes

## Per-Session Tasks (5 min/session)
- [ ] Verify MT5 terminal running before session start
- [ ] Check available account count > expected players
- [ ] Monitor health_check endpoint during session

## Monthly Tasks (1 hour/month)
- [ ] Rotate old accounts with fresh registrations
- [ ] Audit account usage patterns
- [ ] Review broker demo account terms
```

### MT5 Dependency Risks

**Critical Failure Modes:**

| Failure Mode | Impact | Mitigation | Recovery Time |
|-------------|--------|------------|---------------|
| MT5 terminal crash | All sessions paused | Auto-restart script, health monitoring | 1-2 min |
| Broker server downtime | Sessions frozen | Pause sessions, notify users | Broker dependent |
| Account expiry mid-session | Player disconnected, positions closed | Weekly expiry checks, 14-day buffer | Manual (hours) |
| Account pool exhaustion | New players cannot join | Reserve 2 spare accounts, capacity alerts | Manual (hours) |
| Network latency spike | Order delays | No mitigation (inherent to real execution) | N/A |

### Scale Limitations

**Current Architecture Constraints:**
- **Max concurrent players:** 10 (hard limit from account pool)
- **No horizontal scaling:** MT5 connection is single-threaded
- **No automation:** Manual account lifecycle management required
- **No fallback:** MT5 downtime = gameplay stoppage

**Scaling Roadmap (Future):**

| Player Count | Solution Required | Operational Complexity |
|-------------|-------------------|------------------------|
| 5-10 | Manual account pool (current) | Low (30 min/week) |
| 20-50 | Semi-automated account rotation | Medium (requires scripting) |
| 100+ | MT5 Manager API required | High (broker partnership needed) |

### Operational Cost Estimate

**Time Investment:**
- Setup: 2 hours (create initial account pool, configure MT5 integration)
- Weekly maintenance: 30 minutes (expiry checks, renewals)
- Per-incident: 15-60 minutes (account issues, MT5 troubleshooting)

**Risk Tolerance:**
- Acceptable for friends/testing phase (5-10 players)
- Unacceptable for public launch (100+ players)
- Migration path required if user base grows

---

## Implementation Roadmap

**Total Effort:** 155 hours (6 weeks with 1 developer)

### Sprint 1: Leaderboard Infrastructure (40h)
**Goal:** Real-time ranking system operational

- Week 1 (20h):
  - PostgreSQL schema (game_sessions, teams, team_members, virtual_balances)
  - Redis integration (sorted sets, pub/sub)
  - LeaderboardService implementation
  - Materialized view setup with auto-refresh

- Week 2 (20h):
  - Socket.IO room management (session-based broadcasting)
  - `/top` command handler
  - Real-time update propagation
  - Unit tests (ranking logic, cache invalidation)

**Deliverable:** Working leaderboard with `/top` command

---

### Sprint 2: MT5 Integration Service (35h)
**Goal:** Real MT5 demo account execution operational

- Week 3 (35h):
  - MT5IntegrationService class (account pool, order routing)
  - Account allocation/release logic
  - Order execution via MetaTrader5 library
  - Position synchronization (MT5 → database polling)
  - Balance tracking from MT5 account_info
  - Health monitoring (detect disconnections)
  - Database schema (mt5_account_pool, mt5_orders, positions)
  - Manual account pool setup (5-10 demo accounts)
  - Integration tests (real MT5 execution)

**Deliverable:** Real MT5 execution with account pool management

---

### Sprint 3: Game Session & Team Mechanics (30h)
**Goal:** `/csv` and `/jsv` commands working

- Week 4 (15h):
  - GameService implementation
  - Session lifecycle (create, join, start, end)
  - Team formation logic (4-6 players)
  - CommandParser (`/csv`, `/jsv`)
  - Socket.IO event handlers

- Week 5 (15h):
  - Team scoring aggregation
  - P&L calculation service
  - Daily snapshot scheduler
  - Team leaderboard integration
  - Integration tests

**Deliverable:** Multi-player sessions with team competition

---

### Sprint 4: Achievement System (25h)
**Goal:** Badges and engagement mechanics

- Week 6 (25h):
  - AchievementEngine (real-time + deferred)
  - Achievement definitions (8 initial achievements)
  - Badge database schema
  - Celery task queue setup (deferred checks)
  - Achievement progress tracking
  - Socket.IO notifications
  - Frontend badge display
  - Unit tests

**Deliverable:** Working achievement system

---

### Sprint 5: Real-Time Sync & Testing (30h)
**Goal:** Production-ready system

- Week 7 (15h):
  - WebSocket optimization (room-based broadcasting)
  - Performance tuning (Redis caching, query optimization)
  - Load testing (100+ concurrent players)
  - Stress testing (1000+ orders/minute)

- Week 8 (15h):
  - Integration testing (end-to-end scenarios)
  - Bug fixes
  - Documentation
  - Deployment preparation

**Deliverable:** Production-ready multi-player system

---

## Integration with Existing System

### Phase 2.1-2.4 Integration Points

**AI Trading Advisor:**
- Use technical analysis for "AI Coach" achievement
- Integrate recommendations into team chat
- Power-up: "Ask AI Advisor" (limited uses per game)

**Existing WebSocket Infrastructure:**
- Leverage `backend/app/sio.py` Socket.IO server
- Extend `backend/app/events/` with game events
- Reuse `backend/app/processors/` pattern

**MT5 Real Execution Integration:**
- Orders routed directly to MT5 via MetaTrader5 Python library
- Position data synced from MT5 (polling every 5 seconds)
- Leverage existing `data_fetcher.py` for market data
- Reuse Redis caching layer for account allocation

**Database:**
- Extend PostgreSQL schema (11 new tables)
- Leverage existing Redis client
- Reuse connection pooling

---

## Critical Success Factors

### Performance Requirements
- [ ] Leaderboard update latency < 50ms (Tier 1 cache)
- [ ] MT5 order execution < 500ms (broker-dependent)
- [ ] `/top` command response < 200ms
- [ ] Support 5-10 concurrent players (account pool limit)
- [ ] Position sync latency < 5 seconds

### MT5 Integration Validation
- [ ] All 5-10 demo accounts login successfully
- [ ] Order execution returns valid MT5 ticket numbers
- [ ] Position sync accurate (MT5 positions match database)
- [ ] Account allocation/release works without leaks
- [ ] Health check detects MT5 disconnections within 10 seconds

### Engagement Metrics
- [ ] Achievement unlock rate > 2 per player per session
- [ ] Leaderboard check frequency > 5 per session
- [ ] Team chat activity > 10 messages per session
- [ ] Session completion rate > 70%

---

## Risk Assessment & Mitigation

### Technical Risks

**Risk 1: Real-Time Leaderboard Consistency at Scale**
- **Impact:** HIGH (core feature)
- **Probability:** MEDIUM
- **Mitigation:**
  - Three-tier caching architecture (Redis → Materialized View → Direct)
  - Load testing with 1000+ concurrent players
  - Graceful degradation (fallback to Tier 2/3)
  - Monitoring & alerting

**Risk 2: MT5 Terminal Downtime or Disconnection**
- **Impact:** CRITICAL (all gameplay stops)
- **Probability:** MEDIUM (broker maintenance, network issues)
- **Mitigation:**
  - Health monitoring (10-second polling)
  - Pause sessions immediately on disconnect
  - Auto-restart script for terminal crashes
  - User notifications ("MT5 temporarily unavailable")
  - NO FALLBACK (accepted trade-off for real execution)

**Risk 3: WebSocket Connection Stability**
- **Impact:** HIGH (real-time updates)
- **Probability:** LOW (Socket.IO is proven)
- **Mitigation:**
  - Exponential backoff with server hints
  - Connection health monitoring
  - Automatic reconnection
  - Rate limiting (prevent DoS)

**Risk 4: MT5 Demo Account Expiry**
- **Impact:** HIGH (player mid-session disconnect)
- **Probability:** MEDIUM (30-90 day expiry, manual renewal)
- **Mitigation:**
  - Weekly expiry monitoring (automated alerts)
  - Renew 14 days before expiry
  - Pre-session account validation
  - Graceful position closure on expiry detection

**Risk 5: Account Pool Exhaustion**
- **Impact:** HIGH (new players blocked)
- **Probability:** LOW (if capacity monitored)
- **Mitigation:**
  - Reserve 2 spare accounts always
  - Alert when available < 3
  - Queue system for waiting players (future)
  - Display "Server Full" message

**Risk 6: Achievement Computation Performance**
- **Impact:** MEDIUM (engagement feature)
- **Probability:** LOW
- **Mitigation:**
  - Two-phase detection (real-time fast checks, deferred complex)
  - Celery async queue for deferred checks
  - Cache achievement progress
  - Batch nightly calculations

### Product Risks

**Risk 7: Team Size Imbalance**
- **Impact:** MEDIUM (fairness)
- **Probability:** MEDIUM
- **Mitigation:**
  - Enforce team size limits (4-6 players)
  - Skill-based team balancing (future)
  - Participation-weighted scoring (penalize inactive players)

**Risk 8: Engagement Drop After Initial Novelty**
- **Impact:** HIGH (retention)
- **Probability:** MEDIUM
- **Mitigation:**
  - Micro-rewards (achievements every 5-15 min, not annually)
  - Leaderboard reset weekly (fresh competition)
  - Seasonal tournaments
  - Social features (chat, taunts)

---

## Unresolved Questions

### Technical Decisions Needed

1. **MT5 Account Pool Size**
   - **Question:** How many demo accounts to provision initially?
   - **Options:**
     - A) 5 accounts (minimal, 1-2 concurrent sessions)
     - B) 10 accounts (recommended, 2-3 concurrent sessions with buffer)
     - C) 15+ accounts (overkill for testing phase)
   - **Decision:** Option B (10 accounts) - VALIDATED ✅

2. **MT5 Health Monitoring Interval**
   - **Question:** How often to check MT5 connection health?
   - **Options:**
     - A) Every 5 seconds (real-time, higher overhead)
     - B) Every 10 seconds (balanced)
     - C) Every 30 seconds (lazy, delayed failure detection)
   - **Recommendation:** Option B (10 seconds) - detects issues fast enough

3. **Achievement Queue Technology**
   - **Question:** Use Celery or in-process async?
   - **Options:**
     - A) Celery (distributed task queue)
     - B) asyncio background tasks (simpler)
   - **Recommendation:** Start with B (asyncio), migrate to A if scale demands

4. **Leaderboard Refresh Strategy**
   - **Question:** When to reset leaderboards?
   - **Options:**
     - A) Weekly reset (Monday midnight)
     - B) Session-based (each game session independent)
     - C) Rolling 7-day window
   - **Recommendation:** Option B (session-based) - cleanest model

### Product Decisions Needed

5. **MT5 Demo Account Starting Balance**
   - **Question:** What starting balance for demo accounts?
   - **Options:**
     - A) $10,000 (standard, matches most broker defaults)
     - B) $100,000 (high balance, easier to see gains)
     - C) Use broker's default (typically $10K-$100K)
   - **Recommendation:** Option C (broker default) - simplest, no configuration needed

6. **Team Formation**
   - **Question:** Auto-balance teams or manual selection?
   - **Options:**
     - A) Auto-balance by skill (if available)
     - B) Manual selection (friends choose teams)
     - C) Random assignment
   - **Recommendation:** Option B (manual) - better for cooperative play with friends

7. **Chat Moderation**
   - **Question:** How to prevent toxic behavior?
   - **Options:**
     - A) Profanity filter + report system
     - B) No moderation (friends only)
     - C) AI-powered moderation
   - **Recommendation:** Start with A (simple filter), add reporting

---

## Next Steps

### Immediate Actions (This Week)

1. **Review Research Documents**
   - Read `/plans/reports/INDEX-MULTIPLAYER-RESEARCH.md`
   - Distribute documents by role (use navigation guide)
   - Validate technology stack decisions

2. **MT5 Account Pool Setup**
   - Create 10 demo accounts via broker web portal
   - Record credentials in encrypted vault
   - Insert into `mt5_account_pool` table
   - Verify all accounts can login

3. **Validate MT5 Integration**
   - Install MetaTrader5 Python library
   - Test MT5 connection and authentication
   - Verify order execution works
   - Test position synchronization

4. **Make Pending Decisions**
   - MT5 health check interval (10s recommended)
   - Team formation method (manual recommended)
   - Achievement queue technology (asyncio recommended)

### Week 1 (Planning Sprint)

1. **Technical Design Review**
   - Review all services (LeaderboardService, MT5IntegrationService, etc.)
   - Validate database schema (mt5_account_pool, mt5_orders, positions)
   - Review Socket.IO event contracts
   - Design MT5 health monitoring system

2. **MT5 Integration Prototype**
   - Test order execution on demo account
   - Verify position sync accuracy
   - Measure order execution latency
   - Test account allocation/release logic

### Week 2-8 (Implementation)

1. **Execute Sprint Plan**
   - Sprint 1: Leaderboard (Week 2-3)
   - Sprint 2: MT5 Integration (Week 4)
   - Sprint 3: Game Sessions (Week 5-6)
   - Sprint 4: Achievements (Week 7)
   - Sprint 5: Testing (Week 8)

2. **Quality Gates**
   - Code review after each sprint
   - Load testing before production
   - User acceptance testing (internal)

---

## Final Recommendation

### Should You Proceed?

**YES - WITH CAVEATS** - Proceed with MT5 demo account approach for testing phase:

1. **Strong Product-Market Fit:**
   - Cooperative gameplay is differentiated (vs. pure competition)
   - Chat-based commands are intuitive
   - Real-time leaderboard proven engagement driver (83% increase per research)
   - Real MT5 execution provides authentic trader experience

2. **Technical Feasibility (for small scale):**
   - MetaTrader5 Python library proven and stable
   - Leverage existing infrastructure (FastAPI, MT5 data fetcher, Redis)
   - Clear integration patterns for MT5 order routing

3. **Acceptable Scope (for friends/testing):**
   - 160 hours effort (6 weeks) achievable
   - 5-10 player limit acceptable for proof-of-concept
   - Manual operations (30 min/week) manageable short-term

4. **Risks Acknowledged:**
   - ⚠️ MT5 downtime = gameplay stoppage (NO FALLBACK)
   - ⚠️ Manual account management (operational burden)
   - ⚠️ Hard cap at 10 players (not scalable)
   - ⚠️ Account expiry requires vigilance
   - ✅ Three-tier leaderboard caching prevents failures
   - ✅ Health monitoring detects MT5 issues quickly

### Implementation Priority

**Recommended Order:**
1. **Sprint 1:** Leaderboard (highest value, foundational)
2. **Sprint 2:** MT5 Integration (real execution, core differentiator)
3. **Sprint 3:** Game Sessions (enables multi-player)
4. **Sprint 4:** Achievements (engagement boost)
5. **Sprint 5:** Testing & operational hardening

**MVP Definition (After Sprint 3):**
- `/csv`, `/jsv`, `/top` commands working
- Real-time leaderboard updates
- Real MT5 demo account execution (5-10 players)
- Account pool management
- Basic team competition

**Nice-to-Have (Sprint 4-5):**
- Achievement system
- MT5 health monitoring dashboard
- Account expiry alerts
- Operational runbooks

**Critical for Launch:**
- 10 demo accounts provisioned and tested
- MT5 health monitoring operational
- Account expiry tracking setup
- Operational checklist documented

---

## Research Documentation

**Comprehensive research (3,496 lines / 120+ pages) available:**

1. **INDEX-MULTIPLAYER-RESEARCH.md** - Navigation guide (START HERE)
2. **RESEARCH_SUMMARY.md** - Executive overview
3. **researcher-251230-2313-multiplayer-trading-comprehensive.md** - Deep research
4. **researcher-251230-2313-phase3-implementation-roadmap.md** - Sprint plan with code
5. **researcher-251230-2313-dev-quick-reference.md** - Developer bookmark
6. **researcher-251230-2313-technical-deep-dives.md** - Complex solutions

**Location:** `/plans/reports/`

---

## Summary

**Vision:** Transform EV GamePad into cooperative multi-player trading game where friends compete in teams via chat commands, with real-time dashboard showing rankings and achievements. **UPDATED:** Use real MT5 demo accounts for authentic broker execution instead of paper trading simulation.

**Approach:** Leverage existing FastAPI + Socket.IO + PostgreSQL + Redis infrastructure. Build 5 new services (LeaderboardService, **MT5IntegrationService**, GameService, TeamScoringService, AchievementEngine) with **real MT5 demo account execution** and three-tier caching for performance.

**Scale:** 5-10 concurrent players (MT5 account pool limit)

**Timeline:** 6 weeks (160 hours)

**Risk:** MEDIUM-HIGH (MT5 dependency, manual ops, no fallback)

**Recommendation:** PROCEED with Sprint 1 (Leaderboard Infrastructure) → Sprint 2 (MT5 Integration)

**Critical Success Factor:** Manual account pool management acceptable for testing phase (5-10 players), but migration to Manager API required for scale (100+ players)

---

## Appendix: MT5 Integration Details

### MT5 Order Execution Flow
```
1. User initiates trade via chat/dashboard
2. Backend retrieves user's allocated MT5 account from Redis
3. Login to MT5 account via MetaTrader5.login()
4. Send order via MetaTrader5.order_send()
5. Receive MT5 result (order ticket, fill price, retcode)
6. Store order in database (mt5_orders table)
7. Update leaderboard with P&L change
8. Broadcast update to all session participants via Socket.IO

MT5 Return Codes:
- 10009 (TRADE_RETCODE_DONE): Order executed successfully
- 10013 (TRADE_RETCODE_INVALID_REQUEST): Invalid order parameters
- 10015 (TRADE_RETCODE_PRICE_CHANGED): Price changed, requote
- 10019 (TRADE_RETCODE_NO_MONEY): Insufficient margin
```

### Team Scoring (Aggregate P&L)
```
Team Score = Σ(individual P&L for all team members)

Example:
- Player 1: +$500
- Player 2: +$300
- Player 3: -$100
- Player 4: +$400
- Team Score = $500 + $300 - $100 + $400 = $1,100
```

### Leaderboard Rank Update (Redis)
```python
# O(log n) complexity via sorted set
await redis.zadd(f"leaderboard:{session_id}", {team_id: pnl})
rank = await redis.zrevrank(f"leaderboard:{session_id}", team_id)
```

### MT5 Account Pool Management
```sql
-- Check available accounts
SELECT COUNT(*) FROM mt5_account_pool WHERE status = 'available';

-- Check expiring accounts (next 14 days)
SELECT mt5_login, expires_at
FROM mt5_account_pool
WHERE expires_at < NOW() + INTERVAL '14 days'
  AND status != 'expired';

-- Manually mark account as expired
UPDATE mt5_account_pool
SET status = 'expired'
WHERE mt5_login = 12345678;
```

---

**Status:** Updated with MT5 Demo Account Architecture ✅
**Last Updated:** 2025-12-31
**Next Action:** Provision 10 MT5 demo accounts → Setup account pool → Begin Sprint 1
