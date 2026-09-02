from pydantic import BaseModel, Field

from app.schemas.scene import (
    SceneGenerateRequest,
    SceneGenerateResponse,
)


class ProjectGenerateRequest(BaseModel):

    project_id: str = Field(
        ...,
        min_length=1,
    )

    scenes: list[SceneGenerateRequest] = Field(
        ...,
        min_length=1,
    )


class ProjectGenerateResponse(BaseModel):

    project_id: str

    video_id: int

    scenes: list[SceneGenerateResponse]

    final_video_path: str

    final_video_url: str