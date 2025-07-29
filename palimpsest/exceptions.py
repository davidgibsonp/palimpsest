"""
Exception hierarchy for Palimpsest.

Provides structured error handling for all operations.
"""


class PalimpsestError(Exception):
    """Base exception for all Palimpsest errors."""

    pass


class ValidationError(PalimpsestError):
    """Trace data validation failed."""

    pass


class StorageError(PalimpsestError):
    """File storage operation failed."""

    pass


class IndexError(PalimpsestError):
    """Search index operation failed."""

    pass


class SearchError(PalimpsestError):
    """Search operation failed."""

    pass
