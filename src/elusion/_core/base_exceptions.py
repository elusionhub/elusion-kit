"""Base exception hierarchy for all service SDKs."""

from typing import Optional, Dict, Any


class ElusionSDKError(Exception):
    """Base exception for all Elusion SDK errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ServiceAPIError(ElusionSDKError):
    """Base class for service API errors."""

    def __init__(
        self,
        message: str,
        service_name: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        request_id: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.service_name = service_name
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id
        self.response_data = response_data or {}
        self.endpoint = endpoint

    def __str__(self) -> str:
        parts = [f"{self.service_name} API Error: {self.message}"]

        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.error_code:
            parts.append(f"Code: {self.error_code}")
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")

        return " | ".join(parts)


class ServiceAuthenticationError(ServiceAPIError):
    """Authentication failed for the service."""

    def __init__(self, service_name: str, details: Optional[str] = None) -> None:
        message = f"Authentication failed for {service_name}"
        if details:
            message += f": {details}"
        super().__init__(message, service_name, status_code=401)


class ServiceAuthorizationError(ServiceAPIError):
    """Authorization failed for the service."""

    def __init__(self, service_name: str, resource: Optional[str] = None) -> None:
        message = f"Authorization failed for {service_name}"
        if resource:
            message += f" when accessing {resource}"
        super().__init__(message, service_name, status_code=403)


class ServiceRateLimitError(ServiceAPIError):
    """Rate limit exceeded for the service."""

    def __init__(
        self,
        service_name: str,
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
    ) -> None:
        self.retry_after = retry_after
        self.limit_type = limit_type

        message = f"{service_name} rate limit exceeded"
        if limit_type:
            message += f" ({limit_type})"
        if retry_after:
            message += f". Retry after {retry_after} seconds"

        super().__init__(message, service_name, status_code=429)


class ServiceValidationError(ElusionSDKError):
    """Request validation failed."""

    def __init__(self, message: str, field_errors: Optional[Dict[str, str]] = None) -> None:
        super().__init__(message)
        self.field_errors = field_errors or {}


class ServiceNotFoundError(ServiceAPIError):
    """Requested resource not found."""

    def __init__(self, service_name: str, resource_type: str, resource_id: str) -> None:
        message = f"{resource_type} '{resource_id}' not found in {service_name}"
        super().__init__(message, service_name, status_code=404)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ServiceTimeoutError(ServiceAPIError):
    """Request timed out."""

    def __init__(self, service_name: str, timeout_seconds: float) -> None:
        message = f"Request to {service_name} timed out after {timeout_seconds} seconds"
        super().__init__(message, service_name, status_code=408)
        self.timeout_seconds = timeout_seconds


class ServiceUnavailableError(ServiceAPIError):
    """Service is temporarily unavailable."""

    def __init__(self, service_name: str, retry_after: Optional[int] = None) -> None:
        message = f"{service_name} is temporarily unavailable"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, service_name, status_code=503)
        self.retry_after = retry_after
