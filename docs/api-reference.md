# API Reference

## CLI Commands

### `palimpsest init`

Initialize Palimpsest in current directory.

**Options:**

- `--force`: Overwrite existing .palimpsest directory

### `palimpsest add <file>`

Add trace from JSON file.

**Arguments:**

- `file`: Path to JSON trace file

**Example:**

```bash
palimpsest add my_trace.json
```

### `palimpsest list`

List recent traces.

**Options:**

- `--limit N`: Number of traces to show (default: 10)
- `--format FORMAT`: Output format (`table`, `json`)

### `palimpsest search <query>`

Search traces with full-text search.

**Arguments:**

- `query`: Search query string

**Options:**

- `--tags TAG1,TAG2`: Filter by tags
- `--domain DOMAIN`: Filter by domain
- `--limit N`: Max results (default: 10)
- `--format FORMAT`: Output format (`table`, `json`)

**Example:**

```bash
palimpsest search "authentication" --domain backend --limit 5
```

### `palimpsest show <trace-id>`

Display full trace details.

**Arguments:**

- `trace-id`: Trace identifier

**Options:**

- `--format FORMAT`: Output format (`detailed`, `json`)

### `palimpsest stats`

Show collection statistics.

### `palimpsest server start`

Start MCP server for AI agent integration.

**Options:**

- `--transport TRANSPORT`: Transport type (`stdio`)

### `palimpsest config`

Configuration management.

**Subcommands:**

- `show`: Display current configuration
- `init --type TYPE`: Initialize config (`user`, `project`)
- `set KEY VALUE`: Set configuration value

## MCP Tools

### `create_trace(trace_data: dict) → str`

Create new execution trace.

**Parameters:**

- `trace_data`: Trace data dictionary

**Returns:** Trace ID string

**Example:**

```python
trace_id = create_trace({
    "problem_statement": "How to implement caching?",
    "outcome": "Added Redis caching layer",
    "execution_steps": [
        {
            "step_number": 1,
            "action": "analyze",
            "content": "Analyzed caching requirements"
        }
    ],
    "tags": ["redis", "caching"],
    "domain": "backend"
})
```

### `search_traces(query: str, filters: dict = {}, limit: int = 10) → List[dict]`

Search traces with optional filters.

**Parameters:**

- `query`: Search query string
- `filters`: Optional filters dict
  - `tags`: List of tags to filter by
  - `domain`: Domain to filter by
- `limit`: Maximum results

**Returns:** List of trace dictionaries

**Example:**

```python
results = search_traces(
    "database optimization",
    {"domain": "backend", "tags": ["performance"]},
    5
)
```

### `get_trace(trace_id: str) → dict`

Retrieve complete trace by ID.

**Parameters:**

- `trace_id`: Trace identifier

**Returns:** Full trace dictionary

### `list_traces(limit: int = 10) → List[dict]`

List recent traces in chronological order.

**Parameters:**

- `limit`: Maximum traces to return

**Returns:** List of trace dictionaries (newest first)

### `get_stats() → dict`

Get collection statistics.

**Returns:** Statistics dictionary with:

- `total_traces`: Total number of traces
- `total_size_mb`: Collection size in MB
- `all_tags`: Set of all tags used
- `all_domains`: Set of all domains used
- `date_range`: Oldest and newest trace timestamps

## Data Models

### ExecutionTrace

```python
{
    "trace_id": str,
    "problem_statement": str,  # ≥10 characters
    "outcome": str,           # ≥10 characters
    "execution_steps": List[ExecutionStep],
    "tags": List[str],
    "domain": str,            # One of: architecture, backend, frontend, data, security, devops
    "context": TraceContext
}
```

### ExecutionStep

```python
{
    "step_number": int,
    "action": str,           # One of: analyze, implement, test, debug
    "content": str,
    "timestamp": str,        # ISO format
    "metadata": dict         # Optional
}
```

### TraceContext

```python
{
    "timestamp": str,        # ISO format
    "trace_id": str,
    "environment": dict,     # System info
    "version": str          # Schema version
}
```

## Error Codes

- **ValidationError**: Invalid trace data format
- **StorageError**: File system operation failed
- **IndexError**: Search index operation failed
- **NotFoundError**: Trace ID not found
- **ConfigurationError**: Invalid configuration
