from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class VideoPlan(BaseModel):
    """
    Structured plan produced by the Planner Agent.

    The Planner does not write the final narration.
    Its responsibility is to determine what the video should contain,
    who it is for, how it should be presented, and how the content
    should be divided into scenes.
    """

    objective: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Primary objective of the video.",
    )

    target_audience: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Intended audience for the video.",
    )

    tone: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Communication tone of the video.",
    )

    style: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Visual or presentation style.",
    )

    duration: int = Field(
        ...,
        ge=10,
        le=600,
        description="Target video duration in seconds.",
    )

    scene_count: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of scenes planned for the video.",
    )

    content_requirements: List[str] = Field(
        default_factory=list,
        description="Important topics or information that must appear.",
    )

    generation_notes: List[str] = Field(
        default_factory=list,
        description=(
            "Additional instructions that downstream agents should "
            "consider during generation."
        ),
    )

    @field_validator("objective")
    @classmethod
    def validate_objective(cls, value: str) -> str:
        """
        Prevent an objective containing only whitespace.
        """
        value = value.strip()

        if not value:
            raise ValueError("objective must not be blank")

        return value

    @field_validator("content_requirements", "generation_notes")
    @classmethod
    def clean_string_lists(cls, values: List[str]) -> List[str]:
        """
        Remove surrounding whitespace and reject empty items.
        """
        cleaned_values = []

        for value in values:
            value = value.strip()

            if not value:
                raise ValueError(
                    "content requirement and generation note "
                    "items must not be blank"
                )

            cleaned_values.append(value)

        return cleaned_values