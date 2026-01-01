"""Team formation and scoring."""
import logging
from typing import List
from decimal import Decimal
from app.database.postgres_client import postgres_client
from app.models.game_models import Team, TeamMember

logger = logging.getLogger(__name__)


class TeamService:
    """Team formation and scoring logic."""

    async def auto_assign_team(
        self,
        session_id: str,
        user_id: str,
        username: str,
        max_team_size: int
    ) -> Team:
        """
        Auto-assign user to team using round-robin.

        Strategy:
        1. Find team with fewest members
        2. If team_size < max, add to that team
        3. Else, create new team

        Args:
            session_id: Game session ID
            user_id: User to assign
            username: Display username
            max_team_size: Maximum members per team

        Returns:
            Team model
        """
        # Find team with fewest members
        team_row = await postgres_client.fetchrow("""
            SELECT t.team_id, t.team_name, COUNT(tm.member_id) as member_count
            FROM teams t
            LEFT JOIN team_members tm ON t.team_id = tm.team_id
            WHERE t.session_id = $1
            GROUP BY t.team_id, t.team_name
            ORDER BY member_count ASC, t.created_at ASC
            LIMIT 1
        """, session_id)

        if team_row and team_row["member_count"] < max_team_size:
            # Add to existing team
            team_id = team_row["team_id"]
            team_name = team_row["team_name"]
        else:
            # Create new team
            team_count = await postgres_client.fetchval(
                "SELECT COUNT(*) FROM teams WHERE session_id = $1", session_id
            )

            # Get session name for team naming
            session_name = await postgres_client.fetchval(
                "SELECT name FROM game_sessions WHERE session_id = $1",
                session_id
            )

            # Team name = ServerName-A, ServerName-B, ...
            team_suffix = chr(65 + team_count)  # A, B, C...
            team_name = f"{session_name}-{team_suffix}"

            team_row = await postgres_client.fetchrow("""
                INSERT INTO teams (session_id, team_name)
                VALUES ($1, $2)
                RETURNING team_id, team_name, created_at
            """, session_id, team_name)

            team_id = team_row["team_id"]
            team_name = team_row["team_name"]

        # Add user to team
        await postgres_client.execute("""
            INSERT INTO team_members (team_id, user_id, username)
            VALUES ($1, $2, $3)
        """, team_id, user_id, username)

        logger.info(
            f"Assigned {username} to {team_name} in session {session_id}"
        )

        return Team(
            team_id=str(team_id),
            session_id=session_id,
            team_name=team_name,
            total_pnl=Decimal("0"),
            created_at=team_row.get("created_at")
        )

    async def calculate_team_pnl(self, team_id: str) -> Decimal:
        """
        Calculate total P&L for team.

        Args:
            team_id: Team to calculate P&L for

        Returns:
            Total P&L as Decimal
        """
        total = await postgres_client.fetchval("""
            SELECT COALESCE(SUM(p.pnl), 0)
            FROM positions p
            JOIN team_members tm ON p.user_id = tm.user_id
            WHERE tm.team_id = $1 AND p.closed_at IS NULL
        """, team_id)

        return Decimal(str(total))

    async def get_team_members(self, team_id: str) -> List[TeamMember]:
        """
        Get all team members.

        Args:
            team_id: Team to get members for

        Returns:
            List of TeamMember models
        """
        rows = await postgres_client.fetch(
            "SELECT * FROM team_members WHERE team_id = $1", team_id
        )
        return [TeamMember(**dict(row)) for row in rows]


# Global instance
team_service = TeamService()
