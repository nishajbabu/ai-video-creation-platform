from abc import ABC, abstractmethod


class VideoProvider(ABC):

    @abstractmethod
    def generate_video(
        self,
        prompt: str,
        image_url: str | None = None,
        audio_url: str | None = None,
        duration: int = 5,
    ) -> bytes:
        """
        Generate a video from a prompt, optional image,
        and optional narration audio.

        Args:
            prompt: Description of the desired video.
            image_url: Optional input image path.
            audio_url: Optional narration audio path.
            duration: Desired video duration in seconds.

        Returns:
            Generated video as bytes.
        """
        raise NotImplementedError