"""Integration tests for leaderboard flow."""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from app.processors.command_processor import CommandProcessor
from app.mt5.connection_manager import MT5ConnectionManager

@pytest.fixture
def mock_mt5_manager():
    """Create mock MT5 manager."""
    manager = MagicMock(spec=MT5ConnectionManager)
    manager.is_connected.return_value = True
    return manager

@pytest.fixture
def command_processor(mock_mt5_manager):
    """Create command processor."""
    return CommandProcessor(mock_mt5_manager)

@pytest.mark.asyncio
async def test_top_command_flow(command_processor):
    """Test complete /top command flow."""
    sid = "test-socket-id"
    user_id = "test-user-1"
    session_id = "test-session-1"

    with patch('app.services.leaderboard_service.leaderboard_service') as mock_service:
        # Mock leaderboard service responses
        from app.models.game_models import LeaderboardEntry

        mock_rankings = [
            LeaderboardEntry(
                rank=1,
                team_id="team-1",
                team_name="Team Alpha",
                total_pnl=Decimal("2500.00"),
                team_size=3
            ),
            LeaderboardEntry(
                rank=2,
                team_id="team-2",
                team_name="Team Beta",
                total_pnl=Decimal("1500.00"),
                team_size=2
            )
        ]

        mock_my_rank = LeaderboardEntry(
            rank=2,
            team_id="team-2",
            team_name="Team Beta",
            total_pnl=Decimal("1500.00"),
            team_size=2
        )

        mock_service.get_leaderboard = AsyncMock(return_value=mock_rankings)
        mock_service.get_my_rank = AsyncMock(return_value=mock_my_rank)

        # Execute /top command
        result = await command_processor.process_top_command(sid, user_id, session_id, limit=10)

        assert result['success'] is True
        result_data = result.get('data', result)
        assert result_data['type'] == 'leaderboard'
        assert len(result_data['rankings']) == 2
        assert result_data['my_rank'] is not None
        assert "🥇" in result_data['message']  # Gold medal for #1

@pytest.mark.asyncio
async def test_top_command_limit_clamping(command_processor):
    """Test /top command limit clamping (1-50)."""
    sid = "test-socket-id"
    user_id = "test-user-1"
    session_id = "test-session-1"

    with patch('app.services.leaderboard_service.leaderboard_service') as mock_service:
        mock_service.get_leaderboard = AsyncMock(return_value=[])
        mock_service.get_my_rank = AsyncMock(return_value=None)

        # Test limit too low
        result = await command_processor.process_top_command(sid, user_id, session_id, limit=0)
        assert mock_service.get_leaderboard.call_args[0][1] == 1  # Clamped to 1

        # Test limit too high
        result = await command_processor.process_top_command(sid, user_id, session_id, limit=100)
        assert mock_service.get_leaderboard.call_args[0][1] == 50  # Clamped to 50

@pytest.mark.asyncio
async def test_top_command_no_my_rank(command_processor):
    """Test /top command when user has no team."""
    sid = "test-socket-id"
    user_id = "test-user-orphan"
    session_id = "test-session-1"

    with patch('app.services.leaderboard_service.leaderboard_service') as mock_service:
        from app.models.game_models import LeaderboardEntry

        mock_rankings = [
            LeaderboardEntry(
                rank=1,
                team_id="team-1",
                team_name="Team Alpha",
                total_pnl=Decimal("2500.00"),
                team_size=3
            )
        ]

        mock_service.get_leaderboard = AsyncMock(return_value=mock_rankings)
        mock_service.get_my_rank = AsyncMock(return_value=None)  # No team

        result = await command_processor.process_top_command(sid, user_id, session_id, limit=10)

        assert result['success'] is True
        result_data = result.get('data', result)
        assert result_data['my_rank'] is None
        assert "Your Team" not in result_data['message']  # Should not show my rank
