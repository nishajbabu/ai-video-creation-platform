from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseLLMProvider(ABC):
    """
    Common interface that every LLM provider adapter must implement.

    Provider-specific SDK details must stay inside the individual
    provider adapter classes.
    """

    provider_name: str = "unknown"

    def __init__(
        self,
        api_key: str,
        key_id: str,
        model: str,
        **kwargs: Any,
    ):
        if not api_key:
            raise ValueError("api_key must not be empty")

        if not key_id:
            raise ValueError("key_id must not be empty")

        if not model:
            raise ValueError("model must not be empty")

        self.api_key = api_key
        self.key_id = key_id
        self.model = model
        self.config = kwargs

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate a text response from the provider.

        Every provider adapter must implement this method.
        """

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        *,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a structured response.

        The provider adapter is responsible for converting its
        provider-specific structured-output mechanism into a
        standard Python dictionary.
        """

    def health_check(self) -> bool:
        """
        Perform a basic provider health check.

        Providers can override this method when they support
        an inexpensive health-check operation.

        Returning True by default means that the key/provider
        has not been explicitly marked unhealthy.
        """
        return True

    def get_provider_name(self) -> str:
        """
        Return the normalized provider name.
        """
        return self.provider_name

    def get_key_id(self) -> str:
        """
        Return the identifier of the API key currently used
        by this provider instance.

        The actual secret API key is never returned.
        """
        return self.key_id

    def get_model(self) -> str:
        """
        Return the model configured for this provider instance.
        """
        return self.model