from pydantic import BaseModel, Field, model_validator


class TimelineCreate(BaseModel):
    video_id: int
    scene_id: int
    start_time: float = Field(ge=0)
    end_time: float = Field(gt=0)
    transition: str | None = None
    text_overlay: str | None = None

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError(
                "end_time must be greater than start_time"
            )
        return self


class TimelineUpdate(BaseModel):
    start_time: float | None = Field(default=None, ge=0)
    end_time: float | None = Field(default=None, gt=0)
    transition: str | None = None
    text_overlay: str | None = None


class TimelineResponse(TimelineCreate):
    id: int

    model_config = {
        "from_attributes": True
    }


class EditorSceneUpdate(BaseModel):
    duration: float | None = Field(
        default=None,
        gt=0
    )

    text_overlay: str | None = None

    transition: str | None = None

    start_time: float | None = Field(
        default=None,
        ge=0
    )

    end_time: float | None = Field(
        default=None,
        gt=0
    )