# Phase 02: MT5 Integration Service

**Priority:** P1 (CRITICAL - Core differentiator)
**Status:** Pending
**Effort:** 35 hours (2 weeks)
**Dependencies:** Phase 1 (Leaderboard), 10 pre-provisioned MT5 demo accounts

## Context Links

- **Brainstorm:** `/plans/reports/brainstorm-251230-2302-multiplayer-trading-game.md` (Section 2: MT5 Integration Service)
- **Existing MT5 Module:** `backend/app/mt5/` (connection_manager, trading_operations)
- **Phase 1 Leaderboard:** `./phase-01-leaderboard-infrastructure.md`

## Overview

Build MT5 Integration Service to route player orders to real MT5 demo accounts with account pool management, position synchronization, and health monitoring. Replaces paper trading with authentic broker execution.

**Goal:** 5-10 players trading on real MT5 demo accounts with automatic allocation/release and P&L sync to leaderboard.

## Key Insights

1. **Account Pool Critical** - Pre-provision 10 accounts, allocate on join, release on leave
2. **MetaTrader5 Library** - Python API synchronous, wrap in asyncio executor
3. **Position Sync** - Poll MT5 every 5s for open positions, update DB + leaderboard
4. **Health Monitoring** - Detect MT5 disconnect within 10s, pause sessions
5. **No Fallback** - MT5 down = gameplay stops (accepted trade-off for real execution)

## Requirements

### Functional
- [ ] Allocate MT5 account from pool on player join
- [ ] Route orders to allocated MT5 account
- [ ] Sync open positions from MT5 to database (5s interval)
- [ ] Update team leaderboard on P&L change
- [ ] Release account back to pool on player leave
- [ ] Health check detects MT5 disconnection within 10s

### Non-Functional
- [ ] Order execution < 500ms (broker-dependent)
- [ ] Position sync latency < 5s
- [ ] Account allocation < 100ms (Redis lookup)
- [ ] Support 10 concurrent players (full pool)
- [ ] Zero account leaks (always release)

## Architecture

### Account Pool Management

```
┌──────────────────────────────────────────────────────┐
│ PostgreSQL: mt5_account_pool Table                   │
│  - account_id (PK)                                   │
│  - mt5_login, mt5_password, mt5_server               │
│  - status: available | allocated | expired           │
│  - allocated_to_user, allocated_to_session           │
│  - expires_at (demo expiry date)                     │
└──────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│ Redis Cache: user:{user_id}:mt5                     │
│  - account_id, mt5_login, mt5_server                │
│  - Fast lookup for order routing                     │
└──────────────────────────────────────────────────────┘
```

### Order Execution Flow

```
1. Player → Chat command or dashboard action
2. Backend → Get user's MT5 account from Redis
3. MT5Service → Login to account via MetaTrader5.login()
4. MT5Service → Send order via MetaTrader5.order_send()
5. MT5 → Returns order ticket, fill price, retcode
6. Backend → Store in mt5_orders table
7. Backend → Update leaderboard with P&L change
8. Backend → Broadcast via Socket.IO
```

### Position Sync

```
┌─────────────────────────────────────────────┐
│ Background Task (every 5 seconds)           │
│  1. For each allocated account              │
│  2. Login to MT5 account                    │
│  3. Call MetaTrader5.positions_get()        │
│  4. Update positions table                  │
│  5. Calculate team P&L delta                │
│  6. Update leaderboard if changed           │
└─────────────────────────────────────────────┘
```

## Related Code Files

### Files to CREATE

1. **`backend/app/services/mt5_integration_service.py`** - Core MT5 service
   - Account allocation/release
   - Order routing to MT5
   - Position synchronization
   - Health monitoring

2. **`backend/app/models/mt5_models.py`** - MT5 data models
   - MT5Account, MT5Order, MT5Position

3. **`backend/app/tasks/position_sync_task.py`** - Background position sync
   - Poll MT5 every 5s
   - Update positions + leaderboard

4. **`backend/app/tasks/health_check_task.py`** - MT5 health monitoring
   - Check terminal connectivity every 10s
   - Pause sessions on disconnect

5. **`migrations/005_create_mt5_account_pool.sql`** - Account pool schema
6. **`migrations/006_create_mt5_orders.sql`** - Orders schema
7. **`migrations/007_create_positions.sql`** - Positions schema

### Files to MODIFY

1. **`backend/app/main.py`** - Register background tasks
2. **`backend/app/events/game_events.py`** - Add account allocation on join
3. **`backend/app/config.py`** - Add MT5 configuration

## Implementation Steps

### Week 1: Account Pool & Core Service (18h)

#### Step 1.1: Database Schema (3h)

**Migration 005: mt5_account_pool**
```sql
CREATE TABLE mt5_account_pool (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mt5_login BIGINT UNIQUE NOT NULL,
    mt5_password VARCHAR(100) NOT NULL,  -- Encrypted
    mt5_server VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'available',
    allocated_to_user VARCHAR(100),
    allocated_to_session UUID REFERENCES game_sessions(session_id),
    allocated_at TIMESTAMP,
    released_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN ('available', 'allocated', 'expired'))
);

CREATE INDEX idx_mt5_pool_status ON mt5_account_pool(status)
    WHERE status = 'available';
```

**Migration 006: mt5_orders**
```sql
CREATE TABLE mt5_orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    session_id UUID REFERENCES game_sessions(session_id),
    mt5_order_id BIGINT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(10),  -- market, limit, stop
    side VARCHAR(10),        -- buy, sell
    volume DECIMAL(10,2),
    requested_price DECIMAL(15,5),
    executed_price DECIMAL(15,5),
    status VARCHAR(20),      -- filled, partial, rejected
    retcode INT,             -- MT5 return code
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    executed_at TIMESTAMP
);

CREATE INDEX idx_mt5_orders_user ON mt5_orders(user_id, created_at DESC);
```

**Migration 007: positions**
```sql
CREATE TABLE positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    session_id UUID REFERENCES game_sessions(session_id),
    mt5_position_id BIGINT UNIQUE NOT NULL,
    symbol VARCHAR(20),
    side VARCHAR(10),
    volume DECIMAL(10,2),
    open_price DECIMAL(15,5),
    current_price DECIMAL(15,5),
    pnl DECIMAL(15,2),
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    last_synced_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_positions_user ON positions(user_id) WHERE closed_at IS NULL;
CREATE INDEX idx_positions_session ON positions(session_id);
```

#### Step 1.2: MT5 Integration Service - Core (8h)

Create `backend/app/services/mt5_integration_service.py`:

```python
"""MT5 Integration Service - Real broker execution."""
import MetaTrader5 as mt5
from typing import Dict, Optional, List
import asyncio
import logging
from decimal import Decimal
from app.database.redis_client import redis_client
from app.database.postgres_client import postgres_client
from app.services.leaderboard_service import leaderboard_service
from app.models.mt5_models import MT5Order, MT5Position

logger = logging.getLogger(__name__)

class MT5IntegrationService:
    """Manage MT5 account pool and route orders to real MT5."""

    def __init__(self):
        self.initialized = False

    async def initialize(self):
        """Initialize MT5 terminal connection."""
        # Run synchronous MT5 init in executor
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, mt5.initialize)

        if not success:
            raise Exception(f"MT5 init failed: {mt5.last_error()}")

        self.initialized = True
        logger.info("MT5 terminal connected")

    async def allocate_account(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, str]:
        """
        Allocate available MT5 account from pool.

        Returns: {"account_id": "...", "mt5_login": 12345, ...}
        Raises: Exception if no accounts available
        """
        # Use FOR UPDATE SKIP LOCKED for atomic allocation
        query = """
            SELECT account_id, mt5_login, mt5_password, mt5_server
            FROM mt5_account_pool
            WHERE status = 'available'
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """

        async with postgres_client.pool.acquire() as conn:
            async with conn.transaction():
                account = await conn.fetchrow(query)

                if not account:
                    raise Exception("No available MT5 accounts. Pool exhausted.")

                # Mark as allocated
                await conn.execute("""
                    UPDATE mt5_account_pool
                    SET status = 'allocated',
                        allocated_to_user = $1,
                        allocated_to_session = $2,
                        allocated_at = NOW()
                    WHERE account_id = $3
                """, user_id, session_id, account["account_id"])

        # Cache in Redis for fast lookup
        await redis_client.hset(f"user:{user_id}:mt5", {
            "account_id": str(account["account_id"]),
            "mt5_login": str(account["mt5_login"]),
            "mt5_server": account["mt5_server"]
        })

        logger.info(f"Allocated MT5 account {account['mt5_login']} to {user_id}")

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
        side: str,  # buy, sell
        volume: float,
        order_type: str = "market",
        price: Optional[float] = None
    ) -> MT5Order:
        """
        Route order to user's MT5 account.

        Returns: MT5Order with execution details
        """
        # Get user's account
        account_info = await redis_client.hgetall(f"user:{user_id}:mt5")
        if not account_info:
            raise Exception("No MT5 account allocated to user")

        # Get password from DB (not cached for security)
        password = await self._get_account_password(account_info[b"account_id"].decode())

        # Login to MT5 (synchronous, run in executor)
        loop = asyncio.get_event_loop()
        login_success = await loop.run_in_executor(
            None,
            mt5.login,
            int(account_info[b"mt5_login"]),
            password,
            account_info[b"mt5_server"].decode()
        )

        if not login_success:
            raise Exception(f"MT5 login failed: {mt5.last_error()}")

        # Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if side == "buy" else mt5.ORDER_TYPE_SELL,
            "deviation": 10,
            "magic": 234000,
            "comment": f"EV GamePad - {user_id[:8]}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        if order_type != "market" and price:
            request["price"] = price

        # Send order (synchronous)
        result = await loop.run_in_executor(None, mt5.order_send, request)

        # Store in database
        session_id = await self._get_user_session(user_id)
        order = MT5Order(
            user_id=user_id,
            session_id=session_id,
            mt5_order_id=result.order,
            symbol=symbol,
            order_type=order_type,
            side=side,
            volume=Decimal(str(volume)),
            requested_price=Decimal(str(price)) if price else None,
            executed_price=Decimal(str(result.price)),
            status="filled" if result.retcode == 10009 else "rejected",
            retcode=result.retcode,
            comment=result.comment
        )

        await self._store_order(order)

        # Update leaderboard (async)
        asyncio.create_task(self._update_leaderboard_after_trade(user_id, session_id))

        logger.info(f"Order executed: {result.order}, retcode={result.retcode}")
        return order

    async def release_account(self, user_id: str):
        """Release MT5 account back to pool."""
        account_info = await redis_client.hgetall(f"user:{user_id}:mt5")

        if not account_info:
            logger.warning(f"No MT5 account to release for {user_id}")
            return

        # NOTE: Positions kept open on player leave (by design)
        # Players retain positions for continuous trading across sessions

        # Mark as available
        await postgres_client.execute("""
            UPDATE mt5_account_pool
            SET status = 'available',
                allocated_to_user = NULL,
                allocated_to_session = NULL,
                released_at = NOW()
            WHERE account_id = $1
        """, account_info[b"account_id"].decode())

        # Clear Redis cache
        await redis_client.delete(f"user:{user_id}:mt5")

        logger.info(f"Released MT5 account for {user_id}")

    async def sync_positions(self, user_id: str) -> List[MT5Position]:
        """
        Sync open positions from MT5 to database.
        Called by background task every 5 seconds.
        """
        account_info = await redis_client.hgetall(f"user:{user_id}:mt5")
        if not account_info:
            return []

        # Login and fetch positions
        password = await self._get_account_password(account_info[b"account_id"].decode())
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(
            None,
            mt5.login,
            int(account_info[b"mt5_login"]),
            password,
            account_info[b"mt5_server"].decode()
        )

        positions = await loop.run_in_executor(None, mt5.positions_get)

        if positions is None:
            positions = []

        # Update database
        session_id = await self._get_user_session(user_id)
        synced = []

        for pos in positions:
            position = MT5Position(
                user_id=user_id,
                session_id=session_id,
                mt5_position_id=pos.ticket,
                symbol=pos.symbol,
                side="buy" if pos.type == 0 else "sell",
                volume=Decimal(str(pos.volume)),
                open_price=Decimal(str(pos.price_open)),
                current_price=Decimal(str(pos.price_current)),
                pnl=Decimal(str(pos.profit))
            )

            await self._upsert_position(position)
            synced.append(position)

        return synced

    async def health_check(self) -> Dict[str, str]:
        """Check MT5 terminal health."""
        loop = asyncio.get_event_loop()
        terminal_info = await loop.run_in_executor(None, mt5.terminal_info)

        if not terminal_info:
            return {"status": "down", "error": "MT5 terminal disconnected"}

        return {
            "status": "up",
            "connected": terminal_info.connected,
            "ping": terminal_info.ping_last
        }

    # ==================== Helper Methods ====================

    async def _get_account_password(self, account_id: str) -> str:
        """Get decrypted password from DB."""
        query = "SELECT mt5_password FROM mt5_account_pool WHERE account_id = $1"
        row = await postgres_client.fetchrow(query, account_id)
        # TODO: Decrypt password (use cryptography library)
        return row["mt5_password"] if row else ""

    async def _get_user_session(self, user_id: str) -> Optional[str]:
        """Find user's current session."""
        query = """
            SELECT t.session_id
            FROM team_members tm
            JOIN teams t ON tm.team_id = t.team_id
            JOIN game_sessions gs ON t.session_id = gs.session_id
            WHERE tm.user_id = $1 AND gs.status = 'active'
            LIMIT 1
        """
        row = await postgres_client.fetchrow(query, user_id)
        return str(row["session_id"]) if row else None

    async def _store_order(self, order: MT5Order):
        """Store order in database."""
        await postgres_client.execute("""
            INSERT INTO mt5_orders (
                user_id, session_id, mt5_order_id, symbol, order_type,
                side, volume, requested_price, executed_price,
                status, retcode, comment, executed_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())
        """, order.user_id, order.session_id, order.mt5_order_id,
             order.symbol, order.order_type, order.side, order.volume,
             order.requested_price, order.executed_price, order.status,
             order.retcode, order.comment)

    async def _upsert_position(self, position: MT5Position):
        """Insert or update position."""
        await postgres_client.execute("""
            INSERT INTO positions (
                user_id, session_id, mt5_position_id, symbol, side,
                volume, open_price, current_price, pnl, last_synced_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
            ON CONFLICT (mt5_position_id) DO UPDATE
            SET current_price = $8, pnl = $9, last_synced_at = NOW()
        """, position.user_id, position.session_id, position.mt5_position_id,
             position.symbol, position.side, position.volume,
             position.open_price, position.current_price, position.pnl)

    async def _update_leaderboard_after_trade(self, user_id: str, session_id: str):
        """Recalculate team P&L and update leaderboard."""
        # Get user's team
        team_id = await postgres_client.fetchval("""
            SELECT team_id FROM team_members WHERE user_id = $1
        """, user_id)

        if not team_id:
            return

        # Calculate total team P&L
        total_pnl = await postgres_client.fetchval("""
            SELECT COALESCE(SUM(p.pnl), 0)
            FROM positions p
            JOIN team_members tm ON p.user_id = tm.user_id
            WHERE tm.team_id = $1 AND p.closed_at IS NULL
        """, team_id)

        # Update leaderboard
        await leaderboard_service.update_team_score(
            session_id, str(team_id), Decimal(str(total_pnl))
        )

# Global instance
mt5_service = MT5IntegrationService()
```

#### Step 1.3: Data Models (2h)

Create `backend/app/models/mt5_models.py`:

```python
"""MT5 data models."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class MT5Account(BaseModel):
    """MT5 account from pool."""
    account_id: str
    mt5_login: int
    mt5_server: str
    status: str  # available, allocated, expired
    allocated_to_user: Optional[str] = None
    allocated_to_session: Optional[str] = None
    expires_at: Optional[datetime] = None

class MT5Order(BaseModel):
    """MT5 order execution result."""
    user_id: str
    session_id: str
    mt5_order_id: int
    symbol: str
    order_type: str
    side: str
    volume: Decimal
    requested_price: Optional[Decimal] = None
    executed_price: Decimal
    status: str  # filled, partial, rejected
    retcode: int
    comment: Optional[str] = None

class MT5Position(BaseModel):
    """MT5 open position."""
    user_id: str
    session_id: str
    mt5_position_id: int
    symbol: str
    side: str
    volume: Decimal
    open_price: Decimal
    current_price: Decimal
    pnl: Decimal
```

#### Step 1.4: Manual Account Pool Setup (2h)

Create script `scripts/setup_mt5_account_pool.py`:

```python
"""Populate MT5 account pool from manual provisioning."""
import asyncpg
import asyncio
from cryptography.fernet import Fernet
import os

# Generate encryption key (store in env)
ENCRYPTION_KEY = os.getenv("MT5_PASSWORD_KEY", Fernet.generate_key().decode())
cipher = Fernet(ENCRYPTION_KEY.encode())

async def populate_account_pool():
    """Insert 10 demo accounts into pool."""
    conn = await asyncpg.connect(
        host="localhost",
        database="ev_gamepad",
        user="postgres",
        password=""
    )

    accounts = [
        # (login, password, server, expires_at)
        (12345678, "password1", "Broker-Demo", "2025-03-31"),
        (12345679, "password2", "Broker-Demo", "2025-03-31"),
        # ... add remaining 8 accounts
    ]

    for login, password, server, expires_at in accounts:
        encrypted_password = cipher.encrypt(password.encode()).decode()

        await conn.execute("""
            INSERT INTO mt5_account_pool (
                mt5_login, mt5_password, mt5_server, expires_at
            ) VALUES ($1, $2, $3, $4)
        """, login, encrypted_password, server, expires_at)

    print(f"Inserted {len(accounts)} accounts into pool")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(populate_account_pool())
```

Run:
```bash
python scripts/setup_mt5_account_pool.py
```

#### Step 1.5: Unit Tests (3h)

Create `backend/tests/test_mt5_integration_service.py`:

```python
"""Tests for MT5 integration service."""
import pytest
from app.services.mt5_integration_service import mt5_service

@pytest.mark.asyncio
async def test_allocate_account(postgres_client):
    """Test account allocation from pool."""
    user_id = "test-user-1"
    session_id = "test-session-1"

    account = await mt5_service.allocate_account(user_id, session_id)

    assert account["status"] == "allocated"
    assert account["mt5_login"] > 0

    # Verify DB update
    row = await postgres_client.fetchrow(
        "SELECT * FROM mt5_account_pool WHERE account_id = $1",
        account["account_id"]
    )
    assert row["status"] == "allocated"
    assert row["allocated_to_user"] == user_id

@pytest.mark.asyncio
async def test_execute_order_market(mt5_service):
    """Test market order execution."""
    user_id = "test-user-1"

    # Allocate account first
    await mt5_service.allocate_account(user_id, "test-session")

    # Execute order
    order = await mt5_service.execute_order(
        user_id,
        "EURUSD",
        "buy",
        0.01  # 0.01 lot
    )

    assert order.status in ["filled", "rejected"]
    assert order.mt5_order_id > 0
    if order.status == "filled":
        assert order.executed_price > 0
```

### Week 2: Position Sync & Health Monitoring (17h)

#### Step 2.1: Position Sync Background Task (6h)

Create `backend/app/tasks/position_sync_task.py`:

```python
"""Background task to sync positions from MT5 every 5 seconds."""
import asyncio
import logging
from app.database.postgres_client import postgres_client
from app.services.mt5_integration_service import mt5_service
from app.services.leaderboard_service import leaderboard_service

logger = logging.getLogger(__name__)

class PositionSyncTask:
    """Sync positions from MT5 to database."""

    def __init__(self, interval: int = 5):
        self.interval = interval
        self.running = False

    async def start(self):
        """Start background sync loop."""
        self.running = True
        logger.info("Position sync task started (5s interval)")

        while self.running:
            try:
                await self._sync_all_positions()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Position sync failed: {e}")
                await asyncio.sleep(self.interval)

    async def stop(self):
        """Stop sync task."""
        self.running = False
        logger.info("Position sync task stopped")

    async def _sync_all_positions(self):
        """Sync positions for all allocated accounts."""
        # Get all allocated accounts
        query = """
            SELECT allocated_to_user, allocated_to_session
            FROM mt5_account_pool
            WHERE status = 'allocated'
        """
        rows = await postgres_client.fetch(query)

        # Track P&L changes per session
        session_changes = {}

        for row in rows:
            user_id = row["allocated_to_user"]
            session_id = str(row["allocated_to_session"])

            # Sync positions for this user
            positions = await mt5_service.sync_positions(user_id)

            # Aggregate P&L changes
            if session_id not in session_changes:
                session_changes[session_id] = []

            for pos in positions:
                session_changes[session_id].append((user_id, pos.pnl))

        # Update leaderboards
        for session_id, changes in session_changes.items():
            await self._update_session_leaderboard(session_id, changes)

        logger.debug(f"Synced positions for {len(rows)} users")

    async def _update_session_leaderboard(self, session_id: str, changes: list):
        """Update leaderboard for session based on P&L changes."""
        # Group by team
        team_pnls = {}

        for user_id, pnl in changes:
            # Get user's team
            team_id = await postgres_client.fetchval(
                "SELECT team_id FROM team_members WHERE user_id = $1", user_id
            )
            if team_id:
                team_pnls[str(team_id)] = team_pnls.get(str(team_id), 0) + pnl

        # Update leaderboard for each team
        for team_id, total_pnl in team_pnls.items():
            await leaderboard_service.update_team_score(
                session_id, team_id, total_pnl
            )

# Global instance
position_sync_task = PositionSyncTask()
```

Update `backend/app/main.py`:
```python
from app.tasks.position_sync_task import position_sync_task

@app.on_event("startup")
async def startup_event():
    # ... existing startup ...
    await mt5_service.initialize()
    asyncio.create_task(position_sync_task.start())

@app.on_event("shutdown")
async def shutdown_event():
    await position_sync_task.stop()
```

#### Step 2.2: Health Check Task (4h)

Create `backend/app/tasks/health_check_task.py`:

```python
"""MT5 health monitoring task."""
import asyncio
import logging
from app.services.mt5_integration_service import mt5_service

logger = logging.getLogger(__name__)

class HealthCheckTask:
    """Monitor MT5 terminal health every 10 seconds."""

    def __init__(self, interval: int = 10):
        self.interval = interval
        self.running = False
        self.is_healthy = True

    async def start(self):
        """Start health monitoring."""
        self.running = True
        logger.info("Health check task started (10s interval)")

        while self.running:
            try:
                await self._check_health()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.interval)

    async def stop(self):
        """Stop health monitoring."""
        self.running = False

    async def _check_health(self):
        """Check MT5 terminal health."""
        result = await mt5_service.health_check()

        if result["status"] == "down":
            if self.is_healthy:
                # Status changed to down
                logger.error("MT5 terminal DISCONNECTED!")
                await self._pause_all_sessions()
                self.is_healthy = False
        else:
            if not self.is_healthy:
                # Status recovered
                logger.info("MT5 terminal RECONNECTED")
                self.is_healthy = True

    async def _pause_all_sessions(self):
        """Pause all active game sessions."""
        from app.database.postgres_client import postgres_client

        await postgres_client.execute("""
            UPDATE game_sessions
            SET status = 'paused'
            WHERE status = 'active'
        """)

        logger.warning("Paused all active sessions due to MT5 downtime")

# Global instance
health_check_task = HealthCheckTask()
```

#### Step 2.3: Integration with Game Events (3h)

Update `backend/app/events/game_events.py`:

```python
from app.services.mt5_integration_service import mt5_service

@sio.on("game:join")
async def handle_join_game(sid, data):
    """Player joins game session."""
    session_name = data.get("session_name")
    user_id = data.get("user_id")

    # ... existing join logic ...

    # Allocate MT5 account
    try:
        account = await mt5_service.allocate_account(user_id, session_id)
        logger.info(f"Allocated MT5 account {account['mt5_login']} to {user_id}")

        await sio.emit("game:account_allocated", {
            "mt5_login": account["mt5_login"],
            "mt5_server": account["mt5_server"]
        }, room=sid)

    except Exception as e:
        await sio.emit("error", {
            "message": f"No MT5 accounts available: {str(e)}"
        }, room=sid)

@sio.on("game:leave")
async def handle_leave_game(sid, data):
    """Player leaves game session."""
    user_id = data.get("user_id")

    # Release MT5 account
    await mt5_service.release_account(user_id)

    # ... existing leave logic ...

@sio.on("trade:execute")
async def handle_execute_trade(sid, data):
    """Execute trade on MT5."""
    user_id = data.get("user_id")
    symbol = data.get("symbol")
    side = data.get("side")  # buy, sell
    volume = float(data.get("volume"))

    try:
        order = await mt5_service.execute_order(
            user_id, symbol, side, volume
        )

        await sio.emit("trade:executed", {
            "order_id": order.mt5_order_id,
            "status": order.status,
            "executed_price": float(order.executed_price),
            "retcode": order.retcode
        }, room=sid)

    except Exception as e:
        await sio.emit("trade:error", {"message": str(e)}, room=sid)
```

#### Step 2.4: Integration Tests (4h)

Create `backend/tests/test_mt5_integration.py`:

```python
"""End-to-end MT5 integration tests."""
import pytest

@pytest.mark.asyncio
async def test_full_trading_flow(mt5_service, test_user):
    """Test complete trading flow: allocate → trade → sync → release."""
    user_id = test_user["user_id"]
    session_id = "test-session"

    # 1. Allocate account
    account = await mt5_service.allocate_account(user_id, session_id)
    assert account["status"] == "allocated"

    # 2. Execute order
    order = await mt5_service.execute_order(
        user_id, "EURUSD", "buy", 0.01
    )
    assert order.status == "filled"

    # 3. Sync positions
    positions = await mt5_service.sync_positions(user_id)
    assert len(positions) > 0

    # 4. Release account
    await mt5_service.release_account(user_id)

    # Verify account back in pool
    row = await postgres_client.fetchrow(
        "SELECT status FROM mt5_account_pool WHERE account_id = $1",
        account["account_id"]
    )
    assert row["status"] == "available"
```

## Todo Checklist

### Week 1: Account Pool & Core
- [ ] Create database migrations (005-007)
- [ ] Run migrations on PostgreSQL
- [ ] Implement MT5IntegrationService
- [ ] Create MT5 data models
- [ ] Setup account pool provisioning script
- [ ] Encrypt and insert 10 demo accounts
- [ ] Write unit tests for allocation/execution

### Week 2: Position Sync & Health
- [ ] Implement PositionSyncTask (5s interval)
- [ ] Implement HealthCheckTask (10s interval)
- [ ] Update main.py startup/shutdown
- [ ] Add account allocation to game:join event
- [ ] Add trade execution Socket.IO handler
- [ ] Write integration tests
- [ ] Test with real MT5 demo accounts

## Success Criteria

### Functional
- [ ] 10 accounts provisioned and login successful
- [ ] Account allocation atomic (no double-allocate)
- [ ] Orders execute on real MT5 broker
- [ ] Positions sync within 5 seconds
- [ ] Leaderboard updates on P&L change
- [ ] Account released on player leave
- [ ] Health check detects disconnect within 10s

### Performance
- [ ] Account allocation < 100ms
- [ ] Order execution < 500ms
- [ ] Position sync < 5s latency
- [ ] Support 10 concurrent players
- [ ] Zero account leaks (100% release rate)

## Risk Assessment

### HIGH Risks
**MT5 Terminal Crash** - All gameplay stops
- Mitigation: Auto-restart script, health monitoring
- Recovery: 1-2 min restart, sessions resume

**Account Expiry** - Player mid-session disconnect
- Mitigation: Weekly expiry checks, 14-day buffer
- Recovery: Manual account renewal (hours)

### MEDIUM Risks
**Position Sync Lag** - Delayed leaderboard updates
- Mitigation: 5s sync interval, optimistic updates
- Recovery: Next sync corrects

## Security Considerations

- **Password Encryption:** Use cryptography.Fernet for mt5_password
- **Credential Storage:** Never send passwords to frontend
- **Account Isolation:** Each user gets dedicated account
- **Order Validation:** Validate volume, symbol before MT5 call

## Next Steps

1. **Phase 3:** Game Sessions & Teams (uses MT5 service for trading)
2. **Operations:** Monitor account pool usage, renewal alerts
3. **Optimization:** Connection pooling for MT5 login calls

## Resolved Decisions

1. ✅ **Broker Selection** - Fixed broker confirmed for demo accounts
2. ✅ **Position Close on Leave** - Keep positions open (do NOT auto-close)
3. ✅ **Health Check Interval** - 10s confirmed optimal

## Unresolved Questions

1. **Order Type Support:** Market only or add limit/stop orders?
2. **Sync Interval:** 5s optimal or adjust per testing?
3. **Mock MT5 for Tests:** Use real accounts or mock MT5 library?
