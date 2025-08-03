"""Base client class for all service SDKs."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .http_client import HTTPClient
from .configuration import ClientConfiguration, ServiceSettings
from .authentication import BaseAuthenticator


class BaseServiceClient(ABC):
    """Abstract base class for all service SDK clients.

    Provides common patterns and ensures consistency across all service SDKs
    while allowing each service to implement its own specific functionality.
    """

    def __init__(
        self,
        http_client: Optional[HTTPClient] = None,
        config: Optional[ClientConfiguration] = None,
        service_settings: Optional[ServiceSettings] = None,
        authenticator: Optional[BaseAuthenticator] = None,
    ) -> None:
        """Initialize the service client.

        Args:
            http_client: Pre-configured HTTP client
            config: Client configuration
            service_settings: Service-specific settings
            authenticator: Authentication handler
        """
        if http_client is not None:
            self._http_client = http_client
        elif http_client is None:
            if not service_settings:
                raise ValueError("service_settings is required when http_client is not provided")

            self._config = config or ClientConfiguration()
            self._http_client = HTTPClient(
                base_url=service_settings.base_url,
                authenticator=authenticator,
                config=self._config,
                service_settings=service_settings,
                service_name=self._get_service_name(),
            )
            self._owns_http_client = True
        else:
            self._owns_http_client = False

    @abstractmethod
    def _get_service_name(self) -> str:
        """Get the name of the service this client connects to.

        Returns:
            Service name (e.g., "ServiceA")
        """
        pass

    @abstractmethod
    def _get_base_url(self) -> str:
        """Get the base URL for this service's API.

        Returns:
            Base URL for the service API
        """
        pass

    def get_service_info(self) -> Dict[str, Any]:
        """Get information about this service client.

        Returns:
            Dictionary with service information
        """
        return {
            "service_name": self._get_service_name(),
            "base_url": self._get_base_url(),
            "authenticated": self._http_client.authenticator is not None,
        }

    def test_connection(self) -> bool:
        """Test the connection to the service.

        Returns:
            True if connection is successful

        Raises:
            ServiceAPIError: If connection test fails
        """
        try:
            response = self._http_client.get("/")
            return response.is_success()
        except Exception:
            return False

    def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        if self._owns_http_client:
            self._http_client.close()

    def __enter__(self) -> "BaseServiceClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


class BaseResource:
    """Base class for API resource handlers.

    Resources represent collections of related API endpoints (e.g., users, payments).
    """

    def __init__(self, http_client: HTTPClient) -> None:
        """Initialize the resource.

        Args:
            http_client: HTTP client for making requests
        """
        self._http_client = http_client

    def _build_endpoint(self, *parts: str | None) -> str:
        """Build an endpoint URL from parts.

        Args:
            parts: URL path parts

        Returns:
            Complete endpoint path
        """
        # Remove None values and empty strings
        clean_parts = [str(part) for part in parts if part is not None and str(part)]
        return "/" + "/".join(clean_parts)
