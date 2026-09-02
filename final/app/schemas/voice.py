from pydantic import BaseModel


class VoiceResponse(BaseModel):
    id: str
    name: str
    language: str
    gender: str


class VoiceListResponse(BaseModel):
    voices: list[VoiceResponse]