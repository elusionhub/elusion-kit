# Models

Elusion uses Pydantic for data validation and serialization. Learn how to create robust models for your SDK.

## Base Models

All models should inherit from framework base models:

```python
from elusion._core.base_models import BaseServiceModel

class User(BaseServiceModel):
    id: str
    name: str
    email: str
    active: bool = True
```

## Model Types

### Basic Models

For simple data structures:

```python
class Product(BaseServiceModel):
    id: str
    name: str
    price: float
    description: str = ""

    def formatted_price(self) -> str:
        return f"${self.price:.2f}"
```

### Timestamped Models

For resources with creation/update times:

```python
from elusion._core.base_models import TimestampedModel

class Order(TimestampedModel):
    id: str
    customer_id: str
    total: float
    status: str

    # Automatically includes:
    # created_at: Optional[datetime]
    # updated_at: Optional[datetime]
```

### Identifiable Models

For resources with required IDs:

```python
from elusion._core.base_models import IdentifiableModel

class Account(IdentifiableModel):
    name: str
    balance: float

    # Automatically includes:
    # id: str (required)
```

### Metadata Models

For resources supporting metadata:

```python
from elusion._core.base_models import MetadataModel

class Campaign(MetadataModel):
    name: str
    description: str

    # Automatically includes:
    # metadata: Dict[str, Any] = {}
```

## Field Validation

Use Pydantic validators for complex validation:

```python
from pydantic import field_validator, Field
from typing import Optional

class User(BaseServiceModel):
    id: str
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    age: Optional[int] = Field(None, ge=0, le=150)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip().title()

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.lower().strip()
```

## Enums and Types

Define custom types and enums:

```python
from enum import Enum
from typing import Literal

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Type aliases
UserID = str
OrderStatus = Literal["pending", "paid", "shipped", "delivered"]

class User(BaseServiceModel):
    id: UserID
    status: UserStatus
    priority: Priority = Priority.MEDIUM
```

## Nested Models

Create complex nested structures:

```python
class Address(BaseServiceModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"

class Customer(BaseServiceModel):
    id: str
    name: str
    email: str
    billing_address: Address
    shipping_address: Optional[Address] = None

    def get_display_address(self) -> Address:
        return self.shipping_address or self.billing_address
```

## Collections and Lists

Handle lists of models:

```python
from typing import List

class OrderItem(BaseServiceModel):
    product_id: str
    quantity: int
    price: float

class Order(BaseServiceModel):
    id: str
    customer_id: str
    items: List[OrderItem]

    @property
    def total(self) -> float:
        return sum(item.price * item.quantity for item in self.items)

    def add_item(self, product_id: str, quantity: int, price: float) -> None:
        item = OrderItem(product_id=product_id, quantity=quantity, price=price)
        self.items.append(item)
```

## Paginated Responses

Use the framework's pagination model:

```python
from elusion._core.base_models import PaginatedResponse

# Generic paginated response
UserListResponse = PaginatedResponse[User]

# Custom paginated response
class CustomUserListResponse(BaseServiceModel):
    users: List[User]
    total_users: int
    page: int
    per_page: int
    has_next: bool

    @property
    def total_pages(self) -> int:
        return (self.total_users + self.per_page - 1) // self.per_page
```

## API Response Wrappers

Wrap API responses consistently:

```python
from elusion._core.base_models import APIResponse

# Generic response wrapper
class UserResponse(APIResponse[User]):
    pass

# Custom response with metadata
class CreateUserResponse(BaseServiceModel):
    user: User
    welcome_email_sent: bool
    account_setup_url: str
```

## Model Methods

Add useful methods to your models:

```python
class User(BaseServiceModel):
    id: str
    first_name: str
    last_name: str
    email: str
    created_at: datetime

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        return self.full_name or self.email

    def is_recent(self, days: int = 7) -> bool:
        cutoff = datetime.now() - timedelta(days=days)
        return self.created_at > cutoff

    def to_dict(self) -> dict:
        return self.model_dump()

    def __str__(self) -> str:
        return self.display_name
```

## Serialization

Control how models are serialized:

```python
from pydantic import ConfigDict

class User(BaseServiceModel):
    model_config = ConfigDict(
        # Include all fields when serializing
        exclude_none=False,
        # Use enum values instead of enum objects
        use_enum_values=True,
        # Allow extra fields in input
        extra='ignore'
    )

    id: str
    name: str
    internal_field: str = Field(exclude=True)  # Never serialize

    def to_public_dict(self) -> dict:
        # Custom serialization excluding sensitive fields
        return self.model_dump(exclude={'internal_field'})
```

## Model Conversion

Convert between different model types:

```python
class UserCreateRequest(BaseServiceModel):
    name: str
    email: str
    password: str

class User(BaseServiceModel):
    id: str
    name: str
    email: str
    created_at: datetime

    @classmethod
    def from_create_request(cls, request: UserCreateRequest, user_id: str) -> "User":
        return cls(
            id=user_id,
            name=request.name,
            email=request.email,
            created_at=datetime.now()
        )

# Usage
create_request = UserCreateRequest(name="John", email="john@example.com", password="secret")
user = User.from_create_request(create_request, "user_123")
```

## Error Models

Model validation errors:

```python
from elusion._core.base_models import ValidationErrorDetail, ValidationErrorResponse

class UserValidationError(BaseServiceModel):
    field: str
    message: str
    code: str

class UserCreateErrorResponse(BaseServiceModel):
    error: str
    validation_errors: List[UserValidationError] = []
```

## Testing Models

Test your models thoroughly:

```python
import pytest
from pydantic import ValidationError

def test_user_creation():
    user = User(id="123", name="John", email="john@example.com")
    assert user.full_name == "John"
    assert user.display_name == "John"

def test_user_validation():
    with pytest.raises(ValidationError) as exc_info:
        User(id="", name="", email="invalid-email")

    errors = exc_info.value.errors()
    assert len(errors) > 0

def test_user_serialization():
    user = User(id="123", name="John", email="john@example.com")
    data = user.model_dump()

    assert data["id"] == "123"
    assert data["name"] == "John"
```

## Best Practices

1. **Use appropriate base models** for your data types
2. **Add validation** for business rules
3. **Include helpful methods** for common operations
4. **Document fields** with descriptions
5. **Test model validation** thoroughly
6. **Use enums** for fixed value sets
7. **Keep models focused** on single responsibilities
