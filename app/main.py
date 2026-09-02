from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# ============================================================
# DATABASE
# ============================================================

from app.database import Base, engine


# ============================================================
# IMPORT EDITOR MODELS
# This ensures SQLAlchemy registers all editor tables
# before create_all() is executed.
# ============================================================

from app.models.video import Video
from app.models.scene import Scene
from app.models.asset import Asset
from app.models.timeline import Timeline


# ============================================================
# AI MEDIA GENERATION ROUTES
# ============================================================

from app.api.routes.images import router as images_router
from app.api.routes.projects import router as projects_router
from app.api.routes.scenes import router as ai_scenes_router
from app.api.routes.tts import router as tts_router
from app.api.routes.voices import router as voices_router


# ============================================================
# VIDEO EDITOR ROUTES
# ============================================================

from app.routes.videos import router as video_router
from app.routes.scenes import router as scene_router
from app.routes.assets import router as asset_router
from app.routes.timeline import router as timeline_router
from app.routes.editor import router as editor_router
from app.routes.media import router as media_router
from app.routes.export import router as export_router
from app.routes.integration import router as integration_router


# ============================================================
# SETTINGS
# ============================================================

from app.core.config import settings


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_DIR = BASE_DIR / "media"

FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# CREATE MEDIA DIRECTORIES
# ============================================================

(MEDIA_DIR / "images").mkdir(
    parents=True,
    exist_ok=True,
)

(MEDIA_DIR / "videos").mkdir(
    parents=True,
    exist_ok=True,
)

(MEDIA_DIR / "audio").mkdir(
    parents=True,
    exist_ok=True,
)

(MEDIA_DIR / "exports").mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-generated audio and visual media service "
        "with integrated video editor"
    ),
)


# ============================================================
# SERVE MEDIA FILES
# ============================================================

app.mount(
    "/media",
    StaticFiles(
        directory=str(MEDIA_DIR)
    ),
    name="media",
)


# ============================================================
# SERVE FRONTEND
# ============================================================

if FRONTEND_DIR.exists():

    app.mount(
        "/frontend",
        StaticFiles(
            directory=str(FRONTEND_DIR),
            html=True,
        ),
        name="frontend",
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "ai-media-generation",
        "environment": settings.environment,
    }


# ============================================================
# AI MEDIA GENERATION ROUTES
# ============================================================

app.include_router(
    tts_router
)

app.include_router(
    voices_router
)

app.include_router(
    images_router
)

app.include_router(
    ai_scenes_router
)

app.include_router(
    projects_router
)


# ============================================================
# VIDEO EDITOR ROUTES
# ============================================================

app.include_router(
    video_router
)

app.include_router(
    scene_router
)

app.include_router(
    asset_router
)

app.include_router(
    timeline_router
)

app.include_router(
    editor_router
)

app.include_router(
    media_router
)

app.include_router(
    export_router
)

app.include_router(
    integration_router
)