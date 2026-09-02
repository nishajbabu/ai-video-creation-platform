"""
Asset API routes.

This module exposes HTTP endpoints for managing generated-scene
assets.

Business logic is delegated to AssetService.
Database persistence is handled by AssetRepository.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_asset_service
from app.models.asset import AssetModel
from app.schemas.asset import Asset, AssetCreate, AssetUpdate
from app.services.asset_service import AssetService


router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def _to_schema(
    asset: AssetModel,
) -> Asset:
    """
    Convert a database AssetModel into the public API Asset schema.
    """

    return Asset.model_validate(
        asset,
    )


def _to_schema_list(
    assets: List[AssetModel],
) -> List[Asset]:
    """
    Convert a list of AssetModel objects into API schemas.
    """

    return [
        _to_schema(asset)
        for asset in assets
    ]


def _to_model(
    asset: AssetCreate,
) -> AssetModel:
    """
    Convert an AssetCreate request into an AssetModel.
    """

    return AssetModel(
        scene_id=asset.scene_id,
        asset_type=asset.asset_type,
        description=asset.description,
        source=asset.source,
        file_path=asset.file_path,
        url=asset.url,
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=Asset,
    status_code=status.HTTP_201_CREATED,
)
def create_asset(
    asset: AssetCreate,
    service: AssetService = Depends(
        get_asset_service,
    ),
) -> Asset:
    """
    Create a new asset.
    """

    model = _to_model(
        asset,
    )

    try:
        created = service.create_asset(
            model,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return _to_schema(
        created,
    )


# ---------------------------------------------------------------------------
# List all assets
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[Asset],
)
def list_assets(
    service: AssetService = Depends(
        get_asset_service,
    ),
) -> List[Asset]:
    """
    Return all stored assets.
    """

    return _to_schema_list(
        service.list_assets(),
    )


# ---------------------------------------------------------------------------
# List assets for a scene
#
# IMPORTANT:
# This route must appear before /{asset_id}.
# ---------------------------------------------------------------------------

@router.get(
    "/scene/{scene_id}",
    response_model=List[Asset],
)
def get_assets_for_scene(
    scene_id: int,
    service: AssetService = Depends(
        get_asset_service,
    ),
) -> List[Asset]:
    """
    Return all assets belonging to a scene.
    """

    assets = service.get_assets_for_scene(
        scene_id,
    )

    return _to_schema_list(
        assets,
    )


# ---------------------------------------------------------------------------
# List unassigned assets
#
# IMPORTANT:
# This route must appear before /{asset_id}.
# Otherwise "unassigned" would be interpreted as asset_id.
# ---------------------------------------------------------------------------

@router.get(
    "/unassigned",
    response_model=List[Asset],
)
def list_unassigned_assets(
    service: AssetService = Depends(
        get_asset_service,
    ),
) -> List[Asset]:
    """
    Return assets that are not assigned to a scene.
    """

    return _to_schema_list(
        service.list_unassigned_assets(),
    )


# ---------------------------------------------------------------------------
# Get asset by ID
#
# This dynamic route intentionally comes AFTER the static routes above.
# ---------------------------------------------------------------------------

@router.get(
    "/{asset_id}",
    response_model=Asset,
)
def get_asset(
    asset_id: int,
    service: AssetService = Depends(
        get_asset_service,
    ),
) -> Asset:
    """
    Return an asset by its identifier.
    """

    asset = service.get_asset(
        asset_id,
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Asset '{asset_id}' "
                "was not found."
            ),
        )

    return _to_schema(
        asset,
    )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@router.put(
    "/{asset_id}",
    response_model=Asset,
)
def update_asset(
    asset_id: int,
    asset: AssetUpdate,
    service: AssetService = Depends(
        get_asset_service,
    ),
) -> Asset:
    """
    Update selected fields of an existing asset.
    """

    updated = service.update_asset(
        asset_id,
        asset_type=asset.asset_type,
        description=asset.description,
        source=asset.source,
        file_path=asset.file_path,
        url=asset.url,
        scene_id=asset.scene_id,
    )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Asset '{asset_id}' "
                "was not found."
            ),
        )

    return _to_schema(
        updated,
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_asset(
    asset_id: int,
    service: AssetService = Depends(
        get_asset_service,
    ),
) -> None:
    """
    Delete an existing asset.
    """

    deleted = service.delete_asset(
        asset_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Asset '{asset_id}' "
                "was not found."
            ),
        )