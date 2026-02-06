"""Tests for interceptor.py edge cases and 100% coverage."""
import pytest
from unittest.mock import Mock, MagicMock, patch
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
        from unittest.mock import MagicMock, patch
        import inspect

        bad_annotation = MagicMock()
        bad_annotation.__class__ = type  # Make it look like a class

        with patch.object(inspect, 'isclass', return_value=True):
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


class TestCallNextAsync:
    """Tests for _call_next_async."""

    @pytest.mark.asyncio
    async def test_handles_sync_result(self):
        """Handles synchronous (non-awaitable) results."""
        interceptor = ValidationInterceptor()
        ctx = Mock()

        def sync_call_next(c):
            return "sync_result"

        result = await interceptor._call_next_async(ctx, sync_call_next)
        assert result == "sync_result"

    @pytest.mark.asyncio
    async def test_handles_async_result(self):
        """Handles asynchronous (awaitable) results."""
        interceptor = ValidationInterceptor()
        ctx = Mock()

        async def async_call_next(c):
            return "async_result"

        # call_next returns a coroutine
        def call_next_wrapper(c):
            return async_call_next(c)

        result = await interceptor._call_next_async(ctx, call_next_wrapper)
        assert result == "async_result"
