from app.providers.tts.voice_provider import VoiceProvider


class VoiceService:
    def __init__(self, provider: VoiceProvider):
        self.provider = provider

    def list_voices(self) -> list[dict]:
        try:
            return self.provider.list_voices()

        except Exception as exc:
            raise RuntimeError(
                "Failed to retrieve available voices."
            ) from exc