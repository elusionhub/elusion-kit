# Getting Started

This guide will help you install Elusion and build your first SDK.

## Installation

### Requirements

- Python 3.13 or higher
- pip or your preferred package manager

### Install Elusion

```bash
pip install elusion
```

### Development Installation

If you're contributing to Elusion itself:

```bash
git clone https://github.com/elusionhub/elusion-kit
cd elusion-kit
pip install -e ".[dev,test,docs]"
```

## Your First SDK

Let's build a simple SDK for a fictional API service.

### Step 1: Basic Client

```python
# my_sdk/client.py
from elusion._core import BaseServiceClient, HTTPClient
from elusion._core.authentication import APIKeyAuthenticator
from elusion._core.configuration import ClientConfiguration, ServiceSettings

class ExampleSDKClient(BaseServiceClient):
    def __init__(self, api_key: str, base_url: str = "https://api.example.com"):
        # Configure the client
        config = ClientConfiguration(
            timeout=30.0,
            max_retries=3,
            retry_delay=1.0
        )

        # Configure the service
        settings = ServiceSettings(base_url=base_url)

        # Set up authentication
        authenticator = APIKeyAuthenticator(api_key)

        # Initialize base client
        super().__init__(
            config=config,
            service_settings=settings,
            authenticator=authenticator
        )

    def _get_service_name(self) -> str:
        return "ExampleAPI"

    def _get_base_url(self) -> str:
        return "https://api.example.com"
```

### Step 2: Data Models

```python
# my_sdk/models.py
from elusion._core.base_models import BaseServiceModel
from typing import Optional

class User(BaseServiceModel):
    id: str
    name: str
    email: str
    created_at: Optional[str] = None
```

### Step 3: API Resources

```python
# my_sdk/resources.py
from elusion._core.base_client import BaseResource
from .models import User

class UserResource(BaseResource):
    def get_user(self, user_id: str) -> User:
        response = self._http_client.get(f"/users/{user_id}")
        return User.model_validate(response.json())

    def create_user(self, name: str, email: str) -> User:
        data = {"name": name, "email": email}
        response = self._http_client.post("/users", json_data=data)
        return User.model_validate(response.json())
```

### Step 4: Complete the Client

```python
# Update client.py
from .resources import UserResource

class ExampleSDKClient(BaseServiceClient):
    def __init__(self, api_key: str, base_url: str = "https://api.example.com"):
        # ... same as before ...

        # Initialize resources
        self.users = UserResource(self._http_client)
```

### Step 5: Use Your SDK

```python
# Usage
from my_sdk import ExampleSDKClient

client = ExampleSDKClient("your-api-key")

# Get a user
user = client.users.get_user("123")
print(f"User: {user.name} ({user.email})")

# Create a user
new_user = client.users.create_user("John Doe", "john@example.com")
print(f"Created user: {new_user.id}")
```

## Package Structure

Organize your SDK package like this:

```
my-sdk/
├── src/
│   └── elusion/
│       └── exampleSDK/
│           ├── __init__.py
│           ├── client.py
│           ├── models/
│           │   ├── __init__.py
│           │   └── users.py
│           ├── resources/
│           │   ├── __init__.py
│           │   └── user_resource.py
│           ├── types/
│           │   ├── __init__.py
│           │   └── enums.py
│           ├── exceptions.py
│           └── authentication.py
├── tests/
├── examples/
├── pyproject.toml
└── README.md
```

## Package Configuration

Create a `pyproject.toml` file:

```toml
[project]
name = "elusion-exampleSDK"
dependencies = [
    "elusion>=1.0.0",
]

[tool.hatch.version]
path = "src/elusion/exampleSDK/__init__.py"
```

## Next Steps

- [Learn about core concepts](core-concepts.md)
- [Configure authentication](authentication.md)
- [Add error handling](error-handling.md)
- [See complete examples](examples/)
