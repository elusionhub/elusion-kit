"""Retry logic for failed requests."""

import time
import random
from typing import Any, Callable, Optional, List, Type
from enum import Enum
from dataclasses import dataclass
from .base_exceptions import (
    ServiceRateLimitError,
    ServiceUnavailableError,
)


class RetryStrategy(str, Enum):
    """Available retry strategies."""

    FIXED = "fixed"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True
    backoff_multiplier: float = 2.0

    # HTTP status codes that should trigger retries
    retryable_status_codes: Optional[List[int]] = None

    # Exception types that should trigger retries
    retryable_exceptions: Optional[List[Type[Exception]]] = None

    def __post_init__(self) -> None:
        if not self.retryable_status_codes:
            self.retryable_status_codes = [408, 429, 500, 502, 503, 504]

        if not self.retryable_exceptions:
            self.retryable_exceptions = [
                ServiceRateLimitError,
                ServiceUnavailableError,
                ConnectionError,
                TimeoutError,
            ]


class RetryHandler:
    """Handles retry logic for failed requests."""

    def __init__(self, config: Optional[RetryConfig] = None) -> None:
        """Initialize the retry handler.

        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()

    def should_retry(
        self,
        attempt: int,
        exception: Optional[Exception] = None,
        status_code: Optional[int] = None,
    ) -> bool:
        """Determine if a request should be retried.

        Args:
            attempt: Current attempt number (1-based)
            exception: Exception that occurred
            status_code: HTTP status code

        Returns:
            True if the request should be retried
        """
        # Check if we've exceeded max attempts
        if attempt >= self.config.max_attempts:
            return False

        # Check status code
        if (
            status_code
            and self.config.retryable_status_codes
            and status_code in self.config.retryable_status_codes
        ):
            return True

        # Check exception type
        if exception and self.config.retryable_exceptions:
            for retryable_type in self.config.retryable_exceptions:
                if isinstance(exception, retryable_type):
                    return True

        return False

    def get_retry_delay(
        self, attempt: int, exception: Optional[Exception] = None
    ) -> float:
        """Calculate the delay before the next retry attempt.

        Args:
            attempt: Current attempt number (1-based)
            exception: Exception that occurred

        Returns:
            Delay in seconds before next retry
        """
        # Check if exception specifies a retry delay
        if isinstance(exception, (ServiceRateLimitError, ServiceUnavailableError)):
            if hasattr(exception, "retry_after") and exception.retry_after:
                return float(exception.retry_after)

        # Calculate delay based on strategy
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt
        else:  # EXPONENTIAL_BACKOFF
            delay = self.config.base_delay * (
                self.config.backoff_multiplier ** (attempt - 1)
            )

        # Apply maximum delay
        delay = min(delay, self.config.max_delay)

        # Add jitter if enabled
        if self.config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def execute_with_retry(
        self, operation: Callable[[], Any], operation_name: str = "operation"
    ) -> Any:
        """Execute an operation with retry logic.

        Args:
            operation: Function to execute
            operation_name: Name of the operation for logging

        Returns:
            Result of the operation

        Raises:
            The last exception if all retry attempts fail
        """
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                return operation()
            except Exception as e:
                last_exception = e

                # Check if we should retry
                status_code = getattr(e, "status_code", None)
                if not self.should_retry(attempt, e, status_code):
                    raise e

                # Calculate delay and wait
                if attempt < self.config.max_attempts:
                    delay = self.get_retry_delay(attempt, e)
                    if delay > 0:
                        time.sleep(delay)

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
