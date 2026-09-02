"""
Scene database model.

This module defines the persistent Scene entity used by the
database layer.

The SQLAlchemy model is separate from app.schemas.scene, which
handles API/domain validation and serialization.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SceneModel(Base):
    """
    Persistent scene entity.

    A scene belongs to a generated video and represents one
    individual section of that video.
    """

    __tablename__ = "scenes"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    scene_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    video_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("videos.video_id"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Ordering
    # ------------------------------------------------------------------

    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Scene content
    # ------------------------------------------------------------------

    purpose: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    narration: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    visual_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    visual_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    visual_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="image",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="planned",
    )

    # ------------------------------------------------------------------
    # Asset / audio requirements
    # ------------------------------------------------------------------

    has_asset_requirements: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    has_audio_requirements: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )