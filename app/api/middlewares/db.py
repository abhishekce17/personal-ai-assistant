from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import DBEngine
import logging

logger = logging.getLogger("uvicorn.error")


async def db_session_middleware_with_exception_handling(request: Request, call_next):
    # Use the new AsyncSessionLocal factory
    db: AsyncSession = DBEngine().AsyncSessionLocal()
    request.state.db = db
    
    try:
        response = await call_next(request)
        
        if 200 <= response.status_code < 400:
            await db.commit()
        else:
            await db.rollback()
            
        return response

    except Exception as e:
        await db.rollback()
        logger.error(f"[DB] Rolled back due to error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal Server Error",
                "detail": str(e),  # remove in production
            },
        )
    finally:
        await db.close()
        logger.debug("[DB] Session closed")
