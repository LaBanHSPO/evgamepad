"""Game session lifecycle management."""
import logging
from typing import Optional
from app.database.postgres_client import postgres_client
from app.models.game_models import GameSession
from app.services.mt5_integration_service import mt5_integration_service

logger = logging.getLogger(__name__)


class GameService:
    """Manage game session lifecycle."""

    async def create_session(
        self,
        name: str,
        creator_id: str,
        max_team_size: int = 6
    ) -> GameSession:
        """
        Create new game session.

        Args:
            name: Unique session name
            creator_id: User creating the session
            max_team_size: Maximum members per team (default 6)

        Returns:
            GameSession model

        Raises:
            Exception if name already exists
        """
        # Check name uniqueness
        existing = await postgres_client.fetchval(
            "SELECT COUNT(*) FROM game_sessions WHERE name = $1", name
        )

        if existing > 0:
            raise Exception(f"Session '{name}' already exists")

        # Create session
        row = await postgres_client.fetchrow("""
            INSERT INTO game_sessions (name, creator_id, max_team_size, status)
            VALUES ($1, $2, $3, 'waiting')
            RETURNING session_id, name, creator_id, status, start_time,
                      end_time, max_team_size, created_at
        """, name, creator_id, max_team_size)

        session = GameSession(**dict(row))
        logger.info(f"Created session '{name}' by {creator_id}")

        return session

    async def join_session(
        self,
        name: str,
        user_id: str,
        username: str
    ) -> dict:
        """
        Join existing game session.

        Args:
            name: Session name to join
            user_id: User joining
            username: Display username

        Returns:
            {"session": GameSession, "team": Team}

        Raises:
            Exception if session not found, full, or completed
        """
        # Get session
        session_row = await postgres_client.fetchrow(
            "SELECT * FROM game_sessions WHERE name = $1", name
        )

        if not session_row:
            raise Exception(f"Session '{name}' not found")

        session = GameSession(**dict(session_row))

        if session.status == "completed":
            raise Exception(f"Session '{name}' is completed")

        # Check if user already in session
        existing_membership = await postgres_client.fetchval("""
            SELECT COUNT(*) FROM team_members tm
            JOIN teams t ON tm.team_id = t.team_id
            WHERE t.session_id = $1 AND tm.user_id = $2
        """, session.session_id, user_id)

        if existing_membership > 0:
            raise Exception("You are already in this session")

        # Auto-assign to team
        from app.services.team_service import team_service
        team = await team_service.auto_assign_team(
            session.session_id,
            user_id,
            username,
            session.max_team_size
        )

        # Allocate MT5 account
        allocation = await mt5_integration_service.allocate_account(
            user_id,
            session.session_id
        )

        if not allocation:
            logger.warning(
                f"User {user_id} joined session '{name}' but account pool exhausted"
            )

        # Check if we should start session (min 4 players)
        await self._check_start_session(session.session_id)

        logger.info(
            f"User {user_id} joined session '{name}', team '{team.team_name}'"
        )

        return {
            "session": session,
            "team": team,
            "account_allocated": allocation is not None
        }

    async def leave_session(self, user_id: str):
        """
        Leave current game session.

        Args:
            user_id: User leaving the session
        """
        # Find user's current session
        session_id = await postgres_client.fetchval("""
            SELECT t.session_id FROM team_members tm
            JOIN teams t ON tm.team_id = t.team_id
            JOIN game_sessions gs ON t.session_id = gs.session_id
            WHERE tm.user_id = $1 AND gs.status != 'completed'
        """, user_id)

        if not session_id:
            return

        # Release MT5 account
        await mt5_integration_service.release_account(user_id)

        # Remove from team
        await postgres_client.execute(
            "DELETE FROM team_members WHERE user_id = $1", user_id
        )

        logger.info(f"User {user_id} left session {session_id}")

    async def get_session_by_name(self, name: str) -> Optional[GameSession]:
        """
        Get session by name.

        Args:
            name: Session name

        Returns:
            GameSession model or None if not found
        """
        row = await postgres_client.fetchrow(
            "SELECT * FROM game_sessions WHERE name = $1", name
        )
        return GameSession(**dict(row)) if row else None

    async def complete_session(self, session_id: str):
        """
        Mark session as completed.

        Args:
            session_id: Session to complete
        """
        await postgres_client.execute("""
            UPDATE game_sessions
            SET status = 'completed', end_time = NOW()
            WHERE session_id = $1
        """, session_id)

        logger.info(f"Session {session_id} completed")

    async def _check_start_session(self, session_id: str):
        """
        Start session if minimum players reached (4).

        Args:
            session_id: Session to check
        """
        player_count = await postgres_client.fetchval("""
            SELECT COUNT(DISTINCT tm.user_id)
            FROM team_members tm
            JOIN teams t ON tm.team_id = t.team_id
            WHERE t.session_id = $1
        """, session_id)

        if player_count >= 4:
            # Start session
            await postgres_client.execute("""
                UPDATE game_sessions
                SET status = 'active', start_time = NOW()
                WHERE session_id = $1 AND status = 'waiting'
            """, session_id)

            logger.info(
                f"Session {session_id} started with {player_count} players"
            )

            # Broadcast session start
            from app.events.game_events import broadcast_session_start
            await broadcast_session_start(session_id)


# Global instance
game_service = GameService()
