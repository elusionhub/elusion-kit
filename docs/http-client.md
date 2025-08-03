# HTTP Client

The Elusion HTTP client provides robust request handling with automatic retries, error handling, and response processing.

## Basic Usage

In your resources, use the HTTP client:

```python
class UserResource(BaseResource):
    def get_user(self, user_id: str) -> User:
        response = self._http_client.get(f"/users/{user_id}")
        return User.model_validate(response.json())

    def create_user(self, user_data: dict) -> User:
        response = self._http_client.post("/users", json_data=user_data)
        return User.model_validate(response.json())
```

## HTTP Methods

All standard HTTP methods are supported:

```python
# GET request
response = self._http_client.get("/users")
response = self._http_client.get("/users", params={"page": 1, "limit": 10})

# POST request
response = self._http_client.post("/users", json_data={"name": "John"})
response = self._http_client.post("/users", data="raw data")

# PUT request
response = self._http_client.put("/users/123", json_data={"name": "Jane"})

# PATCH request
response = self._http_client.patch("/users/123", json_data={"status": "active"})

# DELETE request
response = self._http_client.delete("/users/123")
```

## Request Parameters

### Query Parameters

```python
# Simple parameters
response = self._http_client.get("/users", params={
    "page": 1,
    "limit": 20,
    "active": True
})

# Parameters are automatically converted to strings
# None values are filtered out
params = {"search": "john", "category": None}  # category won't be sent
response = self._http_client.get("/search", params=params)
```

### Request Body

```python
# JSON data (automatically serialized)
user_data = {"name": "John", "email": "john@example.com"}
response = self._http_client.post("/users", json_data=user_data)

# Raw data
response = self._http_client.post("/upload", data=b"binary data")

# String data
response = self._http_client.post("/webhook", data="payload")
```

### Custom Headers

```python
# Additional headers for specific requests
headers = {"X-Custom-Header": "value"}
response = self._http_client.get("/users", headers=headers)

# Headers are merged with authentication and default headers
```

### Timeouts

```python
# Override default timeout for specific requests
response = self._http_client.get("/slow-endpoint", timeout=120.0)
```

## Response Handling

The HTTP client returns `HTTPResponse` objects:

```python
response = self._http_client.get("/users/123")

# Response properties
print(response.status_code)  # 200
print(response.headers)      # {"content-type": "application/json"}
print(response.url)          # "https://api.example.com/users/123"
print(response.request_id)   # "req_abc123" (if provided by API)

# Response body
print(response.text)         # Raw text
print(response.content)      # Raw bytes
data = response.json()       # Parsed JSON

# Status checks
if response.is_success():
    print("Request succeeded")
elif response.is_client_error():
    print("Client error (4xx)")
elif response.is_server_error():
    print("Server error (5xx)")
```

## Error Handling

The HTTP client automatically handles common errors:

```python
from elusion._core.base_exceptions import (
    ServiceAPIError,
    ServiceRateLimitError,
    ServiceTimeoutError,
    ServiceUnavailableError
)

try:
    response = self._http_client.get("/users/123")
    user = User.model_validate(response.json())
except ServiceRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ServiceTimeoutError as e:
    print(f"Request timed out after {e.timeout_seconds} seconds")
except ServiceUnavailableError as e:
    print(f"Service unavailable. Retry after {e.retry_after} seconds")
except ServiceAPIError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
```

## Automatic Retries

The HTTP client automatically retries failed requests:

```python
# These are retried automatically:
# - Network errors (ConnectionError, TimeoutError)
# - Server errors (500, 502, 503, 504)
# - Rate limits (429)
# - Request timeouts (408)

# These are NOT retried:
# - Client errors (400, 401, 403, 404)
# - Successful responses (2xx)
```

### Retry Configuration

Configure retry behavior in your client:

```python
from elusion._core.configuration import ClientConfiguration

config = ClientConfiguration(
    max_retries=5,              # Maximum retry attempts
    retry_delay=2.0,            # Base delay between retries
    retry_exponential_backoff=True,  # Use exponential backoff
    retry_jitter=True           # Add random jitter
)
```

### Retry Strategies

```python
# Fixed delay: 1s, 1s, 1s
config = ClientConfiguration(
    retry_delay=1.0,
    retry_exponential_backoff=False,
    retry_jitter=False
)

# Exponential backoff: 1s, 2s, 4s, 8s
config = ClientConfiguration(
    retry_delay=1.0,
    retry_exponential_backoff=True,
    retry_jitter=False
)

# With jitter: 1s±10%, 2s±10%, 4s±10%
config = ClientConfiguration(
    retry_delay=1.0,
    retry_exponential_backoff=True,
    retry_jitter=True
)
```

## Rate Limiting

The client respects rate limit headers:

```python
# If API returns:
# HTTP 429 Too Many Requests
# Retry-After: 60

# The client will:
# 1. Automatically wait 60 seconds
# 2. Retry the request
# 3. Raise ServiceRateLimitError if max retries exceeded
```

## URL Building

The client automatically builds URLs:

```python
# Base URL: https://api.example.com

# These are equivalent:
response = self._http_client.get("/users")
response = self._http_client.get("users")  # Leading slash optional

# Full URLs are passed through:
response = self._http_client.get("https://other-api.com/data")
```

## Connection Management

The HTTP client manages connections automatically:

```python
# Connections are pooled and reused
# Close when done (usually in client.__exit__)
def close(self) -> None:
    self._http_client.close()

# Context manager support
with MySDKClient("api-key") as client:
    users = client.users.list_users()
# Client is automatically closed
```

## Debugging

Enable request/response logging:

```python
config = ClientConfiguration(debug_requests=True)

# This will log:
# - Request method, URL, headers, body
# - Response status, headers, body
# - Timing information
```

## Advanced Usage

### Custom Request Processing

```python
class CustomResource(BaseResource):
    def make_custom_request(self):
        # Build custom request
        headers = {"X-Custom": "value"}
        params = {"filter": "active"}

        response = self._http_client.request(
            method="GET",
            endpoint="/custom",
            headers=headers,
            params=params,
            timeout=60.0
        )

        return response.json()
```

### Response Streaming

For large responses:

```python
# Note: Streaming support would be added in future versions
# Current version loads full response into memory
```

### Compression

The client supports response compression:

```python
# Automatically sends: Accept-Encoding: gzip, deflate
# Automatically decompresses responses
```

## Best Practices

1. **Use appropriate HTTP methods** for operations
2. **Handle errors gracefully** with try/catch blocks
3. **Set reasonable timeouts** for your use case
4. **Log errors with context** for debugging
5. **Validate responses** before processing
6. **Close clients** when done to free resources
