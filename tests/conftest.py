from typing import Type

import pytest

from pico_pydantic.interceptor import ValidationInterceptor


class MockMethodCtx:
    def __init__(self, cls: Type, name: str, args: tuple, kwargs: dict):
        self.cls = cls
        self.name = name
        self.args = args
        self.kwargs = kwargs


@pytest.fixture
def interceptor():
    return ValidationInterceptor()
