import json
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

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


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini implementation of the common LLM provider interface.

    Provider-specific Gemini SDK behavior stays inside this adapter.
    Key selection, fallback, and retry decisions are handled elsewhere.
    """

    provider_name = "gemini"

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

        timeout = kwargs.get("timeout")

        client_config: Dict[str, Any] = {
            "api_key": api_key,
        }

        if timeout is not None:
            client_config["http_options"] = types.HttpOptions(
                timeout=int(timeout * 1000),
            )

        self.client = genai.Client(**client_config)

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
        Generate a normal text response using Gemini.
        """

        if not prompt or not prompt.strip():
            raise LLMInvalidRequestError(
                "Prompt must not be empty.",
                provider=self.provider_name,
            )

        config_kwargs: Dict[str, Any] = {
            "temperature": temperature,
        }

        if max_tokens is not None:
            config_kwargs["max_output_tokens"] = max_tokens

        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    **config_kwargs
                ),
            )

            content = getattr(response, "text", None)

            if not content:
                raise LLMResponseError(
                    "Gemini returned an empty response.",
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
        Generate a structured JSON response using Gemini.

        The response is converted into a normal Python dictionary
        before being returned to the rest of the application.
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

        config_kwargs: Dict[str, Any] = {
            "temperature": temperature,
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        }

        if max_tokens is not None:
            config_kwargs["max_output_tokens"] = max_tokens

        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    **config_kwargs
                ),
            )

            content = getattr(response, "text", None)

            if not content:
                raise LLMResponseError(
                    "Gemini returned an empty structured response.",
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
        Return the current local health state.

        We intentionally avoid making a paid generation request
        merely to perform a health check.
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
        Parse Gemini's JSON response into a Python dictionary.
        """

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            raise LLMResponseError(
                "Gemini returned invalid JSON.",
                provider=self.provider_name,
                key_id=self.key_id,
            ) from error

        if not isinstance(parsed, dict):
            raise LLMResponseError(
                "Gemini structured response must be a JSON object.",
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
        Convert Gemini SDK/API errors into application-level
        LLM exceptions.
        """

        error_text = str(error)
        error_lower = error_text.lower()
        error_name = error.__class__.__name__.lower()

        if (
            "authentication" in error_name
            or "api key" in error_lower
            or "unauthenticated" in error_lower
            or "401" in error_text
        ):
            return LLMAuthenticationError(
                "Gemini authentication failed.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "resourceexhausted" in error_name
            or "quota" in error_lower
            or "quota exceeded" in error_lower
        ):
            return LLMQuotaExceededError(
                "Gemini API quota has been exceeded.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "rate" in error_lower
            or "too many requests" in error_lower
            or "429" in error_text
        ):
            return LLMRateLimitError(
                "Gemini rate limit reached.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "timeout" in error_name
            or "timed out" in error_lower
        ):
            return LLMTimeoutError(
                "Gemini request timed out.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if (
            "invalidargument" in error_name
            or "invalid argument" in error_lower
            or "bad request" in error_lower
            or "400" in error_text
        ):
            return LLMInvalidRequestError(
                "Gemini rejected the request.",
                provider=self.provider_name,
            )

        return LLMProviderError(
            f"Gemini provider error: {error_text}",
            provider=self.provider_name,
            key_id=self.key_id,
        )