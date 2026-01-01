from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from dotenv import load_dotenv
import logging
import os
import redis.asyncio as redis

load_dotenv()

logger = logging.getLogger(__name__)


# AsyncRedisSaver Config
class RedisCheckpoint:
    _redis_saver: AsyncRedisSaver = None
    _redis_context = None

    @classmethod
    async def get_saver(cls) -> AsyncRedisSaver:
        if cls._redis_saver is None:
            # Use contextlib to manually enter context manager
            cls._redis_context = AsyncRedisSaver.from_conn_string(
                os.getenv("LOCAL_REDIS_URL"),
                connection_args={"max_connections": 100}
            )
            cls._redis_saver = (
                await cls._redis_context.__aenter__()
            )  # Actually get the AsyncRedisSaver instance
            await cls._redis_saver.setup()
        return cls._redis_saver

    @classmethod
    async def close_connection(cls):
        logger.info("Closing Redis connection...")
        if cls._redis_context:
            try:
                await cls._redis_context.__aexit__(
                    None, None, None
                )  # Close the context manually
            except Exception:
                pass
            cls._redis_context = None
            cls._redis_saver = None

    @classmethod
    async def delete_thread_memory(cls, thread_id: str):
        """Deletes all checkpoint data for a specific thread_id (Async)"""
        try:
            url = os.getenv("LOCAL_REDIS_URL")
            if not url:
                return
            
            # Use async redis client
            client = redis.from_url(url)
            
            # Pattern match for LangGraph checkpoint keys
            # Note: RedisSaver keys usually look like [namespace, thread_id, ...] encoded
            # If checking keys manually, better to use *{thread_id}* if we are sure of uniqueness
            # But let's try the standard LangGraph RedisSaver key structure
            patterns = [
                f"checkpoint:/*{thread_id}*",
                f"checkpoint_writes:/*{thread_id}*",
                f"*{thread_id}*" # Catch-all for safety if namespace prefix varies
            ]
            
            count = 0
            for pattern in patterns:
                keys = await client.keys(pattern)
                logger.info(f"Found {len(keys)} keys for pattern {pattern}")
                if keys:
                    await client.delete(*keys)
                    count += len(keys)
                    
            logger.info(f"🧹 Deleted {count} redis keys for thread {thread_id}")
            await client.close()
            
        except Exception as e:
            logger.error(f"❌ Error deleting thread memory for {thread_id}: {e}")

