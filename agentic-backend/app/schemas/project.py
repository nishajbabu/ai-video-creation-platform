from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


ProjectStatus = Literal[
    "draft",
    "planning",
    "generating",
    "completed",
    "failed",
]


class Project(BaseModel):
    """
    Represents a video-generation project.

    A project acts as the high-level container for the
    video creation workflow.
    """

    project_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier of the project.",
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable project name.",
    )

    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional project description.",
    )

    status: ProjectStatus = Field(
        default="draft",
        description="Current state of the project.",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the project was created.",
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the project was last updated.",
    )