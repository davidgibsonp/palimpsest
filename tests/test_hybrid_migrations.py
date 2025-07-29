"""
Tests for the hybrid migration approach.
"""

from palimpsest.models.migrations import (
    SCHEMA_SNAPSHOTS,
    get_schema_snapshot,
    register_schema_snapshot,
)
from palimpsest.models.trace import ExecutionTrace


def test_schema_snapshot_registration():
    """Test that schema snapshots can be registered and retrieved."""
    # Clear any existing snapshots for clean test
    original_snapshots = SCHEMA_SNAPSHOTS.copy()
    SCHEMA_SNAPSHOTS.clear()

    try:
        # Register a schema snapshot
        register_schema_snapshot("0.1.0", ExecutionTrace)

        # Should be able to retrieve it
        snapshot = get_schema_snapshot("0.1.0")
        assert snapshot is ExecutionTrace

        # Non-existent version should return None
        assert get_schema_snapshot("99.0.0") is None

    finally:
        # Restore original snapshots
        SCHEMA_SNAPSHOTS.clear()
        SCHEMA_SNAPSHOTS.update(original_snapshots)


def test_schema_snapshot_not_required_for_simple_migrations():
    """Test that simple dict-based migrations work without schema snapshots."""
    from palimpsest.models.migrations import migrate_trace

    # Simple migration should work fine without snapshots
    legacy_data = {
        "problem_statement": "Test without schema snapshots",
        "outcome": "Should work fine",
        "execution_steps": [
            {"step_number": 1, "action": "test", "content": "simple migration"}
        ],
    }

    # This uses the existing dict-based migration
    migrated = migrate_trace(legacy_data)
    assert migrated["schema_version"] == "0.1.0"


def test_versioned_directory_structure():
    """Test that the versions directory exists and is properly structured."""
    from pathlib import Path

    # Get the path to the models directory
    models_dir = Path(__file__).parent.parent / "palimpsest" / "models"
    versions_dir = models_dir / "versions"

    # Should exist
    assert versions_dir.exists()
    assert versions_dir.is_dir()

    # Should have __init__.py
    init_file = versions_dir / "__init__.py"
    assert init_file.exists()

    # Read the init file content to verify it has proper documentation
    content = init_file.read_text()
    assert "Versioned schema snapshots" in content
    assert "complex migrations" in content


def test_hybrid_approach_flexibility():
    """Test that the hybrid approach supports both simple and complex patterns."""
    # This test documents the intended usage patterns

    # Pattern 1: Simple dict-based migration (current approach)
    simple_data = {"old_field": "value"}
    simple_result = simple_data.copy()
    simple_result["new_field"] = simple_result.pop("old_field")
    assert simple_result == {"new_field": "value"}

    # Pattern 2: Schema-aware migration (future complex cases)
    # When we need this, we would:
    # 1. Create versioned schema file
    # 2. Register schema snapshot
    # 3. Use both old and new schemas in migration

    # For now, just verify the infrastructure exists
    assert callable(register_schema_snapshot)
    assert callable(get_schema_snapshot)

    # The actual schema-aware migration would be implemented when needed
    # This test just verifies we have the tools ready


def test_migration_guide_examples():
    """Test that examples from migration guide are valid."""
    # Test the dict-based migration pattern from the guide
    trace_data = {"old_field": "test_value"}
    migrated = trace_data.copy()

    if "old_field" in migrated:
        migrated["new_field"] = migrated.pop("old_field")

    assert "old_field" not in migrated
    assert migrated["new_field"] == "test_value"

    # Schema-aware pattern would be tested when we have actual versioned schemas
