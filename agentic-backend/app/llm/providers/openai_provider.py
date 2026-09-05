from typing import Any, Dict, Optional

from openai import OpenAI

from app.llm.base import BaseLLMProvider
from app.llm.exceptions import (
    LLMAuthenticationError,
    LLMInvalidRequestError,
    LLMProviderError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI implementation of the common LLM provider interface.

    This class is responsible only for communicating with OpenAI.
    API-key selection, fallback, retry policy, and orchestration
    are handled by other layers.
    """

    provider_name = "openai"

    def __init__(
        self,
        api_key: str,
        key_id: str,
        model: str,
        **kwargs: Any,
    ):
        super().__init__(
            api_key=api_key,
            key_id=key_id,
            model=model,
            **kwargs,
        )

        timeout = kwargs.get("timeout", 60.0)

        self.client = OpenAI(
            api_key=api_key,
            timeout=timeout,
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
        **kwargs: Any,
    ) -> str:
        """
        Generate a normal text response using OpenAI.
        """

        if not prompt or not prompt.strip():
            raise LLMInvalidRequestError(
                "Prompt must not be empty.",
                provider=self.provider_name,
            )

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        request_kwargs.update(
            self._build_generation_parameters(
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        )

        try:
            response = self.client.chat.completions.create(
                **request_kwargs
            )

            content = response.choices[0].message.content

            if not content:
                raise LLMResponseError(
                    "OpenAI returned an empty response.",
                    provider=self.provider_name,
                    key_id=self.key_id,
                )

            return content.strip()

        except LLMResponseError:
            raise

        except Exception as error:
            raise self._translate_error(error) from error

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
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON using OpenAI structured outputs.

        `response_schema` should be a JSON-schema-compatible
        dictionary.
        """

        if not prompt or not prompt.strip():
            raise LLMInvalidRequestError(
                "Prompt must not be empty.",
                provider=self.provider_name,
            )

        if not response_schema:
            raise LLMInvalidRequestError(
                "response_schema must not be empty.",
                provider=self.provider_name,
            )

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": kwargs.get(
                        "schema_name",
                        "structured_response",
                    ),
                    "strict": True,
                    "schema": response_schema,
                },
            },
        }

        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

        if temperature is not None:
            request_kwargs["temperature"] = temperature

        try:
            response = self.client.chat.completions.create(
                **request_kwargs
            )

            content = response.choices[0].message.content

            if not content:
                raise LLMResponseError(
                    "OpenAI returned an empty structured response.",
                    provider=self.provider_name,
                    key_id=self.key_id,
                )

            return self._parse_json_response(content)

        except LLMResponseError:
            raise

        except Exception as error:
            raise self._translate_error(error) from error

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """
        Perform a lightweight provider health check.

        We intentionally avoid making an unnecessary generation
        request here. The key is considered healthy until a real
        request demonstrates otherwise.
        """

        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_generation_parameters(
        self,
        *,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Build provider generation parameters while keeping
        provider-specific details isolated inside this adapter.
        """

        parameters: Dict[str, Any] = {}

        if temperature is not None:
            parameters["temperature"] = temperature

        if max_tokens is not None:
            parameters["max_tokens"] = max_tokens

        return parameters

    @staticmethod
    def _parse_json_response(
        content: str,
    ) -> Dict[str, Any]:
        """
        Parse a JSON string returned by the provider.
        """

        import json

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            raise LLMResponseError(
                "OpenAI returned invalid JSON.",
                provider="openai",
            ) from error

        if not isinstance(parsed, dict):
            raise LLMResponseError(
                "OpenAI structured response must be a JSON object.",
                provider="openai",
            )

        return parsed

    def _translate_error(
        self,
        error: Exception,
    ) -> Exception:
        """
        Convert OpenAI SDK exceptions into our application's
        normalized LLM exceptions.
        """

        error_text = str(error)
        error_name = error.__class__.__name__.lower()

        if (
            "authentication" in error_name
            or "authentication" in error_text.lower()
            or "invalid api key" in error_text.lower()
            or "401" in error_text
        ):
            return LLMAuthenticationError(
                "OpenAI authentication failed.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "rate" in error_name
            or "rate limit" in error_text.lower()
            or "429" in error_text
        ):
            return LLMRateLimitError(
                "OpenAI rate limit reached.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "quota" in error_text.lower()
            or "insufficient_quota" in error_text.lower()
        ):
            return LLMQuotaExceededError(
                "OpenAI API quota has been exceeded.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "timeout" in error_name
            or "timed out" in error_text.lower()
        ):
            return LLMTimeoutError(
                "OpenAI request timed out.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "badrequest" in error_name
            or "invalidrequest" in error_name
            or "invalid request" in error_text.lower()
            or "400" in error_text
        ):
            return LLMInvalidRequestError(
                "OpenAI rejected the request.",
                provider=self.provider_name,
            )

        return LLMProviderError(
            f"OpenAI provider error: {error_text}",
            provider=self.provider_name,
            key_id=self.key_id,
        )