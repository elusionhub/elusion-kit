"""Tests for authentication patterns."""

import base64

from elusion._core.authentication import (
    APIKeyAuthenticator,
    BearerTokenAuthenticator,
    BasicAuthenticator,
    OAuthAuthenticator,
)


class TestAPIKeyAuthenticator:
    """Test API key authentication."""

    def test_default_api_key_auth(self):
        """Test default API key authentication."""
        auth = APIKeyAuthenticator("test_key_123")
        headers = auth.get_auth_headers()

        assert headers == {"Authorization": "Bearer test_key_123"}

    def test_custom_header_api_key_auth(self):
        """Test custom header API key authentication."""
        auth = APIKeyAuthenticator(
            api_key="test_key_123", header_name="X-API-Key", header_prefix=""
        )
        headers = auth.get_auth_headers()

        assert headers == {"X-API-Key": "test_key_123"}

    def test_custom_prefix_api_key_auth(self):
        """Test custom prefix API key authentication."""
        auth = APIKeyAuthenticator(api_key="test_key_123", header_prefix="Token")
        headers = auth.get_auth_headers()

        assert headers == {"Authorization": "Token test_key_123"}

    def test_authenticate_request(self):
        """Test authenticating a request."""
        auth = APIKeyAuthenticator("test_key_123")
        existing_headers = {"Content-Type": "application/json"}

        authenticated_headers = auth.authenticate_request(existing_headers)

        assert authenticated_headers["Content-Type"] == "application/json"
        assert authenticated_headers["Authorization"] == "Bearer test_key_123"


class TestBearerTokenAuthenticator:
    """Test Bearer token authentication."""

    def test_bearer_token_auth(self):
        """Test Bearer token authentication."""
        auth = BearerTokenAuthenticator("access_token_123")
        headers = auth.get_auth_headers()

        assert headers == {"Authorization": "Bearer access_token_123"}


class TestBasicAuthenticator:
    """Test Basic authentication."""

    def test_basic_auth(self):
        """Test Basic authentication."""
        auth = BasicAuthenticator("username", "password")
        headers = auth.get_auth_headers()

        # Decode the authorization header to verify
        auth_header = headers["Authorization"]
        assert auth_header.startswith("Basic ")

        encoded_credentials = auth_header.split(" ")[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode()
        assert decoded_credentials == "username:password"


class TestOAuthAuthenticator:
    """Test OAuth authentication."""

    def test_oauth_auth_default(self):
        """Test OAuth authentication with default token type."""
        auth = OAuthAuthenticator("oauth_token_123")
        headers = auth.get_auth_headers()

        assert headers == {"Authorization": "Bearer oauth_token_123"}

    def test_oauth_auth_custom_type(self):
        """Test OAuth authentication with custom token type."""
        auth = OAuthAuthenticator("oauth_token_123", token_type="Token")
        headers = auth.get_auth_headers()

        assert headers == {"Authorization": "Token oauth_token_123"}
