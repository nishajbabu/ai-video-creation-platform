from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings

from app.models.video import Video
from app.models.scene import Scene as EditorScene
from app.models.asset import Asset

from app.providers.factory import create_image_provider
from app.providers.tts.provider import TTSProvider
from app.providers.video.provider import VideoProvider

from app.schemas.scene import Scene as AIScene

from app.services.media_generation_service import (
    MediaGenerationError,
    MediaGenerationService,
)

from app.services.timeline_service import generate_timeline

from app.storage.local_storage import LocalMediaStorage


class ProjectGenerationError(Exception):
    """Raised when project media generation fails."""


class ProjectService:

    def __init__(
        self,
        tts_provider: TTSProvider,
        video_provider: VideoProvider,
        storage: LocalMediaStorage,
        db: Session,
    ):
        self.tts_provider = tts_provider
        self.video_provider = video_provider
        self.storage = storage
        self.db = db

    # ============================================================
    # HELPER: CONVERT LOCAL PATH TO MEDIA-RELATIVE PATH
    # ============================================================

    @staticmethod
    def _media_relative_path(
        file_path: str,
    ) -> str:
        """
        Convert a local path such as:

            media\\images\\example.png

        into:

            images/example.png
        """

        normalized = (
            Path(file_path)
            .as_posix()
            .lstrip("/")
        )

        if normalized.startswith("media/"):
            normalized = normalized[
                len("media/"):
            ]

        return normalized

    # ============================================================
    # HELPER: BUILD INTERNAL MEDIA URL
    # ============================================================

    @staticmethod
    def _build_media_asset_url(
        file_path: str,
    ) -> str:
        """
        Build the URL stored in the editor Asset table.

        Example:

            /media/images/example.png
        """

        relative_path = (
            ProjectService._media_relative_path(
                file_path
            )
        )

        return f"/media/{relative_path}"

    # ============================================================
    # GENERATE COMPLETE PROJECT
    # ============================================================

    def generate_project(
        self,
        project_id: str,
        scenes: list[AIScene],
        voice_ids: list[str],
    ) -> dict:

        # --------------------------------------------------------
        # Validate input
        # --------------------------------------------------------

        if not project_id or not project_id.strip():
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

        project_id = project_id.strip()

        results: list[dict] = []

        try:

            # ====================================================
            # 1. GENERATE EVERY AI SCENE
            # ====================================================

            for scene, voice_id in zip(
                scenes,
                voice_ids,
            ):

                # ------------------------------------------------
                # Select image provider
                # ------------------------------------------------

                provider_name = (
                    settings.image_provider
                    .lower()
                    .strip()
                )

                if provider_name == "existing":

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

                    image_provider = (
                        create_image_provider(
                            image_path=str(
                                image_path
                            )
                        )
                    )

                else:

                    image_path = None

                    image_provider = (
                        create_image_provider()
                    )

                # ------------------------------------------------
                # Create media generation service
                # ------------------------------------------------

                media_service = (
                    MediaGenerationService(
                        tts_provider=self.tts_provider,
                        image_provider=image_provider,
                        video_provider=self.video_provider,
                        storage=self.storage,
                    )
                )

                # ------------------------------------------------
                # Generate:
                #
                #   audio
                #   image
                #   scene video
                # ------------------------------------------------

                result = (
                    media_service.generate_scene_media(
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
                )

                results.append(result)

            # ====================================================
            # 2. VALIDATE GENERATED FILES
            # ====================================================

            scene_video_paths: list[str] = []

            for result in results:

                scene_id = result.get(
                    "scene_id"
                )

                audio_path = result.get(
                    "audio_path"
                )

                image_path = result.get(
                    "image_path"
                )

                video_path = result.get(
                    "video_path"
                )

                if not audio_path:

                    raise ProjectGenerationError(
                        f"No audio was generated "
                        f"for scene {scene_id}."
                    )

                if not image_path:

                    raise ProjectGenerationError(
                        f"No image was generated "
                        f"for scene {scene_id}."
                    )

                if not video_path:

                    raise ProjectGenerationError(
                        f"No video was generated "
                        f"for scene {scene_id}."
                    )

                # -----------------------------------------------
                # Validate all physical files
                # -----------------------------------------------

                for media_name, media_path in (
                    ("audio", audio_path),
                    ("image", image_path),
                    ("video", video_path),
                ):

                    media_file = Path(
                        media_path
                    )

                    if not media_file.exists():

                        raise FileNotFoundError(
                            f"Generated {media_name} file "
                            f"not found for scene "
                            f"{scene_id}: {media_file}"
                        )

                    if media_file.stat().st_size == 0:

                        raise RuntimeError(
                            f"Generated {media_name} file "
                            f"is empty for scene "
                            f"{scene_id}: {media_file}"
                        )

                scene_video_paths.append(
                    str(video_path)
                )

            # ====================================================
            # 3. COMBINE ALL SCENE VIDEOS
            # ====================================================

            if not scene_video_paths:

                raise ProjectGenerationError(
                    "No scene videos are available "
                    "to create the final video."
                )

            if not hasattr(
                self.video_provider,
                "combine_videos",
            ):

                raise ProjectGenerationError(
                    "The configured video provider does "
                    "not support combining scene videos."
                )

            final_video_bytes = (
                self.video_provider.combine_videos(
                    scene_video_paths
                )
            )

            if not final_video_bytes:

                raise ProjectGenerationError(
                    "The final combined video is empty."
                )

            # ====================================================
            # 4. SAVE INITIAL COMBINED VIDEO
            # ====================================================

            final_video_path = (
                self.storage.save_video(
                    video=final_video_bytes,
                    filename=(
                        f"{project_id}_final.mp4"
                    ),
                )
            )

            final_video_file = Path(
                final_video_path
            )

            if not final_video_file.exists():

                raise FileNotFoundError(
                    "Final combined video was not saved: "
                    f"{final_video_file}"
                )

            if final_video_file.stat().st_size == 0:

                raise RuntimeError(
                    "Final combined video file is empty."
                )

            # ====================================================
            # 5. CHECK FOR DUPLICATE EDITOR PROJECT
            # ====================================================

            existing_video = (
                self.db.query(Video)
                .filter(
                    Video.title == project_id
                )
                .first()
            )

            if existing_video:

                raise ProjectGenerationError(
                    f"An editor project already exists "
                    f"for '{project_id}'. "
                    f"Existing video_id: "
                    f"{existing_video.id}"
                )

            # ====================================================
            # 6. CREATE VIDEO EDITOR PROJECT
            # ====================================================

            editor_video = Video(
                title=project_id,
                total_duration=0.0,
            )

            self.db.add(
                editor_video
            )

            self.db.flush()

            # ====================================================
            # 7. CREATE EDITOR SCENES
            # ====================================================

            editor_scenes: list[EditorScene] = []

            for index, (
                ai_scene,
                generated_result,
            ) in enumerate(
                zip(
                    scenes,
                    results,
                ),
                start=1,
            ):

                editor_scene = EditorScene(
                    video_id=editor_video.id,
                    order=index,
                    duration=5.0,
                    title=(
                        f"Scene "
                        f"{ai_scene.scene_id}"
                    ),
                )

                self.db.add(
                    editor_scene
                )

                self.db.flush()

                editor_scenes.append(
                    editor_scene
                )

                # =================================================
                # 8. IMAGE ASSET
                # =================================================

                image_path = (
                    generated_result[
                        "image_path"
                    ]
                )

                image_url = (
                    self._build_media_asset_url(
                        image_path
                    )
                )

                self.db.add(
                    Asset(
                        scene_id=editor_scene.id,
                        asset_type="image",
                        file_url=image_url,
                    )
                )

                # =================================================
                # 9. AUDIO ASSET
                # =================================================

                audio_path = (
                    generated_result[
                        "audio_path"
                    ]
                )

                audio_url = (
                    self._build_media_asset_url(
                        audio_path
                    )
                )

                self.db.add(
                    Asset(
                        scene_id=editor_scene.id,
                        asset_type="audio",
                        file_url=audio_url,
                    )
                )

                # =================================================
                # 10. VIDEO ASSET
                # =================================================

                video_path = (
                    generated_result[
                        "video_path"
                    ]
                )

                video_url = (
                    self._build_media_asset_url(
                        video_path
                    )
                )

                self.db.add(
                    Asset(
                        scene_id=editor_scene.id,
                        asset_type="video",
                        file_url=video_url,
                    )
                )

            # ====================================================
            # 11. SAVE VIDEO + SCENES + ASSETS
            # ====================================================

            self.db.commit()

            # ====================================================
            # 12. LOAD CREATED ASSETS
            # ====================================================

            editor_scene_ids = [
                scene.id
                for scene in editor_scenes
            ]

            editor_assets = (
                self.db.query(Asset)
                .filter(
                    Asset.scene_id.in_(
                        editor_scene_ids
                    )
                )
                .all()
            )

            # ====================================================
            # 13. GENERATE INITIAL EDITOR TIMELINE
            # ====================================================

            timelines = generate_timeline(
                db=self.db,
                video_id=editor_video.id,
                scenes=editor_scenes,
                assets=editor_assets,
            )

            # ====================================================
            # 14. CALCULATE TOTAL DURATION
            # ====================================================

            if timelines:

                editor_video.total_duration = max(
                    float(
                        timeline.end_time
                    )
                    for timeline in timelines
                )

            else:

                editor_video.total_duration = sum(
                    float(
                        scene.duration or 0
                    )
                    for scene in editor_scenes
                )

            self.db.commit()

            self.db.refresh(
                editor_video
            )

            # ====================================================
            # 15. RETURN EVERYTHING
            # ====================================================

            return {
                "project_id": project_id,

                # Editor database ID
                "video_id": editor_video.id,

                # Individual generated scenes
                "scenes": results,

                # Initial combined AI video
                "final_video_path": (
                    final_video_path
                ),
            }

        # ========================================================
        # ERROR HANDLING
        # ========================================================

        except MediaGenerationError as exc:

            self.db.rollback()

            raise ProjectGenerationError(
                f"Failed to generate project "
                f"'{project_id}': {exc}"
            ) from exc

        except ProjectGenerationError:

            self.db.rollback()

            raise

        except Exception as exc:

            self.db.rollback()

            raise ProjectGenerationError(
                f"Failed to generate project "
                f"'{project_id}': {exc}"
            ) from exc