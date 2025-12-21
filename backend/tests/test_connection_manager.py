import pytest
from unittest.mock import Mock, patch, MagicMock
from app.mt5.connection_manager import MT5ConnectionManager

@pytest.fixture
def mock_mt5():
    with patch('app.mt5.connection_manager.mt5') as mock:
        mock.initialize.return_value = True
        mock.terminal_info.return_value = MagicMock(connected=True, trade_allowed=True)
        yield mock

def test_connect_success(mock_mt5):
    manager = MT5ConnectionManager()
    assert manager.connect() is True
    assert manager.is_connected() is True

def test_connect_failure(mock_mt5):
    mock_mt5.initialize.return_value = False
    manager = MT5ConnectionManager()
    assert manager.connect() is False
    assert manager.is_connected() is False

def test_disconnect(mock_mt5):
    manager = MT5ConnectionManager()
    manager.connect()
    manager.disconnect()
    mock_mt5.shutdown.assert_called()
    assert manager._connected is False

def test_health_check_reconnect(mock_mt5):
    # This is harder to test without sleeping, but we can verify logic
    manager = MT5ConnectionManager(check_interval=0.1)
    
    # Mock initial connection
    manager.connect()
    
    # Simulate disconnect
    mock_mt5.terminal_info.return_value.connected = False
    
    # Attempt reconnect logic directly to avoid thread race conditions in simple test
    result = manager._attempt_reconnect(max_attempts=1)
    assert result is True
    assert mock_mt5.initialize.call_count >= 2 # Once for init, once for reconnect
