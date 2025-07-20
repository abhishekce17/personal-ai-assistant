from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from db.db import DBEngine
import logging

logger = logging.getLogger("uvicorn.error")


async def db_session_middleware_with_exception_handling(request: Request, call_next):
    db: Session = DBEngine().SessionLocal()
    try:
        request.state.db = db  # Attach session to request
        response = await call_next(request)
        db.commit()
        return response
    except Exception as e:
        db.rollback()
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
        db.close()
        logger.debug("[DB] Session closed")
