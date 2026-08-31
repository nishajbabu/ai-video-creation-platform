from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db

from app.providers.factory import (
    create_tts_provider,
    create_video_provider,
)

from app.schemas.ai_media.project import (
    ProjectGenerateRequest,
    ProjectGenerateResponse,
)

from app.schemas.ai_media.scene import Scene

from app.services.project_service import (
    ProjectGenerationError,
    ProjectService,
)

from app.services.voice_selector import VoiceSelector

from app.services.ai_video_import_service import (
    AIVideoImportError,
    import_generated_project,
)

from app.storage.local_storage import LocalMediaStorage


router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Projects"],
)


@router.post(
    "/generate",
    response_model=ProjectGenerateResponse,
)
def generate_project(
    request: ProjectGenerateRequest,
    db: Session = Depends(get_db),
):
    try:

        # -----------------------------------
        # Create providers
        # -----------------------------------

        tts_provider = create_tts_provider()
        video_provider = create_video_provider()

        storage = LocalMediaStorage()

        service = ProjectService(
            tts_provider=tts_provider,
            video_provider=video_provider,
            storage=storage,
        )

        # -----------------------------------
        # Convert request scenes
        # -----------------------------------

        scenes = [
            Scene(
                scene_id=scene.scene_id,
                narration=scene.narration,
                visual_prompt=scene.visual_prompt,
            )
            for scene in request.scenes
        ]

        # -----------------------------------
        # Select voice automatically
        # -----------------------------------

        voice_selector = VoiceSelector()

        voice_ids = [
            voice_selector.select_voice(
                narration=scene.narration,
                gender=scene.voice,
            )
            for scene in request.scenes
        ]

        # -----------------------------------
        # Generate complete AI media project
        # -----------------------------------

        result = service.generate_project(
            project_id=request.project_id,
            scenes=scenes,
            voice_ids=voice_ids,
        )

        # -----------------------------------
        # Build API response
        # -----------------------------------

        scene_responses = []

        for scene in result["scenes"]:

            audio_path = scene["audio_path"]
            image_path = scene["image_path"]
            video_path = scene["video_path"]

            audio_url = (
                f"{settings.base_url}/"
                f"{audio_path.replace(chr(92), '/')}"
            )

            image_url = (
                f"{settings.base_url}/"
                f"{image_path.replace(chr(92), '/')}"
            )

            video_url = (
                f"{settings.base_url}/"
                f"{video_path.replace(chr(92), '/')}"
            )

            scene_responses.append(
                {
                    "scene_id": scene["scene_id"],
                    "audio_path": audio_path,
                    "image_path": image_path,
                    "video_path": video_path,
                    "audio_url": audio_url,
                    "image_url": image_url,
                    "video_url": video_url,
                }
            )

        # -----------------------------------
        # Create Video Editor records
        #
        # AI generated media is now imported
        # into:
        #
        # Video
        #   └── Scenes
        #        └── Assets
        #   └── Timeline
        # -----------------------------------

        editor_project_result = {
            "project_id": result["project_id"],
            "scenes": scene_responses,
        }

        editor_video = import_generated_project(
            db=db,
            project_result=editor_project_result,
        )

        # -----------------------------------
        # Return AI generation response
        # -----------------------------------

        return ProjectGenerateResponse(
            project_id=result["project_id"],
            scenes=scene_responses,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ProjectGenerationError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except AIVideoImportError as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc