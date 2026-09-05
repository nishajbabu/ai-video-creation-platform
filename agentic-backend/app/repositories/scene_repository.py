"""
Scene database repository.

This module contains database-specific operations for SceneModel.

The repository is responsible only for persistence. Business rules
remain in the service layer.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.scene import SceneModel


class SceneRepository:
    """
    Repository responsible for SceneModel persistence.
    """

    def __init__(
        self,
        session: Session,
    ):
        """
        Initialize the repository with a SQLAlchemy session.
        """

        self.session = session

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        scene: SceneModel,
    ) -> SceneModel:
        """
        Persist a new scene.
        """

        self.session.add(scene)
        self.session.commit()
        self.session.refresh(scene)

        return scene

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(
        self,
        scene_id: int,
    ) -> Optional[SceneModel]:
        """
        Return a scene by its database ID.

        Returns None when the scene does not exist.
        """

        return (
            self.session.query(SceneModel)
            .filter(
                SceneModel.scene_id == scene_id,
            )
            .first()
        )

    def list(self) -> List[SceneModel]:
        """
        Return all scenes ordered by video and timeline order.
        """

        return (
            self.session.query(SceneModel)
            .order_by(
                SceneModel.video_id,
                SceneModel.order,
            )
            .all()
        )

    def list_by_video(
        self,
        video_id: str,
    ) -> List[SceneModel]:
        """
        Return all scenes belonging to a video.

        Scenes are returned in timeline order.
        """

        return (
            self.session.query(SceneModel)
            .filter(
                SceneModel.video_id == video_id,
            )
            .order_by(
                SceneModel.order,
            )
            .all()
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        scene: SceneModel,
    ) -> SceneModel:
        """
        Persist changes made to an existing scene.
        """

        self.session.add(scene)
        self.session.commit()
        self.session.refresh(scene)

        return scene

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(
        self,
        scene: SceneModel,
    ) -> None:
        """
        Delete a scene from the database.
        """

        self.session.delete(scene)
        self.session.commit()

    # ------------------------------------------------------------------
    # Existence
    # ------------------------------------------------------------------

    def exists(
        self,
        scene_id: int,
    ) -> bool:
        """
        Return whether a scene exists.
        """

        return (
            self.session.query(SceneModel)
            .filter(
                SceneModel.scene_id == scene_id,
            )
            .first()
            is not None
        )

    # ------------------------------------------------------------------
    # Video existence
    # ------------------------------------------------------------------

    def exists_for_video(
        self,
        video_id: str,
    ) -> bool:
        """
        Return whether at least one scene exists for a video.
        """

        return (
            self.session.query(SceneModel)
            .filter(
                SceneModel.video_id == video_id,
            )
            .first()
            is not None
        )

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    def count_for_video(
        self,
        video_id: str,
    ) -> int:
        """
        Return the number of scenes belonging to a video.
        """

        return (
            self.session.query(SceneModel)
            .filter(
                SceneModel.video_id == video_id,
            )
            .count()
        )