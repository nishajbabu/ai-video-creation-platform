from app.providers.image.provider import ImageProvider
from app.providers.tts.provider import TTSProvider
from app.providers.video.provider import VideoProvider

from app.schemas.scene import Scene
from app.storage.local_storage import LocalMediaStorage


class MediaGenerationError(Exception):
    """Raised when media generation fails."""


class MediaGenerationService:

    def __init__(
        self,
        tts_provider: TTSProvider,
        image_provider: ImageProvider,
        video_provider: VideoProvider,
        storage: LocalMediaStorage,
    ):
        self.tts_provider = tts_provider
        self.image_provider = image_provider
        self.video_provider = video_provider
        self.storage = storage

    # -----------------------------------
    # Generate narration audio
    # -----------------------------------

    def generate_audio(
        self,
        project_id: str,
        scene: Scene,
        voice_id: str,
    ) -> str:

        try:

            audio = self.tts_provider.generate_speech(
                text=scene.narration,
                voice_id=voice_id,
            )

            audio_path = self.storage.save_audio(
                audio=audio,
                filename=(
                    f"{project_id}_scene_{scene.scene_id}.mp3"
                ),
            )

            return audio_path

        except Exception as exc:

            raise MediaGenerationError(
                f"Audio generation failed "
                f"for scene {scene.scene_id}."
            ) from exc

    # -----------------------------------
    # Generate AI image
    # -----------------------------------

    def generate_image(
        self,
        project_id: str,
        scene: Scene,
    ) -> str:

        try:

            image = self.image_provider.generate_image(
                prompt=scene.visual_prompt,
            )

            image_path = self.storage.save_image(
                image=image,
                filename=(
                    f"{project_id}_scene_{scene.scene_id}.png"
                ),
            )

            return image_path

        except Exception as exc:

            raise MediaGenerationError(
                f"Image generation failed "
                f"for scene {scene.scene_id}."
            ) from exc

    # -----------------------------------
    # Generate AI video
    # -----------------------------------

    def generate_video(
        self,
        project_id: str,
        scene: Scene,
        image_path: str,
        audio_path: str | None = None,
        duration: int = 5,
    ) -> str:

        try:

            video = self.video_provider.generate_video(
                prompt=scene.visual_prompt,
                image_url=image_path,
                audio_url=audio_path,
                duration=duration,
            )

            video_path = self.storage.save_video(
                video=video,
                filename=(
                    f"{project_id}_scene_{scene.scene_id}.mp4"
                ),
            )

            return video_path

        except Exception as exc:

            raise MediaGenerationError(
                f"Video generation failed "
                f"for scene {scene.scene_id}."
            ) from exc

    # -----------------------------------
    # Generate complete scene media
    # -----------------------------------

    def generate_scene_media(
        self,
        project_id: str,
        scene: Scene,
        voice_id: str,
        image_path: str | None = None,
        generate_video: bool = True,
        duration: int = 5,
    ) -> dict:

        try:

            # -----------------------------------
            # 1. Generate narration
            # -----------------------------------

            audio_path = self.generate_audio(
                project_id=project_id,
                scene=scene,
                voice_id=voice_id,
            )

            # -----------------------------------
            # 2. Generate or use image
            # -----------------------------------

            if image_path:

                generated_image_path = image_path

            else:

                generated_image_path = (
                    self.generate_image(
                        project_id=project_id,
                        scene=scene,
                    )
                )

            # -----------------------------------
            # 3. Generate video
            # -----------------------------------

            video_path = None

            if generate_video:

                video_path = self.generate_video(
                    project_id=project_id,
                    scene=scene,
                    image_path=generated_image_path,
                    audio_path=audio_path,
                    duration=duration,
                )

            # -----------------------------------
            # 4. Return scene assets
            # -----------------------------------

            return {
                "scene_id": scene.scene_id,
                "audio_path": audio_path,
                "image_path": generated_image_path,
                "video_path": video_path,
            }

        except MediaGenerationError:
            raise

        except Exception as exc:

            raise MediaGenerationError(
                f"Media generation failed "
                f"for scene {scene.scene_id}."
            ) from exc