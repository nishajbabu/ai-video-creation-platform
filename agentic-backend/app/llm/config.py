import os
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional

from app.llm.key_manager import LLMKey


@dataclass(frozen=True)
class ProviderConfig:
    """
    Configuration for one LLM provider.
    """

    name: str
    default_model: str
    priority: int


class LLMConfig:
    """
    Loads LLM provider configuration and API keys from
    environment variables.

    Multiple API keys are supported for every provider.

    Supported providers:
        - OpenAI
        - Gemini
        - Groq
        - Anthropic

    The environment can optionally be supplied explicitly.
    This makes the configuration deterministic and easy to test.

    In normal application usage:

        config = LLMConfig()

    In tests:

        config = LLMConfig(environment={
            "OPENAI_API_KEY_1": "",
            "OPENAI_API_KEY_2": "test-key",
        })
    """

    KEY_ENV_PREFIXES = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }

    def __init__(
        self,
        environment: Optional[Mapping[str, str]] = None,
    ):
        """
        Build provider configuration and discover API keys.

        Args:
            environment:
                Optional environment mapping.

                When supplied, only that mapping is used.
                This is particularly useful for tests.

                When omitted, the current process environment
                (`os.environ`) is used.
        """

        self._environment = (
            dict(environment)
            if environment is not None
            else os.environ
        )

        self.providers = self._build_provider_configs()
        self._keys = self._load_keys()

    # ------------------------------------------------------------------
    # Environment helpers
    # ------------------------------------------------------------------

    def _getenv(
        self,
        name: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """
        Read one environment value.

        An explicitly empty environment variable remains empty.
        """

        value = self._environment.get(name)

        if value is None:
            return default

        return value

    # ------------------------------------------------------------------
    # Provider configuration
    # ------------------------------------------------------------------

    def _build_provider_configs(
        self,
    ) -> Dict[str, ProviderConfig]:
        """
        Build configuration for every supported provider.

        Model names can be overridden through environment variables.
        """

        return {
            "openai": ProviderConfig(
                name="openai",
                default_model=self._getenv(
                    "OPENAI_MODEL",
                    "gpt-4o-mini",
                ),
                priority=1,
            ),
            "gemini": ProviderConfig(
                name="gemini",
                default_model=self._getenv(
                    "GEMINI_MODEL",
                    "gemini-2.5-flash",
                ),
                priority=2,
            ),
            "groq": ProviderConfig(
                name="groq",
                default_model=self._getenv(
                    "GROQ_MODEL",
                    "llama-3.3-70b-versatile",
                ),
                priority=3,
            ),
            "anthropic": ProviderConfig(
                name="anthropic",
                default_model=self._getenv(
                    "ANTHROPIC_MODEL",
                    "claude-3-5-haiku-latest",
                ),
                priority=4,
            ),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_keys(self) -> List[LLMKey]:
        """
        Return all configured LLM keys.

        A new list is returned so callers cannot directly modify
        the internal key collection.
        """

        return list(self._keys)

    def get_provider_names(self) -> List[str]:
        """
        Return providers that have at least one configured key.

        Provider names are returned alphabetically.
        """

        return sorted(
            {
                key.provider
                for key in self._keys
            }
        )

    def get_keys_for_provider(
        self,
        provider: str,
    ) -> List[LLMKey]:
        """
        Return all configured keys belonging to a provider.
        """

        provider = provider.lower().strip()

        return [
            key
            for key in self._keys
            if key.provider == provider
        ]

    # ------------------------------------------------------------------
    # Key discovery
    # ------------------------------------------------------------------

    def _load_keys(self) -> List[LLMKey]:
        """
        Discover all configured API keys across all providers.
        """

        keys: List[LLMKey] = []

        for (
            provider_name,
            provider_config,
        ) in self.providers.items():

            prefix = self.KEY_ENV_PREFIXES[
                provider_name
            ]

            provider_keys = self._load_provider_keys(
                provider_name=provider_name,
                prefix=prefix,
                default_model=provider_config.default_model,
                provider_priority=provider_config.priority,
            )

            keys.extend(provider_keys)

        return keys

    def _load_provider_keys(
        self,
        *,
        provider_name: str,
        prefix: str,
        default_model: str,
        provider_priority: int,
    ) -> List[LLMKey]:
        """
        Discover all API keys for one provider.

        Supported formats:

            OPENAI_API_KEY
            OPENAI_API_KEY_1
            OPENAI_API_KEY_2
            OPENAI_API_KEY_3

        The same naming convention applies to Gemini, Groq,
        and Anthropic.

        Empty values are ignored.

        Numbered keys take precedence over the plain key when
        both refer to key number one.
        """

        discovered: Dict[int, str] = {}

        # --------------------------------------------------------------
        # Numbered keys
        # --------------------------------------------------------------

        for index in range(1, 101):
            variable_name = f"{prefix}_{index}"

            value = self._getenv(variable_name)

            if value is None:
                continue

            value = value.strip()

            if not value:
                continue

            discovered[index] = value

        # --------------------------------------------------------------
        # Plain key
        # --------------------------------------------------------------

        plain_key = self._getenv(prefix)

        if plain_key is not None:
            plain_key = plain_key.strip()

        if plain_key:
            if 1 not in discovered:
                discovered[1] = plain_key

        # --------------------------------------------------------------
        # Convert discovered keys into LLMKey objects
        # --------------------------------------------------------------

        keys: List[LLMKey] = []

        for index in sorted(discovered):
            key_id = f"{provider_name}_{index}"

            keys.append(
                LLMKey(
                    provider=provider_name,
                    key_id=key_id,
                    api_key=discovered[index],
                    model=default_model,
                    priority=(
                        provider_priority * 100
                    ) + index,
                )
            )

        return keys

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """
        Validate that at least one LLM API key is configured.

        Raises:
            RuntimeError:
                When no supported provider has a configured key.
        """

        if not self._keys:
            raise RuntimeError(
                "No LLM API keys are configured. "
                "Configure at least one of: "
                "OPENAI_API_KEY, "
                "GEMINI_API_KEY, "
                "GROQ_API_KEY, "
                "ANTHROPIC_API_KEY."
            )