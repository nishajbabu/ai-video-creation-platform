"""
Project database model.

This module defines the persistent Project entity used by the
database layer.

The SQLAlchemy model is intentionally separate from
app.schemas.project, which is responsible for API validation
and serialization.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ProjectModel(Base):
    """
    Persistent project entity.

    Each project represents one video-generation workspace.
    """

    __tablename__ = "projects"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    project_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    # ------------------------------------------------------------------
    # Project information
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )