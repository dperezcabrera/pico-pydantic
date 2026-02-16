# How to Validate Nested and Generic BaseModel Types

This guide covers validation of complex type hints including `List[Model]`, `Optional[Model]`, `Union[Model, ...]`, and nested BaseModel fields.

---

## How Type Resolution Works

The `ValidationInterceptor` recursively inspects type annotations to determine whether they contain a `BaseModel` subclass. It checks:

1. **Direct BaseModel subclass** -- e.g., `UserModel`.
2. **Generic `__args__`** -- e.g., `List[UserModel]` has `__args__ = (UserModel,)`.
3. **Recursive nesting** -- e.g., `Optional[List[UserModel]]` is resolved by checking `Union[List[UserModel], None]`, then `List[UserModel]`, then `UserModel`.

If a `BaseModel` is found anywhere in the type tree, the entire argument is validated using `TypeAdapter(annotation).validate_python(value)`.

---

## List of Models

Pass a list of dicts and they are validated and converted to model instances:

```python
from typing import List
from pydantic import BaseModel, Field
from pico_ioc import component
from pico_pydantic import validate

class OrderItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1)

@component
class OrderService:
    @validate
    async def create_order(self, items: List[OrderItem]) -> dict:
        # Each element is guaranteed to be a valid OrderItem
        return {"count": len(items)}
```

**Usage:**

```python
# Dicts are automatically converted to OrderItem instances
await service.create_order([
    {"product_id": 1, "quantity": 2},
    {"product_id": 3, "quantity": 1},
])
```

**Invalid data raises `ValidationFailedError`:**

```python
from pico_pydantic import ValidationFailedError

try:
    await service.create_order([
        {"product_id": -1, "quantity": 0},  # Both fields invalid
    ])
except ValidationFailedError as e:
    print(e.method_name)      # "create_order"
    print(e.pydantic_error)   # Details on which fields failed
```

---

## Optional Models

Use `Optional[Model]` for arguments that may be `None`:

```python
from typing import Optional
from pydantic import BaseModel
from pico_ioc import component
from pico_pydantic import validate

class Address(BaseModel):
    street: str
    city: str

@component
class UserService:
    @validate
    async def update_user(self, address: Optional[Address] = None) -> dict:
        if address is None:
            return {"address": "unchanged"}
        return {"address": address.model_dump()}
```

**Usage:**

```python
# Passing None is valid
await service.update_user(address=None)
await service.update_user()  # Default is None

# Passing a dict is validated and converted
await service.update_user(address={"street": "123 Main St", "city": "Springfield"})
```

`Optional[Address]` is resolved as `Union[Address, None]`. The interceptor detects `Address` in the union's `__args__` and validates accordingly. `None` values pass through because `TypeAdapter(Optional[Address]).validate_python(None)` accepts `None`.

---

## Union Types

Use `Union[ModelA, ModelB]` when an argument accepts multiple model types:

```python
from typing import Union
from pydantic import BaseModel
from pico_ioc import component
from pico_pydantic import validate

class CreditCard(BaseModel):
    card_number: str
    expiry: str

class BankTransfer(BaseModel):
    iban: str
    bic: str

@component
class PaymentService:
    @validate
    async def process(self, method: Union[CreditCard, BankTransfer]) -> str:
        if isinstance(method, CreditCard):
            return "card"
        return "bank"
```

**Usage:**

```python
# Pydantic's TypeAdapter resolves the correct union member
await service.process({"card_number": "4111...", "expiry": "12/28"})
await service.process({"iban": "DE89...", "bic": "COBADEFF"})
```

Pydantic uses a discriminated or left-to-right union strategy to determine which model matches. If neither model can validate the input, a `ValidationFailedError` is raised.

---

## Nested BaseModel Fields

Pydantic natively validates nested models within a `BaseModel`. The interceptor only needs to detect the **top-level** `BaseModel` type hint; Pydantic handles the rest:

```python
from pydantic import BaseModel, Field
from pico_ioc import component
from pico_pydantic import validate

class Address(BaseModel):
    street: str
    city: str

class Company(BaseModel):
    name: str
    address: Address  # Nested model

@component
class CompanyService:
    @validate
    async def register(self, company: Company) -> dict:
        return company.model_dump()
```

**Usage:**

```python
# Nested dicts are validated recursively by Pydantic
await service.register({
    "name": "Acme Corp",
    "address": {"street": "456 Oak Ave", "city": "Shelbyville"},
})
```

---

## Mixed Parameters

Only parameters with `BaseModel` type hints are validated. Other types are passed through without validation:

```python
from pydantic import BaseModel
from pico_ioc import component
from pico_pydantic import validate

class Payload(BaseModel):
    data: str

@component
class MixedService:
    @validate
    async def process(self, payload: Payload, tag: str, count: int = 1) -> dict:
        # payload: validated (BaseModel)
        # tag: passed through (str, not BaseModel)
        # count: passed through (int, not BaseModel)
        return {"data": payload.data, "tag": tag, "count": count}
```

---

## Type Resolution Summary

| Type Hint              | Validated? | Mechanism                                  |
|:-----------------------|:-----------|:-------------------------------------------|
| `UserModel`            | Yes        | Direct `BaseModel` subclass check          |
| `List[UserModel]`      | Yes        | `__args__` contains `BaseModel` subclass   |
| `Optional[UserModel]`  | Yes        | `Union[UserModel, None]` -- `__args__` hit |
| `Union[ModelA, ModelB]` | Yes       | `__args__` contains `BaseModel` subclass   |
| `str`                  | No         | Not a `BaseModel` subclass                 |
| `int`                  | No         | Not a `BaseModel` subclass                 |
| `List[str]`            | No         | `__args__` has no `BaseModel`              |
| `Optional[int]`        | No         | `__args__` has no `BaseModel`              |
| (no annotation)        | No         | Skipped -- `inspect.Parameter.empty`       |
