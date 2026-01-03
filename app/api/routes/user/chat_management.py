from fastapi import APIRouter, HTTPException, status, Depends, Request
from db.models import User, ChatSession, UserChatSessionRetrieve, ChatInteraction
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from sqlalchemy import select, desc, delete
from typing import List
from app.core.config import RedisCheckpoint

router = APIRouter()


@router.get("/list", response_model=List[UserChatSessionRetrieve])
async def get_user_chat_sessions(
    request: Request,
    user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    db: AsyncSession = request.state.db
    
    # Optimized query selecting only required fields
    query = (
        select(
            ChatSession.id,
            ChatSession.thread_id,
            ChatSession.topic,
            ChatSession.updated_at
        )
        .where(ChatSession.user_id == user.id)
        .order_by(desc(ChatSession.updated_at))
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(query)
    chat_sessions = result.mappings().all()
    
    return chat_sessions

@router.delete("/delete/{thread_id}")
async def delete_chat_session(
    thread_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    db: AsyncSession = request.state.db
    
    # Check if session exists and belongs to user
    result = await db.execute(
        select(ChatSession).where(
            (ChatSession.thread_id == thread_id) & 
            (ChatSession.user_id == user.id)
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    try:
        # 1. Delete all interactions for this thread
        # safe to do because we verified the session belongs to the user above
        await db.execute(
            delete(ChatInteraction).where(ChatInteraction.thread_id == thread_id)
        )

        # 2. Delete from Postgres
        await db.delete(session)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting chat session: {str(e)}"
        )
    
    # 3. Delete from Redis
    # This happens after DB commit to ensure data consistency
    await RedisCheckpoint.delete_thread_memory(thread_id)
    
    return {"success": True, "message": "Chat session deleted successfully"}
