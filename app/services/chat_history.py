import logging
import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_core.documents import Document

# --- Imports (Dependencies) ---
import asyncio
from app.core.security import encrypt_value, decrypt_value
from db.db import DBEngine
from db.models import ChatSessionEmbedding

# Try importing Vector DB libraries (Graceful fallback if not installed)
try:
    from langchain_pinecone import PineconeVectorStore
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    PineconeVectorStore = None
    OllamaEmbeddings = None

logger = logging.getLogger(__name__)

class ChatHistoryService:
    """
    Service to handle the Dual-Persistence of Chat History.
    1. 'Cold' Storage: PostgreSQL (Encrypted) for exact history.
    2. 'Hot' Storage: Redis (Already handled by Checkpointer).
    3. 'Long-Term' Storage: Pinecone (Vector) for RAG Search.
    """

    @staticmethod
    def _save_to_sql_sync(
        user_id: str,
        thread_id: str,
        user_message: str,
        ai_response: str,
        topic: str = None
    ) -> str:
        """
        BLOCKING FUNCTION (Run in Thread):
        Handles Encryption (CPU-bound) and SQL (IO-bound).
        Returns timestamp string for metadata.
        """
        db: Session = DBEngine().SessionLocal()
        try:
            timestamp = datetime.now().isoformat()
            plain_text_log = f"\n[{timestamp}] User: {user_message}\n[{timestamp}] AI: {ai_response}"
            
            # CPU Blocking: Encryption
            encrypted_content = encrypt_value(plain_text_log)

            # IO Blocking: Database
            # We use with_for_update() to LOCK this row.
            # If another thread is trying to write to this same session, it must WAIT.
            # This prevents "Lost Update" race conditions.
            session_embedding = db.query(ChatSessionEmbedding).with_for_update().filter(
                ChatSessionEmbedding.thread_id == thread_id
            ).first()

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
                    # embedding_id=str(uuid.uuid4()),  # REMOVED: Now nullable
                    is_active=True
                )
                db.add(new_session)
            
            db.commit()
            logger.info("✅ [SQL] Saved Encrypted History (Threaded)")
            return timestamp
            
        except Exception as e:
            logger.error(f"❌ [SQL Sync Failed]: {e}")
            db.rollback()
            return datetime.now().isoformat()
        finally:
            db.close()

    @staticmethod
    async def save_interaction_background(
        user_id: str,
        thread_id: str,
        user_message: str,
        ai_response: str,
        topic: str = None
    ):
        """
        FIRE-AND-FORGET Task.
        Wrapper that offloads blocking work to a thread.
        """
        logger.info(f"⏳ [Background] Saving interaction for Thread: {thread_id}")

        # 1. Offload Sync/Blocking work (Encryption + SQL) to ThreadPool
        # This prevents blocking the WebSocket Event Loop!
        timestamp = await asyncio.to_thread(
            ChatHistoryService._save_to_sql_sync,
            user_id, thread_id, user_message, ai_response, topic
        )
        
        # 2. Vector DB (Async Native) - Can stay in main loop
        if PineconeVectorStore and os.getenv("PINECONE_API_KEY"):
            try:
                embeddings = OllamaEmbeddings(model="nomic-embed-text")
                vector_store = PineconeVectorStore(
                    index_name=os.getenv("PINECONE_INDEX_NAME", "chat_history"),
                    embedding=embeddings,
                    pinecone_api_key=os.getenv("PINECONE_API_KEY")
                )

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
                logger.info("✅ [Vector] Saved to Pinecone")
            except Exception as e:
                logger.error(f"❌ [Vector Failed]: {e}")
        else:
            if not PineconeVectorStore:
                logger.warning("⚠️ Pinecone libraries not installed.")

    @staticmethod
    def _get_latest_session_sync(user_id: str):
        """
        BLOCKING: Retrieve the most recent chat session for a user.
        Returns: (thread_id, decrypted_content) or (None, None)
        """
        db: Session = DBEngine().SessionLocal()
        try:
            # Get the most recently updated session
            session = db.query(ChatSessionEmbedding).filter(
                ChatSessionEmbedding.user_id == user_id
            ).order_by(ChatSessionEmbedding.updated_at.desc()).first()

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
        finally:
            db.close()

    @staticmethod
    async def get_latest_session_background(user_id: str):
        """
        Async wrapper to fetch history without blocking main loop.
        """
        return await asyncio.to_thread(
            ChatHistoryService._get_latest_session_sync, user_id
        )
