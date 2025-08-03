# Core Concepts

Understanding these concepts will help you build better SDKs with Elusion.

## Architecture Overview

Elusion follows a layered architecture:

```
Your SDK
├── Client (BaseServiceClient)
├── Resources (BaseResource)
├── Models (BaseServiceModel)
└── Framework Layer
    ├── HTTP Client
    ├── Authentication
    ├── Retry Logic
    └── Configuration
```

## Base Service Client

The `BaseServiceClient` is the main entry point for your SDK.

```python
class MySDKClient(BaseServiceClient):
    def __init__(self, api_key: str):
        config = ClientConfiguration(timeout=30.0)
        settings = ServiceSettings(base_url="https://api.example.com")
        authenticator = APIKeyAuthenticator(api_key)

        super().__init__(
            config=config,
            service_settings=settings,
            authenticator=authenticator
        )

        # Initialize your resources
        self.users = UserResource(self._http_client)
        self.orders = OrderResource(self._http_client)
```

### Required Methods

Every client must implement:

```python
def _get_service_name(self) -> str:
    return "MyAPI"  # Used for error messages and logging

def _get_base_url(self) -> str:
    return "https://api.example.com"  # Default base URL
```

## Resources

Resources organize related API endpoints. Each resource inherits from `BaseResource`.

```python
class UserResource(BaseResource):
    def list_users(self, page: int = 1) -> List[User]:
        response = self._http_client.get("/users", params={"page": page})
        users_data = response.json()
        return [User.model_validate(user) for user in users_data]

    def get_user(self, user_id: str) -> User:
        response = self._http_client.get(f"/users/{user_id}")
        return User.model_validate(response.json())

    def create_user(self, user_data: dict) -> User:
        response = self._http_client.post("/users", json_data=user_data)
        return User.model_validate(response.json())
```

### Naming Conventions

Use meaningful, action-oriented names:

- `get_user()` instead of `user()`
- `create_order()` instead of `post_order()`
- `list_products()` instead of `products()`
- `delete_account()` instead of `remove()`

## Models

Models represent API data structures using Pydantic.

```python
from elusion._core.base_models import BaseServiceModel, TimestampedModel
from typing import Optional

class User(TimestampedModel):  # Includes created_at, updated_at
    id: str
    name: str
    email: str
    status: UserStatus
    metadata: dict = {}

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE
```

### Model Inheritance

Use framework base models:

```python
# Basic model
class Product(BaseServiceModel):
    name: str
    price: float

# Model with timestamps
class Order(TimestampedModel):
    id: str
    total: float

# Model with ID
class Customer(IdentifiableModel):
    name: str
    email: str

# Model with metadata support
class Campaign(MetadataModel):
    name: str
    description: str
```

## Configuration

Configure your SDK with `ClientConfiguration` and `ServiceSettings`.

```python
# Client configuration (shared across all requests)
config = ClientConfiguration(
    timeout=60.0,
    max_retries=5,
    retry_delay=2.0,
    debug_requests=True
)

# Service-specific configuration
settings = ServiceSettings(
    base_url="https://api.example.com/v2",
    api_version="2.1",
    rate_limit_per_second=10.0,
    custom_endpoints={
        "health": "/status"
    }
)
```

## Authentication

Elusion provides several authentication patterns:

```python
# API Key authentication
auth = APIKeyAuthenticator("your-api-key")

# Bearer token
auth = BearerTokenAuthenticator("your-token")

# Basic authentication
auth = BasicAuthenticator("username", "password")

# Custom authentication
class CustomAuth(BaseAuthenticator):
    def get_auth_headers(self) -> dict:
        return {"X-Custom-Auth": "custom-value"}
```

## Error Handling

Create service-specific exceptions:

```python
from elusion._core.base_exceptions import ServiceAPIError

class MySDKError(ServiceAPIError):
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('service_name', 'MyAPI')
        super().__init__(message, **kwargs)

class UserNotFoundError(MySDKError):
    def __init__(self, user_id: str):
        super().__init__(f"User {user_id} not found", status_code=404)
```

## HTTP Client

The framework provides a configured HTTP client with:

- Automatic retries with exponential backoff
- Request/response logging
- Connection pooling
- Timeout handling

```python
# In your resources
response = self._http_client.get("/endpoint")
response = self._http_client.post("/endpoint", json_data=data)
response = self._http_client.put("/endpoint", json_data=data)
response = self._http_client.delete("/endpoint")
```

## Type Safety

Use type hints throughout your SDK:

```python
from typing import List, Optional, Dict, Any

def get_users(self, active_only: bool = True) -> List[User]:
    params: Dict[str, Any] = {"active": active_only}
    response = self._http_client.get("/users", params=params)
    return [User.model_validate(user) for user in response.json()]

def get_user(self, user_id: str) -> Optional[User]:
    try:
        response = self._http_client.get(f"/users/{user_id}")
        return User.model_validate(response.json())
    except UserNotFoundError:
        return None
```

## Testing

Elusion provides testing utilities:

```python
import pytest
from elusion._core.configuration import ClientConfiguration
from my_sdk import MySDKClient

@pytest.fixture
def client():
    config = ClientConfiguration(timeout=1.0, max_retries=1)
    return MySDKClient("test-key", config=config)

def test_get_user(client, respx_mock):
    respx_mock.get("https://api.example.com/users/123").mock(
        return_value=httpx.Response(200, json={"id": "123", "name": "John"})
    )

    user = client.users.get_user("123")
    assert user.name == "John"
```

## Best Practices

1. **Use meaningful names** for methods and classes
2. **Validate inputs** with Pydantic models
3. **Handle errors gracefully** with specific exceptions
4. **Document methods** with clear docstrings
5. **Test thoroughly** with framework utilities
6. **Follow Python conventions** for naming and structure
