
import logging
import time
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failed, rejecting requests
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    """
    Circuit breaker pattern for MT5 operations
    Prevents cascading failures from broken MT5 connection
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        recovery_timeout: float = 5.0
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Failures before opening circuit
            timeout: Seconds to wait before attempting recovery
            recovery_timeout: Timeout for recovery attempts
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout

        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker: recovered to CLOSED")

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        # If in HALF_OPEN state, any failure trips the breaker
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker: HALF_OPEN attempt failed -> OPEN"
            )
            return

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker: OPEN (failures: {self.failure_count})"
                )

    def can_execute(self) -> bool:
        """Check if operation can proceed"""

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout expired to attempt recovery
            if self.last_failure_time and time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.failure_count = 0
                logger.info("Circuit breaker: attempting HALF_OPEN recovery")
                return True
            return False

        # HALF_OPEN: allow single attempt
        return True

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            RuntimeError: If circuit is open
            Exception: From executed function
        """
        if not self.can_execute():
            raise RuntimeError(
                f"Circuit breaker is {self.state.value} - operation rejected"
            )

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def get_state(self) -> str:
        """Get current state string"""
        return self.state.value

    def reset(self):
        """Reset circuit breaker"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        logger.info("Circuit breaker reset")
