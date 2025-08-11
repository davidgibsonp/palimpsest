# Quick Start Guide

## Installation

```bash
cd palimpsest/
uv sync    # Install all dependencies
```

## 1. Initialize Project

```bash
palimpsest init
# ✓ Initialized Palimpsest at /path/to/.palimpsest
```

## 2. Create Your First Trace

Create `my_trace.json`:

```json
{
  "problem_statement": "How to implement user authentication in FastAPI?",
  "outcome": "Successfully implemented JWT-based auth with refresh tokens",
  "execution_steps": [
    {
      "step_number": 1,
      "action": "analyze",
      "content": "Researched FastAPI security patterns and JWT libraries"
    },
    {
      "step_number": 2,
      "action": "implement",
      "content": "Created auth routes with python-jose for JWT handling"
    },
    {
      "step_number": 3,
      "action": "test",
      "content": "Added tests for login, token refresh, and protected routes"
    }
  ],
  "tags": ["fastapi", "authentication", "jwt", "security"],
  "domain": "backend"
}
```

Add it:

```bash
palimpsest add my_trace.json
# ✓ Created trace: abc123...
```

## 3. Search and Browse

```bash
# List recent traces
palimpsest list

# Search for solutions
palimpsest search "authentication"
palimpsest search "FastAPI" --domain backend

# View full details
palimpsest show abc123...

# Collection stats
palimpsest stats
```

## 4. For AI Agents

```bash
# Start MCP server
palimpsest server start

# AI agents can now use 5 MCP tools:
# - create_trace(), search_traces(), get_trace()
# - list_traces(), get_stats()
```

## That's It

You're now preserving AI development workflows. The code is your documentation - see `palimpsest/` for implementation details.
