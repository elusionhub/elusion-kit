"""Configuration management for service clients."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LogLevel(str, Enum):
    """Logging levels for the SDK."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ClientConfiguration(BaseModel):
    """Base configuration for all service clients."""

    timeout: float = Field(default=30.0, description="Request timeout in seconds", gt=0)
    max_retries: int = Field(
        default=3, description="Maximum number of retry attempts", ge=0, le=10
    )
    retry_delay: float = Field(
        default=1.0, description="Base delay between retries in seconds", gt=0
    )
    retry_exponential_backoff: bool = Field(
        default=True, description="Use exponential backoff for retries"
    )
    retry_jitter: bool = Field(
        default=True, description="Add random jitter to retry delays"
    )
    user_agent: Optional[str] = Field(
        default=None, description="Custom user agent string"
    )
    log_level: LogLevel = Field(
        default=LogLevel.WARNING, description="Logging level for the SDK"
    )
    debug_requests: bool = Field(
        default=False, description="Log all HTTP requests and responses"
    )
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    custom_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional headers to include in all requests",
    )

    def get_user_agent(self, service_name: str) -> str:
        """Get the user agent string for requests."""
        if self.user_agent:
            return self.user_agent

        # Import here to avoid circular imports
        try:
            from .. import __version__

            return f"elusion-{service_name.lower()}-sdk/{__version__}"
        except ImportError:
            return f"elusion-{service_name.lower()}-sdk/unknown"


class ServiceSettings(BaseModel):
    """Service-specific settings that can override base configuration."""

    base_url: str = Field(..., description="Base URL for the service API")
    api_version: Optional[str] = Field(default=None, description="API version to use")
    rate_limit_per_second: Optional[float] = Field(
        default=None, description="Rate limit for the service"
    )
    custom_endpoints: Dict[str, str] = Field(
        default_factory=dict, description="Custom endpoint URLs for specific operations"
    )
    service_specific_config: Dict[str, Any] = Field(
        default_factory=dict, description="Service-specific configuration options"
    )
