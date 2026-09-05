from pydantic import BaseModel, ConfigDict, Field


class SceneBase(BaseModel):
    title: str | None = None
    duration: float = Field(default=5.0, gt=0)


class SceneCreate(SceneBase):
    video_id: int
    order: int = Field(ge=1)


class SceneUpdate(BaseModel):
    title: str | None = None
    duration: float | None = Field(default=None, gt=0)
    order: int | None = Field(default=None, ge=1)

class SceneReorder(BaseModel):
    scene_ids: list[int]


class SceneResponse(SceneBase):
    id: int
    video_id: int
    order: int

    model_config = ConfigDict(from_attributes=True)
