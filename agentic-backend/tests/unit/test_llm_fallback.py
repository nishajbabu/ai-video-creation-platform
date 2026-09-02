import pytest

from app.llm.exceptions import (
    AllLLMProvidersExhaustedError,
    LLMInvalidRequestError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.llm.key_manager import KeyManager, LLMKey
from app.llm.service import LLMService


def create_test_key(
    provider: str,
    key_id: str,
    priority: int,
) -> LLMKey:
    """
    Create a fake LLM key for testing.

    No real API key is used.
    """

    return LLMKey(
        provider=provider,
        key_id=key_id,
        api_key=f"fake-{key_id}",
        model="test-model",
        priority=priority,
    )


def create_key_manager() -> KeyManager:
    """
    Create a predictable multi-provider test pool.
    """

    return KeyManager(
        [
            create_test_key(
                "openai",
                "openai_1",
                1,
            ),
            create_test_key(
                "openai",
                "openai_2",
                2,
            ),
            create_test_key(
                "gemini",
                "gemini_1",
                3,
            ),
            create_test_key(
                "groq",
                "groq_1",
                4,
            ),
            create_test_key(
                "anthropic",
                "anthropic_1",
                5,
            ),
        ]
    )


def test_key_manager_selects_highest_priority_key():
    """
    The first available key should be the highest-priority key.
    """

    manager = create_key_manager()

    key = manager.get_next_key()

    assert key is not None
    assert key.key_id == "openai_1"


def test_key_manager_falls_back_to_second_key():
    """
    When the first key fails, the next key should be selected.
    """

    manager = create_key_manager()

    first = manager.get_next_key()

    assert first is not None
    assert first.key_id == "openai_1"

    manager.mark_failure(
        "openai_1",
        error="Quota exceeded",
    )

    second = manager.get_next_key()

    assert second is not None
    assert second.key_id == "openai_2"


def test_key_manager_falls_back_to_next_provider():
    """
    When all OpenAI keys are unavailable, the manager should
    move to the next provider.
    """

    manager = create_key_manager()

    manager.mark_failure(
        "openai_1",
        error="Quota exceeded",
    )

    manager.mark_failure(
        "openai_2",
        error="Rate limit",
    )

    key = manager.get_next_key()

    assert key is not None
    assert key.key_id == "gemini_1"
    assert key.provider == "gemini"


def test_key_manager_continues_across_all_providers():
    """
    The manager should continue through the complete provider pool.
    """

    manager = create_key_manager()

    failures = [
        "openai_1",
        "openai_2",
        "gemini_1",
        "groq_1",
    ]

    for key_id in failures:
        manager.mark_failure(
            key_id,
            error="Provider unavailable",
        )

    key = manager.get_next_key()

    assert key is not None
    assert key.key_id == "anthropic_1"
    assert key.provider == "anthropic"


def test_key_manager_returns_none_when_every_key_is_unavailable():
    """
    Once every key is unavailable, no key should be returned.
    """

    manager = create_key_manager()

    for key in manager.get_all_keys():
        manager.mark_failure(
            key.key_id,
            error="Provider unavailable",
        )

    key = manager.get_next_key()

    assert key is None


def test_successful_key_is_restored():
    """
    A key that succeeds should become available again.
    """

    manager = create_key_manager()

    manager.mark_failure(
        "openai_1",
        error="Temporary failure",
    )

    key = manager.get_next_key()

    assert key is not None
    assert key.key_id == "openai_2"

    manager.mark_success("openai_1")

    restored = manager.get_next_key()

    assert restored is not None
    assert restored.key_id == "openai_1"


def test_permanently_disabled_key_is_skipped():
    """
    Permanently disabled keys should not be selected again.
    """

    manager = create_key_manager()

    manager.mark_permanently_disabled(
        "openai_1",
        error="Invalid API key",
    )

    key = manager.get_next_key()

    assert key is not None
    assert key.key_id == "openai_2"


def test_provider_filter_selects_only_requested_provider():
    """
    Supplying a provider filter should restrict selection to that
    provider.
    """

    manager = create_key_manager()

    key = manager.get_next_key(
        provider="gemini",
    )

    assert key is not None
    assert key.provider == "gemini"
    assert key.key_id == "gemini_1"


def test_provider_filter_returns_none_when_provider_is_unavailable():
    """
    If all keys belonging to a requested provider are unavailable,
    the manager should return None rather than another provider.
    """

    manager = create_key_manager()

    manager.mark_failure(
        "gemini_1",
        error="Quota exceeded",
    )

    key = manager.get_next_key(
        provider="gemini",
    )

    assert key is None


def test_service_has_all_provider_adapters():
    """
    The unified LLM service should know about all four providers.
    """

    expected = {
        "openai",
        "gemini",
        "groq",
        "anthropic",
    }

    actual = set(
        LLMService.PROVIDER_CLASSES.keys()
    )

    assert actual == expected


def test_invalid_prompt_does_not_trigger_provider_fallback():
    """
    An empty prompt is a request problem, not a provider problem.

    Therefore the service should reject it immediately.
    """

    manager = create_key_manager()
    service = LLMService(manager)

    with pytest.raises(LLMInvalidRequestError):
        service.generate("")


def test_invalid_structured_prompt_is_rejected():
    """
    Structured generation should reject an empty prompt before
    selecting a provider.
    """

    manager = create_key_manager()
    service = LLMService(manager)

    with pytest.raises(LLMInvalidRequestError):
        service.generate_structured(
            "",
            response_schema={
                "type": "object",
            },
        )


def test_quota_error_is_fallbackable():
    """
    Quota exhaustion should trigger fallback rather than retrying
    the same key indefinitely.
    """

    error = LLMQuotaExceededError(
        "Quota exceeded",
        provider="openai",
        key_id="openai_1",
    )

    assert error.retryable is False
    assert error.fallbackable is True


def test_rate_limit_error_is_retryable_and_fallbackable():
    """
    Rate limits can be retried and can also trigger fallback.
    """

    error = LLMRateLimitError(
        "Rate limited",
        provider="groq",
        key_id="groq_1",
    )

    assert error.retryable is True
    assert error.fallbackable is True


def test_timeout_error_is_retryable_and_fallbackable():
    """
    Temporary timeouts can be retried and can also trigger fallback.
    """

    error = LLMTimeoutError(
        "Request timed out",
        provider="gemini",
        key_id="gemini_1",
    )

    assert error.retryable is True
    assert error.fallbackable is True


def test_all_provider_keys_can_be_exhausted():
    """
    Verify the final exhaustion exception can be raised and caught.
    """

    with pytest.raises(
        AllLLMProvidersExhaustedError
    ):
        raise AllLLMProvidersExhaustedError()