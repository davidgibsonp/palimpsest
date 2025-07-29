"""
Schema migration framework for ExecutionTrace models.

Handles backward compatibility and schema evolution across versions.
Supports both simple dict-based migrations and complex schema-aware migrations.
"""

from typing import Callable, Dict, List, Optional

from loguru import logger
from packaging import version

from ..exceptions import ValidationError

# Current schema version
CURRENT_SCHEMA_VERSION = "0.1.0"

# Registry of migration functions
MIGRATIONS: Dict[str, Callable[[dict], dict]] = {}

# Registry of schema snapshots for complex migrations (added when needed)
SCHEMA_SNAPSHOTS: Dict[str, type] = {}


def register_migration(from_version: str, to_version: str):
    """Decorator to register migration functions."""

    def decorator(func):
        key = f"{from_version}->{to_version}"
        MIGRATIONS[key] = func
        return func

    return decorator


def register_schema_snapshot(version_str: str, schema_class: type):
    """
    Register a schema snapshot for complex migrations.

    Args:
        version_str: Version string (e.g., "0.1.0")
        schema_class: Pydantic model class for that version

    Example:
        from .versions.v0_1_0 import ExecutionTrace as ExecutionTraceV010
        register_schema_snapshot("0.1.0", ExecutionTraceV010)
    """
    SCHEMA_SNAPSHOTS[version_str] = schema_class
    logger.info(f"Registered schema snapshot for version {version_str}")


def get_schema_snapshot(version_str: str) -> Optional[type]:
    """
    Get registered schema snapshot for a version.

    Args:
        version_str: Version string

    Returns:
        Schema class if registered, None otherwise
    """
    return SCHEMA_SNAPSHOTS.get(version_str)


def detect_schema_version(trace_data: dict) -> str:
    """
    Detect the schema version of trace data.

    Args:
        trace_data: Raw trace data dictionary

    Returns:
        Schema version string
    """
    # Check for explicit schema_version field (v0.1.0+)
    if "schema_version" in trace_data:
        return trace_data["schema_version"]

    # Pre-v0.1.0 traces have no schema_version field
    # We can add heuristics here to detect older versions
    return "0.0.1"  # Assume earliest version if no version field


def migrate_trace(trace_data: dict, target_version: str = None) -> dict:
    """
    Migrate trace data from its current version to target version.

    Args:
        trace_data: Raw trace data dictionary
        target_version: Target schema version (defaults to current)

    Returns:
        Migrated trace data dictionary

    Raises:
        ValidationError: If migration fails or path not found
    """
    if target_version is None:
        target_version = CURRENT_SCHEMA_VERSION

    current_version = detect_schema_version(trace_data)

    # No migration needed if versions match
    if current_version == target_version:
        return trace_data.copy()

    # Find migration path
    migration_path = find_migration_path(current_version, target_version)
    if not migration_path:
        raise ValidationError(
            f"No migration path found from {current_version} to {target_version}"
        )

    # Apply migrations sequentially
    migrated_data = trace_data.copy()
    for from_ver, to_ver in migration_path:
        migration_key = f"{from_ver}->{to_ver}"
        if migration_key not in MIGRATIONS:
            raise ValidationError(f"Missing migration function for {migration_key}")

        logger.info(f"Migrating trace from {from_ver} to {to_ver}")
        migrated_data = MIGRATIONS[migration_key](migrated_data)
        migrated_data["schema_version"] = to_ver

    return migrated_data


def find_migration_path(from_version: str, to_version: str) -> Optional[List[tuple]]:
    """
    Find the shortest migration path between two versions.

    Args:
        from_version: Starting version
        to_version: Target version

    Returns:
        List of (from, to) version tuples representing migration steps
    """
    # For now, implement simple direct migration
    # In the future, this could use graph algorithms for complex paths

    available_migrations = [key.split("->") for key in MIGRATIONS.keys()]

    # Check for direct migration
    for from_ver, to_ver in available_migrations:
        if from_ver == from_version and to_ver == to_version:
            return [(from_ver, to_ver)]

    # TODO: Implement multi-step migration path finding
    # For now, only support direct migrations
    return None


def is_migration_needed(trace_data: dict, target_version: str = None) -> bool:
    """
    Check if trace data needs migration to target version.

    Args:
        trace_data: Raw trace data dictionary
        target_version: Target schema version (defaults to current)

    Returns:
        True if migration is needed
    """
    if target_version is None:
        target_version = CURRENT_SCHEMA_VERSION

    current_version = detect_schema_version(trace_data)
    return current_version != target_version


# Example migration functions (will be populated as schema evolves)


@register_migration("0.0.1", "0.1.0")
def migrate_0_0_1_to_0_1_0(trace_data: dict) -> dict:
    """
    Migrate from pre-versioned traces to v0.1.0.

    Changes:
    - Adds schema_version field
    - Ensures all required fields exist with defaults
    """
    migrated = trace_data.copy()

    # Add schema version
    migrated["schema_version"] = "0.1.0"

    # Ensure context exists
    if "context" not in migrated:
        migrated["context"] = {
            "timestamp": "2025-01-01T00:00:00Z",  # Default timestamp
            "trace_id": f"migrated-{hash(str(trace_data))}",  # Generate ID
            "tags": [],
            "metadata": {"migrated_from": "0.0.1"},
        }

    # Ensure required fields exist
    if "success" not in migrated:
        migrated["success"] = True  # Assume success if not specified

    # Migrate any old field names or structures here
    # (none currently, but this is where they would go)

    return migrated


def validate_migration_compatibility():
    """
    Validate that all registered migrations are compatible.

    This can be run during startup to ensure migration integrity.
    """
    # Check that migration functions exist for all registered paths
    for migration_key in MIGRATIONS:
        from_ver, to_ver = migration_key.split("->")

        # Validate version format
        try:
            version.parse(from_ver)
            version.parse(to_ver)
        except Exception as e:
            raise ValidationError(
                f"Invalid version format in migration {migration_key}: {e}"
            )

        # Check function exists and is callable
        if not callable(MIGRATIONS[migration_key]):
            raise ValidationError(f"Migration {migration_key} is not callable")

    logger.info(f"Validated {len(MIGRATIONS)} migration functions")


# Run validation on import
validate_migration_compatibility()
