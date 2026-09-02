from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.providers.image.huggingface_provider import (
    HuggingFaceImageProvider,
)
from app.schemas.image import (
    ImageGenerateRequest,
    ImageGenerateResponse,
)
from app.services.image_service import (
    ImageGenerationError,
    ImageService,
)
from app.storage.local_storage import LocalMediaStorage


router = APIRouter(
    prefix="/api/v1/images",
    tags=["Images"],
)


@router.post(
    "/generate",
    response_model=ImageGenerateResponse,
)
def generate_image(request: ImageGenerateRequest):
    provider = HuggingFaceImageProvider()
    service = ImageService(provider)
    storage = LocalMediaStorage()

    try:
        image = service.generate_image(
            prompt=request.prompt,
        )

        image_path = storage.save_image(
            image=image,
            filename=request.filename,
        )

        image_url = (
            f"{settings.base_url}/{image_path.replace(chr(92), '/')}"
        )

        return ImageGenerateResponse(
            message="Image generated successfully.",
            image_path=image_path,
            image_url=image_url,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ImageGenerationError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc