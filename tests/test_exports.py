"""The public API is exactly what ``__all__`` declares (stability contract)."""

import pico_pydantic


def test_public_api_is_declared_and_importable():
    assert set(pico_pydantic.__all__) == {"ValidationFailedError", "ValidationInterceptor", "validate"}
    for name in pico_pydantic.__all__:
        assert getattr(pico_pydantic, name) is not None
