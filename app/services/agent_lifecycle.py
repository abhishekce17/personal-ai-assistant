from app.core.config import RedisCheckpoint
from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.db import check_and_create_db
from db.base import init_db
from db.db import engine
from app.api.routes.user.chat_interaction import UserAgentManager
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Ensure DB exists (Async check)
    await check_and_create_db()
    
    # 2. Init Tables (Async)
    await init_db()
    logger.info("🔼 Database initialized")

    yield

    logger.info("🔄 Starting application shutdown...")
    


    UserAgentManager.cleanup_all()  # 🔐 Proper Redis close
    await RedisCheckpoint.close_connection()
    engine.dispose()
    logger.info("🔻 Database and Redis connections closed")
