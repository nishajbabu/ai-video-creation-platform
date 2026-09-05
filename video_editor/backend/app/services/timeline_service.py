from sqlalchemy.orm import Session

from app.models.scene import Scene
from app.models.asset import Asset
from app.models.timeline import Timeline

from app.services.render_service import (
    get_local_path,
    get_scene_video,
    get_video_duration
)


def generate_timeline(
    db: Session,
    video_id: int,
    scenes: list[Scene],
    assets: list[Asset]
):
    """
    Automatically generate the complete timeline for a video.

    Timeline is calculated dynamically from:

        Scene order
            +
        Actual video duration

    Existing editing properties are preserved:

        - text_overlay
        - transition

    Example:

        Scene 1 = 5 seconds
        Scene 2 = 8 seconds
        Scene 3 = 6 seconds

    Generated timeline:

        Scene 1 -> 0  to 5
        Scene 2 -> 5  to 13
        Scene 3 -> 13 to 19

    If scenes are reordered, the timings are recalculated
    according to the new order while keeping each scene's
    existing text and transition.
    """

    # --------------------------------------------------
    # Validate scenes
    # --------------------------------------------------

    if not scenes:
        raise ValueError(
            "No scenes available for timeline generation"
        )

    # --------------------------------------------------
    # Sort scenes according to editor order
    # --------------------------------------------------

    ordered_scenes = sorted(
        scenes,
        key=lambda scene: scene.order
    )

    # --------------------------------------------------
    # Save existing editing properties
    # --------------------------------------------------
    #
    # Before deleting the old timeline records,
    # store text and transition for each scene.
    #
    # Example:
    #
    # Scene 7:
    #   text = "Beautiful Nature"
    #   transition = None
    #
    # Scene 8:
    #   text = "Travel Adventure"
    #   transition = "fade"
    #
    # --------------------------------------------------

    existing_timelines = (
        db.query(Timeline)
        .filter(
            Timeline.video_id == video_id
        )
        .all()
    )

    editing_properties = {}

    for timeline in existing_timelines:

        editing_properties[
            timeline.scene_id
        ] = {
            "transition": timeline.transition,
            "text_overlay": timeline.text_overlay
        }

    # --------------------------------------------------
    # Remove existing timeline
    # --------------------------------------------------

    db.query(Timeline).filter(
        Timeline.video_id == video_id
    ).delete(
        synchronize_session=False
    )

    db.flush()

    # --------------------------------------------------
    # Timeline calculation
    # --------------------------------------------------

    current_time = 0.0

    created_timelines = []

    # --------------------------------------------------
    # Process every scene
    # --------------------------------------------------

    for scene in ordered_scenes:

        # ----------------------------------------------
        # Find video asset
        # ----------------------------------------------

        video_url = get_scene_video(
            scene.id,
            assets
        )

        if not video_url:
            continue

        # ----------------------------------------------
        # Convert media URL to local path
        # ----------------------------------------------

        video_path = get_local_path(
            video_url
        )

        # ----------------------------------------------
        # Check file exists
        # ----------------------------------------------

        if not video_path.exists():
            continue

        # ----------------------------------------------
        # Get actual video duration
        # ----------------------------------------------

        duration = get_video_duration(
            video_path
        )

        if duration <= 0:
            continue

        # ----------------------------------------------
        # Calculate timeline position
        # ----------------------------------------------

        start_time = current_time

        end_time = (
            current_time + duration
        )

        # ----------------------------------------------
        # Get existing editing properties
        # ----------------------------------------------

        properties = editing_properties.get(
            scene.id,
            {}
        )

        transition = properties.get(
            "transition"
        )

        text_overlay = properties.get(
            "text_overlay"
        )

        # ----------------------------------------------
        # Create new timeline item
        # ----------------------------------------------

        timeline = Timeline(
            video_id=video_id,
            scene_id=scene.id,
            start_time=start_time,
            end_time=end_time,
            transition=transition,
            text_overlay=text_overlay
        )

        db.add(timeline)

        created_timelines.append(
            timeline
        )

        # ----------------------------------------------
        # Move current timeline position
        # ----------------------------------------------

        current_time = end_time

    # --------------------------------------------------
    # Make sure at least one scene was processed
    # --------------------------------------------------

    if not created_timelines:

        db.rollback()

        raise ValueError(
            "No valid scene videos available "
            "for timeline generation"
        )

    # --------------------------------------------------
    # Save changes
    # --------------------------------------------------

    db.commit()

    # --------------------------------------------------
    # Refresh database objects
    # --------------------------------------------------

    for timeline in created_timelines:

        db.refresh(
            timeline
        )

    # --------------------------------------------------
    # Return generated timeline
    # --------------------------------------------------

    return created_timelines