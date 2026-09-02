from huggingface_hub import InferenceClient

from app.core.config import settings
from app.providers.image.provider import ImageProvider


class HuggingFaceImageProvider(ImageProvider):

    MODEL_ID = "black-forest-labs/FLUX.1-schnell"

    def __init__(self):
        if not settings.hf_token:
            raise RuntimeError(
                "Hugging Face token is not configured."
            )

        self.client = InferenceClient(
            provider="auto",
            api_key=settings.hf_token,
        )

    def generate_image(
        self,
        prompt: str,
    ) -> bytes:
        if not prompt or not prompt.strip():
            raise ValueError("Image prompt cannot be empty.")

        try:
            image = self.client.text_to_image(
                prompt=prompt,
                model=self.MODEL_ID,
            )

            from io import BytesIO

            buffer = BytesIO()
            image.save(buffer, format="PNG")

            return buffer.getvalue()

        except Exception as exc:
            raise RuntimeError(
                "Hugging Face image generation failed."
            ) from exc