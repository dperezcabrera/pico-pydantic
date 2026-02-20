# Getting Started

## Installation

Install Pico-Pydantic using pip:

```bash
pip install pico-pydantic
```

## Basic Setup

### 1. Define your Pydantic models

```python
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=3)
    email: str
    age: int = Field(ge=0)
```

### 2. Create a validated service

```python
from pico_ioc import component
from pico_pydantic import validate

@component
class UserService:
    @validate
    async def create_user(self, data: UserCreate) -> dict:
        # 'data' is guaranteed to be a valid UserCreate
        return {"id": 1, **data.model_dump()}
```

### 3. Initialize the container

```python
import asyncio
from pico_boot import init

container = init(modules=["myapp"])

async def main():
    service = container.get(UserService)

    # Dict is automatically converted to UserCreate
    result = await service.create_user({"username": "alice", "email": "a@b.com", "age": 30})
    print(result)

asyncio.run(main())
```

> **Important:** `@validate` only runs when the component is resolved from
> the container (`container.get(UserService)`). If you instantiate the class
> directly with `UserService()`, validation **will not execute** — the
> `@validate` marker is invisible without the `ValidationInterceptor` that
> the container provides. This is by design: it keeps unit tests fast
> (no container needed) while enforcing contracts in production.

## Error Handling

Invalid data raises `ValidationFailedError`:

```python
from pico_pydantic import ValidationFailedError

try:
    await service.create_user({"username": "ab", "email": "bad", "age": -1})
except ValidationFailedError as e:
    print(e.method_name)      # "create_user"
    print(e.pydantic_error)   # Original Pydantic ValidationError
```

## Supported Types

The interceptor validates arguments with these type hints:

```python
from typing import List, Optional, Union

@component
class ItemService:
    @validate
    async def add_item(self, item: ItemModel):
        ...

    @validate
    async def add_items(self, items: List[ItemModel]):
        ...

    @validate
    async def update_item(self, item: Optional[ItemModel] = None):
        ...

    @validate
    async def process(self, data: Union[ItemModel, OrderModel]):
        ...
```

Arguments without `BaseModel` type hints (e.g. `str`, `int`) are passed through without validation.

## Auto-Discovery

Pico-Pydantic registers itself via the `pico_boot.modules` entry point. When using `pico-boot`, the `ValidationInterceptor` is auto-discovered.

## Next Steps

- Read the [Architecture](architecture.md) documentation
- Check the [FAQ](faq.md) for common questions
