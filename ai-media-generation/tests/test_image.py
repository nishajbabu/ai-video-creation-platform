import pytest

from app.services.image_service import (
    ImageGenerationError,
    ImageService,
)


class FakeImageProvider:

    def generate_image(
        self,
        prompt: str,
    ) -> bytes:
        return b"fake image data"


class EmptyImageProvider:

    def generate_image(
        self,
        prompt: str,
    ) -> bytes:
        return b""


class FailingImageProvider:

    def generate_image(
        self,
        prompt: str,
    ) -> bytes:
        raise RuntimeError("Image provider failed")


def create_service(provider):
    return ImageService(
        provider=provider
    )


def test_generate_image_success():

    service = create_service(
        FakeImageProvider()
    )

    result = service.generate_image(
        prompt="A farmer working in a green field"
    )

    assert result == b"fake image data"


def test_empty_prompt_rejected():

    service = create_service(
        FakeImageProvider()
    )

    with pytest.raises(ValueError):
        service.generate_image(
            prompt=""
        )


def test_whitespace_prompt_rejected():

    service = create_service(
        FakeImageProvider()
    )

    with pytest.raises(ValueError):
        service.generate_image(
            prompt="   "
        )


def test_empty_image_from_provider():

    service = create_service(
        EmptyImageProvider()
    )

    with pytest.raises(ImageGenerationError):
        service.generate_image(
            prompt="A farmer working in a field"
        )


def test_provider_failure():

    service = create_service(
        FailingImageProvider()
    )

    with pytest.raises(ImageGenerationError):
        service.generate_image(
            prompt="A farmer working in a field"
        )