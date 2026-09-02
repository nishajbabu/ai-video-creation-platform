from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
)

from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    scene_id = Column(
        Integer,
        ForeignKey("scenes.id"),
        nullable=False
    )

    asset_type = Column(
        String,
        nullable=False
    )

    file_url = Column(
        String,
        nullable=False
    )