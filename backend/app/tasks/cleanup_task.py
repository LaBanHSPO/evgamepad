
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class CleanupTask:
    """Background task for periodic cleanup"""

    def __init__(self, reconnection_manager, interval: int = 60):
        """
        Initialize cleanup task

        Args:
            reconnection_manager: ReconnectionManager instance
            interval: Cleanup interval in seconds
        """
        self.reconnection_manager = reconnection_manager
        self.interval = interval
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def run(self):
        """Run cleanup loop"""
        self.running = True
        logger.info(f"Cleanup task started (interval: {self.interval}s)")

        while self.running:
            try:
                await asyncio.sleep(self.interval)

                # Cleanup expired sessions
                expired_count = self.reconnection_manager.cleanup_expired_sessions()
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions")

            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.exception("Error in cleanup task")

    def start(self):
        """Start cleanup task"""
        if not self.task:
            self.task = asyncio.create_task(self.run())
            logger.info("Cleanup task scheduled")

    async def stop(self):
        """Stop cleanup task"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            logger.info("Cleanup task stopped")
