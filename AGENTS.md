# pico-pydantic

Declarative, AOP-based Pydantic validation for pico-ioc managed components.

## Commands

```bash
pip install -e .                  # Install in dev mode
pytest tests/ -v                  # Run tests
pytest --cov=pico_pydantic --cov-report=term-missing tests/  # Coverage
tox                               # Full matrix (3.11-3.14)
```

## Project Structure

```
src/pico_pydantic/
  __init__.py          # Exports: validate, ValidationFailedError, ValidationInterceptor
  decorators.py        # @validate decorator, ValidationFailedError exception
  interceptor.py       # ValidationInterceptor (AOP MethodInterceptor)
```

Minimal package (3 source files).

## Key Concepts

- **`@validate`**: Marker decorator for methods. Triggers validation via interceptor before method execution
- **`ValidationInterceptor`**: Singleton `MethodInterceptor`. Inspects method signature for `BaseModel` type hints, calls `TypeAdapter.validate_python()` on arguments
- **`ValidationFailedError`**: Wraps Pydantic `ValidationError` with method name context. Inherits from `ValueError`
- **Type support**: `BaseModel`, `List[BaseModel]`, `Optional[BaseModel]`, `Union[BaseModel, ...]`, nested generics
- **Argument transformation**: Dicts are automatically converted to BaseModel instances

## Code Style

- Python 3.11+
- Helper functions extracted for low cyclomatic complexity
- `_bind_arguments()`, `_should_skip_param()`, `_is_basemodel_class()`, `_has_pydantic_in_args()` are module-level helpers
- Recursive generic type checking via `__args__`

## Testing

- pytest + pytest-asyncio
- Test both sync and async method paths
- Cover edge cases: broken generics, `issubclass` exceptions, class/static methods
- Target: 100% coverage

## Boundaries

- Do not modify `_version.py`
- Validation only on arguments with `BaseModel` (or generic containing it) type hints
- `self`, `cls`, and unannotated parameters are always skipped
