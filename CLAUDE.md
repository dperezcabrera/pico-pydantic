Read and follow ./AGENTS.md for project conventions.

## Pico Ecosystem Context

pico-pydantic provides Pydantic validation integration for pico-ioc. It uses:
- `@component(scope="singleton")` for ValidationInterceptor
- `MethodInterceptor` from pico-ioc for AOP validation
- `@validate` uses `@intercepted_by(ValidationInterceptor)` to attach to the AOP chain
- Auto-discovered via `pico_boot.modules` entry point

## Key Reminders

- pico-ioc dependency: `>= 2.2.0`
- **NEVER change `version_scheme`** in pyproject.toml. It MUST remain `"post-release"`. Changing it to `"guess-next-dev"` causes `.dev0` versions to leak to PyPI. This was already fixed once — do not revert it.
- requires-python >= 3.11
- Commit messages: one line only
- This is a minimal 3-file package - keep it simple
