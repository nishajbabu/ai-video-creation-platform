from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Text,
    ForeignKey,
)

from app.database import Base


class Timeline(Base):
    __tablename__ = "timeline"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    video_id = Column(
        Integer,
        ForeignKey("videos.id"),
        nullable=False
    )

    scene_id = Column(
        Integer,
        ForeignKey("scenes.id"),
        nullable=False
    )

    start_time = Column(
        Float,
        nullable=False
    )

    end_time = Column(
        Float,
        nullable=False
    )

    transition = Column(
        String,
        nullable=True
    )

    text_overlay = Column(
        Text,
        nullable=True
    )