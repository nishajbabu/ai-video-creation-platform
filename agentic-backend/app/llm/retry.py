from dataclasses import dataclass
import random
import time
from typing import Callable, Optional, TypeVar

from .exceptions import (
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)


T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    """
    Configuration for retry behavior.

    Retries are intentionally conservative because LLM requests
    can be expensive and provider rate limits vary.
    """

    max_attempts: int = 3

    initial_delay_seconds: float = 1.0

    max_delay_seconds: float = 30.0

    exponential_base: float = 2.0

    jitter: bool = True

    jitter_ratio: float = 0.25

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if self.initial_delay_seconds < 0:
            raise ValueError(
                "initial_delay_seconds cannot be negative"
            )

        if self.max_delay_seconds < self.initial_delay_seconds:
            raise ValueError(
                "max_delay_seconds must be greater than or equal "
                "to initial_delay_seconds"
            )

        if self.exponential_base < 1:
            raise ValueError(
                "exponential_base must be at least 1"
            )

        if not 0 <= self.jitter_ratio <= 1:
            raise ValueError(
                "jitter_ratio must be between 0 and 1"
            )


class RetryPolicy:
    """
    Determines whether an LLM operation should be retried
    and calculates the delay before the next attempt.
    """

    RETRYABLE_EXCEPTIONS = (
        LLMRateLimitError,
        LLMTimeoutError,
        LLMProviderError,
    )

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
    ):
        self.config = config or RetryConfig()

    def should_retry(
        self,
        error: Exception,
        attempt: int,
    ) -> bool:
        """
        Determine whether another attempt should be made.

        `attempt` is one-based.

        Example:

            max_attempts = 3

            attempt 1 -> retry possible
            attempt 2 -> retry possible
            attempt 3 -> no retry
        """

        if attempt >= self.config.max_attempts:
            return False

        if isinstance(error, LLMError):
            return error.retryable

        return isinstance(
            error,
            self.RETRYABLE_EXCEPTIONS,
        )

    def calculate_delay(
        self,
        attempt: int,
    ) -> float:
        """
        Calculate exponential backoff delay.

        Example with:
            initial_delay = 1
            base = 2

        attempt 1 -> approximately 1 second
        attempt 2 -> approximately 2 seconds
        attempt 3 -> approximately 4 seconds

        The final value is capped by max_delay_seconds.
        """

        if attempt < 1:
            raise ValueError("attempt must be at least 1")

        delay = (
            self.config.initial_delay_seconds
            * (
                self.config.exponential_base
                ** (attempt - 1)
            )
        )

        delay = min(
            delay,
            self.config.max_delay_seconds,
        )

        if self.config.jitter:
            jitter_amount = (
                delay * self.config.jitter_ratio
            )

            delay += random.uniform(
                -jitter_amount,
                jitter_amount,
            )

            delay = max(delay, 0.0)

        return delay

    def wait(
        self,
        attempt: int,
    ) -> float:
        """
        Sleep for the calculated retry delay.

        Returns the actual delay used.
        """

        delay = self.calculate_delay(attempt)

        if delay > 0:
            time.sleep(delay)

        return delay

    def execute(
        self,
        operation: Callable[[], T],
        *,
        on_retry: Optional[
            Callable[[Exception, int, float], None]
        ] = None,
    ) -> T:
        """
        Execute an operation with retry handling.

        `on_retry`, when supplied, receives:

            error
            current attempt
            calculated delay

        before the next attempt is made.
        """

        last_error: Optional[Exception] = None

        for attempt in range(
            1,
            self.config.max_attempts + 1,
        ):
            try:
                return operation()

            except Exception as error:
                last_error = error

                if not self.should_retry(
                    error,
                    attempt,
                ):
                    raise

                delay = self.calculate_delay(attempt)

                if on_retry:
                    on_retry(
                        error,
                        attempt,
                        delay,
                    )

                if delay > 0:
                    time.sleep(delay)

        if last_error is not None:
            raise last_error

        raise RuntimeError(
            "RetryPolicy execution ended without a result."
        )