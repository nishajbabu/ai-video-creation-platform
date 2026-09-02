from typing import Any, Dict, Optional
import json

from groq import Groq

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


class GroqProvider(BaseLLMProvider):
    """
    Groq implementation of the common LLM provider interface.

    Provider-specific SDK behavior stays inside this adapter.
    API-key selection, fallback, and retry decisions are handled
    by the higher-level LLM service.
    """

    provider_name = "groq"

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

        self.client = Groq(
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
        Generate a normal text response using Groq.
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

        if temperature is not None:
            request_kwargs["temperature"] = temperature

        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

        try:
            response = self.client.chat.completions.create(
                **request_kwargs
            )

            content = response.choices[0].message.content

            if not content:
                raise LLMResponseError(
                    "Groq returned an empty response.",
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
        Generate a JSON response using Groq's JSON-object response mode.

        The returned JSON is converted into a Python dictionary.
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

        schema_text = json.dumps(response_schema)

        structured_instruction = (
            "Return ONLY valid JSON. "
            "The JSON must conform to this schema:\n"
            f"{schema_text}"
        )

        if system_prompt:
            system_prompt = (
                f"{system_prompt}\n\n"
                f"{structured_instruction}"
            )
        else:
            system_prompt = structured_instruction

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "response_format": {
                "type": "json_object",
            },
        }

        if temperature is not None:
            request_kwargs["temperature"] = temperature

        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

        try:
            response = self.client.chat.completions.create(
                **request_kwargs
            )

            content = response.choices[0].message.content

            if not content:
                raise LLMResponseError(
                    "Groq returned an empty structured response.",
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
        Return the local provider health state.

        No generation request is made.
        """

        return True

    # ------------------------------------------------------------------
    # JSON parsing
    # ------------------------------------------------------------------

    def _parse_json_response(
        self,
        content: str,
    ) -> Dict[str, Any]:
        """
        Convert a JSON response into a Python dictionary.
        """

        try:
            parsed = json.loads(content)

        except json.JSONDecodeError as error:
            raise LLMResponseError(
                "Groq returned invalid JSON.",
                provider=self.provider_name,
                key_id=self.key_id,
            ) from error

        if not isinstance(parsed, dict):
            raise LLMResponseError(
                "Groq structured response must be a JSON object.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        return parsed

    # ------------------------------------------------------------------
    # Error translation
    # ------------------------------------------------------------------

    def _translate_error(
        self,
        error: Exception,
    ) -> Exception:
        """
        Convert Groq SDK/API errors into our application's
        normalized LLM exceptions.
        """

        error_text = str(error)
        error_lower = error_text.lower()
        error_name = error.__class__.__name__.lower()

        if (
            "authentication" in error_name
            or "authentication" in error_lower
            or "invalid api key" in error_lower
            or "401" in error_text
        ):
            return LLMAuthenticationError(
                "Groq authentication failed.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "rate" in error_name
            or "rate limit" in error_lower
            or "too many requests" in error_lower
            or "429" in error_text
        ):
            return LLMRateLimitError(
                "Groq rate limit reached.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "quota" in error_lower
            or "quota exceeded" in error_lower
            or "limit reached" in error_lower
        ):
            return LLMQuotaExceededError(
                "Groq API quota or usage limit has been exceeded.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "timeout" in error_name
            or "timed out" in error_lower
        ):
            return LLMTimeoutError(
                "Groq request timed out.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "badrequest" in error_name
            or "invalidrequest" in error_name
            or "invalid request" in error_lower
            or "400" in error_text
        ):
            return LLMInvalidRequestError(
                "Groq rejected the request.",
                provider=self.provider_name,
            )

        return LLMProviderError(
            f"Groq provider error: {error_text}",
            provider=self.provider_name,
            key_id=self.key_id,
        )