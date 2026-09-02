from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# AI SCENE SCHEMAS
# ============================================================

class Scene(BaseModel):

    scene_id: int = Field(
        ...,
        ge=1
    )

    narration: str = Field(
        ...,
        min_length=1
    )

    visual_prompt: str = Field(
        ...,
        min_length=1
    )


class SceneGenerateRequest(BaseModel):

    scene_id: int = Field(
        ...,
        ge=1
    )

    narration: str = Field(
        ...,
        min_length=1
    )

    visual_prompt: str = Field(
        ...,
        min_length=1
    )

    voice: str | None = None


class SceneGenerateResponse(BaseModel):

    scene_id: int

    audio_path: str
    image_path: str
    video_path: str

    audio_url: str
    image_url: str
    video_url: str


class MultiSceneGenerateRequest(BaseModel):

    scenes: list[SceneGenerateRequest] = Field(
        ...,
        min_length=1
    )


class MultiSceneGenerateResponse(BaseModel):

    scenes: list[SceneGenerateResponse]


# ============================================================
# VIDEO EDITOR SCHEMAS
# ============================================================

class SceneBase(BaseModel):

    title: str | None = None

    duration: float = Field(
        default=5.0,
        gt=0
    )


class SceneCreate(SceneBase):

    video_id: int

    order: int = Field(
        ge=1
    )


class SceneUpdate(BaseModel):

    title: str | None = None

    duration: float | None = Field(
        default=None,
        gt=0
    )

    order: int | None = Field(
        default=None,
        ge=1
    )


class SceneReorder(BaseModel):

    scene_ids: list[int]


class SceneResponse(SceneBase):

    id: int
    video_id: int
    order: int

    model_config = ConfigDict(
        from_attributes=True
    )