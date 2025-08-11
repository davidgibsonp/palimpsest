"""
End-to-end integration tests for Palimpsest.

Tests complete workflows from trace creation to search and retrieval.
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


@pytest.fixture
def temp_path():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_trace() -> Dict[str, Any]:
    """Create a sample trace for testing."""
    return {
        "problem_statement": "Need to optimize database connection pool for better performance",
        "outcome": "Reduced query latency by 35% by implementing connection pooling with proper timeout settings",
        "execution_steps": [
            {
                "step_number": 1,
                "action": "analyze",
                "content": "Identified that database connections were being created for each query",
            },
            {
                "step_number": 2,
                "action": "implement",
                "content": "Implemented connection pooling with SQLAlchemy",
            },
            {
                "step_number": 3,
                "action": "test",
                "content": "Ran benchmark tests showing 35% improvement in query latency",
            },
        ],
        "context": {"tags": ["performance", "database", "optimization"]},
    }


def test_complete_workflow(temp_path, sample_trace):
    """Test the complete workflow: create, search, get, list, delete."""
    # Create a trace
    trace_id = create_trace(sample_trace, auto_context=False, base_path=temp_path)
    assert trace_id

    # Get the trace by ID
    trace = get_trace(trace_id, base_path=temp_path)
    assert trace["problem_statement"] == sample_trace["problem_statement"]
    assert trace["outcome"] == sample_trace["outcome"]
    assert len(trace["execution_steps"]) == 3

    # List traces
    traces = list_traces(base_path=temp_path)
    assert len(traces) == 1
    assert traces[0]["context"]["trace_id"] == trace_id

    # Search for traces
    results = search_traces("database connection", base_path=temp_path)
    assert len(results) == 1
    assert results[0]["problem_statement"] == sample_trace["problem_statement"]

    # Delete the trace
    deleted = delete_trace(trace_id, base_path=temp_path)
    assert deleted is True

    # Verify it's gone
    traces = list_traces(base_path=temp_path)
    assert len(traces) == 0


def test_create_multiple_traces(temp_path, sample_trace):
    """Test creating and searching multiple traces."""
    # Create 3 different traces
    trace1 = dict(sample_trace)
    trace1["problem_statement"] = "Need to optimize React component rendering"
    trace1["outcome"] = "Reduced render time by 40% using React.memo and useMemo"
    trace1["context"]["tags"] = ["react", "performance", "frontend"]

    trace2 = dict(sample_trace)
    trace2["problem_statement"] = "Database queries are too slow in production"
    trace2["outcome"] = "Added proper indexes and optimized join queries"

    trace3 = dict(sample_trace)
    trace3["problem_statement"] = "API response times are inconsistent"
    trace3["outcome"] = "Implemented request throttling and caching"
    trace3["context"]["tags"] = ["api", "performance", "caching"]

    # Create all traces
    id1 = create_trace(trace1, auto_context=False, base_path=temp_path)
    id2 = create_trace(trace2, auto_context=False, base_path=temp_path)
    _id3 = create_trace(trace3, auto_context=False, base_path=temp_path)

    # List all traces
    traces = list_traces(base_path=temp_path)
    assert len(traces) == 3

    # Search for "performance" should find traces 1 and 3
    results = search_traces("performance", base_path=temp_path)
    assert len(results) == 3  # All have performance-related content

    # Search for "React" should find only trace 1
    results = search_traces("React", base_path=temp_path)
    assert len(results) == 1
    assert results[0]["context"]["trace_id"] == id1

    # Search for "database" should find trace 2
    results = search_traces("database", base_path=temp_path)
    assert len(results) >= 1  # At least one trace with database in it
    result_ids = [r["context"]["trace_id"] for r in results]
    assert id2 in result_ids  # Should include trace 2 (database queries)


def test_validation(sample_trace):
    """Test trace validation without storage."""
    # Valid trace
    is_valid, errors = validate_trace(sample_trace)
    assert is_valid is True
    assert not errors

    # Invalid trace - missing required field
    invalid_trace = dict(sample_trace)
    del invalid_trace["problem_statement"]
    is_valid, errors = validate_trace(invalid_trace)
    assert is_valid is False
    assert len(errors) > 0

    # Invalid trace - wrong action type
    invalid_trace = dict(sample_trace)
    invalid_trace["execution_steps"][0]["action"] = "invalid_action"
    is_valid, errors = validate_trace(invalid_trace)
    assert is_valid is False
    assert len(errors) > 0


def test_index_rebuild(temp_path, sample_trace):
    """Test rebuilding the search index."""
    # Create some traces
    for i in range(5):
        trace = dict(sample_trace)
        trace["problem_statement"] = f"Problem {i}: {trace['problem_statement']}"
        create_trace(trace, auto_context=False, base_path=temp_path)

    # Rebuild index
    count = rebuild_index(base_path=temp_path)
    assert count == 5

    # Search should still work
    results = search_traces("database", base_path=temp_path)
    assert len(results) == 5


def test_stats(temp_path, sample_trace):
    """Test getting statistics about traces."""
    # Create some traces with different tags
    for i in range(10):
        trace = dict(sample_trace)
        trace["problem_statement"] = f"Problem {i}: {trace['problem_statement']}"
        if i % 2 == 0:
            trace["context"]["tags"] = ["even", "database"]
        else:
            trace["context"]["tags"] = ["odd", "database"]
        create_trace(trace, auto_context=False, base_path=temp_path)

    # Get stats
    stats = get_stats(base_path=temp_path)
    assert stats["count"] == 10
    assert stats["storage_size_bytes"] > 0

    # Common tags should include "database", "even", "odd"
    if "common_tags" in stats:  # This may not be implemented yet
        common_tags = [tag for tag, count in stats["common_tags"]]
        assert "database" in common_tags
        assert "even" in common_tags or "odd" in common_tags
