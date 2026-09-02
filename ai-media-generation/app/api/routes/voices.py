from fastapi import APIRouter, HTTPException, Query

from app.providers.tts.edge_tts_voice_provider import EdgeTTSVoiceProvider
from app.schemas.voice import VoiceListResponse
from app.services.voice_service import VoiceService


router = APIRouter(
    prefix="/api/v1/tts",
    tags=["TTS"],
)


@router.get(
    "/voices",
    response_model=VoiceListResponse,
)
def list_voices(
    language: str | None = Query(
        default=None,
        description="Filter voices by language/locale, e.g. en-US or ta-IN.",
    ),
):
    provider = EdgeTTSVoiceProvider()
    service = VoiceService(provider)

    try:
        voices = service.list_voices()

        if language:
            voices = [
                voice
                for voice in voices
                if voice["language"].lower() == language.lower()
            ]

        return VoiceListResponse(
            voices=voices,
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc