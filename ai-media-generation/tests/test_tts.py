from pathlib import Path

import pytest

from app.services.tts_service import (
    TTSGenerationError,
    TTSService,
)


class FakeTTSProvider:

    def generate_speech(
        self,
        text: str,
        voice_id: str,
    ) -> bytes:
        return b"fake audio data"


class EmptyTTSProvider:

    def generate_speech(
        self,
        text: str,
        voice_id: str,
    ) -> bytes:
        return b""


class FailingTTSProvider:

    def generate_speech(
        self,
        text: str,
        voice_id: str,
    ) -> bytes:
        raise RuntimeError("Provider failed")


class FakeStorage:

    def __init__(self, base_directory):
        self.base_directory = Path(base_directory)

    def save_audio(
        self,
        audio: bytes,
        filename: str,
    ) -> str:

        file_path = (
            self.base_directory / filename
        )

        file_path.write_bytes(audio)

        return str(file_path)


def create_service(
    tmp_path,
    provider,
):
    storage = FakeStorage(tmp_path)

    return TTSService(
        provider=provider,
        storage=storage,
    )


def test_generate_audio_success(tmp_path):

    service = create_service(
        tmp_path,
        FakeTTSProvider(),
    )

    result = service.generate_audio(
        text="Hello, this is a test.",
        voice_id="test-voice",
        filename="test.mp3",
    )

    file_path = Path(result)

    assert file_path.exists()
    assert file_path.read_bytes() == b"fake audio data"


def test_empty_text_rejected(tmp_path):

    service = create_service(
        tmp_path,
        FakeTTSProvider(),
    )

    with pytest.raises(ValueError):
        service.generate_audio(
            text="",
            voice_id="test-voice",
            filename="test.mp3",
        )


def test_empty_voice_id_rejected(tmp_path):

    service = create_service(
        tmp_path,
        FakeTTSProvider(),
    )

    with pytest.raises(ValueError):
        service.generate_audio(
            text="Hello",
            voice_id="",
            filename="test.mp3",
        )


def test_empty_filename_rejected(tmp_path):

    service = create_service(
        tmp_path,
        FakeTTSProvider(),
    )

    with pytest.raises(ValueError):
        service.generate_audio(
            text="Hello",
            voice_id="test-voice",
            filename="",
        )


def test_empty_audio_from_provider(tmp_path):

    service = create_service(
        tmp_path,
        EmptyTTSProvider(),
    )

    with pytest.raises(TTSGenerationError):
        service.generate_audio(
            text="Hello",
            voice_id="test-voice",
            filename="test.mp3",
        )


def test_provider_failure(tmp_path):

    service = create_service(
        tmp_path,
        FailingTTSProvider(),
    )

    with pytest.raises(TTSGenerationError):
        service.generate_audio(
            text="Hello",
            voice_id="test-voice",
            filename="test.mp3",
        )