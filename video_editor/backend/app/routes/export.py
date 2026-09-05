from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db

from app.models.video import Video
from app.models.scene import Scene
from app.models.asset import Asset
from app.models.timeline import Timeline

from app.services.render_service import render_video


router = APIRouter(
    prefix="/export",
    tags=["Export"],
)


@router.post("/{video_id}")
def export_video(
    video_id: int,
    db: Session = Depends(get_db),
):
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
            detail="Video not found",
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
            detail="Video has no scenes",
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

    if not assets:
        raise HTTPException(
            status_code=400,
            detail="No media assets found for this video",
        )

    # --------------------------------------------------
    # Validate that every scene has a video/image asset
    # --------------------------------------------------

    assets_by_scene = {}

    for asset in assets:
        assets_by_scene.setdefault(
            asset.scene_id,
            []
        ).append(asset)

    for scene in scenes:

        scene_assets = assets_by_scene.get(
            scene.id,
            []
        )

        if not scene_assets:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No assets found for scene "
                    f"{scene.id}"
                ),
            )

    # --------------------------------------------------
    # Get timeline
    # --------------------------------------------------

    timeline_items = (
        db.query(Timeline)
        .filter(
            Timeline.video_id == video_id
        )
        .order_by(
            Timeline.start_time
        )
        .all()
    )

    if not timeline_items:
        raise HTTPException(
            status_code=400,
            detail=(
                "No timeline found for this video. "
                "Generate the timeline before exporting."
            ),
        )

    # --------------------------------------------------
    # Render final video
    # --------------------------------------------------

    try:

        result = render_video(
            video_id=video_id,
            scenes=scenes,
            assets=assets,
            timeline_items=timeline_items,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Video rendering failed: {error}"
            ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unexpected video rendering error: "
                f"{error}"
            ),
        ) from error

    # --------------------------------------------------
    # Build public URL
    # --------------------------------------------------

    file_url = result.get("file_url")

    if not file_url:
        raise HTTPException(
            status_code=500,
            detail="Video renderer did not return a file URL.",
        )

    # If renderer returns a local media path,
    # convert it into the API's public URL.
    if not file_url.startswith("http://") and not file_url.startswith("https://"):

        normalized_path = file_url.replace("\\", "/")

        if normalized_path.startswith("/"):
            normalized_path = normalized_path[1:]

        file_url = (
            f"{settings.base_url}/"
            f"{normalized_path}"
        )

    # --------------------------------------------------
    # Response
    # --------------------------------------------------

    return {
        "message": "Video exported successfully",
        "video_id": video_id,
        "file_url": file_url,
    }