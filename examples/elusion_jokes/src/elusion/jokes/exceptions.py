from typing import Any, Optional
from elusion._core.base_exceptions import ServiceAPIError, ServiceNotFoundError, ServiceUnavailableError, ElusionSDKError


class JokesError(ElusionSDKError):
    """Base exception for Jokes SDK errors."""

    pass


class JokesAPIError(ServiceAPIError):
    """API error from the Jokes service."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        # Ensure service_name is set
        kwargs.setdefault("service_name", "SampleAPIsJokes")
        super().__init__(message, **kwargs)


class JokesNotFoundError(ServiceNotFoundError):
    """Requested joke was not found."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__("SampleAPIsJokes", resource_type, resource_id)


class JokesServiceUnavailableError(ServiceUnavailableError):
    """Jokes service is temporarily unavailable."""

    def __init__(self, retry_after: Optional[int] = None) -> None:
        super().__init__("SampleAPIsJokes", retry_after)


class JokesValidationError(JokesError):
    """Validation error for joke data."""

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        super().__init__(message)
        self.field = field
