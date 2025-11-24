import pytest
from typing import List, Optional, Union, Any, Type
from unittest.mock import AsyncMock, Mock
from pydantic import BaseModel, ValidationError, Field
from pico_pydantic.decorators import validate, VALIDATE_META, ValidationFailedError
from pico_pydantic.interceptor import ValidationInterceptor

class MockMethodCtx:
    def __init__(self, cls: Type, name: str, args: tuple, kwargs: dict):
        self.cls = cls
        self.name = name
        self.args = args
        self.kwargs = kwargs

class Item(BaseModel):
    id: int = Field(gt=0)
    name: str

class User(BaseModel):
    email: str

class NonPydanticArg:
    pass

class TestService:
    @validate
    def simple_method(self, item: Item) -> bool:
        return isinstance(item, Item)

    @validate
    def list_method(self, items: List[Item]) -> bool:
        return all(isinstance(i, Item) for i in items)

    @validate
    def optional_method(self, item: Optional[Item] = None) -> bool:
        if item is None:
            return True
        return isinstance(item, Item)

    @validate
    def union_method(self, data: Union[Item, int]) -> str:
        if isinstance(data, Item):
            return "item"
        return "int"

    @validate
    def mixed_method(self, item: Item, other: NonPydanticArg) -> bool:
        return isinstance(item, Item) and isinstance(other, NonPydanticArg)

    @validate
    def method_with_defaults(self, item: Item, limit: int = 10) -> int:
        return limit

    def non_validated(self, item: Item) -> bool:
        return True

@pytest.fixture
def interceptor():
    return ValidationInterceptor()

def test_validate_decorator_sets_meta():
    def test_func(): pass
    decorated_func = validate(test_func)
    assert getattr(decorated_func, VALIDATE_META) is True

def test_validation_failed_error_message():
    mock_pydantic_error = Mock(spec=ValidationError)
    mock_pydantic_error.errors.return_value = [] 
    error = ValidationFailedError("test_method", mock_pydantic_error)
    assert "Validation failed for method 'test_method'" in str(error)

@pytest.mark.asyncio
async def test_invoke_transforms_dict_to_model(interceptor):
    valid_data = {"id": 1, "name": "Transformation"}
    
    ctx = MockMethodCtx(
        cls=TestService,
        name="simple_method",
        args=(Mock(spec=TestService), valid_data),
        kwargs={}
    )

    async def call_next(context):
        service = TestService()
        return service.simple_method(*context.args[1:], **context.kwargs)

    result = await interceptor.invoke(ctx, call_next)
    
    assert result is True
    assert isinstance(ctx.args[1], Item)

@pytest.mark.asyncio
async def test_invoke_handles_list_generics(interceptor):
    valid_list = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    
    ctx = MockMethodCtx(
        cls=TestService,
        name="list_method",
        args=(Mock(spec=TestService), valid_list),
        kwargs={}
    )

    async def call_next(context):
        service = TestService()
        return service.list_method(*context.args[1:])

    result = await interceptor.invoke(ctx, call_next)
    assert result is True
    assert isinstance(ctx.args[1], list)
    assert isinstance(ctx.args[1][0], Item)

@pytest.mark.asyncio
async def test_invoke_handles_optional_none(interceptor):
    ctx = MockMethodCtx(
        cls=TestService,
        name="optional_method",
        args=(Mock(spec=TestService), None),
        kwargs={}
    )
    
    call_next = AsyncMock(return_value=True)
    await interceptor.invoke(ctx, call_next)
    assert ctx.args[1] is None

@pytest.mark.asyncio
async def test_invoke_handles_optional_value(interceptor):
    valid_data = {"id": 1, "name": "Optional"}
    ctx = MockMethodCtx(
        cls=TestService,
        name="optional_method",
        args=(Mock(spec=TestService), valid_data),
        kwargs={}
    )
    
    async def call_next(context):
        return isinstance(context.args[1], Item)

    result = await interceptor.invoke(ctx, call_next)
    assert result is True

@pytest.mark.asyncio
async def test_invoke_handles_union_types(interceptor):
    valid_data = {"id": 1, "name": "Union"}
    ctx = MockMethodCtx(
        cls=TestService,
        name="union_method",
        args=(Mock(spec=TestService), valid_data),
        kwargs={}
    )
    
    async def call_next(context):
        return isinstance(context.args[1], Item)

    result = await interceptor.invoke(ctx, call_next)
    assert result is True

@pytest.mark.asyncio
async def test_invoke_skips_non_pydantic_args(interceptor):
    valid_item = {"id": 1, "name": "Mixed"}
    non_pydantic = NonPydanticArg()
    
    ctx = MockMethodCtx(
        cls=TestService,
        name="mixed_method",
        args=(Mock(spec=TestService), valid_item, non_pydantic),
        kwargs={}
    )
    
    async def call_next(context):
        return isinstance(context.args[1], Item) and context.args[2] is non_pydantic

    result = await interceptor.invoke(ctx, call_next)
    assert result is True

@pytest.mark.asyncio
async def test_invoke_raises_error_on_invalid_data(interceptor):
    invalid_data = {"id": -5, "name": "Invalid"}
    
    ctx = MockMethodCtx(
        cls=TestService,
        name="simple_method",
        args=(Mock(spec=TestService), invalid_data),
        kwargs={}
    )
    
    call_next = Mock()
    
    with pytest.raises(ValidationFailedError) as exc:
        await interceptor.invoke(ctx, call_next)
    
    assert isinstance(exc.value.pydantic_error, ValidationError)
    call_next.assert_not_called()

@pytest.mark.asyncio
async def test_invoke_raises_error_inside_list(interceptor):
    invalid_list = [{"id": 1, "name": "Ok"}, {"id": -1, "name": "Bad"}]
    
    ctx = MockMethodCtx(
        cls=TestService,
        name="list_method",
        args=(Mock(spec=TestService), invalid_list),
        kwargs={}
    )
    
    call_next = Mock()
    
    with pytest.raises(ValidationFailedError):
        await interceptor.invoke(ctx, call_next)

@pytest.mark.asyncio
async def test_invoke_skips_undecorated_methods(interceptor):
    ctx = MockMethodCtx(
        cls=TestService,
        name="non_validated",
        args=(Mock(spec=TestService), {"bad": "data"}),
        kwargs={}
    )
    
    call_next = AsyncMock(return_value=True)
    await interceptor.invoke(ctx, call_next)
    
    call_next.assert_called_once()
    assert ctx.args[1] == {"bad": "data"}

@pytest.mark.asyncio
async def test_invoke_handles_kwargs_transformation(interceptor):
    valid_data = {"id": 99, "name": "Kwargs"}
    
    ctx = MockMethodCtx(
        cls=TestService,
        name="simple_method",
        args=(Mock(spec=TestService),),
        kwargs={"item": valid_data}
    )
    
    async def call_next(context):
        item_arg = context.kwargs.get("item")
        if item_arg is None and len(context.args) > 1:
            item_arg = context.args[1]
            
        return isinstance(item_arg, Item)

    result = await interceptor.invoke(ctx, call_next)
    assert result is True
