from pydantic import BaseModel, Field

from app.schemas.scene import SceneGenerateRequest, SceneGenerateResponse


class ProjectGenerateRequest(BaseModel):

    project_id: str = Field(..., min_length=1)

    scenes: list[SceneGenerateRequest] = Field(
        ...,
        min_length=1,
    )


class ProjectGenerateResponse(BaseModel):

    project_id: str

    scenes: list[SceneGenerateResponse]