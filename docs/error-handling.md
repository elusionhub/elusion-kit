# Error Handling

Robust error handling is crucial for good SDK design. Elusion provides a comprehensive exception hierarchy and patterns.

## Exception Hierarchy

All SDK exceptions inherit from framework base exceptions:

```python
from elusion._core.base_exceptions import (
    ElusionSDKError,           # Base for all SDK errors
    ServiceAPIError,           # API-related errors
    ServiceAuthenticationError, # Authentication failures
    ServiceRateLimitError,     # Rate limiting
    ServiceTimeoutError,       # Request timeouts
    ServiceUnavailableError,   # Service downtime
    ServiceNotFoundError,      # Resource not found
    ServiceValidationError     # Input validation errors
)
```

## Creating Custom Exceptions

Create service-specific exceptions:

```python
from elusion._core.base_exceptions import ServiceAPIError, ServiceNotFoundError

class ExampleSDKError(ServiceAPIError):
    """Base exception for ExampleSDK."""

    def __init__(self, message: str, **kwargs):
        # Ensure service_name is always set
        kwargs.setdefault('service_name', 'ExampleAPI')
        super().__init__(message, **kwargs)

class UserNotFoundError(ServiceNotFoundError):
    """User not found in the system."""

    def __init__(self, user_id: str):
        super().__init__("ExampleAPI", "User", user_id)

class InvalidUserDataError(ExampleSDKError):
    """Invalid user data provided."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Invalid {field}: {reason}")

class QuotaExceededError(ExampleSDKError):
    """API quota exceeded."""

    def __init__(self, quota_type: str, reset_time: int):
        self.quota_type = quota_type
        self.reset_time = reset_time
        super().__init__(
            f"Quota exceeded for {quota_type}. Resets at {reset_time}",
            status_code=429
        )
```

## Handling Errors in Resources

Handle errors at the resource level:

```python
from elusion._core.base_client import BaseResource
from .exceptions import UserNotFoundError, InvalidUserDataError
from .models import User

class UserResource(BaseResource):
    def get_user(self, user_id: str) -> User:
        try:
            response = self._http_client.get(f"/users/{user_id}")
            return User.model_validate(response.json())
        except ServiceAPIError as e:
            if e.status_code == 404:
                raise UserNotFoundError(user_id) from e
            raise  # Re-raise other API errors

    def create_user(self, user_data: dict) -> User:
        try:
            response = self._http_client.post("/users", json_data=user_data)
            return User.model_validate(response.json())
        except ServiceAPIError as e:
            if e.status_code == 422:
                # Parse validation errors from response
                error_data = e.response_data or {}
                field = error_data.get('field', 'unknown')
                reason = error_data.get('message', 'validation failed')
                raise InvalidUserDataError(field, reason) from e
            raise
```

## Error Context

Provide rich error context:

```python
class DetailedAPIError(ExampleSDKError):
    """API error with rich context."""

    def __init__(
        self,
        message: str,
        status_code: int = None,
        error_code: str = None,
        request_id: str = None,
        endpoint: str = None,
        request_data: dict = None
    ):
        super().__init__(
            message,
            status_code=status_code,
            error_code=error_code,
            request_id=request_id,
            endpoint=endpoint
        )
        self.request_data = request_data

    def __str__(self) -> str:
        parts = [f"ExampleAPI Error: {self.message}"]

        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.error_code:
            parts.append(f"Code: {self.error_code}")
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")

        return " | ".join(parts)
```

## Client-Level Error Handling

Handle errors at the client level:

```python
class ExampleSDKClient(BaseServiceClient):
    def _handle_common_errors(self, func, *args, **kwargs):
        """Common error handling for all operations."""
        try:
            return func(*args, **kwargs)
        except ServiceAuthenticationError:
            # Log and re-raise auth errors
            logger.error("Authentication failed for ExampleAPI")
            raise
        except ServiceRateLimitError as e:
            # Log rate limit with details
            logger.warning(f"Rate limited by ExampleAPI. Retry after {e.retry_after}s")
            raise
        except ServiceTimeoutError:
            # Log timeout
            logger.error("Request to ExampleAPI timed out")
            raise
        except Exception as e:
            # Log unexpected errors
            logger.exception("Unexpected error in ExampleAPI client")
            raise

    def safe_get_user(self, user_id: str) -> Optional[User]:
        """Get user with automatic error handling."""
        try:
            return self.users.get_user(user_id)
        except UserNotFoundError:
            return None  # Return None instead of raising
        except ExampleSDKError:
            logger.exception(f"Failed to get user {user_id}")
            return None
```

## Retry Logic with Custom Errors

Customize retry behavior based on errors:

```python
from elusion._core.retry_handler import RetryConfig

# Configure what errors should trigger retries
retry_config = RetryConfig(
    max_attempts=3,
    retryable_exceptions=[
        ServiceTimeoutError,
        ServiceUnavailableError,
        ServiceRateLimitError,
        ConnectionError,
        # Add your custom retryable errors
        TemporaryServiceError,
    ]
)
```

## Validation Errors

Handle input validation errors:

```python
from pydantic import ValidationError

class UserResource(BaseResource):
    def create_user(self, user_data: dict) -> User:
        # Validate input before sending request
        try:
            create_request = CreateUserRequest.model_validate(user_data)
        except ValidationError as e:
            raise InvalidUserDataError(
                field="input",
                reason=f"Validation failed: {e}"
            ) from e

        # Make API request
        response = self._http_client.post("/users", json_data=create_request.model_dump())
        return User.model_validate(response.json())
```

## Error Recovery

Implement error recovery strategies:

```python
class ResilientUserResource(BaseResource):
    def get_user_with_fallback(self, user_id: str) -> Optional[User]:
        """Get user with fallback strategies."""

        # Try primary endpoint
        try:
            return self.get_user(user_id)
        except ServiceTimeoutError:
            # Try with longer timeout
            response = self._http_client.get(
                f"/users/{user_id}",
                timeout=60.0
            )
            return User.model_validate(response.json())
        except ServiceUnavailableError:
            # Try backup endpoint
            try:
                response = self._http_client.get(f"/backup/users/{user_id}")
                return User.model_validate(response.json())
            except ServiceAPIError:
                # If backup also fails, return None
                return None
        except UserNotFoundError:
            return None
```

## Error Logging

Implement comprehensive error logging:

```python
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class LoggingResource(BaseResource):
    def _log_error(
        self,
        operation: str,
        error: Exception,
        context: Dict[str, Any] = None
    ) -> None:
        """Log error with context."""
        context = context or {}

        if isinstance(error, ServiceAPIError):
            logger.error(
                f"API error in {operation}: {error.message}",
                extra={
                    "operation": operation,
                    "status_code": error.status_code,
                    "error_code": error.error_code,
                    "request_id": error.request_id,
                    "endpoint": error.endpoint,
                    **context
                }
            )
        else:
            logger.exception(
                f"Unexpected error in {operation}: {error}",
                extra={"operation": operation, **context}
            )

    def get_user(self, user_id: str) -> User:
        try:
            response = self._http_client.get(f"/users/{user_id}")
            return User.model_validate(response.json())
        except Exception as e:
            self._log_error("get_user", e, {"user_id": user_id})
            raise
```

## Testing Error Handling

Test your error handling:

```python
import pytest
from unittest.mock import patch
import respx

def test_user_not_found_error(client):
    with respx.mock:
        respx.get("https://api.example.com/users/999").mock(
            return_value=httpx.Response(404, json={"error": "User not found"})
        )

        with pytest.raises(UserNotFoundError) as exc_info:
            client.users.get_user("999")

        assert exc_info.value.resource_id == "999"

def test_rate_limit_handling(client):
    with respx.mock:
        respx.get("https://api.example.com/users/123").mock(
            return_value=httpx.Response(
                429,
                json={"error": "Rate limit exceeded"},
                headers={"Retry-After": "60"}
            )
        )

        with pytest.raises(ServiceRateLimitError) as exc_info:
            client.users.get_user("123")

        assert exc_info.value.retry_after == 60

def test_error_recovery(client):
    with respx.mock:
        # First call fails
        respx.get("https://api.example.com/users/123").mock(
            side_effect=[
                httpx.Response(503, json={"error": "Service unavailable"}),
                httpx.Response(200, json={"id": "123", "name": "John"})
            ]
        )

        # Should succeed after retry
        user = client.users.get_user("123")
        assert user.name == "John"
```

## Best Practices

1. **Create specific exceptions** for different error scenarios
2. **Provide rich context** in error messages
3. **Log errors appropriately** for debugging
4. **Handle retryable vs non-retryable** errors differently
5. **Document error conditions** in your SDK
6. **Test error scenarios** thoroughly
7. **Consider error recovery** strategies for critical operations
