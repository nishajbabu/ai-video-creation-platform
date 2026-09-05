from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.timeline import Timeline
from app.models.video import Video
from app.models.scene import Scene
from app.models.asset import Asset

from app.schemas.timeline import (
    TimelineCreate,
    TimelineUpdate,
    TimelineResponse
)

from app.services.timeline_service import generate_timeline


router = APIRouter(
    prefix="/timeline",
    tags=["Timeline"]
)


# --------------------------------------------------
# Create timeline item manually
# --------------------------------------------------

@router.post(
    "/",
    response_model=TimelineResponse
)
def create_timeline_item(
    timeline_data: TimelineCreate,
    db: Session = Depends(get_db)
):
    """
    Create a timeline item manually.

    This endpoint is still useful when the frontend
    wants to explicitly control timeline properties.
    """

    # Check video exists
    video = (
        db.query(Video)
        .filter(Video.id == timeline_data.video_id)
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    # Check scene exists
    scene = (
        db.query(Scene)
        .filter(Scene.id == timeline_data.scene_id)
        .first()
    )

    if not scene:
        raise HTTPException(
            status_code=404,
            detail="Scene not found"
        )

    # Make sure scene belongs to video
    if scene.video_id != timeline_data.video_id:
        raise HTTPException(
            status_code=400,
            detail="Scene does not belong to this video"
        )

    # Validate time
    if timeline_data.end_time <= timeline_data.start_time:
        raise HTTPException(
            status_code=400,
            detail="end_time must be greater than start_time"
        )

    timeline = Timeline(
        video_id=timeline_data.video_id,
        scene_id=timeline_data.scene_id,
        start_time=timeline_data.start_time,
        end_time=timeline_data.end_time,
        transition=timeline_data.transition,
        text_overlay=timeline_data.text_overlay
    )

    db.add(timeline)
    db.commit()
    db.refresh(timeline)

    return timeline


# --------------------------------------------------
# Automatically generate timeline
# --------------------------------------------------

@router.post(
    "/generate/{video_id}",
    response_model=list[TimelineResponse]
)
def generate_video_timeline(
    video_id: int,
    db: Session = Depends(get_db)
):
    """
    Automatically generate the timeline based on
    the actual duration of each scene video.

    The user does NOT need to provide:

        start_time
        end_time

    The system calculates them automatically.
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
    # Get scenes
    # --------------------------------------------------

    scenes = (
        db.query(Scene)
        .filter(Scene.video_id == video_id)
        .order_by(Scene.order)
        .all()
    )

    if not scenes:
        raise HTTPException(
            status_code=400,
            detail="Video has no scenes"
        )

    # --------------------------------------------------
    # Get scene IDs
    # --------------------------------------------------

    scene_ids = [
        scene.id
        for scene in scenes
    ]

    # --------------------------------------------------
    # Get assets
    # --------------------------------------------------

    assets = (
        db.query(Asset)
        .filter(
            Asset.scene_id.in_(scene_ids)
        )
        .all()
    )

    # --------------------------------------------------
    # Make sure scenes have videos
    # --------------------------------------------------

    video_assets = [
        asset
        for asset in assets
        if asset.asset_type == "video"
    ]

    if not video_assets:
        raise HTTPException(
            status_code=400,
            detail="No video assets found for the scenes"
        )

    # --------------------------------------------------
    # Remove existing timeline entries
    # --------------------------------------------------

    db.query(Timeline).filter(
        Timeline.video_id == video_id
    ).delete(
        synchronize_session=False
    )

    db.commit()

    # --------------------------------------------------
    # Generate timeline automatically
    # --------------------------------------------------

    try:

        timelines = generate_timeline(
            db=db,
            video_id=video_id,
            scenes=scenes,
            assets=assets
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    return timelines


# --------------------------------------------------
# Get video timeline
# --------------------------------------------------

@router.get(
    "/video/{video_id}",
    response_model=list[TimelineResponse]
)
def get_video_timeline(
    video_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all timeline items for a video.
    """

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

    timeline = (
        db.query(Timeline)
        .filter(
            Timeline.video_id == video_id
        )
        .order_by(
            Timeline.start_time
        )
        .all()
    )

    return timeline


# --------------------------------------------------
# Get single timeline item
# --------------------------------------------------

@router.get(
    "/{timeline_id}",
    response_model=TimelineResponse
)
def get_timeline_item(
    timeline_id: int,
    db: Session = Depends(get_db)
):
    """
    Get one timeline item.
    """

    timeline = (
        db.query(Timeline)
        .filter(
            Timeline.id == timeline_id
        )
        .first()
    )

    if not timeline:
        raise HTTPException(
            status_code=404,
            detail="Timeline item not found"
        )

    return timeline


# --------------------------------------------------
# Update timeline item
# --------------------------------------------------

@router.put(
    "/{timeline_id}",
    response_model=TimelineResponse
)
def update_timeline_item(
    timeline_id: int,
    timeline_data: TimelineUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing timeline item.

    This allows the frontend/editor to manually
    adjust timing, transition or text.
    """

    timeline = (
        db.query(Timeline)
        .filter(
            Timeline.id == timeline_id
        )
        .first()
    )

    if not timeline:
        raise HTTPException(
            status_code=404,
            detail="Timeline item not found"
        )

    # Determine new start time
    new_start = (
        timeline_data.start_time
        if timeline_data.start_time is not None
        else timeline.start_time
    )

    # Determine new end time
    new_end = (
        timeline_data.end_time
        if timeline_data.end_time is not None
        else timeline.end_time
    )

    # Validate time
    if new_end <= new_start:
        raise HTTPException(
            status_code=400,
            detail="end_time must be greater than start_time"
        )

    # Update start time
    if timeline_data.start_time is not None:
        timeline.start_time = (
            timeline_data.start_time
        )

    # Update end time
    if timeline_data.end_time is not None:
        timeline.end_time = (
            timeline_data.end_time
        )

    # Update transition
    if timeline_data.transition is not None:
        timeline.transition = (
            timeline_data.transition
        )

    # Update text overlay
    if timeline_data.text_overlay is not None:
        timeline.text_overlay = (
            timeline_data.text_overlay
        )

    db.commit()
    db.refresh(timeline)

    return timeline


# --------------------------------------------------
# Delete timeline item
# --------------------------------------------------

@router.delete(
    "/{timeline_id}"
)
def delete_timeline_item(
    timeline_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a timeline item.
    """

    timeline = (
        db.query(Timeline)
        .filter(
            Timeline.id == timeline_id
        )
        .first()
    )

    if not timeline:
        raise HTTPException(
            status_code=404,
            detail="Timeline item not found"
        )

    db.delete(timeline)
    db.commit()

    return {
        "message": "Timeline item deleted successfully"
    }