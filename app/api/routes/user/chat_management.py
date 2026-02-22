from fastapi import APIRouter, HTTPException, status, Depends, Request
from db.models import User, ChatSession, UserChatSessionRetrieve, ChatInteraction
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from sqlalchemy import select, desc, delete, func
from typing import List
from app.core.config import RedisCheckpoint
from app.services.chat_history import ChatHistoryService

router = APIRouter()


@router.get("/list")
async def get_user_chat_sessions(
    request: Request,
    user: User = Depends(get_current_user),
    search: str = None,
    limit: int = 10,
    offset: int = 0,
):
    db: AsyncSession = request.state.db
    
    # Base filter: user's sessions only
    base_filter = ChatSession.user_id == user.id
    
    # Optional search filter on topic (matches any word independently)
    if search:
        from sqlalchemy import or_
        # Standardize space encoding (handle both '+' and '%20')
        normalized_search = search.replace("+", " ").strip().lower()
        search_terms = []
        for word in normalized_search.split():
            if term := word.strip():
                search_terms.append(ChatSession.topic.ilike(f"%{term}%"))
        
        if search_terms:
            base_filter = base_filter & or_(*search_terms)
    
    # Optimized query selecting only required fields
    query = (
        select(
            ChatSession.id,
            ChatSession.thread_id,
            ChatSession.topic,
            ChatSession.pinned,
            ChatSession.updated_at
        )
        .where(base_filter)
        .order_by(
            desc(ChatSession.pinned).nulls_last(),
            desc(ChatSession.updated_at)
        )
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(query)
    chat_sessions = result.mappings().all()
    
    return {
        "success": True,
        "data": chat_sessions,
        "has_more": len(chat_sessions) == limit
    }


@router.get("/history/{thread_id}")
async def get_chat_history(
    thread_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    db: AsyncSession = request.state.db

    # Verify the session exists and belongs to the user
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

    # Get total message count for pagination metadata
    total_count_result = await db.execute(
        select(func.count(ChatInteraction.id))
        .where(ChatInteraction.thread_id == thread_id)
    )
    total_count = total_count_result.scalar() or 0

    # Fetch paginated, decrypted messages
    messages = await ChatHistoryService.get_session_history(
        user.id, thread_id, limit=limit, offset=offset
    )

    return {
        "success": True,
        "data": {
            "id": session.id,
            "thread_id": thread_id,
            "topic": session.topic,
            "messages": messages
        },
        "pagination": {
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1,
            "current_page": (offset // limit) + 1 if limit > 0 else 1,
            "limit": limit,
            "offset": offset
        }
    }

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
    
    return {"success": True, "data": None, "message": "Chat session deleted successfully"}


@router.patch("/pin/{thread_id}")
async def toggle_pin_chat_session(
    thread_id: str,
    pin: bool,
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
        from datetime import datetime
        session.pinned = datetime.utcnow() if pin else None
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error switching pin status: {str(e)}"
        )
    
    return {
        "success": True, 
        "data": {"pinned": session.pinned}, 
        "message": "Chat session pinned" if pin else "Chat session unpinned"
    }
