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

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true",
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


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
