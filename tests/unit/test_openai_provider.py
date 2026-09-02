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
from app.llm.providers.openai_provider import OpenAIProvider


# ---------------------------------------------------------------------------
# Fake OpenAI SDK objects
# ---------------------------------------------------------------------------


class FakeMessage:
    """
    Minimal fake OpenAI message.
    """

    def __init__(self, content):
        self.content = content


class FakeChoice:
    """
    Minimal fake OpenAI choice.
    """

    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    """
    Minimal fake OpenAI completion response.
    """

    def __init__(self, content):
        self.choices = [
            FakeChoice(content)
        ]


class FakeCompletions:
    """
    Fake OpenAI chat completions API.
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
    Fake OpenAI chat API.
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
    Fake OpenAI client.
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
    timeout=None,
):
    """
    Create an OpenAIProvider with a fake OpenAI client.
    """

    provider = OpenAIProvider(
        api_key="test-openai-key",
        key_id="openai_1",
        model="test-openai-model",
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


def test_openai_provider_initializes():
    provider = create_provider()

    assert provider.provider_name == "openai"
    assert provider.api_key == "test-openai-key"
    assert provider.key_id == "openai_1"
    assert provider.model == "test-openai-model"


def test_openai_provider_health_check_returns_true():
    provider = create_provider()

    assert provider.health_check() is True


# ---------------------------------------------------------------------------
# Normal text generation
# ---------------------------------------------------------------------------


def test_generate_returns_response_text():
    provider = create_provider(
        response=FakeResponse(
            "Hello from OpenAI."
        )
    )

    result = provider.generate(
        "Say hello."
    )

    assert result == "Hello from OpenAI."


def test_generate_strips_response_text():
    provider = create_provider(
        response=FakeResponse(
            "  Hello from OpenAI.  "
        )
    )

    result = provider.generate(
        "Say hello."
    )

    assert result == "Hello from OpenAI."


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

    assert call["model"] == "test-openai-model"


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
        match="OpenAI returned an empty response.",
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
        match="OpenAI returned an empty response.",
    ):
        provider.generate(
            "Generate something."
        )


# ---------------------------------------------------------------------------
# Generation parameter helper
# ---------------------------------------------------------------------------


def test_build_generation_parameters_includes_temperature():
    provider = create_provider()

    parameters = provider._build_generation_parameters(
        temperature=0.5,
        max_tokens=None,
    )

    assert parameters == {
        "temperature": 0.5,
    }


def test_build_generation_parameters_includes_max_tokens():
    provider = create_provider()

    parameters = provider._build_generation_parameters(
        temperature=0.5,
        max_tokens=300,
    )

    assert parameters == {
        "temperature": 0.5,
        "max_tokens": 300,
    }


def test_build_generation_parameters_allows_none_temperature():
    provider = create_provider()

    parameters = provider._build_generation_parameters(
        temperature=None,
        max_tokens=300,
    )

    assert parameters == {
        "max_tokens": 300,
    }


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

    assert call["model"] == "test-openai-model"


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

    assert call["messages"] == [
        {
            "role": "user",
            "content": "Create structured output.",
        }
    ]


def test_generate_structured_passes_system_prompt():
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
        system_prompt="Return only JSON.",
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
            "content": "Return only JSON.",
        },
        {
            "role": "user",
            "content": "Create structured output.",
        },
    ]


def test_generate_structured_builds_json_schema_response_format():
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

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert call["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "structured_response",
            "strict": True,
            "schema": schema,
        },
    }


def test_generate_structured_supports_custom_schema_name():
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
        schema_name="video_plan",
    )

    call = (
        provider.client
        .chat
        .completions
        .calls[0]
    )

    assert (
        call["response_format"]["json_schema"]["name"]
        == "video_plan"
    )


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
        match="OpenAI returned an empty structured response.",
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
        match="OpenAI returned invalid JSON.",
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
            "OpenAI structured response must "
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

    assert error.provider == "openai"
    assert error.key_id == "openai_1"


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

    assert error.provider == "openai"
    assert error.key_id == "openai_1"


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

    assert error.provider == "openai"
    assert error.key_id == "openai_1"


def test_translate_insufficient_quota_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "insufficient_quota"
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

    assert error.provider == "openai"
    assert error.key_id == "openai_1"


def test_translate_invalid_request_error():
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

    assert error.provider == "openai"


def test_translate_bad_request_error():
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


def test_translate_generic_provider_error():
    provider = create_provider()

    error = provider._translate_error(
        RuntimeError(
            "Unexpected OpenAI failure"
        )
    )

    assert isinstance(
        error,
        LLMProviderError,
    )

    assert error.provider == "openai"
    assert error.key_id == "openai_1"


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
            "insufficient_quota"
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