from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoResponse


router = APIRouter(
    prefix="/videos",
    tags=["Videos"]
)


@router.post("/", response_model=VideoResponse)
def create_video(
    video_data: VideoCreate,
    db: Session = Depends(get_db)
):
    video = Video(
        title=video_data.title,
        total_duration=video_data.total_duration
    )

    db.add(video)
    db.commit()
    db.refresh(video)

    return video


@router.get("/", response_model=list[VideoResponse])
def get_videos(
    db: Session = Depends(get_db)
):
    return db.query(Video).all()


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    return video


@router.delete("/{video_id}")
def delete_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    db.delete(video)
    db.commit()

    return {
        "message": "Video deleted successfully"
    }