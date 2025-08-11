# Palimpsest

<div align="center">

**Their model. Your code. Your work.**

[![Development Status](https://img.shields.io/badge/Status-Pre--Alpha-red)](https://github.com/damiangibson/meta-palimpsest)
[![Python Version](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/Version-0.0.4-blue)](https://github.com/damiangibson/meta-palimpsest/releases)

</div>

## The Problem

```bash
Developer: "How did I fix that async timeout issue last month?"
AI: "I don't remember your previous conversations..."
Developer: *scrolls through 47 chat histories* 😵‍💫
```

## The Solution

What if your AI coding assistant could learn from every session you've ever had?

Palimpsest captures the traces of your AI collaboration sessions. The breakthrough moments. The dead ends. The "aha!" discoveries.

**Your debugging wisdom, preserved.**

> **Warning**: This project is in early development. APIs are unstable and subject to change.

## Get Started

```bash
# Install with pip
pip install palimpsest

# Or use uv (recommended)
uv pip install palimpsest
```

### CLI Usage

```bash
# Initialize palimpsest in your project
palimpsest init

# Add a trace from a JSON file
palimpsest add trace_file.json

# Search your traces
palimpsest search "full-text search"

# List recent traces
palimpsest list

# Show detailed trace information
palimpsest show <trace-id>

# See collection statistics
palimpsest stats
```

#### Example Trace Data

```bash
echo '{
  "problem_statement": "How to optimize database queries in Django ORM?",
  "outcome": "Implemented select_related and prefetch_related optimizations",
  "execution_steps": [
    {
      "step_number": 1,
      "action": "analyze", 
      "content": "Profiled slow queries using Django Debug Toolbar"
    },
    {
      "step_number": 2,
      "action": "implement",
      "content": "Added select_related for foreign keys, prefetch_related for many-to-many"
    }
  ],
  "tags": ["django", "orm", "performance", "optimization"],
  "domain": "backend"
}' > trace_file.json
```

### MCP Server for AI Agents (In Development)

```bash
# Start MCP server for AI integration
palimpsest server start
```

## Features

🔬 **Local-first** - Your traces stay on your machine  
🔍 **Searchable** - Fast full-text search with SQLite FTS5  
🤝 **Shareable** - Help others (when you want to)  
🧠 **Smart** - AI assistants that actually remember and learn  
⚡ **Fast** - <1s response time for typical operations  

## Get Involved

⭐ **Star to follow progress**
💬 **Questions? Ideas?** [Open an issue](https://github.com/damiangibson/meta-palimpsest/issues)
🔧 **Want to contribute?** See our [contribution guidelines](https://github.com/damiangibson/meta-palimpsest/blob/main/CONTRIBUTING.md)

---

_Like a palimpsest, where traces of previous writings remain beneath new text._
