# server.py - Enhanced with Redis connection cleanup
from middlewares.db import db_session_middleware_with_exception_handling
from contextlib import asynccontextmanager
from routes import authentication, user, chat_management, chat_interaction
from db.base import init_db
from db.db import engine
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("🔼 Database initialized")

    yield

    logger.info("🔄 Starting application shutdown...")
    from routes.chat_interaction import UserAgentManager
    from main import SocketAgent  # Update import

    UserAgentManager.cleanup_all()
    SocketAgent.cleanup_shared_redis()  # 🔐 Proper Redis close
    engine.dispose()
    logger.info("🔻 Database and Redis connections closed")


app = FastAPI(lifespan=lifespan)

app.middleware("http")(db_session_middleware_with_exception_handling)

app.include_router(authentication.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(chat_management.router, prefix="/chat", tags=["Chat Management"])
app.include_router(
    chat_interaction.router, prefix="/interaction", tags=["Chat Interaction"]
)


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "message": "Server is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
