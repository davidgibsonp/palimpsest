# Architecture Overview

## Core Principle

**Three-layer separation**: Storage ↔ Engine ↔ Interface

## Layer Responsibilities

### Storage Layer (`palimpsest/storage/`)

- **TraceFileManager**: JSON persistence in `.palimpsest/traces/`
- **TraceIndexer**: SQLite FTS5 full-text search index
- Atomic writes, thread-safe operations

### Engine Layer (`palimpsest/engine.py`)

- **PalimpsestEngine**: Business logic orchestration
- Coordinates storage components
- Validates data models
- Single source of truth for operations

### Interface Layer (`palimpsest/cli/`, `palimpsest/mcp/`)

- **CLI**: Human-friendly commands (Click framework)
- **MCP Server**: AI agent protocol (FastMCP framework)  
- Thin wrappers over PalimpsestEngine
- No business logic duplication

## Data Flow

```
CLI Command / MCP Tool Call
        ↓
PalimpsestEngine
        ↓
TraceFileManager + TraceIndexer
        ↓
File System (.palimpsest/)
```

## Key Design Patterns

### Pydantic Models

All data structures use Pydantic for validation:

- `ExecutionTrace`: Core trace model
- `ExecutionStep`: Individual workflow steps
- `TraceContext`: Metadata and environment

### Error Handling

Custom exception hierarchy:

- `StorageError`: File system issues
- `IndexError`: Search/indexing problems  
- `ValidationError`: Data validation failures

### Configuration

Layered config system:

- Project: `.palimpsest/config.yaml`
- User: `~/.palimpsest/config.yaml`
- Environment variables
- CLI flags (highest priority)

## Directory Structure

```
.palimpsest/
├── traces/           # JSON trace files
│   ├── abc123.json
│   └── def456.json
├── palimpsest.db    # SQLite search index
├── logs/            # Operation logs
└── config.yaml      # Project configuration
```

## Thread Safety

- File operations use atomic writes (temp + rename)
- SQLite handles concurrent reads/writes
- Engine coordinates access patterns
- No shared mutable state between interfaces

## Extension Points

The architecture supports future extensions:

- **New Interfaces**: Web API, VS Code extension
- **Storage Backends**: Cloud storage, databases
- **Search Engines**: Elasticsearch, Vector search
- **Data Formats**: Markdown, XML export

All extensions integrate at the Engine layer, maintaining consistency.
