"""HTTP client with retry logic and error handling."""

import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
import httpx

from .types import HeadersDict, ParamsDict, JSONData, RequestData
from .authentication import BaseAuthenticator
from .configuration import ClientConfiguration, ServiceSettings
from .retry_handler import RetryHandler, RetryConfig, RetryStrategy
from .base_exceptions import (
    ServiceAPIError,
    ServiceTimeoutError,
    ServiceRateLimitError,
    ServiceUnavailableError,
)


@dataclass
class HTTPResponse:
    """Response from an HTTP request."""

    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    url: str
    request_id: Optional[str] = None

    def json(self) -> Any:
        """Parse response content as JSON."""
        try:
            return json.loads(self.content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Response is not valid JSON: {e}")

    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return 200 <= self.status_code < 300

    def is_client_error(self) -> bool:
        """Check if the response indicates a client error."""
        return 400 <= self.status_code < 500

    def is_server_error(self) -> bool:
        """Check if the response indicates a server error."""
        return 500 <= self.status_code < 600


class HTTPClient:
    """HTTP client with comprehensive error handling and retry logic."""

    def __init__(
        self,
        base_url: str,
        authenticator: Optional[BaseAuthenticator] = None,
        config: Optional[ClientConfiguration] = None,
        service_settings: Optional[ServiceSettings] = None,
        service_name: str = "Unknown",
    ) -> None:
        """Initialize the HTTP client.

        Args:
            base_url: Base URL for all requests
            authenticator: Authentication handler
            config: Client configuration
            service_settings: Service-specific settings
            service_name: Name of the service for error reporting
        """
        self.base_url = base_url.rstrip("/")
        self.authenticator = authenticator
        self.config = config or ClientConfiguration()
        self.service_settings = service_settings
        self.service_name = service_name

        # Initialize retry handler
        retry_config = RetryConfig(
            max_attempts=self.config.max_retries + 1,  # +1 for initial attempt
            base_delay=self.config.retry_delay,
            strategy=(RetryStrategy.EXPONENTIAL_BACKOFF if self.config.retry_exponential_backoff else RetryStrategy.FIXED),
            jitter=self.config.retry_jitter,
        )
        self.retry_handler = RetryHandler(retry_config)

        # Initialize httpx client
        self._client = httpx.Client(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            headers=self._get_default_headers(),
        )

    def _get_default_headers(self) -> HeadersDict:
        """Get default headers for all requests."""
        headers = {
            "User-Agent": self.config.get_user_agent(self.service_name),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Add custom headers
        headers.update(self.config.custom_headers)

        return headers

    def build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint.

        Args:
            endpoint: API endpoint (with or without leading slash)

        Returns:
            Full URL
        """
        if endpoint.startswith(("http://", "https://")):
            return endpoint

        # Remove leading slash if present
        endpoint = endpoint.lstrip("/")

        return f"{self.base_url}/{endpoint}"

    def prepare_headers(self, additional_headers: Optional[HeadersDict] = None) -> HeadersDict:
        """Prepare headers for a request.

        Args:
            additional_headers: Additional headers to include

        Returns:
            Complete headers dictionary
        """
        headers = self._get_default_headers()

        # Add authentication headers
        if self.authenticator:
            headers = self.authenticator.authenticate_request(headers)

        # Add additional headers
        if additional_headers:
            headers.update(additional_headers)

        return headers

    def prepare_params(self, params: Optional[ParamsDict] = None) -> Optional[Dict[str, str]]:
        """Prepare query parameters for a request.

        Args:
            params: Query parameters

        Returns:
            Prepared parameters
        """
        if not params:
            return None

        # Convert all values to strings
        return {key: str(value) for key, value in params.items() if value}

    def _handle_response(self, response: httpx.Response, endpoint: str) -> HTTPResponse:
        """Handle and validate HTTP response.

        Args:
            response: Raw httpx response
            endpoint: The endpoint that was called

        Returns:
            Processed HTTP response

        Raises:
            ServiceAPIError: If the response indicates an error
        """
        # Extract request ID if available
        request_id = response.headers.get("x-request-id") or response.headers.get("request-id")

        http_response = HTTPResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            text=response.text,
            url=str(response.url),
            request_id=request_id,
        )

        # Handle successful responses
        if http_response.is_success():
            return http_response

        # Handle error responses
        self._handle_error_response(http_response, endpoint)

        return http_response  # This line should never be reached

    def _handle_error_response(self, response: HTTPResponse, endpoint: str) -> None:
        """Handle error responses and raise appropriate exceptions.

        Args:
            response: HTTP response object
            endpoint: The endpoint that was called

        Raises:
            ServiceAPIError: Appropriate error based on status code
        """
        try:
            error_data = response.json()
        except (ValueError, json.JSONDecodeError):
            error_data = {"error": response.text or "Unknown error"}

        error_message = self._extract_error_message(error_data, response.status_code)
        error_code = self._extract_error_code(error_data)

        # Handle specific status codes
        if response.status_code == 401:
            if self.authenticator:
                self.authenticator.handle_auth_error(response.status_code, error_data)
        elif response.status_code == 408:
            raise ServiceTimeoutError(self.service_name, self.config.timeout)
        elif response.status_code == 429:
            retry_after = self._extract_retry_after(response.headers, error_data)
            raise ServiceRateLimitError(
                service_name=self.service_name,
                retry_after=retry_after,
                limit_type=error_data.get("limit_type"),
            )
        elif response.status_code == 503:
            retry_after = self._extract_retry_after(response.headers, error_data)
            raise ServiceUnavailableError(self.service_name, retry_after)

        # Generic API error
        raise ServiceAPIError(
            message=error_message,
            service_name=self.service_name,
            status_code=response.status_code,
            error_code=error_code,
            request_id=response.request_id,
            response_data=error_data,
            endpoint=endpoint,
        )

    def _extract_error_message(self, error_data: Dict[str, Any], status_code: int) -> str:
        """Extract error message from response data."""
        # Common error message fields
        for field in ["message", "error", "error_description", "detail", "msg"]:
            if field in error_data:
                return str(error_data[field])

        # If nested under 'error' object
        if isinstance(error_data.get("error"), dict):
            error_obj = error_data["error"]
            for field in ["message", "description", "detail"]:
                if field in error_obj:
                    return str(error_obj[field])

        # Fallback to status code
        return f"HTTP {status_code} error"

    def _extract_error_code(self, error_data: Dict[str, Any]) -> Optional[str]:
        """Extract error code from response data."""
        for field in ["code", "error_code", "type", "error_type"]:
            if field in error_data:
                return str(error_data[field])

        if isinstance(error_data.get("error"), dict):
            error_obj = error_data["error"]
            for field in ["code", "type"]:
                if field in error_obj:
                    return str(error_obj[field])

        return None

    def _extract_retry_after(self, headers: Dict[str, str], error_data: Dict[str, Any]) -> Optional[int]:
        """Extract retry-after value from headers or response data."""
        # Check Retry-After header
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass

        # Check response data
        for field in ["retry_after", "retry_after_seconds", "reset_time"]:
            value = error_data.get(field)
            if value is not None:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    pass

        return None

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[ParamsDict] = None,
        data: Optional[RequestData] = None,
        json_data: Optional[JSONData] = None,
        headers: Optional[HeadersDict] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            json_data: JSON request body data
            headers: Additional headers
            timeout: Request timeout override

        Returns:
            HTTP response
        """

        def make_request() -> HTTPResponse:
            url = self.build_url(endpoint)
            prepared_headers = self.prepare_headers(headers)
            prepared_params = self.prepare_params(params)

            # Prepare request body
            if json_data is not None:
                request_data = json.dumps(json_data)
                prepared_headers["Content-Type"] = "application/json"
            else:
                request_data = data

            try:
                response = self._client.request(
                    method=method,
                    url=url,
                    params=prepared_params,
                    json=request_data,
                    headers=prepared_headers,
                    timeout=timeout or self.config.timeout,
                )
                return self._handle_response(response, endpoint)
            except httpx.TimeoutException:
                raise ServiceTimeoutError(self.service_name, timeout or self.config.timeout)
            except httpx.ConnectError as e:
                raise ServiceAPIError(
                    f"Failed to connect to {self.service_name}",
                    self.service_name,
                    endpoint=endpoint,
                ) from e

        return self.retry_handler.execute_with_retry(make_request, f"{method} {endpoint}")

    def get(
        self,
        endpoint: str,
        *,
        params: Optional[ParamsDict] = None,
        headers: Optional[HeadersDict] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a GET request."""
        return self.request("GET", endpoint, params=params, headers=headers, timeout=timeout)

    def post(
        self,
        endpoint: str,
        *,
        data: Optional[RequestData] = None,
        json_data: Optional[JSONData] = None,
        params: Optional[ParamsDict] = None,
        headers: Optional[HeadersDict] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a POST request."""
        return self.request(
            "POST",
            endpoint,
            data=data,
            json_data=json_data,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    def put(
        self,
        endpoint: str,
        *,
        data: Optional[RequestData] = None,
        json_data: Optional[JSONData] = None,
        params: Optional[ParamsDict] = None,
        headers: Optional[HeadersDict] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a PUT request."""
        return self.request(
            "PUT",
            endpoint,
            data=data,
            json_data=json_data,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    def patch(
        self,
        endpoint: str,
        *,
        data: Optional[RequestData] = None,
        json_data: Optional[JSONData] = None,
        params: Optional[ParamsDict] = None,
        headers: Optional[HeadersDict] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a PATCH request."""
        return self.request(
            "PATCH",
            endpoint,
            data=data,
            json_data=json_data,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    def delete(
        self,
        endpoint: str,
        *,
        params: Optional[ParamsDict] = None,
        headers: Optional[HeadersDict] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a DELETE request."""
        return self.request("DELETE", endpoint, params=params, headers=headers, timeout=timeout)

    def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        self._client.close()

    def __enter__(self) -> "HTTPClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
