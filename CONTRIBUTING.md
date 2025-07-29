# Contributing to Palimpsest

Thank you for your interest in contributing to Palimpsest! This guide outlines our development standards and workflows to ensure consistent, maintainable code.

## Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Initial Setup

```bash
git clone https://github.com/davidgibsonp/palimpsest.git
cd palimpsest
uv sync
```

### Running Commands

Always use `uv` commands for consistency:

```bash
# Run Python scripts
uv run python script.py

# Execute tools that need project environment
uv run pytest tests/
uv run mypy palimpsest/

# Execute standalone tools
uvx pre-commit run --all-files

# Install dependencies
uv add package-name
uv add --dev package-name  # for development dependencies
```

## Code Quality Standards

### Formatting and Linting

We use `ruff` for linting and formatting, plus `isort` for import sorting:

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
uvx pre-commit install
```

All formatting and linting is handled automatically via pre-commit hooks:

```bash
git add .
git commit -m "feat: add new feature"  # Triggers automatic formatting
```

### Type Hints

- **Required**: All functions must have type hints for parameters and return values
- **Use modern syntax**: `list[str]` instead of `List[str]` (Python 3.13+)
- **Pydantic models**: Prefer Pydantic for data validation over basic types

```python
from pydantic import BaseModel

def search_traces(query: str, limit: int = 10) -> list[TraceResult]:
    """Search execution traces by query string."""
    pass
```

## File Organization

### Module Structure

- **Maximum file length**: ~200 lines per file
- **Single responsibility**: Each module focuses on one clear purpose
- **Clear naming**: Use descriptive names (`trace_storage.py`, not `utils.py`)

### Import Organization

Group imports with clear separation:

```python
# Standard library
import json
from pathlib import Path

# Third-party packages
from pydantic import BaseModel

# Local imports
from palimpsest.models import ExecutionTrace
from palimpsest.storage import TraceStorage
```

## Error Handling

### Custom Exceptions

Define domain-specific exceptions in `palimpsest/exceptions.py`:

```python
class PalimpsestError(Exception):
    """Base exception for all Palimpsest errors."""
    pass

class TraceValidationError(PalimpsestError):
    """Raised when trace data fails validation."""
    pass
```

### Error Messages

- **User-friendly**: Clear, actionable messages
- **Context-rich**: Include relevant details for debugging
- **Consistent format**: Standardized across all interfaces

```python
raise TraceValidationError(
    "Invalid trace format: missing required field 'problem_statement'. "
    "Expected format: {'problem_statement': 'Description of the problem'}"
)
```

### Logging

We use [loguru](https://loguru.readthedocs.io/) for robust, structured logging:

```python
from loguru import logger

# Configure logger in main module
logger.add("logs/palimpsest.log", rotation="10 MB", retention="30 days")

# Use throughout codebase
logger.info("Starting trace capture session")
logger.debug("Processing trace data: {data}", data=trace_dict)
logger.error("Failed to validate trace: {error}", error=str(e))
logger.warning("Search returned no results for query: {query}", query=search_term)
```

**Logging Guidelines**:

- **INFO**: User-facing operations and major state changes
- **DEBUG**: Detailed execution flow for troubleshooting
- **WARNING**: Recoverable issues that may need attention
- **ERROR**: Failures that prevent normal operation
- **Include context**: Use structured logging with relevant variables

## Testing Philosophy

### Test Coverage

- **Focus on core functionality**: Test business logic, not implementation details
- **Integration over unit**: Prefer tests that validate end-to-end workflows
- **Maintainable tests**: Simple, clear tests that won't break with refactoring

### Test Structure

```bash
tests/
├── test_models.py        # Pydantic model validation
├── test_storage.py       # Data persistence
├── test_search.py        # Search functionality
├── test_cli.py           # Command line interface
└── integration/          # End-to-end tests
    └── test_trace_workflow.py
```

### Running Tests

```bash
uv run pytest tests/                    # Run all tests
uv run pytest tests/test_storage.py     # Run specific test file
uv run pytest -v --cov=palimpsest      # Run with coverage
```

## Configuration Management

### Settings Pattern

Use Pydantic Settings for all configuration:

```python
from pydantic_settings import BaseSettings

class PalimpsestSettings(BaseSettings):
    trace_dir: Path = Path(".palimpsest/traces")
    max_search_results: int = 20
    debug: bool = False
    
    class Config:
        env_prefix = "PALIMPSEST_"
```

### Hierarchical Configuration

- **Environment variables**: Override defaults
- **Project config**: `.palimpsest/config.yaml`
- **Global config**: `~/.palimpsest/config.yaml`

## Documentation Standards

### Docstrings

Use Google-style docstrings:

```python
def create_trace(trace_data: dict) -> ExecutionTrace:
    """Create and validate a new execution trace.
    
    Args:
        trace_data: Raw trace data dictionary containing problem statement,
            execution steps, and outcome.
    
    Returns:
        Validated ExecutionTrace instance ready for storage.
        
    Raises:
        TraceValidationError: If trace_data fails validation requirements.
        
    Example:
        >>> trace = create_trace({
        ...     "problem_statement": "Debug async timeout",
        ...     "outcome": "success"
        ... })
    """
    pass
```

### README Structure

Each module should include a brief README explaining:

- Purpose and responsibility
- Key classes/functions
- Usage examples
- Integration points

## Git Workflow

### Commit Messages

Use conventional commit format:

```bash
feat: add MCP server for trace capture
fix: resolve search indexing performance issue
docs: update CLI usage examples
test: add integration tests for trace storage
```

### Branch Naming

- **Features**: `feature/trace-validation`
- **Bug fixes**: `fix/search-performance`
- **Documentation**: `docs/contributing-guide`

### Pull Request Guidelines

- **Small, focused changes**: One feature or fix per PR
- **Clear description**: What changed and why
- **Test coverage**: Include tests for new functionality
- **Documentation updates**: Update docs when adding features

## Performance Considerations

### Storage Optimization

- **Target scale**: Optimize for 1000s of traces per repository
- **Search performance**: <1 second response time for typical queries
- **Memory usage**: Minimize memory footprint for background processes

### Code Efficiency

- **Lazy loading**: Don't load data until needed
- **Caching**: Cache expensive operations when appropriate
- **Async patterns**: Use async/await for I/O operations

## Development Workflow

### Local Development Loop

1. Create feature branch: `git checkout -b feature/new-functionality`
2. Make changes with frequent commits
3. Run tests: `uvx pytest`
4. Format code: `uvx ruff format .`
5. Commit with conventional message
6. Push and create pull request

### Before Committing

Pre-commit hooks handle formatting and linting automatically, but you can run them manually:

```bash
uvx pre-commit run --all-files    # Run all pre-commit hooks
uv run pytest                     # Run tests
```

## Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Architecture questions and design discussions
- **Documentation**: Check `/docs` for detailed guides

---

By following these guidelines, you'll help maintain Palimpsest's code quality and ensure a great experience for all contributors.
