# Configuration

Learn how to configure Elusion clients for different environments and use cases.

## Client Configuration

`ClientConfiguration` controls how the HTTP client behaves:

```python
from elusion._core.configuration import ClientConfiguration

config = ClientConfiguration(
    timeout=30.0,                    # Request timeout in seconds
    max_retries=3,                   # Maximum retry attempts
    retry_delay=1.0,                 # Base delay between retries
    retry_exponential_backoff=True,  # Use exponential backoff
    retry_jitter=True,               # Add random jitter to delays
    debug_requests=False,            # Log all requests/responses
    verify_ssl=True,                 # Verify SSL certificates
    custom_headers={}                # Additional headers for all requests
)
```

### Development vs Production

```python
# Development configuration
dev_config = ClientConfiguration(
    timeout=60.0,        # Longer timeout for debugging
    max_retries=1,       # Fewer retries for faster feedback
    debug_requests=True, # Log all requests
    verify_ssl=False     # Skip SSL verification for local APIs
)

# Production configuration
prod_config = ClientConfiguration(
    timeout=30.0,        # Standard timeout
    max_retries=5,       # More retries for reliability
    debug_requests=False,# No debug logging
    verify_ssl=True      # Always verify SSL
)
```

## Service Settings

`ServiceSettings` configures service-specific options:

```python
from elusion._core.configuration import ServiceSettings

settings = ServiceSettings(
    base_url="https://api.example.com",
    api_version="v2",
    rate_limit_per_second=10.0,
    custom_endpoints={
        "health": "/health-check",
        "metrics": "/internal/metrics"
    },
    service_specific_config={
        "enable_webhooks": True,
        "batch_size": 100
    }
)
```

### Environment-Based Configuration

```python
import os

def get_service_settings(environment: str) -> ServiceSettings:
    if environment == "production":
        return ServiceSettings(
            base_url="https://api.example.com",
            api_version="v1"
        )
    elif environment == "staging":
        return ServiceSettings(
            base_url="https://staging-api.example.com",
            api_version="v2"
        )
    else:  # development
        return ServiceSettings(
            base_url="http://localhost:8000",
            api_version="v2"
        )

# Usage
env = os.getenv("ENVIRONMENT", "development")
settings = get_service_settings(env)
```

## Retry Configuration

Configure retry behavior with `RetryConfig`:

```python
from elusion._core.retry_handler import RetryConfig, RetryStrategy

# Conservative retry policy
conservative_retry = RetryConfig(
    max_attempts=2,
    base_delay=0.5,
    strategy=RetryStrategy.FIXED
)

# Aggressive retry policy
aggressive_retry = RetryConfig(
    max_attempts=5,
    base_delay=1.0,
    max_delay=30.0,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    backoff_multiplier=2.0,
    jitter=True
)

# Custom retryable conditions
custom_retry = RetryConfig(
    max_attempts=3,
    retryable_status_codes=[408, 429, 500, 502, 503, 504],
    retryable_exceptions=[ConnectionError, TimeoutError]
)
```

## User Agent Configuration

Customize the User-Agent header:

```python
# Custom user agent
config = ClientConfiguration(
    user_agent="MySDK/1.0.0 (https://example.com)"
)

# Get default user agent
default_ua = config.get_user_agent("MyService")
# Returns: "elusion-myservice-sdk/1.0.0"
```

## Custom Headers

Add headers to all requests:

```python
config = ClientConfiguration(
    custom_headers={
        "X-Client-Version": "1.0.0",
        "X-Client-Platform": "python",
        "Accept-Encoding": "gzip, deflate"
    }
)
```

## Logging Configuration

Control logging levels:

```python
from elusion._core.configuration import LogLevel

config = ClientConfiguration(
    log_level=LogLevel.DEBUG,     # Log everything
    debug_requests=True           # Log HTTP requests/responses
)

# In production
prod_config = ClientConfiguration(
    log_level=LogLevel.WARNING,   # Only warnings and errors
    debug_requests=False          # No request logging
)
```

## Complete Example

```python
from elusion._core.configuration import ClientConfiguration, ServiceSettings
from elusion._core.authentication import APIKeyAuthenticator
from elusion._core import BaseServiceClient

class ExampleSDKClient(BaseServiceClient):
    def __init__(
        self,
        api_key: str,
        environment: str = "production",
        timeout: float = 30.0,
        debug: bool = False
    ):
        # Environment-specific settings
        if environment == "production":
            base_url = "https://api.example.com"
            max_retries = 5
        elif environment == "staging":
            base_url = "https://staging-api.example.com"
            max_retries = 3
        else:  # development
            base_url = "http://localhost:8000"
            max_retries = 1

        # Client configuration
        config = ClientConfiguration(
            timeout=timeout,
            max_retries=max_retries,
            debug_requests=debug,
            custom_headers={
                "X-SDK-Version": "1.0.0",
                "X-Environment": environment
            }
        )

        # Service settings
        settings = ServiceSettings(
            base_url=base_url,
            api_version="v1",
            service_specific_config={
                "environment": environment
            }
        )

        # Authentication
        authenticator = APIKeyAuthenticator(api_key)

        super().__init__(
            config=config,
            service_settings=settings,
            authenticator=authenticator
        )

    def _get_service_name(self) -> str:
        return "ExampleAPI"

    def _get_base_url(self) -> str:
        return self._service_settings.base_url

# Usage
client = ExampleSDKClient(
    api_key="your-key",
    environment="staging",
    timeout=60.0,
    debug=True
)
```

## Configuration Validation

Configurations are validated using Pydantic:

```python
from pydantic import ValidationError

try:
    config = ClientConfiguration(
        timeout=-1.0,  # Invalid: must be positive
        max_retries=20  # Invalid: too many retries
    )
except ValidationError as e:
    print("Configuration error:", e)
```

## Best Practices

1. **Use environment variables** for sensitive configuration
2. **Validate configuration** early in your application
3. **Provide sensible defaults** for optional parameters
4. **Document configuration options** in your SDK
5. **Test with different configurations** to ensure compatibility