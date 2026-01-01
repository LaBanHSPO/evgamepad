"""Integration tests for game session flow (Phase 03)."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.game_service import game_service
from app.services.team_service import team_service
from app.processors.command_processor import CommandProcessor


@pytest.mark.asyncio
class TestGameSessionFlow:
    """Test complete session creation and join flow."""

    @pytest.fixture
    def mock_postgres(self):
        """Mock PostgreSQL client."""
        with patch('app.services.game_service.postgres_client') as mock_pg:
            yield mock_pg

    @pytest.fixture
    def mock_mt5_service(self):
        """Mock MT5 integration service."""
        with patch('app.services.game_service.mt5_integration_service') as mock_mt5:
            mock_mt5.allocate_account = AsyncMock(return_value=MagicMock(
                account_number=12345,
                broker_server="BrokerDemo"
            ))
            mock_mt5.release_account = AsyncMock(return_value=True)
            yield mock_mt5

    @pytest.mark.asyncio
    async def test_create_session_success(self, mock_postgres):
        """Test successful session creation."""
        # Mock database response
        mock_postgres.fetchval.return_value = 0  # No existing session
        mock_postgres.fetchrow.return_value = {
            'session_id': 'test-session-id',
            'name': 'TestServer',
            'creator_id': 'user-1',
            'status': 'waiting',
            'start_time': None,
            'end_time': None,
            'max_team_size': 6,
            'created_at': '2025-12-31T00:00:00'
        }

        # Create session
        session = await game_service.create_session('TestServer', 'user-1')

        assert session.name == 'TestServer'
        assert session.status == 'waiting'
        assert session.creator_id == 'user-1'

    @pytest.mark.asyncio
    async def test_create_session_duplicate_name(self, mock_postgres):
        """Test session creation with duplicate name."""
        # Mock existing session
        mock_postgres.fetchval.return_value = 1

        # Should raise exception
        with pytest.raises(Exception, match="already exists"):
            await game_service.create_session('TestServer', 'user-1')

    @pytest.mark.asyncio
    async def test_join_session_success(self, mock_postgres, mock_mt5_service):
        """Test successful session join."""
        # Mock session lookup
        mock_postgres.fetchrow.side_effect = [
            {  # Session row
                'session_id': 'test-session-id',
                'name': 'TestServer',
                'creator_id': 'user-1',
                'status': 'waiting',
                'start_time': None,
                'end_time': None,
                'max_team_size': 6,
                'created_at': '2025-12-31T00:00:00'
            },
            {  # Team row for auto-assign
                'team_id': 'test-team-id',
                'team_name': 'TestServer-A',
                'member_count': 0,
                'created_at': '2025-12-31T00:00:00'
            }
        ]
        mock_postgres.fetchval.side_effect = [0, 2]  # Not in session, player count

        # Mock team service
        with patch('app.services.team_service.postgres_client', mock_postgres):
            result = await game_service.join_session(
                'TestServer', 'user-2', 'User2'
            )

        assert result['session'].name == 'TestServer'
        assert result['account_allocated'] is True

    @pytest.mark.asyncio
    async def test_join_session_already_joined(self, mock_postgres):
        """Test joining session when already a member."""
        # Mock session lookup
        mock_postgres.fetchrow.return_value = {
            'session_id': 'test-session-id',
            'name': 'TestServer',
            'status': 'waiting',
            'max_team_size': 6,
            'creator_id': 'user-1',
            'start_time': None,
            'end_time': None,
            'created_at': '2025-12-31T00:00:00'
        }
        mock_postgres.fetchval.return_value = 1  # Already in session

        # Should raise exception
        with pytest.raises(Exception, match="already in this session"):
            await game_service.join_session(
                'TestServer', 'user-2', 'User2'
            )

    @pytest.mark.asyncio
    async def test_auto_start_at_4_players(self, mock_postgres, mock_mt5_service):
        """Test session auto-starts at 4 players."""
        # Mock session
        mock_postgres.fetchrow.return_value = {
            'session_id': 'test-session-id',
            'name': 'TestServer',
            'creator_id': 'user-1',
            'status': 'waiting',
            'start_time': None,
            'end_time': None,
            'max_team_size': 6,
            'created_at': '2025-12-31T00:00:00'
        }
        mock_postgres.fetchval.side_effect = [0, 4]  # Not in session, 4 players

        # Mock broadcast
        with patch('app.events.game_events.broadcast_session_start') as mock_broadcast:
            mock_broadcast.return_value = AsyncMock()

            # Join should trigger auto-start
            await game_service.join_session(
                'TestServer', 'user-4', 'User4'
            )

            # Verify status updated to active
            assert mock_postgres.execute.called

    @pytest.mark.asyncio
    async def test_team_auto_assignment_round_robin(self, mock_postgres):
        """Test team auto-assignment uses round-robin."""
        # Mock: Team A has 5 members (almost full)
        mock_postgres.fetchrow.return_value = {
            'team_id': 'team-a-id',
            'team_name': 'TestServer-A',
            'member_count': 5,
            'created_at': '2025-12-31T00:00:00'
        }

        # Should add to Team A (not full yet)
        team = await team_service.auto_assign_team(
            'test-session-id', 'user-6', 'User6', max_team_size=6
        )

        assert team.team_name == 'TestServer-A'

    @pytest.mark.asyncio
    async def test_team_auto_assignment_create_new_team(self, mock_postgres):
        """Test team auto-assignment creates new team when full."""
        # Mock: Team A is full (6 members)
        mock_postgres.fetchrow.side_effect = [
            {  # First team (full)
                'team_id': 'team-a-id',
                'team_name': 'TestServer-A',
                'member_count': 6,
                'created_at': '2025-12-31T00:00:00'
            },
            {  # New team creation
                'team_id': 'team-b-id',
                'team_name': 'TestServer-B',
                'created_at': '2025-12-31T00:00:00'
            }
        ]
        mock_postgres.fetchval.side_effect = [1, 'TestServer']  # 1 existing team

        # Should create Team B
        team = await team_service.auto_assign_team(
            'test-session-id', 'user-7', 'User7', max_team_size=6
        )

        assert team.team_name == 'TestServer-B'

    @pytest.mark.asyncio
    async def test_leave_session(self, mock_postgres, mock_mt5_service):
        """Test leaving session releases account."""
        # Mock user in active session
        mock_postgres.fetchval.return_value = 'test-session-id'

        await game_service.leave_session('user-1')

        # Verify MT5 account released
        mock_mt5_service.release_account.assert_called_once_with('user-1')

        # Verify team member deleted
        assert mock_postgres.execute.called

    @pytest.mark.asyncio
    async def test_close_session_by_creator(self, mock_postgres):
        """Test closing session by creator."""
        # Mock session
        mock_postgres.fetchrow.return_value = {
            'session_id': 'test-session-id',
            'name': 'TestServer',
            'creator_id': 'user-1',
            'status': 'active'
        }

        await game_service.complete_session('test-session-id')

        # Verify status updated to completed
        assert mock_postgres.execute.called


@pytest.mark.asyncio
class TestCommandProcessorGameCommands:
    """Test command processor game commands."""

    @pytest.fixture
    def command_processor(self):
        """Create command processor instance."""
        mock_mt5_manager = MagicMock()
        return CommandProcessor(mock_mt5_manager)

    @pytest.mark.asyncio
    async def test_csv_command_success(self, command_processor):
        """Test /csv command success."""
        with patch('app.processors.command_processor.game_service') as mock_gs:
            mock_session = MagicMock()
            mock_session.dict.return_value = {'name': 'TestServer'}
            mock_gs.create_session = AsyncMock(return_value=mock_session)

            result = await command_processor.process_create_server(
                'sid-1', 'user-1', 'TestServer'
            )

            assert result['success'] is True
            assert result['data']['type'] == 'session_created'

    @pytest.mark.asyncio
    async def test_csv_command_missing_args(self, command_processor):
        """Test /csv command with missing args."""
        result = await command_processor.process_create_server(
            'sid-1', 'user-1', ''
        )

        assert result['success'] is False
        assert 'Usage' in result['error']['message']

    @pytest.mark.asyncio
    async def test_jsv_command_success(self, command_processor):
        """Test /jsv command success."""
        with patch('app.processors.command_processor.game_service') as mock_gs:
            mock_session = MagicMock()
            mock_session.dict.return_value = {'name': 'TestServer'}
            mock_team = MagicMock()
            mock_team.dict.return_value = {'team_name': 'TestServer-A'}
            mock_team.team_name = 'TestServer-A'

            mock_gs.join_session = AsyncMock(return_value={
                'session': mock_session,
                'team': mock_team,
                'account_allocated': True
            })

            result = await command_processor.process_join_server(
                'sid-1', 'user-2', 'TestServer'
            )

            assert result['success'] is True
            assert result['data']['type'] == 'session_joined'

    @pytest.mark.asyncio
    async def test_close_command_by_creator(self, command_processor):
        """Test /close command by creator."""
        with patch('app.processors.command_processor.postgres_client') as mock_pg:
            with patch('app.processors.command_processor.game_service') as mock_gs:
                mock_pg.fetchrow.return_value = {
                    'session_id': 'test-session-id',
                    'name': 'TestServer',
                    'creator_id': 'user-1',
                    'status': 'active'
                }
                mock_gs.complete_session = AsyncMock()

                result = await command_processor.process_close_server(
                    'sid-1', 'user-1'
                )

                assert result['success'] is True
                assert result['data']['type'] == 'session_closed'

    @pytest.mark.asyncio
    async def test_close_command_by_non_creator(self, command_processor):
        """Test /close command by non-creator."""
        with patch('app.processors.command_processor.postgres_client') as mock_pg:
            mock_pg.fetchrow.return_value = {
                'session_id': 'test-session-id',
                'name': 'TestServer',
                'creator_id': 'user-1',  # Different from requester
                'status': 'active'
            }

            result = await command_processor.process_close_server(
                'sid-1', 'user-2'  # Not the creator
            )

            assert result['success'] is False
            assert 'creator' in result['error']['message'].lower()
