"""
Public API for Palimpsest.

This module exports the main functions for using Palimpsest programmatically.
"""

from .core import (
    create_trace,
    delete_trace,
    get_stats,
    get_trace,
    list_traces,
    rebuild_index,
    search_traces,
    validate_trace,
)

__all__ = [
    "create_trace",
    "search_traces",
    "get_trace",
    "validate_trace",
    "list_traces",
    "delete_trace",
    "get_stats",
    "rebuild_index",
]
