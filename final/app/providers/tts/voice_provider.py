from abc import ABC, abstractmethod


class VoiceProvider(ABC):

    @abstractmethod
    def list_voices(self) -> list[dict]:
        """
        Return the voices available from the TTS provider.
        """
        raise NotImplementedError