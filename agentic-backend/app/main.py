"""
Main FastAPI application entry point.

This module creates the application instance and registers
the API routers.
"""

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.videos import router as videos_router
from app.api.routes.scenes import router as scenes_router
from app.api.routes.generation import router as generation_router
from app.api.routes.assets import router as assets_router
from app.api.routes.assets import router as assets_router


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Agentic Backend",
    description=(
        "Backend API for an agentic AI video-generation system."
    ),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

app.include_router(
    health_router,
)

app.include_router(
    projects_router,
)

app.include_router(
    videos_router,
)

app.include_router(
    scenes_router,
)

app.include_router(
    generation_router,
)

app.include_router(
    assets_router,
)



# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------

@app.get("/")
def root() -> dict:
    """
    Return basic information about the API.
    """

    return {
        "name": "Agentic Backend",
        "version": "0.1.0",
        "status": "running",
    }