"""Background task to sync MT5 positions - Phase 02"""
import asyncio
import logging
from app.services.mt5_integration_service import mt5_integration_service
from app.database.postgres_client import postgres_client

logger = logging.getLogger(__name__)


class MT5PositionSyncTask:
    """Sync MT5 positions to database every 5 seconds."""

    def __init__(self, interval: int = 5):
        self.interval = interval
        self.running = False
        self.task = None

    async def start(self):
        """Start background position sync loop."""
        self.running = True
        logger.info(f"MT5 position sync task started (interval: {self.interval}s)")

        while self.running:
            try:
                await self._sync_all_active_sessions()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Position sync failed: {e}")
                await asyncio.sleep(self.interval)

    async def stop(self):
        """Stop background sync."""
        self.running = False
        logger.info("MT5 position sync task stopped")

    async def _sync_all_active_sessions(self):
        """Sync positions for all active game sessions."""
        # Get all active sessions
        query = """
            SELECT session_id
            FROM game_sessions
            WHERE status = 'active'
        """

        try:
            sessions = await postgres_client.fetch(query)

            if not sessions:
                return

            # Sync each session
            total_synced = 0
            for session_row in sessions:
                session_id = session_row['session_id']
                count = await mt5_integration_service.sync_positions(session_id)
                total_synced += count

            if total_synced > 0:
                logger.debug(f"Synced {total_synced} positions across {len(sessions)} sessions")

        except Exception as e:
            logger.error(f"Failed to sync active sessions: {e}")


# Global instance
mt5_position_sync_task = MT5PositionSyncTask()
