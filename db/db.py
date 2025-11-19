from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from dotenv import load_dotenv
import threading
import psycopg2
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


# Connection details parsed from DATABASE_URL
user = "postgres"
password = "mysecretpassword"
host = "localhost"
port = 5432
target_db = "llm_chat_pdf"

try:
    # Connect to default 'postgres' database
    # conn = psycopg2.connect(
    #     dbname="postgres", user=user, password=password, host=host, port=port
    # )
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()

    # Check if database already exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
    exists = cur.fetchone()

    if not exists:
        cur.execute(f"CREATE DATABASE {target_db}")
        print(f"Database '{target_db}' created successfully.")
    else:
        print(f"Database '{target_db}' already exists.")

    cur.close()
    conn.close()

except Exception as e:
    print("Error:", e)


class DBEngine:
    """Thread-safe singleton for DB engine + session factory"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:  # 🚨 Prevent race condition
                if cls._instance is None:  # Double-check
                    cls._instance = super(DBEngine, cls).__new__(cls)
                    cls._engine = create_engine(
                        DATABASE_URL,
                        echo=True,
                        pool_size=10,
                        max_overflow=20,
                        pool_pre_ping=True,
                        pool_recycle=3600,
                        pool_timeout=30,
                    )
                    cls.SessionLocal = sessionmaker(
                        autocommit=False, autoflush=False, bind=cls._engine
                    )
        return cls._instance

    @property
    def engine(self):
        return self._engine


@asynccontextmanager
async def get_db_session():
    db = DBEngine().SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


engine = DBEngine().engine
