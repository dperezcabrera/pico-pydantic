# 📦 pico-pydantic

[![PyPI](https://img.shields.io/pypi/v/pico-pydantic.svg)](https://pypi.org/project/pico-pydantic/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/dperezcabrera/pico-pydantic)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![CI (tox matrix)](https://github.com/dperezcabrera/pico-ioc/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/dperezcabrera/pico-pydantic/branch/main/graph/badge.svg)](https://codecov.io/gh/dperezcabrera/pico-pydantic)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-pydantic&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-pydantic)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-pydantic&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-pydantic)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=dperezcabrera_pico-pydantic&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=dperezcabrera_pico-pydantic)
[![Docs](https://img.shields.io/badge/Docs-pico--pydantic-blue?style=flat&logo=readthedocs&logoColor=white)](https://dperezcabrera.github.io/pico-pydantic/)

# Pico-Pydantic

**Pico-Pydantic** integrates **[Pico-IoC](https://github.com/dperezcabrera/pico-ioc)** with **[Pydantic](https://docs.pydantic.dev/)**, enabling **declarative, aspect-oriented validation** of method arguments within your service layer.

It uses Pico-IoC's **`MethodInterceptor`** system to perform validation based on Pydantic **`BaseModel`** type hints **before** your method's business logic runs. This is the ideal tool for ensuring arguments passed between IoC-managed services are structurally correct.

> 🐍 Requires Python 3.10+
> 🧩 Works with Pydantic 2.0+
> 🔄 Supports async and sync methods
> 🧪 Enables unit testing of validation separate from business logic

-----

## 🎯 Why pico-pydantic

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

## 🧱 Core Features

  * Method validation via **`@validate`** decorator.
  * **`ValidationInterceptor`** for AOP execution.
  * Seamless compatibility with **`BaseModel`** type annotations.
  * Correct handling of positional, keyword, and default arguments.
  * Zero coupling to web frameworks.

-----

## 📦 Installation

```bash
pip install pico-pydantic
```

Also install `pico-ioc` and `pydantic`:

```bash
pip install pico-ioc pydantic
```

-----

## 🚀 Quick Example

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
from pico_ioc import DictSource, configuration
from pico_stack import init, DictSource, configuration
from pico_pydantic import ValidationFailedError

# Define the base configuration (optional)
config = configuration(DictSource({}))

# 'components' is used here as the module containing InventoryService.
container = init(
    modules=["components"],
    config=config,
)

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

## ⚙️ How It Works

  * The **`ValidationInterceptor`** is globally registered with Pico-IoC.
  * When a method decorated with **`@validate`** is called:
  * The interceptor captures the call arguments.
  * It inspects the method signature for arguments with the **`BaseModel`** type hint.
  * It calls **`BaseModel.model_validate(value)`** on the argument value.
  * If validation fails, it wraps the error in **`ValidationFailedError`** and stops execution.
  * If successful, **`call_next`** is executed, and the original method runs.

No manual checks inside the service method. Logic stays clean.

-----

## 💡 Architecture Overview

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
                 │  Inspect & model_validate()  │
                 └──────────────┬───────────────┘
                                │
                             Pydantic 2.0+
```

-----

## 📝 License

MIT

