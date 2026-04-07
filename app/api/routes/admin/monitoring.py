from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func, select
from db.models import User, ChatSession, FederatedIdentity
from app.api.routes.user.chat_interaction import UserAgentManager
from app.core.security import require_admin_role_ids
from dotenv import load_dotenv
import redis.asyncio as aioredis
import platform
import httpx
import time
import os

load_dotenv()

MASTER_ADMIN_ID = os.getenv("MASTER_ADMIN_ID")
LOCAL_REDIS_URL = os.getenv("LOCAL_REDIS_URL", "redis://localhost:6379")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1")

router = APIRouter()

# Track server start time
_server_start_time = time.time()


@router.get("/health", summary="Full server health check")
async def server_health(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    """
    Returns health status of all services: Database, Redis, Ollama, and system info.
    """
    db: AsyncSession = request.state.db

    results = {
        "database": await _check_database(db),
        "redis": await _check_redis(),
        "ollama": await _check_ollama(),
        "system": _get_system_info(),
    }

    all_healthy = all(
        results[service].get("status") == "healthy"
        for service in ["database", "redis", "ollama"]
    )

    return {
        "success": True,
        "overall_status": "healthy" if all_healthy else "degraded",
        "services": results,
    }


@router.get("/stats", summary="Application statistics")
async def app_stats(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    """
    Returns application-level statistics: user counts, chat sessions, etc.
    """
    db: AsyncSession = request.state.db

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar() or 0
    verified_users = (await db.execute(select(func.count(User.id)).where(User.is_verified == True))).scalar() or 0
    total_sessions = (await db.execute(select(func.count(ChatSession.id)))).scalar() or 0
    total_tool_links = (await db.execute(select(func.count(FederatedIdentity.id)).where(FederatedIdentity.is_active == True))).scalar() or 0

    return {
        "success": True,
        "data": {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
                "inactive": total_users - active_users,
            },
            "chat_sessions": total_sessions,
            "tool_links": total_tool_links,
            "active_connections": UserAgentManager.get_active_connections_count(),
            "uptime_seconds": round(time.time() - _server_start_time),
        }
    }


# ─── Internal Health Check Helpers ───


async def _check_database(db: AsyncSession) -> dict:
    try:
        start = time.time()
        await db.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start) * 1000, 2)
        return {"status": "healthy", "latency_ms": latency_ms}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _check_redis() -> dict:
    try:
        start = time.time()
        client = aioredis.from_url(LOCAL_REDIS_URL)
        pong = await client.ping()
        info = await client.info("memory")
        latency_ms = round((time.time() - start) * 1000, 2)
        await client.close()
        return {
            "status": "healthy" if pong else "unhealthy",
            "latency_ms": latency_ms,
            "used_memory": info.get("used_memory_human", "N/A"),
            "peak_memory": info.get("used_memory_peak_human", "N/A"),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _check_ollama() -> dict:
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"http://{OLLAMA_HOST}:11434/api/tags")
        latency_ms = round((time.time() - start) * 1000, 2)

        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "loaded_models": [m.get("name") for m in models],
            }
        return {"status": "unhealthy", "status_code": response.status_code}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def _get_system_info() -> dict:
    try:
        load_1, load_5, load_15 = os.getloadavg()
    except (OSError, AttributeError):
        load_1 = load_5 = load_15 = None

    return {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "load_avg": {
            "1min": load_1,
            "5min": load_5,
            "15min": load_15,
        } if load_1 is not None else "N/A (Windows)",
        "uptime_seconds": round(time.time() - _server_start_time),
    }
