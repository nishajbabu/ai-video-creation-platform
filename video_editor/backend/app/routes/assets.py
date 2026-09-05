from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset import Asset
from app.models.scene import Scene
from app.schemas.asset import AssetCreate, AssetResponse


router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)


ALLOWED_ASSET_TYPES = {
    "image",
    "video",
    "audio"
}


@router.post("/", response_model=AssetResponse)
def create_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db)
):
    # Check asset type
    if asset_data.asset_type not in ALLOWED_ASSET_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid asset type. "
                "Allowed types: image, video, audio"
            )
        )

    # Check scene exists
    scene = (
        db.query(Scene)
        .filter(Scene.id == asset_data.scene_id)
        .first()
    )

    if not scene:
        raise HTTPException(
            status_code=404,
            detail="Scene not found"
        )

    asset = Asset(
        scene_id=asset_data.scene_id,
        asset_type=asset_data.asset_type,
        file_url=asset_data.file_url
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


@router.get("/", response_model=list[AssetResponse])
def get_assets(
    db: Session = Depends(get_db)
):
    return db.query(Asset).all()


@router.get(
    "/scene/{scene_id}",
    response_model=list[AssetResponse]
)
def get_scene_assets(
    scene_id: int,
    db: Session = Depends(get_db)
):
    # Check scene exists
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

    return (
        db.query(Asset)
        .filter(Asset.scene_id == scene_id)
        .all()
    )


@router.get(
    "/{asset_id}",
    response_model=AssetResponse
)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    return asset


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id)
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    db.delete(asset)
    db.commit()

    return {
        "message": "Asset deleted successfully"
    }