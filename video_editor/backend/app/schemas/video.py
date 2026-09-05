from pydantic import BaseModel, ConfigDict


class VideoBase(BaseModel):
    title: str
    total_duration: float = 0.0


class VideoCreate(VideoBase):
    pass


class VideoResponse(VideoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)