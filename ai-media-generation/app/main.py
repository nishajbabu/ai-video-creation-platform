from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.images import router as images_router
from app.api.routes.projects import router as projects_router
from app.api.routes.scenes import router as scenes_router
from app.api.routes.tts import router as tts_router
from app.api.routes.voices import router as voices_router

from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-generated audio and visual media service",
)


app.mount(
    "/media",
    StaticFiles(directory="media"),
    name="media",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-media-generation",
        "environment": settings.environment,
    }


app.include_router(tts_router)
app.include_router(voices_router)
app.include_router(images_router)
app.include_router(scenes_router)
app.include_router(projects_router)