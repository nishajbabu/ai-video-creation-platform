"""
Scene application service.

This module contains business logic for managing generated
video scenes.

Persistence is delegated to SceneRepository.
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.scene import SceneModel
from app.repositories.scene_repository import SceneRepository


class SceneService:
    """
    Application service responsible for scene operations.

    Business logic lives here.
    Database persistence is delegated to SceneRepository.
    """

    def __init__(
        self,
        repository: SceneRepository,
    ):
        """
        Initialize the scene service.
        """

        self.repository = repository

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_scene(
        self,
        scene: SceneModel,
    ) -> SceneModel:
        """
        Create and persist a scene.
        """

        return self.repository.create(
            scene,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_scene(
        self,
        scene_id: int,
    ) -> Optional[SceneModel]:
        """
        Return a scene by ID.

        Returns None when the scene does not exist.
        """

        return self.repository.get(
            scene_id,
        )

    def list_scenes(
        self,
    ) -> List[SceneModel]:
        """
        Return all scenes.
        """

        return self.repository.list()

    def list_scenes_for_video(
        self,
        video_id: str,
    ) -> List[SceneModel]:
        """
        Return all scenes belonging to a video.
        """

        return self.repository.list_by_video(
            video_id,
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_scene(
        self,
        scene_id: int,
        *,
        purpose: Optional[str] = None,
        narration: Optional[str] = None,
        visual_description: Optional[str] = None,
        visual_prompt: Optional[str] = None,
        visual_type: Optional[str] = None,
        status: Optional[str] = None,
        duration: Optional[int] = None,
        order: Optional[int] = None,
    ) -> Optional[SceneModel]:
        """
        Update selected scene fields.

        Returns:
            Updated scene if found, otherwise None.
        """

        scene = self.repository.get(
            scene_id,
        )

        if scene is None:
            return None

        if purpose is not None:
            scene.purpose = purpose

        if narration is not None:
            scene.narration = narration

        if visual_description is not None:
            scene.visual_description = visual_description

        if visual_prompt is not None:
            scene.visual_prompt = visual_prompt

        if visual_type is not None:
            scene.visual_type = visual_type

        if status is not None:
            scene.status = status

        if duration is not None:
            scene.duration = duration

        if order is not None:
            scene.order = order

        scene.updated_at = datetime.now(
            timezone.utc,
        )

        return self.repository.update(
            scene,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_scene(
        self,
        scene_id: int,
    ) -> bool:
        """
        Delete a scene.

        Returns:
            True if deleted.
            False when the scene does not exist.
        """

        scene = self.repository.get(
            scene_id,
        )

        if scene is None:
            return False

        self.repository.delete(
            scene,
        )

        return True

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def exists(
        self,
        scene_id: int,
    ) -> bool:
        """
        Check whether a scene exists.
        """

        return self.repository.exists(
            scene_id,
        )

    def has_scenes_for_video(
        self,
        video_id: str,
    ) -> bool:
        """
        Return whether a video contains at least one scene.
        """

        return self.repository.exists_for_video(
            video_id,
        )

    def count_scenes_for_video(
        self,
        video_id: str,
    ) -> int:
        """
        Return the number of scenes belonging to a video.
        """

        return self.repository.count_for_video(
            video_id,
        )