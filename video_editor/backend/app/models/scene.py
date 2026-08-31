from sqlalchemy import Column, Integer, Float, String, ForeignKey
from app.database import Base


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)

    video_id = Column(
        Integer,
        ForeignKey("videos.id"),
        nullable=False
    )

    order = Column(Integer, nullable=False)
    duration = Column(Float, default=5.0)
    title = Column(String, nullable=True)