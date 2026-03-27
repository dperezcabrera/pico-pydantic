"""AOP validation interceptor for pico-ioc managed components.

This module implements the ``ValidationInterceptor``, a singleton
``MethodInterceptor`` that inspects method signatures for Pydantic
``BaseModel`` type hints and validates arguments using
``TypeAdapter.validate_python()`` before the method body executes.

Helper functions are extracted at module level to keep cyclomatic
complexity low:
    - ``_bind_arguments``: Binds positional/keyword args to a signature.
    - ``_should_skip_param``: Determines if a parameter should bypass validation.
    - ``_is_basemodel_class``: Checks if an annotation is a ``BaseModel`` subclass.
    - ``_has_pydantic_in_args``: Recursively checks generic ``__args__`` for
      ``BaseModel`` types.
"""

import inspect
from typing import Any, Callable

from pico_ioc import MethodCtx, MethodInterceptor, component
from pydantic import BaseModel, TypeAdapter, ValidationError

from .decorators import VALIDATE_META, ValidationFailedError


def _bind_arguments(sig: inspect.Signature, args: tuple, kwargs: dict) -> inspect.BoundArguments:
    """Bind positional and keyword arguments to a function signature.

    Handles the discrepancy between how pico-ioc passes arguments (where
    ``self`` may be included explicitly in ``args``) and how Python
    normally binds them. If the initial bind fails with a ``TypeError``,
    it retries without the first positional argument (assumed to be
    ``self`` or ``cls``).

    Args:
        sig: The ``inspect.Signature`` of the target method.
        args: Positional arguments passed to the method.
        kwargs: Keyword arguments passed to the method.

    Returns:
        An ``inspect.BoundArguments`` instance mapping parameter names
        to their values.

    Raises:
        TypeError: If binding fails even after removing the first
            positional argument.
    """
    try:
        return sig.bind(*args, **kwargs)
    except TypeError:
        return sig.bind(*args[1:], **kwargs)


def _should_skip_param(name: str, annotation: Any) -> bool:
    """Determine whether a parameter should be skipped during validation.

    Parameters named ``self`` or ``cls``, and parameters without type
    annotations, are never validated.

    Args:
        name: The parameter name.
        annotation: The parameter's type annotation, or
            ``inspect.Parameter.empty`` if absent.

    Returns:
        ``True`` if the parameter should be skipped, ``False`` otherwise.
    """
    return name in ("self", "cls") or annotation == inspect.Parameter.empty


def _is_basemodel_class(annotation: Any) -> bool:
    """Check whether an annotation is a direct ``BaseModel`` subclass.

    Args:
        annotation: The type annotation to check.

    Returns:
        ``True`` if ``annotation`` is a class that inherits from
        ``pydantic.BaseModel``, ``False`` otherwise.
    """
    return inspect.isclass(annotation) and issubclass(annotation, BaseModel)


def _has_pydantic_in_args(annotation: Any, check_func: Callable[[Any], bool]) -> bool:
    """Check whether any generic type argument requires Pydantic validation.

    Inspects the ``__args__`` attribute of generic types (e.g.,
    ``List[UserModel]``, ``Optional[UserModel]``, ``Union[UserModel, int]``)
    and recursively applies ``check_func`` to each argument.

    Args:
        annotation: A generic type annotation that may have ``__args__``.
        check_func: A callable that returns ``True`` if a single type
            argument requires Pydantic validation. Typically
            ``ValidationInterceptor._requires_pydantic_validation``.

    Returns:
        ``True`` if at least one generic argument requires validation,
        ``False`` if the annotation has no ``__args__`` or none of them
        require validation.
    """
    if not hasattr(annotation, "__args__"):
        return False
    return any(check_func(arg) for arg in annotation.__args__)


@component(scope="singleton")
class ValidationInterceptor(MethodInterceptor):
    """AOP interceptor that validates method arguments against Pydantic schemas.

    Registered as a singleton component via pico-ioc. When a method
    decorated with ``@validate`` is called, this interceptor:

    1. Checks for the ``@validate`` marker on the target method.
    2. Inspects the method signature for ``BaseModel`` type hints.
    3. Validates each matching argument using
       ``TypeAdapter(annotation).validate_python(value)``.
    4. Replaces dict arguments with validated ``BaseModel`` instances.
    5. Raises ``ValidationFailedError`` if any argument fails validation.

    Only parameters with ``BaseModel`` type hints (or generic types
    containing ``BaseModel``, such as ``List[Model]``, ``Optional[Model]``,
    ``Union[Model, ...]``) are validated. Parameters without annotations
    or with non-Pydantic types (``str``, ``int``, etc.) are passed through.

    Auto-discovery:
        Registered via the ``pico_boot.modules`` entry point. No manual
        registration is needed when using ``pico-boot``.

    Example:
        >>> from pydantic import BaseModel
        >>> from pico_ioc import component
        >>> from pico_pydantic import validate
        >>>
        >>> class UserData(BaseModel):
        ...     name: str
        ...     age: int
        >>>
        >>> @component
        ... class UserService:
        ...     @validate
        ...     async def create(self, data: UserData) -> dict:
        ...         return data.model_dump()
        >>>
        >>> # Dicts are automatically converted to UserData instances:
        >>> # await service.create({"name": "alice", "age": 30})
    """

    async def invoke(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        """Intercept a method call and validate arguments if marked.

        This is the main entry point called by pico-ioc's interceptor
        chain. If the target method has the ``@validate`` marker, its
        arguments are validated and transformed before proceeding.

        Args:
            ctx: The method invocation context provided by pico-ioc,
                containing the target class, method name, args, and kwargs.
            call_next: Callable to invoke the next interceptor or the
                actual method in the chain.

        Returns:
            The return value of the target method (or next interceptor).

        Raises:
            ValidationFailedError: If any argument with a ``BaseModel``
                type hint fails Pydantic validation. Wraps the original
                ``pydantic.ValidationError``.
        """
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
        """Validate and transform method arguments using Pydantic.

        Binds the given positional and keyword arguments to the function
        signature, then iterates over each parameter. For parameters with
        ``BaseModel`` type hints (or generics containing them), the value
        is validated and potentially transformed (e.g., dicts become model
        instances) via ``TypeAdapter(annotation).validate_python(value)``.

        Args:
            func: The original method (used to obtain the signature).
            args: Positional arguments from the method call.
            kwargs: Keyword arguments from the method call.

        Returns:
            A tuple of ``(new_args, new_kwargs)`` with validated and
            transformed values.

        Raises:
            pydantic.ValidationError: If any argument fails validation.
                This is caught by ``invoke()`` and wrapped in
                ``ValidationFailedError``.
        """
        sig = inspect.signature(func)
        # Strip 'self'/'cls' from signature — the AOP proxy doesn't include
        # the instance in ctx.args, but test mocks might.
        params = [v for k, v in sig.parameters.items() if k not in ("self", "cls")]
        sig = sig.replace(parameters=params)
        try:
            bound = sig.bind(*args, **kwargs)
        except TypeError:
            # Fallback: args may still include self (e.g. in test mocks)
            bound = sig.bind(*args[1:], **kwargs)
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
        """Determine whether a type annotation requires Pydantic validation.

        Checks if the annotation is a ``BaseModel`` subclass directly, or
        if it is a generic type (``List``, ``Optional``, ``Union``, etc.)
        whose ``__args__`` contain a ``BaseModel`` subclass. The check is
        recursive, so deeply nested generics are supported.

        Any exception during the check (e.g., ``TypeError`` from
        ``issubclass`` on special typing constructs, or broken
        ``__args__`` iterators) is silently caught, and ``False`` is
        returned.

        Args:
            annotation: The type annotation to inspect.

        Returns:
            ``True`` if the annotation involves a ``BaseModel`` type that
            should be validated, ``False`` otherwise.
        """
        try:
            if _is_basemodel_class(annotation):
                return True
            return _has_pydantic_in_args(annotation, self._requires_pydantic_validation)
        except Exception:
            return False

    async def _call_next_async(self, ctx: MethodCtx, call_next: Callable[[MethodCtx], Any]) -> Any:
        """Invoke the next handler in the interceptor chain.

        Supports both synchronous and asynchronous method implementations.
        If ``call_next`` returns an awaitable (coroutine), it is awaited;
        otherwise the result is returned directly.

        Args:
            ctx: The method invocation context.
            call_next: Callable to invoke the next interceptor or the
                actual method.

        Returns:
            The result of the next handler, whether sync or async.
        """
        res = call_next(ctx)
        if inspect.isawaitable(res):
            return await res
        return res
