import asyncio

import edge_tts

from app.providers.tts.voice_provider import VoiceProvider


class EdgeTTSVoiceProvider(VoiceProvider):

    def list_voices(self) -> list[dict]:
        return asyncio.run(
            self._list_voices_async()
        )

    async def _list_voices_async(self) -> list[dict]:
        voices = await edge_tts.list_voices()

        return [
            {
                "id": voice["ShortName"],
                "name": voice["ShortName"],
                "language": voice["Locale"],
                "gender": voice["Gender"],
            }
            for voice in voices
        ]