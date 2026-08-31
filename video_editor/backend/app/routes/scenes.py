from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.timeline import Timeline

from app.database import get_db
from app.models.scene import Scene
from app.models.video import Video
from app.schemas.scene import (
    SceneCreate,
    SceneUpdate,
    SceneReorder,
    SceneResponse
)


router = APIRouter(
    prefix="/scenes",
    tags=["Scenes"]
)


@router.post("/", response_model=SceneResponse)
def create_scene(
    scene_data: SceneCreate,
    db: Session = Depends(get_db)
):
    video = (
        db.query(Video)
        .filter(Video.id == scene_data.video_id)
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    scene = Scene(
        video_id=scene_data.video_id,
        order=scene_data.order,
        duration=scene_data.duration,
        title=scene_data.title
    )

    db.add(scene)
    db.commit()
    db.refresh(scene)

    return scene


@router.get(
    "/video/{video_id}",
    response_model=list[SceneResponse]
)
def get_video_scenes(
    video_id: int,
    db: Session = Depends(get_db)
):
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

    scenes = (
        db.query(Scene)
        .filter(Scene.video_id == video_id)
        .order_by(Scene.order)
        .all()
    )

    return scenes


@router.get(
    "/{scene_id}",
    response_model=SceneResponse
)
def get_scene(
    scene_id: int,
    db: Session = Depends(get_db)
):
    scene = (
        db.query(Scene)
        .filter(Scene.id == scene_id)
        .first()
    )

    if not scene:
        raise HTTPException(
            status_code=404,
            detail="Scene not found"
        )

    return scene


@router.put(
    "/{scene_id}",
    response_model=SceneResponse
)
def update_scene(
    scene_id: int,
    scene_data: SceneUpdate,
    db: Session = Depends(get_db)
):
    scene = (
        db.query(Scene)
        .filter(Scene.id == scene_id)
        .first()
    )

    if not scene:
        raise HTTPException(
            status_code=404,
            detail="Scene not found"
        )

    if scene_data.title is not None:
        scene.title = scene_data.title

    if scene_data.duration is not None:
        scene.duration = scene_data.duration

    if scene_data.order is not None:
        scene.order = scene_data.order

    db.commit()
    db.refresh(scene)

    return scene

@router.put(
    "/video/{video_id}/reorder",
    response_model=list[SceneResponse]
)
def reorder_scenes(
    video_id: int,
    reorder_data: SceneReorder,
    db: Session = Depends(get_db)
):
    # Check video exists
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

    # Get scenes
    scenes = (
        db.query(Scene)
        .filter(Scene.video_id == video_id)
        .all()
    )

    scene_map = {
        scene.id: scene
        for scene in scenes
    }

    # Validate scene IDs
    if set(reorder_data.scene_ids) != set(scene_map.keys()):
        raise HTTPException(
            status_code=400,
            detail="Scene list does not match video's scenes"
        )

    # Update scene order
    for index, scene_id in enumerate(
        reorder_data.scene_ids,
        start=1
    ):
        scene_map[scene_id].order = index

    db.flush()

    # Get timeline entries
    timeline_items = (
        db.query(Timeline)
        .filter(Timeline.video_id == video_id)
        .all()
    )

    timeline_map = {
        item.scene_id: item
        for item in timeline_items
    }

    # Recalculate timeline
    current_time = 0.0

    for scene_id in reorder_data.scene_ids:

        scene = scene_map[scene_id]

        timeline = timeline_map.get(scene_id)

        if timeline:
            timeline.start_time = current_time
            timeline.end_time = (
                current_time + scene.duration
            )

        current_time += scene.duration

    # Update total video duration
    video.total_duration = current_time

    db.commit()

    # Return updated scenes
    updated_scenes = (
        db.query(Scene)
        .filter(Scene.video_id == video_id)
        .order_by(Scene.order)
        .all()
    )

    return updated_scenes

@router.delete("/{scene_id}")
def delete_scene(
    scene_id: int,
    db: Session = Depends(get_db)
):
    scene = (
        db.query(Scene)
        .filter(Scene.id == scene_id)
        .first()
    )

    if not scene:
        raise HTTPException(
            status_code=404,
            detail="Scene not found"
        )

    db.delete(scene)
    db.commit()

    return {
        "message": "Scene deleted successfully"
    }