from pathlib import Path

from app.core.config import settings
from app.providers.factory import create_image_provider
from app.providers.tts.provider import TTSProvider
from app.providers.video.provider import VideoProvider

from app.schemas.scene import Scene
from app.services.media_generation_service import (
    MediaGenerationError,
    MediaGenerationService,
)
from app.storage.local_storage import LocalMediaStorage


class ProjectGenerationError(Exception):
    """Raised when project media generation fails."""


class ProjectService:

    def __init__(
        self,
        tts_provider: TTSProvider,
        video_provider: VideoProvider,
        storage: LocalMediaStorage,
    ):
        self.tts_provider = tts_provider
        self.video_provider = video_provider
        self.storage = storage

    def generate_project(
        self,
        project_id: str,
        scenes: list[Scene],
        voice_ids: list[str],
    ) -> dict:

        if not project_id:
            raise ValueError(
                "Project ID is required."
            )

        if not scenes:
            raise ValueError(
                "At least one scene is required."
            )

        if len(scenes) != len(voice_ids):
            raise ValueError(
                "Each scene must have a corresponding voice."
            )

        results = []

        try:

            for scene, voice_id in zip(
                scenes,
                voice_ids,
            ):

                # -----------------------------------
                # Create image provider
                # -----------------------------------

                provider_name = (
                    settings.image_provider
                    .lower()
                    .strip()
                )

                if provider_name == "existing":

                    # Existing-image mode:
                    # use media/images/scene_X.png

                    image_path = (
                        Path("media")
                        / "images"
                        / f"scene_{scene.scene_id}.png"
                    )

                    if not image_path.exists():
                        raise FileNotFoundError(
                            f"Image for scene "
                            f"{scene.scene_id} not found: "
                            f"{image_path}"
                        )

                    image_provider = create_image_provider(
                        image_path=str(image_path),
                    )

                else:

                    # AI-image mode:
                    # image will be generated from
                    # scene.visual_prompt

                    image_path = None

                    image_provider = create_image_provider()

                # -----------------------------------
                # Create media generation service
                # -----------------------------------

                media_service = MediaGenerationService(
                    tts_provider=self.tts_provider,
                    image_provider=image_provider,
                    video_provider=self.video_provider,
                    storage=self.storage,
                )

                # -----------------------------------
                # Generate complete scene media
                # -----------------------------------

                result = media_service.generate_scene_media(
                    project_id=project_id,
                    scene=scene,
                    voice_id=voice_id,
                    image_path=(
                        str(image_path)
                        if image_path
                        else None
                    ),
                    generate_video=True,
                    duration=5,
                )

                results.append(result)

            return {
                "project_id": project_id,
                "scenes": results,
            }

        except MediaGenerationError as exc:

            raise ProjectGenerationError(
                f"Failed to generate project "
                f"'{project_id}': {exc}"
            ) from exc

        except Exception as exc:

            raise ProjectGenerationError(
                f"Failed to generate project "
                f"'{project_id}': {exc}"
            ) from exc