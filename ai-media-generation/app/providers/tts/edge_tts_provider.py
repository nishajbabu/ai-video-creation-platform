import asyncio

import edge_tts

from app.providers.tts.provider import TTSProvider


class EdgeTTSProvider(TTSProvider):

    def generate_speech(
        self,
        text: str,
        voice_id: str,
    ) -> bytes:
        return asyncio.run(
            self._generate_speech_async(
                text=text,
                voice_id=voice_id,
            )
        )

    async def _generate_speech_async(
        self,
        text: str,
        voice_id: str,
    ) -> bytes:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice_id,
        )

        audio_chunks = []

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        return b"".join(audio_chunks)
    