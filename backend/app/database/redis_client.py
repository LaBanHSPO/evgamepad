"""
Redis cache client for technical indicators.
Implements get/set with automatic serialization and TTL.
"""
import json
import logging
from typing import Optional, Any, Dict
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisClient:
    """Async Redis client wrapper for indicator caching."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> bool:
        """Initialize Redis connection pool."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            await self._client.ping()
            logger.info(f"Redis connected: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False

    async def disconnect(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis disconnected")

    async def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        Get cached indicators for symbol/timeframe.
        Returns None if cache miss.
        """
        if not self._client:
            return None

        key = f"indicators:{symbol}:{timeframe}"
        try:
            data = await self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Redis GET failed: {e}")
            return None

    async def set_indicators(
        self,
        symbol: str,
        timeframe: str,
        data: Dict[str, Any],
        ttl: int = 60  # 1 minute (adjusted from 5min)
    ) -> bool:
        """
        Cache indicators for symbol/timeframe.
        TTL in seconds (default 1 min per validation adjustment).
        """
        if not self._client:
            return False

        key = f"indicators:{symbol}:{timeframe}"
        try:
            await self._client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")
            return False

    async def is_connected(self) -> bool:
        """Check Redis connection health."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    # ==================== Sorted Set Operations (Phase 01 - Leaderboard) ====================

    async def zadd(self, key: str, mapping: Dict[str, float]):
        """Add members to sorted set."""
        if not self._client:
            return 0
        return await self._client.zadd(key, mapping)

    async def zrevrange(
        self,
        key: str,
        start: int,
        stop: int,
        withscores: bool = False
    ):
        """Get members by reverse rank (highest first)."""
        if not self._client:
            return []
        return await self._client.zrevrange(key, start, stop, withscores=withscores)

    async def zrevrank(self, key: str, member: str) -> Optional[int]:
        """Get reverse rank of member (0 = highest)."""
        if not self._client:
            return None
        return await self._client.zrevrank(key, member)

    async def zscore(self, key: str, member: str) -> Optional[float]:
        """Get score of member."""
        if not self._client:
            return None
        return await self._client.zscore(key, member)

    async def zcard(self, key: str) -> int:
        """Get total number of members in sorted set."""
        if not self._client:
            return 0
        return await self._client.zcard(key)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set TTL on key."""
        if not self._client:
            return False
        return await self._client.expire(key, seconds)

    async def delete(self, key: str) -> int:
        """Delete key."""
        if not self._client:
            return 0
        return await self._client.delete(key)
    async def get_portfolio_analysis(self, cache_key: str) -> Optional[Dict]:
        """Get cached portfolio analysis."""
        if not self._client:
            return None

        try:
            data = await self._client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning(f"Portfolio analysis cache get failed: {e}")
            return None

    async def set_portfolio_analysis(
        self,
        cache_key: str,
        data: Dict,
        ttl: int = 300
    ) -> bool:
        """Cache portfolio analysis for 5 minutes."""
        if not self._client:
            return False

        try:
            await self._client.setex(cache_key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.warning(f"Portfolio analysis cache set failed: {e}")
            return False
