# Claude Code Skills

Pico-Pydantic includes pre-designed skills for [Claude Code](https://claude.ai/claude-code) that enable AI-assisted development following pico-framework patterns and best practices.

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Pico Validate** | `/pico-validate` | Adds Pydantic validation to pico-ioc components |
| **Pico Test Generator** | `/pico-tests` | Generates tests for pico-framework components |

---

## Pico Validate

Adds declarative Pydantic validation to service methods via AOP.

### Basic Usage

```python
from pydantic import BaseModel
from pico_pydantic import validate

class UserInput(BaseModel):
    name: str
    email: str
    age: int

@component
class UserService:
    @validate
    def create_user(self, data: UserInput) -> User:
        # data is already validated
        return User(**data.model_dump())
```

### Multiple Arguments

```python
class QueryParams(BaseModel):
    limit: int = 10
    offset: int = 0
    search: str | None = None

@component
class SearchService:
    @validate
    def search(self, query: str, params: QueryParams) -> list:
        ...
```

### Error Handling

```python
from pico_pydantic import ValidationFailedError

try:
    service.create_user({"name": "", "email": "invalid"})
except ValidationFailedError as e:
    print(f"Validation failed: {e.errors}")
```

---

## Pico Test Generator

Generates tests for any pico-framework component.

### Testing Validation

```python
import pytest
from pico_pydantic import ValidationFailedError

class TestUserService:
    def test_create_valid_user(self, service):
        result = service.create_user({"name": "Alice", "email": "a@b.com", "age": 30})
        assert result.name == "Alice"

    def test_create_invalid_user_raises(self, service):
        with pytest.raises(ValidationFailedError):
            service.create_user({"name": "", "email": "invalid"})
```

---

## Installation

```bash
# Project-level (recommended)
mkdir -p .claude/skills/pico-validate
# Copy the skill YAML+Markdown to .claude/skills/pico-validate/SKILL.md

mkdir -p .claude/skills/pico-tests
# Copy the skill YAML+Markdown to .claude/skills/pico-tests/SKILL.md

# Or user-level (available in all projects)
mkdir -p ~/.claude/skills/pico-validate
mkdir -p ~/.claude/skills/pico-tests
```

## Usage

```bash
# Invoke directly in Claude Code
/pico-validate UserService
/pico-tests UserService
```

See the full skill templates in the [pico-framework skill catalog](https://github.com/dperezcabrera/pico-pydantic).
