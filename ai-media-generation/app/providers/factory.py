from app.core.config import settings

from app.providers.image.provider import ImageProvider
from app.providers.image.existing_image_provider import (
    ExistingImageProvider,
)
from app.providers.image.huggingface_provider import (
    HuggingFaceImageProvider,
)

from app.providers.video.provider import VideoProvider
from app.providers.video.local_video_provider import (
    LocalVideoProvider,
)

from app.providers.tts.provider import TTSProvider
from app.providers.tts.edge_tts_provider import (
    EdgeTTSProvider,
)


class ProviderConfigurationError(Exception):
    """Raised when a provider configuration is invalid."""


def create_image_provider(
    image_path: str | None = None,
) -> ImageProvider:

    provider = settings.image_provider.lower().strip()

    if provider == "existing":

        if not image_path:
            raise ProviderConfigurationError(
                "An image path is required when IMAGE_PROVIDER=existing."
            )

        return ExistingImageProvider(
            image_path=image_path,
        )

    if provider == "huggingface":
        return HuggingFaceImageProvider()

    raise ProviderConfigurationError(
        f"Unsupported image provider: {provider}"
    )


def create_video_provider() -> VideoProvider:

    provider = settings.video_provider.lower().strip()

    if provider == "local":
        return LocalVideoProvider()

    raise ProviderConfigurationError(
        f"Unsupported video provider: {provider}"
    )


def create_tts_provider() -> TTSProvider:

    provider = settings.tts_provider.lower().strip()

    if provider == "edge":
        return EdgeTTSProvider()

    raise ProviderConfigurationError(
        f"Unsupported TTS provider: {provider}"
    )
