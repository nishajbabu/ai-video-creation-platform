from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AssetBase(BaseModel):
    scene_id: Optional[int] = Field(
        default=None,
        description="Scene associated with the asset.",
    )

    asset_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Type of asset, such as image, video, audio, or logo.",
    )

    description: str = Field(
        ...,
        min_length=1,
        description="Description of the asset.",
    )

    source: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Origin of the asset.",
    )

    file_path: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Local file path when the asset is stored locally.",
    )

    url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="External URL when the asset is externally hosted.",
    )


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    scene_id: Optional[int] = None

    asset_type: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    description: Optional[str] = Field(
        default=None,
        min_length=1,
    )

    source: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    file_path: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    url: Optional[str] = Field(
        default=None,
        max_length=2000,
    )


class Asset(AssetBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    asset_id: int = Field(
        ...,
        description="Unique database identifier of the asset.",
    )

    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the asset was created.",
    )
