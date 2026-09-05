from pathlib import Path

from app.storage.media_storage import MediaStorage


class LocalMediaStorage(MediaStorage):

    def __init__(self, base_directory: str = "media"):
        self.base_directory = Path(base_directory)

    def _safe_filename(self, filename: str) -> str:
        safe_name = Path(filename).name

        if not safe_name:
            raise ValueError(
                "Filename cannot be empty."
            )

        if safe_name != filename:
            raise ValueError(
                "Invalid filename."
            )

        return safe_name

    def save_audio(
        self,
        audio: bytes,
        filename: str,
    ) -> str:

        filename = self._safe_filename(filename)

        audio_directory = self.base_directory / "audio"
        audio_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = audio_directory / filename
        file_path.write_bytes(audio)

        return str(file_path)

    def save_image(
        self,
        image: bytes,
        filename: str,
    ) -> str:

        filename = self._safe_filename(filename)

        image_directory = self.base_directory / "images"
        image_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = image_directory / filename
        file_path.write_bytes(image)

        return str(file_path)

    def save_video(
        self,
        video: bytes,
        filename: str,
    ) -> str:

        filename = self._safe_filename(filename)

        video_directory = self.base_directory / "videos"
        video_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = video_directory / filename
        file_path.write_bytes(video)

        return str(file_path)