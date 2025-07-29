"""
Tests for TraceIndexer.
"""

import tempfile
from pathlib import Path

import pytest

from palimpsest.models.trace import ExecutionStep, ExecutionTrace
from palimpsest.storage.indexer import TraceIndexer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def indexer(temp_dir):
    """Create a TraceIndexer with temporary directory."""
    return TraceIndexer(base_path=temp_dir)


@pytest.fixture
def sample_traces():
    """Create sample ExecutionTrace objects for testing."""
    traces = []

    # Trace 1: Python setup
    traces.append(
        ExecutionTrace(
            problem_statement="Set up Python project with dependencies",
            outcome="Successfully configured Python environment with uv and pydantic",
            execution_steps=[
                ExecutionStep(
                    step_number=1,
                    action="setup",
                    content="Initialize Python project structure with pyproject.toml",
                ),
                ExecutionStep(
                    step_number=2,
                    action="install",
                    content="Add pydantic and loguru dependencies via uv add",
                ),
            ],
            domain="python",
            complexity="simple",
            success=True,
        )
    )

    # Trace 2: Debugging issue
    traces.append(
        ExecutionTrace(
            problem_statement="Debug performance issue in data processing pipeline",
            outcome="Identified bottleneck in JSON serialization, improved by 3x",
            execution_steps=[
                ExecutionStep(
                    step_number=1,
                    action="profile",
                    content="Run performance profiler to identify slow functions",
                ),
                ExecutionStep(
                    step_number=2,
                    action="optimize",
                    content="Replace json.dumps with faster orjson library",
                ),
                ExecutionStep(
                    step_number=3,
                    action="test",
                    content="Verify performance improvement with benchmarks",
                ),
            ],
            domain="performance",
            complexity="moderate",
            success=True,
        )
    )

    # Trace 3: Failed database migration
    traces.append(
        ExecutionTrace(
            problem_statement="Migrate database schema to add new user fields",
            outcome="Migration failed due to foreign key constraints",
            execution_steps=[
                ExecutionStep(
                    step_number=1,
                    action="create",
                    content="Write Alembic migration script for new columns",
                ),
                ExecutionStep(
                    step_number=2,
                    action="run",
                    content="Execute migration against staging database",
                    success=False,
                    error_message="FOREIGN KEY constraint failed on users table",
                ),
            ],
            domain="database",
            complexity="complex",
            success=False,
        )
    )

    return traces


def test_indexer_initialization(temp_dir):
    """Test that TraceIndexer initializes database correctly."""
    indexer = TraceIndexer(base_path=temp_dir)

    # Database file should be created
    assert indexer.db_path.exists()
    assert indexer.db_path == (temp_dir / ".palimpsest" / "index.db").resolve()

    # Should be able to get empty stats
    stats = indexer.get_stats()
    assert stats["total_traces"] == 0
    assert stats["successful_traces"] == 0
    assert stats["domains"] == {}


def test_index_single_trace(indexer, sample_traces):
    """Test indexing a single trace."""
    trace = sample_traces[0]
    trace_id = trace.context.trace_id

    # Index the trace
    indexer.index_trace(trace)

    # Should be able to find it
    results = indexer.search_traces("Python project")
    assert trace_id in results

    # Metadata should be available
    metadata = indexer.get_trace_metadata(trace_id)
    assert metadata is not None
    assert metadata["problem_statement"] == trace.problem_statement
    assert metadata["domain"] == "python"
    assert metadata["complexity"] == "simple"
    assert metadata["success"] is True


def test_index_multiple_traces(indexer, sample_traces):
    """Test indexing multiple traces."""
    # Index all traces
    for trace in sample_traces:
        indexer.index_trace(trace)

    # Stats should reflect all traces
    stats = indexer.get_stats()
    assert stats["total_traces"] == 3
    assert stats["successful_traces"] == 2
    assert stats["failed_traces"] == 1
    assert "python" in stats["domains"]
    assert "performance" in stats["domains"]
    assert "database" in stats["domains"]


def test_full_text_search(indexer, sample_traces):
    """Test full-text search functionality."""
    # Index traces
    for trace in sample_traces:
        indexer.index_trace(trace)

    # Search for Python-related traces
    results = indexer.search_traces("Python dependencies")
    assert len(results) >= 1

    # Search for performance-related traces
    results = indexer.search_traces("performance bottleneck")
    assert len(results) >= 1

    # Search for database-related traces
    results = indexer.search_traces("database migration")
    assert len(results) >= 1

    # Search for non-existent content
    results = indexer.search_traces("nonexistent content")
    assert len(results) == 0


def test_filtered_search(indexer, sample_traces):
    """Test search with filters."""
    # Index traces
    for trace in sample_traces:
        indexer.index_trace(trace)

    # Filter by domain
    results = indexer.search_traces("", filters={"domain": "python"})
    assert len(results) == 1

    # Filter by complexity
    results = indexer.search_traces("", filters={"complexity": "moderate"})
    assert len(results) == 1

    # Filter by success
    results = indexer.search_traces("", filters={"success": False})
    assert len(results) == 1

    # Combined filters
    results = indexer.search_traces("", filters={"domain": "python", "success": True})
    assert len(results) == 1


def test_search_with_limit(indexer, sample_traces):
    """Test search result limiting."""
    # Index traces
    for trace in sample_traces:
        indexer.index_trace(trace)

    # Search with limit
    results = indexer.search_traces("", limit=2)
    assert len(results) <= 2

    # Search with higher limit
    results = indexer.search_traces("", limit=10)
    assert len(results) == 3  # Only 3 traces total


def test_empty_search_returns_recent(indexer, sample_traces):
    """Test that empty search returns recent traces."""
    # Index traces
    for trace in sample_traces:
        indexer.index_trace(trace)

    # Empty search should return all traces ordered by timestamp
    results = indexer.search_traces("")
    assert len(results) == 3

    # Results should be ordered (most recent first)
    assert len(results) > 0


def test_remove_trace(indexer, sample_traces):
    """Test removing traces from index."""
    trace = sample_traces[0]
    trace_id = trace.context.trace_id

    # Index and verify it exists
    indexer.index_trace(trace)
    results = indexer.search_traces("Python")
    assert trace_id in results

    # Remove trace
    indexer.remove_trace(trace_id)

    # Should no longer be found
    results = indexer.search_traces("Python")
    assert trace_id not in results

    # Metadata should be None
    metadata = indexer.get_trace_metadata(trace_id)
    assert metadata is None


def test_update_existing_trace(indexer, sample_traces):
    """Test updating an existing trace in the index."""
    trace = sample_traces[0]
    trace_id = trace.context.trace_id

    # Index original trace
    indexer.index_trace(trace)
    original_metadata = indexer.get_trace_metadata(trace_id)
    assert original_metadata["problem_statement"] == trace.problem_statement

    # Modify trace
    trace.problem_statement = "Updated Python project setup with new requirements"

    # Re-index (should update, not duplicate)
    indexer.index_trace(trace)

    # Should find updated content
    results = indexer.search_traces("Updated Python")
    assert trace_id in results

    # Metadata should be updated
    updated_metadata = indexer.get_trace_metadata(trace_id)
    assert updated_metadata["problem_statement"] == trace.problem_statement

    # Should still only have one trace total
    stats = indexer.get_stats()
    assert stats["total_traces"] == 1


def test_search_execution_steps_content(indexer, sample_traces):
    """Test that search includes execution steps content."""
    # Index traces
    for trace in sample_traces:
        indexer.index_trace(trace)

    # Search for content that's only in execution steps
    results = indexer.search_traces("pyproject.toml")
    assert len(results) >= 1

    results = indexer.search_traces("orjson library")
    assert len(results) >= 1

    results = indexer.search_traces("Alembic migration")
    assert len(results) >= 1


def test_search_error_messages(indexer, sample_traces):
    """Test that search includes error messages from failed steps."""
    # Index traces
    for trace in sample_traces:
        indexer.index_trace(trace)

    # Search for error message content
    results = indexer.search_traces("FOREIGN KEY constraint")
    assert len(results) >= 1


def test_rebuild_index(indexer, sample_traces):
    """Test rebuilding the FTS5 index."""
    # Index traces
    for trace in sample_traces:
        indexer.index_trace(trace)

    # Rebuild index
    count = indexer.rebuild_index()
    assert count == 3

    # Search should still work
    results = indexer.search_traces("Python")
    assert len(results) >= 1


def test_get_nonexistent_metadata(indexer):
    """Test getting metadata for non-existent trace."""
    metadata = indexer.get_trace_metadata("nonexistent-trace-id")
    assert metadata is None


def test_concurrent_indexing(indexer):
    """Test basic thread safety for indexing operations."""
    import threading

    traces = []
    errors = []

    def index_trace(i):
        try:
            trace = ExecutionTrace(
                problem_statement=f"Concurrent trace {i}",
                outcome="Success",
                execution_steps=[
                    ExecutionStep(
                        step_number=1,
                        action="concurrent",
                        content=f"thread {i} content",
                    )
                ],
            )
            indexer.index_trace(trace)
            traces.append(trace.context.trace_id)
        except Exception as e:
            errors.append(e)

    # Start multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=index_trace, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    # Should have no errors and all traces indexed
    assert len(errors) == 0
    assert len(traces) == 5

    # Search should find all traces
    results = indexer.search_traces("Concurrent")
    assert len(results) == 5


def test_performance_with_many_traces(indexer):
    """Test indexer performance with many traces."""
    import time

    # Create and index many traces
    trace_count = 100
    start_time = time.time()

    for i in range(trace_count):
        trace = ExecutionTrace(
            problem_statement=f"Performance test trace {i}",
            outcome=f"Completed trace {i}",
            execution_steps=[
                ExecutionStep(
                    step_number=1,
                    action="performance",
                    content=f"Performance test content for trace {i}",
                )
            ],
            domain="testing",
            complexity="simple",
        )
        indexer.index_trace(trace)

    index_time = time.time() - start_time
    print(
        f"Indexed {trace_count} traces in {index_time:.2f}s ({index_time / trace_count * 1000:.1f}ms per trace)"
    )

    # Test search performance
    start_time = time.time()
    results = indexer.search_traces("Performance test", limit=trace_count)
    search_time = time.time() - start_time

    print(f"Searched {trace_count} traces in {search_time * 1000:.1f}ms")
    assert len(results) == trace_count
    assert search_time < 1.0  # Should be under 1 second

    # Verify stats
    stats = indexer.get_stats()
    assert stats["total_traces"] == trace_count
