from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.video import Video
from app.models.scene import Scene
from app.models.asset import Asset
from app.models.timeline import Timeline

from app.schemas.project import ProjectGenerateResponse


router = APIRouter(
    prefix="/integration",
    tags=["Integration"],
)


@router.post("/project-to-editor")
def import_project_to_editor(
    project: ProjectGenerateResponse,
    db: Session = Depends(get_db),
):
    """
    Import an AI-generated project into the Video Editor.

    AI project
        ↓
    Video
        ↓
    Editor scenes
        ↓
    Image/audio/video assets
        ↓
    Timeline
    """

    # --------------------------------------------------
    # Check whether this project already exists
    # --------------------------------------------------

    existing_video = (
        db.query(Video)
        .filter(
            Video.title == project.project_id
        )
        .first()
    )

    if existing_video:
        raise HTTPException(
            status_code=409,
            detail=(
                "This project has already been "
                "imported into the editor."
            ),
        )

    # --------------------------------------------------
    # Create editor video
    # --------------------------------------------------

    video = Video(
        title=project.project_id,
        total_duration=0.0,
    )

    db.add(video)
    db.flush()

    # --------------------------------------------------
    # Create scenes
    # --------------------------------------------------

    current_time = 0.0
    created_scenes = []

    for index, generated_scene in enumerate(
        project.scenes,
        start=1,
    ):

        duration = 5.0

        scene = Scene(
            video_id=video.id,
            order=index,
            duration=duration,
            title=f"Scene {generated_scene.scene_id}",
        )

        db.add(scene)
        db.flush()

        created_scenes.append(scene)

        # ----------------------------------------------
        # Image asset
        # ----------------------------------------------

        if generated_scene.image_url:

            db.add(
                Asset(
                    scene_id=scene.id,
                    asset_type="image",
                    file_url=generated_scene.image_url,
                )
            )

        # ----------------------------------------------
        # Audio asset
        # ----------------------------------------------

        if generated_scene.audio_url:

            db.add(
                Asset(
                    scene_id=scene.id,
                    asset_type="audio",
                    file_url=generated_scene.audio_url,
                )
            )

        # ----------------------------------------------
        # Video asset
        # ----------------------------------------------

        if generated_scene.video_url:

            db.add(
                Asset(
                    scene_id=scene.id,
                    asset_type="video",
                    file_url=generated_scene.video_url,
                )
            )

        # ----------------------------------------------
        # Initial timeline
        # ----------------------------------------------

        timeline = Timeline(
            video_id=video.id,
            scene_id=scene.id,
            start_time=current_time,
            end_time=current_time + duration,
            transition=None,
            text_overlay=None,
        )

        db.add(timeline)

        current_time += duration

    # --------------------------------------------------
    # Update total duration
    # --------------------------------------------------

    video.total_duration = current_time

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    db.commit()
    db.refresh(video)

    return {
        "message": (
            "Project imported into "
            "video editor successfully"
        ),
        "video_id": video.id,
        "project_id": project.project_id,
        "total_duration": video.total_duration,
        "scene_count": len(created_scenes),
        "editor_url": f"/editor/{video.id}",
    }