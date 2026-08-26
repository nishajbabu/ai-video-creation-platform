import base64
import mimetypes
import os
import subprocess
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

from app.providers.video.provider import VideoProvider


class LTXVideoProvider(VideoProvider):

    API_URL = "https://api.ltx.io/v1/image-to-video"

    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("LTX_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "LTX_API_KEY was not found in the .env file."
            )

    def _image_to_data_uri(
        self,
        image_path: Path,
    ) -> str:

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image file not found: {image_path}"
            )

        mime_type, _ = mimetypes.guess_type(
            image_path.name
        )

        if mime_type not in {
            "image/png",
            "image/jpeg",
            "image/webp",
        }:
            raise ValueError(
                "Unsupported image format. "
                "Use PNG, JPEG, or WebP."
            )

        image_bytes = image_path.read_bytes()

        encoded_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        return (
            f"data:{mime_type};base64,"
            f"{encoded_image}"
        )

    def _merge_audio(
        self,
        video_bytes: bytes,
        audio_path: Path,
    ) -> bytes:

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        try:
            import imageio_ffmpeg

            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        except Exception as exc:
            raise RuntimeError(
                "FFmpeg is required to merge "
                "narration audio with the video."
            ) from exc

        with tempfile.TemporaryDirectory() as temp_dir:

            temp_directory = Path(temp_dir)

            input_video = (
                temp_directory / "input_video.mp4"
            )

            output_video = (
                temp_directory / "output_video.mp4"
            )

            input_video.write_bytes(video_bytes)

            command = [
                ffmpeg_path,
                "-y",

                "-i",
                str(input_video),

                "-i",
                str(audio_path),

                "-map",
                "0:v:0",

                "-map",
                "1:a:0",

                "-c:v",
                "copy",

                "-c:a",
                "aac",

                "-shortest",

                str(output_video),
            ]

            try:
                subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    "FFmpeg failed while merging "
                    "narration audio with the video:\n"
                    f"{exc.stderr}"
                ) from exc

            if not output_video.exists():
                raise RuntimeError(
                    "FFmpeg completed but the "
                    "merged video was not created."
                )

            return output_video.read_bytes()

    def generate_video(
        self,
        prompt: str,
        image_url: str | None = None,
        audio_url: str | None = None,
        duration: int = 5,
    ) -> bytes:

        if not image_url:
            raise ValueError(
                "An image path is required "
                "for LTX video generation."
            )

        image_path = Path(image_url)

        prompt_image = self._image_to_data_uri(
            image_path
        )

        payload = {
            "image_uri": prompt_image,
            "prompt": prompt,
            "model": "ltx-2-3-fast",
            "duration": duration,
            "resolution": "1920x1080",
            "fps": 24,
            "generate_audio": False,
        }

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=300,
            )

        except requests.RequestException as exc:
            raise RuntimeError(
                "Could not connect to LTX API."
            ) from exc

        if not response.ok:
            raise RuntimeError(
                f"LTX API request failed "
                f"with status {response.status_code}: "
                f"{response.text}"
            )

        content_type = response.headers.get(
            "Content-Type",
            "",
        )

        if "video/mp4" not in content_type:
            raise RuntimeError(
                "LTX API did not return an MP4 video."
            )

        video_bytes = response.content

        if not video_bytes:
            raise RuntimeError(
                "LTX API returned an empty video."
            )

        # ---------------------------------------
        # Add narration audio when provided
        # ---------------------------------------

        if audio_url:

            audio_path = Path(audio_url)

            video_bytes = self._merge_audio(
                video_bytes=video_bytes,
                audio_path=audio_path,
            )

        return video_bytes