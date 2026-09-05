"""
Unified LLM service.

This module provides the application's single entry point for
text and structured LLM generation.

Responsibilities:

    - Select an available provider/API key.
    - Create the correct provider adapter.
    - Execute requests with retry handling.
    - Fall back between configured keys/providers.
    - Record provider-key health through KeyManager.

Supported providers:

    - OpenAI
    - Gemini
    - Groq
    - Anthropic
"""

from typing import Any, Dict, List, Optional, Type

from app.llm.base import BaseLLMProvider
from app.llm.exceptions import (
    AllLLMProvidersExhaustedError,
    LLMError,
    LLMInvalidRequestError,
)
from app.llm.key_manager import KeyManager, LLMKey
from app.llm.retry import RetryConfig, RetryPolicy

from app.llm.providers.anthropic_provider import AnthropicProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.groq_provider import GroqProvider
from app.llm.providers.openai_provider import OpenAIProvider


class LLMService:
    """
    Unified gateway for all configured LLM providers.

    Agents should use this class instead of directly importing
    provider SDKs.
    """

    # ------------------------------------------------------------------
    # Provider registry
    # ------------------------------------------------------------------

    PROVIDER_CLASSES: Dict[
        str,
        Type[BaseLLMProvider],
    ] = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "groq": GroqProvider,
        "anthropic": AnthropicProvider,
    }

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(
        self,
        key_manager: KeyManager,
        *,
        retry_config: Optional[RetryConfig] = None,
    ):
        """
        Initialize the LLM service.

        Args:
            key_manager:
                Manager responsible for provider and API-key
                selection and health tracking.

            retry_config:
                Optional retry configuration.
        """

        self.key_manager = key_manager

        self.retry_policy = RetryPolicy(
            retry_config or RetryConfig(),
        )

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate a text response.

        The service attempts available keys according to the
        KeyManager's priority and falls back when a failure is
        considered fallbackable.
        """

        if not prompt or not prompt.strip():
            raise LLMInvalidRequestError(
                "Prompt must not be empty.",
            )

        attempted_keys: List[str] = []
        last_error: Optional[Exception] = None

        while True:
            key = self.key_manager.get_next_key(
                provider=provider,
                exclude_key_ids=attempted_keys,
            )

            if key is None:
                break

            selected_model = (
                model
                if model is not None
                else key.model
            )

            attempted_keys.append(
                key.key_id,
            )

            adapter = self._create_provider(
                key=key,
                model=selected_model,
            )

            try:
                return self._execute_with_retry(
                    adapter.generate,
                    prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    key=key,
                    **kwargs,
                )

            except LLMError as error:
                last_error = error

                if not error.fallbackable:
                    raise

                self._record_failure(
                    key=key,
                    error=error,
                )

                # If a specific provider was requested, allow
                # the service to continue with other providers
                # after that provider's keys are exhausted.
                if provider is not None:
                    provider = None

        if last_error is not None:
            raise AllLLMProvidersExhaustedError(
                "All available LLM providers and API keys "
                "failed for this request.",
            ) from last_error

        raise AllLLMProvidersExhaustedError(
            "No available LLM providers or API keys are configured.",
        )

    # ------------------------------------------------------------------
    # Structured generation
    # ------------------------------------------------------------------

    def generate_structured(
        self,
        prompt: str,
        *,
        response_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a structured response.

        The service attempts available keys according to the
        KeyManager's priority and falls back when a failure is
        considered fallbackable.
        """

        if not prompt or not prompt.strip():
            raise LLMInvalidRequestError(
                "Prompt must not be empty.",
            )

        if not response_schema:
            raise LLMInvalidRequestError(
                "response_schema must not be empty.",
            )

        attempted_keys: List[str] = []
        last_error: Optional[Exception] = None

        while True:
            key = self.key_manager.get_next_key(
                provider=provider,
                exclude_key_ids=attempted_keys,
            )

            if key is None:
                break

            selected_model = (
                model
                if model is not None
                else key.model
            )

            attempted_keys.append(
                key.key_id,
            )

            adapter = self._create_provider(
                key=key,
                model=selected_model,
            )

            try:
                return self._execute_with_retry(
                    adapter.generate_structured,
                    prompt,
                    response_schema=response_schema,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    key=key,
                    **kwargs,
                )

            except LLMError as error:
                last_error = error

                if not error.fallbackable:
                    raise

                self._record_failure(
                    key=key,
                    error=error,
                )

                if provider is not None:
                    provider = None

        if last_error is not None:
            raise AllLLMProvidersExhaustedError(
                "All available LLM providers and API keys "
                "failed for this structured request.",
            ) from last_error

        raise AllLLMProvidersExhaustedError(
            "No available LLM providers or API keys are configured.",
        )

    # ------------------------------------------------------------------
    # Provider creation
    # ------------------------------------------------------------------

    def _create_provider(
        self,
        *,
        key: LLMKey,
        model: str,
    ) -> BaseLLMProvider:
        """
        Create the appropriate provider adapter.
        """

        provider_name = (
            key.provider
            .lower()
            .strip()
        )

        provider_class = self.PROVIDER_CLASSES.get(
            provider_name,
        )

        if provider_class is None:
            raise LLMInvalidRequestError(
                f"Unsupported LLM provider: {key.provider}",
                provider=key.provider,
                key_id=key.key_id,
            )

        return provider_class(
            api_key=key.api_key,
            key_id=key.key_id,
            model=model,
            timeout=60.0,
        )

    # ------------------------------------------------------------------
    # Retry execution
    # ------------------------------------------------------------------

    def _execute_with_retry(
        self,
        operation: Any,
        *args: Any,
        key: LLMKey,
        **kwargs: Any,
    ) -> Any:
        """
        Execute one provider operation using RetryPolicy.
        """

        def call() -> Any:
            return operation(
                *args,
                **kwargs,
            )

        def on_retry(
            error: Exception,
            attempt: int,
            delay: float,
        ) -> None:
            """
            Retry hook reserved for logging and metrics.

            API keys and provider responses must never be logged.
            """

            return None

        result = self.retry_policy.execute(
            call,
            on_retry=on_retry,
        )

        self.key_manager.mark_success(
            key.key_id,
        )

        return result

    # ------------------------------------------------------------------
    # Failure recording
    # ------------------------------------------------------------------

    def _record_failure(
        self,
        *,
        key: LLMKey,
        error: LLMError,
    ) -> None:
        """
        Update KeyManager according to the failure type.
        """

        key_id = (
            error.key_id
            if error.key_id
            else key.key_id
        )

        if error.__class__.__name__ == "LLMAuthenticationError":
            self.key_manager.mark_permanently_disabled(
                key_id,
                error=str(error),
            )
            return

        self.key_manager.mark_failure(
            key_id,
            error=str(error),
        )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_available_providers(
        self,
    ) -> List[str]:
        """
        Return configured provider names.
        """

        return self.key_manager.get_providers()

    def get_key_status(
        self,
        key_id: str,
    ) -> Dict[str, object]:
        """
        Return safe status information for one API key.
        """

        return self.key_manager.get_key_status(
            key_id,
        )