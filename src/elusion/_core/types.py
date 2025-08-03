"""Core type definitions and protocols."""

from typing import Protocol, TypeVar, Dict, Any, Union
from abc import abstractmethod
from .base_models import BaseServiceModel

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound="BaseServiceModel")

HeadersDict = Dict[str, str]
ParamsDict = Dict[str, Union[str, int, float, bool]]
JSONData = Dict[str, Any]
RequestData = Union[str, bytes, JSONData]


class AuthenticatorProtocol(Protocol):
    """Protocol for authentication handlers."""

    @abstractmethod
    def get_auth_headers(self) -> HeadersDict:
        """Get headers required for authentication."""
        ...

    @abstractmethod
    def authenticate_request(self, headers: HeadersDict) -> HeadersDict:
        """Add authentication to request headers."""
        ...


class SerializerProtocol(Protocol):
    """Protocol for request/response serialization."""

    @abstractmethod
    def serialize_request(self, data: Any) -> RequestData:
        """Serialize request data."""
        ...

    @abstractmethod
    def deserialize_response(self, content: bytes, content_type: str) -> Any:
        """Deserialize response content."""
        ...
