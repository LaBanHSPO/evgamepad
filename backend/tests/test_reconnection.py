
import unittest
import time
from datetime import datetime, timedelta
from app.reconnection_manager import ReconnectionManager

class TestReconnectionManager(unittest.TestCase):
    def setUp(self):
        self.rm = ReconnectionManager(session_ttl=1) # 1 second TTL

    def test_store_and_recover_session(self):
        sid = "test_sid"
        session_data = {"user": "test", "pending_orders": {}}
        
        self.rm.store_disconnected_session(sid, session_data)
        
        recovered = self.rm.recover_session(sid)
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered['user'], "test")

    def test_session_expiration(self):
        sid = "expired_sid"
        session_data = {"user": "test"}
        
        self.rm.store_disconnected_session(sid, session_data)
        
        # Wait for expiration
        time.sleep(1.1)
        
        recovered = self.rm.recover_session(sid)
        self.assertIsNone(recovered)

    def test_cleanup_task(self):
        self.rm.store_disconnected_session("s1", {})
        self.rm.store_disconnected_session("s2", {})
        
        time.sleep(1.1)
        
        removed = self.rm.cleanup_expired_sessions()
        self.assertEqual(removed, 2)
        self.assertEqual(len(self.rm.disconnected_sessions), 0)

    def test_reconnection_count_increments(self):
        sid = "count_sid"
        self.rm.store_disconnected_session(sid, {})
        
        self.rm.recover_session(sid) # 1st
        self.assertEqual(self.rm.disconnected_sessions[sid]['reconnection_count'], 1)

if __name__ == '__main__':
    unittest.main()
