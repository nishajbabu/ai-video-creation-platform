from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db

from app.providers.factory import (
    create_tts_provider,
    create_video_provider,
)

from app.schemas.project import (
    ProjectGenerateRequest,
    ProjectGenerateResponse,
)

from app.schemas.scene import Scene

from app.services.project_service import (
    ProjectGenerationError,
    ProjectService,
)

from app.services.voice_selector import VoiceSelector
from app.storage.local_storage import LocalMediaStorage


router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Projects"],
)


# ============================================================
# BUILD MEDIA URL
# ============================================================

def build_media_url(
    file_path: str | None,
) -> str | None:
    """
    Convert a local media path such as:

        media/videos/example.mp4

    into:

        http://127.0.0.1:8001/media/videos/example.mp4

    The BASE_URL is taken from app settings.
    """

    if not file_path:
        return None

    normalized_path = (
        Path(file_path)
        .as_posix()
    )

    # Remove leading slash if present
    normalized_path = normalized_path.lstrip("/")

    # Remove the physical "media/" prefix
    # because FastAPI mounts that directory at /media
    if normalized_path.startswith("media/"):
        normalized_path = normalized_path[
            len("media/") :
        ]

    return (
        f"{settings.base_url.rstrip('/')}"
        f"/media/"
        f"{normalized_path}"
    )


# ============================================================
# GENERATE PROJECT
# ============================================================

@router.post(
    "/generate",
    response_model=ProjectGenerateResponse,
)
def generate_project(
    request: ProjectGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a complete AI project and automatically
    create its Video Editor database records.

    Workflow:

        Request
            ↓
        AI media generation
            ↓
        Video Editor Video
            ↓
        Editor Scenes
            ↓
        Image / Audio / Video Assets
            ↓
        Timeline
            ↓
        Combined initial video
    """

    try:

        # ========================================================
        # 1. CREATE PROVIDERS
        # ========================================================

        tts_provider = create_tts_provider()

        video_provider = create_video_provider()

        storage = LocalMediaStorage()

        # ========================================================
        # 2. CREATE PROJECT SERVICE
        # ========================================================

        service = ProjectService(
            tts_provider=tts_provider,
            video_provider=video_provider,
            storage=storage,
            db=db,
        )

        # ========================================================
        # 3. CONVERT REQUEST SCENES
        # ========================================================

        scenes = [
            Scene(
                scene_id=scene.scene_id,
                narration=scene.narration,
                visual_prompt=scene.visual_prompt,
            )
            for scene in request.scenes
        ]

        # ========================================================
        # 4. SELECT VOICES
        # ========================================================

        voice_selector = VoiceSelector()

        voice_ids = [
            voice_selector.select_voice(
                narration=scene.narration,
                gender=scene.voice,
            )
            for scene in request.scenes
        ]

        # ========================================================
        # 5. GENERATE PROJECT
        # ========================================================

        result = service.generate_project(
            project_id=request.project_id,
            scenes=scenes,
            voice_ids=voice_ids,
        )

        # ========================================================
        # 6. BUILD SCENE RESPONSE
        # ========================================================

        scene_responses = []

        for generated_scene in result["scenes"]:

            audio_path = generated_scene.get(
                "audio_path"
            )

            image_path = generated_scene.get(
                "image_path"
            )

            video_path = generated_scene.get(
                "video_path"
            )

            scene_responses.append(
                {
                    "scene_id": generated_scene[
                        "scene_id"
                    ],

                    "audio_path": audio_path,

                    "image_path": image_path,

                    "video_path": video_path,

                    "audio_url": build_media_url(
                        audio_path
                    ),

                    "image_url": build_media_url(
                        image_path
                    ),

                    "video_url": build_media_url(
                        video_path
                    ),
                }
            )

        # ========================================================
        # 7. BUILD FINAL VIDEO URL
        # ========================================================

        final_video_path = result.get(
            "final_video_path"
        )

        if not final_video_path:

            raise ProjectGenerationError(
                "Project generation completed, but "
                "the final combined video was not created."
            )

        final_video_url = build_media_url(
            final_video_path
        )

        # ========================================================
        # 8. GET EDITOR VIDEO ID
        # ========================================================

        video_id = result.get(
            "video_id"
        )

        if video_id is None:

            raise ProjectGenerationError(
                "Project generation completed, but "
                "no Video Editor video_id was returned."
            )

        # ========================================================
        # 9. RETURN COMPLETE RESPONSE
        # ========================================================

        return ProjectGenerateResponse(
            project_id=result[
                "project_id"
            ],

            video_id=video_id,

            scenes=scene_responses,

            final_video_path=final_video_path,

            final_video_url=final_video_url,
        )

    # ============================================================
    # VALIDATION ERROR
    # ============================================================

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    # ============================================================
    # PROJECT GENERATION ERROR
    # ============================================================

    except ProjectGenerationError as exc:

        message = str(exc)

        # --------------------------------------------------------
        # Duplicate project
        # --------------------------------------------------------

        if "already exists" in message.lower():

            raise HTTPException(
                status_code=409,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=500,
            detail=message,
        ) from exc

    # ============================================================
    # UNEXPECTED ERROR
    # ============================================================

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unexpected project generation error: "
                f"{exc}"
            ),
        ) from exc