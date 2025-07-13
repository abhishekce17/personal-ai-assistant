from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from db.db import get_single_db_session
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages database connections for WebSocket connections"""

    def __init__(self):
        self._active_connections = {}

    def get_connection(self, id: str) -> Session:
        """
        Get or create a database connection for a user.
        Reuses existing connection if available.
        """
        if id in self._active_connections:
            session = self._active_connections[id]
            # Check if session is still valid
            try:
                session.execute("SELECT 1")
                return session
            except Exception:
                # Session is invalid, remove it
                logger.warning(f"Invalid session found for user {id}, creating new one")
                self._remove_connection(id)

        # Create new session
        session = get_single_db_session()
        self._active_connections[id] = session
        logger.debug(f"Created new database session for user {id}")
        return session

    def _remove_connection(self, id: str):
        """Remove and close a user's database connection"""
        if id in self._active_connections:
            try:
                session = self._active_connections[id]
                session.close()
                del self._active_connections[id]
                logger.debug(f"Closed database session for user {id}")
            except Exception as e:
                logger.error(f"Error closing database session for user {id}: {e}")

    def close_connection(self, id: str):
        """Public method to close a user's connection"""
        self._remove_connection(id)

    def close_all_connections(self):
        """Close all active connections (useful for shutdown)"""
        user_ids = list(self._active_connections.keys())
        for id in user_ids:
            self._remove_connection(id)
        logger.info(f"Closed all database connections ({len(user_ids)} connections)")


# Global connection manager instance
db_connection_manager = DatabaseConnectionManager()


@asynccontextmanager
async def get_websocket_db_session(id: str):
    """
    Context manager for WebSocket database sessions.
    Automatically handles connection reuse and cleanup.
    """
    session = None
    try:
        session = db_connection_manager.get_connection(id)
        yield session
    except Exception as e:
        logger.error(f"Database session error for user {id}: {e}")
        # Remove the problematic connection
        db_connection_manager.close_connection(id)
        raise
    # Note: We don't close the session here as it's reused
