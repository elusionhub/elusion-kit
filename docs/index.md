# Elusion Framework

A modern Python framework for building high-quality, type-safe API SDKs with comprehensive error handling and retry logic.

## What is Elusion?

Elusion is a framework that provides the infrastructure needed to build professional API SDKs. It handles the common patterns like HTTP clients, authentication, retry logic, error handling, and data validation, so you can focus on implementing your specific API's business logic.

## Key Features

- **Type Safe**: Full type hints with strict mypy configuration
- **Robust Error Handling**: Comprehensive exception hierarchy with detailed context
- **Automatic Retries**: Configurable retry strategies with exponential backoff
- **Flexible Authentication**: Extensible authentication patterns
- **Modern Python**: Built for Python 3.13+ with latest features
- **Well Tested**: High test coverage with comprehensive test utilities
- **Developer Friendly**: Meaningful naming patterns and clear abstractions

## Quick Example

```python
from elusion._core import BaseServiceClient, HTTPClient
from elusion._core.authentication import APIKeyAuthenticator
from elusion._core.configuration import ClientConfiguration, ServiceSettings

class ExampleSDKClient(BaseServiceClient):
    def __init__(self, api_key: str):
        config = ClientConfiguration(timeout=30.0, max_retries=3)
        settings = ServiceSettings(base_url="https://api.example.com")
        authenticator = APIKeyAuthenticator(api_key)

        super().__init__(
            config=config,
            service_settings=settings,
            authenticator=authenticator
        )

    def _get_service_name(self) -> str:
        return "ExampleAPI"

    def _get_base_url(self) -> str:
        return "https://api.example.com"

# Usage
client = ExampleSDKClient("your-api-key")
```

## Documentation Structure

- [Getting Started](getting-started.md) - Installation and basic setup
- [Core Concepts](core-concepts.md) - Understanding the framework architecture
- [Configuration](configuration.md) - Configuring clients and services
- [Authentication](authentication.md) - Authentication patterns and implementations
- [HTTP Client](http-client.md) - Making HTTP requests with retry logic
- [Models](models.md) - Data models and validation
- [Error Handling](error-handling.md) - Exception handling and custom errors
- [Testing](testing.md) - Testing SDKs built with Elusion
- [Examples](examples/) - Complete SDK examples
- [API Reference](api-reference/) - Detailed API documentation

## Who Should Use Elusion?

- **SDK Developers**: Building client libraries for REST APIs
- **API Providers**: Creating official SDKs for your services
- **Enterprise Teams**: Standardizing API client patterns across projects
- **Open Source Maintainers**: Building high-quality community SDKs

## Next Steps

1. [Install Elusion](getting-started.md#installation)
2. [Build your first SDK](getting-started.md#your-first-sdk)
3. [Explore the examples](examples/)
