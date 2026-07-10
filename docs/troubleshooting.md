# Troubleshooting

## @validate does nothing

- The class must be a `@component` (or otherwise container-managed):
  validation runs through pico-ioc method interception, so direct
  instantiation (`MyService()`) bypasses it.
- The parameter needs a type annotation containing a `BaseModel` (directly
  or inside a generic like `list[Item]`); unannotated parameters are skipped
  by design.

## ValidationFailedError instead of pydantic.ValidationError

That is the contract: the interceptor wraps pydantic's error so callers
depend on pico-pydantic's exception, not on pydantic internals. The original
error is chained (`__cause__`).

## My dict argument was replaced by a model instance

Also the contract: valid input is transformed via
`TypeAdapter(annotation).validate_python(value)` — a dict annotated as
`Item` arrives as `Item`. Annotate as `dict` if you want the raw dict.

## Validation runs twice in FastAPI controllers

FastAPI already validates request bodies against the endpoint signature.
Use `@validate` for service-layer methods called from multiple entry points;
controllers usually do not need it.

## Async method returns a coroutine that explodes later

The interceptor is sync and validates arguments before dispatch; the
coroutine result passes through untouched. If you see late failures, the
error is in the method body, not in validation.
