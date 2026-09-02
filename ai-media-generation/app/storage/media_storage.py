from abc import ABC, abstractmethod


class MediaStorage(ABC):

    @abstractmethod
    def save_audio(
        self,
        audio: bytes,
        filename: str,
    ) -> str:
        """
        Save audio data and return its storage path.
        """
        raise NotImplementedError

    @abstractmethod
    def save_image(
        self,
        image: bytes,
        filename: str,
    ) -> str:
        """
        Save image data and return its storage path.
        """
        raise NotImplementedError

    @abstractmethod
    def save_video(
        self,
        video: bytes,
        filename: str,
    ) -> str:
        """
        Save video data and return its storage path.
        """
        raise NotImplementedError