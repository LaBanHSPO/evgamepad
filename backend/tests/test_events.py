import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.events import trading_events
from app.validation import validate_login_command

@pytest.mark.asyncio
async def test_connect_event():
    """Test client connection"""
    # Mock sio and session_manager
    sid = "test_client_1"
    environ = {'REMOTE_ADDR': '192.168.1.100'}
    
    with patch('app.events.trading_events.sio', new_callable=AsyncMock) as mock_sio, \
         patch('app.events.trading_events.session_manager') as mock_sm:
        
        # Call connect handler
        await trading_events.connect(sid, environ)
        
        # Verify session created
        mock_sm.create_session.assert_called_once()
        args = mock_sm.create_session.call_args[0]
        assert args[0] == sid
        assert args[1]['remote_addr'] == '192.168.1.100'
        
        # Verify welcome message
        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == 'connected'
        assert call_args[1]['to'] == sid

def test_login_validation():
    """Test login command validation"""
    # Valid
    valid, msg = validate_login_command({
        'account': 12345678,
        'password': 'test',
        'server': 'Demo'
    })
    assert valid is True

    # Invalid - missing field
    valid, msg = validate_login_command({
        'account': 12345678,
        'password': 'test'
    })
    assert valid is False
    assert 'server' in msg

@pytest.mark.asyncio
async def test_login_event_success():
    """Test successful login"""
    sid = "test_sid"
    data = {
        'account': 12345678,
        'password': 'pass',
        'server': 'server'
    }
    
    mock_account_info = {
        'login': 12345678,
        'name': 'Test User',
        'server': 'server',
        'currency': 'USD',
        'balance': 1000.0,
        'equity': 1000.0,
        'leverage': 100
    }

    with patch('app.events.trading_events.sio', new_callable=AsyncMock) as mock_sio, \
         patch('app.events.trading_events.session_manager') as mock_sm, \
         patch('app.events.trading_events.mt5_manager') as mock_mt5:
        
        mock_mt5.login_account.return_value = mock_account_info
        mock_sm.get_session.return_value = {}

        await trading_events.login(sid, data)
        
        mock_mt5.login_account.assert_called_once_with(12345678, 'pass', 'server')
        # Check success emission
        # We can't easily check the content of arguments with assert_called_with if they are complex objects
        # But we can check calls list
        assert mock_sio.emit.called
        call_args = mock_sio.emit.call_args_list[0]
        assert call_args[0][0] == 'login_result'
        assert call_args[0][1]['success'] is True
        assert call_args[1]['to'] == sid
