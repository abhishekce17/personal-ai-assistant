from db.models import Base  # Make sure all models are imported
from db.db import engine


def init_db():
    Base.metadata.create_all(bind=engine)
