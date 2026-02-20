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

The most common cause: **the component was not resolved from the container.**

`@validate` is a marker — it does nothing on its own. The actual validation
is performed by the `ValidationInterceptor`, which is part of pico-ioc's
AOP pipeline. This pipeline only runs for components obtained via
`container.get()` (or injected by the container into another component).

```python
# Validation runs — interceptor is active
service = container.get(MyService)
await service.process({"bad": "data"})    # -> ValidationFailedError

# Validation does NOT run — no interceptor
service = MyService()
await service.process({"bad": "data"})    # -> executes normally
```

If you are getting the service from the container and validation still does
not run, check these additional causes:

1. **Missing `@validate` on the method:**

    ```python
    from pico_pydantic import validate

    @component
    class MyService:
        @validate  # Required!
        async def process(self, data: MyModel):
            ...
    ```

2. **`ValidationInterceptor` not registered.** If you use `pico-boot`, it
   is auto-discovered via the `pico_boot.modules` entry point. If you do
   not use `pico-boot`, add `"pico_pydantic"` to your modules list:

    ```python
    from pico_ioc import init
    container = init(modules=["myapp", "pico_pydantic"])
    ```

3. **The parameter is not a `BaseModel` type.** Only `BaseModel` subclasses
   (and generics like `List[Model]`, `Optional[Model]`) are validated.
   Plain types (`str`, `int`) are passed through.

See the [unified troubleshooting guide](https://github.com/dperezcabrera/pico-boot/blob/main/docs/troubleshooting.md) for a complete decision tree.

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

---

## Error Reference

This section documents every error message produced by pico-pydantic with its exact text, cause, and fix.

### `ValidationFailedError`

**Exact message format:**

```
Validation failed for method '<method_name>': <pydantic_error>
```

**Example output:**

```
Validation failed for method 'create_user': 1 validation error for UserCreate
username
  String should have at least 3 characters [type=string_too_short, input_value='ab', input_type=str]
```

**Cause:** An argument with a `BaseModel` type hint failed Pydantic validation. The interceptor called `TypeAdapter(annotation).validate_python(value)` and Pydantic raised a `ValidationError`.

**Attributes:**

| Attribute        | Type                          | Description                                    |
|:-----------------|:------------------------------|:-----------------------------------------------|
| `method_name`    | `str`                         | Name of the method that failed validation      |
| `pydantic_error` | `pydantic.ValidationError`    | The original Pydantic error with field details  |

**Fix:** Inspect `e.pydantic_error.errors()` to see which fields failed and why:

```python
from pico_pydantic import ValidationFailedError

try:
    await service.create_user({"username": "ab"})
except ValidationFailedError as e:
    for error in e.pydantic_error.errors():
        print(f"Field: {error['loc']}, Message: {error['msg']}")
```

`ValidationFailedError` inherits from `ValueError`, so it can be caught with `except ValueError` as well.

---

### `TypeError` from argument binding

**Exact message format (Python standard):**

```
missing a required argument: '<param_name>'
```

or

```
got an unexpected keyword argument '<param_name>'
```

**Cause:** The `_bind_arguments()` helper tries to bind positional and keyword arguments to the method signature. If binding fails even after adjusting for `self`/`cls`, Python raises a `TypeError`.

**Fix:** Ensure the arguments you pass match the method signature (correct number of positional args, correct keyword names).

---

### `TypeAdapter` validation errors

**Exact message format (from Pydantic):**

```
N validation error(s) for <TypeName>
<field_name>
  <error_message> [type=<error_type>, input_value=<value>, input_type=<type>]
```

**Example:**

```
2 validation errors for ItemData
name
  String should have at least 3 characters [type=string_too_short, input_value='ab', input_type=str]
price
  Input should be greater than 0 [type=greater_than, input_value=-5, input_type=int]
```

**Cause:** `TypeAdapter(annotation).validate_python(value)` found that the input data violates one or more Pydantic field constraints. This error is always wrapped in `ValidationFailedError` by the interceptor, so you will not see a bare `pydantic.ValidationError` unless you bypass the interceptor.

**Fix:** Correct the input data to satisfy the model's field constraints (`Field(min_length=...)`, `Field(gt=...)`, required fields, etc.).

---

### Silent failure on broken generic types

**Symptom:** No `ValidationFailedError` is raised even though the type annotation looks like it should be validated.

**Cause:** The `_requires_pydantic_validation()` method wraps its type-checking logic in a broad `except Exception` handler. If a type annotation has a broken `__args__` iterator or causes `issubclass()` to raise a `TypeError` (common with some typing constructs), the method returns `False` and the argument is silently passed through.

**Fix:** This is by design to avoid crashes on exotic type annotations. If you suspect a type is not being validated, verify that `issubclass(YourType, BaseModel)` works correctly in an interactive Python session. Standard `BaseModel` subclasses and common generics (`List`, `Optional`, `Union`) are fully supported.
