"""MT5 Integration Service - Phase 02

Handles MT5 account pool management, order routing, and position synchronization.
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from cryptography.fernet import Fernet
import MetaTrader5 as mt5

from app.database.postgres_client import postgres_client
from app.models.mt5_models import (
    MT5Account,
    MT5AccountAllocation,
    MT5Order,
    MT5Position,
    MT5PositionSync,
    AccountStatus,
    HealthStatus,
    OrderStatus,
    OrderType,
    PositionStatus,
    AccountPoolStats
)
from app.config import config

logger = logging.getLogger(__name__)


class MT5IntegrationService:
    """
    Manages MT5 account pool and trading operations.

    Features:
    - Account allocation with row-level locking (FOR UPDATE SKIP LOCKED)
    - Password encryption/decryption using Fernet
    - Order routing to allocated accounts
    - Position synchronization (5s interval)
    - Health monitoring (10s interval)
    """

    def __init__(self):
        self._encryption_key: Optional[bytes] = None
        self._cipher: Optional[Fernet] = None
        self._initialized = False

    async def initialize(self):
        """Initialize encryption key from config."""
        if self._initialized:
            return

        # Get or generate encryption key
        key = config.MT5_ENCRYPTION_KEY if hasattr(config, 'MT5_ENCRYPTION_KEY') else None
        if not key:
            # Generate new key (should be saved to config in production)
            key = Fernet.generate_key()
            logger.warning("Generated new encryption key - save to config.MT5_ENCRYPTION_KEY")

        if isinstance(key, str):
            key = key.encode('utf-8')

        self._encryption_key = key
        self._cipher = Fernet(key)
        self._initialized = True
        logger.info("MT5 Integration Service initialized")

    def _encrypt_password(self, password: str) -> str:
        """Encrypt MT5 account password."""
        if not self._cipher:
            raise RuntimeError("Service not initialized")
        encrypted = self._cipher.encrypt(password.encode('utf-8'))
        return encrypted.decode('utf-8')

    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt MT5 account password."""
        if not self._cipher:
            raise RuntimeError("Service not initialized")
        decrypted = self._cipher.decrypt(encrypted_password.encode('utf-8'))
        return decrypted.decode('utf-8')

    # ============= ACCOUNT POOL MANAGEMENT =============

    async def allocate_account(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> Optional[MT5AccountAllocation]:
        """
        Allocate an available MT5 account to user.

        Uses FOR UPDATE SKIP LOCKED to prevent race conditions.

        Args:
            user_id: User requesting account
            session_id: Optional game session ID (Phase 03)

        Returns:
            MT5AccountAllocation with decrypted credentials, or None if pool exhausted
        """
        query = """
            UPDATE mt5_account_pool
            SET status = 'in_use',
                allocated_to_user_id = $1,
                allocated_at = NOW()
            WHERE account_id = (
                SELECT account_id
                FROM mt5_account_pool
                WHERE status = 'available' AND health_status = 'healthy'
                ORDER BY last_health_check DESC NULLS LAST
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING account_number, broker_server, encrypted_password, allocated_at
        """

        try:
            result = await postgres_client.fetchrow(query, user_id)

            if not result:
                logger.warning(f"Account pool exhausted for user {user_id}")
                return None

            # Decrypt password
            decrypted_password = self._decrypt_password(result['encrypted_password'])

            allocation = MT5AccountAllocation(
                account_number=result['account_number'],
                broker_server=result['broker_server'],
                decrypted_password=decrypted_password,
                allocated_at=result['allocated_at']
            )

            logger.info(f"Allocated account {allocation.account_number} to user {user_id}")
            return allocation

        except Exception as e:
            logger.error(f"Account allocation failed: {e}")
            return None

    async def release_account(self, user_id: str) -> bool:
        """
        Release user's allocated account back to pool.

        Args:
            user_id: User releasing account

        Returns:
            True if released successfully
        """
        query = """
            UPDATE mt5_account_pool
            SET status = 'available',
                allocated_to_user_id = NULL,
                allocated_at = NULL
            WHERE allocated_to_user_id = $1 AND status = 'in_use'
            RETURNING account_number
        """

        try:
            result = await postgres_client.fetchrow(query, user_id)

            if result:
                logger.info(f"Released account {result['account_number']} from user {user_id}")
                return True
            else:
                logger.warning(f"No account to release for user {user_id}")
                return False

        except Exception as e:
            logger.error(f"Account release failed: {e}")
            return False

    async def get_user_account(self, user_id: str) -> Optional[MT5AccountAllocation]:
        """Get currently allocated account for user."""
        query = """
            SELECT account_number, broker_server, encrypted_password, allocated_at
            FROM mt5_account_pool
            WHERE allocated_to_user_id = $1 AND status = 'in_use'
        """

        try:
            result = await postgres_client.fetchrow(query, user_id)

            if not result:
                return None

            decrypted_password = self._decrypt_password(result['encrypted_password'])

            return MT5AccountAllocation(
                account_number=result['account_number'],
                broker_server=result['broker_server'],
                decrypted_password=decrypted_password,
                allocated_at=result['allocated_at']
            )

        except Exception as e:
            logger.error(f"Failed to get user account: {e}")
            return None

    async def get_pool_stats(self) -> AccountPoolStats:
        """Get account pool statistics."""
        query = """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'available') as available,
                COUNT(*) FILTER (WHERE status = 'in_use') as in_use,
                COUNT(*) FILTER (WHERE status = 'error') as error,
                COUNT(*) FILTER (WHERE status = 'expired') as expired,
                COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy,
                COUNT(*) FILTER (WHERE health_status = 'unhealthy') as unhealthy,
                COUNT(*) FILTER (WHERE health_status = 'disconnected') as disconnected
            FROM mt5_account_pool
        """

        try:
            result = await postgres_client.fetchrow(query)

            return AccountPoolStats(
                total_accounts=result['total'],
                available=result['available'],
                in_use=result['in_use'],
                error=result['error'],
                expired=result['expired'],
                healthy=result['healthy'],
                unhealthy=result['unhealthy'],
                disconnected=result['disconnected']
            )

        except Exception as e:
            logger.error(f"Failed to get pool stats: {e}")
            return AccountPoolStats(
                total_accounts=0, available=0, in_use=0, error=0,
                expired=0, healthy=0, unhealthy=0, disconnected=0
            )

    # ============= ORDER EXECUTION =============

    async def execute_order(
        self,
        session_id: str,
        user_id: str,
        symbol: str,
        order_type: OrderType,
        volume: Decimal,
        sl: Optional[Decimal] = None,
        tp: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Execute MT5 order using user's allocated account.

        Args:
            session_id: Game session ID
            user_id: User ID
            symbol: Trading symbol
            order_type: BUY or SELL
            volume: Lot size
            sl: Stop loss (optional)
            tp: Take profit (optional)

        Returns:
            Order execution result with ticket or error
        """
        # Get user's allocated account
        account = await self.get_user_account(user_id)
        if not account:
            return {
                "success": False,
                "error": "No MT5 account allocated. Join game session first."
            }

        # CRITICAL FIX: Validate user is member of session
        membership_query = """
            SELECT 1
            FROM team_members tm
            JOIN teams t ON tm.team_id = t.team_id
            WHERE tm.user_id = $1 AND t.session_id = $2
        """
        is_member = await postgres_client.fetchval(membership_query, user_id, session_id)

        if not is_member:
            return {
                "success": False,
                "error": "User not a member of this session"
            }

        # Login to MT5 account (in thread pool to avoid blocking)
        login_success = await asyncio.to_thread(
            self._login_to_account,
            account.account_number,
            account.decrypted_password,
            account.broker_server
        )

        if not login_success:
            return {
                "success": False,
                "error": f"Failed to login to MT5 account {account.account_number}"
            }

        # Execute order
        result = await asyncio.to_thread(
            self._place_market_order,
            symbol,
            float(volume),
            order_type,
            float(sl) if sl else None,
            float(tp) if tp else None
        )

        # Record order in database
        await self._record_order(
            session_id=session_id,
            user_id=user_id,
            account_number=account.account_number,
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            ticket=result.get('order'),
            price=Decimal(str(result.get('price', 0))),
            sl=sl,
            tp=tp,
            retcode=result.get('retcode'),
            comment=result.get('comment'),
            status=OrderStatus.EXECUTED if result.get('retcode') == mt5.TRADE_RETCODE_DONE else OrderStatus.FAILED
        )

        return result

    def _login_to_account(self, account: int, password: str, server: str) -> bool:
        """Login to MT5 account (synchronous)."""
        try:
            if not mt5.initialize():
                logger.error("MT5 initialization failed")
                return False

            authorized = mt5.login(account, password=password, server=server)
            if not authorized:
                logger.error(f"MT5 login failed for {account}: {mt5.last_error()}")
                return False

            return True

        except Exception as e:
            logger.error(f"MT5 login exception: {e}")
            return False

    def _place_market_order(
        self,
        symbol: str,
        volume: float,
        order_type: OrderType,
        sl: Optional[float],
        tp: Optional[float]
    ) -> Dict[str, Any]:
        """Place market order (synchronous)."""
        try:
            # Get market price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {
                    "success": False,
                    "retcode": mt5.TRADE_RETCODE_INVALID,
                    "comment": f"Symbol {symbol} not found"
                }

            price = tick.ask if order_type == OrderType.BUY else tick.bid
            mt5_order_type = mt5.ORDER_TYPE_BUY if order_type == OrderType.BUY else mt5.ORDER_TYPE_SELL

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5_order_type,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "GamePad Trade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            if sl:
                request["sl"] = sl
            if tp:
                request["tp"] = tp

            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return {
                    "success": True,
                    "retcode": result.retcode,
                    "order": result.order,
                    "price": result.price,
                    "volume": result.volume,
                    "comment": result.comment
                }
            else:
                return {
                    "success": False,
                    "retcode": result.retcode,
                    "comment": result.comment
                }

        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            return {
                "success": False,
                "retcode": -1,
                "comment": str(e)
            }

    async def _record_order(
        self,
        session_id: str,
        user_id: str,
        account_number: int,
        symbol: str,
        order_type: OrderType,
        volume: Decimal,
        ticket: Optional[int],
        price: Decimal,
        sl: Optional[Decimal],
        tp: Optional[Decimal],
        retcode: int,
        comment: str,
        status: OrderStatus
    ):
        """Record order execution in database."""
        query = """
            INSERT INTO mt5_orders (
                session_id, user_id, account_number, ticket, symbol,
                order_type, volume, price, sl, tp, status, retcode, comment,
                executed_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW()
            )
        """

        try:
            await postgres_client.execute(
                query,
                session_id, user_id, account_number, ticket, symbol,
                order_type.value, volume, price, sl, tp,
                status.value, retcode, comment
            )
        except Exception as e:
            logger.error(f"Failed to record order: {e}")

    # ============= POSITION SYNCHRONIZATION =============

    async def sync_positions(self, session_id: str) -> int:
        """
        Sync all open positions from MT5 to database.

        Args:
            session_id: Game session to sync

        Returns:
            Number of positions synced
        """
        # Get all accounts allocated to this session
        query = """
            SELECT DISTINCT mp.account_number, mp.broker_server, mp.encrypted_password
            FROM mt5_account_pool mp
            JOIN teams t ON t.session_id = $1
            JOIN team_members tm ON tm.team_id = t.team_id
            WHERE mp.allocated_to_user_id = tm.user_id
              AND mp.status = 'in_use'
        """

        try:
            accounts = await postgres_client.fetch(query, session_id)

            total_synced = 0

            for account_row in accounts:
                # Login to account
                password = self._decrypt_password(account_row['encrypted_password'])
                login_success = await asyncio.to_thread(
                    self._login_to_account,
                    account_row['account_number'],
                    password,
                    account_row['broker_server']
                )

                if not login_success:
                    logger.warning(f"Failed to login for sync: {account_row['account_number']}")
                    continue

                # Get positions from MT5
                positions = await asyncio.to_thread(mt5.positions_get)

                if positions:
                    for pos in positions:
                        await self._sync_single_position(session_id, account_row['account_number'], pos)
                        total_synced += 1

            return total_synced

        except Exception as e:
            logger.error(f"Position sync failed: {e}")
            return 0

    async def _sync_single_position(self, session_id: str, account_number: int, mt5_position):
        """Sync single MT5 position to database."""
        # Check if position exists in DB
        check_query = """
            SELECT position_id FROM positions
            WHERE ticket = $1 AND session_id = $2 AND status = 'open'
        """

        existing = await postgres_client.fetchrow(check_query, mt5_position.ticket, session_id)

        if existing:
            # Update existing position (P&L)
            update_query = """
                UPDATE positions
                SET pnl = $1, updated_at = NOW()
                WHERE position_id = $2
            """
            await postgres_client.execute(update_query, Decimal(str(mt5_position.profit)), existing['position_id'])
        else:
            # Insert new position (opened outside our system or not yet recorded)
            insert_query = """
                INSERT INTO positions (
                    session_id, user_id, account_number, ticket, symbol,
                    position_type, volume, open_price, pnl, status, opened_at
                )
                SELECT $1, tm.user_id, $2, $3, $4, $5, $6, $7, $8, 'open', $9
                FROM team_members tm
                JOIN mt5_account_pool mp ON mp.allocated_to_user_id = tm.user_id
                WHERE mp.account_number = $2
                LIMIT 1
            """

            position_type = "BUY" if mt5_position.type == mt5.ORDER_TYPE_BUY else "SELL"

            await postgres_client.execute(
                insert_query,
                session_id, account_number, mt5_position.ticket, mt5_position.symbol,
                position_type, Decimal(str(mt5_position.volume)),
                Decimal(str(mt5_position.price_open)), Decimal(str(mt5_position.profit)),
                datetime.fromtimestamp(mt5_position.time)
            )


# Global singleton
mt5_integration_service = MT5IntegrationService()
