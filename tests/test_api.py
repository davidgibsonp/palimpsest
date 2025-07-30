"""
API layer tests for Palimpsest.

Tests the stateless function-based API for external consumption.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from palimpsest.api import (
    create_trace,
    delete_trace,
    get_stats,
    get_trace,
    list_traces,
    rebuild_index,
    search_traces,
    validate_trace,
)
from palimpsest.exceptions import PalimpsestError, ValidationError


@pytest.fixture
def temp_path():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_trace() -> Dict[str, Any]:
    """Create a sample trace for testing."""
    return {
        "problem_statement": "Need to test the API functions work correctly",
        "outcome": "Successfully tested all API functions with proper error handling",
        "execution_steps": [
            {
                "step_number": 1,
                "action": "analyze",
                "content": "Analyzed API function requirements",
            },
            {
                "step_number": 2,
                "action": "implement",
                "content": "Implemented comprehensive API tests",
            },
            {
                "step_number": 3,
                "action": "test",
                "content": "Validated all API functions work correctly",
            },
        ],
        "context": {"tags": ["testing", "api", "validation"]},
    }


def test_create_trace_success(temp_path, sample_trace):
    """Test successful trace creation."""
    trace_id = create_trace(sample_trace, auto_context=False, base_path=temp_path)

    assert trace_id
    assert isinstance(trace_id, str)
    assert len(trace_id) > 0


def test_create_trace_with_auto_context(temp_path, sample_trace):
    """Test trace creation with automatic environment context."""
    trace_id = create_trace(sample_trace, auto_context=True, base_path=temp_path)

    # Retrieve the trace to verify context was added
    trace = get_trace(trace_id, base_path=temp_path)
    assert "environment" in trace["context"]
    assert "python_version" in trace["context"]["environment"]
    assert "os_platform" in trace["context"]["environment"]


def test_create_trace_validation_error(temp_path):
    """Test trace creation with invalid data."""
    invalid_trace = {
        "outcome": "Missing problem_statement should cause validation error",
        "execution_steps": [],
    }

    with pytest.raises((ValidationError, PalimpsestError)):
        create_trace(invalid_trace, base_path=temp_path)


def test_get_trace_success(temp_path, sample_trace):
    """Test successful trace retrieval."""
    trace_id = create_trace(sample_trace, auto_context=False, base_path=temp_path)

    retrieved_trace = get_trace(trace_id, base_path=temp_path)

    assert isinstance(retrieved_trace, dict)
    assert retrieved_trace["problem_statement"] == sample_trace["problem_statement"]
    assert retrieved_trace["outcome"] == sample_trace["outcome"]
    assert len(retrieved_trace["execution_steps"]) == 3
    assert retrieved_trace["context"]["trace_id"] == trace_id


def test_get_trace_not_found(temp_path):
    """Test retrieving non-existent trace."""
    with pytest.raises(PalimpsestError):
        get_trace("non-existent-id", base_path=temp_path)


def test_search_traces_success(temp_path, sample_trace):
    """Test successful trace search."""
    # Create traces with different content
    trace1 = dict(sample_trace)
    trace1["problem_statement"] = "Frontend performance optimization needed"
    trace1["context"]["tags"] = ["frontend", "performance"]

    trace2 = dict(sample_trace)
    trace2["problem_statement"] = "Backend API response time improvement"
    trace2["context"]["tags"] = ["backend", "api"]

    id1 = create_trace(trace1, auto_context=False, base_path=temp_path)
    id2 = create_trace(trace2, auto_context=False, base_path=temp_path)

    # Search for "frontend"
    results = search_traces("frontend", base_path=temp_path)
    assert len(results) >= 1
    result_ids = [r["context"]["trace_id"] for r in results]
    assert id1 in result_ids

    # Search for "backend"
    results = search_traces("backend", base_path=temp_path)
    assert len(results) >= 1
    result_ids = [r["context"]["trace_id"] for r in results]
    assert id2 in result_ids


def test_search_traces_with_filters(temp_path, sample_trace):
    """Test trace search with filters."""
    create_trace(sample_trace, auto_context=False, base_path=temp_path)

    # Search with filters (basic test - actual filter implementation may vary)
    results = search_traces("API", filters={"tags": ["api"]}, base_path=temp_path)
    assert isinstance(results, list)


def test_search_traces_with_limit(temp_path, sample_trace):
    """Test trace search with result limit."""
    # Create multiple traces
    for i in range(5):
        trace = dict(sample_trace)
        trace["problem_statement"] = f"Problem {i}: {trace['problem_statement']}"
        create_trace(trace, auto_context=False, base_path=temp_path)

    # Search with limit
    results = search_traces("test", limit=3, base_path=temp_path)
    assert len(results) <= 3


def test_list_traces_success(temp_path, sample_trace):
    """Test successful trace listing."""
    # Create multiple traces
    trace_ids = []
    for i in range(3):
        trace = dict(sample_trace)
        trace["problem_statement"] = f"Problem {i}: {trace['problem_statement']}"
        trace_id = create_trace(trace, auto_context=False, base_path=temp_path)
        trace_ids.append(trace_id)

    # List all traces
    traces = list_traces(base_path=temp_path)
    assert len(traces) == 3

    # Verify all traces are present
    listed_ids = [t["context"]["trace_id"] for t in traces]
    for trace_id in trace_ids:
        assert trace_id in listed_ids


def test_list_traces_with_limit(temp_path, sample_trace):
    """Test trace listing with limit."""
    # Create multiple traces
    for i in range(5):
        trace = dict(sample_trace)
        trace["problem_statement"] = f"Problem {i}: {trace['problem_statement']}"
        create_trace(trace, auto_context=False, base_path=temp_path)

    # List with limit
    traces = list_traces(limit=3, base_path=temp_path)
    assert len(traces) <= 3


def test_delete_trace_success(temp_path, sample_trace):
    """Test successful trace deletion."""
    trace_id = create_trace(sample_trace, auto_context=False, base_path=temp_path)

    # Verify trace exists
    trace = get_trace(trace_id, base_path=temp_path)
    assert trace["context"]["trace_id"] == trace_id

    # Delete trace
    result = delete_trace(trace_id, base_path=temp_path)
    assert result is True

    # Verify trace is gone
    with pytest.raises(PalimpsestError):
        get_trace(trace_id, base_path=temp_path)


def test_delete_trace_not_found(temp_path):
    """Test deleting non-existent trace."""
    with pytest.raises(PalimpsestError):
        delete_trace("non-existent-id", base_path=temp_path)


def test_validate_trace_success(sample_trace):
    """Test successful trace validation."""
    is_valid, errors = validate_trace(sample_trace)

    assert is_valid is True
    assert errors == []


def test_validate_trace_failure():
    """Test trace validation with invalid data."""
    invalid_trace = {
        "outcome": "Missing problem_statement",
        "execution_steps": [],
    }

    is_valid, errors = validate_trace(invalid_trace)

    assert is_valid is False
    assert len(errors) > 0
    assert isinstance(errors, list)
    assert all(isinstance(error, str) for error in errors)


def test_validate_trace_with_invalid_action():
    """Test trace validation with invalid action type."""
    invalid_trace = {
        "problem_statement": "Test problem",
        "outcome": "Test outcome",
        "execution_steps": [
            {
                "step_number": 1,
                "action": "invalid_action",  # Invalid action
                "content": "Test content",
            }
        ],
    }

    is_valid, errors = validate_trace(invalid_trace)

    assert is_valid is False
    assert len(errors) > 0


def test_get_stats_success(temp_path, sample_trace):
    """Test getting statistics."""
    # Create some traces
    for i in range(3):
        trace = dict(sample_trace)
        trace["problem_statement"] = f"Problem {i}: {trace['problem_statement']}"
        if i % 2 == 0:
            trace["context"]["tags"] = ["even", "testing"]
        else:
            trace["context"]["tags"] = ["odd", "testing"]
        create_trace(trace, auto_context=False, base_path=temp_path)

    # Get stats
    stats = get_stats(base_path=temp_path)

    assert isinstance(stats, dict)
    assert "count" in stats
    assert stats["count"] == 3
    assert "storage_size_bytes" in stats
    assert stats["storage_size_bytes"] > 0
    assert "updated_at" in stats


def test_rebuild_index_success(temp_path, sample_trace):
    """Test rebuilding the search index."""
    # Create some traces
    trace_count = 5
    for i in range(trace_count):
        trace = dict(sample_trace)
        trace["problem_statement"] = f"Problem {i}: {trace['problem_statement']}"
        create_trace(trace, auto_context=False, base_path=temp_path)

    # Rebuild index
    indexed_count = rebuild_index(base_path=temp_path)

    assert indexed_count == trace_count

    # Verify search still works
    results = search_traces("test", base_path=temp_path)
    assert len(results) > 0


def test_api_functions_return_serializable_data(temp_path, sample_trace):
    """Test that all API functions return JSON-serializable data."""
    import json

    trace_id = create_trace(sample_trace, auto_context=False, base_path=temp_path)

    # Test get_trace returns serializable data
    trace = get_trace(trace_id, base_path=temp_path)
    json.dumps(trace)  # Should not raise exception

    # Test search_traces returns serializable data
    results = search_traces("test", base_path=temp_path)
    json.dumps(results)  # Should not raise exception

    # Test list_traces returns serializable data
    traces = list_traces(base_path=temp_path)
    json.dumps(traces)  # Should not raise exception

    # Test get_stats returns serializable data
    stats = get_stats(base_path=temp_path)
    json.dumps(stats)  # Should not raise exception


def test_api_functions_type_consistency(temp_path, sample_trace):
    """Test that API functions return consistent types."""
    trace_id = create_trace(sample_trace, auto_context=False, base_path=temp_path)

    # create_trace should return string
    assert isinstance(trace_id, str)

    # get_trace should return dict
    trace = get_trace(trace_id, base_path=temp_path)
    assert isinstance(trace, dict)

    # search_traces should return list of dicts
    results = search_traces("test", base_path=temp_path)
    assert isinstance(results, list)
    assert all(isinstance(result, dict) for result in results)

    # list_traces should return list of dicts
    traces = list_traces(base_path=temp_path)
    assert isinstance(traces, list)
    assert all(isinstance(trace, dict) for trace in traces)

    # validate_trace should return tuple of (bool, list)
    is_valid, errors = validate_trace(sample_trace)
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)

    # delete_trace should return bool
    result = delete_trace(trace_id, base_path=temp_path)
    assert isinstance(result, bool)

    # get_stats should return dict
    stats = get_stats(base_path=temp_path)
    assert isinstance(stats, dict)

    # rebuild_index should return int
    count = rebuild_index(base_path=temp_path)
    assert isinstance(count, int)


def test_error_handling_provides_meaningful_messages(temp_path):
    """Test that error messages are helpful for debugging."""
    # Test with completely invalid trace data
    try:
        create_trace({"invalid": "data"}, base_path=temp_path)
        assert False, "Should have raised exception"
    except (ValidationError, PalimpsestError) as e:
        error_msg = str(e)
        assert len(error_msg) > 0
        assert (
            "problem_statement" in error_msg.lower()
            or "validation" in error_msg.lower()
        )

    # Test getting non-existent trace
    try:
        get_trace("does-not-exist", base_path=temp_path)
        assert False, "Should have raised exception"
    except PalimpsestError as e:
        error_msg = str(e)
        assert len(error_msg) > 0
        assert "does-not-exist" in error_msg or "not found" in error_msg.lower()
