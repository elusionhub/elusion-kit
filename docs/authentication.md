# Authentication

Elusion provides flexible authentication patterns for different API requirements.

## Built-in Authenticators

### API Key Authentication

Most common for REST APIs:

```python
from elusion._core.authentication import APIKeyAuthenticator

# Default: Authorization: Bearer {api_key}
auth = APIKeyAuthenticator("your-api-key")

# Custom header name
auth = APIKeyAuthenticator(
    api_key="your-key",
    header_name="X-API-Key",
    header_prefix=""  # No prefix
)

# Custom prefix
auth = APIKeyAuthenticator(
    api_key="your-key",
    header_prefix="Token"
)
```

### Bearer Token Authentication

For OAuth and JWT tokens:

```python
from elusion._core.authentication import BearerTokenAuthenticator

auth = BearerTokenAuthenticator("your-bearer-token")
# Sends: Authorization: Bearer your-bearer-token
```

### Basic Authentication

For username/password authentication:

```python
from elusion._core.authentication import BasicAuthenticator

auth = BasicAuthenticator("username", "password")
# Sends: Authorization: Basic {base64(username:password)}
```

### OAuth Authentication

For OAuth access tokens:

```python
from elusion._core.authentication import OAuthAuthenticator

# Default Bearer token
auth = OAuthAuthenticator("access-token")

# Custom token type
auth = OAuthAuthenticator("access-token", token_type="Token")
```

## Custom Authentication

Create custom authenticators for specific requirements:

```python
from elusion._core.authentication import BaseAuthenticator
from typing import Dict

class HMACAuthenticator(BaseAuthenticator):
    def __init__(self, access_key: str, secret_key: str):
        self.access_key = access_key
        self.secret_key = secret_key

    def get_auth_headers(self) -> Dict[str, str]:
        import hmac
        import hashlib
        import time

        timestamp = str(int(time.time()))
        signature = hmac.new(
            self.secret_key.encode(),
            f"{self.access_key}{timestamp}".encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            "X-Access-Key": self.access_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }

# Usage
auth = HMACAuthenticator("access-key", "secret-key")
```

### AWS Signature v4

For AWS-style authentication:

```python
class AWSSignatureAuthenticator(BaseAuthenticator):
    def __init__(self, access_key: str, secret_key: str, region: str, service: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.service = service

    def get_auth_headers(self) -> Dict[str, str]:
        # Implement AWS Signature Version 4
        # This is a simplified example
        return {
            "Authorization": f"AWS4-HMAC-SHA256 Credential={self.access_key}",
            "X-Amz-Date": "20230101T000000Z"
        }
```

### JWT Authentication

For JSON Web Tokens:

```python
class JWTAuthenticator(BaseAuthenticator):
    def __init__(self, private_key: str, algorithm: str = "RS256"):
        self.private_key = private_key
        self.algorithm = algorithm

    def get_auth_headers(self) -> Dict[str, str]:
        import jwt
        import time

        payload = {
            "iss": "your-app",
            "exp": int(time.time()) + 3600,  # 1 hour
            "iat": int(time.time())
        }

        token = jwt.encode(payload, self.private_key, algorithm=self.algorithm)
        return {"Authorization": f"Bearer {token}"}
```

## No Authentication

For public APIs:

```python
class NoAuthAuthenticator(BaseAuthenticator):
    def get_auth_headers(self) -> Dict[str, str]:
        return {}

    def authenticate_request(self, headers: Dict[str, str]) -> Dict[str, str]:
        return headers  # Pass through unchanged
```

## Authentication in Client

Use authenticators in your client:

```python
class ExampleSDKClient(BaseServiceClient):
    def __init__(self, api_key: str):
        # Choose appropriate authenticator
        authenticator = APIKeyAuthenticator(api_key)

        config = ClientConfiguration()
        settings = ServiceSettings(base_url="https://api.example.com")

        super().__init__(
            config=config,
            service_settings=settings,
            authenticator=authenticator
        )
```

## Multiple Authentication Methods

Support different auth methods:

```python
from typing import Union

class FlexibleSDKClient(BaseServiceClient):
    def __init__(
        self,
        auth: Union[str, Dict[str, str], BaseAuthenticator],
        base_url: str = "https://api.example.com"
    ):
        # Handle different auth types
        if isinstance(auth, str):
            authenticator = APIKeyAuthenticator(auth)
        elif isinstance(auth, dict):
            if "username" in auth and "password" in auth:
                authenticator = BasicAuthenticator(auth["username"], auth["password"])
            else:
                raise ValueError("Invalid auth dictionary")
        elif isinstance(auth, BaseAuthenticator):
            authenticator = auth
        else:
            raise ValueError("Invalid authentication type")

        config = ClientConfiguration()
        settings = ServiceSettings(base_url=base_url)

        super().__init__(
            config=config,
            service_settings=settings,
            authenticator=authenticator
        )

# Usage examples
client1 = FlexibleSDKClient("api-key")
client2 = FlexibleSDKClient({"username": "user", "password": "pass"})
client3 = FlexibleSDKClient(CustomAuthenticator())
```

## Error Handling

Authentication errors are handled automatically:

```python
from elusion._core.base_exceptions import ServiceAuthenticationError

try:
    user = client.users.get_user("123")
except ServiceAuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Handle re-authentication or token refresh
```

## Token Refresh

Implement token refresh for OAuth:

```python
class RefreshableOAuthAuthenticator(BaseAuthenticator):
    def __init__(self, access_token: str, refresh_token: str, client_id: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.token_expires_at = None

    def get_auth_headers(self) -> Dict[str, str]:
        if self._token_expired():
            self._refresh_token()

        return {"Authorization": f"Bearer {self.access_token}"}

    def _token_expired(self) -> bool:
        if not self.token_expires_at:
            return False
        return time.time() >= self.token_expires_at

    def _refresh_token(self) -> None:
        # Make request to refresh endpoint
        # Update self.access_token and self.token_expires_at
        pass
```

## Testing Authentication

Test your authentication:

```python
def test_api_key_auth():
    auth = APIKeyAuthenticator("test-key")
    headers = auth.get_auth_headers()

    assert headers["Authorization"] == "Bearer test-key"

def test_custom_auth():
    auth = CustomAuthenticator("key", "secret")
    headers = auth.get_auth_headers()

    assert "X-Custom-Header" in headers
```

## Best Practices

1. **Store credentials securely** - use environment variables
2. **Handle auth errors gracefully** - implement retry logic
3. **Support token refresh** - for OAuth workflows
4. **Validate credentials early** - fail fast on invalid auth
5. **Test authentication** - verify headers are correct
6. **Document auth requirements** - make it clear for users
