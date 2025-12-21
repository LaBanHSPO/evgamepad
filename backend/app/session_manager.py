import logging
from typing import Dict, Any, Optional
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class SessionManager:
    """Manage Socket.IO client sessions"""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def create_session(self, sid: str, initial_data: Dict[str, Any] = None):
        """Create new session for client"""
        with self._lock:
            self.sessions[sid] = initial_data or {}
            logger.debug(f"Session created: {sid}")

    def get_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        with self._lock:
            return self.sessions.get(sid)

    def update_session(self, sid: str, data: Dict[str, Any]):
        """Update session data"""
        with self._lock:
            if sid in self.sessions:
                self.sessions[sid].update(data)
                logger.debug(f"Session updated: {sid}")

    def remove_session(self, sid: str):
        """Remove session"""
        with self._lock:
            if sid in self.sessions:
                del self.sessions[sid]
                logger.debug(f"Session removed: {sid}")

    def add_pending_order(self, sid: str, order_id: str, order_data: Dict[str, Any]):
        """Track pending order for session"""
        with self._lock:
            session = self.sessions.get(sid)
            if session:
                if 'pending_orders' not in session:
                    session['pending_orders'] = {}
                session['pending_orders'][order_id] = {
                    'data': order_data,
                    'timestamp': datetime.utcnow(),
                }

    def remove_pending_order(self, sid: str, order_id: str):
        """Remove pending order"""
        with self._lock:
            session = self.sessions.get(sid)
            if session and 'pending_orders' in session:
                session['pending_orders'].pop(order_id, None)

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all sessions (for debugging)"""
        with self._lock:
            return self.sessions.copy()
