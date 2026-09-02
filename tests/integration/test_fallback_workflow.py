from typing import Any, Dict, Optional

import pytest

from app.llm.base import BaseLLMProvider
from app.llm.exceptions import (
    AllLLMProvidersExhaustedError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.llm.key_manager import KeyManager, LLMKey
from app.llm.service import LLMService


# ---------------------------------------------------------------------------
# Fake provider
# ---------------------------------------------------------------------------


class FakeProvider(BaseLLMProvider):
    """
    Fake LLM provider used to test the real LLMService fallback flow.

    No external API is called.
    """

    def __init__(
        self,
        api_key: str,
        key_id: str,
        model: str,
        *,
        provider_name: str,
        behavior: str = "success",
    ):
        super().__init__(
            api_key=api_key,
            key_id=key_id,
            model=model,
        )

        self.provider_name = provider_name
        self.behavior = behavior

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:

        if self.behavior == "quota":
            raise LLMQuotaExceededError(
                "Simulated quota exceeded.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if self.behavior == "rate_limit":
            raise LLMRateLimitError(
                "Simulated rate limit.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        if self.behavior == "timeout":
            raise LLMTimeoutError(
                "Simulated timeout.",
                provider=self.provider_name,
                key_id=self.key_id,
            )

        return (
            f"SUCCESS from {self.provider_name} "
            f"using {self.key_id}"
        )

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

        return {
            "status": "success",
            "provider": self.provider_name,
            "key_id": self.key_id,
        }


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def make_key(
    provider: str,
    key_id: str,
    priority: int,
) -> LLMKey:
    """
    Create a fake key without using a real API secret.
    """

    return LLMKey(
        provider=provider,
        key_id=key_id,
        api_key=f"fake-{key_id}",
        model="test-model",
        priority=priority,
    )


def make_manager() -> KeyManager:
    """
    Create a predictable provider/key pool.

    Selection order:

        openai_1
        openai_2
        gemini_1
        groq_1
        anthropic_1
    """

    return KeyManager(
        [
            make_key("openai", "openai_1", 1),
            make_key("openai", "openai_2", 2),
            make_key("gemini", "gemini_1", 3),
            make_key("groq", "groq_1", 4),
            make_key("anthropic", "anthropic_1", 5),
        ]
    )


def make_fake_provider(
    key: LLMKey,
    behavior: str,
) -> FakeProvider:
    """
    Build a fake provider using the selected LLMKey.
    """

    return FakeProvider(
        api_key=key.api_key,
        key_id=key.key_id,
        model=key.model,
        provider_name=key.provider,
        behavior=behavior,
    )


# ---------------------------------------------------------------------------
# Existing KeyManager fallback tests
# ---------------------------------------------------------------------------


def test_fallback_moves_to_next_openai_key():
    """
    If OpenAI key 1 fails, OpenAI key 2 should be selected.
    """

    manager = make_manager()

    manager.mark_failure(
        "openai_1",
        error="Simulated quota exceeded.",
    )

    key = manager.get_next_key()

    assert key is not None
    assert key.key_id == "openai_2"
    assert key.provider == "openai"


def test_fallback_moves_from_openai_to_gemini():
    """
    When all OpenAI keys are unavailable, Gemini should be selected.
    """

    manager = make_manager()

    manager.mark_failure(
        "openai_1",
        error="Quota exceeded.",
    )

    manager.mark_failure(
        "openai_2",
        error="Rate limited.",
    )

    key = manager.get_next_key()

    assert key is not None
    assert key.key_id == "gemini_1"
    assert key.provider == "gemini"


def test_fallback_moves_through_multiple_providers():
    """
    Verify the complete provider selection chain.
    """

    manager = make_manager()

    for key_id in [
        "openai_1",
        "openai_2",
        "gemini_1",
        "groq_1",
    ]:
        manager.mark_failure(
            key_id,
            error="Simulated provider failure.",
        )

    key = manager.get_next_key()

    assert key is not None
    assert key.provider == "anthropic"
    assert key.key_id == "anthropic_1"


# ---------------------------------------------------------------------------
# Fake provider behavior tests
# ---------------------------------------------------------------------------


def test_fake_provider_success():

    provider = FakeProvider(
        api_key="fake-key",
        key_id="groq_1",
        model="test-model",
        provider_name="groq",
    )

    result = provider.generate(
        "Create a video plan."
    )

    assert result == (
        "SUCCESS from groq using groq_1"
    )


def test_fake_provider_quota_failure():

    provider = FakeProvider(
        api_key="fake-key",
        key_id="openai_1",
        model="test-model",
        provider_name="openai",
        behavior="quota",
    )

    with pytest.raises(
        LLMQuotaExceededError
    ):
        provider.generate(
            "Create a video plan."
        )


def test_fake_provider_rate_limit_failure():

    provider = FakeProvider(
        api_key="fake-key",
        key_id="gemini_1",
        model="test-model",
        provider_name="gemini",
        behavior="rate_limit",
    )

    with pytest.raises(
        LLMRateLimitError
    ):
        provider.generate(
            "Create a video plan."
        )


def test_fake_provider_timeout_failure():

    provider = FakeProvider(
        api_key="fake-key",
        key_id="groq_1",
        model="test-model",
        provider_name="groq",
        behavior="timeout",
    )

    with pytest.raises(
        LLMTimeoutError
    ):
        provider.generate(
            "Create a video plan."
        )


# ---------------------------------------------------------------------------
# REAL LLMService fallback tests
# ---------------------------------------------------------------------------


def test_llm_service_falls_back_to_next_key(monkeypatch):
    """
    Test the real LLMService fallback mechanism.

    Scenario:

        OpenAI key 1
            ↓
        quota exceeded
            ↓
        OpenAI key 2
            ↓
        success

    No real API call is made.
    """

    manager = make_manager()

    service = LLMService(manager)

    behaviors = {
        "openai_1": "quota",
        "openai_2": "success",
    }

    def fake_create_provider(
        *,
        key: LLMKey,
        model: str,
    ) -> FakeProvider:

        return make_fake_provider(
            key,
            behaviors[key.key_id],
        )

    monkeypatch.setattr(
        service,
        "_create_provider",
        fake_create_provider,
    )

    result = service.generate(
        "Create a professional product video."
    )

    assert result == (
        "SUCCESS from openai using openai_2"
    )

    assert manager.get_key(
        "openai_1"
    ).failure_count == 1

    assert manager.get_key(
        "openai_2"
    ).failure_count == 0


def test_llm_service_falls_back_across_providers(monkeypatch):
    """
    Test complete multi-provider fallback.

    Scenario:

        OpenAI key 1 → quota
             ↓
        OpenAI key 2 → rate limit
             ↓
        Gemini key 1 → timeout
             ↓
        Groq key 1 → success
    """

    manager = make_manager()

    service = LLMService(manager)

    behaviors = {
        "openai_1": "quota",
        "openai_2": "rate_limit",
        "gemini_1": "timeout",
        "groq_1": "success",
        "anthropic_1": "success",
    }

    def fake_create_provider(
        *,
        key: LLMKey,
        model: str,
    ) -> FakeProvider:

        return make_fake_provider(
            key,
            behaviors[key.key_id],
        )

    monkeypatch.setattr(
        service,
        "_create_provider",
        fake_create_provider,
    )

    result = service.generate(
        "Create a professional AI product video."
    )

    assert result == (
        "SUCCESS from groq using groq_1"
    )

    assert manager.get_key(
        "openai_1"
    ).failure_count == 1

    assert manager.get_key(
        "openai_2"
    ).failure_count == 1

    assert manager.get_key(
        "gemini_1"
    ).failure_count == 1

    assert manager.get_key(
        "groq_1"
    ).failure_count == 0


def test_llm_service_exhausts_all_providers(monkeypatch):
    """
    If every configured provider fails, LLMService should raise
    AllLLMProvidersExhaustedError.
    """

    manager = make_manager()

    service = LLMService(manager)

    behaviors = {
        "openai_1": "quota",
        "openai_2": "quota",
        "gemini_1": "timeout",
        "groq_1": "rate_limit",
        "anthropic_1": "timeout",
    }

    def fake_create_provider(
        *,
        key: LLMKey,
        model: str,
    ) -> FakeProvider:

        return make_fake_provider(
            key,
            behaviors[key.key_id],
        )

    monkeypatch.setattr(
        service,
        "_create_provider",
        fake_create_provider,
    )

    with pytest.raises(
        AllLLMProvidersExhaustedError
    ):
        service.generate(
            "Create a professional AI product video."
        )