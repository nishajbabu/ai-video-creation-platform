from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.providers.tts.edge_tts_provider import EdgeTTSProvider
from app.schemas.tts import TTSGenerateRequest, TTSGenerateResponse
from app.services.tts_service import TTSGenerationError, TTSService
from app.storage.local_storage import LocalMediaStorage


router = APIRouter(
    prefix="/api/v1/tts",
    tags=["TTS"],
)


@router.post(
    "/generate",
    response_model=TTSGenerateResponse,
)
def generate_speech(request: TTSGenerateRequest):
    provider = EdgeTTSProvider()
    storage = LocalMediaStorage()
    service = TTSService(provider, storage)

    try:
        audio_path = service.generate_audio(
            text=request.text,
            voice_id=request.voice_id,
            filename=request.filename,
        )

        media_path = audio_path.replace("\\", "/")

        audio_url = (
            f"{settings.base_url.rstrip('/')}/{media_path}"
        )

        return TTSGenerateResponse(
            message="Speech generated successfully.",
            audio_path=media_path,
            audio_url=audio_url,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except TTSGenerationError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc