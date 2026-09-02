"""
Video generation API routes.

This module exposes the HTTP entry point for starting a video
generation workflow.

The route remains thin:

    HTTP Request
        ↓
    GenerationService
        ↓
    Orchestrator
        ↓
    Planner → Script → Storyboard

Application dependencies are provided through FastAPI dependency
injection so the generation workflow uses the configured LLM service.
"""

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_generation_service
from app.schemas.requests import VideoRequest
from app.schemas.responses import APIResponse
from app.services.generation_service import GenerationService


router = APIRouter(
    prefix="/generation",
    tags=["Generation"],
)


# ---------------------------------------------------------------------------
# Start generation
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=APIResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_generation(
    request: VideoRequest,
    service: GenerationService = Depends(
        get_generation_service,
    ),
) -> APIResponse:
    """
    Start a video-generation workflow.

    The GenerationService is provided through FastAPI dependency
    injection. The service delegates workflow execution to the
    configured Orchestrator.

    The route itself does not contain agent or workflow logic.
    """

    result = service.start_generation(
        request,
    )

    return APIResponse(
        success=True,
        message="Video generation workflow completed.",
        data=result,
    )