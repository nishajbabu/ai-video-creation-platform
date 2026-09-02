from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


VideoStatus = Literal[
    "queued",
    "rendering",
    "completed",
    "failed",
]


class Video(BaseModel):
    """
    Represents the final generated video.

    This object is produced after storyboard generation,
    media generation, audio synthesis, and video rendering.
    """

    video_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier of the generated video.",
    )

    project_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Project that owns this video.",
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display title of the generated video.",
    )

    duration: int = Field(
        ...,
        ge=1,
        le=600,
        description="Final video duration in seconds.",
    )

    status: VideoStatus = Field(
        default="queued",
        description="Current rendering status.",
    )

    resolution: str = Field(
        default="1920x1080",
        description="Output resolution.",
    )

    fps: int = Field(
        default=30,
        ge=24,
        le=60,
        description="Frames per second.",
    )

    file_path: Optional[str] = Field(
        default=None,
        description="Location of the rendered video file.",
    )

    thumbnail_path: Optional[str] = Field(
        default=None,
        description="Location of the generated thumbnail.",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the video record was created.",
    )