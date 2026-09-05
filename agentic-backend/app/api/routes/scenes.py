"""
Scene API routes.

This module exposes endpoints for retrieving generated video
scenes.

Business logic and database access remain outside the route layer.
SceneRepository handles persistence and querying.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import get_scene_repository
from app.repositories.scene_repository import SceneRepository


router = APIRouter(
    prefix="/scenes",
    tags=["Scenes"],
)


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class SceneResponse(BaseModel):
    """
    API representation of a persisted scene.

    This schema intentionally represents the fields that are actually
    stored by SceneModel.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    scene_id: int
    video_id: str
    order: int
    duration: int
    purpose: str
    narration: str
    visual_description: str
    visual_prompt: str
    visual_type: str
    status: str
    has_asset_requirements: bool
    has_audio_requirements: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# List scenes
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[SceneResponse],
)
def list_scenes(
    repository: SceneRepository = Depends(
        get_scene_repository,
    ),
) -> List[SceneResponse]:
    """
    Return all generated scenes.

    Scenes are ordered by video and timeline order.
    """

    scenes = repository.list()

    return [
        SceneResponse.model_validate(scene)
        for scene in scenes
    ]


# ---------------------------------------------------------------------------
# List scenes for video
# ---------------------------------------------------------------------------

@router.get(
    "/video/{video_id}",
    response_model=List[SceneResponse],
)
def list_scenes_for_video(
    video_id: str,
    repository: SceneRepository = Depends(
        get_scene_repository,
    ),
) -> List[SceneResponse]:
    """
    Return all scenes belonging to a specific video.

    Scenes are returned in timeline order.
    """

    scenes = repository.list_by_video(
        video_id,
    )

    return [
        SceneResponse.model_validate(scene)
        for scene in scenes
    ]


# ---------------------------------------------------------------------------
# Get scene
# ---------------------------------------------------------------------------

@router.get(
    "/{scene_id}",
    response_model=SceneResponse,
)
def get_scene(
    scene_id: int,
    repository: SceneRepository = Depends(
        get_scene_repository,
    ),
) -> SceneResponse:
    """
    Return a scene by its database identifier.

    Raises:
        HTTPException:
            404 when the requested scene does not exist.
    """

    scene = repository.get(
        scene_id,
    )

    if scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Scene '{scene_id}' "
                "was not found."
            ),
        )

    return SceneResponse.model_validate(
        scene,
    )