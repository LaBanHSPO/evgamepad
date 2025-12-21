import sys
from unittest.mock import MagicMock

# Mock MetaTrader5 module before it is imported by app modules
# This allows running tests on non-Windows environments (Linux/Mac)
# where the MetaTrader5 package cannot be installed.
module_name = 'MetaTrader5'
if module_name not in sys.modules:
    mock_mt5 = MagicMock()
    # Define constants used in code
    mock_mt5.TRADE_RETCODE_DONE = 10009
    mock_mt5.TRADE_RETCODE_REQUOTE = 10004
    mock_mt5.TRADE_RETCODE_TIMEOUT = 10022
    mock_mt5.TRADE_RETCODE_INVALID_PRICE = 10015
    mock_mt5.TRADE_RETCODE_PRICE_OFF = 10016
    mock_mt5.TRADE_RETCODE_PRICE_CHANGED = 10017
    mock_mt5.TRADE_RETCODE_CONNECTION = 10018
    mock_mt5.TRADE_RETCODE_ERROR = 10000
    mock_mt5.TRADE_RETCODE_DONE_PARTIAL = 10010
    mock_mt5.TRADE_RETCODE_INVALID = 10013
    
    mock_mt5.ORDER_TYPE_BUY = 0
    mock_mt5.ORDER_TYPE_SELL = 1
    
    mock_mt5.TRADE_ACTION_DEAL = 1
    mock_mt5.TRADE_ACTION_SLTP = 6
    
    mock_mt5.ORDER_TIME_GTC = 0
    mock_mt5.ORDER_FILLING_IOC = 1
    
    sys.modules[module_name] = mock_mt5
