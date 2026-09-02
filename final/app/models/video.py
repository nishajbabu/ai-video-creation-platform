from sqlalchemy import Column, Integer, String, Float

from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(
        String,
        nullable=False
    )

    total_duration = Column(
        Float,
        default=0.0
    )