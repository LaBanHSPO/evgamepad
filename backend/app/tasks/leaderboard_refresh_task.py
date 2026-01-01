"""Background task to refresh materialized view."""
import asyncio
import logging
from app.database.postgres_client import postgres_client

logger = logging.getLogger(__name__)

class LeaderboardRefreshTask:
    """Refresh materialized view every 30 seconds."""

    def __init__(self, interval: int = 30):
        self.interval = interval
        self.running = False
        self.task = None

    async def start(self):
        """Start background refresh loop."""
        self.running = True
        logger.info("Leaderboard refresh task started")

        while self.running:
            try:
                await self._refresh_view()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Leaderboard refresh failed: {e}")
                await asyncio.sleep(self.interval)

    async def stop(self):
        """Stop background refresh."""
        self.running = False
        logger.info("Leaderboard refresh task stopped")

    async def _refresh_view(self):
        """Refresh materialized view concurrently."""
        query = "REFRESH MATERIALIZED VIEW CONCURRENTLY team_leaderboard"
        await postgres_client.execute(query)
        logger.debug("Materialized view refreshed")

# Global instance
leaderboard_refresh_task = LeaderboardRefreshTask()
