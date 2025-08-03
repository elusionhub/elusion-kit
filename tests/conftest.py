"""Shared test configuration and fixtures."""

import pytest
from typing import Dict, Any
import respx

from elusion._core.configuration import ClientConfiguration, ServiceSettings
from elusion._core.authentication import APIKeyAuthenticator, BearerTokenAuthenticator
from elusion._core.http_client import HTTPClient
from elusion._core.retry_handler import RetryConfig


@pytest.fixture
def base_config() -> ClientConfiguration:
    """Basic client configuration for testing."""
    return ClientConfiguration(
        timeout=10.0,
        max_retries=2,
        retry_delay=0.1,  # Fast retries for testing
        debug_requests=True,
    )


@pytest.fixture
def service_settings() -> ServiceSettings:
    """Basic service settings for testing."""
    return ServiceSettings(
        base_url="https://api.example.com",
        api_version="v1"
    )


@pytest.fixture
def api_key_auth() -> APIKeyAuthenticator:
    """API key authenticator for testing."""
    return APIKeyAuthenticator("test_api_key_12345")


@pytest.fixture
def bearer_auth() -> BearerTokenAuthenticator:
    """Bearer token authenticator for testing."""
    return BearerTokenAuthenticator("test_bearer_token_67890")


@pytest.fixture
def mock_http_client(
    base_config: ClientConfiguration, api_key_auth: APIKeyAuthenticator
) -> HTTPClient:
    """Mock HTTP client for testing."""
    return HTTPClient(
        base_url="https://api.example.com",
        authenticator=api_key_auth,
        config=base_config,
        service_name="TestService",
    )


@pytest.fixture
def retry_config() -> RetryConfig:
    """Retry configuration for testing."""
    return RetryConfig(
        max_attempts=3,
        base_delay=0.1,
        max_delay=1.0,
        jitter=False,  # Disable jitter for predictable tests
    )


@pytest.fixture
def sample_response_data() -> Dict[str, Any]:
    """Sample API response data."""
    return {
        "id": "test_123",
        "name": "Test Resource",
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "metadata": {"key": "value"},
    }


@pytest.fixture
def sample_error_response() -> Dict[str, Any]:
    """Sample API error response."""
    return {
        "error": "Resource not found",
        "error_code": "NOT_FOUND",
        "request_id": "req_123456789",
    }


@pytest.fixture
def respx_mock():
    """Respx mock for HTTP testing."""
    with respx.mock:
        yield respx
