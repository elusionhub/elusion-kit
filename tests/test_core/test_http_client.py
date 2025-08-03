"""Tests for HTTP client functionality."""

from typing import Any, Dict
import pytest
import httpx
import respx

from elusion._core.http_client import HTTPClient, HTTPResponse
from elusion._core.authentication import APIKeyAuthenticator
from elusion._core.configuration import ClientConfiguration
from elusion._core.base_exceptions import (
    ServiceAPIError,
    ServiceRateLimitError,
    ServiceUnavailableError,
)


class TestHTTPResponse:
    """Test HTTPResponse functionality."""

    def test_http_response_creation(self):
        """Test creating HTTPResponse object."""
        response = HTTPResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            content=b'{"message": "success"}',
            text='{"message": "success"}',
            url="https://api.example.com/test",
            request_id="req_123",
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert response.content == b'{"message": "success"}'
        assert response.text == '{"message": "success"}'
        assert response.url == "https://api.example.com/test"
        assert response.request_id == "req_123"

    def test_json_parsing(self):
        """Test JSON parsing from response."""
        response = HTTPResponse(
            status_code=200,
            headers={},
            content=b'{"key": "value", "number": 42}',
            text='{"key": "value", "number": 42}',
            url="https://api.example.com/test",
        )

        data = response.json()
        assert data == {"key": "value", "number": 42}

    def test_invalid_json_parsing(self):
        """Test invalid JSON parsing."""
        response = HTTPResponse(
            status_code=200,
            headers={},
            content=b"invalid json",
            text="invalid json",
            url="https://api.example.com/test",
        )

        with pytest.raises(ValueError, match="Response is not valid JSON"):
            response.json()

    def test_status_code_checks(self):
        """Test status code checking methods."""
        success_response = HTTPResponse(200, {}, b"", "", "")
        assert success_response.is_success() is True
        assert success_response.is_client_error() is False
        assert success_response.is_server_error() is False

        client_error_response = HTTPResponse(404, {}, b"", "", "")
        assert client_error_response.is_success() is False
        assert client_error_response.is_client_error() is True
        assert client_error_response.is_server_error() is False

        server_error_response = HTTPResponse(500, {}, b"", "", "")
        assert server_error_response.is_success() is False
        assert server_error_response.is_client_error() is False
        assert server_error_response.is_server_error() is True


class TestHTTPClient:
    """Test HTTPClient functionality."""

    @pytest.fixture
    def http_client(
        self, base_config: ClientConfiguration, api_key_auth: APIKeyAuthenticator
    ) -> HTTPClient:
        """HTTP client fixture for testing."""
        return HTTPClient(
            base_url="https://api.example.com",
            authenticator=api_key_auth,
            config=base_config,
            service_name="TestService",
        )

    def test_http_client_initialization(self, http_client: HTTPClient):
        """Test HTTP client initialization."""
        assert http_client.base_url == "https://api.example.com"
        assert http_client.service_name == "TestService"
        assert http_client.authenticator is not None

    def test_build_url(self, http_client: HTTPClient):
        """Test URL building."""
        # Test with leading slash
        url = http_client.build_url("/users")
        assert url == "https://api.example.com/users"

        # Test without leading slash
        url = http_client.build_url("users")
        assert url == "https://api.example.com/users"

        # Test with full URL
        url = http_client.build_url("https://other.api.com/users")
        assert url == "https://other.api.com/users"

    def test(self, http_client: HTTPClient):
        """Test header preparation."""
        headers = http_client.prepare_headers()

        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Content-Type" in headers
        assert "Authorization" in headers  # From authenticator
        assert headers["Authorization"] == "Bearer test_api_key_12345"

    def test_prepare_headers_with_additional(self, http_client: HTTPClient):
        """Test header preparation with additional headers."""
        additional_headers = {"X-Custom": "value"}
        headers = http_client.prepare_headers(additional_headers)

        assert headers["X-Custom"] == "value"
        assert "Authorization" in headers

    def test_prepare_params(self, http_client: HTTPClient):
        """Test parameter preparation."""
        params: Dict[str, Any] = {
            "page": 1,
            "limit": 10,
            "active": True,
            "search": None,
        }
        prepared = http_client.prepare_params(params)

        expected = {"page": "1", "limit": "10", "active": "True"}
        assert prepared == expected

    def test_prepare_params_none(self, http_client: HTTPClient):
        """Test parameter preparation with None."""
        prepared = http_client.prepare_params(None)
        assert prepared is None


@respx.mock
class TestHTTPClientRequests:
    """Test HTTP client request functionality with mocked responses."""

    @pytest.fixture
    def http_client(
        self, base_config: ClientConfiguration, api_key_auth: APIKeyAuthenticator
    ) -> HTTPClient:
        """HTTP client fixture for testing."""
        return HTTPClient(
            base_url="https://api.example.com",
            authenticator=api_key_auth,
            config=base_config,
            service_name="TestService",
        )

    def test_successful_get_request(self, http_client: HTTPClient):
        """Test successful GET request."""
        # Mock the response
        respx.get("https://api.example.com/users").mock(
            return_value=httpx.Response(
                200,
                json={"users": [{"id": 1, "name": "John"}]},
                headers={"x-request-id": "req_123"},
            )
        )

        response = http_client.get("/users")

        assert response.status_code == 200
        assert response.request_id == "req_123"
        data = response.json()
        assert data["users"][0]["name"] == "John"

    def test_successful_post_request(self, http_client: HTTPClient):
        """Test successful POST request."""
        respx.post("https://api.example.com/users").mock(
            return_value=httpx.Response(
                201, json={"id": 2, "name": "Jane", "email": "jane@example.com"}
            )
        )

        response = http_client.post(
            "/users", json_data={"name": "Jane", "email": "jane@example.com"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Jane"

    def test_404_error_handling(self, http_client: HTTPClient):
        """Test 404 error handling."""
        respx.get("https://api.example.com/users/999").mock(
            return_value=httpx.Response(
                404, json={"error": "User not found", "error_code": "NOT_FOUND"}
            )
        )

        with pytest.raises(ServiceAPIError) as exc_info:
            http_client.get("/users/999")

        error = exc_info.value
        assert error.status_code == 404
        assert error.error_code == "NOT_FOUND"
        assert "User not found" in str(error)

    def test_rate_limit_error_handling(self, http_client: HTTPClient):
        """Test rate limit error handling."""
        respx.get("https://api.example.com/users").mock(
            return_value=httpx.Response(
                429,
                json={"error": "Rate limit exceeded"},
                headers={"Retry-After": "60"},
            )
        )

        with pytest.raises(ServiceRateLimitError) as exc_info:
            http_client.get("/users")

        error = exc_info.value
        assert error.status_code == 429
        assert error.retry_after == 60

    def test_server_error_handling(self, http_client: HTTPClient):
        """Test 503 server error handling."""
        respx.get("https://api.example.com/users").mock(
            return_value=httpx.Response(
                503,
                json={"error": "Service temporarily unavailable"},
                headers={"Retry-After": "30"},
            )
        )

        with pytest.raises(ServiceUnavailableError) as exc_info:
            http_client.get("/users")

        error = exc_info.value
        assert error.status_code == 503
        assert error.retry_after == 30
