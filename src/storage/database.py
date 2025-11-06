"""
Database connection and session management.

This module provides database connection utilities for both SQLite (development)
and PostgreSQL (production).
"""

from typing import Generator
from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base class for all models
Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agenticmath.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
DATABASE_POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))


def create_db_engine(database_url: str | None = None) -> Engine:
    """
    Create a SQLAlchemy engine with appropriate configuration.

    Args:
        database_url: Database connection URL. If None, uses environment variable.

    Returns:
        SQLAlchemy Engine instance
    """
    url = database_url or DATABASE_URL

    # SQLite-specific configuration
    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            echo=DATABASE_ECHO,
            connect_args={"check_same_thread": False},  # Allow multiple threads
        )
    # PostgreSQL-specific configuration
    else:
        engine = create_engine(
            url,
            echo=DATABASE_ECHO,
            pool_size=DATABASE_POOL_SIZE,
            max_overflow=DATABASE_MAX_OVERFLOW,
            pool_timeout=DATABASE_POOL_TIMEOUT,
            pool_pre_ping=True,  # Verify connections before using them
        )

    return engine


# Global engine and session factory
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get a database session.

    Yields:
        Database session that will be automatically closed after use.

    Example:
        ```python
        @app.get("/problems")
        def list_problems(db: Session = Depends(get_db)):
            return db.query(Problem).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in non-FastAPI code.

    Yields:
        Database session that will be automatically closed after use.

    Example:
        ```python
        with get_db_session() as db:
            problem = db.query(Problem).first()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    Note: In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    """
    Drop all tables from the database.

    WARNING: This will delete all data. Only use in development/testing.
    """
    Base.metadata.drop_all(bind=engine)
