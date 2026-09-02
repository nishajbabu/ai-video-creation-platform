"""
Schemas used for the Agentic AI -> AI Media Generation handoff.

These schemas define the stable contract consumed by the
AI Media Generation module.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class MediaGenerationSceneInput(BaseModel):
    """
    Scene information required by the AI Media Generation module.
    """

    scene_id: int = Field(
        ...,
        description="Unique identifier of the scene.",
    )

    narration: str = Field(
        ...,
        description="Narration that should be converted into audio.",
    )

    visual_prompt: str = Field(
        ...,
        description="Prompt describing the visual content to generate.",
    )

    voice: Optional[str] = Field(
        default=None,
        description=(
            "Optional voice identifier selected for narration "
            "generation."
        ),
    )


class MediaGenerationInput(BaseModel):
    """
    Complete media-generation input for one generated video.
    """

    video_id: str = Field(
        ...,
        description="Unique identifier of the generated video.",
    )

    project_id: str = Field(
        ...,
        description="Project that owns the generated video.",
    )

    scenes: List[MediaGenerationSceneInput] = Field(
        ...,
        min_length=1,
        description=(
            "Ordered scene inputs consumed by the AI Media "
            "Generation module."
        ),
    )