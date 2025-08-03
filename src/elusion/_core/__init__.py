"""Core infrastructure for all Elusion service SDKs.

This module provides the shared foundation that all service SDKs build upon,
including HTTP clients, authentication patterns, base models, and utilities.
"""

from .base_client import BaseServiceClient
from .http_client import HTTPClient, HTTPResponse
from .authentication import (
    BaseAuthenticator,
    APIKeyAuthenticator,
    BearerTokenAuthenticator,
)
from .base_models import BaseServiceModel, PaginatedResponse, BaseRequest, APIResponse
from .base_exceptions import (
    ElusionSDKError,
    ServiceAPIError,
    ServiceAuthenticationError,
    ServiceRateLimitError,
    ServiceValidationError,
    ServiceNotFoundError,
)
from .retry_handler import RetryHandler, RetryStrategy
from .configuration import ClientConfiguration, ServiceSettings

__all__ = [
    # Base classes
    "BaseServiceClient",
    "HTTPClient",
    "HTTPResponse",
    # Authentication
    "BaseAuthenticator",
    "APIKeyAuthenticator",
    "BearerTokenAuthenticator",
    # Models
    "BaseServiceModel",
    "PaginatedResponse",
    "BaseRequest",
    "APIResponse",
    # Exceptions
    "ElusionSDKError",
    "ServiceAPIError",
    "ServiceAuthenticationError",
    "ServiceRateLimitError",
    "ServiceValidationError",
    "ServiceNotFoundError",
    # Utilities
    "RetryHandler",
    "RetryStrategy",
    "ClientConfiguration",
    "ServiceSettings",
]
