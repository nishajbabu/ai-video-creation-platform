from pydantic import BaseModel, Field


class TTSGenerateRequest(BaseModel):
    text: str = Field(..., min_length=1)

    voice_id: str = Field(..., min_length=1)

    filename: str = Field(..., min_length=1)


class TTSGenerateResponse(BaseModel):
    message: str

    audio_path: str

    audio_url: str