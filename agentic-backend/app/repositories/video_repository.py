"""
Video database repository.

This module contains database-specific operations for VideoModel.

The repository is responsible only for persistence. Business rules
remain in VideoService.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.video import VideoModel


class VideoRepository:
    """
    Repository responsible for VideoModel persistence.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a SQLAlchemy session.
        """

        self.session = session

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        video: VideoModel,
    ) -> VideoModel:
        """
        Persist a new video.
        """

        self.session.add(video)
        self.session.commit()
        self.session.refresh(video)

        return video

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(
        self,
        video_id: str,
    ) -> Optional[VideoModel]:
        """
        Return a video by ID.

        Returns None when the video does not exist.
        """

        return (
            self.session.query(VideoModel)
            .filter(
                VideoModel.video_id == video_id,
            )
            .first()
        )

    def list(self) -> List[VideoModel]:
        """
        Return all videos.
        """

        return (
            self.session.query(VideoModel)
            .order_by(VideoModel.created_at)
            .all()
        )

    def list_by_project(
        self,
        project_id: str,
    ) -> List[VideoModel]:
        """
        Return all videos belonging to a project.
        """

        return (
            self.session.query(VideoModel)
            .filter(
                VideoModel.project_id == project_id,
            )
            .order_by(VideoModel.created_at)
            .all()
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        video: VideoModel,
    ) -> VideoModel:
        """
        Persist changes made to an existing video.
        """

        self.session.add(video)
        self.session.commit()
        self.session.refresh(video)

        return video

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(
        self,
        video: VideoModel,
    ) -> None:
        """
        Delete a video from the database.
        """

        self.session.delete(video)
        self.session.commit()

    # ------------------------------------------------------------------
    # Existence
    # ------------------------------------------------------------------

    def exists(
        self,
        video_id: str,
    ) -> bool:
        """
        Return whether a video exists.
        """

        return (
            self.session.query(VideoModel)
            .filter(
                VideoModel.video_id == video_id,
            )
            .first()
            is not None
        )