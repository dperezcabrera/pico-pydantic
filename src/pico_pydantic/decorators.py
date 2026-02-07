from typing import Callable, TypeVar

T = TypeVar("T", bound=Callable)

VALIDATE_META = "_pico_pydantic_validate_meta"


class ValidationFailedError(ValueError):
    def __init__(self, method_name: str, pydantic_error: Exception):
        self.method_name = method_name
        self.pydantic_error = pydantic_error
        super().__init__(f"Validation failed for method '{method_name}': {pydantic_error}")


def validate(func: T) -> T:
    setattr(func, VALIDATE_META, True)
    return func
