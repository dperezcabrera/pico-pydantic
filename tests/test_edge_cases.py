import pytest
from typing import List, Optional, Union
from unittest.mock import Mock
from pydantic import BaseModel
from pico_ioc import component
from pico_pydantic.decorators import validate
from pico_pydantic.interceptor import ValidationInterceptor

class Item(BaseModel):
    id: int
    name: str

class ComplexService:
    @validate
    def process_list(self, items: List[Item]) -> int:
        return len(items)

    @validate
    def process_optional(self, item: Optional[Item] = None) -> bool:
        return True

    @validate
    def process_union(self, data: Union[Item, int]) -> str:
        return "ok"

    @classmethod
    @validate
    def class_method_op(cls, item: Item) -> bool:
        return True

    @staticmethod
    @validate
    def static_method_op(item: Item) -> bool:
        return True

class MockMethodCtx:
    def __init__(self, cls, name, args, kwargs):
        self.cls = cls
        self.name = name
        self.args = args
        self.kwargs = kwargs

@pytest.fixture
def interceptor():
    return ValidationInterceptor()

@pytest.mark.asyncio
async def test_validation_handles_list_types(interceptor):
    # Changed from "ignores" to "handles"
    raw_data = [{"id": 1, "name": "valid"}, {"id": 2, "name": "valid"}]
    ctx = MockMethodCtx(
        cls=ComplexService,
        name="process_list",
        args=(Mock(spec=ComplexService), raw_data),
        kwargs={}
    )
    call_next = Mock(return_value=2)
    
    await interceptor.invoke(ctx, call_next)
    
    assert isinstance(ctx.args[1], list)
    # FIX: Now we expect Pydantic Models, not dicts
    assert isinstance(ctx.args[1][0], Item)
    assert ctx.args[1][0].id == 1

@pytest.mark.asyncio
async def test_validation_handles_optional_types(interceptor):
    raw_data = {"id": 1, "name": "valid"}
    ctx = MockMethodCtx(
        cls=ComplexService,
        name="process_optional",
        args=(Mock(spec=ComplexService), raw_data),
        kwargs={}
    )
    call_next = Mock(return_value=True)
    
    await interceptor.invoke(ctx, call_next)
    
    assert isinstance(ctx.args[1], Item)
    assert ctx.args[1].name == "valid"

@pytest.mark.asyncio
async def test_class_method_binding(interceptor):
    valid_item = Item(id=10, name="ClassMethod")
    ctx = MockMethodCtx(
        cls=ComplexService,
        name="class_method_op",
        args=(ComplexService, valid_item),
        kwargs={}
    )
    call_next = Mock(return_value=True)
    
    await interceptor.invoke(ctx, call_next)
    
    call_next.assert_called_once()

@pytest.mark.asyncio
async def test_static_method_binding_failure_risk(interceptor):
    valid_item = Item(id=11, name="StaticMethod")
    ctx = MockMethodCtx(
        cls=ComplexService,
        name="static_method_op",
        args=(valid_item,),
        kwargs={}
    )
    call_next = Mock(return_value=True)
    
    await interceptor.invoke(ctx, call_next)
    
    call_next.assert_called_once()
