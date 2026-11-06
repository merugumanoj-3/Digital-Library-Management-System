"""
Database configuration – SQLAlchemy sync engine.
Uses asyncpg dialect for PostgreSQL (postgresql+asyncpg://...)
but accessed synchronously via run_sync pattern in tests.
For production: set DATABASE_URL=postgresql+asyncpg://...
For testing: SQLite is used via the test override.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings


def _build_sync_url(url: str) -> str:
    """Convert async DB URLs to sync equivalents for SQLAlchemy sync engine."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgresql://") or url.startswith("sqlite"):
        return url
    return url


SYNC_URL = _build_sync_url(settings.DATABASE_URL)

engine = create_engine(
    SYNC_URL,
    pool_pre_ping=True,
    # SQLite specific: allow same thread
    connect_args={"check_same_thread": False} if "sqlite" in SYNC_URL else {},
    pool_size=5 if "sqlite" not in SYNC_URL else 1,
    max_overflow=10 if "sqlite" not in SYNC_URL else 0,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
