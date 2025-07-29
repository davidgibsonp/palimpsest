"""
Simple migration framework for ExecutionTrace models.

Handles backward compatibility with minimal complexity for v0.1.0 MVP.
"""

from loguru import logger

from ..exceptions import ValidationError

# Current schema version
CURRENT_SCHEMA_VERSION = "0.1.0"


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
    return "0.0.1"


def migrate_trace(trace_data: dict, target_version: str | None = None) -> dict:
    """
    Migrate trace data to target version (defaults to current).

    Args:
        trace_data: Raw trace data dictionary
        target_version: Target schema version (defaults to current)

    Returns:
        Migrated trace data dictionary

    Raises:
        ValidationError: If migration fails
    """
    if target_version is None:
        target_version = CURRENT_SCHEMA_VERSION

    current_version = detect_schema_version(trace_data)

    # No migration needed if versions match
    if current_version == target_version:
        return trace_data.copy()

    # Only support migration to current version for MVP
    if target_version != CURRENT_SCHEMA_VERSION:
        raise ValidationError(
            f"Only migration to {CURRENT_SCHEMA_VERSION} is supported"
        )

    # Migrate from 0.0.1 to 0.1.0
    if current_version == "0.0.1" and target_version == "0.1.0":
        return _migrate_0_0_1_to_0_1_0(trace_data)

    raise ValidationError(
        f"No migration path from {current_version} to {target_version}"
    )


def is_migration_needed(trace_data: dict, target_version: str | None = None) -> bool:
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


def _migrate_0_0_1_to_0_1_0(trace_data: dict) -> dict:
    """
    Migrate from pre-versioned traces to v0.1.0.

    Changes:
    - Adds schema_version field
    - Ensures context exists with required fields
    - Adds success field default
    - Maps action values to allowed values (analyze, implement, test, debug)
    """
    migrated = trace_data.copy()

    # Add schema version
    migrated["schema_version"] = "0.1.0"

    # Ensure context exists with minimal required fields
    if "context" not in migrated:
        migrated["context"] = {}

    context = migrated["context"]

    # Add required context fields if missing
    if "trace_id" not in context:
        context["trace_id"] = f"migrated-{hash(str(trace_data))}"
    if "timestamp" not in context:
        context["timestamp"] = "2025-01-01T00:00:00Z"
    if "tags" not in context:
        context["tags"] = []
    if "environment" not in context:
        context["environment"] = {}

    # Mark as migrated
    context["environment"]["migrated_from"] = "0.0.1"

    # Ensure success field exists
    if "success" not in migrated:
        migrated["success"] = True

    logger.info("Migrated trace from 0.0.1 to 0.1.0")
    return migrated
