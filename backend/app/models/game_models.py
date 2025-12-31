"""Game session and leaderboard data models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class GameSession(BaseModel):
    """Game session model."""
    session_id: str
    name: str
    creator_id: str
    status: str  # waiting, active, completed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_team_size: int = 6
    created_at: datetime

class Team(BaseModel):
    """Team model."""
    team_id: str
    session_id: str
    team_name: str
    total_pnl: Decimal = Decimal("0")
    created_at: datetime

class TeamMember(BaseModel):
    """Team member model."""
    member_id: str
    team_id: str
    user_id: str
    username: str
    joined_at: datetime

class LeaderboardEntry(BaseModel):
    """Leaderboard entry model."""
    rank: int
    team_id: str
    team_name: str
    total_pnl: Decimal
    team_size: int

class LeaderboardResponse(BaseModel):
    """Response for /top command."""
    rankings: List[LeaderboardEntry]
    my_rank: Optional[LeaderboardEntry] = None
    total_teams: int
