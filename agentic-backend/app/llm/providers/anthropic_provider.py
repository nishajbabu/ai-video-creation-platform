from typing import Any, Dict, Optional
import json

from anthropic import Anthropic

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


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic implementation of the common LLM provider interface.

    Provider-specific SDK behavior stays inside this adapter.

    API-key selection, fallback, retry handling, and orchestration
    are handled by the higher-level LLM service.
    """

    provider_name = "anthropic"

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

        self.client = Anthropic(
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
        Generate a normal text response using Anthropic.
        """

        if not prompt or not prompt.strip():
            raise LLMInvalidRequestError(
                "Prompt must not be empty.",
                provider=self.provider_name,
            )

        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or 4096,
        }

        if system_prompt:
            request_kwargs["system"] = system_prompt

        if temperature is not None:
            request_kwargs["temperature"] = temperature

        try:
            response = self.client.messages.create(
                **request_kwargs
            )

            content = self._extract_text(response)

            if not content:
                raise LLMResponseError(
                    "Anthropic returned an empty response.",
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
        Generate structured JSON using Anthropic.

        Anthropic's response is instructed to contain only JSON.
        The adapter parses and validates that response into a
        Python dictionary.
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

        schema_text = json.dumps(
            response_schema,
            indent=2,
        )

        structured_instruction = (
            "Return ONLY valid JSON. "
            "Do not include markdown fences, explanations, "
            "or additional text.\n\n"
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

        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens or 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "system": system_prompt,
        }

        if temperature is not None:
            request_kwargs["temperature"] = temperature

        try:
            response = self.client.messages.create(
                **request_kwargs
            )

            content = self._extract_text(response)

            if not content:
                raise LLMResponseError(
                    "Anthropic returned an empty structured response.",
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
        Return local provider health state.

        No generation request is made.
        """

        return True

    # ------------------------------------------------------------------
    # Response extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(
        response: Any,
    ) -> str:
        """
        Extract text from an Anthropic Messages API response.
        """

        content_blocks = getattr(
            response,
            "content",
            None,
        )

        if not content_blocks:
            return ""

        text_parts = []

        for block in content_blocks:
            text = getattr(
                block,
                "text",
                None,
            )

            if text:
                text_parts.append(text)

        return "".join(text_parts)

    # ------------------------------------------------------------------
    # JSON parsing
    # ------------------------------------------------------------------

    def _parse_json_response(
        self,
        content: str,
    ) -> Dict[str, Any]:
        """
        Parse Anthropic's structured response into a dictionary.
        """

        cleaned_content = content.strip()

        # Handle accidental markdown fences defensively.
        if cleaned_content.startswith("```"):
            lines = cleaned_content.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned_content = "\n".join(lines).strip()

        if cleaned_content.lower().startswith("json\n"):
            cleaned_content = cleaned_content[5:].strip()

        try:
            parsed = json.loads(cleaned_content)

        except json.JSONDecodeError as error:
            raise LLMResponseError(
                "Anthropic returned invalid JSON.",
                provider=self.provider_name,
                key_id=self.key_id,
            ) from error

        if not isinstance(parsed, dict):
            raise LLMResponseError(
                "Anthropic structured response must be a JSON object.",
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
        Convert Anthropic SDK/API errors into normalized
        application-level LLM exceptions.
        """

        error_text = str(error)
        error_lower = error_text.lower()
        error_name = error.__class__.__name__.lower()

        # --------------------------------------------------------------
        # Authentication
        # --------------------------------------------------------------

        if (
            "authentication" in error_name
            or "authentication" in error_lower
            or "invalid api key" in error_lower
            or "401" in error_text
        ):
            return LLMAuthenticationError(
                "Anthropic authentication failed.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        # --------------------------------------------------------------
        # Rate limit
        # --------------------------------------------------------------

        if (
            "ratelimit" in error_name
            or "rate limit" in error_lower
            or "too many requests" in error_lower
            or "429" in error_text
        ):
            return LLMRateLimitError(
                "Anthropic rate limit reached.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        # --------------------------------------------------------------
        # Quota / billing / credits
        #
        # Anthropic may return HTTP 400 when the account has no
        # remaining credits. This must be checked BEFORE the
        # generic 400 / invalid-request classification.
        # --------------------------------------------------------------

        if (
            "quota" in error_lower
            or "quota exceeded" in error_lower
            or "usage limit" in error_lower
            or "credit balance" in error_lower
            or "credit balance is too low" in error_lower
            or "insufficient credit" in error_lower
            or "insufficient credits" in error_lower
            or "billing" in error_lower
            or "purchase credits" in error_lower
            or "plans & billing" in error_lower
        ):
            return LLMQuotaExceededError(
                "Anthropic API quota, credits, or billing limit "
                "has been exceeded.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        # --------------------------------------------------------------
        # Timeout
        # --------------------------------------------------------------

        if (
            "timeout" in error_name
            or "timed out" in error_lower
        ):
            return LLMTimeoutError(
                "Anthropic request timed out.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        # --------------------------------------------------------------
        # Invalid request
        # --------------------------------------------------------------

        if (
            "badrequest" in error_name
            or "invalidrequest" in error_name
            or "invalid request" in error_lower
            or "400" in error_text
        ):
            return LLMInvalidRequestError(
                "Anthropic rejected the request.",
                provider=self.provider_name,
            )

        # --------------------------------------------------------------
        # Unknown provider error
        # --------------------------------------------------------------

        return LLMProviderError(
            f"Anthropic provider error: {error_text}",
            provider=self.provider_name,
            key_id=self.key_id,
        )