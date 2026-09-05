"""
Application dependency providers.

This module creates and exposes shared application services.

The dependency flow is:

    Environment
        ↓
    LLMConfig
        ↓
    KeyManager
        ↓
    LLMService

The rest of the application should depend on LLMService rather than
constructing provider clients or API-key managers directly.
"""

from functools import lru_cache

from app.core.startup import initialize_llm_environment
from app.llm.config import LLMConfig
from app.llm.key_manager import KeyManager
from app.llm.service import LLMService


# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_llm_config() -> LLMConfig:
    """
    Create the application's shared LLM configuration.

    The environment is initialized before the configuration is built.

    Returns:
        LLMConfig instance.
    """

    initialize_llm_environment()

    return LLMConfig()


# ---------------------------------------------------------------------------
# LLM key manager
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_llm_key_manager() -> KeyManager:
    """
    Create the application's shared LLM key manager.

    The KeyManager receives all API-key configurations discovered
    by LLMConfig.

    Returns:
        KeyManager instance.
    """

    config = get_llm_config()

    return KeyManager(
        config.get_keys(),
    )


# ---------------------------------------------------------------------------
# LLM service
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    """
    Create the application's shared LLM service.

    LLMService is responsible for:

        - provider selection
        - provider adapter creation
        - retries
        - fallback
        - structured generation
        - error handling

    Returns:
        LLMService instance.
    """

    key_manager = get_llm_key_manager()

    return LLMService(
        key_manager,
    )


# ---------------------------------------------------------------------------
# Dependency cache management
# ---------------------------------------------------------------------------

def clear_dependency_cache() -> None:
    """
    Clear all cached application dependencies.

    This is primarily useful for:

        - automated tests
        - configuration reloads
        - controlled application reinitialization

    The order matters because LLMService depends on KeyManager,
    and KeyManager depends on LLMConfig.
    """

    get_llm_service.cache_clear()
    get_llm_key_manager.cache_clear()
    get_llm_config.cache_clear()