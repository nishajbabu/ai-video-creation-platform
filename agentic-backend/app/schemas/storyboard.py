from typing import List

from pydantic import BaseModel, Field, model_validator

from .scene import Scene


class Storyboard(BaseModel):
    """
    Complete storyboard produced by the Storyboard Agent.

    A storyboard contains the ordered scenes that will later be
    consumed by downstream modules such as asset retrieval,
    media generation, audio generation, video editing, and the frontend.
    """

    scenes: List[Scene] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Ordered list of scenes in the storyboard.",
    )

    @model_validator(mode="after")
    def validate_scene_structure(self):
        """
        Validate relationships between scenes.

        Individual Scene objects are validated by scene.py.
        This validator handles rules that require looking at
        multiple scenes together.
        """

        scene_ids = [scene.scene_id for scene in self.scenes]
        orders = [scene.order for scene in self.scenes]

        # Scene IDs must be unique.
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError(
                "scene_id values must be unique within a storyboard"
            )

        # Timeline order values must be unique.
        if len(orders) != len(set(orders)):
            raise ValueError(
                "scene order values must be unique within a storyboard"
            )

        # Scenes must be supplied in timeline order.
        if orders != sorted(orders):
            raise ValueError(
                "scenes must be ordered by the 'order' field"
            )

        return self

    @property
    def total_duration(self) -> int:
        """
        Return the total duration of the storyboard in seconds.
        """
        return sum(scene.duration for scene in self.scenes)

    @property
    def scene_count(self) -> int:
        """
        Return the number of scenes in the storyboard.
        """
        return len(self.scenes)