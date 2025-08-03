"""Authentication patterns for service SDKs."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from .types import HeadersDict


class BaseAuthenticator(ABC):
    """Base class for all authentication handlers."""

    @abstractmethod
    def get_auth_headers(self) -> HeadersDict:
        """Get headers required for authentication.

        Returns:
            Dictionary of headers to include in requests
        """
        pass

    def authenticate_request(self, headers: HeadersDict) -> HeadersDict:
        """Add authentication to request headers.

        Args:
            headers: Existing request headers

        Returns:
            Updated headers with authentication
        """
        auth_headers = self.get_auth_headers()
        return {**headers, **auth_headers}

    def handle_auth_error(self, status_code: int, response_data: Dict[str, Any]) -> None:
        """Handle authentication errors from the API.

        Args:
            status_code: HTTP status code
            response_data: Response data from the API

        Raises:
            ServiceAuthenticationError: If authentication failed
        """
        if status_code == 401:
            from .base_exceptions import ServiceAuthenticationError

            raise ServiceAuthenticationError(
                service_name=self.__class__.__name__.replace("Authenticator", ""),
                details=response_data.get("error", "Invalid credentials"),
            )


class APIKeyAuthenticator(BaseAuthenticator):
    """Authentication using API keys."""

    def __init__(
        self,
        api_key: str,
        header_name: str = "Authorization",
        header_prefix: str = "Bearer",
    ) -> None:
        """Initialize API key authentication.

        Args:
            api_key: The API key for authentication
            header_name: Name of the header to use
            header_prefix: Prefix for the header value
        """
        self.api_key = api_key
        self.header_name = header_name
        self.header_prefix = header_prefix

    def get_auth_headers(self) -> HeadersDict:
        """Get API key authentication headers."""
        if self.header_prefix:
            header_value = f"{self.header_prefix} {self.api_key}"
        else:
            header_value = self.api_key

        return {self.header_name: header_value}


class BearerTokenAuthenticator(BaseAuthenticator):
    """Authentication using Bearer tokens."""

    def __init__(self, token: str) -> None:
        """Initialize Bearer token authentication.

        Args:
            token: The Bearer token for authentication
        """
        self.token = token

    def get_auth_headers(self) -> HeadersDict:
        """Get Bearer token authentication headers."""
        return {"Authorization": f"Bearer {self.token}"}


class BasicAuthenticator(BaseAuthenticator):
    """Authentication using Basic auth."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize Basic authentication.

        Args:
            username: Username for authentication
            password: Password for authentication
        """
        import base64

        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"

    def get_auth_headers(self) -> HeadersDict:
        """Get Basic authentication headers."""
        return {"Authorization": self.auth_header}


class OAuthAuthenticator(BaseAuthenticator):
    """Authentication using OAuth tokens."""

    def __init__(self, access_token: str, token_type: str = "Bearer") -> None:
        """Initialize OAuth authentication.

        Args:
            access_token: OAuth access token
            token_type: Type of token (usually "Bearer")
        """
        self.access_token = access_token
        self.token_type = token_type

    def get_auth_headers(self) -> HeadersDict:
        """Get OAuth authentication headers."""
        return {"Authorization": f"{self.token_type} {self.access_token}"}
