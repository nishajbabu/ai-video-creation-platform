from pydantic import BaseModel, Field


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)


class ImageGenerateResponse(BaseModel):
    message: str
    image_path: str
    image_url: str