# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.4] - 2025-08-10

### Added

- CLI interface with `palimpsest` command-line tool
- Model Context Protocol (MCP) server implementation
- CLI configuration and utility modules
- MCP server lifecycle management
- Comprehensive test coverage for CLI and MCP components
- Comprehensive documentation suite including API reference, architecture overview, interface layer guide, and quick start guide
- README improvements with correct repository links and installation instructions

### Changed

- Streamlined import statements across CLI and MCP modules
- Updated pyproject.toml and uv.lock for improved build configuration
- Updated .gitignore to include macOS specific files
- Improved README for clarity and formatting

## [0.0.3] - 2025-07-30

### Added

- TraceFileManager for JSON file-based persistence of ExecutionTrace objects
- TraceIndexer with SQLite-based full-text search (FTS5) capabilities
- Advanced search capabilities with metadata filtering
- Public API layer (palimpsest.api.core) for creating and managing traces
- Palimpsest Engine for coordinating storage and indexing operations
- Comprehensive test suite including integration and performance tests
- Code quality audit script

### Changed

- Improved SQL command formatting in indexer for better readability
- Enhanced migration system with better type hints and action definitions
- Refactored integration tests and migration handling

### Fixed

- Updated action types in migration tests for consistency

### Removed

- Unused search engine module

## [0.0.1] - 2025-07-29

### Added

- Initial project structure and configuration
- Core data models (ExecutionTrace, ExecutionStep, TraceContext)
- Pydantic-based model definitions with full type safety
- Schema migration system for backward compatibility
- Version management for trace schemas
- Exception handling with custom exception classes
- Basic test suite for models and migrations
- Contributing guidelines
- Project documentation (migration guide)
- Python 3.13+ support with uv package manager

---

## Historical Note

Versions 0.0.1 through 0.0.4 represent early development milestones and were not formally released. These entries document the project's evolution during initial development. Formal releases with tags will begin at v0.1.0.

[unreleased]: https://github.com/davidgibsonp/palimpsest/compare/af1ea5a...HEAD
[0.0.4]: https://github.com/davidgibsonp/palimpsest/commit/af1ea5a
[0.0.3]: https://github.com/davidgibsonp/palimpsest/commit/508837e
[0.0.1]: https://github.com/davidgibsonp/palimpsest/commit/9785bf2