from app.llm.config import LLMConfig


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def build_environment(**overrides):
    """
    Build a completely isolated environment for configuration tests.

    Only the variables explicitly provided to this helper exist in
    the returned environment.
    """

    environment = {
        "OPENAI_MODEL": "gpt-4o-mini",
        "GEMINI_MODEL": "gemini-2.5-flash",
        "GROQ_MODEL": "llama-3.3-70b-versatile",
        "ANTHROPIC_MODEL": "claude-3-5-haiku-latest",
    }

    environment.update(overrides)

    return environment


# ---------------------------------------------------------------------------
# Basic configuration tests
# ---------------------------------------------------------------------------

def test_config_can_be_created():
    config = LLMConfig(
        environment=build_environment()
    )

    assert config is not None


def test_config_discovers_numbered_api_keys():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="openai-test-key-1",
            OPENAI_API_KEY_2="openai-test-key-2",
        )
    )

    keys = config.get_keys_for_provider(
        "openai"
    )

    assert len(keys) == 2

    assert keys[0].key_id == "openai_1"
    assert keys[1].key_id == "openai_2"

    assert keys[0].api_key == "openai-test-key-1"
    assert keys[1].api_key == "openai-test-key-2"


def test_config_discovers_multiple_providers():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="openai-test-key",
            GEMINI_API_KEY_1="gemini-test-key",
            GROQ_API_KEY_1="groq-test-key",
            ANTHROPIC_API_KEY_1="anthropic-test-key",
        )
    )

    providers = set(
        config.get_provider_names()
    )

    assert providers == {
        "openai",
        "gemini",
        "groq",
        "anthropic",
    }


# ---------------------------------------------------------------------------
# Plain API key tests
# ---------------------------------------------------------------------------

def test_config_supports_plain_api_key():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY="openai-plain-key",
        )
    )

    keys = config.get_keys_for_provider(
        "openai"
    )

    assert len(keys) == 1
    assert keys[0].api_key == "openai-plain-key"
    assert keys[0].key_id == "openai_1"


def test_numbered_key_has_precedence_over_plain_key():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY="plain-key",
            OPENAI_API_KEY_1="numbered-key",
        )
    )

    keys = config.get_keys_for_provider(
        "openai"
    )

    assert len(keys) == 1
    assert keys[0].api_key == "numbered-key"
    assert keys[0].key_id == "openai_1"


# ---------------------------------------------------------------------------
# Provider priority tests
# ---------------------------------------------------------------------------

def test_config_assigns_provider_priority():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="openai-key",
            GEMINI_API_KEY_1="gemini-key",
            GROQ_API_KEY_1="groq-key",
        )
    )

    openai_key = config.get_keys_for_provider(
        "openai"
    )[0]

    gemini_key = config.get_keys_for_provider(
        "gemini"
    )[0]

    groq_key = config.get_keys_for_provider(
        "groq"
    )[0]

    assert openai_key.priority == 101
    assert gemini_key.priority == 201
    assert groq_key.priority == 301


# ---------------------------------------------------------------------------
# Key identity tests
# ---------------------------------------------------------------------------

def test_multiple_keys_have_unique_key_ids():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="key-one",
            OPENAI_API_KEY_2="key-two",
            OPENAI_API_KEY_3="key-three",
        )
    )

    keys = config.get_keys_for_provider(
        "openai"
    )

    key_ids = [
        key.key_id
        for key in keys
    ]

    assert key_ids == [
        "openai_1",
        "openai_2",
        "openai_3",
    ]

    assert len(key_ids) == len(
        set(key_ids)
    )


# ---------------------------------------------------------------------------
# Empty key tests
# ---------------------------------------------------------------------------

def test_config_ignores_empty_keys():
    """
    Empty numbered keys must not create LLMKey objects.

    This test uses an isolated environment so that real API keys
    configured on the developer machine cannot interfere with it.
    """

    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="",
            OPENAI_API_KEY_2="valid-key",
        )
    )

    keys = config.get_keys_for_provider(
        "openai"
    )

    assert len(keys) == 1
    assert keys[0].key_id == "openai_2"
    assert keys[0].api_key == "valid-key"


def test_config_strips_key_whitespace():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="   test-key   ",
        )
    )

    keys = config.get_keys_for_provider(
        "openai"
    )

    assert len(keys) == 1
    assert keys[0].api_key == "test-key"


# ---------------------------------------------------------------------------
# Model configuration tests
# ---------------------------------------------------------------------------

def test_config_uses_default_models():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="openai-key",
            GEMINI_API_KEY_1="gemini-key",
        )
    )

    openai_key = config.get_keys_for_provider(
        "openai"
    )[0]

    gemini_key = config.get_keys_for_provider(
        "gemini"
    )[0]

    assert openai_key.model == "gpt-4o-mini"
    assert gemini_key.model == "gemini-2.5-flash"


def test_config_supports_custom_models():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="openai-key",
            OPENAI_MODEL="custom-openai-model",
            GEMINI_API_KEY_1="gemini-key",
            GEMINI_MODEL="custom-gemini-model",
        )
    )

    openai_key = config.get_keys_for_provider(
        "openai"
    )[0]

    gemini_key = config.get_keys_for_provider(
        "gemini"
    )[0]

    assert openai_key.model == (
        "custom-openai-model"
    )

    assert gemini_key.model == (
        "custom-gemini-model"
    )


# ---------------------------------------------------------------------------
# Collection safety tests
# ---------------------------------------------------------------------------

def test_get_keys_returns_copy():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="openai-key",
        )
    )

    first = config.get_keys()
    second = config.get_keys()

    assert first is not second
    assert first == second


def test_get_keys_for_provider_returns_filtered_keys():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="openai-key",
            GEMINI_API_KEY_1="gemini-key",
            GROQ_API_KEY_1="groq-key",
        )
    )

    openai_keys = config.get_keys_for_provider(
        "openai"
    )

    assert len(openai_keys) == 1
    assert openai_keys[0].provider == "openai"


def test_provider_lookup_is_case_insensitive():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="openai-key",
        )
    )

    lowercase = config.get_keys_for_provider(
        "openai"
    )

    uppercase = config.get_keys_for_provider(
        "OPENAI"
    )

    mixed_case = config.get_keys_for_provider(
        "OpenAI"
    )

    assert len(lowercase) == 1
    assert len(uppercase) == 1
    assert len(mixed_case) == 1

    assert lowercase[0].key_id == "openai_1"
    assert uppercase[0].key_id == "openai_1"
    assert mixed_case[0].key_id == "openai_1"


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

def test_validate_succeeds_when_keys_exist():
    config = LLMConfig(
        environment=build_environment(
            OPENAI_API_KEY_1="openai-key",
        )
    )

    config.validate()


def test_validate_fails_when_no_keys_exist():
    config = LLMConfig(
        environment=build_environment()
    )

    try:
        config.validate()
        assert False, (
            "Expected validate() to raise RuntimeError"
        )
    except RuntimeError as exc:
        assert "No LLM API keys are configured" in str(exc)