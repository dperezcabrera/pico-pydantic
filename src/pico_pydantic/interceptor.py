import inspect
from typing import Any, Callable
from pico_ioc import MethodCtx, MethodInterceptor, component
from pydantic import ValidationError, TypeAdapter, BaseModel
from .decorators import VALIDATE_META, ValidationFailedError

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
        sig = inspect.signature(func)
        bound = None

        try:
            bound = sig.bind(*args, **kwargs)
        except TypeError:
            bound = sig.bind(*args[1:], **kwargs)
        
        bound.apply_defaults()
        
        validated_args_map = bound.arguments.copy()

        for name, val in bound.arguments.items():
            param = sig.parameters[name]
            
            if name in ('self', 'cls') or param.annotation == inspect.Parameter.empty:
                continue

            if self._requires_pydantic_validation(param.annotation):
                adapter = TypeAdapter(param.annotation)
                validated_value = adapter.validate_python(val)
                validated_args_map[name] = validated_value
        
        bound.arguments.update(validated_args_map)
        
        return bound.args, bound.kwargs

    def _requires_pydantic_validation(self, annotation: Any) -> bool:
        try:
            if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                return True
            
            if hasattr(annotation, "__args__"):
                return any(self._requires_pydantic_validation(arg) for arg in annotation.__args__)
            
            return False
        except Exception:
            return False

    async def _call_next_async(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        res = call_next(ctx)
        if inspect.isawaitable(res):
            return await res
        return res
