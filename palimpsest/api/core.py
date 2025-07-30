"""
Python API for Palimpsest.

Provides a clean, stateless function-based API for external consumption.
This module is the primary interface for using Palimpsest programmatically.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from ..engine import PalimpsestEngine
from ..exceptions import PalimpsestError, ValidationError


def create_trace(
    trace_data: Dict[str, Any],
    auto_context: bool = True,
    base_path: Optional[Path] = None,
) -> str:
    """
    Create a new execution trace.

    Args:
        trace_data: Dictionary containing trace data (problem, outcome, steps)
        auto_context: Whether to automatically enrich with environment context
        base_path: Optional base path for storage (defaults to current dir)

    Returns:
        trace_id: The ID of the created trace

    Raises:
        ValidationError: If trace data is invalid
        PalimpsestError: If trace cannot be created
    """
    try:
        engine = PalimpsestEngine(base_path)

        # Collect environment data if auto_context is enabled
        env_data = None
        if auto_context:
            env_data = engine._collect_environment_data()

        return engine.create_trace(trace_data, env_data)

    except Exception as e:
        logger.error(f"Error creating trace: {e}")
        if isinstance(e, (ValidationError, PalimpsestError)):
            raise
        raise PalimpsestError(f"Failed to create trace: {e}")


def search_traces(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 50,
    base_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Search for traces matching query and filters.

    Args:
        query: Search query string
        filters: Optional filters like tags, domain, etc.
        limit: Maximum number of results to return
        base_path: Optional base path for storage

    Returns:
        List of trace dictionaries matching the search

    Raises:
        PalimpsestError: If search operation fails
    """
    try:
        engine = PalimpsestEngine(base_path)
        traces = engine.search_traces(query, filters, limit)

        # Convert Pydantic models to dicts for API consistency
        return [trace.model_dump(mode="json") for trace in traces]

    except Exception as e:
        logger.error(f"Error searching traces: {e}")
        if isinstance(e, PalimpsestError):
            raise
        raise PalimpsestError(f"Search failed: {e}")


def get_trace(trace_id: str, base_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Retrieve a trace by its ID.

    Args:
        trace_id: The ID of the trace to retrieve
        base_path: Optional base path for storage

    Returns:
        Trace as a dictionary

    Raises:
        PalimpsestError: If trace cannot be found or loaded
    """
    try:
        engine = PalimpsestEngine(base_path)
        trace = engine.get_trace(trace_id)
        return trace.model_dump(mode="json")

    except Exception as e:
        logger.error(f"Error getting trace {trace_id}: {e}")
        if isinstance(e, PalimpsestError):
            raise
        raise PalimpsestError(f"Failed to get trace {trace_id}: {e}")


def validate_trace(trace_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate trace data without storing it.

    Args:
        trace_data: Dictionary containing trace data

    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        engine = PalimpsestEngine()
        engine.validate_and_enrich(trace_data)
        return True, []

    except ValidationError as e:
        return False, [str(e)]
    except Exception as e:
        logger.error(f"Unexpected error validating trace: {e}")
        return False, [f"Validation error: {e}"]


def list_traces(
    limit: int = 50, base_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    List traces in chronological order (newest first).

    Args:
        limit: Maximum number of traces to return
        base_path: Optional base path for storage

    Returns:
        List of trace dictionaries

    Raises:
        PalimpsestError: If traces cannot be listed
    """
    try:
        engine = PalimpsestEngine(base_path)
        traces = engine.list_traces(limit)

        # Convert Pydantic models to dicts for API consistency
        return [trace.model_dump(mode="json") for trace in traces]

    except Exception as e:
        logger.error(f"Error listing traces: {e}")
        if isinstance(e, PalimpsestError):
            raise
        raise PalimpsestError(f"Failed to list traces: {e}")


def delete_trace(trace_id: str, base_path: Optional[Path] = None) -> bool:
    """
    Delete a trace by its ID.

    Args:
        trace_id: The ID of the trace to delete
        base_path: Optional base path for storage

    Returns:
        True if deleted successfully

    Raises:
        PalimpsestError: If trace cannot be deleted
    """
    try:
        engine = PalimpsestEngine(base_path)
        return engine.delete_trace(trace_id)

    except Exception as e:
        logger.error(f"Error deleting trace {trace_id}: {e}")
        if isinstance(e, PalimpsestError):
            raise
        raise PalimpsestError(f"Failed to delete trace {trace_id}: {e}")


def get_stats(base_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get statistics about stored traces.

    Args:
        base_path: Optional base path for storage

    Returns:
        Dictionary with stats like count, size, tags, etc.

    Raises:
        PalimpsestError: If stats cannot be computed
    """
    try:
        engine = PalimpsestEngine(base_path)
        return engine.get_stats()

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        if isinstance(e, PalimpsestError):
            raise
        raise PalimpsestError(f"Failed to get stats: {e}")


def rebuild_index(base_path: Optional[Path] = None) -> int:
    """
    Rebuild the search index from trace files.

    Args:
        base_path: Optional base path for storage

    Returns:
        Number of traces indexed

    Raises:
        PalimpsestError: If index rebuild fails
    """
    try:
        engine = PalimpsestEngine(base_path)
        return engine.rebuild_index()

    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
        if isinstance(e, PalimpsestError):
            raise
        raise PalimpsestError(f"Failed to rebuild index: {e}")
