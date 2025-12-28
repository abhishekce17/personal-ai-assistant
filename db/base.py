from db.models import Base  # Make sure all models are imported
from db.db import engine


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
