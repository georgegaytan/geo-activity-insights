import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@db:5432/geo_activities",
)

# Shared engine instance used across the application
engine = create_engine(DATABASE_URL, future=True)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)

# Base declarative class
Base = declarative_base()


def get_db() -> Session:
    """Yield a SQLAlchemy Session for FastAPI dependencies."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
