import pytest
from pathlib import Path

from app.storage.local_storage import LocalMediaStorage


def test_save_audio(tmp_path):
    storage = LocalMediaStorage(
        base_directory=str(tmp_path)
    )

    audio_data = b"test audio data"

    result = storage.save_audio(
        audio=audio_data,
        filename="test.mp3",
    )

    file_path = Path(result)

    assert file_path.exists()
    assert file_path.read_bytes() == audio_data


def test_save_image(tmp_path):
    storage = LocalMediaStorage(
        base_directory=str(tmp_path)
    )

    image_data = b"test image data"

    result = storage.save_image(
        image=image_data,
        filename="test.png",
    )

    file_path = Path(result)

    assert file_path.exists()
    assert file_path.read_bytes() == image_data


def test_save_video(tmp_path):
    storage = LocalMediaStorage(
        base_directory=str(tmp_path)
    )

    video_data = b"test video data"

    result = storage.save_video(
        video=video_data,
        filename="test.mp4",
    )

    file_path = Path(result)

    assert file_path.exists()
    assert file_path.read_bytes() == video_data


def test_reject_invalid_filename(tmp_path):
    storage = LocalMediaStorage(
        base_directory=str(tmp_path)
    )

    with pytest.raises(ValueError):
        storage.save_audio(
            audio=b"test",
            filename="../unsafe.mp3",
        )