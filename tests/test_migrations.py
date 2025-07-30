"""
Tests for the simplified migration framework.
"""

import pytest

from palimpsest.exceptions import ValidationError
from palimpsest.models.migrations import (
    CURRENT_SCHEMA_VERSION,
    detect_schema_version,
    is_migration_needed,
    migrate_trace,
)
from palimpsest.models.trace import ExecutionStep, ExecutionTrace


def test_current_version_detection():
    """Test that current version traces are detected correctly."""
    trace_data = {
        "schema_version": "0.1.0",
        "problem_statement": "Test problem",
        "outcome": "Test outcome",
        "execution_steps": [
            {"step_number": 1, "action": "test", "content": "test content"}
        ],
    }

    version = detect_schema_version(trace_data)
    assert version == "0.1.0"


def test_legacy_version_detection():
    """Test that legacy traces without version are detected as 0.0.1."""
    trace_data = {
        "problem_statement": "Test problem",
        "outcome": "Test outcome",
        "execution_steps": [
            {"step_number": 1, "action": "test", "content": "test content"}
        ],
    }

    version = detect_schema_version(trace_data)
    assert version == "0.0.1"


def test_migration_from_0_0_1_to_0_1_0():
    """Test migration from legacy format to v0.1.0."""
    legacy_data = {
        "problem_statement": "Legacy trace without version",
        "outcome": "Successfully migrated",
        "execution_steps": [
            {"step_number": 1, "action": "test", "content": "legacy content"}
        ],
    }

    migrated = migrate_trace(legacy_data, "0.1.0")

    # Check that schema version was added
    assert migrated["schema_version"] == "0.1.0"

    # Check that context was added
    assert "context" in migrated
    assert "trace_id" in migrated["context"]
    assert "timestamp" in migrated["context"]
    assert migrated["context"]["environment"]["migrated_from"] == "0.0.1"

    # Check that success field was added
    assert migrated["success"] is True

    # Original data should be preserved
    assert migrated["problem_statement"] == legacy_data["problem_statement"]
    assert migrated["outcome"] == legacy_data["outcome"]
    assert len(migrated["execution_steps"]) == 1


def test_no_migration_needed_for_current_version():
    """Test that current version traces don't need migration."""
    current_data = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "problem_statement": "Current version trace",
        "outcome": "No migration needed",
        "execution_steps": [
            {"step_number": 1, "action": "test", "content": "current content"}
        ],
    }

    assert not is_migration_needed(current_data)

    # Migration should return the same data
    migrated = migrate_trace(current_data)
    assert migrated == current_data


def test_model_validate_with_migration():
    """Test that ExecutionTrace can validate and migrate legacy data."""
    legacy_data = {
        "problem_statement": "Legacy trace for validation test",
        "outcome": "Successfully validated with migration",
        "execution_steps": [
            {
                "step_number": 1,
                "action": "test",
                "content": "legacy validation content",
            }
        ],
    }

    # This should automatically migrate and validate
    trace = ExecutionTrace.model_validate_with_migration(legacy_data)

    assert trace.schema_version == CURRENT_SCHEMA_VERSION
    assert trace.problem_statement == legacy_data["problem_statement"]
    assert trace.context.environment["migrated_from"] == "0.0.1"
    assert trace.success is True


def test_unsupported_migration_target():
    """Test error handling for unsupported migration targets."""
    trace_data = {
        "schema_version": "0.1.0",
        "problem_statement": "Test problem",
        "outcome": "Should fail",
        "execution_steps": [{"step_number": 1, "action": "test", "content": "test"}],
    }

    with pytest.raises(ValidationError, match="Only migration to 0.1.0 is supported"):
        migrate_trace(trace_data, "0.2.0")


def test_unsupported_source_version():
    """Test error handling for unsupported source versions."""
    trace_data = {
        "schema_version": "99.0.0",  # Nonexistent version
        "problem_statement": "Test problem",
        "outcome": "Should fail",
        "execution_steps": [{"step_number": 1, "action": "test", "content": "test"}],
    }

    with pytest.raises(ValidationError, match="No migration path from 99.0.0 to 0.1.0"):
        migrate_trace(trace_data, "0.1.0")


def test_get_version_method():
    """Test that ExecutionTrace.get_version() returns correct version."""
    trace = ExecutionTrace(
        problem_statement="Test version method",
        outcome="Version retrieved",
        execution_steps=[
            ExecutionStep(step_number=1, action="test", content="version test")
        ],
    )

    assert trace.get_version() == "0.1.0"


def test_migration_preserves_optional_fields():
    """Test that migration preserves optional fields when present."""
    legacy_data = {
        "problem_statement": "Legacy with optional fields",
        "outcome": "Optional fields preserved",
        "execution_steps": [
            {"step_number": 1, "action": "test", "content": "test content"}
        ],
        "domain": "testing",
        "complexity": "simple",
        "context": {"git_branch": "test-branch", "tags": ["test", "migration"]},
    }

    migrated = migrate_trace(legacy_data)

    # Optional fields should be preserved
    assert migrated["domain"] == "testing"
    assert migrated["complexity"] == "simple"
    assert migrated["context"]["git_branch"] == "test-branch"
    assert migrated["context"]["tags"] == ["test", "migration"]
