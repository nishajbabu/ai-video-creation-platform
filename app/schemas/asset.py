from pydantic import BaseModel, ConfigDict


class AssetCreate(BaseModel):
    scene_id: int
    asset_type: str
    file_url: str


class AssetResponse(AssetCreate):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )