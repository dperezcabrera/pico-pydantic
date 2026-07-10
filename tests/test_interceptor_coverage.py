"""Tests for interceptor.py edge cases and 100% coverage."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from pico_pydantic.interceptor import ValidationInterceptor


class TestRequiresPydanticValidation:
    """Tests for _requires_pydantic_validation edge cases."""

    def test_handles_annotation_that_raises_exception(self):
        """Returns False when annotation check raises an exception."""
        interceptor = ValidationInterceptor()

        # Create an annotation with __args__ that raises when iterated
        class BrokenGeneric:
            @property
            def __args__(self):
                # Return something that will raise when iterated in any()
                class BrokenIterator:
                    def __iter__(self):
                        raise RuntimeError("Cannot iterate")

                return BrokenIterator()

        result = interceptor._requires_pydantic_validation(BrokenGeneric())
        assert result is False

    def test_handles_issubclass_exception(self):
        """Returns False when issubclass raises TypeError."""
        interceptor = ValidationInterceptor()

        # Some special objects raise TypeError on issubclass
        # Use a mock that passes isclass but fails issubclass
        import inspect
        from unittest.mock import MagicMock, patch

        bad_annotation = MagicMock()
        bad_annotation.__class__ = type  # Make it look like a class

        with patch.object(inspect, "isclass", return_value=True):
            # issubclass will fail on MagicMock
            result = interceptor._requires_pydantic_validation(bad_annotation)
            assert result is False

    def test_returns_false_for_non_class_non_generic(self):
        """Returns False for simple types without __args__."""
        interceptor = ValidationInterceptor()

        # Simple string annotation
        result = interceptor._requires_pydantic_validation(str)
        assert result is False

        # Simple int
        result = interceptor._requires_pydantic_validation(int)
        assert result is False

    def test_returns_true_for_basemodel_subclass(self):
        """Returns True for BaseModel subclasses."""
        from pydantic import BaseModel

        class MyModel(BaseModel):
            name: str

        interceptor = ValidationInterceptor()
        result = interceptor._requires_pydantic_validation(MyModel)
        assert result is True

    def test_returns_true_for_generic_containing_basemodel(self):
        """Returns True for generic types containing BaseModel."""
        from typing import List, Optional

        from pydantic import BaseModel

        class MyModel(BaseModel):
            name: str

        interceptor = ValidationInterceptor()

        # List[MyModel]
        result = interceptor._requires_pydantic_validation(List[MyModel])
        assert result is True

        # Optional[MyModel]
        result = interceptor._requires_pydantic_validation(Optional[MyModel])
        assert result is True

    def test_returns_false_for_generic_without_basemodel(self):
        """Returns False for generic types not containing BaseModel."""
        from typing import List, Optional

        interceptor = ValidationInterceptor()

        # List[str]
        result = interceptor._requires_pydantic_validation(List[str])
        assert result is False

        # Optional[int]
        result = interceptor._requires_pydantic_validation(Optional[int])
        assert result is False


class TestInvokePassthrough:
    """invoke() is sync: plain results return directly, awaitables pass through."""

    def test_sync_result_returned_directly(self):
        interceptor = ValidationInterceptor()
        ctx = Mock()
        ctx.cls = object
        ctx.name = "missing"
        assert interceptor.invoke(ctx, lambda c: "sync_result") == "sync_result"

    @pytest.mark.asyncio
    async def test_awaitable_passes_through_untouched(self):
        interceptor = ValidationInterceptor()
        ctx = Mock()
        ctx.cls = object
        ctx.name = "missing"

        async def async_call_next(c):
            return "async_result"

        result = interceptor.invoke(ctx, lambda c: async_call_next(c))
        assert await result == "async_result"


class TestValidateAndTransformArgs:
    """_validate_and_transform binding edge cases."""

    def test_args_including_self_use_fallback_bind(self):
        from pydantic import BaseModel

        class Item(BaseModel):
            name: str

        class Service:
            def handle(self, item: Item) -> Item:
                return item

        interceptor = ValidationInterceptor()
        instance = Service()
        args, kwargs = interceptor._validate_and_transform(Service.handle, (instance, {"name": "x"}), {})
        assert isinstance(args[0], Item)
        assert args[0].name == "x"

    def test_unannotated_params_are_skipped(self):
        class Service:
            def handle(self, raw) -> str:
                return raw

        interceptor = ValidationInterceptor()
        args, kwargs = interceptor._validate_and_transform(Service.handle, ({"untouched": True},), {})
        assert args[0] == {"untouched": True}
