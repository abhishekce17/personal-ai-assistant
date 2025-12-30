import logging
import os
import uuid
from datetime import datetime
from langchain_core.documents import Document
from sqlalchemy import select
import asyncio
from app.core.security import encrypt_value, decrypt_value
from db.db import DBEngine
from db.models import ChatInteraction, ChatSession
import json
from sqlalchemy.exc import IntegrityError

from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class ChatHistoryService:
    """
    Service to handle the Dual-Persistence of Chat History.
    1. 'Cold' Storage: PostgreSQL (Encrypted) for exact history.
    2. 'Hot' Storage: Redis (Already handled by Checkpointer).
    3. 'Long-Term' Storage: Qdrant (Vector) for RAG Search.
    """

    # @staticmethod
    # async def get_session_background(user_id: str, thread_id: str):
    #     """
    #     Async retrieval of chat session.
    #     Uses AsyncSession directly (Non-blocking).
    #     """
    #     if not thread_id:
    #          return None, None

    #     async_session_factory = DBEngine().AsyncSessionLocal
    #     async with async_session_factory() as db:
    #         try:
    #             # Specific Thread
    #             stmt = select(ChatSession).where(
    #                 (ChatSession.user_id == user_id) &
    #                 (ChatSession.thread_id == thread_id)
    #             )
    #             result = await db.execute(stmt)
    #             session = result.scalars().first()

    #             if session:
    #                 try:
    #                     decrypted_content = decrypt_value(session.content)
    #                     return session.thread_id, decrypted_content
    #                 except Exception as e:
    #                     logger.error(f"Failed to decrypt session {session.thread_id}: {e}")
    #                     return None, None
    #             return None, None
    #         except Exception as e:
    #             logger.error(f"Failed to fetch session: {e}")
    #             return None, None

    @staticmethod
    async def _save_to_sql_async(
        user_id: str,
        thread_id: str,
        user_message: str,
        ai_response: str,
        topic: str = None
    ) -> str:
        """
        Saves a Q&A pair to the SQL database using the normalized schema.
        - Creates a ChatSession if it doesn't exist.
        - Appends a new ChatInteraction row.
        """
        async_session_factory = DBEngine().AsyncSessionLocal
        async with async_session_factory() as db:
            try:
                timestamp = datetime.utcnow()

                interaction_data = {
                    "user": user_message,
                    "ai": ai_response,
                    "timestamp": timestamp.isoformat()
                }
                
                # Encrypt the JSON payload (CPU bound, but fast for small JSON)
                json_payload = json.dumps(interaction_data)
                encrypted_content = encrypt_value(json_payload)

                # 2. Check if the Session (Thread) already exists
                # We use a simple select first to avoid locking if we don't have to
                stmt = select(ChatSession).where(ChatSession.thread_id == thread_id)
                result = await db.execute(stmt)
                session = result.scalars().first()

                if session:
                    if topic and session.topic != topic:
                        session.topic = topic
                    
                    new_interaction = ChatInteraction(
                        thread_id=thread_id,  # Links to the session via thread_id
                        content=encrypted_content,
                    )
                    db.add(new_interaction)
                    
                else:
                    # --- SCENARIO B: NEW CHAT ---
                    # We need to create the "Folder" (Session) AND the first "File" (Interaction)
                    
                    new_session = ChatSession(
                        user_id=user_id,
                        thread_id=thread_id,
                        topic=topic or "New Conversation",
                    )
                    db.add(new_session)
                    
                    new_interaction = ChatInteraction(
                        thread_id=thread_id,
                        content=encrypted_content,
                    )
                    db.add(new_interaction)

                await db.commit()
                logger.info(f"✅ [SQL] Saved Interaction to thread {thread_id}")
                return timestamp.isoformat()

            except IntegrityError:
                logger.warning(f"⚠️ Race condition detected for thread {thread_id}. Retrying save...")
                await db.rollback()
                return await _save_to_sql_async(
                    user_id, thread_id, user_message, ai_response, topic
                )

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
                print({"documents" : documents})
                await vector_store.aadd_documents(documents)
                logger.info("✅ [Vector] Saved to Qdrant")
            except Exception as e:
                logger.error(f"❌ [Vector Failed]: {e}")
        else:
            if os.getenv("QDRANT_URL"):
                 logger.error("⚠️ Failed to get Qdrant store instance.")
