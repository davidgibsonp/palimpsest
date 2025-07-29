"""
Tests for TraceFileManager.
"""

import json
import tempfile
from pathlib import Path

import pytest

from palimpsest.exceptions import StorageError
from palimpsest.models.trace import ExecutionStep, ExecutionTrace
from palimpsest.storage.file_manager import TraceFileManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def file_manager(temp_dir):
    """Create a TraceFileManager with temporary directory."""
    return TraceFileManager(base_path=temp_dir)


@pytest.fixture
def sample_trace():
    """Create a sample ExecutionTrace for testing."""
    return ExecutionTrace(
        problem_statement="Test file manager operations",
        outcome="File operations work correctly",
        execution_steps=[
            ExecutionStep(step_number=1, action="test", content="create sample trace")
        ],
        domain="testing",
        complexity="simple",
    )


def test_file_manager_initialization(temp_dir):
    """Test that TraceFileManager creates required directories."""
    fm = TraceFileManager(base_path=temp_dir)

    # Directories should be created
    assert fm.palimpsest_dir.exists()
    assert fm.traces_dir.exists()
    assert fm.logs_dir.exists()

    # Paths should be correct (resolve both sides for symlink compatibility)
    assert fm.palimpsest_dir == (temp_dir / ".palimpsest").resolve()
    assert fm.traces_dir == (temp_dir / ".palimpsest" / "traces").resolve()
    assert fm.logs_dir == (temp_dir / ".palimpsest" / "logs").resolve()


def test_save_and_load_trace(file_manager, sample_trace):
    """Test saving and loading a trace."""
    # Save trace
    trace_id = file_manager.save_trace(sample_trace)

    # Should generate a valid trace ID
    assert trace_id
    assert isinstance(trace_id, str)

    # File should exist
    trace_path = file_manager.get_trace_path(trace_id)
    assert trace_path.exists()

    # Load trace
    loaded_trace = file_manager.load_trace(trace_id)

    # Should be equivalent
    assert loaded_trace.problem_statement == sample_trace.problem_statement
    assert loaded_trace.outcome == sample_trace.outcome
    assert len(loaded_trace.execution_steps) == 1
    assert loaded_trace.domain == "testing"
    assert loaded_trace.complexity == "simple"
    assert loaded_trace.schema_version == "0.1.0"


def test_trace_id_generation(file_manager):
    """Test that trace IDs are unique and properly formatted."""
    trace_ids = set()

    # Generate multiple trace IDs
    for _ in range(10):
        trace_id = file_manager._generate_trace_id()
        trace_ids.add(trace_id)

    # Should all be unique
    assert len(trace_ids) == 10

    # Should follow expected format (YYYYMMDD_HHMMSS_uuid)
    for trace_id in trace_ids:
        parts = trace_id.split("_")
        assert len(parts) == 3
        assert len(parts[0]) == 8  # YYYYMMDD
        assert len(parts[1]) == 6  # HHMMSS
        assert len(parts[2]) == 8  # UUID prefix


def test_delete_trace(file_manager, sample_trace):
    """Test deleting a trace."""
    # Save trace
    trace_id = file_manager.save_trace(sample_trace)
    assert file_manager.trace_exists(trace_id)

    # Delete trace
    result = file_manager.delete_trace(trace_id)
    assert result is True
    assert not file_manager.trace_exists(trace_id)

    # Delete non-existent trace
    result = file_manager.delete_trace("nonexistent")
    assert result is False


def test_list_traces(file_manager, sample_trace):
    """Test listing traces."""
    # Initially empty
    assert file_manager.list_traces() == []

    # Save multiple traces
    trace_ids = []
    for i in range(5):
        trace = ExecutionTrace(
            problem_statement=f"Test trace {i}",
            outcome="Success",
            execution_steps=[
                ExecutionStep(step_number=1, action="test", content=f"test {i}")
            ],
        )
        trace_id = file_manager.save_trace(trace)
        trace_ids.append(trace_id)

    # List all traces
    listed_traces = file_manager.list_traces()
    assert len(listed_traces) == 5
    assert set(listed_traces) == set(trace_ids)

    # List with limit
    limited_traces = file_manager.list_traces(limit=3)
    assert len(limited_traces) == 3
    assert all(tid in trace_ids for tid in limited_traces)


def test_load_nonexistent_trace(file_manager):
    """Test loading a trace that doesn't exist."""
    with pytest.raises(StorageError, match="Trace nonexistent not found"):
        file_manager.load_trace("nonexistent")


def test_atomic_write_safety(file_manager, sample_trace):
    """Test that writes are atomic (no partial files on failure)."""
    # This is hard to test directly, but we can verify the basic mechanism
    trace_id = file_manager.save_trace(sample_trace)
    trace_path = file_manager.get_trace_path(trace_id)

    # File should exist and be valid JSON
    assert trace_path.exists()
    with open(trace_path, "r") as f:
        data = json.load(f)
    assert "problem_statement" in data


# Removed get_trace_stats and cleanup_corrupted_files tests
# These methods were removed to simplify the API for MVP


def test_migration_on_load(file_manager, temp_dir):
    """Test that old traces are migrated when loaded."""
    # Create a legacy trace file (without schema_version)
    legacy_data = {
        "problem_statement": "Legacy trace without version",
        "outcome": "Should be migrated on load",
        "execution_steps": [
            {"step_number": 1, "action": "legacy", "content": "old format"}
        ],
    }

    # Write legacy file directly
    traces_dir = temp_dir / ".palimpsest" / "traces"
    legacy_file = traces_dir / "legacy_trace.json"
    with open(legacy_file, "w") as f:
        json.dump(legacy_data, f)

    # Load trace - should trigger migration
    loaded_trace = file_manager.load_trace("legacy_trace")

    # Should be migrated to current version
    assert loaded_trace.schema_version == "0.1.0"
    assert loaded_trace.problem_statement == legacy_data["problem_statement"]
    assert loaded_trace.context.environment["migrated_from"] == "0.0.1"


def test_concurrent_operations(file_manager):
    """Test basic thread safety assumptions."""
    import threading

    results = []
    errors = []

    def save_trace(i):
        try:
            trace = ExecutionTrace(
                problem_statement=f"Concurrent trace {i}",
                outcome="Success",
                execution_steps=[
                    ExecutionStep(
                        step_number=1, action="concurrent", content=f"thread {i}"
                    )
                ],
            )
            trace_id = file_manager.save_trace(trace)
            results.append(trace_id)
        except Exception as e:
            errors.append(e)

    # Start multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=save_trace, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    # Should have no errors and all traces saved
    assert len(errors) == 0
    assert len(results) == 5
    assert len(set(results)) == 5  # All unique trace IDs
