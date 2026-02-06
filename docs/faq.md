# Frequently Asked Questions

## General

### What is Pico-Pydantic?

Pico-Pydantic provides AOP-based argument validation for pico-ioc managed components. It uses Pydantic's `TypeAdapter` to validate method arguments against `BaseModel` type hints before the method executes.

### What Python versions are supported?

Pico-Pydantic requires Python 3.11 or later.

### What Pydantic version is required?

Pydantic 2.0 or later is required.

## Validation

### How does validation work?

The `@validate` decorator is a lightweight marker. The actual validation is performed by the `ValidationInterceptor`, a singleton `MethodInterceptor` that:

1. Intercepts the method call
2. Inspects the method signature for `BaseModel` type hints
3. Validates each argument using `TypeAdapter.validate_python()`
4. Transforms dicts into model instances automatically
5. Raises `ValidationFailedError` if validation fails

### Which types are validated?

Only arguments with Pydantic `BaseModel` type hints (or generics containing them):

```python
@validate
async def process(self, user: UserModel, count: int):
    # 'user' is validated, 'count' is passed through
    ...
```

Supported generic types: `List[BaseModel]`, `Optional[BaseModel]`, `Union[BaseModel, ...]`.

### Are dicts automatically converted to models?

Yes. If an argument has a `BaseModel` type hint and you pass a dict, it is validated and converted:

```python
# Both calls work:
await service.create(UserModel(name="alice"))
await service.create({"name": "alice"})  # Dict converted to UserModel
```

### How do I handle validation errors?

Catch `ValidationFailedError`:

```python
from pico_pydantic import ValidationFailedError

try:
    await service.create({"invalid": "data"})
except ValidationFailedError as e:
    print(e.method_name)      # Method that failed
    print(e.pydantic_error)   # Original Pydantic ValidationError
```

`ValidationFailedError` inherits from `ValueError`.

## Architecture

### Why use a decorator + interceptor instead of inline validation?

Separation of concerns. The `@validate` decorator is a marker that keeps your business logic clean. The `ValidationInterceptor` handles all validation logic via AOP, so services don't need `model_validate()` calls or try/except blocks.

### Does it work with sync methods?

Yes. The interceptor supports both `async def` and regular methods.

### Is there a performance overhead?

The interceptor checks for the `@validate` marker first. Methods without it are skipped instantly. For validated methods, a `TypeAdapter` is created per parameter per call. This is suitable for service-layer validation where correctness matters more than microsecond latency.

## Troubleshooting

### Validation is not running

Ensure the method is decorated with `@validate`:

```python
from pico_pydantic import validate

@component
class MyService:
    @validate  # Required!
    async def process(self, data: MyModel):
        ...
```

### Arguments are not being validated

Only parameters with `BaseModel` type hints are validated. Parameters without annotations, or with non-Pydantic types, are passed through:

```python
@validate
async def process(self, data: MyModel, name: str, count):
    # data: validated (BaseModel)
    # name: passed through (str, not BaseModel)
    # count: passed through (no annotation)
    ...
```
