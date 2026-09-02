"""
Video database model.

This module defines the persistent Video entity.

The SQLAlchemy model is intentionally separate from
app.schemas.video, which is responsible for API validation
and serialization.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class VideoModel(Base):
    """
    Persistent generated-video entity.

    A video belongs to a project and represents the output of the
    video-generation workflow.
    """

    __tablename__ = "videos"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    video_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    project_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("projects.project_id"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Video information
    # ------------------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued",
    )

    resolution: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1920x1080",
    )

    fps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )

    # ------------------------------------------------------------------
    # Generated files
    # ------------------------------------------------------------------

    file_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    thumbnail_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )