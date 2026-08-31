from abc import ABC, abstractmethod


class TTSProvider(ABC):

    @abstractmethod
    def generate_speech(
        self,
        text: str,
        voice_id: str,
    ) -> bytes:
        """
        Generate speech audio from text.

        Args:
            text: Text to convert into speech.
            voice_id: Identifier of the selected voice.

        Returns:
            Generated audio as bytes.
        """
        raise NotImplementedError