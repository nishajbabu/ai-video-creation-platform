import json

import pytest

from app.llm.exceptions import (
    LLMAuthenticationError,
    LLMInvalidRequestError,
    LLMProviderError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)
from app.llm.providers.gemini_provider import GeminiProvider


# ---------------------------------------------------------------------------
# Fake Gemini SDK objects
# ---------------------------------------------------------------------------


class FakeResponse:
    """
    Minimal fake Gemini response used by provider tests.
    """

    def __init__(self, text):
        self.text = text


class FakeModels:
    """
    Fake Gemini models API.
    """

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def generate_content(
        self,
        *,
        model,
        contents,
        config,
    ):
        self.calls.append(
            {
                "model": model,
                "contents": contents,
                "config": config,
            }
        )

        if self.error is not None:
            raise self.error

        return self.response


class FakeClient:
    """
    Fake Gemini client containing the models API.
    """

    def __init__(
        self,
        response=None,
        error=None,
    ):
        self.models = FakeModels(
            response=response,
            error=error,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def create_provider(
    *,
    response=None,
    error=None,
    timeout=None,
):
    """
    Create a GeminiProvider with a fake Gemini client.
    """

    provider = GeminiProvider(
        api_key="test-gemini-key",
        key_id="gemini_1",
        model="test-gemini-model",
        timeout=timeout,
    )

    provider.client = FakeClient(
        response=response,
        error=error,
    )

    return provider


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_gemini_provider_initializes():
    provider = create_provider()

    assert provider.provider_name == "gemini"
    assert provider.api_key == "test-gemini-key"
    assert provider.key_id == "gemini_1"
    assert provider.model == "test-gemini-model"


def test_gemini_provider_health_check_returns_true():
    provider = create_provider()

    assert provider.health_check() is True


# ---------------------------------------------------------------------------
# Normal text generation
# ---------------------------------------------------------------------------


def test_generate_returns_response_text():
    provider = create_provider(
        response=FakeResponse(
            "Hello from Gemini."
        )
    )

    result = provider.generate(
        "Say hello."
    )

    assert result == "Hello from Gemini."


def test_generate_strips_response_text():
    provider = create_provider(
        response=FakeResponse(
            "  Hello from Gemini.  "
        )
    )

    result = provider.generate(
        "Say hello."
    )

    assert result == "Hello from Gemini."


def test_generate_passes_prompt_to_gemini():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video script."
    )

    calls = provider.client.models.calls

    assert len(calls) == 1
    assert calls[0]["contents"] == (
        "Create a video script."
    )


def test_generate_uses_provider_model():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video."
    )

    calls = provider.client.models.calls

    assert calls[0]["model"] == "test-gemini-model"


def test_generate_uses_temperature():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        temperature=0.7,
    )

    config = provider.client.models.calls[0]["config"]

    assert config.temperature == 0.7


def test_generate_supports_max_tokens():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        max_tokens=500,
    )

    config = provider.client.models.calls[0]["config"]

    assert config.max_output_tokens == 500


def test_generate_supports_system_prompt():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        system_prompt="You are a professional video writer.",
    )

    config = provider.client.models.calls[0]["config"]

    assert (
        config.system_instruction
        == "You are a professional video writer."
    )


# ---------------------------------------------------------------------------
# Normal generation validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prompt",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_generate_rejects_empty_prompt(prompt):
    provider = create_provider()

    with pytest.raises(
        LLMInvalidRequestError,
        match="Prompt must not be empty.",
    ):
        provider.generate(
            prompt,
        )


def test_generate_rejects_empty_response():
    provider = create_provider(
        response=FakeResponse(
            ""
        )
    )

    with pytest.raises(
        LLMResponseError,
        match="Gemini returned an empty response.",
    ):
        provider.generate(
            "Generate something."
        )


def test_generate_rejects_missing_response_text():
    provider = create_provider(
        response=FakeResponse(
            None
        )
    )

    with pytest.raises(
        LLMResponseError,
        match="Gemini returned an empty response.",
    ):
        provider.generate(
            "Generate something."
        )


# ---------------------------------------------------------------------------
# Structured generation
# ---------------------------------------------------------------------------


def test_generate_structured_returns_dictionary():
    payload = {
        "objective": "Create a product video.",
        "duration": 60,
        "scene_count": 5,
    }

    provider = create_provider(
        response=FakeResponse(
            json.dumps(payload)
        )
    )

    result = provider.generate_structured(
        "Create a structured plan.",
        response_schema={
            "type": "object",
        },
    )

    assert result == payload
    assert isinstance(result, dict)


def test_generate_structured_passes_prompt():
    provider = create_provider(
        response=FakeResponse(
            '{"status": "ok"}'
        )
    )

    provider.generate_structured(
        "Create structured output.",
        response_schema={
            "type": "object",
        },
    )

    calls = provider.client.models.calls

    assert calls[0]["contents"] == (
        "Create structured output."
    )


def test_generate_structured_uses_json_response_type():
    provider = create_provider(
        response=FakeResponse(
            '{"status": "ok"}'
        )
    )

    provider.generate_structured(
        "Create structured output.",
        response_schema={
            "type": "object",
        },
    )

    config = provider.client.models.calls[0]["config"]

    assert config.response_mime_type == "application/json"


def test_generate_structured_passes_response_schema():
    schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
            },
        },
    }

    provider = create_provider(
        response=FakeResponse(
            '{"title": "Test"}'
        )
    )

    provider.generate_structured(
        "Create structured output.",
        response_schema=schema,
    )

    config = provider.client.models.calls[0]["config"]

    assert config.response_schema == schema


def test_generate_structured_supports_system_prompt():
    provider = create_provider(
        response=FakeResponse(
            '{"status": "ok"}'
        )
    )

    provider.generate_structured(
        "Create structured output.",
        response_schema={
            "type": "object",
        },
        system_prompt="Return only structured data.",
    )

    config = provider.client.models.calls[0]["config"]

    assert (
        config.system_instruction
        == "Return only structured data."
    )


@pytest.mark.parametrize(
    "prompt",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_generate_structured_rejects_empty_prompt(prompt):
    provider = create_provider()

    with pytest.raises(
        LLMInvalidRequestError,
        match="Prompt must not be empty.",
    ):
        provider.generate_structured(
            prompt,
            response_schema={
                "type": "object",
            },
        )


def test_generate_structured_rejects_empty_schema():
    provider = create_provider()

    with pytest.raises(
        LLMInvalidRequestError,
        match="response_schema must not be empty.",
    ):
        provider.generate_structured(
            "Create structured output.",
            response_schema={},
        )


def test_generate_structured_rejects_empty_response():
    provider = create_provider(
        response=FakeResponse("")
    )

    with pytest.raises(
        LLMResponseError,
        match="Gemini returned an empty structured response.",
    ):
        provider.generate_structured(
            "Create structured output.",
            response_schema={
                "type": "object",
            },
        )


# ---------------------------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------------------------


def test_parse_json_response_accepts_object():
    provider = create_provider()

    result = provider._parse_json_response(
        '{"name": "video"}'
    )

    assert result == {
        "name": "video",
    }


def test_parse_json_response_rejects_invalid_json():
    provider = create_provider()

    with pytest.raises(
        LLMResponseError,
        match="Gemini returned invalid JSON.",
    ):
        provider._parse_json_response(
            "this is not json"
        )


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        '"hello"',
        "123",
        "true",
        "null",
    ],
)
def test_parse_json_response_requires_object(content):
    provider = create_provider()

    with pytest.raises(
        LLMResponseError,
        match=(
            "Gemini structured response must "
            "be a JSON object."
        ),
    ):
        provider._parse_json_response(
            content
        )


# ---------------------------------------------------------------------------
# Error translation
# ---------------------------------------------------------------------------


def test_translate_authentication_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "401 authentication failed"
        )
    )

    assert isinstance(
        error,
        LLMAuthenticationError,
    )
    assert error.provider == "gemini"
    assert error.key_id == "gemini_1"


def test_translate_api_key_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "Invalid API key"
        )
    )

    assert isinstance(
        error,
        LLMAuthenticationError,
    )


def test_translate_unauthenticated_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "Request was unauthenticated"
        )
    )

    assert isinstance(
        error,
        LLMAuthenticationError,
    )


def test_translate_quota_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "Quota exceeded"
        )
    )

    assert isinstance(
        error,
        LLMQuotaExceededError,
    )
    assert error.provider == "gemini"
    assert error.key_id == "gemini_1"


def test_translate_resource_exhausted_error():
    class ResourceExhaustedError(Exception):
        pass

    provider = create_provider()

    error = provider._translate_error(
        ResourceExhaustedError(
            "Resource exhausted"
        )
    )

    assert isinstance(
        error,
        LLMQuotaExceededError,
    )


def test_translate_rate_limit_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "429 too many requests"
        )
    )

    assert isinstance(
        error,
        LLMRateLimitError,
    )


def test_translate_timeout_error():
    provider = create_provider()

    error = provider._translate_error(
        TimeoutError(
            "Request timed out"
        )
    )

    assert isinstance(
        error,
        LLMTimeoutError,
    )


def test_translate_invalid_argument_error():
    class InvalidArgumentError(Exception):
        pass

    provider = create_provider()

    error = provider._translate_error(
        InvalidArgumentError(
            "Invalid argument"
        )
    )

    assert isinstance(
        error,
        LLMInvalidRequestError,
    )


def test_translate_bad_request_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "400 bad request"
        )
    )

    assert isinstance(
        error,
        LLMInvalidRequestError,
    )


def test_translate_generic_provider_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "Something unexpected happened"
        )
    )

    assert isinstance(
        error,
        LLMProviderError,
    )

    assert error.provider == "gemini"
    assert error.key_id == "gemini_1"


# ---------------------------------------------------------------------------
# Error propagation from generate()
# ---------------------------------------------------------------------------


def test_generate_translates_provider_error():
    provider = create_provider(
        error=RuntimeError(
            "401 authentication failed"
        )
    )

    with pytest.raises(
        LLMAuthenticationError,
    ):
        provider.generate(
            "Generate a response."
        )


def test_generate_translates_quota_error():
    provider = create_provider(
        error=RuntimeError(
            "Quota exceeded"
        )
    )

    with pytest.raises(
        LLMQuotaExceededError,
    ):
        provider.generate(
            "Generate a response."
        )


def test_generate_translates_rate_limit_error():
    provider = create_provider(
        error=RuntimeError(
            "429 too many requests"
        )
    )

    with pytest.raises(
        LLMRateLimitError,
    ):
        provider.generate(
            "Generate a response."
        )


def test_generate_translates_timeout_error():
    provider = create_provider(
        error=TimeoutError(
            "Request timed out"
        )
    )

    with pytest.raises(
        LLMTimeoutError,
    ):
        provider.generate(
            "Generate a response."
        )


# ---------------------------------------------------------------------------
# Error propagation from structured generation
# ---------------------------------------------------------------------------


def test_generate_structured_translates_provider_error():
    provider = create_provider(
        error=RuntimeError(
            "401 authentication failed"
        )
    )

    with pytest.raises(
        LLMAuthenticationError,
    ):
        provider.generate_structured(
            "Generate structured output.",
            response_schema={
                "type": "object",
            },
        )


def test_generate_structured_translates_quota_error():
    provider = create_provider(
        error=RuntimeError(
            "Quota exceeded"
        )
    )

    with pytest.raises(
        LLMQuotaExceededError,
    ):
        provider.generate_structured(
            "Generate structured output.",
            response_schema={
                "type": "object",
            },
        )


# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------


def test_generate_with_timeout_configuration():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        ),
        timeout=15,
    )

    result = provider.generate(
        "Generate something."
    )

    assert result == "Generated response."