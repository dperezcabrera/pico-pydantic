"""Decorators and exceptions for pico-pydantic validation.

This module provides:
    - The ``@validate`` marker decorator that flags methods for argument
      validation by the ``ValidationInterceptor``.
    - The ``ValidationFailedError`` exception raised when Pydantic
      validation fails on a method argument.
"""

from typing import Callable, TypeVar

T = TypeVar("T", bound=Callable)

VALIDATE_META = "_pico_pydantic_validate_meta"
"""str: Hidden attribute name set on functions by ``@validate``.

The ``ValidationInterceptor`` checks for this attribute to determine
whether a method should undergo argument validation.
"""


class ValidationFailedError(ValueError):
    """Exception raised when Pydantic validation fails on method arguments.

    Wraps the underlying Pydantic ``ValidationError`` with the name of the
    method that triggered the failure. Inherits from ``ValueError`` so it
    can be caught broadly as a value-related error.

    Attributes:
        method_name: The name of the method whose arguments failed validation.
        pydantic_error: The original Pydantic ``ValidationError`` instance.

    Message format:
        ``"Validation failed for method '<method_name>': <pydantic_error>"``

    Example:
        >>> from pico_pydantic import ValidationFailedError
        >>> try:
        ...     await service.create_user({"username": "ab"})
        ... except ValidationFailedError as e:
        ...     print(e.method_name)       # "create_user"
        ...     print(e.pydantic_error)    # Original ValidationError
    """

    def __init__(self, method_name: str, pydantic_error: Exception):
        """Initialize ValidationFailedError.

        Args:
            method_name: The name of the method that failed validation.
            pydantic_error: The original Pydantic ``ValidationError`` that
                describes which fields or constraints were violated.
        """
        self.method_name = method_name
        self.pydantic_error = pydantic_error
        super().__init__(f"Validation failed for method '{method_name}': {pydantic_error}")


def validate(func: T) -> T:
    """Marker decorator that enables Pydantic validation on a method.

    Marks the decorated function with a hidden metadata attribute
    (``_pico_pydantic_validate_meta``) so the ``ValidationInterceptor``
    knows to inspect and validate its arguments at call time.

    This decorator does **not** contain validation logic itself. It is
    intentionally lightweight to keep import times fast and to delegate
    the heavy lifting to the interceptor, which has access to the full
    IoC context.

    Args:
        func: The function or method to mark for validation.

    Returns:
        The same function, unmodified except for the added metadata attribute.

    Example:
        >>> from pico_ioc import component
        >>> from pico_pydantic import validate
        >>> from pydantic import BaseModel
        >>>
        >>> class ItemData(BaseModel):
        ...     name: str
        ...     price: float
        >>>
        >>> @component
        ... class ItemService:
        ...     @validate
        ...     async def add_item(self, data: ItemData) -> dict:
        ...         return data.model_dump()
    """
    setattr(func, VALIDATE_META, True)
    from pico_ioc import intercepted_by

    from .interceptor import ValidationInterceptor

    return intercepted_by(ValidationInterceptor)(func)
