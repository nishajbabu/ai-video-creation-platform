from elevenlabs.client import ElevenLabs

from app.core.config import settings
from app.providers.tts.provider import TTSProvider


class ElevenLabsTTSProvider(TTSProvider):

    def __init__(self):
        self.client = ElevenLabs(
            api_key=settings.elevenlabs_api_key
        )

    def generate_speech(
        self,
        text: str,
        voice_id: str,
    ) -> bytes:

        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=settings.elevenlabs_tts_model,
        )

        return b"".join(audio)