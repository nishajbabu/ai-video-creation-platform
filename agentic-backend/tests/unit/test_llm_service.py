import pytest

from app.llm.exceptions import (
    AllLLMProvidersExhaustedError,
    LLMInvalidRequestError,
    LLMQuotaExceededError,
)
from app.llm.key_manager import KeyManager, LLMKey
from app.llm.service import LLMService


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def make_key(
    provider: str,
    key_id: str,
    priority: int,
) -> LLMKey:
    """
    Create a fake key for unit testing.
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
    Create a small deterministic LLM key pool.
    """

    return KeyManager(
        [
            make_key("openai", "openai_1", 1),
            make_key("gemini", "gemini_1", 2),
            make_key("groq", "groq_1", 3),
            make_key("anthropic", "anthropic_1", 4),
        ]
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_service_can_be_created():
    manager = make_manager()

    service = LLMService(manager)

    assert service is not None
    assert isinstance(service, LLMService)


def test_service_exposes_all_supported_providers():
    manager = make_manager()

    service = LLMService(manager)

    providers = set(
        service.PROVIDER_CLASSES.keys()
    )

    assert providers == {
        "openai",
        "gemini",
        "groq",
        "anthropic",
    }


def test_service_returns_configured_providers():
    manager = make_manager()

    service = LLMService(manager)

    providers = service.get_available_providers()

    assert providers == [
        "anthropic",
        "gemini",
        "groq",
        "openai",
    ]


# ---------------------------------------------------------------------------
# Provider creation
# ---------------------------------------------------------------------------

def test_service_can_create_openai_adapter(monkeypatch):
    manager = make_manager()

    service = LLMService(manager)

    created = {}

    class FakeAdapter:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            created["api_key"] = api_key
            created["key_id"] = key_id
            created["model"] = model
            created["kwargs"] = kwargs

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "openai",
        FakeAdapter,
    )

    key = manager.get_key(
        "openai_1"
    )

    adapter = service._create_provider(
        key=key,
        model="test-model",
    )

    assert isinstance(
        adapter,
        FakeAdapter,
    )

    assert created["api_key"] == (
        "fake-openai_1"
    )

    assert created["key_id"] == (
        "openai_1"
    )

    assert created["model"] == (
        "test-model"
    )

    assert created["kwargs"]["timeout"] == 60.0


def test_service_can_create_gemini_adapter(monkeypatch):
    manager = make_manager()

    service = LLMService(manager)

    class FakeAdapter:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            self.key_id = key_id
            self.model = model

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "gemini",
        FakeAdapter,
    )

    key = manager.get_key(
        "gemini_1"
    )

    adapter = service._create_provider(
        key=key,
        model="test-model",
    )

    assert adapter.key_id == "gemini_1"
    assert adapter.model == "test-model"


def test_service_can_create_groq_adapter(monkeypatch):
    manager = make_manager()

    service = LLMService(manager)

    class FakeAdapter:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            self.key_id = key_id

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "groq",
        FakeAdapter,
    )

    key = manager.get_key(
        "groq_1"
    )

    adapter = service._create_provider(
        key=key,
        model="test-model",
    )

    assert adapter.key_id == "groq_1"


def test_service_can_create_anthropic_adapter(monkeypatch):
    manager = make_manager()

    service = LLMService(manager)

    class FakeAdapter:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            self.key_id = key_id

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "anthropic",
        FakeAdapter,
    )

    key = manager.get_key(
        "anthropic_1"
    )

    adapter = service._create_provider(
        key=key,
        model="test-model",
    )

    assert adapter.key_id == "anthropic_1"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_service_rejects_empty_prompt():
    manager = make_manager()

    service = LLMService(manager)

    with pytest.raises(
        LLMInvalidRequestError
    ):
        service.generate("")


def test_service_rejects_whitespace_prompt():
    manager = make_manager()

    service = LLMService(manager)

    with pytest.raises(
        LLMInvalidRequestError
    ):
        service.generate("   ")


def test_structured_generation_rejects_empty_prompt():
    manager = make_manager()

    service = LLMService(manager)

    with pytest.raises(
        LLMInvalidRequestError
    ):
        service.generate_structured(
            "",
            response_schema={
                "type": "object"
            },
        )


def test_structured_generation_rejects_empty_schema():
    manager = make_manager()

    service = LLMService(manager)

    with pytest.raises(
        LLMInvalidRequestError
    ):
        service.generate_structured(
            "Create a video plan.",
            response_schema={},
        )


# ---------------------------------------------------------------------------
# Key status
# ---------------------------------------------------------------------------

def test_service_reports_key_status():
    manager = make_manager()

    service = LLMService(manager)

    status = service.get_key_status(
        "openai_1"
    )

    assert status["key_id"] == "openai_1"
    assert status["provider"] == "openai"
    assert status["model"] == "test-model"
    assert status["enabled"] is True
    assert status["failure_count"] == 0


def test_service_reports_failed_key_status():
    manager = make_manager()

    service = LLMService(manager)

    manager.mark_failure(
        "openai_1",
        error="Simulated quota failure.",
    )

    status = service.get_key_status(
        "openai_1"
    )

    assert status["key_id"] == "openai_1"
    assert status["failure_count"] == 1
    assert status["last_error"] == (
        "Simulated quota failure."
    )
    assert status["available"] is False


def test_service_reports_successful_key_status():
    manager = make_manager()

    service = LLMService(manager)

    manager.mark_failure(
        "openai_1",
        error="Temporary failure.",
    )

    manager.mark_success(
        "openai_1"
    )

    status = service.get_key_status(
        "openai_1"
    )

    assert status["failure_count"] == 0
    assert status["last_error"] is None
    assert status["available"] is True


# ---------------------------------------------------------------------------
# Provider response
# ---------------------------------------------------------------------------

def test_service_generate_returns_provider_response(
    monkeypatch,
):
    manager = make_manager()

    service = LLMService(manager)

    received = {}

    class FakeAdapter:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            received["api_key"] = api_key
            received["key_id"] = key_id
            received["model"] = model
            received["init_kwargs"] = kwargs

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            received["prompt"] = prompt
            received["kwargs"] = kwargs

            return "Generated video description."

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "openai",
        FakeAdapter,
    )

    result = service.generate(
        "Create a product video."
    )

    assert result == (
        "Generated video description."
    )

    assert received["prompt"] == (
        "Create a product video."
    )

    assert received["key_id"] == (
        "openai_1"
    )


def test_service_generate_passes_generation_options(
    monkeypatch,
):
    manager = make_manager()

    service = LLMService(manager)

    received = {}

    class FakeAdapter:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            received["prompt"] = prompt
            received["kwargs"] = kwargs

            return "Generated response."

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "openai",
        FakeAdapter,
    )

    result = service.generate(
        "Create a video.",
        system_prompt="You are a video expert.",
        temperature=0.7,
        max_tokens=500,
    )

    assert result == (
        "Generated response."
    )

    assert received["prompt"] == (
        "Create a video."
    )

    assert (
        received["kwargs"]["system_prompt"]
        == "You are a video expert."
    )

    assert (
        received["kwargs"]["temperature"]
        == 0.7
    )

    assert (
        received["kwargs"]["max_tokens"]
        == 500
    )


def test_service_generate_structured_returns_provider_response(
    monkeypatch,
):
    manager = make_manager()

    service = LLMService(manager)

    class FakeAdapter:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate_structured(
            self,
            prompt,
            **kwargs,
        ):
            assert prompt == (
                "Create a structured video plan."
            )

            assert (
                kwargs["response_schema"]
                == {
                    "type": "object",
                }
            )

            return {
                "status": "ok",
                "scene_count": 5,
            }

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "openai",
        FakeAdapter,
    )

    result = service.generate_structured(
        "Create a structured video plan.",
        response_schema={
            "type": "object",
        },
    )

    assert result == {
        "status": "ok",
        "scene_count": 5,
    }


# ---------------------------------------------------------------------------
# Successful execution
# ---------------------------------------------------------------------------

def test_successful_generation_marks_key_success():
    manager = make_manager()

    service = LLMService(manager)

    key = manager.get_key(
        "openai_1"
    )

    manager.mark_failure(
        "openai_1",
        error="Previous failure.",
    )

    result = service._execute_with_retry(
        lambda: "Success.",
        key=key,
    )

    assert result == "Success."

    status = manager.get_key_status(
        "openai_1"
    )

    assert status["failure_count"] == 0
    assert status["last_error"] is None
    assert status["available"] is True


# ---------------------------------------------------------------------------
# Provider fallback
# ---------------------------------------------------------------------------

def test_service_falls_back_to_next_provider(
    monkeypatch,
):
    manager = make_manager()

    service = LLMService(manager)

    calls = []

    class FakeOpenAI:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            calls.append("openai")

            raise LLMQuotaExceededError(
                "Quota exceeded.",
                provider="openai",
                key_id="openai_1",
            )

    class FakeGemini:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            calls.append("gemini")

            return (
                "Gemini fallback response."
            )

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "openai",
        FakeOpenAI,
    )

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "gemini",
        FakeGemini,
    )

    result = service.generate(
        "Create a video."
    )

    assert result == (
        "Gemini fallback response."
    )

    assert calls == [
        "openai",
        "gemini",
    ]


def test_service_records_failure_before_fallback(
    monkeypatch,
):
    manager = make_manager()

    service = LLMService(manager)

    class FakeOpenAI:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            raise LLMQuotaExceededError(
                "Quota exceeded.",
                provider="openai",
                key_id="openai_1",
            )

    class FakeGemini:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            return "Fallback success."

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "openai",
        FakeOpenAI,
    )

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "gemini",
        FakeGemini,
    )

    result = service.generate(
        "Create a video."
    )

    assert result == (
        "Fallback success."
    )

    status = manager.get_key_status(
        "openai_1"
    )

    assert status["failure_count"] == 1

    assert (
        status["last_error"]
        == "[provider=openai, key=openai_1] Quota exceeded."
    )

    assert status["available"] is False


def test_provider_argument_falls_back_to_other_provider(
    monkeypatch,
):
    manager = make_manager()

    service = LLMService(manager)

    calls = []

    class FakeOpenAI:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            calls.append("openai")

            raise LLMQuotaExceededError(
                "OpenAI quota exceeded.",
                provider="openai",
                key_id="openai_1",
            )

    class FakeGemini:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            calls.append("gemini")

            return "Gemini fallback."

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "openai",
        FakeOpenAI,
    )

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "gemini",
        FakeGemini,
    )

    result = service.generate(
        "Create a video.",
        provider="openai",
    )

    assert result == (
        "Gemini fallback."
    )

    assert calls == [
        "openai",
        "gemini",
    ]


# ---------------------------------------------------------------------------
# Non-fallbackable errors
# ---------------------------------------------------------------------------

def test_non_fallbackable_error_is_reraised(
    monkeypatch,
):
    manager = make_manager()

    service = LLMService(manager)

    class FakeAdapter:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            raise LLMInvalidRequestError(
                "Invalid request."
            )

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "openai",
        FakeAdapter,
    )

    with pytest.raises(
        LLMInvalidRequestError,
        match="Invalid request.",
    ):
        service.generate(
            "Create a video."
        )


def test_non_fallbackable_error_does_not_disable_key(
    monkeypatch,
):
    manager = make_manager()

    service = LLMService(manager)

    class FakeAdapter:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            raise LLMInvalidRequestError(
                "Invalid request."
            )

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "openai",
        FakeAdapter,
    )

    with pytest.raises(
        LLMInvalidRequestError
    ):
        service.generate(
            "Create a video."
        )

    status = manager.get_key_status(
        "openai_1"
    )

    assert status["failure_count"] == 0
    assert status["available"] is True


# ---------------------------------------------------------------------------
# All providers exhausted
# ---------------------------------------------------------------------------

def test_service_raises_when_all_providers_fail(
    monkeypatch,
):
    manager = make_manager()

    service = LLMService(manager)

    class FakeAdapter:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate(
            self,
            prompt,
            **kwargs,
        ):
            raise LLMQuotaExceededError(
                "Quota exceeded."
            )

    for provider_name in (
        service.PROVIDER_CLASSES
    ):
        monkeypatch.setitem(
            service.PROVIDER_CLASSES,
            provider_name,
            FakeAdapter,
        )

    with pytest.raises(
        AllLLMProvidersExhaustedError,
        match=(
            "All available LLM providers "
            "and API keys failed"
        ),
    ):
        service.generate(
            "Create a video."
        )


# ---------------------------------------------------------------------------
# Structured fallback
# ---------------------------------------------------------------------------

def test_structured_generation_falls_back(
    monkeypatch,
):
    manager = make_manager()

    service = LLMService(manager)

    calls = []

    class FakeOpenAI:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate_structured(
            self,
            prompt,
            **kwargs,
        ):
            calls.append("openai")

            raise LLMQuotaExceededError(
                "Quota exceeded.",
                provider="openai",
                key_id="openai_1",
            )

    class FakeGemini:
        def __init__(
            self,
            api_key,
            key_id,
            model,
            **kwargs,
        ):
            pass

        def generate_structured(
            self,
            prompt,
            **kwargs,
        ):
            calls.append("gemini")

            return {
                "status": "success",
            }

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "openai",
        FakeOpenAI,
    )

    monkeypatch.setitem(
        service.PROVIDER_CLASSES,
        "gemini",
        FakeGemini,
    )

    result = service.generate_structured(
        "Create a plan.",
        response_schema={
            "type": "object",
        },
    )

    assert result == {
        "status": "success",
    }

    assert calls == [
        "openai",
        "gemini",
    ]


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

def test_service_provider_registry_is_independent_per_instance():
    manager_one = make_manager()
    manager_two = make_manager()

    service_one = LLMService(
        manager_one
    )

    service_two = LLMService(
        manager_two
    )

    assert (
        service_one.PROVIDER_CLASSES
        is service_two.PROVIDER_CLASSES
    )