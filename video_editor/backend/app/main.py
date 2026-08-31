from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine

# --------------------------------------------------
# Your Video Editor routes
# --------------------------------------------------

from app.routes.videos import router as video_router
from app.routes.scenes import router as scene_router
from app.routes.assets import router as asset_router
from app.routes.timeline import router as timeline_router
from app.routes.editor import router as editor_router
from app.routes.media import router as media_router
from app.routes.export import router as export_router

# --------------------------------------------------
# AI Media Generation routes
# --------------------------------------------------

from app.api.routes.images import router as images_router
from app.api.routes.projects import router as projects_router
from app.api.routes.scenes import router as ai_scenes_router
from app.api.routes.tts import router as tts_router
from app.api.routes.voices import router as voices_router


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "media"


# --------------------------------------------------
# Create media directories
# --------------------------------------------------

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


# --------------------------------------------------
# Database
# --------------------------------------------------

Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="AI Video Creation Platform API",
    version="1.0.0",
)


# --------------------------------------------------
# YOUR VIDEO EDITOR ROUTES
# --------------------------------------------------

app.include_router(video_router)
app.include_router(scene_router)
app.include_router(asset_router)
app.include_router(timeline_router)
app.include_router(editor_router)
app.include_router(media_router)
app.include_router(export_router)


# --------------------------------------------------
# AI MEDIA GENERATION ROUTES
# --------------------------------------------------

app.include_router(tts_router)
app.include_router(voices_router)
app.include_router(images_router)
app.include_router(ai_scenes_router)
app.include_router(projects_router)


# --------------------------------------------------
# Serve shared media files
# --------------------------------------------------

app.mount(
    "/media",
    StaticFiles(directory=str(MEDIA_DIR)),
    name="media",
)


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AI Video Creation Platform",
    }