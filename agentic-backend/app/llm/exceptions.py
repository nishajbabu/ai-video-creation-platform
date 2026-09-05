from typing import Optional


class LLMError(Exception):
    """
    Base exception for all LLM-related failures.

    Every provider-specific failure is converted into one of the
    application's LLM exceptions before reaching the higher layers.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        key_id: Optional[str] = None,
        retryable: bool = True,
        fallbackable: bool = True,
    ):
        super().__init__(message)

        self.message = message
        self.provider = provider
        self.key_id = key_id
        self.retryable = retryable
        self.fallbackable = fallbackable

    def __str__(self) -> str:
        context = []

        if self.provider:
            context.append(
                f"provider={self.provider}"
            )

        if self.key_id:
            context.append(
                f"key={self.key_id}"
            )

        if context:
            return (
                f"[{', '.join(context)}] "
                f"{self.message}"
            )

        return self.message


class LLMConfigurationError(LLMError):
    """
    Raised when the LLM system is incorrectly configured.

    Configuration errors should not trigger provider fallback.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        key_id: Optional[str] = None,
    ):
        super().__init__(
            message,
            provider=provider,
            key_id=key_id,
            retryable=False,
            fallbackable=False,
        )


class LLMAuthenticationError(LLMError):
    """
    Raised when a provider rejects an API key.

    The current key should normally be marked unhealthy and the
    fallback system should try another key/provider.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        key_id: Optional[str] = None,
    ):
        super().__init__(
            message,
            provider=provider,
            key_id=key_id,
            retryable=False,
            fallbackable=True,
        )


class LLMRateLimitError(LLMError):
    """
    Raised when the current provider/key is rate limited.

    The system can move to another key or provider.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        key_id: Optional[str] = None,
    ):
        super().__init__(
            message,
            provider=provider,
            key_id=key_id,
            retryable=True,
            fallbackable=True,
        )


class LLMQuotaExceededError(LLMError):
    """
    Raised when the current API key has exhausted its quota.

    This is one of the primary conditions that triggers
    multi-key and multi-provider fallback.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        key_id: Optional[str] = None,
    ):
        super().__init__(
            message,
            provider=provider,
            key_id=key_id,
            retryable=False,
            fallbackable=True,
        )


class LLMTimeoutError(LLMError):
    """
    Raised when an LLM request exceeds the configured timeout.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        key_id: Optional[str] = None,
    ):
        super().__init__(
            message,
            provider=provider,
            key_id=key_id,
            retryable=True,
            fallbackable=True,
        )


class LLMProviderError(LLMError):
    """
    Raised for temporary or general provider-side failures.

    The fallback system may try another key/provider.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        key_id: Optional[str] = None,
    ):
        super().__init__(
            message,
            provider=provider,
            key_id=key_id,
            retryable=True,
            fallbackable=True,
        )


class LLMResponseError(LLMError):
    """
    Raised when the provider responds but the returned content
    is malformed, empty, or otherwise unusable.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        key_id: Optional[str] = None,
    ):
        super().__init__(
            message,
            provider=provider,
            key_id=key_id,
            retryable=True,
            fallbackable=True,
        )


class LLMInvalidRequestError(LLMError):
    """
    Raised when the request itself is invalid.

    Switching API providers will not fix an invalid request,
    so fallback should stop.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        key_id: Optional[str] = None,
    ):
        super().__init__(
            message,
            provider=provider,
            key_id=key_id,
            retryable=False,
            fallbackable=False,
        )


class AllLLMProvidersExhaustedError(LLMError):
    """
    Raised when every available provider/key combination has
    failed or become unavailable.

    This represents the final failure of the fallback system.
    """

    def __init__(
        self,
        message: str = (
            "All configured LLM providers and API keys "
            "have been exhausted."
        ),
    ):
        super().__init__(
            message,
            retryable=False,
            fallbackable=False,
        )