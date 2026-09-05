from pydantic import BaseModel, Field


class Scene(BaseModel):

    scene_id: int = Field(..., ge=1)

    narration: str = Field(
        ...,
        min_length=1,
    )

    visual_prompt: str = Field(
        ...,
        min_length=1,
    )


class SceneGenerateRequest(BaseModel):

    scene_id: int = Field(..., ge=1)

    narration: str = Field(
        ...,
        min_length=1,
    )

    visual_prompt: str = Field(
        ...,
        min_length=1,
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
        min_length=1,
    )


class MultiSceneGenerateResponse(BaseModel):

    scenes: list[SceneGenerateResponse]