from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class VideoRequest(BaseModel):
    """
    Represents the user's request to create an AI-generated video.

    This model is the input contract for the video-generation workflow.
    The frontend/API layer will create this object and pass it to
    the Planner Agent.
    """

    prompt: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Natural-language description of the video to create.",
    )

    duration: int = Field(
        ...,
        ge=10,
        le=600,
        description="Requested video duration in seconds.",
    )

    style: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Desired visual or presentation style.",
    )

    target_audience: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Intended audience for the video.",
    )

    tone: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Desired communication tone.",
    )

    supporting_files: List[str] = Field(
        default_factory=list,
        description=(
            "References to files uploaded through the document/asset "
            "module."
        ),
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        """
        Prevent blank prompts even when whitespace is supplied.
        """
        value = value.strip()

        if not value:
            raise ValueError("prompt must not be blank")

        return value