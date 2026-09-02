from pathlib import Path
import shutil
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.scene import Scene
from app.models.asset import Asset


router = APIRouter(
    prefix="/media",
    tags=["Media"]
)


BASE_MEDIA_DIR = Path("media")

IMAGE_DIR = BASE_MEDIA_DIR / "images"
VIDEO_DIR = BASE_MEDIA_DIR / "videos"
AUDIO_DIR = BASE_MEDIA_DIR / "audio"


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".webm"
}

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a"
}


for directory in [
    IMAGE_DIR,
    VIDEO_DIR,
    AUDIO_DIR
]:
    directory.mkdir(
        parents=True,
        exist_ok=True
    )


def get_asset_directory(asset_type: str):
    if asset_type == "image":
        return IMAGE_DIR

    if asset_type == "video":
        return VIDEO_DIR

    if asset_type == "audio":
        return AUDIO_DIR

    raise HTTPException(
        status_code=400,
        detail="Invalid asset type"
    )


def validate_extension(
    filename: str,
    asset_type: str
):
    extension = Path(filename).suffix.lower()

    if asset_type == "image":
        allowed = IMAGE_EXTENSIONS

    elif asset_type == "video":
        allowed = VIDEO_EXTENSIONS

    elif asset_type == "audio":
        allowed = AUDIO_EXTENSIONS

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid asset type"
        )

    if extension not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {extension}"
            )
        )


@router.post("/upload/{scene_id}")
def upload_media(
    scene_id: int,
    asset_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # -----------------------------------
    # Check asset type
    # -----------------------------------

    if asset_type not in {
        "image",
        "video",
        "audio"
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "asset_type must be "
                "image, video, or audio"
            )
        )

    # -----------------------------------
    # Check scene
    # -----------------------------------

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

    # -----------------------------------
    # Check filename
    # -----------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is missing"
        )

    validate_extension(
        file.filename,
        asset_type
    )

    # -----------------------------------
    # Generate safe filename
    # -----------------------------------

    extension = Path(
        file.filename
    ).suffix.lower()

    unique_filename = (
        f"{uuid.uuid4().hex}{extension}"
    )

    directory = get_asset_directory(
        asset_type
    )

    file_path = directory / unique_filename

    # -----------------------------------
    # Save file
    # -----------------------------------

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    # -----------------------------------
    # URL
    # -----------------------------------

    file_url = (
        f"/media/{asset_type}s/"
        f"{unique_filename}"
    )

    # -----------------------------------
    # Save asset in database
    # -----------------------------------

    asset = Asset(
        scene_id=scene_id,
        asset_type=asset_type,
        file_url=file_url
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return {
        "message": "Media uploaded successfully",
        "asset": {
            "id": asset.id,
            "scene_id": asset.scene_id,
            "asset_type": asset.asset_type,
            "file_url": asset.file_url
        }
    }