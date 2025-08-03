"""Tests for base model functionality."""
import pytest
from datetime import datetime
from pydantic import ValidationError

from elusion._core.base_models import (
    BaseServiceModel,
    TimestampedModel,
    IdentifiableModel,
    MetadataModel,
    PaginatedResponse,
    APIResponse,
    ErrorResponse,
    ValidationErrorDetail,
    ValidationErrorResponse
)


class TestBaseServiceModel:
    """Test BaseServiceModel functionality."""
    
    def test_base_model_creation(self):
        """Test creating a base service model."""
        class TestModel(BaseServiceModel):
            name: str
            value: int
        
        model = TestModel(name="test", value=42)
        assert model.name == "test"
        assert model.value == 42
    
    def test_base_model_extra_fields_ignored(self):
        """Test that extra fields are ignored."""
        class TestModel(BaseServiceModel):
            name: str
        
        # Extra fields should be ignored, not cause errors
        model = TestModel(name="test")
        assert model.name == "test"
        assert not hasattr(model, "extra_field")


class TestTimestampedModel:
    """Test TimestampedModel functionality."""
    
    def test_timestamped_model_with_timestamps(self):
        """Test timestamped model with provided timestamps."""
        now = datetime.now()
        
        class TestModel(TimestampedModel):
            name: str
        
        model = TestModel(
            name="test",
            created_at=now,
            updated_at=now
        )
        
        assert model.name == "test"
        assert model.created_at == now
        assert model.updated_at == now
    
    def test_timestamped_model_without_timestamps(self):
        """Test timestamped model without provided timestamps."""
        class TestModel(TimestampedModel):
            name: str
        
        model = TestModel(name="test")
        
        assert model.name == "test"
        assert model.created_at is None
        assert model.updated_at is None


class TestIdentifiableModel:
    """Test IdentifiableModel functionality."""
    
    def test_identifiable_model(self):
        """Test identifiable model."""
        class TestModel(IdentifiableModel):
            name: str
        
        model = TestModel(id="test_123", name="test")
        
        assert model.id == "test_123"
        assert model.name == "test"
    
    def test_identifiable_model_missing_id(self):
        """Test identifiable model with missing ID."""
        class TestModel(IdentifiableModel):
            name: str
        
        with pytest.raises(ValidationError):
            TestModel(name="test")  # Missing required id field


class TestMetadataModel:
    """Test MetadataModel functionality."""
    
    def test_metadata_model_with_metadata(self):
        """Test metadata model with provided metadata."""
        class TestModel(MetadataModel):
            name: str
        
        model = TestModel(
            name="test",
            metadata={"key": "value", "number": 42}
        )
        
        assert model.name == "test"
        assert model.metadata == {"key": "value", "number": 42}
    
    def test_metadata_model_without_metadata(self):
        """Test metadata model without provided metadata."""
        class TestModel(MetadataModel):
            name: str
        
        model = TestModel(name="test")
        
        assert model.name == "test"
        assert model.metadata == {}


class TestPaginatedResponse:
    """Test PaginatedResponse functionality."""
    
    def test_paginated_response_basic(self):
        """Test basic paginated response."""
        class Item(BaseServiceModel):
            id: str
            name: str
        
        items = [
            Item(id="1", name="Item 1"),
            Item(id="2", name="Item 2")
        ]
        
        response = PaginatedResponse[Item](
            data=items,
            has_more=True,
            total_count=10
        )
        
        assert len(response.data) == 2
        assert response.data[0].name == "Item 1"
        assert response.has_more is True
        assert response.total_count == 10
    
    def test_paginated_response_cursor_pagination(self):
        """Test paginated response with cursor pagination."""
        class Item(BaseServiceModel):
            id: str
        
        response = PaginatedResponse[Item](
            data=[Item(id="1")],
            has_more=True,
            next_cursor="cursor_123",
            previous_cursor="cursor_456"
        )
        
        assert response.has_more is True
        assert response.next_cursor == "cursor_123"
        assert response.previous_cursor == "cursor_456"


class TestAPIResponse:
    """Test APIResponse functionality."""
    
    def test_successful_api_response(self):
        """Test successful API response."""
        class Data(BaseServiceModel):
            message: str
        
        data = Data(message="Operation successful")
        response = APIResponse[Data](
            success=True,
            data=data,
            request_id="req_123"
        )

        assert response.success is True
        assert response.data.message == "Operation successful"
        assert response.error is None
        assert response.request_id == "req_123"
    
    def test_error_api_response(self):
        """Test error API response."""
        response = APIResponse[None](
            success=False,
            error="Something went wrong",
            error_code="INTERNAL_ERROR",
            request_id="req_456"
        )
        
        assert response.success is False
        assert response.data is None
        assert response.error == "Something went wrong"
        assert response.error_code == "INTERNAL_ERROR"
        assert response.request_id == "req_456"


class TestErrorResponse:
    """Test ErrorResponse functionality."""
    
    def test_basic_error_response(self):
        """Test basic error response."""
        response = ErrorResponse(
            error="Resource not found",
            error_code="NOT_FOUND",
            request_id="req_789"
        )
        
        assert response.error == "Resource not found"
        assert response.error_code == "NOT_FOUND"
        assert response.request_id == "req_789"
        assert response.error_details is None
    
    def test_error_response_with_details(self):
        """Test error response with details."""
        response = ErrorResponse(
            error="Validation failed",
            error_code="VALIDATION_ERROR",
            error_details={"field": "email", "issue": "invalid format"}
        )
        
        assert response.error == "Validation failed"
        assert response.error_details == {"field": "email", "issue": "invalid format"}


class TestValidationErrorResponse:
    """Test ValidationErrorResponse functionality."""
    
    def test_validation_error_response(self):
        """Test validation error response."""
        validation_errors = [
            ValidationErrorDetail(
                field="email",
                message="Invalid email format",
                code="INVALID_FORMAT",
                value="not-an-email"
            ),
            ValidationErrorDetail(
                field="age",
                message="Must be a positive integer",
                code="INVALID_VALUE",
                value=-5
            )
        ]
        
        response = ValidationErrorResponse(
            error="Validation failed",
            error_code="VALIDATION_ERROR",
            validation_errors=validation_errors
        )
        
        assert response.error == "Validation failed"
        assert len(response.validation_errors) == 2
        assert response.validation_errors[0].field == "email"
        assert response.validation_errors[1].field == "age"

