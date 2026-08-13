# Pico-Pydantic

Declarative, AOP-based Pydantic validation for pico-ioc managed components.

## Features

- **`@validate` Decorator**: Mark methods for automatic argument validation
- **AOP Interceptor**: Validation runs before method execution via `ValidationInterceptor`
- **Type Support**: `BaseModel`, `List[BaseModel]`, `Optional[BaseModel]`, `Union` types
- **Argument Transformation**: Dicts are automatically converted to BaseModel instances
- **Async & Sync**: Works with both `async def` and regular methods

## Quick Start

```python
from pydantic import BaseModel, Field
from pico_ioc import component
from pico_pydantic import validate

class ItemData(BaseModel):
    name: str
    price: float = Field(gt=0)

@component
class InventoryService:
    @validate
    async def add_item(self, data: ItemData) -> dict:
        # 'data' is guaranteed to be a valid ItemData instance
        return data.model_dump()
```

> **Important:** Validation only runs when the component is resolved from
> the pico-ioc container. If you instantiate the class directly
> (`InventoryService()`), `@validate` has no effect. See
> [Getting Started](getting-started.md) for details.

## Installation

```bash
pip install pico-pydantic
```

## Requirements

- Python 3.11+ (tested on 3.11, 3.12, 3.13 and 3.14)
- pico-ioc >= 2.2.0
- Pydantic 2.0+

## Documentation

- [Getting Started](getting-started.md) - Installation and basic usage
- [Architecture](architecture.md) - Design and implementation details
- [FAQ](faq.md) - Frequently asked questions

## License

MIT License - see LICENSE file for details.

**See it in context**: the [flagship use case](https://dperezcabrera.github.io/pico-boot/flagship/) wires this module into a full order platform together with the rest of the ecosystem.
