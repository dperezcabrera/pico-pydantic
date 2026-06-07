# AI Coding Skills

[Claude Code](https://code.claude.com) and [OpenAI Codex](https://openai.com/index/introducing-codex/) skills for AI-assisted development with pico-pydantic.

## Installation

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- pydantic
```

Or install all pico skills:

```bash
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash
```

### Platform-specific

```bash
# Claude Code only
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- --claude pydantic

# OpenAI Codex only
curl -sL https://raw.githubusercontent.com/dperezcabrera/pico-skills/main/install.sh | bash -s -- --codex pydantic
```

## Available Commands

### `/add-validation`

Adds Pydantic validation to component methods via AOP. Use when you need automatic input validation on service methods without manual checking.

**How it works:** pico-pydantic's `ValidationInterceptor` inspects type hints with `BaseModel` parameters and validates them automatically before method execution.

```
/add-validation UserService
/add-validation OrderService.create_order
```

### `/add-component`

Creates a new pico-ioc component with dependency injection. Use when adding services, factories, or interceptors.

```
/add-component UserService
```

### `/add-tests`

Generates tests for existing pico components. Creates unit tests with validation error assertions.

```
/add-tests UserService
```

## More Information

See [pico-skills](https://github.com/dperezcabrera/pico-skills) for the full list of skills, selective installation, and details.
