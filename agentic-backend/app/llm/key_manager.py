from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict, List, Optional


@dataclass
class LLMKey:
    """
    Represents one API key belonging to one LLM provider.

    The actual API secret is stored in `api_key`.
    `key_id` is a safe identifier used for logging and tracking.
    """

    provider: str
    key_id: str
    api_key: str

    model: str

    priority: int = 100

    enabled: bool = True

    failure_count: int = 0

    last_error: Optional[str] = None

    unavailable_until: Optional[datetime] = None

    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """
        Determine whether this key can currently be used.
        """

        if not self.enabled:
            return False

        if self.unavailable_until is None:
            return True

        now = datetime.now(timezone.utc)

        if now >= self.unavailable_until:
            self.unavailable_until = None
            return True

        return False


class KeyManager:
    """
    Manages API keys across multiple LLM providers.

    Responsibilities:
    - Store provider/key configurations.
    - Select the next available provider/key.
    - Track failed keys.
    - Temporarily disable unhealthy keys.
    - Restore keys after their cooldown expires.
    - Prevent concurrent requests from selecting the same key
      unnecessarily.

    This class does NOT make LLM API calls.
    """

    def __init__(
        self,
        keys: Optional[List[LLMKey]] = None,
        *,
        failure_cooldown_seconds: int = 60,
    ):
        self.failure_cooldown_seconds = failure_cooldown_seconds

        self._keys: Dict[str, LLMKey] = {}

        self._provider_positions: Dict[str, int] = {}

        self._lock = Lock()

        if keys:
            for key in keys:
                self.add_key(key)

    # ------------------------------------------------------------------
    # Key registration
    # ------------------------------------------------------------------

    def add_key(self, key: LLMKey) -> None:
        """
        Add a provider API key to the manager.

        key_id must be globally unique within this manager.
        """

        if not key.key_id:
            raise ValueError("key_id must not be empty")

        if not key.provider:
            raise ValueError("provider must not be empty")

        if not key.api_key:
            raise ValueError("api_key must not be empty")

        if not key.model:
            raise ValueError("model must not be empty")

        with self._lock:
            if key.key_id in self._keys:
                raise ValueError(
                    f"Duplicate LLM key_id: {key.key_id}"
                )

            self._keys[key.key_id] = key

            self._provider_positions.setdefault(
                key.provider,
                0,
            )

    # ------------------------------------------------------------------
    # Key lookup
    # ------------------------------------------------------------------

    def get_key(self, key_id: str) -> LLMKey:
        """
        Return a registered key by its identifier.
        """

        with self._lock:
            try:
                return self._keys[key_id]
            except KeyError:
                raise KeyError(
                    f"Unknown LLM key_id: {key_id}"
                ) from None

    def get_all_keys(self) -> List[LLMKey]:
        """
        Return all registered keys.

        This method is mainly useful for diagnostics and testing.
        """

        with self._lock:
            return list(self._keys.values())

    # ------------------------------------------------------------------
    # Provider discovery
    # ------------------------------------------------------------------

    def get_providers(self) -> List[str]:
        """
        Return all configured provider names ordered alphabetically.
        """

        with self._lock:
            return sorted(
                {
                    key.provider
                    for key in self._keys.values()
                }
            )

    # ------------------------------------------------------------------
    # Key selection
    # ------------------------------------------------------------------

    def get_next_key(
        self,
        *,
        provider: Optional[str] = None,
        exclude_key_ids: Optional[List[str]] = None,
    ) -> Optional[LLMKey]:
        """
        Select the next available key.

        If provider is supplied, only keys belonging to that
        provider are considered.

        If provider is omitted, keys from all providers are
        considered.

        Higher-priority keys are preferred.

        Keys temporarily marked unavailable are skipped.
        """

        excluded = set(exclude_key_ids or [])

        with self._lock:
            candidates = [
                key
                for key in self._keys.values()
                if key.is_available
                and key.key_id not in excluded
                and (
                    provider is None
                    or key.provider == provider
                )
            ]

            if not candidates:
                return None

            candidates.sort(
                key=lambda key: (
                    key.priority,
                    key.provider,
                    key.key_id,
                )
            )

            return candidates[0]

    # ------------------------------------------------------------------
    # Failure handling
    # ------------------------------------------------------------------

    def mark_failure(
        self,
        key_id: str,
        *,
        error: str,
        cooldown_seconds: Optional[int] = None,
    ) -> None:
        """
        Mark a key as temporarily unavailable.

        This is used for failures such as:
        - quota exhaustion
        - rate limiting
        - temporary provider failures
        - authentication failures
        - timeouts
        """

        with self._lock:
            key = self._keys.get(key_id)

            if key is None:
                raise KeyError(
                    f"Unknown LLM key_id: {key_id}"
                )

            key.failure_count += 1
            key.last_error = error

            cooldown = (
                cooldown_seconds
                if cooldown_seconds is not None
                else self.failure_cooldown_seconds
            )

            key.unavailable_until = (
                datetime.now(timezone.utc)
                + timedelta(seconds=cooldown)
            )

    def mark_permanently_disabled(
        self,
        key_id: str,
        *,
        error: str,
    ) -> None:
        """
        Permanently disable a key until explicitly re-enabled.

        Useful for invalid or revoked API keys.
        """

        with self._lock:
            key = self._keys.get(key_id)

            if key is None:
                raise KeyError(
                    f"Unknown LLM key_id: {key_id}"
                )

            key.enabled = False
            key.failure_count += 1
            key.last_error = error
            key.unavailable_until = None

    def mark_success(self, key_id: str) -> None:
        """
        Record a successful request.

        A successful request resets the consecutive failure state.
        """

        with self._lock:
            key = self._keys.get(key_id)

            if key is None:
                raise KeyError(
                    f"Unknown LLM key_id: {key_id}"
                )

            key.failure_count = 0
            key.last_error = None
            key.unavailable_until = None

    # ------------------------------------------------------------------
    # Key recovery
    # ------------------------------------------------------------------

    def enable_key(self, key_id: str) -> None:
        """
        Re-enable a previously disabled key.
        """

        with self._lock:
            key = self._keys.get(key_id)

            if key is None:
                raise KeyError(
                    f"Unknown LLM key_id: {key_id}"
                )

            key.enabled = True
            key.unavailable_until = None
            key.failure_count = 0
            key.last_error = None

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_key_status(self, key_id: str) -> Dict[str, object]:
        """
        Return safe diagnostic information about a key.

        The actual API secret is deliberately never returned.
        """

        with self._lock:
            key = self._keys.get(key_id)

            if key is None:
                raise KeyError(
                    f"Unknown LLM key_id: {key_id}"
                )

            return {
                "key_id": key.key_id,
                "provider": key.provider,
                "model": key.model,
                "priority": key.priority,
                "enabled": key.enabled,
                "available": key.is_available,
                "failure_count": key.failure_count,
                "last_error": key.last_error,
                "unavailable_until": (
                    key.unavailable_until.isoformat()
                    if key.unavailable_until
                    else None
                ),
            }

    def reset_all(self) -> None:
        """
        Reset the health state of every configured key.

        Useful for testing and controlled recovery.
        """

        with self._lock:
            for key in self._keys.values():
                key.enabled = True
                key.failure_count = 0
                key.last_error = None
                key.unavailable_until = None