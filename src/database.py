"""
Database connection and session management

Technisch ontwerp: Database configuration
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/invoice_db",
)


class _EngineProxy:
    """Proxy object that defers engine creation to first use"""

    def __init__(self):
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            self._engine = create_engine(
                DATABASE_URL,
                echo=os.getenv("SQL_ECHO", "False").lower() == "true",
                pool_pre_ping=True,  # Verify connections before using
                pool_size=10,
                max_overflow=20,
            )
        return self._engine

    def __getattr__(self, name):
        return getattr(self._get_engine(), name)

    def __repr__(self):
        return repr(self._get_engine())


# Lazy-initialized engine (allows testing without PostgreSQL driver)
engine = _EngineProxy()
_SessionLocal = None


def SessionLocal():
    """Create new database session"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine._get_engine(),  # type: ignore
        )
    return _SessionLocal()


def get_db():
    """
    Dependency for getting database session in FastAPI

    Yields:
        Database session for request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from src.models.invoice import Base

    Base.metadata.create_all(bind=engine)
