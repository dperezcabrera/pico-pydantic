# How to Test Validated Services

This guide covers strategies for testing pico-ioc components that use `@validate` for argument validation, including unit testing with mocks, integration testing with the container, and testing validation error paths.

---

## Unit Testing Without the Container

The `@validate` decorator is a lightweight marker. It does not perform validation itself. You can call the method directly in unit tests without pico-ioc, and validation will **not** run:

```python
import pytest
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str

class UserService:
    async def create_user(self, data: UserCreate) -> dict:
        return {"id": 1, **data.model_dump()}

@pytest.mark.asyncio
async def test_create_user_directly():
    service = UserService()
    result = await service.create_user(UserCreate(username="alice", email="a@b.com"))
    assert result["username"] == "alice"
```

This tests your business logic in isolation without the AOP validation layer.

---

## Testing the Interceptor Directly

To test that validation works correctly for a method, instantiate the `ValidationInterceptor` and call its `invoke` method with a mock context:

```python
import pytest
from unittest.mock import Mock, AsyncMock
from pico_pydantic import ValidationInterceptor, ValidationFailedError
from pydantic import BaseModel, Field

class ItemData(BaseModel):
    name: str = Field(min_length=3)
    price: float = Field(gt=0)

class ItemService:
    from pico_pydantic import validate

    @validate
    async def add_item(self, data: ItemData) -> dict:
        return data.model_dump()


class MockMethodCtx:
    """Lightweight stand-in for pico-ioc's MethodCtx."""
    def __init__(self, cls, name, args, kwargs):
        self.cls = cls
        self.name = name
        self.args = args
        self.kwargs = kwargs


@pytest.fixture
def interceptor():
    return ValidationInterceptor()


@pytest.mark.asyncio
async def test_valid_dict_is_converted(interceptor):
    ctx = MockMethodCtx(
        cls=ItemService,
        name="add_item",
        args=(Mock(spec=ItemService), {"name": "Hammer", "price": 9.99}),
        kwargs={},
    )

    async def call_next(context):
        return context.args[1].model_dump()

    result = await interceptor.invoke(ctx, call_next)
    assert isinstance(ctx.args[1], ItemData)
    assert result["name"] == "Hammer"


@pytest.mark.asyncio
async def test_invalid_dict_raises_error(interceptor):
    ctx = MockMethodCtx(
        cls=ItemService,
        name="add_item",
        args=(Mock(spec=ItemService), {"name": "ab", "price": -1}),
        kwargs={},
    )

    with pytest.raises(ValidationFailedError) as exc_info:
        await interceptor.invoke(ctx, Mock())

    assert exc_info.value.method_name == "add_item"
    assert exc_info.value.pydantic_error is not None
```

---

## Testing Validation Error Messages

`ValidationFailedError` provides structured access to the failure details:

```python
@pytest.mark.asyncio
async def test_error_message_format(interceptor):
    ctx = MockMethodCtx(
        cls=ItemService,
        name="add_item",
        args=(Mock(spec=ItemService), {"name": "ab", "price": -1}),
        kwargs={},
    )

    with pytest.raises(ValidationFailedError) as exc_info:
        await interceptor.invoke(ctx, Mock())

    error = exc_info.value

    # Check the error message format
    assert "Validation failed for method 'add_item'" in str(error)

    # Access the original Pydantic error for detailed inspection
    pydantic_errors = error.pydantic_error.errors()
    field_names = {e["loc"][0] for e in pydantic_errors}
    assert "name" in field_names or "price" in field_names
```

---

## Integration Testing With the Container

For end-to-end tests that include the full AOP pipeline, initialize the pico-ioc container:

```python
import pytest
from pico_boot import init
from pico_pydantic import ValidationFailedError

@pytest.fixture
def container():
    c = init(modules=["myapp"])
    yield c
    c.shutdown()

@pytest.mark.asyncio
async def test_validation_through_container(container):
    from myapp import UserService, UserCreate

    service = container.get(UserService)

    # Valid data passes through
    result = await service.create_user({"username": "alice", "email": "a@b.com"})
    assert result["username"] == "alice"

    # Invalid data raises ValidationFailedError
    with pytest.raises(ValidationFailedError):
        await service.create_user({"username": "ab"})
```

---

## Mocking Validated Dependencies

When testing a component that depends on a validated service, you can mock the dependency. The mock bypasses the interceptor entirely:

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_controller_with_mocked_service():
    mock_service = AsyncMock()
    mock_service.create_user.return_value = {"id": 1, "username": "alice"}

    # Inject the mock into whatever consumes the service
    controller = UserController(user_service=mock_service)
    result = await controller.handle_create({"username": "alice", "email": "a@b.com"})

    assert result["id"] == 1
    mock_service.create_user.assert_called_once()
```

---

## Testing That Validation Is Skipped for Unmarked Methods

Methods without `@validate` should pass arguments through without validation:

```python
class OrderService:
    # No @validate decorator
    async def process(self, data: dict) -> dict:
        return data

@pytest.mark.asyncio
async def test_undecorated_method_skips_validation(interceptor):
    ctx = MockMethodCtx(
        cls=OrderService,
        name="process",
        args=(Mock(spec=OrderService), {"anything": "goes"}),
        kwargs={},
    )

    call_next = AsyncMock(return_value={"anything": "goes"})
    result = await interceptor.invoke(ctx, call_next)

    call_next.assert_called_once()
    assert result == {"anything": "goes"}
```

---

## Summary of Testing Strategies

| Strategy                   | Validation runs? | Use case                             |
|:---------------------------|:-----------------|:-------------------------------------|
| Direct method call         | No               | Unit test business logic only        |
| Interceptor + MockMethodCtx| Yes              | Test validation behavior in isolation|
| Full container             | Yes              | End-to-end integration tests         |
| Mocked dependency          | No               | Test callers of validated services   |
