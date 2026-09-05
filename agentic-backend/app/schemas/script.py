from typing import List

from pydantic import BaseModel, Field, field_validator, model_validator


class ScriptScene(BaseModel):
    """
    Represents the script content for one video scene.

    The Script Agent uses the VideoPlan to create one ScriptScene
    for each planned scene.
    """

    scene_id: int = Field(
        ...,
        ge=1,
        description="Unique identifier of the scene.",
    )

    purpose: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Purpose of the scene within the overall video.",
    )

    duration: int = Field(
        ...,
        ge=1,
        le=600,
        description="Target duration of the scene in seconds.",
    )

    narration: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Narration or spoken content for the scene.",
    )

    @field_validator("purpose", "narration")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """
        Prevent blank text values.
        """
        value = value.strip()

        if not value:
            raise ValueError("text fields must not be blank")

        return value


class Script(BaseModel):
    """
    Complete scene-by-scene script produced by the Script Agent.
    """

    scenes: List[ScriptScene] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Ordered list of scripted scenes.",
    )

    @model_validator(mode="after")
    def validate_scene_ids(self):
        """
        Ensure every scene has a unique scene ID.
        """
        scene_ids = [scene.scene_id for scene in self.scenes]

        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("scene_id values must be unique")

        return self

    @property
    def total_duration(self) -> int:
        """
        Calculate the total duration of all scripted scenes.
        """
        return sum(scene.duration for scene in self.scenes)