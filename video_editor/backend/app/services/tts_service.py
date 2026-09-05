from app.providers.tts.provider import TTSProvider
from app.storage.media_storage import MediaStorage


class TTSGenerationError(Exception):
    """Raised when speech generation fails."""


class TTSService:
    def __init__(
        self,
        provider: TTSProvider,
        storage: MediaStorage,
    ):
        self.provider = provider
        self.storage = storage

    def generate_audio(
        self,
        text: str,
        voice_id: str,
        filename: str,
    ) -> str:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        if not voice_id or not voice_id.strip():
            raise ValueError("Voice ID cannot be empty.")

        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty.")

        try:
            audio = self.provider.generate_speech(
                text=text,
                voice_id=voice_id,
            )

            if not audio:
                raise TTSGenerationError(
                    "TTS provider returned empty audio."
                )

            file_path = self.storage.save_audio(
                audio=audio,
                filename=filename,
            )

            return file_path

        except (ValueError, TTSGenerationError):
            raise

        except Exception as exc:
            raise TTSGenerationError(
                "Failed to generate and store speech."
            ) from exc