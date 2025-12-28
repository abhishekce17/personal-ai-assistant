from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv
import os
import psycopg
from psycopg import sql

load_dotenv()

# Ensure we use the async driver
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and not DATABASE_URL.startswith("postgresql+psycopg"):
    # Allow pure 'postgresql://' to be upgraded, but user should generally set it right in env
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")


class DBEngine:
    """Singleton for Async DB Engine + Session Factory"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBEngine, cls).__new__(cls)
            cls._engine = create_async_engine(
                DATABASE_URL,
                #echo=True, # Set to False in production
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_timeout=30,
            )
            cls.AsyncSessionLocal = async_sessionmaker(
                bind=cls._engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False 
            )
        return cls._instance

    @property
    def engine(self):
        return self._engine


async def get_db_session() -> AsyncSession:
    """Dependency for FastAPI Routes usually"""
    async_session_factory = DBEngine().AsyncSessionLocal
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Global Engine Instance (for startup events if needed)
engine = DBEngine().engine

async def check_and_create_db():
    """
    Checks if the database exists and creates it if not.
    Uses ASYNC psycopg connection to ensure the event loop is not blocked.
    """

    url = os.getenv("DATABASE_URL")
    if not url:
        return
    
    try:
        # 1. Parse connection details
        target_db_name = url.split("/")[-1]
        if "?" in target_db_name:
             target_db_name = target_db_name.split("?")[0]

        if "postgresql+psycopg://" in url:
             base_url = url.replace("postgresql+psycopg://", "postgresql://")
        else:
             base_url = url
             
        postgres_url = base_url.rsplit("/", 1)[0] + "/postgres"

        # 2. Connect asynchronously to 'postgres' system DB
        # Note: 'await psycopg.AsyncConnection.connect'
        async with await psycopg.AsyncConnection.connect(postgres_url, autocommit=True) as conn:
            async with conn.cursor() as cur:
                # 3. Check if target DB exists
                await cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db_name,))
                exists = await cur.fetchone()

                if not exists:
                    print(f"🛠️ Database '{target_db_name}' not found. Creating (Async)...", flush=True)
                    # 4. Create DB
                    await cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db_name)))
                    print(f"✅ Database '{target_db_name}' created successfully.", flush=True)
                else:
                    print(f"✅ Database '{target_db_name}' already exists.", flush=True)

    except Exception as e:
        print(f"⚠️  Database check/creation warning: {e}", flush=True)
        print("   Continuing startup, assuming database might be ready or unreachable from this check.", flush=True)
