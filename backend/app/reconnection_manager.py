
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class ReconnectionManager:
    """
    Manage client reconnection and session recovery
    """

    def __init__(self, session_ttl: int = 300):
        """
        Initialize reconnection manager

        Args:
            session_ttl: Session time-to-live in seconds (default 5 minutes)
        """
        self.session_ttl = session_ttl
        self.disconnected_sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def store_disconnected_session(self, sid: str, session_data: Dict[str, Any]):
        """
        Store session data when client disconnects

        Args:
            sid: Session ID
            session_data: Session state to preserve
        """
        with self._lock:
            self.disconnected_sessions[sid] = {
                'data': session_data,
                'disconnected_at': datetime.utcnow(),
                'pending_orders': session_data.get('pending_orders', {}),
                'reconnection_count': 0,
            }
            logger.info(f"Session {sid} stored for recovery (TTL: {self.session_ttl}s)")

    def recover_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to recover session data

        Args:
            sid: Session ID

        Returns:
            Session data if found and not expired, None otherwise
        """
        with self._lock:
            if sid not in self.disconnected_sessions:
                logger.debug(f"No stored session for {sid}")
                return None

            stored = self.disconnected_sessions[sid]
            disconnected_at = stored['disconnected_at']

            # Check expiration
            if datetime.utcnow() - disconnected_at > timedelta(seconds=self.session_ttl):
                logger.warning(f"Session {sid} expired (TTL exceeded)")
                del self.disconnected_sessions[sid]
                return None

            # Recover session
            logger.info(f"Recovering session {sid}")
            stored['reconnection_count'] += 1
            return stored['data']

    def cleanup_expired_sessions(self):
        """Remove expired disconnected sessions"""
        with self._lock:
            now = datetime.utcnow()
            expired = []

            for sid, stored in self.disconnected_sessions.items():
                disconnected_at = stored['disconnected_at']
                if now - disconnected_at > timedelta(seconds=self.session_ttl):
                    expired.append(sid)

            for sid in expired:
                logger.info(f"Cleaning up expired session {sid}")
                del self.disconnected_sessions[sid]

            return len(expired)

    def get_pending_orders(self, sid: str) -> List[Dict[str, Any]]:
        """
        Get pending orders for session

        Args:
            sid: Session ID

        Returns:
            List of pending orders
        """
        with self._lock:
            if sid in self.disconnected_sessions:
                pending = self.disconnected_sessions[sid].get('pending_orders', {})
                return list(pending.values())
            return []

    def remove_session(self, sid: str):
        """Remove session from storage"""
        with self._lock:
            if sid in self.disconnected_sessions:
                del self.disconnected_sessions[sid]
                logger.debug(f"Removed stored session {sid}")
