# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.html).

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

