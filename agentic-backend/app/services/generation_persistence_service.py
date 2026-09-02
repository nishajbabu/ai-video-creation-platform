"""
Generation persistence service.

This module converts completed AI-generation workflow output into
persistent database records.

The service coordinates existing application services. It does not
contain database-specific logic.

Persistence flow:

    WorkflowResult
        ↓
    Video
        ↓
    Scenes
        ↓
    Asset requirements
        ↓
    Database
"""

from datetime import datetime, timezone
from typing import List

from app.agents.orchestrator import WorkflowResult
from app.schemas.video import Video
from app.schemas.project import Project
from app.models.scene import SceneModel
from app.models.asset import AssetModel
from app.services.video_service import VideoService
from app.services.scene_service import SceneService
from app.services.asset_service import AssetService


class GenerationPersistenceService:
    """
    Persist the output of a completed generation workflow.

    Project creation remains outside this service because a project
    represents an application-level workspace and should be created
    explicitly by the project workflow.
    """

    def __init__(
        self,
        video_service: VideoService,
        scene_service: SceneService,
        asset_service: AssetService,
    ):
        """
        Initialize the persistence coordinator.
        """

        self.video_service = video_service
        self.scene_service = scene_service
        self.asset_service = asset_service

    # ------------------------------------------------------------------
    # Persist complete workflow
    # ------------------------------------------------------------------

    def persist_workflow(
        self,
        result: WorkflowResult,
        project: Project,
    ) -> Video:
        """
        Persist a completed workflow under an existing project.

        The workflow must contain a storyboard. The storyboard is
        converted into persistent scene records, and each scene's
        asset requirements are converted into asset records.

        Returns:
            Persisted Video schema.

        Raises:
            ValueError:
                If the workflow is not completed or does not contain
                the required storyboard.
        """

        if result.status != "completed":
            raise ValueError(
                "Only completed workflows can be persisted."
            )

        if result.storyboard is None:
            raise ValueError(
                "Cannot persist workflow without a storyboard."
            )

        video = self._create_video(
            result,
            project,
        )

        for scene in result.storyboard.scenes:
            scene_model = self._create_scene(
                scene,
                video.video_id,
            )

            self._create_assets(
                scene,
                scene_model.scene_id,
            )

        return video

    # ------------------------------------------------------------------
    # Video
    # ------------------------------------------------------------------

    def _create_video(
        self,
        result: WorkflowResult,
        project: Project,
    ) -> Video:
        """
        Create the persistent video record for a workflow.
        """

        if result.storyboard is None:
            raise ValueError(
                "Cannot create video without a storyboard."
            )

        video_id = self._create_video_id(
            result,
        )

        title = self._create_video_title(
            result,
        )

        video = Video(
            video_id=video_id,
            project_id=project.project_id,
            title=title,
            duration=result.storyboard.total_duration,
            status="queued",
        )

        return self.video_service.create_video(
            video,
        )

    # ------------------------------------------------------------------
    # Scene
    # ------------------------------------------------------------------

    def _create_scene(
        self,
        scene,
        video_id: str,
    ) -> SceneModel:
        """
        Convert a storyboard scene into a persistent SceneModel.
        """

        scene_model = SceneModel(
            video_id=video_id,
            order=scene.order,
            duration=scene.duration,
            purpose=scene.purpose,
            narration=scene.narration,
            visual_description=scene.visual_description,
            visual_prompt=scene.visual_prompt,
            visual_type=scene.visual_type,
            status=scene.status,
            has_asset_requirements=bool(
                scene.asset_requirements,
            ),
            has_audio_requirements=(
                scene.audio_requirements.required
            ),
        )

        return self.scene_service.create_scene(
            scene_model,
        )

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------

    def _create_assets(
        self,
        scene,
        scene_id: int,
    ) -> List[AssetModel]:
        """
        Convert scene asset requirements into persistent assets.

        These records represent asset requirements at this stage.
        Actual AI/media asset generation is handled later.
        """

        assets: List[AssetModel] = []

        for requirement in scene.asset_requirements:
            asset = AssetModel(
                scene_id=scene_id,
                asset_type=requirement.asset_type,
                description=requirement.description,
                source=requirement.source,
            )

            saved_asset = self.asset_service.create_asset(
                asset,
            )

            assets.append(
                saved_asset,
            )

        return assets

    # ------------------------------------------------------------------
    # Identifiers
    # ------------------------------------------------------------------

    @staticmethod
    def _create_video_id(
        result: WorkflowResult,
    ) -> str:
        """
        Create a stable video identifier for the workflow.

        The workflow ID is already unique, so it is used as the
        foundation for the video identifier.
        """

        workflow_id = getattr(
            result,
            "workflow_id",
            None,
        )

        if workflow_id:
            return f"video_{workflow_id}"

        timestamp = datetime.now(
            timezone.utc,
        ).strftime(
            "%Y%m%d%H%M%S%f",
        )

        return f"video_{timestamp}"

    @staticmethod
    def _create_video_title(
        result: WorkflowResult,
    ) -> str:
        """
        Create a human-readable video title from the request.

        The first part of the user's prompt is used until a later
        title-generation stage is introduced.
        """

        prompt = result.request.prompt.strip()

        if len(prompt) <= 200:
            return prompt

        return prompt[:197].rstrip() + "..."