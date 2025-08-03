# Simple SDK Example

This example shows how to build a minimal SDK for a hypothetical user management API.

## API Overview

The ExampleAPI provides basic user management:

- GET /users/{id} - Get user by ID
- POST /users - Create user
- PUT /users/{id} - Update user
- DELETE /users/{id} - Delete user

## Implementation

### Project Structure

```
simple-sdk/
├── src/
│   └── elusion/
│       └── exampleSDK/
│           ├── __init__.py
│           ├── client.py
│           ├── models.py
│           ├── resources.py
│           └── exceptions.py
├── tests/
└── pyproject.toml
```

### Models

```python
# src/elusion/exampleSDK/models.py
from elusion._core.base_models import BaseServiceModel, TimestampedModel
from typing import Optional

class User(TimestampedModel):
    id: str
    name: str
    email: str
    active: bool = True

    @property
    def display_name(self) -> str:
        return self.name or self.email

class CreateUserRequest(BaseServiceModel):
    name: str
    email: str
    active: bool = True

class UpdateUserRequest(BaseServiceModel):
    name: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = None
```

### Exceptions

```python
# src/elusion/exampleSDK/exceptions.py
from elusion._core.base_exceptions import ServiceAPIError, ServiceNotFoundError

class ExampleSDKError(ServiceAPIError):
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('service_name', 'ExampleAPI')
        super().__init__(message, **kwargs)

class UserNotFoundError(ServiceNotFoundError):
    def __init__(self, user_id: str):
        super().__init__("ExampleAPI", "User", user_id)

class DuplicateEmailError(ExampleSDKError):
    def __init__(self, email: str):
        super().__init__(f"User with email {email} already exists", status_code=409)
```

### Resources

```python
# src/elusion/exampleSDK/resources.py
from typing import List
from elusion._core.base_client import BaseResource
from .models import User, CreateUserRequest, UpdateUserRequest
from .exceptions import UserNotFoundError, DuplicateEmailError, ExampleSDKError

class UserResource(BaseResource):
    def get_user(self, user_id: str) -> User:
        """Get a user by ID."""
        try:
            response = self._http_client.get(f"/users/{user_id}")
            return User.model_validate(response.json())
        except ServiceAPIError as e:
            if e.status_code == 404:
                raise UserNotFoundError(user_id) from e
            raise

    def create_user(self, user_data: CreateUserRequest) -> User:
        """Create a new user."""
        try:
            response = self._http_client.post(
                "/users",
                json_data=user_data.model_dump()
            )
            return User.model_validate(response.json())
        except ServiceAPIError as e:
            if e.status_code == 409:
                raise DuplicateEmailError(user_data.email) from e
            raise

    def update_user(self, user_id: str, user_data: UpdateUserRequest) -> User:
        """Update an existing user."""
        try:
            response = self._http_client.put(
                f"/users/{user_id}",
                json_data=user_data.model_dump(exclude_none=True)
            )
            return User.model_validate(response.json())
        except ServiceAPIError as e:
            if e.status_code == 404:
                raise UserNotFoundError(user_id) from e
            raise

    def delete_user(self, user_id: str) -> None:
        """Delete a user."""
        try:
            self._http_client.delete(f"/users/{user_id}")
        except ServiceAPIError as e:
            if e.status_code == 404:
                raise UserNotFoundError(user_id) from e
            raise

    def list_users(self, active_only: bool = True) -> List[User]:
        """List all users."""
        params = {"active": active_only} if active_only else {}
        response = self._http_client.get("/users", params=params)

        users_data = response.json()
        return [User.model_validate(user) for user in users_data]
```

### Client

```python
# src/elusion/exampleSDK/client.py
from elusion._core import BaseServiceClient
from elusion._core.authentication import APIKeyAuthenticator
from elusion._core.configuration import ClientConfiguration, ServiceSettings
from .resources import UserResource

class ExampleSDKClient(BaseServiceClient):
    """Simple SDK client for ExampleAPI."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.example.com",
        timeout: float = 30.0
    ):
        # Configure client
        config = ClientConfiguration(timeout=timeout, max_retries=3)
        settings = ServiceSettings(base_url=base_url)
        auth = APIKeyAuthenticator(api_key)

        # Initialize base client
        super().__init__(
            config=config,
            service_settings=settings,
            authenticator=auth
        )

        # Initialize resources
        self.users = UserResource(self._http_client)

    def _get_service_name(self) -> str:
        return "ExampleAPI"

    def _get_base_url(self) -> str:
        return "https://api.example.com"
```

### Package Exports

```python
# src/elusion/exampleSDK/__init__.py
"""Simple SDK for ExampleAPI."""

from .client import ExampleSDKClient
from .models import User, CreateUserRequest, UpdateUserRequest
from .exceptions import (
    ExampleSDKError,
    UserNotFoundError,
    DuplicateEmailError
)

__all__ = [
    "ExampleSDKClient",
    "User",
    "CreateUserRequest",
    "UpdateUserRequest",
    "ExampleSDKError",
    "UserNotFoundError",
    "DuplicateEmailError"
]

__version__ = "1.0.0"
```

## Usage Examples

### Basic Usage

```python
from elusion.exampleSDK import ExampleSDKClient, CreateUserRequest

# Initialize client
client = ExampleSDKClient("your-api-key")

# Create a user
user_request = CreateUserRequest(
    name="John Doe",
    email="john@example.com"
)
user = client.users.create_user(user_request)
print(f"Created user: {user.id}")

# Get the user
retrieved_user = client.users.get_user(user.id)
print(f"User name: {retrieved_user.name}")

# List all users
all_users = client.users.list_users()
print(f"Total users: {len(all_users)}")
```

### Error Handling

```python
from elusion.exampleSDK.exceptions import UserNotFoundError, DuplicateEmailError

try:
    user = client.users.get_user("nonexistent")
except UserNotFoundError:
    print("User not found")

try:
    # Try to create user with duplicate email
    duplicate_user = CreateUserRequest(
        name="Jane Doe",
        email="john@example.com"  # Same email as before
    )
    client.users.create_user(duplicate_user)
except DuplicateEmailError as e:
    print(f"Email already exists: {e}")
```

### Update and Delete

```python
from elusion.exampleSDK import UpdateUserRequest

# Update user
update_request = UpdateUserRequest(name="John Smith")
updated_user = client.users.update_user(user.id, update_request)
print(f"Updated name: {updated_user.name}")

# Delete user
client.users.delete_user(user.id)
print("User deleted")
```

## Package Configuration

```toml
# pyproject.toml
[project]
name = "elusion-exampleSDK"
dependencies = ["elusion>=1.0.0"]

[tool.hatch.version]
path = "src/elusion/exampleSDK/__init__.py"
```

## Testing

```python
# tests/test_client.py
import pytest
import respx
import httpx
from elusion.exampleSDK import ExampleSDKClient, UserNotFoundError

@pytest.fixture
def client():
    return ExampleSDKClient("test-api-key", base_url="https://api.test.example.com")

@respx.mock
def test_get_user_success(client):
    respx.get("https://api.test.example.com/users/123").mock(
        return_value=httpx.Response(200, json={
            "id": "123",
            "name": "John Doe",
            "email": "john@example.com",
            "active": True,
            "created_at": "2024-01-01T00:00:00Z"
        })
    )

    user = client.users.get_user("123")
    assert user.name == "John Doe"
    assert user.email == "john@example.com"

@respx.mock
def test_get_user_not_found(client):
    respx.get("https://api.test.example.com/users/999").mock(
        return_value=httpx.Response(404, json={"error": "User not found"})
    )

    with pytest.raises(UserNotFoundError):
        client.users.get_user("999")
```

This simple SDK demonstrates all the core patterns:

- Type-safe models with validation
- Resource-based API organization
- Proper error handling with custom exceptions
- Clean client interface
- Comprehensive testing

You can use this as a template for building your own SDKs with the Elusion framework.
