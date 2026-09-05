"""
Video application service.

This module contains business logic for managing generated videos.

The service converts between API schemas and database models while
delegating persistence to VideoRepository.
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.video import VideoModel
from app.repositories.video_repository import VideoRepository
from app.schemas.video import Video


class VideoService:
    """
    Application service responsible for video operations.

    Dependency flow:

        API Schema
            ↓
        VideoService
            ↓
        VideoModel
            ↓
        VideoRepository
            ↓
        Database
    """

    def __init__(
        self,
        repository: VideoRepository,
    ):
        """
        Initialize the video service.
        """

        self.repository = repository

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_model(
        video: Video,
    ) -> VideoModel:
        """
        Convert a Pydantic Video schema into a SQLAlchemy model.
        """

        return VideoModel(
            video_id=video.video_id,
            project_id=video.project_id,
            title=video.title,
            duration=video.duration,
            status=video.status,
            resolution=video.resolution,
            fps=video.fps,
            file_path=video.file_path,
            thumbnail_path=video.thumbnail_path,
            created_at=video.created_at,
        )

    @staticmethod
    def _to_schema(
        video: VideoModel,
    ) -> Video:
        """
        Convert a SQLAlchemy VideoModel into a Pydantic schema.
        """

        return Video(
            video_id=video.video_id,
            project_id=video.project_id,
            title=video.title,
            duration=video.duration,
            status=video.status,
            resolution=video.resolution,
            fps=video.fps,
            file_path=video.file_path,
            thumbnail_path=video.thumbnail_path,
            created_at=video.created_at,
        )

    # ------------------------------------------------------------------
    # Create / register
    # ------------------------------------------------------------------

    def create_video(
        self,
        video: Video,
    ) -> Video:
        """
        Register and persist a generated video.

        Raises:
            ValueError:
                If a video with the same ID already exists.
        """

        if self.repository.exists(
            video.video_id,
        ):
            raise ValueError(
                f"Video '{video.video_id}' already exists."
            )

        model = self._to_model(
            video,
        )

        saved_model = self.repository.create(
            model,
        )

        return self._to_schema(
            saved_model,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_video(
        self,
        video_id: str,
    ) -> Optional[Video]:
        """
        Return a video by ID.

        Returns None when the video does not exist.
        """

        model = self.repository.get(
            video_id,
        )

        if model is None:
            return None

        return self._to_schema(
            model,
        )

    def list_videos(self) -> List[Video]:
        """
        Return all stored videos.
        """

        models = self.repository.list()

        return [
            self._to_schema(model)
            for model in models
        ]

    def get_videos_for_project(
        self,
        project_id: str,
    ) -> List[Video]:
        """
        Return all videos belonging to a project.
        """

        models = self.repository.list_by_project(
            project_id,
        )

        return [
            self._to_schema(model)
            for model in models
        ]

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_video_status(
        self,
        video_id: str,
        status: str,
    ) -> Optional[Video]:
        """
        Update the rendering status of a video.

        Returns:
            Updated video if found, otherwise None.
        """

        model = self.repository.get(
            video_id,
        )

        if model is None:
            return None

        model.status = status

        updated_model = self.repository.update(
            model,
        )

        return self._to_schema(
            updated_model,
        )

    def update_video_file(
        self,
        video_id: str,
        *,
        file_path: Optional[str] = None,
        thumbnail_path: Optional[str] = None,
    ) -> Optional[Video]:
        """
        Update generated video and thumbnail paths.

        Returns:
            Updated video if found, otherwise None.
        """

        model = self.repository.get(
            video_id,
        )

        if model is None:
            return None

        if file_path is not None:
            model.file_path = file_path

        if thumbnail_path is not None:
            model.thumbnail_path = thumbnail_path

        updated_model = self.repository.update(
            model,
        )

        return self._to_schema(
            updated_model,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_video(
        self,
        video_id: str,
    ) -> bool:
        """
        Delete a video record.

        Returns:
            True if the video existed and was deleted.
            False otherwise.
        """

        model = self.repository.get(
            video_id,
        )

        if model is None:
            return False

        self.repository.delete(
            model,
        )

        return True

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def exists(
        self,
        video_id: str,
    ) -> bool:
        """
        Check whether a video exists.
        """

        return self.repository.exists(
            video_id,
        )

    def clear(self) -> None:
        """
        Remove all stored video records.
        """

        models = self.repository.list()

        for model in models:
            self.repository.delete(
                model,
            )