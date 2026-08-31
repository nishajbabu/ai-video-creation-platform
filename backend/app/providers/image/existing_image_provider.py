from pathlib import Path

from app.providers.image.provider import ImageProvider


class ExistingImageProvider(ImageProvider):
    """
    Image provider that loads an existing local image.

    Useful for:
    - testing
    - local/offline workflows
    - development without paid image APIs
    - integration with externally generated images
    """

    def __init__(self, image_path: str):
        self.image_path = Path(image_path)

    def generate_image(
        self,
        prompt: str,
    ) -> bytes:

        if not prompt or not prompt.strip():
            raise ValueError(
                "Image prompt cannot be empty."
            )

        if not self.image_path.exists():
            raise FileNotFoundError(
                f"Image file not found: "
                f"{self.image_path}"
            )

        if not self.image_path.is_file():
            raise ValueError(
                f"Image path is not a file: "
                f"{self.image_path}"
            )

        return self.image_path.read_bytes()