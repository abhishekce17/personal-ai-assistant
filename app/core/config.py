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
