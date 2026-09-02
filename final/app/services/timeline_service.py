from sqlalchemy.orm import Session

from app.models.scene import Scene
from app.models.asset import Asset
from app.models.timeline import Timeline

from app.services.render_service import (
    get_local_path,
    get_scene_video,
    get_scene_audio,
    get_video_duration,
)


# ============================================================
# GENERATE TIMELINE
# ============================================================

def generate_timeline(
    db: Session,
    video_id: int,
    scenes: list[Scene],
    assets: list[Asset],
):
    """
    Automatically generate the complete timeline for a video.

    Duration priority for each scene:

        1. Actual generated video duration
        2. Actual audio duration
        3. Scene.duration

    This allows the editor to work with:

        image + audio

    even when a video asset is not available.

    Example:

        Scene 1 = 4.2 seconds
        Scene 2 = 5.7 seconds
        Scene 3 = 6.1 seconds

    Timeline:

        Scene 1 -> 0.0  to 4.2
        Scene 2 -> 4.2  to 9.9
        Scene 3 -> 9.9  to 16.0

    Existing editing properties are preserved:

        - text_overlay
        - transition
    """

    # ========================================================
    # 1. VALIDATE
    # ========================================================

    if not scenes:

        raise ValueError(
            "No scenes available for timeline generation."
        )

    # Make sure scenes belong to the requested video.
    invalid_scenes = [
        scene.id
        for scene in scenes
        if scene.video_id != video_id
    ]

    if invalid_scenes:

        raise ValueError(
            "Some scenes do not belong to the specified video: "
            f"{invalid_scenes}"
        )

    # ========================================================
    # 2. SORT BY EDITOR ORDER
    # ========================================================

    ordered_scenes = sorted(
        scenes,
        key=lambda scene: scene.order,
    )

    # ========================================================
    # 3. SAVE EXISTING EDITING PROPERTIES
    # ========================================================

    existing_timelines = (
        db.query(Timeline)
        .filter(
            Timeline.video_id == video_id
        )
        .all()
    )

    editing_properties = {}

    for timeline in existing_timelines:

        editing_properties[timeline.scene_id] = {
            "transition": timeline.transition,
            "text_overlay": timeline.text_overlay,
        }

    # ========================================================
    # 4. REMOVE OLD TIMELINE
    # ========================================================

    db.query(Timeline).filter(
        Timeline.video_id == video_id
    ).delete(
        synchronize_session=False
    )

    db.flush()

    # ========================================================
    # 5. GENERATE NEW TIMELINE
    # ========================================================

    current_time = 0.0

    created_timelines = []

    for scene in ordered_scenes:

        # ----------------------------------------------------
        # Find generated video asset
        # ----------------------------------------------------

        video_url = get_scene_video(
            scene.id,
            assets,
        )

        # ----------------------------------------------------
        # Find generated audio asset
        # ----------------------------------------------------

        audio_url = get_scene_audio(
            scene.id,
            assets,
        )

        duration = None

        # ====================================================
        # PRIORITY 1: ACTUAL VIDEO DURATION
        # ====================================================

        if video_url:

            try:

                video_path = get_local_path(
                    video_url
                )

                if video_path.exists():

                    detected_duration = (
                        get_video_duration(
                            video_path
                        )
                    )

                    if detected_duration > 0:

                        duration = float(
                            detected_duration
                        )

            except (
                OSError,
                ValueError,
                RuntimeError,
            ):

                # If video duration cannot be read,
                # fall back to audio or scene duration.
                duration = None

        # ====================================================
        # PRIORITY 2: ACTUAL AUDIO DURATION
        # ====================================================

        if duration is None and audio_url:

            try:

                audio_path = get_local_path(
                    audio_url
                )

                if audio_path.exists():

                    detected_duration = (
                        get_video_duration(
                            audio_path
                        )
                    )

                    if detected_duration > 0:

                        duration = float(
                            detected_duration
                        )

            except (
                OSError,
                ValueError,
                RuntimeError,
            ):

                duration = None

        # ====================================================
        # PRIORITY 3: SCENE DURATION
        # ====================================================

        if duration is None:

            if (
                scene.duration is not None
                and scene.duration > 0
            ):

                duration = float(
                    scene.duration
                )

            else:

                raise ValueError(
                    f"Scene {scene.id} has no valid duration."
                )

        # ====================================================
        # UPDATE SCENE DURATION
        # ====================================================

        scene.duration = duration

        # ====================================================
        # CALCULATE TIMELINE POSITION
        # ====================================================

        start_time = current_time

        end_time = (
            current_time + duration
        )

        # ====================================================
        # RESTORE EDITING PROPERTIES
        # ====================================================

        properties = editing_properties.get(
            scene.id,
            {},
        )

        transition = properties.get(
            "transition"
        )

        text_overlay = properties.get(
            "text_overlay"
        )

        # ====================================================
        # CREATE TIMELINE RECORD
        # ====================================================

        timeline = Timeline(
            video_id=video_id,
            scene_id=scene.id,
            start_time=start_time,
            end_time=end_time,
            transition=transition,
            text_overlay=text_overlay,
        )

        db.add(timeline)

        created_timelines.append(
            timeline
        )

        # ====================================================
        # MOVE CURRENT POSITION
        # ====================================================

        current_time = end_time

    # ========================================================
    # 6. VALIDATE RESULT
    # ========================================================

    if not created_timelines:

        db.rollback()

        raise ValueError(
            "No valid scenes were available "
            "for timeline generation."
        )

    # ========================================================
    # 7. SAVE
    # ========================================================

    db.commit()

    # ========================================================
    # 8. REFRESH
    # ========================================================

    for timeline in created_timelines:

        db.refresh(
            timeline
        )

    # ========================================================
    # 9. RETURN
    # ========================================================

    return created_timelines