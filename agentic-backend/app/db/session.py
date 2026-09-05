"""
Database session dependency.

This module provides the SQLAlchemy session used by FastAPI
routes and application services.

Each request receives its own database session, and the session
is always closed after the request finishes.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for a FastAPI request.

    The session is automatically closed when the request finishes,
    including when an exception occurs.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()