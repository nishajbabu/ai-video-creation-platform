from abc import ABC, abstractmethod


class ImageProvider(ABC):

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
    ) -> bytes:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the image to generate.

        Returns:
            Generated image as bytes.
        """
        raise NotImplementedError