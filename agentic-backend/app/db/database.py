"""
Database configuration and SQLAlchemy base.

This module provides the shared SQLAlchemy declarative base and
database engine configuration used by the application's database
models.

The database URL can be configured through the DATABASE_URL
environment variable.

Default:
    SQLite database stored in agentic_backend.db
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./agentic_backend.db",
)


# ---------------------------------------------------------------------------
# SQLAlchemy engine
# ---------------------------------------------------------------------------

# SQLite requires this option when the same database connection may
# be accessed from different threads, which can happen with FastAPI.
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy database models.
    """

    pass


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

def create_tables() -> None:
    """
    Create all registered database tables.

    Models must be imported before this function is called so that
    SQLAlchemy knows about their table definitions.
    """

    Base.metadata.create_all(
        bind=engine,
    )