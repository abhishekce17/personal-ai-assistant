from app.core.config import RedisCheckpoint
from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.base import init_db
from db.db import engine
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("🔼 Database initialized")

    yield

    logger.info("🔄 Starting application shutdown...")
    from app.api.routes.user.chat_interaction import UserAgentManager

    UserAgentManager.cleanup_all()  # 🔐 Proper Redis close
    await RedisCheckpoint.close_connection()
    engine.dispose()
    logger.info("🔻 Database and Redis connections closed")
