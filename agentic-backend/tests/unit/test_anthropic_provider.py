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
from app.llm.providers.anthropic_provider import AnthropicProvider


# ---------------------------------------------------------------------------
# Fake Anthropic SDK objects
# ---------------------------------------------------------------------------


class FakeContentBlock:
    """
    Minimal fake Anthropic content block.
    """

    def __init__(self, text):
        self.text = text


class FakeResponse:
    """
    Minimal fake Anthropic Messages API response.
    """

    def __init__(self, content):
        self.content = content


class FakeMessages:
    """
    Fake Anthropic messages API.
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


class FakeClient:
    """
    Fake Anthropic client.
    """

    def __init__(
        self,
        response=None,
        error=None,
    ):
        self.messages = FakeMessages(
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
    Create an AnthropicProvider with a fake Anthropic client.
    """

    provider = AnthropicProvider(
        api_key="test-anthropic-key",
        key_id="anthropic_1",
        model="test-anthropic-model",
        timeout=timeout,
    )

    provider.client = FakeClient(
        response=response,
        error=error,
    )

    return provider


def create_text_response(
    *texts,
):
    """
    Create a fake Anthropic response containing text blocks.
    """

    return FakeResponse(
        [
            FakeContentBlock(text)
            for text in texts
        ]
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_anthropic_provider_initializes():
    provider = create_provider()

    assert provider.provider_name == "anthropic"
    assert provider.api_key == "test-anthropic-key"
    assert provider.key_id == "anthropic_1"
    assert provider.model == "test-anthropic-model"


def test_anthropic_provider_health_check_returns_true():
    provider = create_provider()

    assert provider.health_check() is True


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def test_extract_text_returns_single_text_block():
    response = create_text_response(
        "Hello from Anthropic."
    )

    result = AnthropicProvider._extract_text(
        response
    )

    assert result == "Hello from Anthropic."


def test_extract_text_combines_multiple_text_blocks():
    response = create_text_response(
        "Hello ",
        "from ",
        "Anthropic.",
    )

    result = AnthropicProvider._extract_text(
        response
    )

    assert result == "Hello from Anthropic."


def test_extract_text_ignores_empty_text_blocks():
    response = FakeResponse(
        [
            FakeContentBlock("Hello"),
            FakeContentBlock(""),
            FakeContentBlock(None),
            FakeContentBlock(" World"),
        ]
    )

    result = AnthropicProvider._extract_text(
        response
    )

    assert result == "Hello World"


def test_extract_text_returns_empty_string_for_missing_content():
    response = FakeResponse(
        None
    )

    result = AnthropicProvider._extract_text(
        response
    )

    assert result == ""


def test_extract_text_returns_empty_string_for_empty_content():
    response = FakeResponse(
        []
    )

    result = AnthropicProvider._extract_text(
        response
    )

    assert result == ""


def test_extract_text_ignores_non_text_blocks():
    class NonTextBlock:
        pass

    response = FakeResponse(
        [
            NonTextBlock(),
            FakeContentBlock("Hello"),
        ]
    )

    result = AnthropicProvider._extract_text(
        response
    )

    assert result == "Hello"


# ---------------------------------------------------------------------------
# Normal text generation
# ---------------------------------------------------------------------------


def test_generate_returns_response_text():
    provider = create_provider(
        response=create_text_response(
            "Hello from Anthropic."
        )
    )

    result = provider.generate(
        "Say hello."
    )

    assert result == "Hello from Anthropic."


def test_generate_strips_response_text():
    provider = create_provider(
        response=create_text_response(
            "  Hello from Anthropic.  "
        )
    )

    result = provider.generate(
        "Say hello."
    )

    assert result == "Hello from Anthropic."


def test_generate_passes_model():
    provider = create_provider(
        response=create_text_response(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video."
    )

    call = (
        provider.client
        .messages
        .calls[0]
    )

    assert call["model"] == "test-anthropic-model"


def test_generate_passes_user_prompt():
    provider = create_provider(
        response=create_text_response(
            "Generated response."
        )
    )

    provider.generate(
        "Create a product video."
    )

    call = (
        provider.client
        .messages
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
        response=create_text_response(
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
        .messages
        .calls[0]
    )

    assert call["system"] == (
        "You are a professional video writer."
    )


def test_generate_uses_default_max_tokens():
    provider = create_provider(
        response=create_text_response(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video."
    )

    call = (
        provider.client
        .messages
        .calls[0]
    )

    assert call["max_tokens"] == 4096


def test_generate_passes_max_tokens():
    provider = create_provider(
        response=create_text_response(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        max_tokens=500,
    )

    call = (
        provider.client
        .messages
        .calls[0]
    )

    assert call["max_tokens"] == 500


def test_generate_uses_default_max_tokens_when_zero():
    provider = create_provider(
        response=create_text_response(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        max_tokens=0,
    )

    call = (
        provider.client
        .messages
        .calls[0]
    )

    assert call["max_tokens"] == 4096


def test_generate_passes_temperature():
    provider = create_provider(
        response=create_text_response(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        temperature=0.7,
    )

    call = (
        provider.client
        .messages
        .calls[0]
    )

    assert call["temperature"] == 0.7


def test_generate_omits_temperature_when_none():
    provider = create_provider(
        response=create_text_response(
            "Generated response."
        )
    )

    provider.generate(
        "Create a video.",
        temperature=None,
    )

    call = (
        provider.client
        .messages
        .calls[0]
    )

    assert "temperature" not in call


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
        response=FakeResponse([])
    )

    with pytest.raises(
        LLMResponseError,
        match="Anthropic returned an empty response.",
    ):
        provider.generate(
            "Generate something."
        )


def test_generate_rejects_response_without_content():
    provider = create_provider(
        response=FakeResponse(None)
    )

    with pytest.raises(
        LLMResponseError,
        match="Anthropic returned an empty response.",
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
        response=create_text_response(
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
        response=create_text_response(
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
        .messages
        .calls[0]
    )

    assert call["model"] == "test-anthropic-model"


def test_generate_structured_passes_user_prompt():
    provider = create_provider(
        response=create_text_response(
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
        .messages
        .calls[0]
    )

    assert call["messages"] == [
        {
            "role": "user",
            "content": "Create structured output.",
        }
    ]


def test_generate_structured_includes_json_instruction():
    provider = create_provider(
        response=create_text_response(
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
        .messages
        .calls[0]
    )

    system_prompt = call["system"]

    assert "Return ONLY valid JSON." in system_prompt
    assert "Do not include markdown fences" in system_prompt
    assert json.dumps(
        schema,
        indent=2,
    ) in system_prompt


def test_generate_structured_combines_system_prompt():
    provider = create_provider(
        response=create_text_response(
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
        .messages
        .calls[0]
    )

    system_prompt = call["system"]

    assert (
        "You are a video planning assistant."
        in system_prompt
    )

    assert (
        "Return ONLY valid JSON."
        in system_prompt
    )


def test_generate_structured_uses_default_max_tokens():
    provider = create_provider(
        response=create_text_response(
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
        .messages
        .calls[0]
    )

    assert call["max_tokens"] == 4096


def test_generate_structured_passes_max_tokens():
    provider = create_provider(
        response=create_text_response(
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
        .messages
        .calls[0]
    )

    assert call["max_tokens"] == 500


def test_generate_structured_uses_default_max_tokens_when_zero():
    provider = create_provider(
        response=create_text_response(
            '{"status": "ok"}'
        )
    )

    provider.generate_structured(
        "Create structured output.",
        response_schema={
            "type": "object",
        },
        max_tokens=0,
    )

    call = (
        provider.client
        .messages
        .calls[0]
    )

    assert call["max_tokens"] == 4096


def test_generate_structured_passes_temperature():
    provider = create_provider(
        response=create_text_response(
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
        .messages
        .calls[0]
    )

    assert call["temperature"] == 0.4


def test_generate_structured_omits_temperature_when_none():
    provider = create_provider(
        response=create_text_response(
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
        .messages
        .calls[0]
    )

    assert "temperature" not in call


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
        response=FakeResponse([])
    )

    with pytest.raises(
        LLMResponseError,
        match="Anthropic returned an empty structured response.",
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


def test_parse_json_response_accepts_whitespace():
    provider = create_provider()

    result = provider._parse_json_response(
        '  {"name": "video"}  '
    )

    assert result == {
        "name": "video",
    }


def test_parse_json_response_removes_markdown_fences():
    provider = create_provider()

    result = provider._parse_json_response(
        """```json
{"name": "video"}
```"""
    )

    assert result == {
        "name": "video",
    }


def test_parse_json_response_removes_plain_markdown_fences():
    provider = create_provider()

    result = provider._parse_json_response(
        """```
{"name": "video"}
```"""
    )

    assert result == {
        "name": "video",
    }


def test_parse_json_response_removes_json_prefix():
    provider = create_provider()

    result = provider._parse_json_response(
        """json
{"name": "video"}"""
    )

    assert result == {
        "name": "video",
    }


def test_parse_json_response_handles_json_prefix_case_insensitively():
    provider = create_provider()

    result = provider._parse_json_response(
        """JSON
{"name": "video"}"""
    )

    assert result == {
        "name": "video",
    }


def test_parse_json_response_rejects_invalid_json():
    provider = create_provider()

    with pytest.raises(
        LLMResponseError,
        match="Anthropic returned invalid JSON.",
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
            "Anthropic structured response must "
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

    assert error.provider == "anthropic"
    assert error.key_id == "anthropic_1"


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


def test_translate_authentication_class_error():
    class AuthenticationError(Exception):
        pass

    provider = create_provider()

    error = provider._translate_error(
        AuthenticationError(
            "Authentication failed"
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

    assert error.provider == "anthropic"
    assert error.key_id == "anthropic_1"


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

    assert error.provider == "anthropic"
    assert error.key_id == "anthropic_1"


def test_translate_usage_limit_error():
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

    assert error.provider == "anthropic"
    assert error.key_id == "anthropic_1"


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
            "Unexpected Anthropic failure"
        )
    )

    assert isinstance(
        error,
        LLMProviderError,
    )

    assert error.provider == "anthropic"
    assert error.key_id == "anthropic_1"


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