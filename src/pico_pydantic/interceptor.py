import inspect
from typing import Any, Callable
from pico_ioc import MethodCtx, MethodInterceptor, component
from pydantic import ValidationError, TypeAdapter, BaseModel
from .decorators import VALIDATE_META, ValidationFailedError


def _bind_arguments(sig: inspect.Signature, args: tuple, kwargs: dict) -> inspect.BoundArguments:
    """Bind arguments to signature, handling self/cls prefix."""
    try:
        return sig.bind(*args, **kwargs)
    except TypeError:
        return sig.bind(*args[1:], **kwargs)


def _should_skip_param(name: str, annotation: Any) -> bool:
    """Check if parameter should be skipped for validation."""
    return name in ('self', 'cls') or annotation == inspect.Parameter.empty


def _is_basemodel_class(annotation: Any) -> bool:
    """Check if annotation is a BaseModel subclass."""
    return inspect.isclass(annotation) and issubclass(annotation, BaseModel)


def _has_pydantic_in_args(annotation: Any, check_func: Callable[[Any], bool]) -> bool:
    """Check if any generic argument requires pydantic validation."""
    if not hasattr(annotation, "__args__"):
        return False
    return any(check_func(arg) for arg in annotation.__args__)


@component(scope="singleton")
class ValidationInterceptor(MethodInterceptor):
    async def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        original_func = getattr(ctx.cls, ctx.name, None)

        if not original_func or not getattr(original_func, VALIDATE_META, False):
            return await self._call_next_async(ctx, call_next)

        try:
            new_args, new_kwargs = self._validate_and_transform(original_func, ctx.args, ctx.kwargs)
            ctx.args = new_args
            ctx.kwargs = new_kwargs
        except ValidationError as e:
            raise ValidationFailedError(ctx.name, e) from e

        return await self._call_next_async(ctx, call_next)

    def _validate_and_transform(self, func: Callable, args: tuple, kwargs: dict) -> tuple[tuple, dict]:
        """Validate and transform arguments using Pydantic."""
        sig = inspect.signature(func)
        bound = _bind_arguments(sig, args, kwargs)
        bound.apply_defaults()

        validated_args_map = bound.arguments.copy()

        for name, val in bound.arguments.items():
            param = sig.parameters[name]

            if _should_skip_param(name, param.annotation):
                continue

            if self._requires_pydantic_validation(param.annotation):
                validated_args_map[name] = TypeAdapter(param.annotation).validate_python(val)

        bound.arguments.update(validated_args_map)
        return bound.args, bound.kwargs

    def _requires_pydantic_validation(self, annotation: Any) -> bool:
        """Check if annotation requires Pydantic validation."""
        try:
            if _is_basemodel_class(annotation):
                return True
            return _has_pydantic_in_args(annotation, self._requires_pydantic_validation)
        except Exception:
            return False

    async def _call_next_async(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        """Call next in chain, awaiting if necessary."""
        res = call_next(ctx)
        if inspect.isawaitable(res):
            return await res
        return res
