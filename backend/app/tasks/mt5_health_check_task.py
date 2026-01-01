"""Background task to monitor MT5 account pool health - Phase 02"""
import asyncio
import logging
from datetime import datetime
import MetaTrader5 as mt5
from app.services.mt5_integration_service import mt5_integration_service
from app.database.postgres_client import postgres_client
from app.models.mt5_models import HealthStatus

logger = logging.getLogger(__name__)


class MT5HealthCheckTask:
    """Monitor MT5 account pool health every 10 seconds."""

    def __init__(self, interval: int = 10):
        self.interval = interval
        self.running = False
        self.task = None

    async def start(self):
        """Start background health check loop."""
        self.running = True
        logger.info(f"MT5 health check task started (interval: {self.interval}s)")

        while self.running:
            try:
                await self._check_all_accounts()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                await asyncio.sleep(self.interval)

    async def stop(self):
        """Stop background health check."""
        self.running = False
        logger.info("MT5 health check task stopped")

    async def _check_all_accounts(self):
        """Check health of all accounts in pool."""
        # Get all accounts (both available and in_use)
        query = """
            SELECT account_number, broker_server, encrypted_password, status
            FROM mt5_account_pool
            WHERE status != 'expired'
        """

        try:
            accounts = await postgres_client.fetch(query)

            if not accounts:
                return

            healthy_count = 0
            unhealthy_count = 0

            for account_row in accounts:
                is_healthy = await self._check_single_account(
                    account_row['account_number'],
                    account_row['broker_server'],
                    account_row['encrypted_password']
                )

                if is_healthy:
                    healthy_count += 1
                else:
                    unhealthy_count += 1

            logger.debug(f"Health check: {healthy_count} healthy, {unhealthy_count} unhealthy")

        except Exception as e:
            logger.error(f"Failed to check all accounts: {e}")

    async def _check_single_account(
        self,
        account_number: int,
        broker_server: str,
        encrypted_password: str
    ) -> bool:
        """
        Check health of single MT5 account.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Decrypt password
            password = mt5_integration_service._decrypt_password(encrypted_password)

            # Attempt login in thread pool
            login_success = await asyncio.to_thread(
                self._test_login,
                account_number,
                password,
                broker_server
            )

            # Update health status in database
            health_status = HealthStatus.HEALTHY if login_success else HealthStatus.DISCONNECTED

            update_query = """
                UPDATE mt5_account_pool
                SET health_status = $1,
                    last_health_check = NOW()
                WHERE account_number = $2
            """

            await postgres_client.execute(update_query, health_status.value, account_number)

            if not login_success:
                logger.warning(f"Account {account_number} unhealthy: login failed")

            return login_success

        except Exception as e:
            logger.error(f"Health check failed for account {account_number}: {e}")

            # Mark as unhealthy
            update_query = """
                UPDATE mt5_account_pool
                SET health_status = $1,
                    last_health_check = NOW()
                WHERE account_number = $2
            """

            await postgres_client.execute(
                update_query,
                HealthStatus.UNHEALTHY.value,
                account_number
            )

            return False

    def _test_login(self, account: int, password: str, server: str) -> bool:
        """Test MT5 account login (synchronous)."""
        try:
            if not mt5.initialize():
                return False

            authorized = mt5.login(account, password=password, server=server)

            if authorized:
                # Check terminal connection status
                term_info = mt5.terminal_info()
                if term_info and term_info.connected:
                    return True

            return False

        except Exception as e:
            logger.error(f"Login test exception for {account}: {e}")
            return False
        finally:
            # CRITICAL FIX: Always shutdown to prevent resource leak
            mt5.shutdown()


# Global instance
mt5_health_check_task = MT5HealthCheckTask()
