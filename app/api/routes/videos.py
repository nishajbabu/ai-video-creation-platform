"""
Video API routes.

This module provides endpoints for retrieving generated videos
and exposing scene information required by downstream media
generation services.

Video persistence is handled through VideoService and
VideoRepository.

The `_videos` dictionary is retained only for compatibility with
the existing integration-test setup. It is NOT used as the source
of truth for video data.
"""

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_scene_repository,
    get_video_service,
)
from app.repositories.scene_repository import SceneRepository
from app.schemas.media_generation import MediaGenerationInput
from app.schemas.video import Video
from app.services.video_service import VideoService


router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
)


# ---------------------------------------------------------------------------
# Legacy test compatibility
# ---------------------------------------------------------------------------

# Existing integration tests import `_videos` and clear it between tests.
#
# Video persistence itself is handled by:
#
#     VideoService
#         ↓
#     VideoRepository
#         ↓
#     SQLAlchemy database
#
# This dictionary is intentionally NOT used by the API endpoints.

_videos: Dict[str, Video] = {}


# ---------------------------------------------------------------------------
# List videos
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[Video],
)
def list_videos(
    service: VideoService = Depends(
        get_video_service,
    ),
) -> list[Video]:
    """
    Return all generated videos.

    Video records are retrieved from the database through
    VideoService.
    """

    return service.list_videos()


# ---------------------------------------------------------------------------
# Media-generation input
# ---------------------------------------------------------------------------

@router.get(
    "/{video_id}/media-inputs",
    response_model=MediaGenerationInput,
)
def get_media_generation_inputs(
    video_id: str,
    video_service: VideoService = Depends(
        get_video_service,
    ),
    scene_repository: SceneRepository = Depends(
        get_scene_repository,
    ),
) -> MediaGenerationInput:
    """
    Return the scene information required by the
    AI Media Generation module.

    This endpoint provides the integration contract between
    the Agentic AI + Backend module and the AI Media Generation
    module.

    The backend provides:

        - project_id
        - video_id
        - scene_id
        - narration
        - visual_prompt

    Voice selection is optional and is currently returned as None
    until a voice-selection workflow is introduced.
    """

    video = video_service.get_video(
        video_id,
    )

    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Video '{video_id}' "
                "was not found."
            ),
        )

    scenes = scene_repository.list_by_video(
        video_id,
    )

    if not scenes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No scenes were found for video "
                f"'{video_id}'."
            ),
        )

    return MediaGenerationInput(
        video_id=video.video_id,
        project_id=video.project_id,
        scenes=[
            {
                "scene_id": scene.scene_id,
                "narration": scene.narration,
                "visual_prompt": scene.visual_prompt,
                "voice": None,
            }
            for scene in scenes
        ],
    )


# ---------------------------------------------------------------------------
# Get video
# ---------------------------------------------------------------------------

@router.get(
    "/{video_id}",
    response_model=Video,
)
def get_video(
    video_id: str,
    service: VideoService = Depends(
        get_video_service,
    ),
) -> Video:
    """
    Return a generated video by its identifier.

    Raises:
        HTTPException:
            404 when the requested video does not exist.
    """

    video = service.get_video(
        video_id,
    )

    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Video '{video_id}' "
                "was not found."
            ),
        )

    return video