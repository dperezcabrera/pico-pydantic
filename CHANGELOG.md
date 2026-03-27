# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.html).

---

## [0.2.2] - 2026-03-27

### Fixed
- **`@validate` now works in the AOP interceptor chain.** Previously, `@validate` only set a metadata flag but did not attach `ValidationInterceptor` to the method via `@intercepted_by`, so validation never executed at runtime. The decorator now correctly registers the interceptor, enabling dict-to-model conversion and argument validation when combined with other interceptors like `@transactional`.
- **Signature binding with `self` parameter.** `_validate_and_transform` now strips `self`/`cls` from the method signature before binding arguments, matching how the AOP proxy passes `ctx.args` without the instance.

### Changed
- Updated tests to reflect the real AOP proxy behavior where `ctx.args` does not include `self`.
- Updated `CLAUDE.md` to document the `@intercepted_by` usage.

---

## [0.2.1] - 2025-02-04

### Changed
- **Code Quality**: Refactored `ValidationInterceptor` to reduce cyclomatic complexity from A(3.375) to A(2.5).
  - Extracted helper functions: `_bind_arguments`, `_should_skip_param`, `_is_basemodel_class`, `_has_pydantic_in_args`.
- **Documentation**: Standardized MkDocs configuration with Material theme (indigo), git-revision-date-localized plugin, and math extensions.
- **CI/CD**: Unified GitHub Actions workflow for documentation deployment.

### Fixed
- **Test Coverage**: Achieved 100% test coverage for `interceptor.py`.

### Added
- `tests/test_interceptor_coverage.py`: 8 new tests for `_requires_pydantic_validation` edge cases including exception handling and generic types.

---

## [0.2.0] - 2025-11-25

### Added
- **Pico-Boot Integration:** Added `pico_boot.modules` entry point for automatic discovery.
  `pico-pydantic` now loads automatically when using `pico-boot`, removing the need to manually include `"pico_pydantic"` in the module list.

### Changed
- Updated documentation and examples to use the new **pico-boot auto-discovery** workflow by default.

---

## [0.1.0]

### Added
* **Initial public release** of `pico-pydantic`.
* **`@validate`** decorator providing annotation-driven validation for methods of IoC-managed components.
* **`ValidationInterceptor`** implementing **AOP-based argument validation** for methods decorated with `@validate`.
* Supports Pydantic **`BaseModel`** type hints on method arguments for automatic validation.
* **`ValidationFailedError`** exception for wrapping Pydantic's `ValidationError` to provide better context (method name).
* Fully compatible with **synchronous and asynchronous methods** (`async def`).
* Test suite validating successful validation, failure handling, and correct skipping of non-decorated methods.
* Added dependency requirement for `pico-ioc>=2.1.3` and `pydantic>=2.0.0`.

