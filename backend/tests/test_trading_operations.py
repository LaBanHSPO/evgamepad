import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from app.mt5.trading_operations import TradingOperations
from app.mt5.connection_manager import MT5ConnectionManager
import MetaTrader5 as mt5

@pytest.fixture
def mock_conn():
    conn = Mock(spec=MT5ConnectionManager)
    conn.is_connected.return_value = True
    return conn

@pytest.mark.asyncio
async def test_place_buy_market(mock_conn):
    ops = TradingOperations(mock_conn)

    # Mock MT5
    with patch('app.mt5.trading_operations.mt5') as mock_mt5, \
         patch('app.mt5.error_handler.mt5', mock_mt5): # Patch where ErrorHandler uses it too
        
        mock_mt5.symbol_info.return_value = MagicMock(visible=True)
        mock_mt5.symbol_info_tick.return_value = MagicMock(ask=1.0850, bid=1.0848)
        
        mock_ret = MagicMock()
        mock_ret.retcode = 10009 # DONE
        mock_ret.order = 123456
        mock_ret.price = 1.0850
        mock_ret._asdict.return_value = {'retcode': 10009, 'ticket': 123456, 'price': 1.0850}
        
        mock_mt5.order_send.return_value = mock_ret
        mock_mt5.TRADE_RETCODE_DONE = 10009
        mock_mt5.ORDER_TYPE_BUY = 0

        result = await ops.place_buy_market('EURUSD', 0.01, sl=1.0800, tp=1.0900)

        assert result['ticket'] == 123456
        assert result['price'] == 1.0850
        mock_mt5.order_send.assert_called_once()

@pytest.mark.asyncio
async def test_place_order_not_connected(mock_conn):
    mock_conn.is_connected.return_value = False
    ops = TradingOperations(mock_conn)
    result = await ops.place_buy_market('EURUSD', 0.01)
    # Check retcode for connection error (whatever we mapped or MT5 const)
    assert 'retcode' in result

@pytest.mark.asyncio
async def test_modify_position(mock_conn):
    ops = TradingOperations(mock_conn)
    
    with patch('app.mt5.trading_operations.mt5') as mock_mt5:
        # Mock existing position
        mock_pos = MagicMock()
        mock_pos._asdict.return_value = {'ticket': 123, 'symbol': 'EURUSD', 'sl': 1.0, 'tp': 2.0}
        mock_mt5.positions_get.return_value = [mock_pos]
        
        # Mock successful modification
        mock_ret = MagicMock()
        mock_ret.retcode = 10009
        mock_ret._asdict.return_value = {'retcode': 10009}
        mock_mt5.order_send.return_value = mock_ret
        mock_mt5.TRADE_RETCODE_DONE = 10009
        
        result = await ops.modify_position(123, new_sl=1.1)
        
        assert result['retcode'] == 10009
        args, _ = mock_mt5.order_send.call_args
        request = args[0]
        assert request['action'] == mt5.TRADE_ACTION_SLTP
        assert request['sl'] == 1.1
        assert request['tp'] == 2.0 # Unchanged
