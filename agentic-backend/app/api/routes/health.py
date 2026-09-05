"""
Health check API routes.

These endpoints are intentionally lightweight.

They are used by:
    - developers
    - Docker
    - load balancers
    - deployment platforms
    - monitoring systems

A health check should not depend on an LLM request.
"""


from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.responses import APIResponse


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


# ---------------------------------------------------------------------------
# Basic health check
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=APIResponse,
)
def health_check() -> APIResponse:
    """
    Return the current application health status.

    This endpoint only verifies that the API process is alive.
    It deliberately does not call an LLM provider or database.
    """

    return APIResponse(
        success=True,
        message="Agentic Backend is healthy.",
        data={
            "status": "healthy",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )


# ---------------------------------------------------------------------------
# Liveness check
# ---------------------------------------------------------------------------

@router.get(
    "/live",
    response_model=APIResponse,
)
def liveness_check() -> APIResponse:
    """
    Kubernetes/container-style liveness check.

    A successful response means the application process is alive.
    """

    return APIResponse(
        success=True,
        message="Application is alive.",
        data={
            "status": "alive",
        },
    )


# ---------------------------------------------------------------------------
# Readiness check
# ---------------------------------------------------------------------------

@router.get(
    "/ready",
    response_model=APIResponse,
)
def readiness_check() -> APIResponse:
    """
    Check whether the application is ready to receive requests.

    At this stage readiness only verifies that the application
    process is running.

    External dependencies such as the database and LLM providers
    will be incorporated into readiness checks when those layers
    are implemented.
    """

    return APIResponse(
        success=True,
        message="Application is ready.",
        data={
            "status": "ready",
        },
    )