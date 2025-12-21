import MetaTrader5 as mt5
import threading
import time
import logging
from typing import Dict, Any, Optional, Callable
from ..config import config
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class MT5ConnectionManager:
    """
    Manages the connection to the MetaTrader 5 terminal.
    Handles initialization, login, health monitoring, and auto-reconnection.
    """
    def __init__(self, check_interval: float = 5.0, timeout: float = 30.0):
        self.check_interval = check_interval
        self.timeout = timeout
        self._connected = False
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._health_thread: Optional[threading.Thread] = None
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=30.0
        )
        
    def connect(self) -> bool:
        """Initialize MT5 connection and login."""
        with self._lock:
            if self._connected:
                return True

            logger.info("Initializing MT5 connection...")
            
            # Initialize MT5
            if not mt5.initialize(timeout=int(self.timeout * 1000)):
                logger.error(f"MT5 initialization failed, error: {mt5.last_error()}")
                return False

            # Login if credentials provided
            if config.ACCOUNT_NUMBER and config.ACCOUNT_PASSWORD and config.BROKER_SERVER:
                logger.info(f"Logging in to account {config.ACCOUNT_NUMBER}...")
                authorized = mt5.login(
                    config.ACCOUNT_NUMBER, 
                    password=config.ACCOUNT_PASSWORD, 
                    server=config.BROKER_SERVER
                )
                if not authorized:
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
            
            self._connected = True
            logger.info("MT5 connected successfully")
            
            # Log account info
            info = self.get_account_info()
            if info:
                logger.info(f"Account: {info.get('login')} ({info.get('server')})")
                logger.info(f"Balance: {info.get('balance')} {info.get('currency')}")

            # Start health check if not running
            self._start_health_check()
            return True

    def login_account(self, account: int, password: str, server: str) -> Optional[Dict[str, Any]]:
        """Login to specific MT5 account."""
        with self._lock:
            # Ensure initialized
            if not self._connected:
                if not mt5.initialize(timeout=int(self.timeout * 1000)):
                     logger.error("MT5 initialization failed during login request")
                     return None

            logger.info(f"Logging in to account {account}...")
            authorized = mt5.login(
                account, 
                password=password, 
                server=server
            )
            
            if authorized:
                self._connected = True
                logger.info(f"Successfully logged in to {account}")
                self.circuit_breaker.reset() # Reset circuit breaker on successful login
                return self.get_account_info()
            else:
                logger.error(f"Login failed for {account}: {mt5.last_error()}")
                return None

    def execute_with_circuit_breaker(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute MT5 operation with circuit breaker protection

        Args:
            func: MT5 function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            RuntimeError: If circuit is open or operation fails
        """
        if not self.is_connected():
            raise RuntimeError("MT5 not connected")

        try:
            return self.circuit_breaker.execute(func, *args, **kwargs)
        except RuntimeError as e:
            if "Circuit breaker is open" in str(e):
                logger.error("Circuit breaker OPEN - refusing MT5 operations")
            raise

    def disconnect(self):
        """Disconnect from MT5 and stop health check."""
        with self._lock:
            self._stop_event.set()
            if self._health_thread:
                self._health_thread.join(timeout=2.0)
            
            if self._connected:
                mt5.shutdown()
                self._connected = False
                logger.info("MT5 disconnected")

    def is_connected(self) -> bool:
        """Check if connected to MT5 and terminal is connected to server."""
        if not self._connected:
            return False
        
        # Check actual terminal state
        term_info = mt5.terminal_info()
        if term_info is None:
            return False
            
        return term_info.connected

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get current account information."""
        if not self.is_connected():
            return None
        
        info = mt5.account_info()
        if info is None:
            return None
        return info._asdict()

    def _start_health_check(self):
        """Start the background health check thread."""
        if self._health_thread is not None and self._health_thread.is_alive():
            return

        self._stop_event.clear()
        self._health_thread = threading.Thread(
            target=self._health_check_loop, 
            name="MT5HealthCheck",
            daemon=True
        )
        self._health_thread.start()
        logger.info("Health check thread started")

    def _health_check_loop(self):
        """Background loop to monitor connection health."""
        while not self._stop_event.is_set():
            try:
                if self._connected:
                    if not self.is_connected():
                        logger.warning("Connection lost, attempting reconnect...")
                        if self._attempt_reconnect():
                             self.circuit_breaker.reset()
                
            except Exception as e:
                logger.error(f"Error in health check: {e}")
            
            time.sleep(self.check_interval)

    def _attempt_reconnect(self, max_attempts: int = 3) -> bool:
        """Attempt to reconnect to MT5."""
        with self._lock:
            self._connected = False
            # Ensure clean state
            mt5.shutdown()
            
            backoff = 1.0
            
            for attempt in range(max_attempts):
                logger.info(f"Reconnection attempt {attempt + 1}/{max_attempts}")
                
                if mt5.initialize(timeout=int(self.timeout * 1000)):
                    if config.ACCOUNT_NUMBER:
                        if mt5.login(config.ACCOUNT_NUMBER, config.ACCOUNT_PASSWORD, config.BROKER_SERVER):
                            self._connected = True
                            logger.info("Reconnection successful")
                            return True
                    else:
                        # If no login needed (just terminal init)
                        self._connected = True
                        logger.info("Reconnection successful (no login)")
                        return True
                
                time.sleep(backoff)
                backoff *= 2.0  # Exponential backoff
                
            logger.error("Reconnection failed after all attempts")
            return False
