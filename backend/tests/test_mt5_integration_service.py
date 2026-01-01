"""Unit tests for MT5IntegrationService - Phase 02"""
import pytest
import pytest_asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from app.services.mt5_integration_service import MT5IntegrationService
from app.models.mt5_models import (
    MT5AccountAllocation,
    OrderType,
    OrderStatus,
    AccountPoolStats,
    HealthStatus
)


@pytest_asyncio.fixture
async def mt5_service():
    """Create MT5 integration service instance."""
    service = MT5IntegrationService()
    await service.initialize()
    return service


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL client."""
    with patch('app.services.mt5_integration_service.postgres_client') as mock_pg:
        yield mock_pg


@pytest.mark.asyncio
async def test_initialize_service(mt5_service):
    """Test service initialization."""
    assert mt5_service._initialized is True
    assert mt5_service._cipher is not None


@pytest.mark.asyncio
async def test_allocate_account_success(mt5_service, mock_postgres):
    """Test successful account allocation."""
    user_id = "test-user-1"

    # Mock database response
    mock_postgres.fetchrow = AsyncMock(return_value={
        'account_number': 12345,
        'broker_server': 'TestBroker-Demo',
        'encrypted_password': mt5_service._encrypt_password('test-password'),
        'allocated_at': datetime.now()
    })

    allocation = await mt5_service.allocate_account(user_id)

    assert allocation is not None
    assert allocation.account_number == 12345
    assert allocation.broker_server == 'TestBroker-Demo'
    assert allocation.decrypted_password == 'test-password'
    assert mock_postgres.fetchrow.called


@pytest.mark.asyncio
async def test_allocate_account_pool_exhausted(mt5_service, mock_postgres):
    """Test account allocation when pool is exhausted."""
    user_id = "test-user-2"

    # Mock no available accounts
    mock_postgres.fetchrow = AsyncMock(return_value=None)

    allocation = await mt5_service.allocate_account(user_id)

    assert allocation is None


@pytest.mark.asyncio
async def test_release_account_success(mt5_service, mock_postgres):
    """Test successful account release."""
    user_id = "test-user-3"

    # Mock successful release
    mock_postgres.fetchrow = AsyncMock(return_value={'account_number': 12345})

    result = await mt5_service.release_account(user_id)

    assert result is True
    assert mock_postgres.fetchrow.called


@pytest.mark.asyncio
async def test_release_account_not_allocated(mt5_service, mock_postgres):
    """Test releasing account when none allocated."""
    user_id = "test-user-4"

    # Mock no account to release
    mock_postgres.fetchrow = AsyncMock(return_value=None)

    result = await mt5_service.release_account(user_id)

    assert result is False


@pytest.mark.asyncio
async def test_get_user_account(mt5_service, mock_postgres):
    """Test getting user's allocated account."""
    user_id = "test-user-5"

    # Mock database response
    mock_postgres.fetchrow = AsyncMock(return_value={
        'account_number': 67890,
        'broker_server': 'TestBroker',
        'encrypted_password': mt5_service._encrypt_password('secure-pass'),
        'allocated_at': datetime.now()
    })

    account = await mt5_service.get_user_account(user_id)

    assert account is not None
    assert account.account_number == 67890
    assert account.decrypted_password == 'secure-pass'


@pytest.mark.asyncio
async def test_get_pool_stats(mt5_service, mock_postgres):
    """Test getting account pool statistics."""
    # Mock stats query
    mock_postgres.fetchrow = AsyncMock(return_value={
        'total': 10,
        'available': 3,
        'in_use': 5,
        'error': 1,
        'expired': 1,
        'healthy': 8,
        'unhealthy': 1,
        'disconnected': 1
    })

    stats = await mt5_service.get_pool_stats()

    assert stats.total_accounts == 10
    assert stats.available == 3
    assert stats.in_use == 5
    assert stats.healthy == 8


@pytest.mark.asyncio
async def test_execute_order_no_account(mt5_service):
    """Test order execution when user has no allocated account."""
    with patch.object(mt5_service, 'get_user_account', return_value=None):
        result = await mt5_service.execute_order(
            session_id="test-session",
            user_id="test-user",
            symbol="EURUSD",
            order_type=OrderType.BUY,
            volume=Decimal("0.1")
        )

        assert result['success'] is False
        assert 'No MT5 account allocated' in result['error']


@pytest.mark.asyncio
async def test_execute_order_success(mt5_service, mock_postgres):
    """Test successful order execution."""
    user_id = "test-user-6"

    # Mock allocated account
    mock_account = MT5AccountAllocation(
        account_number=12345,
        broker_server='TestBroker',
        decrypted_password='test-pass',
        allocated_at=datetime.now()
    )

    with patch.object(mt5_service, 'get_user_account', return_value=mock_account):
        # Mock session membership validation
        mock_postgres.fetchval = AsyncMock(return_value=1)  # User is member

        with patch.object(mt5_service, '_login_to_account', return_value=True):
            with patch.object(mt5_service, '_place_market_order', return_value={
                'success': True,
                'retcode': 10009,  # TRADE_RETCODE_DONE
                'order': 123456,
                'price': 1.1234,
                'volume': 0.1,
                'comment': 'Done'
            }):
                # Mock order recording
                mock_postgres.execute = AsyncMock()

                result = await mt5_service.execute_order(
                    session_id="test-session",
                    user_id=user_id,
                    symbol="EURUSD",
                    order_type=OrderType.BUY,
                    volume=Decimal("0.1")
                )

                assert result['success'] is True
                assert result['order'] == 123456


@pytest.mark.asyncio
async def test_sync_positions_no_active_sessions(mt5_service, mock_postgres):
    """Test position sync when no active sessions."""
    # Mock no active sessions
    mock_postgres.fetch = AsyncMock(return_value=[])

    count = await mt5_service.sync_positions("test-session")

    assert count == 0


@pytest.mark.asyncio
async def test_password_encryption_decryption(mt5_service):
    """Test password encryption and decryption."""
    original_password = "MySecurePassword123!"

    # Encrypt
    encrypted = mt5_service._encrypt_password(original_password)

    # Verify encrypted != original
    assert encrypted != original_password

    # Decrypt
    decrypted = mt5_service._decrypt_password(encrypted)

    # Verify decrypted == original
    assert decrypted == original_password
