import MetaTrader5 as mt5
import logging
from typing import Dict, Any, Optional, List
from .connection_manager import MT5ConnectionManager
from .error_handler import MT5ErrorHandler
from ..config import config

logger = logging.getLogger(__name__)

class TradingOperations:
    """
    Handles all trading operations including order placement, modification, and closing.
    """
    def __init__(self, connection_manager: MT5ConnectionManager):
        self.conn = connection_manager

    async def place_market_order(
        self, 
        symbol: str, 
        volume: float, 
        order_type: int, 
        sl: Optional[float] = None, 
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Place a market order (Buy or Sell)."""
        if not self.conn.is_connected():
            return {"retcode": mt5.TRADE_RETCODE_CONNECTION, "comment": "Not connected to MT5"}

        if not self._validate_symbol(symbol):
            return {"retcode": mt5.TRADE_RETCODE_INVALID, "comment": f"Symbol {symbol} not found or not visible"}

        price = self._get_market_price(symbol, order_type)
        if price is None:
            return {"retcode": mt5.TRADE_RETCODE_INVALID_PRICE, "comment": "Failed to get market price"}

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": int(config.DEFAULT_SLIPPAGE),
            "magic": 123456,  # TODO: Make configurable
            "comment": "SocketIO Server",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._get_filling_mode(symbol),
        }

        if sl:
            request["sl"] = sl
        if tp:
            request["tp"] = tp

        logger.info(f"Placing order: {symbol} {volume} lots @ {price}")
        return await MT5ErrorHandler.order_with_retry(request)

    async def place_buy_market(self, symbol: str, volume: float, sl: float = None, tp: float = None) -> Dict[str, Any]:
        """Convenience method for Buy Market order."""
        return await self.place_market_order(symbol, volume, mt5.ORDER_TYPE_BUY, sl, tp)

    async def place_sell_market(self, symbol: str, volume: float, sl: float = None, tp: float = None) -> Dict[str, Any]:
        """Convenience method for Sell Market order."""
        return await self.place_market_order(symbol, volume, mt5.ORDER_TYPE_SELL, sl, tp)

    async def modify_position(
        self, 
        ticket: int, 
        new_sl: Optional[float] = None, 
        new_tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Modify SL/TP of an existing position."""
        if not self.conn.is_connected():
            return {"retcode": mt5.TRADE_RETCODE_CONNECTION, "comment": "Not connected"}

        position = self.get_position(ticket)
        if not position:
            return {"retcode": mt5.TRADE_RETCODE_INVALID, "comment": "Position not found"}

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": position['symbol'],
            "sl": new_sl if new_sl is not None else position['sl'],
            "tp": new_tp if new_tp is not None else position['tp'],
        }

        logger.info(f"Modifying position {ticket}: SL={request['sl']}, TP={request['tp']}")
        return await MT5ErrorHandler.order_with_retry(request)

    async def close_position(self, ticket: int, volume: Optional[float] = None) -> Dict[str, Any]:
        """Close an existing position (full or partial)."""
        if not self.conn.is_connected():
            return {"retcode": mt5.TRADE_RETCODE_CONNECTION, "comment": "Not connected"}

        position = self.get_position(ticket)
        if not position:
            return {"retcode": mt5.TRADE_RETCODE_INVALID, "comment": "Position not found"}

        symbol = position['symbol']
        lot = volume if volume else position['volume']
        
        # Determine close type (Opposite of open type)
        order_type = mt5.ORDER_TYPE_SELL if position['type'] == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = self._get_market_price(symbol, order_type)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "deviation": int(config.DEFAULT_SLIPPAGE),
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._get_filling_mode(symbol),
        }

        logger.info(f"Closing position {ticket}: {lot} lots")
        return await MT5ErrorHandler.order_with_retry(request)

    def get_position(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Get position details by ticket."""
        positions = mt5.positions_get(ticket=ticket)
        if positions and len(positions) > 0:
            return positions[0]._asdict()
        return None

    def get_all_positions(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open positions, optionally filtered by symbol."""
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
            
        if positions:
            return [p._asdict() for p in positions]
        return []

    def _validate_symbol(self, symbol: str) -> bool:
        """Check if symbol exists and is visible in Market Watch."""
        sym = mt5.symbol_info(symbol)
        if sym is None:
            # Try to select it
            if not mt5.symbol_select(symbol, True):
                return False
            sym = mt5.symbol_info(symbol)
            return sym is not None
        
        if not sym.visible:
            if not mt5.symbol_select(symbol, True):
                return False
        
        return True

    def _get_market_price(self, symbol: str, order_type: int) -> Optional[float]:
        """Get the correct price for the order type."""
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        
        if order_type == mt5.ORDER_TYPE_BUY:
            return tick.ask
        elif order_type == mt5.ORDER_TYPE_SELL:
            return tick.bid
        return None

    def _get_filling_mode(self, symbol: str) -> int:
        """Determine appropriate filling mode for symbol."""
        # This can be more complex based on symbol properties
        # For now, rely on config or default to IOC
        filling = config.ORDER_FILLING_TYPE
        if filling == "FOK":
            return mt5.ORDER_FILLING_FOK
        elif filling == "RETURN":
            return mt5.ORDER_FILLING_RETURN
        return mt5.ORDER_FILLING_IOC
