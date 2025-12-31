"""Integration tests for MT5 trading flow - Phase 02"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.mt5_integration_service import mt5_integration_service
from app.models.mt5_models import OrderType


@pytest.fixture
def mock_database():
    """Mock database operations."""
    with patch('app.services.mt5_integration_service.postgres_client') as mock_pg:
        yield mock_pg


@pytest.mark.asyncio
async def test_full_trading_flow(mock_database):
    """
    Test complete trading flow:
    1. Allocate account
    2. Execute order
    3. Sync positions
    4. Release account
    """
    user_id = "integration-user-1"
    session_id = "integration-session-1"

    # Initialize service
    await mt5_integration_service.initialize()

    # Step 1: Allocate account
    mock_database.fetchrow = AsyncMock(return_value={
        'account_number': 99999,
        'broker_server': 'IntegrationBroker',
        'encrypted_password': mt5_integration_service._encrypt_password('integration-pass'),
        'allocated_at': MagicMock()
    })

    allocation = await mt5_integration_service.allocate_account(user_id)

    assert allocation is not None
    assert allocation.account_number == 99999

    # Step 2: Execute order
    with patch.object(mt5_integration_service, '_login_to_account', return_value=True):
        with patch.object(mt5_integration_service, '_place_market_order', return_value={
            'success': True,
            'retcode': 10009,
            'order': 777777,
            'price': 1.2000,
            'volume': 0.5,
            'comment': 'Done'
        }):
            mock_database.execute = AsyncMock()
            mock_database.fetchrow.return_value = {
                'account_number': 99999,
                'broker_server': 'IntegrationBroker',
                'encrypted_password': mt5_integration_service._encrypt_password('integration-pass'),
                'allocated_at': MagicMock()
            }
            # Mock session membership validation
            mock_database.fetchval = AsyncMock(return_value=1)  # User is member

            result = await mt5_integration_service.execute_order(
                session_id=session_id,
                user_id=user_id,
                symbol="GBPUSD",
                order_type=OrderType.BUY,
                volume=Decimal("0.5")
            )

            assert result['success'] is True
            assert result['order'] == 777777

    # Step 3: Sync positions
    mock_database.fetch = AsyncMock(return_value=[
        {
            'account_number': 99999,
            'broker_server': 'IntegrationBroker',
            'encrypted_password': mt5_integration_service._encrypt_password('integration-pass')
        }
    ])

    with patch.object(mt5_integration_service, '_login_to_account', return_value=True):
        with patch('app.services.mt5_integration_service.mt5.positions_get', return_value=[]):
            sync_count = await mt5_integration_service.sync_positions(session_id)

            # No positions to sync in this mock
            assert sync_count >= 0

    # Step 4: Release account
    mock_database.fetchrow.return_value = {'account_number': 99999}

    released = await mt5_integration_service.release_account(user_id)

    assert released is True


@pytest.mark.asyncio
async def test_account_pool_exhaustion_handling(mock_database):
    """Test handling of pool exhaustion scenario."""
    await mt5_integration_service.initialize()

    # Try to allocate when pool is empty
    mock_database.fetchrow = AsyncMock(return_value=None)

    allocation = await mt5_integration_service.allocate_account("user-pool-full")

    assert allocation is None


@pytest.mark.asyncio
async def test_concurrent_account_allocation(mock_database):
    """Test concurrent account allocation (FOR UPDATE SKIP LOCKED)."""
    await mt5_integration_service.initialize()

    # Simulate concurrent allocations
    users = ["concurrent-user-1", "concurrent-user-2", "concurrent-user-3"]

    allocations = []

    for i, user_id in enumerate(users):
        mock_database.fetchrow = AsyncMock(return_value={
            'account_number': 10000 + i,
            'broker_server': 'ConcurrentBroker',
            'encrypted_password': mt5_integration_service._encrypt_password(f'pass-{i}'),
            'allocated_at': MagicMock()
        })

        allocation = await mt5_integration_service.allocate_account(user_id)
        allocations.append(allocation)

    # All should get unique accounts
    assert len(allocations) == 3
    assert all(a is not None for a in allocations)
    # Verify different account numbers
    account_numbers = [a.account_number for a in allocations]
    assert len(set(account_numbers)) == 3  # All unique


@pytest.mark.asyncio
async def test_order_execution_without_allocated_account(mock_database):
    """Test that order execution fails gracefully without account."""
    await mt5_integration_service.initialize()

    # No account allocated
    mock_database.fetchrow = AsyncMock(return_value=None)

    result = await mt5_integration_service.execute_order(
        session_id="test-session",
        user_id="no-account-user",
        symbol="EURUSD",
        order_type=OrderType.SELL,
        volume=Decimal("1.0")
    )

    assert result['success'] is False
    assert 'No MT5 account allocated' in result['error']


@pytest.mark.asyncio
async def test_position_sync_with_multiple_accounts(mock_database):
    """Test position sync across multiple allocated accounts."""
    await mt5_integration_service.initialize()

    session_id = "multi-account-session"

    # Mock multiple accounts in session
    mock_database.fetch = AsyncMock(return_value=[
        {
            'account_number': 11111,
            'broker_server': 'MultiTest1',
            'encrypted_password': mt5_integration_service._encrypt_password('pass1')
        },
        {
            'account_number': 22222,
            'broker_server': 'MultiTest2',
            'encrypted_password': mt5_integration_service._encrypt_password('pass2')
        }
    ])

    with patch.object(mt5_integration_service, '_login_to_account', return_value=True):
        # Mock positions
        mock_position = MagicMock()
        mock_position.ticket = 88888
        mock_position.symbol = 'USDJPY'
        mock_position.type = 0  # BUY
        mock_position.volume = 1.0
        mock_position.price_open = 110.50
        mock_position.profit = 50.0
        mock_position.time = 1234567890

        with patch('app.services.mt5_integration_service.mt5.positions_get', return_value=[mock_position]):
            mock_database.fetchrow = AsyncMock(return_value=None)  # No existing position
            mock_database.execute = AsyncMock()

            sync_count = await mt5_integration_service.sync_positions(session_id)

            # Should sync positions from both accounts
            assert sync_count == 2  # 1 position per account
