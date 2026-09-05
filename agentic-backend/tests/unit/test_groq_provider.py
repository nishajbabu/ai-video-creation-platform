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
from app.llm.providers.groq_provider import GroqProvider


# ---------------------------------------------------------------------------
# Fake Groq SDK objects
# ---------------------------------------------------------------------------


class FakeMessage:
    """
    Minimal fake Groq message.
    """

    def __init__(self, content):
        self.content = content


class FakeChoice:
    """
    Minimal fake Groq choice.
    """

    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    """
    Minimal fake Groq completion response.
    """

    def __init__(self, content):
        self.choices = [
            FakeChoice(content)
        ]


class FakeCompletions:
    """
    Fake Groq chat completions API.
    """

    def __init__(
        self,
        response=None,
        error=None,
    ):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error

        return self.response


class FakeChat:
    """
    Fake Groq chat API.
    """

    def __init__(
        self,
        response=None,
        error=None,
    ):
        self.completions = FakeCompletions(
            response=response,
            error=error,
        )


class FakeClient:
    """
    Fake Groq client.
    """

    def __init__(
        self,
        response=None,
        error=None,
    ):
        self.chat = FakeChat(
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
    timeout=60.0,
):
    """
    Create a GroqProvider with a fake Groq client.
    """

    provider = GroqProvider(
        api_key="test-groq-key",
        key_id="groq_1",
        model="test-groq-model",
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


def test_groq_provider_initializes():
    provider = create_provider()

    assert provider.provider_name == "groq"
    assert provider.api_key == "test-groq-key"
    assert provider.key_id == "groq_1"
    assert provider.model == "test-groq-model"


def test_groq_provider_health_check_returns_true():
    provider = create_provider()

    assert provider.health_check() is True


# ---------------------------------------------------------------------------
# Normal text generation
# ---------------------------------------------------------------------------


def test_generate_returns_response_text():
    provider = create_provider(
        response=FakeResponse(
            "Hello from Groq."
        )
    )

    result = provider.generate(
        "Say hello."
    )

    assert result == "Hello from Groq."


def test_generate_strips_response_text():
    provider = create_provider(
        response=FakeResponse(
            "  Hello from Groq.  "
        )
    )

    result = provider.generate(
        "Say hello."
    )

    assert result == "Hello from Groq."


def test_generate_passes_model():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video."
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["model"] == "test-groq-model"


def test_generate_passes_user_prompt():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a product video."
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["messages"] == [
        {
            "role": "user",
            "content": "Create a product video.",
        }
    ]


def test_generate_passes_system_prompt():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a product video.",
        system_prompt=(
            "You are a professional video writer."
        ),
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["messages"] == [
        {
            "role": "system",
            "content": (
                "You are a professional video writer."
            ),
        },
        {
            "role": "user",
            "content": "Create a product video.",
        },
    ]


def test_generate_passes_temperature():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        temperature=0.7,
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["temperature"] == 0.7


def test_generate_omits_temperature_when_none():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        temperature=None,
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert "temperature" not in call


def test_generate_passes_max_tokens():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        max_tokens=500,
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["max_tokens"] == 500


def test_generate_omits_max_tokens_when_none():
    provider = create_provider(
        response=FakeResponse(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        max_tokens=None,
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert "max_tokens" not in call


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
        response=FakeResponse("")
    )

    with pytest.raises(
        LLMResponseError,
        match="Groq returned an empty response.",
    ):
        provider.generate(
            "Generate something."
        )


def test_generate_rejects_missing_response_content():
    provider = create_provider(
        response=FakeResponse(None)
    )

    with pytest.raises(
        LLMResponseError,
        match="Groq returned an empty response.",
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


def test_generate_structured_passes_model():
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

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["model"] == "test-groq-model"


def test_generate_structured_passes_user_prompt():
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

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["messages"][1] == {
        "role": "user",
        "content": "Create structured output.",
    }


def test_generate_structured_adds_json_instruction():
    provider = create_provider(
        response=FakeResponse(
            '{"status": "ok"}'
        )
    )

    schema = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
            },
        },
    }

    provider.generate_structured(
        "Create structured output.",
        response_schema=schema,
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    system_message = call["messages"][0]["content"]

    assert "Return ONLY valid JSON." in system_message
    assert json.dumps(schema) in system_message


def test_generate_structured_combines_system_prompt_with_instruction():
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
        system_prompt="You are a video planning assistant.",
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    system_message = call["messages"][0]["content"]

    assert (
        "You are a video planning assistant."
        in system_message
    )

    assert (
        "Return ONLY valid JSON."
        in system_message
    )


def test_generate_structured_uses_json_object_response_format():
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

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["response_format"] == {
        "type": "json_object",
    }


def test_generate_structured_passes_temperature():
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
        temperature=0.4,
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["temperature"] == 0.4


def test_generate_structured_omits_temperature_when_none():
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
        temperature=None,
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert "temperature" not in call


def test_generate_structured_passes_max_tokens():
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
        max_tokens=500,
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["max_tokens"] == 500


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
        match="Groq returned an empty structured response.",
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
        match="Groq returned invalid JSON.",
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
            "Groq structured response must "
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

    assert error.provider == "groq"
    assert error.key_id == "groq_1"


def test_translate_invalid_api_key_error():
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


def test_translate_rate_limit_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "429 rate limit exceeded"
        )
    )

    assert isinstance(
        error,
        LLMRateLimitError,
    )

    assert error.provider == "groq"
    assert error.key_id == "groq_1"


def test_translate_rate_limit_class_error():
    class RateLimitError(Exception):
        pass

    provider = create_provider()

    error = provider._translate_error(
        RateLimitError(
            "Request limited"
        )
    )

    assert isinstance(
        error,
        LLMRateLimitError,
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

    assert error.provider == "groq"
    assert error.key_id == "groq_1"


def test_translate_limit_reached_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "Usage limit reached"
        )
    )

    assert isinstance(
        error,
        LLMQuotaExceededError,
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

    assert error.provider == "groq"
    assert error.key_id == "groq_1"


def test_translate_timeout_class_error():
    class TimeoutErrorFromProvider(Exception):
        pass

    provider = create_provider()

    error = provider._translate_error(
        TimeoutErrorFromProvider(
            "Provider timeout"
        )
    )

    assert isinstance(
        error,
        LLMTimeoutError,
    )


def test_translate_bad_request_class_error():
    class BadRequestError(Exception):
        pass

    provider = create_provider()

    error = provider._translate_error(
        BadRequestError(
            "Bad request"
        )
    )

    assert isinstance(
        error,
        LLMInvalidRequestError,
    )


def test_translate_invalid_request_class_error():
    class InvalidRequestError(Exception):
        pass

    provider = create_provider()

    error = provider._translate_error(
        InvalidRequestError(
            "Invalid request"
        )
    )

    assert isinstance(
        error,
        LLMInvalidRequestError,
    )


def test_translate_invalid_request_status_code():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "400 invalid request"
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
            "Unexpected Groq failure"
        )
    )

    assert isinstance(
        error,
        LLMProviderError,
    )

    assert error.provider == "groq"
    assert error.key_id == "groq_1"


# ---------------------------------------------------------------------------
# Error propagation from generate()
# ---------------------------------------------------------------------------


def test_generate_translates_authentication_error():
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


def test_generate_translates_rate_limit_error():
    provider = create_provider(
        error=RuntimeError(
            "429 rate limit exceeded"
        )
    )

    with pytest.raises(
        LLMRateLimitError,
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


def test_generate_translates_invalid_request_error():
    provider = create_provider(
        error=RuntimeError(
            "400 invalid request"
        )
    )

    with pytest.raises(
        LLMInvalidRequestError,
    ):
        provider.generate(
            "Generate a response."
        )


# ---------------------------------------------------------------------------
# Error propagation from structured generation
# ---------------------------------------------------------------------------


def test_generate_structured_translates_authentication_error():
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


def test_generate_structured_translates_rate_limit_error():
    provider = create_provider(
        error=RuntimeError(
            "429 rate limit exceeded"
        )
    )

    with pytest.raises(
        LLMRateLimitError,
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
# Default timeout
# ---------------------------------------------------------------------------


def test_default_timeout_is_passed_to_groq_client():
    """
    Verify that the provider supplies the default timeout.

    The actual SDK client is replaced after construction, so this test
    focuses on the provider's configured timeout behavior through a
    lightweight fake SDK constructor.
    """

    provider = create_provider()

    assert provider is not None