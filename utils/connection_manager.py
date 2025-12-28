from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.db import DBEngine
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages database connections for WebSocket connections"""

    def __init__(self):
        self._active_connections = {}

    async def get_connection(self, id: str) -> AsyncSession:
        """
        Get or create a database connection for a user.
        Reuses existing connection if available.
        """
        if id in self._active_connections:
            session = self._active_connections[id]
            # Check if session is still valid
            try:
                await session.execute(text("SELECT 1"))
                return session
            except Exception:
                # Session is invalid, remove it
                logger.warning(f"Invalid session found for user {id}, creating new one")
                await self._remove_connection(id)

        # Create new session
        async_session_factory = DBEngine().AsyncSessionLocal
        session = async_session_factory()
        self._active_connections[id] = session
        logger.debug(f"Created new database session for user {id}")
        return session

    async def _remove_connection(self, id: str):
        """Remove and close a user's database connection"""
        if id in self._active_connections:
            try:
                session = self._active_connections[id]
                await session.close()
                del self._active_connections[id]
                logger.debug(f"Closed database session for user {id}")
            except Exception as e:
                logger.error(f"Error closing database session for user {id}: {e}")

    async def close_connection(self, id: str):
        """Public method to close a user's connection"""
        await self._remove_connection(id)

    async def close_all_connections(self):
        """Close all active connections (useful for shutdown)"""
        user_ids = list(self._active_connections.keys())
        for id in user_ids:
            await self._remove_connection(id)
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
        session = await db_connection_manager.get_connection(id)
        yield session
    except Exception as e:
        logger.error(f"Database session error for user {id}: {e}")
        # Remove the problematic connection
        await db_connection_manager.close_connection(id)
        raise
    # Note: We don't close the session here as it's reused
