# server.py - Enhanced with Redis connection cleanup
from app.api.routes.admin import (
    authentication as admin_authentication,
    model_management,
)
from app.api.routes.user import authentication, user, chat_management, chat_interaction, tool_auth_link, tools_management, staticdata, feature_flag
from app.api.middlewares.db import db_session_middleware_with_exception_handling
from app.api.routes.admin import model_feature_tools_plan_mapping, user_management, tool_management, staticdata_management, feature_flag_management
# from app.api.routes.webhook import tool_installation
from app.services.agent_lifecycle import lifespan
from app.api.routes.admin import plan_management
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

logger = logging.getLogger(__name__)


app = FastAPI(lifespan=lifespan)
admin = FastAPI(lifespan=lifespan)

origins = [
    "https://orvio-admin.vercel.app",
]

# CORS for main app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# CORS for admin app
admin.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


app.middleware("http")(db_session_middleware_with_exception_handling)

app.include_router(authentication.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(chat_management.router, prefix="/chat", tags=["Chat Management"])
app.include_router(
    chat_interaction.router, prefix="/interaction", tags=["Chat Interaction"]
)
# app.include_router(
#     tool_installation.router, prefix="/tool-installation", tags=["Tool Installation"]
# )
app.include_router(
    tool_auth_link.router, prefix="/tool-auth", tags=["Tool Link"]
)
app.include_router(
    tools_management.router, prefix="/tool-management", tags=["Tool Management"]
)
app.include_router(staticdata.router, prefix="/staticdata", tags=["Static Data"])
app.include_router(feature_flag.router, prefix="/feature-flag", tags=["Feature Flag"])

admin.middleware("http")(db_session_middleware_with_exception_handling)

admin.include_router(admin_authentication.router, prefix="/auth", tags=["Admin Auth"])
admin.include_router(plan_management.router, prefix="/plan", tags=["Plan Management"])
admin.include_router(
    model_management.router, prefix="/model", tags=["Model Management"]
)
admin.include_router(
    model_feature_tools_plan_mapping.router,
    prefix="/model-feature-tools-plan-mapping",
    tags=["Model Feature Tools Plan Mapping"],
)
admin.include_router(user_management.router, prefix="/user-management", tags=["User Management"])
admin.include_router(tool_management.router, prefix="/tool-management", tags=["Tool Management"])
admin.include_router(staticdata_management.router, prefix="/staticdata-management", tags=["Static Data Management"])
admin.include_router(feature_flag_management.router, prefix="/feature-flag-management", tags=["Feature Flag Management"])
app.mount(path="/admin", app=admin, name="Admin")


@app.get("/")
async def root():
    """Root endpoint for Hugging Face health checks and UI"""
    return {
        "success": True, 
        "message": "Welcome to Orvio Backend API",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"success": True, "data": {"status": "healthy"}, "message": "Server is running"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
