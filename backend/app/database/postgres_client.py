"""PostgreSQL connection pool and query helpers."""
import asyncpg
from typing import Optional, List, Dict, Any
import logging
from app.config import config

logger = logging.getLogger(__name__)

class PostgresClient:
    """Async PostgreSQL client with connection pooling."""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Create connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=config.POSTGRES_HOST,
                port=config.POSTGRES_PORT,
                database=config.POSTGRES_DB,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD,
                min_size=5,
                max_size=20,
                command_timeout=60,
            )
            logger.info("PostgreSQL pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise

    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL pool closed")

    async def execute(self, query: str, *args) -> str:
        """Execute query without returning results."""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch single row."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

# Global instance
postgres_client = PostgresClient()
