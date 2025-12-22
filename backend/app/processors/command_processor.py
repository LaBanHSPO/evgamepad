import logging
import uuid
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from app.mt5.trading_operations import TradingOperations
from app.mt5.connection_manager import MT5ConnectionManager
from app.models.responses import ErrorCode, error_response, success_response
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

class CommandProcessor:
    """
    Central command processing layer
    Routes Socket.IO events to MT5 operations
    """

    def __init__(self, mt5_manager: MT5ConnectionManager):
        self.mt5_manager = mt5_manager
        self.trading_ops = TradingOperations(mt5_manager)
        self.pending_commands: Dict[str, Dict[str, Any]] = {}

    async def _execute_mt5_operation(self, command_id: str, operation_name: str, func, **kwargs) -> Dict[str, Any]:
        """
        Helper to execute MT5 operations with common error handling and logging.
        """
        try:
            # Execute with circuit breaker protection (blocking call, wrapped in async)
            # We pass the function and kwargs to execute_with_circuit_breaker
            def wrapped_func():
                return func(**kwargs)

            result = await asyncio.to_thread(
                self.mt5_manager.execute_with_circuit_breaker,
                wrapped_func
            )
            return result

        except ValueError as e:
            # Validation error (invalid symbol, etc.)
            logger.warning(f"[{command_id}] {operation_name} validation failed: {e}")
            raise
        except RuntimeError as e:
            # MT5 connection error or Circuit Breaker Open
            logger.error(f"[{command_id}] {operation_name} failed (MT5 error): {e}")
            raise
        except Exception as e:
             # Generic error
            logger.exception(f"[{command_id}] {operation_name} failed unexpectedly")
            raise

    async def process_buy_order(
        self,
        sid: str,
        symbol: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process buy market order
        """
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing BUY order: {symbol} {volume} lots (client: {sid})")

        self.pending_commands[command_id] = {
            'type': 'buy',
            'symbol': symbol,
            'volume': volume,
            'client_id': sid,
            'started_at': datetime.utcnow(),
        }

        try:
            result = await self._execute_mt5_operation(
                command_id, "BUY order",
                self.trading_ops.place_buy_market,
                symbol=symbol,
                volume=volume,
                sl=sl,
                tp=tp
            )

            if result.get('retcode') != mt5.TRADE_RETCODE_DONE:
                retcode = result.get('retcode')
                comment = result.get('comment', 'Unknown MT5 error')
                logger.error(
                    f"[{command_id}] BUY order failed - retcode: {retcode}, comment: {comment}, "
                    f"symbol: {symbol}, volume: {volume}"
                )
                return error_response(
                    ErrorCode.MT5_ERROR,
                    f"MT5 Error {retcode}: {comment}",
                    details={'retcode': retcode, 'symbol': symbol, 'volume': volume}
                )

            logger.info(
                f"[{command_id}] BUY order executed: "
                f"Ticket={result['ticket']}, Price={result['price']}"
            )

            return success_response({
                'command_id': command_id,
                'ticket': result['ticket'],
                'symbol': symbol,
                'volume': result['volume'],
                'price': result['price'],
                'sl': sl,
                'tp': tp,
                'timestamp': result['timestamp'],
            })

        except ValueError as e:
            return error_response(ErrorCode.VALIDATION_ERROR, str(e))
        except RuntimeError as e:
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))
        except Exception as e:
            return error_response(ErrorCode.INTERNAL_ERROR, f"Order execution failed: {str(e)}")
        finally:
             self.pending_commands.pop(command_id, None)

    async def process_sell_order(
        self,
        sid: str,
        symbol: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process sell market order"""
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing SELL order: {symbol} {volume} lots (client: {sid})")

        self.pending_commands[command_id] = {
            'type': 'sell',
            'symbol': symbol,
            'volume': volume,
            'client_id': sid,
            'started_at': datetime.utcnow(),
        }

        try:
            result = await self._execute_mt5_operation(
                 command_id, "SELL order",
                self.trading_ops.place_sell_market,
                symbol=symbol,
                volume=volume,
                sl=sl,
                tp=tp
            )

            if result.get('retcode') != mt5.TRADE_RETCODE_DONE:
                retcode = result.get('retcode')
                comment = result.get('comment', 'Unknown MT5 error')
                logger.error(
                    f"[{command_id}] SELL order failed - retcode: {retcode}, comment: {comment}, "
                    f"symbol: {symbol}, volume: {volume}"
                )
                return error_response(
                    ErrorCode.MT5_ERROR,
                    f"MT5 Error {retcode}: {comment}",
                    details={'retcode': retcode, 'symbol': symbol, 'volume': volume}
                )

            logger.info(
                f"[{command_id}] SELL order executed: "
                f"Ticket={result['ticket']}, Price={result['price']}"
            )

            return success_response({
                'command_id': command_id,
                'ticket': result['ticket'],
                'symbol': symbol,
                'volume': result['volume'],
                'price': result['price'],
                'sl': sl,
                'tp': tp,
                'timestamp': result['timestamp'],
            })

        except ValueError as e:
            return error_response(ErrorCode.VALIDATION_ERROR, str(e))
        except RuntimeError as e:
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))
        except Exception as e:
            return error_response(ErrorCode.INTERNAL_ERROR, f"Order execution failed: {str(e)}")
        finally:
            self.pending_commands.pop(command_id, None)

    async def process_modify_position(
        self,
        sid: str,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process modify position TP/SL"""
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing MODIFY: Ticket={ticket} (client: {sid})")

        self.pending_commands[command_id] = {
            'type': 'modify',
            'ticket': ticket,
            'client_id': sid,
            'started_at': datetime.utcnow(),
        }

        try:
            result = await self._execute_mt5_operation(
                command_id, "MODIFY",
                self.trading_ops.modify_position,
                ticket=ticket,
                new_sl=sl,
                new_tp=tp
            )

            if result.get('retcode') != mt5.TRADE_RETCODE_DONE:
                retcode = result.get('retcode')
                comment = result.get('comment', 'Unknown MT5 error')
                logger.error(
                    f"[{command_id}] MODIFY failed - retcode: {retcode}, comment: {comment}, "
                    f"ticket: {ticket}"
                )
                return error_response(
                    ErrorCode.MT5_ERROR,
                    f"MT5 Error {retcode}: {comment}",
                    details={'retcode': retcode, 'ticket': ticket}
                )

            logger.info(
                f"[{command_id}] Position modified: "
                f"Ticket={ticket}, SL={result['new_sl']}, TP={result['new_tp']}"
            )

            return success_response({
                'command_id': command_id,
                'ticket': ticket,
                'sl': result['new_sl'],
                'tp': result['new_tp'],
                'modified_at': result['modified_at'],
            })

        except ValueError as e:
            return error_response(ErrorCode.POSITION_NOT_FOUND, str(e))
        except RuntimeError as e:
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))
        except Exception as e:
            return error_response(ErrorCode.INTERNAL_ERROR, f"Modify failed: {str(e)}")
        finally:
             self.pending_commands.pop(command_id, None)

    async def process_close_position(
        self,
        sid: str,
        ticket: int,
        volume: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process close position"""
        command_id = str(uuid.uuid4())
        logger.info(f"[{command_id}] Processing CLOSE: Ticket={ticket} (client: {sid})")

        self.pending_commands[command_id] = {
            'type': 'close',
            'ticket': ticket,
            'client_id': sid,
            'started_at': datetime.utcnow(),
        }

        try:
            result = await self._execute_mt5_operation(
                command_id, "CLOSE",
                self.trading_ops.close_position,
                ticket=ticket,
                volume=volume
            )

            if result.get('retcode') != mt5.TRADE_RETCODE_DONE:
                retcode = result.get('retcode')
                comment = result.get('comment', 'Unknown MT5 error')
                logger.error(
                    f"[{command_id}] CLOSE failed - retcode: {retcode}, comment: {comment}, "
                    f"ticket: {ticket}"
                )
                return error_response(
                    ErrorCode.MT5_ERROR,
                    f"MT5 Error {retcode}: {comment}",
                    details={'retcode': retcode, 'ticket': ticket}
                )

            logger.info(
                f"[{command_id}] Position closed: "
                f"Ticket={ticket}, Price={result['close_price']}, Profit={result['profit']}"
            )

            return success_response({
                'command_id': command_id,
                'ticket': ticket,
                'close_ticket': result['close_ticket'],
                'close_price': result['close_price'],
                'volume_closed': result['volume_closed'],
                'profit': result['profit'],
                'closed_at': result['closed_at'],
            })

        except ValueError as e:
            return error_response(ErrorCode.POSITION_NOT_FOUND, str(e))
        except RuntimeError as e:
            return error_response(ErrorCode.MT5_NOT_CONNECTED, str(e))
        except Exception as e:
            return error_response(ErrorCode.INTERNAL_ERROR, f"Close failed: {str(e)}")
        finally:
             self.pending_commands.pop(command_id, None)

    def get_pending_commands(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending commands (for debugging)"""
        return self.pending_commands.copy()
