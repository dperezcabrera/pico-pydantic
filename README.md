# pico-pydantic

[![PyPI](https://img.shields.io/pypi/v/pico-pydantic.svg)](https://pypi.org/project/pico-pydantic/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/dperezcabrera/pico-pydantic)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![CI (tox matrix)](https://github.com/dperezcabrera/pico-pydantic/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/dperezcabrera/pico-pydantic/branch/main/graph/badge.svg)](https://codecov.io/gh/dperezcabrera/pico-pydantic)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-pydantic&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-pydantic)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-pydantic&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-pydantic)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-pydantic&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-pydantic)
[![Docs](https://img.shields.io/badge/Docs-pico--pydantic-blue?style=flat&logo=readthedocs&logoColor=white)](https://dperezcabrera.github.io/pico-pydantic/)
[![Interactive Lab](https://img.shields.io/badge/Learn-online-green?style=flat&logo=python&logoColor=white)](https://dperezcabrera.github.io/pico-learn/)

# Pico-Pydantic

**Pico-Pydantic** integrates **[Pico-IoC](https://github.com/dperezcabrera/pico-ioc)** with **[Pydantic](https://docs.pydantic.dev/)**, enabling **declarative, aspect-oriented validation** of method arguments within your service layer.

It uses Pico-IoC's **`MethodInterceptor`** system to perform validation based on Pydantic **`BaseModel`** type hints **before** your method's business logic runs. This is the ideal tool for ensuring arguments passed between IoC-managed services are structurally correct.

> Requires Python 3.11+
> Works with Pydantic 2.0+
> Supports async and sync methods
> Enables unit testing of validation separate from business logic

-----

## Why pico-pydantic

While web frameworks handle validation at the HTTP boundary, business services often need to guarantee input integrity internally, especially when components are called from CLI tools, workers, or other services.

Pico-Pydantic provides:

  * Declarative **`@validate`** boundaries for service methods.
  * **Aspect-Oriented Programming (AOP)** for argument validation.
  * Clear error handling with **`ValidationFailedError`**.
  * Centralized validation logic, decoupled from the core service code.

| Concern | Pico-IoC Default | pico-pydantic |
| :--- | :--- | :--- |
| Argument checking | Manual `if/raise` | Declarative `@validate` |
| Schema definition | None | Pydantic `BaseModel` type hints |
| Handling errors | Raw `ValidationError` | Wrapped `ValidationFailedError` |

-----

## Core Features

  * Method validation via **`@validate`** decorator.
  * **`ValidationInterceptor`** for AOP execution.
  * Seamless compatibility with **`BaseModel`** type annotations.
  * Correct handling of positional, keyword, and default arguments.
  * Zero coupling to web frameworks.

-----

## Installation

```bash
pip install pico-pydantic
```

-----

## Quick Example

### 1\. Define the Data Model and Service:

```python
from pydantic import BaseModel, Field
from pico_ioc import component
from pico_pydantic import validate

class ItemData(BaseModel):
    name: str = Field(min_length=3)
    price: float = Field(gt=0)

@component
class InventoryService:
    @validate
    async def add_item(self, data: ItemData) -> dict:
        # Validation happens BEFORE this line
        print(f"Adding item: {data.name}")
        return data.model_dump()
```

### 2\. Full Example: Initialization, Success, and Failure Handling

```python
import asyncio
from pico_boot import init
from pico_pydantic import ValidationFailedError

# 'components' is used here as the module containing InventoryService.
container = init(modules=["components"])

async def main():
    service = container.get(InventoryService)

    # --- Success: Validation Passes ---
    print("--- Testing Success ---")
    result = await service.add_item({"name": "Hammer", "price": 10.50})
    print(f"Result: {result}")
    
    # --- Failure: ValidationFailedError is thrown by the Interceptor ---
    print("\n--- Testing Failure ---")
    try:
        # Fails: 'price' is negative, violating Field(gt=0)
        await service.add_item({"name": "A", "price": -5})
    except ValidationFailedError as e:
        print(f"Validation failed for method '{e.method_name}'.")
        print(e.pydantic_error) # Shows the detailed Pydantic error
    
    await container.cleanup_all_async()
    container.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

-----

## How It Works

  * The **`@validate`** decorator attaches `ValidationInterceptor` to the method's AOP chain via `@intercepted_by`.
  * When the method is called:
  * The interceptor captures the call arguments.
  * It inspects the method signature for arguments with the **`BaseModel`** type hint.
  * It validates each argument using **`TypeAdapter.validate_python(value)`**.
  * If validation fails, it wraps the error in **`ValidationFailedError`** and stops execution.
  * If successful, **`call_next`** is executed, and the original method runs.

No manual checks inside the service method. Logic stays clean.

-----

## Architecture Overview

```
                 ┌─────────────────────────────┐
                 │         Your App            │
                 │ (Service Layer)             │
                 └──────────────┬──────────────┘
                                │
                        @validate called
                                │
                 ┌──────────────▼───────────────┐
                 │          Pico-IoC            │
                 └──────────────┬───────────────┘
                                │
                    ValidationInterceptor (AOP)
                                │
                 ┌──────────────▼───────────────┐
                 │         pico-pydantic        │
                 │  Inspect & validate_python()  │
                 └──────────────┬───────────────┘
                                │
                             Pydantic 2.0+
```

-----

## Built for AI-assisted development

pico-pydantic is part of an ecosystem designed for humans and coding agents building software together. Every package ships `AGENTS.md` working conventions, an `llms.txt` machine-readable docs index and documented behaviour pinned by regression tests; [pico-testing](https://github.com/dperezcabrera/pico-testing) gives agents a verification loop for their own changes, and releases are gated by the whole ecosystem booting together against real infrastructure. The full story: [Built for AI-assisted development](https://github.com/dperezcabrera/pico-ioc#built-for-ai-assisted-development).

Install the agent skills for [Claude Code](https://code.claude.com) or [OpenAI Codex](https://openai.com/index/introducing-codex/):

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- pydantic
```

| Command | Description |
|---------|-------------|
| `/add-validation` | Add Pydantic validation to component methods |
| `/add-component` | Add components, factories, interceptors, settings |
| `/add-tests` | Generate tests for pico components |

All skills: `curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash`

See [pico-skills](https://github.com/dperezcabrera/pico-skills) for details.

---

## License

MIT

