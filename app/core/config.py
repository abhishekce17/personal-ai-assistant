from langgraph.checkpoint.redis import RedisSaver
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logger = logging.getLogger(__name__)


# RedisSaver Config
class RedisCheckpoint:
    _redis_saver: RedisSaver = None
    _redis_context = None

    @classmethod
    def get_saver(cls) -> RedisSaver:
        if cls._redis_saver is None:
            # Use contextlib to manually enter context manager
            cls._redis_context = RedisSaver.from_conn_string(
                os.getenv("LOCAL_REDIS_URL")
            )
            cls._redis_saver = (
                cls._redis_context.__enter__()
            )  # Actually get the RedisSaver instance
            cls._redis_saver.setup()
        return cls._redis_saver

    @classmethod
    def close_connection(cls):
        logger.info("Closing Redis connection...")
        if cls._redis_context:
            try:
                cls._redis_context.__exit__(
                    None, None, None
                )  # Close the context manually
            except Exception:
                pass
            cls._redis_context = None
            cls._redis_saver = None

    @classmethod
    def delete_thread_memory(cls, thread_id: str):
        """Deletes all checkpoint data for a specific thread_id"""
        try:
            url = os.getenv("LOCAL_REDIS_URL")
            if not url:
                return
            
            # Create a temporary sync connection for cleanup
            import redis
            client = redis.from_url(url)
            
            # Pattern match for LangGraph checkpoint keys
            # Default namespace is usually "checkpoint"
            # Keys are typically: checkpoint:{thread_id}:... and checkpoint_writes:{thread_id}:...
            
            # We use a safe pattern including the thread_id
            # Note: This assumes standard langgraph key structure.
            patterns = [
                f"checkpoint:{{{thread_id}}}:*",
                f"checkpoint_writes:{{{thread_id}}}:*"
            ]
            
            count = 0
            for pattern in patterns:
                keys = client.keys(pattern)
                if keys:
                    client.delete(*keys)
                    count += len(keys)
                    
            logger.info(f"🧹 Deleted {count} redis keys for thread {thread_id}")
            client.close()
            
        except Exception as e:
            logger.error(f"❌ Error deleting thread memory for {thread_id}: {e}")

