from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.providers.image.huggingface_provider import (
    HuggingFaceImageProvider,
)
from app.providers.tts.edge_tts_provider import EdgeTTSProvider
from app.schemas.scene import (
    MultiSceneGenerateRequest,
    MultiSceneGenerateResponse,
    Scene,
    SceneGenerateRequest,
    SceneGenerateResponse,
)
from app.services.scene_service import (
    SceneGenerationError,
    SceneService,
)
from app.storage.local_storage import LocalMediaStorage


router = APIRouter(
    prefix="/api/v1/scenes",
    tags=["Scenes"],
)


@router.post(
    "/generate",
    response_model=SceneGenerateResponse,
)
def generate_scene(request: SceneGenerateRequest):
    tts_provider = EdgeTTSProvider()
    image_provider = HuggingFaceImageProvider()
    storage = LocalMediaStorage()

    service = SceneService(
        tts_provider=tts_provider,
        image_provider=image_provider,
        storage=storage,
    )

    try:
        result = service.generate_scene(
            scene=request,
            voice_id=request.voice_id,
        )

        audio_url = (
            f"{settings.base_url}/"
            f"{result['audio_path'].replace(chr(92), '/')}"
        )

        image_url = (
            f"{settings.base_url}/"
            f"{result['image_path'].replace(chr(92), '/')}"
        )

        return SceneGenerateResponse(
            scene_id=result["scene_id"],
            audio_path=result["audio_path"],
            image_path=result["image_path"],
            audio_url=audio_url,
            image_url=image_url,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except SceneGenerationError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post(
    "/generate-batch",
    response_model=MultiSceneGenerateResponse,
)
def generate_scenes(
    request: MultiSceneGenerateRequest,
):
    tts_provider = EdgeTTSProvider()
    image_provider = HuggingFaceImageProvider()
    storage = LocalMediaStorage()

    service = SceneService(
        tts_provider=tts_provider,
        image_provider=image_provider,
        storage=storage,
    )

    try:
        scenes = [
            Scene(
                scene_id=scene.scene_id,
                narration=scene.narration,
                visual_prompt=scene.visual_prompt,
            )
            for scene in request.scenes
        ]

        voice_ids = [
            scene.voice_id
            for scene in request.scenes
        ]

        results = service.generate_scenes(
            scenes=scenes,
            voice_ids=voice_ids,
        )

        responses = []

        for result in results:
            audio_url = (
                f"{settings.base_url}/"
                f"{result['audio_path'].replace(chr(92), '/')}"
            )

            image_url = (
                f"{settings.base_url}/"
                f"{result['image_path'].replace(chr(92), '/')}"
            )

            responses.append(
                SceneGenerateResponse(
                    scene_id=result["scene_id"],
                    audio_path=result["audio_path"],
                    image_path=result["image_path"],
                    audio_url=audio_url,
                    image_url=image_url,
                )
            )

        return MultiSceneGenerateResponse(
            scenes=responses,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except SceneGenerationError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc