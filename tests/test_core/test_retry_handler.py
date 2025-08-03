"""Tests for retry handler functionality."""

import pytest
from unittest.mock import Mock

from elusion._core.retry_handler import RetryHandler, RetryConfig, RetryStrategy
from elusion._core.base_exceptions import ServiceRateLimitError, ServiceUnavailableError


class TestRetryConfig:
    """Test RetryConfig functionality."""

    def test_default_retry_config(self):
        """Test default retry configuration."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.jitter is True
        assert config.backoff_multiplier == 2.0
        assert 429 in config.retryable_status_codes
        assert ServiceRateLimitError in config.retryable_exceptions

    def test_custom_retry_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            jitter=False,
        )

        assert config.max_attempts == 5
        assert config.base_delay == 0.5
        assert config.strategy == RetryStrategy.LINEAR_BACKOFF
        assert config.jitter is False


class TestRetryHandler:
    """Test RetryHandler functionality."""

    @pytest.fixture
    def retry_handler(self, retry_config: RetryConfig) -> RetryHandler:
        """Retry handler fixture."""
        return RetryHandler(retry_config)

    def test_should_retry_with_retryable_status_code(self, retry_handler: RetryHandler):
        """Test retry decision with retryable status code."""
        assert retry_handler.should_retry(1, status_code=429) is True
        assert retry_handler.should_retry(1, status_code=500) is True
        assert retry_handler.should_retry(1, status_code=503) is True
        assert retry_handler.should_retry(1, status_code=400) is False
        assert retry_handler.should_retry(1, status_code=404) is False

    def test_should_retry_with_retryable_exception(self, retry_handler: RetryHandler):
        """Test retry decision with retryable exception."""
        rate_limit_error = ServiceRateLimitError("TestService")
        unavailable_error = ServiceUnavailableError("TestService")
        connection_error = ConnectionError("Connection failed")

        assert retry_handler.should_retry(1, exception=rate_limit_error) is True
        assert retry_handler.should_retry(1, exception=unavailable_error) is True
        assert retry_handler.should_retry(1, exception=connection_error) is True
        assert retry_handler.should_retry(1, exception=ValueError("Invalid")) is False

    def test_should_retry_max_attempts_exceeded(self, retry_handler: RetryHandler):
        """Test retry decision when max attempts exceeded."""
        assert (
            retry_handler.should_retry(3, status_code=429) is False
        )  # At max attempts
        assert (
            retry_handler.should_retry(4, status_code=429) is False
        )  # Exceeded max attempts

    def test_get_retry_delay_fixed_strategy(self):
        """Test retry delay calculation with fixed strategy."""
        config = RetryConfig(strategy=RetryStrategy.FIXED, base_delay=1.0, jitter=False)
        handler = RetryHandler(config)

        assert handler.get_retry_delay(1) == 1.0
        assert handler.get_retry_delay(2) == 1.0
        assert handler.get_retry_delay(3) == 1.0

    def test_get_retry_delay_linear_strategy(self):
        """Test retry delay calculation with linear backoff strategy."""
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR_BACKOFF, base_delay=1.0, jitter=False
        )
        handler = RetryHandler(config)

        assert handler.get_retry_delay(1) == 1.0
        assert handler.get_retry_delay(2) == 2.0
        assert handler.get_retry_delay(3) == 3.0

    def test_get_retry_delay_exponential_strategy(self):
        """Test retry delay calculation with exponential backoff strategy."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            backoff_multiplier=2.0,
            jitter=False,
        )
        handler = RetryHandler(config)

        assert handler.get_retry_delay(1) == 1.0
        assert handler.get_retry_delay(2) == 2.0
        assert handler.get_retry_delay(3) == 4.0

    def test_get_retry_delay_with_max_delay(self):
        """Test retry delay with maximum delay limit."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=3.0,
            jitter=False,
        )
        handler = RetryHandler(config)

        assert handler.get_retry_delay(1) == 1.0
        assert handler.get_retry_delay(2) == 2.0
        assert handler.get_retry_delay(3) == 3.0  # Capped at max_delay
        assert handler.get_retry_delay(4) == 3.0  # Still capped

    def test_get_retry_delay_with_exception_retry_after(self):
        """Test retry delay with exception-specified retry_after."""
        config = RetryConfig(jitter=False)
        handler = RetryHandler(config)

        rate_limit_error = ServiceRateLimitError("TestService", retry_after=5)
        delay = handler.get_retry_delay(1, rate_limit_error)

        assert delay == 5.0

    def test_execute_with_retry_success(self, retry_handler: RetryHandler):
        """Test successful operation execution."""
        mock_operation = Mock(return_value="success")

        result = retry_handler.execute_with_retry(mock_operation, "test_operation")

        assert result == "success"
        assert mock_operation.call_count == 1

    def test_execute_with_retry_eventual_success(self, retry_handler: RetryHandler):
        """Test operation that succeeds after retries."""
        mock_operation = Mock(
            side_effect=[
                ServiceRateLimitError("TestService"),  # First attempt fails
                ServiceRateLimitError("TestService"),  # Second attempt fails
                "success",  # Third attempt succeeds
            ]
        )

        result = retry_handler.execute_with_retry(mock_operation, "test_operation")

        assert result == "success"
        assert mock_operation.call_count == 3

    def test_execute_with_retry_max_attempts_reached(self, retry_handler: RetryHandler):
        """Test operation that fails after max attempts."""
        mock_operation = Mock(side_effect=ServiceRateLimitError("TestService"))

        with pytest.raises(ServiceRateLimitError):
            retry_handler.execute_with_retry(mock_operation, "test_operation")

        assert mock_operation.call_count == 3  # max_attempts from config

    def test_execute_with_retry_non_retryable_error(self, retry_handler: RetryHandler):
        """Test operation with non-retryable error."""
        mock_operation = Mock(side_effect=ValueError("Invalid input"))

        with pytest.raises(ValueError):
            retry_handler.execute_with_retry(mock_operation, "test_operation")

        assert mock_operation.call_count == 1  # No retries for non-retryable error
