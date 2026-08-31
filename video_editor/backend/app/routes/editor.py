from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.video import Video
from app.models.scene import Scene
from app.models.asset import Asset
from app.models.timeline import Timeline

from app.schemas.timeline import EditorSceneUpdate


router = APIRouter(
    prefix="/editor",
    tags=["Editor"]
)


# ==================================================
# GET COMPLETE EDITOR DATA
# ==================================================

@router.get("/{video_id}")
def get_editor_data(
    video_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all information required by the video editor.

    Includes:
        - Video
        - Scenes
        - Assets
        - Timeline
    """

    # --------------------------------------------------
    # Check video
    # --------------------------------------------------

    video = (
        db.query(Video)
        .filter(Video.id == video_id)
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    # --------------------------------------------------
    # Get scenes in editor order
    # --------------------------------------------------

    scenes = (
        db.query(Scene)
        .filter(Scene.video_id == video_id)
        .order_by(Scene.order)
        .all()
    )

    editor_scenes = []

    # --------------------------------------------------
    # Build editor scene data
    # --------------------------------------------------

    for scene in scenes:

        # ----------------------------------------------
        # Get assets
        # ----------------------------------------------

        assets = (
            db.query(Asset)
            .filter(
                Asset.scene_id == scene.id
            )
            .all()
        )

        asset_data = []

        for asset in assets:

            asset_data.append({
                "id": asset.id,
                "type": asset.asset_type,
                "url": asset.file_url
            })

        # ----------------------------------------------
        # Get timeline
        # ----------------------------------------------

        timeline = (
            db.query(Timeline)
            .filter(
                Timeline.video_id == video_id,
                Timeline.scene_id == scene.id
            )
            .first()
        )

        timeline_data = None

        if timeline:

            timeline_data = {
                "id": timeline.id,
                "start_time": timeline.start_time,
                "end_time": timeline.end_time,
                "transition": timeline.transition,
                "text_overlay": timeline.text_overlay
            }

        # ----------------------------------------------
        # Add scene
        # ----------------------------------------------

        editor_scenes.append({
            "scene_id": scene.id,
            "order": scene.order,
            "title": scene.title,
            "duration": scene.duration,
            "assets": asset_data,
            "timeline": timeline_data
        })

    # --------------------------------------------------
    # Return editor data
    # --------------------------------------------------

    return {
        "video": {
            "id": video.id,
            "title": video.title,
            "total_duration": video.total_duration
        },
        "scenes": editor_scenes
    }


# ==================================================
# UPDATE SINGLE SCENE
# ==================================================

@router.put(
    "/{video_id}/scenes/{scene_id}"
)
def update_editor_scene(
    video_id: int,
    scene_id: int,
    update_data: EditorSceneUpdate,
    db: Session = Depends(get_db)
):
    """
    Update scene editing properties.

    Supports:
        - Duration
        - Start time
        - End time
        - Text overlay
        - Transition
    """

    # --------------------------------------------------
    # Check video
    # --------------------------------------------------

    video = (
        db.query(Video)
        .filter(Video.id == video_id)
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    # --------------------------------------------------
    # Check scene
    # --------------------------------------------------

    scene = (
        db.query(Scene)
        .filter(
            Scene.id == scene_id,
            Scene.video_id == video_id
        )
        .first()
    )

    if not scene:
        raise HTTPException(
            status_code=404,
            detail="Scene not found"
        )

    # --------------------------------------------------
    # Update scene duration
    # --------------------------------------------------

    if update_data.duration is not None:

        if update_data.duration <= 0:
            raise HTTPException(
                status_code=400,
                detail="Scene duration must be greater than 0"
            )

        scene.duration = (
            update_data.duration
        )

    # --------------------------------------------------
    # Find timeline
    # --------------------------------------------------

    timeline = (
        db.query(Timeline)
        .filter(
            Timeline.video_id == video_id,
            Timeline.scene_id == scene_id
        )
        .first()
    )

    # --------------------------------------------------
    # Create timeline if missing
    # --------------------------------------------------

    if not timeline:

        duration = (
            scene.duration
            if scene.duration is not None
            else 0
        )

        if duration <= 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Scene must have a valid "
                    "duration before creating "
                    "a timeline"
                )
            )

        timeline = Timeline(
            video_id=video_id,
            scene_id=scene_id,
            start_time=0,
            end_time=duration
        )

        db.add(timeline)

        db.flush()

    # --------------------------------------------------
    # Update timeline start
    # --------------------------------------------------

    if update_data.start_time is not None:

        if update_data.start_time < 0:
            raise HTTPException(
                status_code=400,
                detail="start_time cannot be negative"
            )

        timeline.start_time = (
            update_data.start_time
        )

    # --------------------------------------------------
    # Update timeline end
    # --------------------------------------------------

    if update_data.end_time is not None:

        timeline.end_time = (
            update_data.end_time
        )

    # --------------------------------------------------
    # Update text
    # --------------------------------------------------

    if update_data.text_overlay is not None:

        timeline.text_overlay = (
            update_data.text_overlay
        )

    # --------------------------------------------------
    # Update transition
    # --------------------------------------------------

    if update_data.transition is not None:

        timeline.transition = (
            update_data.transition
        )

    # --------------------------------------------------
    # Validate timeline
    # --------------------------------------------------

    if timeline.start_time < 0:

        raise HTTPException(
            status_code=400,
            detail="start_time cannot be negative"
        )

    if timeline.end_time <= timeline.start_time:

        raise HTTPException(
            status_code=400,
            detail=(
                "end_time must be greater "
                "than start_time"
            )
        )

    # --------------------------------------------------
    # Recalculate total video duration
    # --------------------------------------------------

    scenes = (
        db.query(Scene)
        .filter(
            Scene.video_id == video_id
        )
        .all()
    )

    total_duration = sum(
        float(scene.duration or 0)
        for scene in scenes
    )

    video.total_duration = (
        total_duration
    )

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    db.commit()

    db.refresh(scene)
    db.refresh(timeline)
    db.refresh(video)

    # --------------------------------------------------
    # Response
    # --------------------------------------------------

    return {
        "message": "Scene updated successfully",

        "scene": {
            "id": scene.id,
            "video_id": scene.video_id,
            "order": scene.order,
            "title": scene.title,
            "duration": scene.duration
        },

        "timeline": {
            "id": timeline.id,
            "start_time": timeline.start_time,
            "end_time": timeline.end_time,
            "transition": timeline.transition,
            "text_overlay": timeline.text_overlay
        },

        "video_total_duration": (
            video.total_duration
        )
    }


# ==================================================
# REORDER SCENES
# ==================================================

@router.put(
    "/{video_id}/reorder"
)
def reorder_scenes(
    video_id: int,
    scene_ids: list[int],
    db: Session = Depends(get_db)
):
    """
    Reorder scenes for a video.

    Example request body:

        [8, 7, 9]

    This means:

        Scene 8 -> order 1
        Scene 7 -> order 2
        Scene 9 -> order 3

    After reordering, the automatic timeline
    can be regenerated.
    """

    # --------------------------------------------------
    # Check video
    # --------------------------------------------------

    video = (
        db.query(Video)
        .filter(Video.id == video_id)
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    # --------------------------------------------------
    # Validate request
    # --------------------------------------------------

    if not scene_ids:

        raise HTTPException(
            status_code=400,
            detail="scene_ids cannot be empty"
        )

    # Check duplicate IDs
    if len(scene_ids) != len(set(scene_ids)):

        raise HTTPException(
            status_code=400,
            detail="Duplicate scene IDs are not allowed"
        )

    # --------------------------------------------------
    # Get existing scenes
    # --------------------------------------------------

    scenes = (
        db.query(Scene)
        .filter(
            Scene.video_id == video_id
        )
        .all()
    )

    existing_scene_ids = {
        scene.id
        for scene in scenes
    }

    requested_scene_ids = set(
        scene_ids
    )

    # --------------------------------------------------
    # Make sure all scenes are included
    # --------------------------------------------------

    if requested_scene_ids != existing_scene_ids:

        raise HTTPException(
            status_code=400,
            detail=(
                "scene_ids must contain "
                "every scene belonging "
                "to this video exactly once"
            )
        )

    # --------------------------------------------------
    # Update order
    # --------------------------------------------------

    scene_map = {
        scene.id: scene
        for scene in scenes
    }

    for new_order, scene_id in enumerate(
        scene_ids,
        start=1
    ):

        scene = scene_map[scene_id]

        scene.order = new_order

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    db.commit()

    # --------------------------------------------------
    # Refresh scenes
    # --------------------------------------------------

    for scene in scenes:
        db.refresh(scene)

    # --------------------------------------------------
    # Return new order
    # --------------------------------------------------

    ordered_scenes = sorted(
        scenes,
        key=lambda scene: scene.order
    )

    return {
        "message": "Scenes reordered successfully",

        "video_id": video_id,

        "scenes": [
            {
                "scene_id": scene.id,
                "title": scene.title,
                "order": scene.order,
                "duration": scene.duration
            }
            for scene in ordered_scenes
        ]
    }