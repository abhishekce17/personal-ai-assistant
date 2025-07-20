# server.py - Enhanced with Redis connection cleanup
from routes.user import authentication, user, chat_management, chat_interaction
from middlewares.db import db_session_middleware_with_exception_handling
from routes.admin import authentication as admin_authentication, model_management
from contextlib import asynccontextmanager
from routes.admin import plan_management
from routes.admin import model_feature_tools_plan_mapping
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
    from routes.user.chat_interaction import UserAgentManager
    from main import SocketAgent  # Update import

    UserAgentManager.cleanup_all()
    SocketAgent.cleanup_shared_redis()  # 🔐 Proper Redis close
    engine.dispose()
    logger.info("🔻 Database and Redis connections closed")


app = FastAPI(lifespan=lifespan)
admin = FastAPI(lifespan=lifespan)

app.middleware("http")(db_session_middleware_with_exception_handling)

app.include_router(authentication.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(chat_management.router, prefix="/chat", tags=["Chat Management"])
app.include_router(
    chat_interaction.router, prefix="/interaction", tags=["Chat Interaction"]
)

admin.middleware("http")(db_session_middleware_with_exception_handling)

admin.include_router(admin_authentication.router, prefix="/auth", tags=["Admin Auth"])
admin.include_router(plan_management.router, prefix="/plan", tags=["Plan Management"])
admin.include_router(model_management.router, prefix="/model", tags=["Model Management"])
admin.include_router(model_feature_tools_plan_mapping.router, prefix="/model-feature-tools-plan-mapping", tags=["Model Feature Tools Plan Mapping"])

app.mount(path="/admin", app=admin, name="Admin")

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "message": "Server is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
