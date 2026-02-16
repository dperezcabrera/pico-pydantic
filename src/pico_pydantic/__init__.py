"""pico-pydantic: Declarative, AOP-based Pydantic validation for pico-ioc.

This package provides automatic argument validation for pico-ioc managed
components using Pydantic ``BaseModel`` type hints. It intercepts method
calls via AOP and validates arguments with ``TypeAdapter.validate_python()``
before the method body executes.

Public API:
    validate: Marker decorator that enables validation on a method.
    ValidationFailedError: Exception raised when argument validation fails.
    ValidationInterceptor: Singleton MethodInterceptor that performs validation.

Auto-discovery:
    Registered via the ``pico_boot.modules`` entry point. When using
    ``pico-boot``, the ``ValidationInterceptor`` is auto-discovered and
    globally registered with the container.

Example:
    >>> from pydantic import BaseModel, Field
    >>> from pico_ioc import component
    >>> from pico_pydantic import validate
    >>>
    >>> class UserCreate(BaseModel):
    ...     username: str = Field(min_length=3)
    ...     email: str
    >>>
    >>> @component
    ... class UserService:
    ...     @validate
    ...     async def create_user(self, data: UserCreate) -> dict:
    ...         return data.model_dump()
"""

from .decorators import ValidationFailedError, validate
from .interceptor import ValidationInterceptor

__all__ = ["validate", "ValidationFailedError", "ValidationInterceptor"]
