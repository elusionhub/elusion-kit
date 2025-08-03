# Examples

This directory contains complete examples of SDKs built with the Elusion framework.

## Available Examples

### Basic Examples

- [Simple SDK](simple-sdk.md) - Minimal SDK implementation

## Quick Start Example

Here's a minimal SDK to get you started:

```python
from elusion._core import BaseServiceClient
from elusion._core.authentication import APIKeyAuthenticator
from elusion._core.configuration import ClientConfiguration, ServiceSettings
from elusion._core.base_models import BaseServiceModel
from elusion._core.base_client import BaseResource

# Data model
class User(BaseServiceModel):
    id: str
    name: str
    email: str

# Resource for API operations
class UserResource(BaseResource):
    def get_user(self, user_id: str) -> User:
        response = self._http_client.get(f"/users/{user_id}")
        return User.model_validate(response.json())

# Main client
class SimpleSDK(BaseServiceClient):
    def __init__(self, api_key: str):
        config = ClientConfiguration()
        settings = ServiceSettings(base_url="https://api.example.com")
        auth = APIKeyAuthenticator(api_key)

        super().__init__(
            config=config,
            service_settings=settings,
            authenticator=auth
        )

        self.users = UserResource(self._http_client)

    def _get_service_name(self) -> str:
        return "SimpleAPI"

    def _get_base_url(self) -> str:
        return "https://api.example.com"

# Usage
client = SimpleSDK("your-api-key")
user = client.users.get_user("123")
print(f"User: {user.name}")
```

For more detailed examples, see the individual example files.
