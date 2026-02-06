Read and follow ./AGENTS.md for project conventions.

## Pico Ecosystem Context

pico-pydantic provides Pydantic validation integration for pico-ioc. It uses:
- `@component(scope="singleton")` for ValidationInterceptor
- `MethodInterceptor` from pico-ioc for AOP validation
- `@intercepted_by` is NOT used directly - the interceptor is globally registered
- Auto-discovered via `pico_boot.modules` entry point

## Key Reminders

- pico-ioc dependency: `>= 2.2.0`
- `version_scheme = "post-release"` (clean versions on tag)
- requires-python >= 3.11
- Commit messages: one line only
- This is a minimal 3-file package - keep it simple
