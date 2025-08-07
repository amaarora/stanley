# Stanley Codegen

A production-ready code generator for Stanley AI agents. Write simple tool signatures, generate complete agents.

## Features

- **Simple Syntax**: Write tools as `ToolName(param: type)`
- **Multiple Formats**: Supports YAML, JSON, and Python formats
- **Type Safety**: Pydantic validation for all specifications
- **Professional CLI**: Click-based interface with rich output
- **Template System**: Customizable Jinja2 templates
- **Error Handling**: Clear error messages with helpful suggestions
- **Code Formatting**: Automatic formatting with ruff
- **Dry Run Mode**: Preview changes before generating
- **Progress Indicators**: Visual feedback during generation

## Installation

```bash
pip install stanley-codegen
```

Or install from source:

```bash
pip install -e .
```

## Quick Start

1. Create a tool specification file:

```yaml
# tools.yml
tools:
  - "SearchLinkedIn(url: str)"
  - "ReadBlogPost(url: str, read_latest_n_posts: int = 3)"
```

2. Generate your agent:

```bash
stanley-codegen generate tools.yml --name MyAgent
```

3. Run your agent:

```bash
cd my-agent
python agent.py
```

## CLI Commands

### Generate

Generate a complete agent from specifications:

```bash
stanley-codegen generate tools.yml [OPTIONS]

Options:
  -o, --output PATH          Output directory (default: current)
  -n, --name TEXT           Agent name (default: MyAgent)
  -m, --model TEXT          LLM model to use
  --dry-run                 Preview without writing files
  -f, --force              Overwrite existing files
  --no-format              Skip code formatting
  -v, --verbose            Enable verbose output
  --system-prompt PATH     Path to system prompt file
```

### Validate

Check if your specification file is valid:

```bash
stanley-codegen validate tools.yml
```

### New

Create a new specification file from command line:

```bash
stanley-codegen new "SearchTool(query: str)" "AnalyzeTool(text: str)" -o my_tools.yml
```

### Examples

Show example specifications:

```bash
stanley-codegen examples
```

## Specification Formats

### YAML Format (Recommended)

```yaml
tools:
  - "ToolName(param1: type, param2: type = default)"
  - "AnotherTool(param: str)"
```

### JSON Format

```json
{
  "tools": [
    "ToolName(param1: type, param2: type = default)",
    "AnotherTool(param: str)"
  ]
}
```

### Python Format

```python
# tools.py
ToolName(param1: type, param2: type = default)
AnotherTool(param: str)
```

## Advanced Features

### Custom Templates

Create custom templates in a directory:

```
templates/
  tool.jinja2
  agent.jinja2
  readme.jinja2
```

Use with: `stanley-codegen generate tools.yml --template-dir ./templates`

### Type Support

Supported parameter types:
- `str` - String values
- `int` - Integer values
- `float` - Floating point values
- `bool` - Boolean values
- `list` - List/array values
- `dict` - Dictionary/object values
- `Any` - Any type

### Error Messages

Stanley Codegen provides helpful error messages:

```
Error: Invalid tool signature: 'BadTool'
Expected format: ToolName(param: type, param: type = default)
```

## Design Philosophy

Stanley Codegen follows best practices from world-class libraries:

- **Click** - Excellent CLI design and help system
- **FastAPI** - Type hints and automatic validation
- **Pydantic** - Robust data validation and error messages
- **Rich** - Beautiful terminal output and progress bars
- **Django** - Clear project structure and conventions

## Development

Run tests:
```bash
pytest
```

Format code:
```bash
ruff format .
ruff check . --fix
```

## License

MIT License
