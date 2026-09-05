from pathlib import Path

import pytest

from app.providers.video.local_video_provider import (
    LocalVideoProvider,
)


def test_generate_video_with_audio():
    provider = LocalVideoProvider()

    image_path = Path(
    "media/images/scene_1.png"
   )

    audio_path = Path(
    "media/audio/scene_1.mp3"
   )

    assert image_path.exists()
    assert audio_path.exists()

    video = provider.generate_video(
        prompt="Test scene",
        image_url=str(image_path),
        audio_url=str(audio_path),
        duration=5,
    )

    assert isinstance(video, bytes)
    assert len(video) > 0


def test_generate_video_without_audio():
    provider = LocalVideoProvider()

    image_path = Path(
        "media/images/scene_1.png"
    )

    assert image_path.exists()

    video = provider.generate_video(
        prompt="Test scene",
        image_url=str(image_path),
        audio_url=None,
        duration=2,
    )

    assert isinstance(video, bytes)
    assert len(video) > 0


def test_missing_image_rejected():
    provider = LocalVideoProvider()

    with pytest.raises(FileNotFoundError):
        provider.generate_video(
            prompt="Test scene",
            image_url="media/images/not_existing.png",
            audio_url=None,
            duration=2,
        )


def test_missing_audio_rejected():
    provider = LocalVideoProvider()

    image_path = Path(
        "media/images/scene_1.png"
    )

    assert image_path.exists()

    with pytest.raises(FileNotFoundError):
        provider.generate_video(
            prompt="Test scene",
            image_url=str(image_path),
            audio_url="media/audio/not_existing.mp3",
            duration=2,
        )


def test_missing_image_path_rejected():
    provider = LocalVideoProvider()

    with pytest.raises(ValueError):
        provider.generate_video(
            prompt="Test scene",
            image_url=None,
            audio_url=None,
            duration=2,
        )