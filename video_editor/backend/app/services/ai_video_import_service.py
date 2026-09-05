from sqlalchemy.orm import Session

from app.models.video import Video
from app.models.scene import Scene
from app.models.asset import Asset
from app.models.timeline import Timeline


class AIVideoImportError(Exception):
    """Raised when AI-generated media cannot be imported into the editor."""


def import_generated_project(
    db: Session,
    project_result: dict,
) -> Video:
    """
    Convert an AI-generated project into Video Editor
    database records.

    AI scene IDs and database scene IDs are intentionally
    kept separate.

    AI result:

    {
        "project_id": "...",
        "scenes": [
            {
                "scene_id": 1,
                "audio_path": "...",
                "image_path": "...",
                "video_path": "...",
                "audio_url": "...",
                "image_url": "...",
                "video_url": "..."
            }
        ]
    }

    Database:

        Video
          |
          +-- Scene(id=...)
          |     +-- image Asset
          |     +-- audio Asset
          |     +-- Timeline
          |
          +-- Scene(id=...)
                +-- image Asset
                +-- audio Asset
                +-- Timeline

    IMPORTANT:

    generated_scene["scene_id"]
        = AI scene ID

    scene.id
        = database scene ID

    Assets and Timeline ALWAYS use scene.id.
    """

    # --------------------------------------------------
    # Validate project result
    # --------------------------------------------------

    project_id = project_result.get("project_id")

    generated_scenes = project_result.get(
        "scenes",
        [],
    )

    if not project_id:
        raise AIVideoImportError(
            "AI generation result does not contain project_id."
        )

    if not generated_scenes:
        raise AIVideoImportError(
            "AI generation result does not contain any scenes."
        )

    try:

        # --------------------------------------------------
        # Create editor Video
        # --------------------------------------------------

        video = Video(
            title=project_id,
            total_duration=0.0,
        )

        db.add(video)

        # Get database Video ID
        db.flush()

        current_time = 0.0

        # --------------------------------------------------
        # Create scenes
        # --------------------------------------------------

        for index, generated_scene in enumerate(
            generated_scenes,
            start=1,
        ):

            # ----------------------------------------------
            # AI scene ID
            # ----------------------------------------------

            ai_scene_id = generated_scene.get(
                "scene_id",
                index,
            )

            # ----------------------------------------------
            # Duration
            # ----------------------------------------------

            scene_duration = float(
                generated_scene.get(
                    "duration",
                    5.0,
                )
                or 5.0
            )

            if scene_duration <= 0:
                scene_duration = 5.0

            # ----------------------------------------------
            # Text
            # ----------------------------------------------

            text_overlay = (
                generated_scene.get(
                    "text_overlay"
                )
                or generated_scene.get(
                    "title"
                )
                or f"Scene {ai_scene_id}"
            )

            # ----------------------------------------------
            # Transition
            # ----------------------------------------------

            transition = (
                generated_scene.get(
                    "transition"
                )
                or "fade"
            )

            # ----------------------------------------------
            # Create DB Scene
            # ----------------------------------------------

            scene = Scene(
                video_id=video.id,
                order=index,
                duration=scene_duration,
                title=f"Scene {ai_scene_id}",
            )

            db.add(scene)

            # VERY IMPORTANT:
            #
            # This obtains the actual database scene ID.
            #
            # Example:
            #
            # AI scene_id = 1
            # DB scene.id = 15
            #
            db.flush()

            database_scene_id = scene.id

            # ----------------------------------------------
            # Get generated media URLs
            # ----------------------------------------------

            image_url = generated_scene.get(
                "image_url"
            )

            audio_url = generated_scene.get(
                "audio_url"
            )

            video_url = generated_scene.get(
                "video_url"
            )

            # ----------------------------------------------
            # Image Asset
            # ----------------------------------------------

            if image_url:

                image_asset = Asset(
                    scene_id=database_scene_id,
                    asset_type="image",
                    file_url=image_url,
                )

                db.add(image_asset)

            # ----------------------------------------------
            # Audio Asset
            # ----------------------------------------------

            if audio_url:

                audio_asset = Asset(
                    scene_id=database_scene_id,
                    asset_type="audio",
                    file_url=audio_url,
                )

                db.add(audio_asset)

            # ----------------------------------------------
            # Video Asset
            #
            # Keep this only if the AI generator actually
            # generated a video.
            #
            # Our final renderer can work directly from
            # image + audio, so this is optional.
            # ----------------------------------------------

            if video_url:

                video_asset = Asset(
                    scene_id=database_scene_id,
                    asset_type="video",
                    file_url=video_url,
                )

                db.add(video_asset)

            # ----------------------------------------------
            # Make sure scene has visual media
            # ----------------------------------------------

            if not image_url and not video_url:

                raise AIVideoImportError(
                    f"Scene {ai_scene_id} does not contain "
                    "an image or video."
                )

            # ----------------------------------------------
            # Timeline
            # ----------------------------------------------

            timeline = Timeline(
                video_id=video.id,

                # IMPORTANT:
                # Use DATABASE scene ID.
                scene_id=database_scene_id,

                start_time=current_time,

                end_time=(
                    current_time
                    + scene_duration
                ),

                transition=transition,

                text_overlay=text_overlay,
            )

            db.add(timeline)

            # ----------------------------------------------
            # Move timeline forward
            # ----------------------------------------------

            current_time += scene_duration

        # --------------------------------------------------
        # Update total duration
        # --------------------------------------------------

        video.total_duration = current_time

        # --------------------------------------------------
        # Save everything atomically
        # --------------------------------------------------

        db.commit()

        db.refresh(video)

        return video

    except AIVideoImportError:

        db.rollback()

        raise

    except Exception as exc:

        db.rollback()

        raise AIVideoImportError(
            "Failed to import AI-generated project: "
            f"{exc}"
        ) from exc