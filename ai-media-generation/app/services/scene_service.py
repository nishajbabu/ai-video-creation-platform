from app.providers.image.provider import ImageProvider
from app.providers.tts.provider import TTSProvider
from app.providers.video.provider import VideoProvider

from app.schemas.scene import Scene
from app.storage.local_storage import LocalMediaStorage


class SceneGenerationError(Exception):
    """Raised when scene media generation fails."""


class SceneService:

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

    def generate_scene(
        self,
        scene: Scene,
        voice_id: str,
        existing_image_path: str | None = None,
    ) -> dict:

        try:
            # -----------------------------------
            # 1. Generate narration audio
            # -----------------------------------
            audio = self.tts_provider.generate_speech(
                text=scene.narration,
                voice_id=voice_id,
            )

            audio_path = self.storage.save_audio(
                audio=audio,
                filename=f"scene_{scene.scene_id}.mp3",
            )

            # -----------------------------------
            # 2. Get scene image
            # -----------------------------------
            if existing_image_path:

                image_path = existing_image_path

            else:

                image = self.image_provider.generate_image(
                    prompt=scene.visual_prompt,
                )

                image_path = self.storage.save_image(
                    image=image,
                    filename=f"scene_{scene.scene_id}.png",
                )

            # -----------------------------------
            # 3. Generate scene video
            # -----------------------------------
            video = self.video_provider.generate_video(
                prompt=scene.visual_prompt,
                image_url=image_path,
                audio_url=audio_path,
                duration=5,
            )

            video_path = self.storage.save_video(
                video=video,
                filename=f"scene_{scene.scene_id}.mp4",
            )

            # -----------------------------------
            # 4. Return generated media
            # -----------------------------------
            return {
                "scene_id": scene.scene_id,
                "audio_path": audio_path,
                "image_path": image_path,
                "video_path": video_path,
            }

        except Exception as exc:
            raise SceneGenerationError(
                f"Failed to generate scene "
                f"{scene.scene_id}."
            ) from exc

    def generate_scenes(
        self,
        scenes: list[Scene],
        voice_ids: list[str],
        image_paths: list[str] | None = None,
    ) -> list[dict]:

        if not scenes:
            raise ValueError(
                "At least one scene is required."
            )

        if len(scenes) != len(voice_ids):
            raise ValueError(
                "Each scene must have a corresponding voice."
            )

        if image_paths is not None:

            if len(scenes) != len(image_paths):
                raise ValueError(
                    "Each scene must have a corresponding image."
                )

        results = []

        for index, (scene, voice_id) in enumerate(
            zip(scenes, voice_ids)
        ):

            existing_image_path = None

            if image_paths is not None:
                existing_image_path = image_paths[index]

            result = self.generate_scene(
                scene=scene,
                voice_id=voice_id,
                existing_image_path=existing_image_path,
            )

            results.append(result)

        return results