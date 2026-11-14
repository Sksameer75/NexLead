"""SQLAlchemy Database configuration and session management."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

# Engine configuration with connection pooling and health checks
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Automatically verify connection viability before use
    pool_recycle=3600,       # Recycle connections every hour to avoid stale handles
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

