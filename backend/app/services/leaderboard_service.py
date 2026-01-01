"""Real-time leaderboard service with three-tier caching."""
import logging
from typing import List, Optional, Dict
from decimal import Decimal
from app.database.redis_client import RedisClient
from app.database.postgres_client import postgres_client
from app.models.game_models import LeaderboardEntry, LeaderboardResponse

logger = logging.getLogger(__name__)

class LeaderboardService:
    """Three-tier leaderboard: Redis → Materialized View → Direct Query."""

    def __init__(self, redis_client: Optional[RedisClient] = None):
        self.redis_client = redis_client

    async def update_team_score(
        self,
        session_id: str,
        team_id: str,
        pnl: Decimal
    ):
        """
        Update team score in Redis leaderboard.
        O(log n) complexity via sorted set.
        """
        if not self.redis_client:
            logger.warning("Redis not available, skipping leaderboard update")
            return

        key = f"leaderboard:{session_id}"

        # Update Redis sorted set (Tier 1)
        await self.redis_client.zadd(key, {team_id: float(pnl)})
        await self.redis_client.expire(key, 3600)  # 1 hour TTL

        logger.debug(f"Updated leaderboard for session {session_id}, team {team_id}: {pnl}")

    async def get_leaderboard(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[LeaderboardEntry]:
        """
        Get top N teams with ranks.
        Tier 1 (Redis) → Tier 2 (Mat View) → Tier 3 (Direct)
        """
        # Tier 1: Try Redis (fastest)
        rankings = await self._get_from_redis(session_id, limit)
        if rankings:
            return rankings

        # Tier 2: Materialized View (fallback)
        try:
            rankings = await self._get_from_materialized_view(session_id, limit)
            if rankings:
                # Warm Redis cache
                await self._warm_redis_cache(session_id, rankings)
                return rankings
        except Exception as e:
            logger.warning(f"Materialized view failed: {e}")

        # Tier 3: Direct Query (guaranteed fresh)
        return await self._get_from_direct_query(session_id, limit)

    async def get_my_rank(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[LeaderboardEntry]:
        """Get my team's rank in session."""
        # Find my team
        team_id = await self._get_user_team(session_id, user_id)
        if not team_id:
            return None

        # Get rank from Redis
        if self.redis_client:
            key = f"leaderboard:{session_id}"
            rank = await self.redis_client.zrevrank(key, team_id)
            score = await self.redis_client.zscore(key, team_id)

            if rank is not None and score is not None:
                # Get team name
                team_name = await self._get_team_name(team_id)
                team_size = await self._get_team_size(team_id)

                return LeaderboardEntry(
                    rank=rank + 1,  # 0-indexed → 1-indexed
                    team_id=team_id,
                    team_name=team_name,
                    total_pnl=Decimal(str(score)),
                    team_size=team_size
                )

        # Fallback to DB
        return await self._get_rank_from_db(session_id, team_id)

    async def get_total_teams(self, session_id: str) -> int:
        """Get total number of teams in session."""
        if self.redis_client:
            key = f"leaderboard:{session_id}"
            count = await self.redis_client.zcard(key)
            if count > 0:
                return count

        # Fallback to DB
        query = "SELECT COUNT(*) FROM teams WHERE session_id = $1"
        return await postgres_client.fetchval(query, session_id) or 0

    # ==================== Tier 1: Redis ====================

    async def _get_from_redis(
        self,
        session_id: str,
        limit: int
    ) -> Optional[List[LeaderboardEntry]]:
        """Tier 1: Get leaderboard from Redis sorted set."""
        if not self.redis_client:
            return None

        key = f"leaderboard:{session_id}"

        # Get top N teams with scores
        rankings = await self.redis_client.zrevrange(
            key, 0, limit - 1, withscores=True
        )

        if not rankings:
            logger.debug(f"Redis cache miss for session {session_id}")
            return None

        # Convert to LeaderboardEntry
        entries = []
        for idx, (team_id, score) in enumerate(rankings):
            team_name = await self._get_team_name(team_id)
            team_size = await self._get_team_size(team_id)

            entries.append(LeaderboardEntry(
                rank=idx + 1,
                team_id=team_id,
                team_name=team_name,
                total_pnl=Decimal(str(score)),
                team_size=team_size
            ))

        logger.debug(f"Redis cache hit for session {session_id}")
        return entries

    # ==================== Tier 2: Materialized View ====================

    async def _get_from_materialized_view(
        self,
        session_id: str,
        limit: int
    ) -> Optional[List[LeaderboardEntry]]:
        """Tier 2: Get leaderboard from materialized view."""
        query = """
            SELECT team_id, team_name, total_pnl, team_size
            FROM team_leaderboard
            WHERE session_id = $1
            ORDER BY total_pnl DESC
            LIMIT $2
        """

        rows = await postgres_client.fetch(query, session_id, limit)

        if not rows:
            return None

        entries = [
            LeaderboardEntry(
                rank=idx + 1,
                team_id=str(row["team_id"]),
                team_name=row["team_name"],
                total_pnl=row["total_pnl"],
                team_size=row["team_size"]
            )
            for idx, row in enumerate(rows)
        ]

        logger.debug(f"Materialized view hit for session {session_id}")
        return entries

    # ==================== Tier 3: Direct Query ====================

    async def _get_from_direct_query(
        self,
        session_id: str,
        limit: int
    ) -> List[LeaderboardEntry]:
        """Tier 3: Direct query (guaranteed fresh, slowest)."""
        query = """
            SELECT
                t.team_id,
                t.team_name,
                COALESCE(SUM(p.pnl), 0) as total_pnl,
                COUNT(DISTINCT tm.user_id) as team_size
            FROM teams t
            JOIN team_members tm ON t.team_id = tm.team_id
            LEFT JOIN positions p ON tm.user_id = p.user_id
                AND p.session_id = t.session_id
                AND p.closed_at IS NULL
            WHERE t.session_id = $1
            GROUP BY t.team_id, t.team_name
            ORDER BY total_pnl DESC
            LIMIT $2
        """

        rows = await postgres_client.fetch(query, session_id, limit)

        entries = [
            LeaderboardEntry(
                rank=idx + 1,
                team_id=str(row["team_id"]),
                team_name=row["team_name"],
                total_pnl=row["total_pnl"],
                team_size=row["team_size"]
            )
            for idx, row in enumerate(rows)
        ]

        logger.debug(f"Direct query for session {session_id}")
        return entries

    # ==================== Helper Methods ====================

    async def _get_user_team(self, session_id: str, user_id: str) -> Optional[str]:
        """Find which team the user belongs to."""
        query = """
            SELECT tm.team_id
            FROM team_members tm
            JOIN teams t ON tm.team_id = t.team_id
            WHERE t.session_id = $1 AND tm.user_id = $2
        """
        row = await postgres_client.fetchrow(query, session_id, user_id)
        return str(row["team_id"]) if row else None

    async def _get_team_name(self, team_id: str) -> str:
        """Get team name from database."""
        query = "SELECT team_name FROM teams WHERE team_id = $1"
        row = await postgres_client.fetchrow(query, team_id)
        return row["team_name"] if row else "Unknown Team"

    async def _get_team_size(self, team_id: str) -> int:
        """Get team member count."""
        query = "SELECT COUNT(*) FROM team_members WHERE team_id = $1"
        count = await postgres_client.fetchval(query, team_id)
        return count or 0

    async def _warm_redis_cache(
        self,
        session_id: str,
        entries: List[LeaderboardEntry]
    ):
        """Warm Redis cache from DB results."""
        if not self.redis_client:
            return

        key = f"leaderboard:{session_id}"

        # Build score mapping
        mapping = {entry.team_id: float(entry.total_pnl) for entry in entries}

        # Bulk update Redis
        if mapping:
            await self.redis_client.zadd(key, mapping)
            await self.redis_client.expire(key, 3600)
            logger.debug(f"Warmed Redis cache for session {session_id}")

    async def _get_rank_from_db(
        self,
        session_id: str,
        team_id: str
    ) -> Optional[LeaderboardEntry]:
        """Get rank from DB when Redis unavailable."""
        query = """
            WITH ranked_teams AS (
                SELECT
                    team_id,
                    team_name,
                    total_pnl,
                    team_size,
                    ROW_NUMBER() OVER (ORDER BY total_pnl DESC) as rank
                FROM team_leaderboard
                WHERE session_id = $1
            )
            SELECT * FROM ranked_teams WHERE team_id = $2
        """
        row = await postgres_client.fetchrow(query, session_id, team_id)

        if not row:
            return None

        return LeaderboardEntry(
            rank=row["rank"],
            team_id=str(row["team_id"]),
            team_name=row["team_name"],
            total_pnl=row["total_pnl"],
            team_size=row["team_size"]
        )

# Global instance
leaderboard_service = LeaderboardService()
