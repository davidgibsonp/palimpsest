# Interface Layer Documentation

## Overview

Palimpsest provides two interfaces for accessing the same core functionality:

- **CLI**: Human-friendly command-line interface  
- **MCP Server**: AI agent integration via Model Context Protocol

Both interfaces are thin wrappers over `PalimpsestEngine`, ensuring consistent behavior.

## CLI Interface

### Installation & Setup

```bash
uv sync                    # Install dependencies
palimpsest init           # Initialize .palimpsest/ in current directory
```

### Core Commands

```bash
# Trace management
palimpsest add <file.json>        # Create trace from JSON file
palimpsest list [--limit N]       # List recent traces  
palimpsest show <trace-id>        # Show full trace details
palimpsest search "query"         # Full-text search traces

# Project management  
palimpsest stats                  # Collection statistics
palimpsest config show           # View configuration
palimpsest server start          # Start MCP server

# Output formats
palimpsest list --format json    # Machine-readable output
palimpsest search "query" --format json
```

### Trace File Format

```json
{
  "problem_statement": "Your question or problem (≥10 characters)",
  "outcome": "What was achieved (≥10 characters)",
  "execution_steps": [
    {
      "step_number": 1,
      "action": "analyze|implement|test|debug",
      "content": "Description of what was done"
    }
  ],
  "tags": ["tag1", "tag2"],
  "domain": "architecture|backend|frontend|data|security|devops"
}
```

## MCP Server Interface

### Starting the Server

```bash
palimpsest server start    # Starts with stdio transport (default)
```

### Available Tools

1. **create_trace(trace_data: dict) → str**
   - Creates new execution trace
   - Returns trace_id

2. **search_traces(query: str, filters: dict, limit: int) → List[dict]**  
   - Full-text search with optional filters
   - Filters: `{"tags": ["tag1"], "domain": "backend"}`

3. **get_trace(trace_id: str) → dict**
   - Retrieves complete trace by ID

4. **list_traces(limit: int) → List[dict]**
   - Lists recent traces, newest first

5. **get_stats() → dict**
   - Returns collection statistics

### Example Usage (AI Agent)

```python
# Create trace
trace_id = create_trace({
    "problem_statement": "How to optimize database queries?",
    "outcome": "Implemented query optimization patterns",
    "execution_steps": [...],
    "tags": ["database", "performance"],
    "domain": "backend"
})

# Search traces  
results = search_traces("database optimization", {"domain": "backend"}, 10)

# Get specific trace
trace = get_trace(trace_id)
```

## Architecture

```
┌─────────────────────────────────────────┐
│              Interfaces                 │
│  ┌─────────────┐   ┌─────────────────┐  │
│  │     CLI     │   │   MCP Server    │  │
│  │   (Click)   │   │   (FastMCP)     │  │
│  └─────────────┘   └─────────────────┘  │
└─────────────┬───────────────┬───────────┘
              │               │
         ┌────▼───────────────▼────┐
         │   PalimpsestEngine      │  ← Business Logic
         │                         │
         └────┬───────────────┬────┘
              │               │
    ┌─────────▼─┐         ┌───▼──────┐
    │TraceFile  │         │ Trace    │      ← Storage Layer
    │Manager    │         │ Indexer  │
    │(JSON)     │         │(SQLite)  │
    └───────────┘         └──────────┘
```

## Configuration

### Project Configuration

Located at `.palimpsest/config.yaml`:

```yaml
default_search_limit: 50
default_tags: ["development"]
log_level: "INFO"
```

### User Configuration  

Located at `~/.palimpsest/config.yaml`:

```yaml
default_search_limit: 20
preferred_format: "table"
```

## Error Handling

Common validation errors:

- **problem_statement**: Must be ≥10 characters
- **outcome**: Must be ≥10 characters  
- **action**: Must be one of: "analyze", "implement", "test", "debug"
- **JSON**: Must be valid JSON with required fields

## Performance

- **Response time**: <1s for typical operations
- **Search**: SQLite FTS5 handles 100+ traces efficiently
- **Concurrent access**: Thread-safe operations
- **Memory**: Minimal usage with proper cleanup
