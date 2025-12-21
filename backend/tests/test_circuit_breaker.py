
import unittest
import time
from unittest.mock import MagicMock
from app.mt5.circuit_breaker import CircuitBreaker, CircuitState

class TestCircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.cb = CircuitBreaker(
            failure_threshold=5,
            timeout=1.0,  # Short timeout for testing
            recovery_timeout=0.1
        )

    def test_closed_state_initially(self):
        self.assertEqual(self.cb.state, CircuitState.CLOSED)
        self.assertEqual(self.cb.failure_count, 0)

    def test_failure_counting(self):
        self.cb.record_failure()
        self.assertEqual(self.cb.failure_count, 1)
        self.assertEqual(self.cb.state, CircuitState.CLOSED)

    def test_circuit_opens_after_threshold(self):
        # Fail 5 times
        for _ in range(5):
            self.cb.record_failure()

        self.assertEqual(self.cb.failure_count, 5)
        self.assertEqual(self.cb.state, CircuitState.OPEN)

    def test_rejects_execution_when_open(self):
        self.cb.state = CircuitState.OPEN
        self.cb.last_failure_time = time.time()
        
        with self.assertRaises(RuntimeError):
            self.cb.execute(lambda: True)

    def test_recovery_to_half_open(self):
        self.cb.state = CircuitState.OPEN
        self.cb.last_failure_time = time.time() - 2.0  # Past timeout
        self.cb.failure_count = 5

        # Should transition to half-open
        self.assertTrue(self.cb.can_execute())
        self.assertEqual(self.cb.state, CircuitState.HALF_OPEN)

    def test_success_closes_half_open(self):
        self.cb.state = CircuitState.HALF_OPEN
        
        self.cb.execute(lambda: "success")
        
        self.assertEqual(self.cb.state, CircuitState.CLOSED)
        self.assertEqual(self.cb.failure_count, 0)

    def test_failure_reopens_half_open(self):
        self.cb.state = CircuitState.HALF_OPEN
        
        try:
            self.cb.execute(lambda: exec('raise Exception("fail")'))
        except Exception:
            pass
            
        self.assertEqual(self.cb.state, CircuitState.OPEN)

if __name__ == '__main__':
    unittest.main()
