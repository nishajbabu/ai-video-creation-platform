"""
Asset database model.

This module defines persistent assets used by generated scenes.

Examples:
    - logos
    - product images
    - reference images
    - uploaded media
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AssetModel(Base):
    """
    Persistent asset entity.

    An asset can be associated with a scene and represents a
    file or external resource required during video generation.
    """

    __tablename__ = "assets"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    asset_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    scene_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("scenes.scene_id"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Asset information
    # ------------------------------------------------------------------

    asset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )