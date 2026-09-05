from app.core.dependencies import (
    clear_dependency_cache,
    get_llm_config,
    get_llm_key_manager,
    get_llm_service,
)
from app.llm.config import LLMConfig
from app.llm.key_manager import KeyManager
from app.llm.service import LLMService


# ---------------------------------------------------------------------------
# Configuration dependency
# ---------------------------------------------------------------------------

def test_get_llm_config_returns_config():
    clear_dependency_cache()

    config = get_llm_config()

    assert isinstance(config, LLMConfig)


def test_get_llm_config_returns_cached_instance():
    clear_dependency_cache()

    first = get_llm_config()
    second = get_llm_config()

    assert first is second


# ---------------------------------------------------------------------------
# Key manager dependency
# ---------------------------------------------------------------------------

def test_get_llm_key_manager_returns_key_manager():
    clear_dependency_cache()

    manager = get_llm_key_manager()

    assert isinstance(manager, KeyManager)


def test_get_llm_key_manager_returns_cached_instance():
    clear_dependency_cache()

    first = get_llm_key_manager()
    second = get_llm_key_manager()

    assert first is second


def test_key_manager_contains_configured_keys():
    clear_dependency_cache()

    config = get_llm_config()
    manager = get_llm_key_manager()

    assert len(manager.get_all_keys()) == len(
        config.get_keys()
    )


# ---------------------------------------------------------------------------
# LLM service dependency
# ---------------------------------------------------------------------------

def test_get_llm_service_returns_service():
    clear_dependency_cache()

    service = get_llm_service()

    assert isinstance(service, LLMService)


def test_get_llm_service_returns_cached_instance():
    clear_dependency_cache()

    first = get_llm_service()
    second = get_llm_service()

    assert first is second


def test_llm_service_uses_shared_key_manager():
    clear_dependency_cache()

    manager = get_llm_key_manager()
    service = get_llm_service()

    assert service.key_manager is manager


# ---------------------------------------------------------------------------
# Dependency relationship
# ---------------------------------------------------------------------------

def test_dependency_chain_is_consistent():
    clear_dependency_cache()

    config = get_llm_config()
    manager = get_llm_key_manager()
    service = get_llm_service()

    assert isinstance(config, LLMConfig)
    assert isinstance(manager, KeyManager)
    assert isinstance(service, LLMService)

    assert len(config.get_keys()) == len(
        manager.get_all_keys()
    )

    assert service.key_manager is manager


# ---------------------------------------------------------------------------
# Cache reset
# ---------------------------------------------------------------------------

def test_clear_dependency_cache_creates_new_instances():
    clear_dependency_cache()

    first_config = get_llm_config()
    first_manager = get_llm_key_manager()
    first_service = get_llm_service()

    clear_dependency_cache()

    second_config = get_llm_config()
    second_manager = get_llm_key_manager()
    second_service = get_llm_service()

    assert first_config is not second_config
    assert first_manager is not second_manager
    assert first_service is not second_service


def test_clear_dependency_cache_rebuilds_dependency_chain():
    clear_dependency_cache()

    first_manager = get_llm_key_manager()
    first_service = get_llm_service()

    clear_dependency_cache()

    second_manager = get_llm_key_manager()
    second_service = get_llm_service()

    assert first_manager is not second_manager
    assert first_service is not second_service

    assert second_service.key_manager is second_manager