# Testing

Learn how to test SDKs built with the Elusion framework using the provided testing utilities.

## Test Setup

### Basic Test Structure

```python
# tests/conftest.py
import pytest
from elusion._core.configuration import ClientConfiguration, ServiceSettings
from elusion._core.authentication import APIKeyAuthenticator
from my_sdk import ExampleSDKClient

@pytest.fixture
def test_config():
    return ClientConfiguration(
        timeout=5.0,
        max_retries=1,
        retry_delay=0.1,
        debug_requests=True
    )

@pytest.fixture
def test_settings():
    return ServiceSettings(base_url="https://api.test.example.com")

@pytest.fixture
def client(test_config, test_settings):
    return ExampleSDKClient(
        api_key="test-api-key",
        config=test_config,
        service_settings=test_settings
    )
```

## Mocking HTTP Requests

### Using respx

Use respx for mocking HTTP requests:

```python
import respx
import httpx
import pytest

@respx.mock
def test_get_user_success(client):
    # Mock the API response
    respx.get("https://api.test.example.com/users/123").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "123",
                "name": "John Doe",
                "email": "john@example.com"
            }
        )
    )

    # Test the SDK method
    user = client.users.get_user("123")

    # Assert the result
    assert user.id == "123"
    assert user.name == "John Doe"
    assert user.email == "john@example.com"

@respx.mock
def test_get_user_not_found(client):
    respx.get("https://api.test.example.com/users/999").mock(
        return_value=httpx.Response(
            404,
            json={"error": "User not found"}
        )
    )

    with pytest.raises(UserNotFoundError):
        client.users.get_user("999")
```

### Multiple Responses

Test retry logic with multiple responses:

```python
@respx.mock
def test_retry_on_server_error(client):
    respx.get("https://api.test.example.com/users/123").mock(
        side_effect=[
            httpx.Response(503, json={"error": "Service unavailable"}),
            httpx.Response(503, json={"error": "Service unavailable"}),
            httpx.Response(200, json={"id": "123", "name": "John"})
        ]
    )

    # Should succeed after retries
    user = client.users.get_user("123")
    assert user.name == "John"
```

## Testing Authentication

### API Key Authentication

```python
def test_api_key_authentication():
    from elusion._core.authentication import APIKeyAuthenticator

    auth = APIKeyAuthenticator("test-key-123")
    headers = auth.get_auth_headers()

    assert headers["Authorization"] == "Bearer test-key-123"

def test_custom_authentication():
    from my_sdk.authentication import CustomAuthenticator

    auth = CustomAuthenticator("key", "secret")
    headers = auth.get_auth_headers()

    assert "X-Custom-Key" in headers
    assert "X-Signature" in headers
```

### Authentication in Requests

```python
@respx.mock
def test_authentication_headers_sent(client):
    # Set up mock to capture request
    mock_request = respx.get("https://api.test.example.com/users/123").mock(
        return_value=httpx.Response(200, json={"id": "123", "name": "John"})
    )

    client.users.get_user("123")

    # Check that auth header was sent
    request = mock_request.calls[0].request
    assert request.headers["Authorization"] == "Bearer test-api-key"
```

## Testing Models

### Model Validation

```python
import pytest
from pydantic import ValidationError
from my_sdk.models import User

def test_user_model_valid():
    user = User(
        id="123",
        name="John Doe",
        email="john@example.com",
        active=True
    )

    assert user.id == "123"
    assert user.name == "John Doe"
    assert user.is_active()

def test_user_model_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        User(
            id="",  # Empty ID should fail
            name="John",
            email="invalid-email"  # Invalid email should fail
        )

    errors = exc_info.value.errors()
    assert len(errors) >= 2

def test_user_model_from_api_data():
    api_data = {
        "id": "123",
        "name": "John Doe",
        "email": "john@example.com",
        "active": True,
        "extra_field": "ignored"  # Should be ignored
    }

    user = User.model_validate(api_data)
    assert user.name == "John Doe"
```

### Model Methods

```python
def test_user_display_name():
    user = User(id="123", name="John Doe", email="john@example.com")
    assert user.display_name == "John Doe"

    user_no_name = User(id="123", name="", email="john@example.com")
    assert user_no_name.display_name == "john@example.com"

def test_user_serialization():
    user = User(id="123", name="John Doe", email="john@example.com")
    data = user.model_dump()

    expected = {
        "id": "123",
        "name": "John Doe",
        "email": "john@example.com",
        "active": True
    }
    assert data == expected
```

## Testing Error Handling

### Exception Handling

```python
@respx.mock
def test_rate_limit_error(client):
    respx.get("https://api.test.example.com/users/123").mock(
        return_value=httpx.Response(
            429,
            json={"error": "Rate limit exceeded"},
            headers={"Retry-After": "60"}
        )
    )

    with pytest.raises(ServiceRateLimitError) as exc_info:
        client.users.get_user("123")

    error = exc_info.value
    assert error.status_code == 429
    assert error.retry_after == 60

@respx.mock
def test_validation_error(client):
    respx.post("https://api.test.example.com/users").mock(
        return_value=httpx.Response(
            422,
            json={
                "error": "Validation failed",
                "field": "email",
                "message": "Invalid email format"
            }
        )
    )

    with pytest.raises(InvalidUserDataError) as exc_info:
        client.users.create_user({"name": "John", "email": "invalid"})

    error = exc_info.value
    assert error.field == "email"
    assert "Invalid email format" in str(error)
```

### Error Recovery

```python
@respx.mock
def test_error_recovery(client):
    # Mock primary endpoint failure and backup success
    respx.get("https://api.test.example.com/users/123").mock(
        return_value=httpx.Response(503, json={"error": "Service unavailable"})
    )
    respx.get("https://api.test.example.com/backup/users/123").mock(
        return_value=httpx.Response(200, json={"id": "123", "name": "John"})
    )

    user = client.users.get_user_with_fallback("123")
    assert user.name == "John"
```

## Testing Configuration

### Different Configurations

```python
def test_timeout_configuration():
    config = ClientConfiguration(timeout=1.0)
    client = ExampleSDKClient("test-key", config=config)

    assert client._config.timeout == 1.0

def test_retry_configuration():
    config = ClientConfiguration(max_retries=5, retry_delay=0.5)
    client = ExampleSDKClient("test-key", config=config)

    assert client._config.max_retries == 5
    assert client._config.retry_delay == 0.5
```

## Integration Testing

### Real API Testing

```python
@pytest.mark.integration
def test_real_api_connection():
    """Test against real API (requires API key)."""
    import os

    api_key = os.getenv("TEST_API_KEY")
    if not api_key:
        pytest.skip("TEST_API_KEY not set")

    client = ExampleSDKClient(api_key)

    # Test connection
    assert client.test_connection()

    # Test actual API call
    users = client.users.list_users(limit=1)
    assert isinstance(users, list)

@pytest.mark.integration
@pytest.mark.slow
def test_full_user_lifecycle():
    """Test complete user creation, update, deletion."""
    import os

    api_key = os.getenv("TEST_API_KEY")
    if not api_key:
        pytest.skip("TEST_API_KEY not set")

    client = ExampleSDKClient(api_key)

    # Create user
    user_data = {
        "name": "Test User",
        "email": f"test+{uuid4()}@example.com"
    }
    user = client.users.create_user(user_data)
    assert user.name == "Test User"

    try:
        # Update user
        updated_user = client.users.update_user(user.id, {"name": "Updated User"})
        assert updated_user.name == "Updated User"

        # Get user
        fetched_user = client.users.get_user(user.id)
        assert fetched_user.id == user.id
    finally:
        # Clean up
        client.users.delete_user(user.id)
```

## Performance Testing

### Load Testing

```python
import time
import threading
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.slow
def test_concurrent_requests(client):
    """Test SDK under concurrent load."""

    @respx.mock
    def make_requests():
        respx.get("https://api.test.example.com/users/123").mock(
            return_value=httpx.Response(200, json={"id": "123", "name": "John"})
        )

        def get_user():
            return client.users.get_user("123")

        # Run 20 concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_user) for _ in range(20)]
            results = [future.result() for future in futures]

        assert len(results) == 20
        assert all(user.name == "John" for user in results)

    make_requests()

@pytest.mark.slow
def test_rate_limiting_behavior(client):
    """Test how SDK handles rate limiting."""

    @respx.mock
    def test_rate_limit():
        # First few requests succeed, then rate limited
        responses = [
            httpx.Response(200, json={"id": "123", "name": "John"})
            for _ in range(3)
        ] + [
            httpx.Response(429, json={"error": "Rate limited"}, headers={"Retry-After": "1"})
            for _ in range(2)
        ]

        respx.get("https://api.test.example.com/users/123").mock(side_effect=responses)

        # First 3 should succeed
        for _ in range(3):
            user = client.users.get_user("123")
            assert user.name == "John"

        # Next should be rate limited
        with pytest.raises(ServiceRateLimitError):
            client.users.get_user("123")

    test_rate_limit()
```

## Test Organization

### Test Markers

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",
    "integration: Integration tests requiring API access",
    "slow: Slow running tests",
    "auth: Authentication-related tests",
    "models: Model validation tests",
    "errors: Error handling tests"
]

# Use markers in tests
@pytest.mark.unit
def test_model_validation():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_real_api():
    pass
```

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run with coverage
pytest --cov=my_sdk --cov-report=html

# Skip slow tests
pytest -m "not slow"
```

## Test Utilities

### Custom Fixtures

```python
# tests/conftest.py
@pytest.fixture
def sample_user_data():
    return {
        "id": "123",
        "name": "John Doe",
        "email": "john@example.com",
        "active": True
    }

@pytest.fixture
def mock_user_response(sample_user_data):
    return httpx.Response(200, json=sample_user_data)

@pytest.fixture
def authenticated_client():
    return ExampleSDKClient("test-api-key")
```

### Helper Functions

```python
# tests/helpers.py
def create_mock_response(status_code=200, data=None, headers=None):
    return httpx.Response(
        status_code,
        json=data or {},
        headers=headers or {}
    )

def assert_user_equal(user1, user2):
    assert user1.id == user2.id
    assert user1.name == user2.name
    assert user1.email == user2.email
```

## Best Practices

1. **Use respx for HTTP mocking** in unit tests
2. **Test both success and error cases** for all methods
3. **Mock at the HTTP level**, not the SDK level
4. **Use markers** to organize different test types
5. **Test with realistic data** that matches your API
6. **Include integration tests** for critical functionality
7. **Test error recovery** and retry logic
8. **Validate authentication** is working correctly
