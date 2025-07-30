"""
Performance tests for Palimpsest.

Tests performance targets, particularly search performance with large datasets.
"""

import random
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

import pytest

from palimpsest.api import create_trace, list_traces, search_traces


@pytest.fixture
def temp_path():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_trace_template() -> Dict[str, Any]:
    """Create a sample trace template for testing."""
    return {
        "problem_statement": "Need to optimize performance for better user experience",
        "outcome": "Improved performance by implementing optimizations",
        "execution_steps": [
            {
                "step_number": 1,
                "action": "analyze",
                "content": "Identified performance bottlenecks",
            },
            {
                "step_number": 2,
                "action": "implement",
                "content": "Implemented optimizations",
            },
            {
                "step_number": 3,
                "action": "test",
                "content": "Verified performance improvements",
            },
        ],
        "context": {"tags": ["performance", "optimization"]},
    }


def create_random_trace(template: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Create a random trace based on the template."""
    domains = ["frontend", "backend", "database", "api", "mobile", "desktop", "cloud"]
    actions = ["refactor", "optimize", "debug", "implement", "test", "deploy"]
    components = [
        "UI",
        "API",
        "database",
        "authentication",
        "cache",
        "network",
        "storage",
    ]

    domain = random.choice(domains)
    component = random.choice(components)
    action = random.choice(actions)

    trace = dict(template)
    trace["problem_statement"] = (
        f"#{index}: Need to {action} {domain} {component} for better performance"
    )
    trace["outcome"] = (
        f"Successfully {action}ed {domain} {component}, improving performance by {random.randint(10, 50)}%"
    )

    # Randomize steps
    steps = []
    for i in range(1, random.randint(3, 6)):
        step_action = random.choice(["analyze", "implement", "test", "debug"])
        step = {
            "step_number": i,
            "action": step_action,
            "content": f"{step_action.capitalize()}d {domain} {component} {random.choice(['issue', 'performance', 'behavior', 'implementation'])}",
        }
        steps.append(step)
    trace["execution_steps"] = steps

    # Randomize tags
    tags = ["performance", domain, component]
    if random.random() > 0.5:
        tags.append(action)
    trace["context"]["tags"] = tags

    return trace


def test_search_performance_target(temp_path, sample_trace_template):
    """
    Test search performance with 1000+ traces.

    Target: <1s search time for 1000+ traces
    """
    # Create 1000 traces with randomized content
    print("Creating 1000 traces for performance testing...")
    start_time = time.time()

    for i in range(1000):
        trace = create_random_trace(sample_trace_template, i)
        create_trace(trace, auto_context=False, base_path=temp_path)

        # Log progress
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            print(
                f"Created {i + 1} traces in {elapsed:.2f}s ({(i + 1) / elapsed:.2f} traces/s)"
            )

    creation_time = time.time() - start_time
    print(f"Created 1000 traces in {creation_time:.2f}s")

    # Verify trace count
    traces = list_traces(limit=2000, base_path=temp_path)
    assert len(traces) >= 1000, f"Expected 1000+ traces, got {len(traces)}"

    # Test search performance for various queries
    search_queries = [
        "frontend",
        "database performance",
        "API optimization",
        "cache implementation",
        "debug network issue",
        "mobile UI",
    ]

    total_search_time = 0
    for query in search_queries:
        start_time = time.time()
        results = search_traces(query, base_path=temp_path)
        search_time = time.time() - start_time

        print(
            f"Search for '{query}' returned {len(results)} results in {search_time:.4f}s"
        )

        # Search should complete in < 1 second
        assert search_time < 1.0, f"Search took too long: {search_time:.4f}s > 1.0s"
        total_search_time += search_time

    avg_search_time = total_search_time / len(search_queries)
    print(f"Average search time: {avg_search_time:.4f}s")

    # Average search time should be < 0.5 seconds
    assert avg_search_time < 0.5, (
        f"Average search time too high: {avg_search_time:.4f}s > 0.5s"
    )


def test_concurrent_operations(temp_path, sample_trace_template):
    """Test performance and data integrity under concurrent operations."""
    import concurrent.futures

    # Function to create a trace
    def create_one_trace(index):
        trace = create_random_trace(sample_trace_template, index)
        trace_id = create_trace(trace, auto_context=False, base_path=temp_path)
        return trace_id

    # Create 100 traces concurrently
    trace_ids = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_index = {executor.submit(create_one_trace, i): i for i in range(100)}
        for future in concurrent.futures.as_completed(future_to_index):
            trace_id = future.result()
            trace_ids.append(trace_id)

    # Verify all traces were created
    traces = list_traces(limit=200, base_path=temp_path)
    assert len(traces) == 100, f"Expected 100 traces, got {len(traces)}"

    # Function to search traces
    def search_for_query(query):
        return search_traces(query, base_path=temp_path)

    # Search queries to run concurrently
    search_queries = [
        "frontend",
        "database",
        "API",
        "cache",
        "network",
        "mobile",
    ]

    # Run searches concurrently
    results = {}
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(search_queries)
    ) as executor:
        future_to_query = {
            executor.submit(search_for_query, query): query for query in search_queries
        }
        for future in concurrent.futures.as_completed(future_to_query):
            query = future_to_query[future]
            results[query] = future.result()

    # Verify all searches returned results
    for query, query_results in results.items():
        print(f"Search for '{query}' returned {len(query_results)} results")
        assert isinstance(query_results, list), (
            f"Expected list result for query '{query}'"
        )
