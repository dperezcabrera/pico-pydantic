from typing import Callable, ParamSpec, TypeVar
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")

VALIDATE_META = "_pico_pydantic_validate_meta"

class ValidationFailedError(ValueError):
    def __init__(self, method_name: str, pydantic_error: Exception):
        self.method_name = method_name
        self.pydantic_error = pydantic_error
        super().__init__(f"Validation failed for method '{method_name}': {pydantic_error}")

def validate(func: Callable[P, R]) -> Callable[P, R]:
    setattr(func, VALIDATE_META, True)
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)
    return wrapper
