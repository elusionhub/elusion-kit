"""Base models for all service SDKs."""

from datetime import datetime
from typing import Annotated, Optional, Dict, Any, Generic, TypeVar, List
from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")


class BaseServiceModel(BaseModel):
    """Base model for all service API responses.

    Provides common patterns and validation for all service models.
    """

    model_config = ConfigDict(
        # Allow extra fields for forward compatibility
        extra="ignore",
        # Use enum values instead of enum objects in serialization
        use_enum_values=True,
        # Validate assignments after model creation
        validate_assignment=True,
        # Allow population by field name or alias
        populate_by_name=True,
    )


class TimestampedModel(BaseServiceModel):
    """Model with timestamp fields."""

    created_at: Optional[datetime] = Field(default=None, description="When the resource was created")
    updated_at: Optional[datetime] = Field(default=None, description="When the resource was last updated")


class IdentifiableModel(BaseServiceModel):
    """Model with an ID field."""

    id: str = Field(..., description="Unique identifier for the resource")


class MetadataModel(BaseServiceModel):
    """Model that supports metadata."""

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata associated with the resource")


class BaseRequest(BaseServiceModel):
    """Base model for API request data."""

    pass


class PaginatedResponse(BaseServiceModel, Generic[T]):
    """Generic paginated response model that adapts to different service patterns."""

    # Core pagination fields that most services support
    data: List[T] = Field(..., description="List of items in this page")
    has_more: bool = Field(..., description="Whether there are more results available")

    # Optional fields that services can use if supported
    total_count: Optional[int] = Field(default=None, description="Total number of items across all pages")
    page_size: Optional[int] = Field(default=None, description="Number of items per page")
    current_page: Optional[int] = Field(default=None, description="Current page number (1-based)")
    total_pages: Optional[int] = Field(default=None, description="Total number of pages")

    # Cursor-based pagination
    next_cursor: Optional[str] = Field(default=None, description="Cursor for the next page")
    previous_cursor: Optional[str] = Field(default=None, description="Cursor for the previous page")

    # URL-based pagination
    next_url: Optional[str] = Field(default=None, description="URL for the next page")
    previous_url: Optional[str] = Field(default=None, description="URL for the previous page")

    # Offset-based pagination
    offset: Optional[int] = Field(default=None, description="Current offset")
    limit: Optional[int] = Field(default=None, description="Items per page limit")


class APIResponse(BaseServiceModel, Generic[T]):
    """Standard wrapper for API responses."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if request failed")
    error_code: Optional[str] = Field(default=None, description="Specific error code")
    request_id: Optional[str] = Field(default=None, description="Unique request identifier")
    timestamp: Optional[datetime] = Field(default=None, description="Response timestamp")


class ErrorResponse(BaseServiceModel):
    """Standard error response model."""

    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Specific error code")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    request_id: Optional[str] = Field(default=None, description="Request identifier")
    timestamp: Optional[datetime] = Field(default=None, description="Error timestamp")


class ValidationErrorDetail(BaseServiceModel):
    """Details about a validation error."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    code: Optional[str] = Field(default=None, description="Validation error code")
    value: Optional[Any] = Field(default=None, description="Value that failed validation")


class ValidationErrorResponse(ErrorResponse):
    """Response for validation errors."""

    validation_errors: Annotated[
        List[ValidationErrorDetail],
        Field(default_factory=list, description="List of field validation errors"),
    ]
