import logging
import os
import uuid
from datetime import datetime
from langchain_core.documents import Document

# --- Imports (Dependencies) ---
import asyncio
from app.core.security import encrypt_value, decrypt_value
from db.db import DBEngine
from db.models import ChatSessionEmbedding

from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class ChatHistoryService:
    """
    Service to handle the Dual-Persistence of Chat History.
    1. 'Cold' Storage: PostgreSQL (Encrypted) for exact history.
    2. 'Hot' Storage: Redis (Already handled by Checkpointer).
    3. 'Long-Term' Storage: Qdrant (Vector) for RAG Search.
    """



    
    @staticmethod
    async def get_session_background(user_id: str, thread_id: str):
        """
        Async retrieval of chat session.
        Uses AsyncSession directly (Non-blocking).
        """
        if not thread_id:
             return None, None

        async_session_factory = DBEngine().AsyncSessionLocal
        async with async_session_factory() as db:
            try:
                # Specific Thread
                stmt = select(ChatSessionEmbedding).where(
                    (ChatSessionEmbedding.user_id == user_id) &
                    (ChatSessionEmbedding.thread_id == thread_id)
                )
                result = await db.execute(stmt)
                session = result.scalars().first()

                if session:
                    try:
                        decrypted_content = decrypt_value(session.content)
                        return session.thread_id, decrypted_content
                    except Exception as e:
                        logger.error(f"Failed to decrypt session {session.thread_id}: {e}")
                        return None, None
                return None, None
            except Exception as e:
                logger.error(f"Failed to fetch session: {e}")
                return None, None

    @staticmethod
    async def _save_to_sql_async(
        user_id: str,
        thread_id: str,
        user_message: str,
        ai_response: str,
        topic: str = None
    ) -> str:
        """
        Non-blocking SQL save using AsyncSession.
        """
        async_session_factory = DBEngine().AsyncSessionLocal
        async with async_session_factory() as db:
            try:
                timestamp = datetime.now().isoformat()
                plain_text_log = f"\n[{timestamp}] User: {user_message}\n[{timestamp}] AI: {ai_response}"
                
                # CPU Bound (Keep in thread if very heavy, but usually fine for short text)
                encrypted_content = encrypt_value(plain_text_log)

                # IO Bound: Database (Async)
                stmt = select(ChatSessionEmbedding).where(ChatSessionEmbedding.thread_id == thread_id).with_for_update()
                result = await db.execute(stmt)
                session_embedding = result.scalars().first()

                if session_embedding:
                    try:
                        current_history = decrypt_value(session_embedding.content) or ""
                        updated_history = current_history + plain_text_log
                        session_embedding.content = encrypt_value(updated_history)
                        session_embedding.updated_at = datetime.now()
                        if topic:
                            session_embedding.topic = topic
                    except Exception as e:
                        logger.error(f"Failed to append to encrypted history: {e}")
                        session_embedding.content = encrypt_value(plain_text_log)
                else:
                    new_session = ChatSessionEmbedding(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        thread_id=thread_id,
                        content=encrypted_content,
                        topic=topic or "New Conversation",
                        is_active=True
                    )
                    db.add(new_session)
                
                await db.commit()
                logger.info("✅ [SQL] Saved Encrypted History (Async)")
                return timestamp
                
            except Exception as e:
                logger.error(f"❌ [SQL Async Failed]: {e}")
                await db.rollback()
                return datetime.now().isoformat()

    @staticmethod
    async def save_interaction_background(
        user_id: str,
        thread_id: str,
        user_message: str,
        ai_response: str,
        topic: str = None
    ):
        """
        FIRE-AND-FORGET Task using native Async DB.
        """
        logger.info(f"⏳ [Background] Saving interaction for Thread: {thread_id}")

        timestamp = await ChatHistoryService._save_to_sql_async(
            user_id, thread_id, user_message, ai_response, topic
        )
        
        # 2. Vector DB (Async Native) - Can stay in main loop
        vector_store = await VectorStoreService.get_qdrant_store()
        
        if vector_store:
            try:
                documents = [
                    Document(
                        page_content=user_message,
                        metadata={
                            "thread_id": thread_id,
                            "role": "user",
                            "user_id": user_id,
                            "timestamp": timestamp
                        }
                    ),
                    Document(
                        page_content=ai_response,
                        metadata={
                            "thread_id": thread_id,
                            "role": "ai",
                            "user_id": user_id,
                            "timestamp": timestamp
                        }
                    )
                ]
                await vector_store.aadd_documents(documents)
                logger.info("✅ [Vector] Saved to Qdrant")
            except Exception as e:
                logger.error(f"❌ [Vector Failed]: {e}")
        else:
            if os.getenv("QDRANT_URL"):
                 logger.error("⚠️ Failed to get Qdrant store instance.")
