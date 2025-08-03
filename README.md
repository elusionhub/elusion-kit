# Elusion Kit

![Elusion Kit Logo](docs/assets/elusion-kit-logo.png)

A modern Python framework for building high-quality, type-safe API SDKs with comprehensive error handling and retry logic.

## What is Elusion Kit?

Elusion Kit is a framework that provides the infrastructure needed to build professional API SDKs. It handles the common patterns like HTTP clients, authentication, retry logic, error handling, and data validation, so you can focus on implementing your specific API's business logic.

## Key Features

- **Type Safe**: Full type hints with strict mypy configuration
- **Robust Error Handling**: Comprehensive exception hierarchy with detailed context
- **Automatic Retries**: Configurable retry strategies with exponential backoff
- **Flexible Authentication**: Extensible authentication patterns for any API
- **Modern Python**: Built for Python 3.13+ with latest features
- **Well Tested**: High test coverage with comprehensive test utilities
- **Developer Friendly**: Meaningful naming patterns and clear abstractions

## Quick Start

```python
from elusion._core import BaseServiceClient, HTTPClient
from elusion._core.authentication import APIKeyAuthenticator
from elusion._core.configuration import ClientConfiguration, ServiceSettings

class MySDKClient(BaseServiceClient):
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
        return "MyAPI"

    def _get_base_url(self) -> str:
        return "https://api.example.com"

# Usage
client = MySDKClient("your-api-key")
```

## Installation

```bash
pip install elusion-kit
```

## Documentation

- [Getting Started](docs/getting-started.md) - Build your first SDK
- [Core Concepts](docs/core-concepts.md) - Understanding the framework
- [Configuration](docs/configuration.md) - Client and service configuration
- [Authentication](docs/authentication.md) - Authentication patterns
- [HTTP Client](docs/http-client.md) - Making requests with retry logic
- [Models](docs/models.md) - Data models and validation
- [Error Handling](docs/error-handling.md) - Exception handling patterns
- [Testing](docs/testing.md) - Testing your SDKs
- [Examples](docs/examples/) - Complete SDK examples
- [API Reference](docs/api-reference/) - Detailed API documentation

## Who Should Use Elusion Kit?

- **SDK Developers**: Building client libraries for REST APIs
- **API Providers**: Creating official SDKs for your services
- **Enterprise Teams**: Standardizing API client patterns across projects
- **Open Source Maintainers**: Building high-quality community SDKs

## Example SDKs Built with Elusion

- [elusion-jokes](https://github.com/elusionhub/elusion-kit-examples/elusion-jokes) - Sample APIs Jokes SDK

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- [Documentation](docs/)
- [Issues](https://github.com/elusionhub/elusion-kit/issues)
- [Discussions](https://github.com/elusionhub/elusion-kit/discussions)
