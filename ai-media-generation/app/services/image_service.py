from app.providers.image.provider import ImageProvider


class ImageGenerationError(Exception):
    """Raised when image generation fails."""


class ImageService:

    def __init__(self, provider: ImageProvider):
        self.provider = provider

    def generate_image(
        self,
        prompt: str,
    ) -> bytes:
        if not prompt or not prompt.strip():
            raise ValueError("Image prompt cannot be empty.")

        try:
            image = self.provider.generate_image(
                prompt=prompt,
            )

            if not image:
                raise ImageGenerationError(
                    "Image provider returned empty image data."
                )

            return image

        except (ValueError, ImageGenerationError):
            raise

        except Exception as exc:
            raise ImageGenerationError(
                "Failed to generate image."
            ) from exc