"""Tests for configuration management."""

import pytest
from pydantic import ValidationError

from elusion._core.configuration import ClientConfiguration, ServiceSettings, LogLevel


class TestClientConfiguration:
    """Test ClientConfiguration functionality."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = ClientConfiguration()

        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.retry_exponential_backoff is True
        assert config.retry_jitter is True
        assert config.user_agent is None
        assert config.log_level == LogLevel.WARNING
        assert config.debug_requests is False
        assert config.verify_ssl is True
        assert config.custom_headers == {}

    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = ClientConfiguration(
            timeout=60.0,
            max_retries=5,
            retry_delay=2.0,
            user_agent="custom-agent/1.0",
            debug_requests=True,
            custom_headers={"X-Custom": "value"},
        )

        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.user_agent == "custom-agent/1.0"
        assert config.debug_requests is True
        assert config.custom_headers == {"X-Custom": "value"}

    def test_validation_errors(self):
        """Test configuration validation."""
        with pytest.raises(ValidationError):
            ClientConfiguration(timeout=-1.0)  # Negative timeout

        with pytest.raises(ValidationError):
            ClientConfiguration(max_retries=-1)  # Negative retries

        with pytest.raises(ValidationError):
            ClientConfiguration(max_retries=20)  # Too many retries

    def test_get_user_agent(self):
        """Test user agent generation."""
        config = ClientConfiguration()
        user_agent = config.get_user_agent("TestService")

        assert "elusion-testservice-sdk" in user_agent
        assert "/" in user_agent  # Should include version

    def test_custom_user_agent(self):
        """Test custom user agent."""
        config = ClientConfiguration(user_agent="MySDK/2.0")
        user_agent = config.get_user_agent("TestService")

        assert user_agent == "MySDK/2.0"


class TestServiceSettings:
    """Test ServiceSettings functionality."""

    def test_service_settings_creation(self):
        """Test creating service settings."""
        settings = ServiceSettings(
            base_url="https://api.service.com",
            api_version="v2",
            rate_limit_per_second=10.0,
            custom_endpoints={"users": "/v2/users"},
            service_specific_config={"feature_flag": True},
        )

        assert settings.base_url == "https://api.service.com"
        assert settings.api_version == "v2"
        assert settings.rate_limit_per_second == 10.0
        assert settings.custom_endpoints == {"users": "/v2/users"}
        assert settings.service_specific_config == {"feature_flag": True}
