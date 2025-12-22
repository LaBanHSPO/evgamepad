import MetaTrader5 as mt5
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MT5ErrorHandler:
    # Retriable return codes
    RETRIABLE_CODES = {
        mt5.TRADE_RETCODE_REQUOTE,
        mt5.TRADE_RETCODE_TIMEOUT,
        mt5.TRADE_RETCODE_PRICE_OFF,
        mt5.TRADE_RETCODE_PRICE_CHANGED,
        mt5.TRADE_RETCODE_CONNECTION,
    }

    # Common error messages map (fallback if MT5 doesn't provide clear desc)
    ERROR_MESSAGES = {
        mt5.TRADE_RETCODE_DONE: "Request completed",
        mt5.TRADE_RETCODE_DONE_PARTIAL: "Request completed partially",
        mt5.TRADE_RETCODE_ERROR: "Common error",
        mt5.TRADE_RETCODE_TIMEOUT: "Request timed out",
        mt5.TRADE_RETCODE_INVALID: "Invalid request",
        mt5.TRADE_RETCODE_REQUOTE: "Requote",
        mt5.TRADE_RETCODE_PRICE_OFF: "Price is off quotes",
        mt5.TRADE_RETCODE_PRICE_CHANGED: "Price changed",
        mt5.TRADE_RETCODE_INVALID_PRICE: "Invalid price",
        mt5.TRADE_RETCODE_CONNECTION: "No connection",
    }

    @staticmethod
    def is_retriable(retcode: int) -> bool:
        """Check if the error code indicates the operation should be retried."""
        return retcode in MT5ErrorHandler.RETRIABLE_CODES

    @staticmethod
    def get_error_message(retcode: int) -> str:
        """Get human-readable error message for a return code."""
        return MT5ErrorHandler.ERROR_MESSAGES.get(retcode, f"Unknown error code: {retcode}")

    @staticmethod
    def order_with_retry(
        request: Dict[str, Any], 
        max_retries: int = 3, 
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Execute an order request with retry logic for retriable errors.
        This is a synchronous method (run in thread).
        """
        for attempt in range(max_retries):
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                logger.error("Order send returned None (MT5 internal error)")
                return {"retcode": mt5.TRADE_RETCODE_ERROR, "comment": "Internal MT5 API error"}
                
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return result._asdict()
            
            if MT5ErrorHandler.is_retriable(result.retcode):
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Retriable error {result.retcode} ({result.comment}), "
                        f"retrying in {retry_delay}s (Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    continue
            
            # If we get here, it's either success (handled above), 
            # non-retriable error, or out of retries
            logger.error(f"Order failed: {result.retcode} - {result.comment}")
            return result._asdict()
            
        return {"retcode": mt5.TRADE_RETCODE_TIMEOUT, "comment": "Max retries exceeded"}
