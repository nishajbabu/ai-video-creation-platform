import base64
import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from runwayml import RunwayML
import runwayml

from app.providers.video.provider import VideoProvider


load_dotenv()


class RunwayVideoProvider(VideoProvider):

    def __init__(self):
        api_key = os.getenv("RUNWAYML_API_SECRET")

        if not api_key:
            raise RuntimeError(
                "RUNWAYML_API_SECRET was not found. "
                "Please add it to the .env file."
            )

        self.client = RunwayML(
            api_key=api_key,
        )

    def _image_to_data_uri(
        self,
        image_path: Path,
    ) -> str:

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image file not found: {image_path}"
            )

        if not image_path.is_file():
            raise ValueError(
                f"Image path is not a file: {image_path}"
            )

        mime_type, _ = mimetypes.guess_type(
            image_path.name
        )

        supported_types = {
            "image/png",
            "image/jpeg",
            "image/webp",
        }

        if mime_type not in supported_types:
            raise ValueError(
                "Unsupported image format. "
                "Use PNG, JPEG, or WebP."
            )

        image_bytes = image_path.read_bytes()

        if not image_bytes:
            raise ValueError(
                f"Image file is empty: {image_path}"
            )

        encoded_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        return (
            f"data:{mime_type};base64,"
            f"{encoded_image}"
        )

    def generate_video(
        self,
        prompt: str,
        image_url: str | None = None,
        duration: int = 5,
    ) -> bytes:

        if not prompt or not prompt.strip():
            raise ValueError(
                "Video prompt cannot be empty."
            )

        if not image_url:
            raise ValueError(
                "An image path is required for "
                "Runway video generation."
            )

        image_path = Path(image_url)

        if duration not in {5, 10}:
            raise ValueError(
                "Runway video duration must be "
                "5 or 10 seconds."
            )

        prompt_image = self._image_to_data_uri(
            image_path
        )

        try:
            task = (
                self.client.image_to_video.create(
                    model="gen4_turbo",
                    prompt_image=prompt_image,
                    prompt_text=prompt.strip(),
                    ratio="1280:720",
                    duration=duration,
                )
                .wait_for_task_output()
            )

        except runwayml.APIConnectionError as exc:
            raise RuntimeError(
                "Could not connect to the Runway API."
            ) from exc

        except runwayml.RateLimitError as exc:
            raise RuntimeError(
                "Runway API rate limit reached."
            ) from exc

        except runwayml.APIStatusError as exc:
            raise RuntimeError(
                "Runway API request failed "
                f"with status {exc.status_code}."
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                "Runway video generation failed."
            ) from exc

        if not task.output:
            raise RuntimeError(
                "Runway completed the task but "
                "returned no video output."
            )

        video_url = task.output[0]

        try:
            response = self.client.get(
                video_url,
            )

            response.raise_for_status()

            video_bytes = response.content

        except Exception as exc:
            raise RuntimeError(
                "Failed to download the generated "
                "Runway video."
            ) from exc

        if not video_bytes:
            raise RuntimeError(
                "Runway returned an empty video."
            )

        return video_bytes