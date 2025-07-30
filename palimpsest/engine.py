"""
Business Logic Engine for Palimpsest.

Provides a unified interface for handling traces, combining storage and search
capabilities with business logic for validation, enrichment, and operations.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from .exceptions import IndexError, PalimpsestError, StorageError, ValidationError
from .models.trace import ExecutionTrace
from .storage.file_manager import TraceFileManager
from .storage.indexer import TraceIndexer


class PalimpsestEngine:
    """
    Unified business logic engine for Palimpsest.

    This class orchestrates the storage and indexing components, providing
    high-level operations for creating, searching, and managing execution traces.
    It contains all business logic for the system, including validation,
    enrichment, and search operations.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the engine with storage and indexing components.

        Args:
            base_path: Base directory for storage (defaults to current dir)
        """
        if base_path is None:
            base_path = Path.cwd()

        self.base_path = Path(base_path).resolve()
        self.file_manager = TraceFileManager(self.base_path)
        self.indexer = TraceIndexer(self.base_path)

        logger.debug(f"PalimpsestEngine initialized with base path: {self.base_path}")

    def create_trace(
        self, llm_data: Dict[str, Any], env_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new execution trace from LLM and environment data.

        This method combines data from an LLM agent with optional environment
        context, validates it, enriches it with metadata, and stores it.

        Args:
            llm_data: Trace data provided by LLM (problem, outcome, steps)
            env_data: Optional environment data (git info, dependencies, etc.)

        Returns:
            trace_id: The ID of the created trace

        Raises:
            ValidationError: If trace data is invalid
            StorageError: If trace cannot be stored
            IndexError: If trace cannot be indexed
        """
        try:
            # Validate and enrich the trace
            trace = self.validate_and_enrich(llm_data, env_data)

            # Store the trace
            trace_id = self.file_manager.save_trace(trace)

            # Index the trace
            self.indexer.index_trace(trace)

            logger.info(f"Created trace: {trace_id}")
            return trace_id

        except ValidationError as e:
            logger.error(f"Validation error creating trace: {e}")
            raise
        except (StorageError, IndexError) as e:
            logger.error(f"Storage/index error creating trace: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error creating trace: {e}")
            raise PalimpsestError(f"Failed to create trace: {e}")

    def validate_and_enrich(
        self, trace_data: Dict[str, Any], env_data: Optional[Dict[str, Any]] = None
    ) -> ExecutionTrace:
        """
        Validate and enrich trace data with additional context.

        Args:
            trace_data: Raw trace data (problem, outcome, steps)
            env_data: Optional environment data to include

        Returns:
            ExecutionTrace: Validated and enriched trace object

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Make a copy to avoid modifying the input
            data = trace_data.copy()

            # Handle context field if it exists
            if "context" not in data:
                data["context"] = {}

            # Add environment data if provided
            if env_data and isinstance(env_data, dict):
                data["context"]["environment"] = env_data

            # Create the Pydantic model - this validates the data
            trace = ExecutionTrace(**data)

            # Ensure steps are properly numbered
            self._ensure_sequential_steps(trace)

            return trace

        except Exception as e:
            logger.error(f"Trace validation failed: {e}")
            raise ValidationError(f"Trace validation failed: {e}")

    def _ensure_sequential_steps(self, trace: ExecutionTrace) -> None:
        """
        Ensure execution steps are numbered sequentially starting from 1.

        Args:
            trace: The trace to normalize step numbers for
        """
        for i, step in enumerate(trace.execution_steps, start=1):
            step.step_number = i

    def search_traces(
        self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 50
    ) -> List[ExecutionTrace]:
        """
        Search for traces matching query and filters.

        This performs a full-text search across all trace content and
        returns complete ExecutionTrace objects.

        Args:
            query: Search query string
            filters: Optional filters like tags, domain, etc.
            limit: Maximum number of results to return

        Returns:
            List of ExecutionTrace objects matching the search

        Raises:
            IndexError: If search operation fails
        """
        try:
            # Delegate to indexer for search
            trace_ids = self.indexer.search(query, filters, limit)

            # Fetch the full traces
            traces = []
            for trace_id in trace_ids:
                try:
                    trace = self.file_manager.load_trace(trace_id)
                    traces.append(trace)
                except StorageError as e:
                    logger.warning(f"Could not load trace {trace_id}: {e}")

            return traces

        except IndexError as e:
            logger.error(f"Search error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected search error: {e}")
            raise PalimpsestError(f"Search failed: {e}")

    def search_metadata_only(
        self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for traces and return only metadata (not full traces).

        This is more efficient for UI displays or when full trace content
        is not immediately needed.

        Args:
            query: Search query string
            filters: Optional filters like tags, domain, etc.
            limit: Maximum number of results to return

        Returns:
            List of metadata dictionaries with trace_id, problem_statement, etc.

        Raises:
            IndexError: If search operation fails
        """
        try:
            return self.indexer.search_metadata(query, filters, limit)
        except IndexError as e:
            logger.error(f"Metadata search error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected metadata search error: {e}")
            raise PalimpsestError(f"Metadata search failed: {e}")

    def get_trace(self, trace_id: str) -> ExecutionTrace:
        """
        Retrieve a trace by its ID.

        Args:
            trace_id: The ID of the trace to retrieve

        Returns:
            ExecutionTrace object

        Raises:
            StorageError: If trace cannot be loaded
        """
        try:
            return self.file_manager.load_trace(trace_id)
        except StorageError as e:
            logger.error(f"Error loading trace {trace_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error loading trace {trace_id}: {e}")
            raise PalimpsestError(f"Failed to load trace {trace_id}: {e}")

    def list_traces(self, limit: int = 50) -> List[ExecutionTrace]:
        """
        List traces in chronological order (newest first).

        Args:
            limit: Maximum number of traces to return

        Returns:
            List of ExecutionTrace objects

        Raises:
            StorageError: If traces cannot be loaded
        """
        try:
            trace_ids = self.file_manager.list_traces(limit)

            traces = []
            for trace_id in trace_ids:
                try:
                    trace = self.file_manager.load_trace(trace_id)
                    traces.append(trace)
                except StorageError as e:
                    logger.warning(f"Could not load trace {trace_id}: {e}")

            return traces

        except StorageError as e:
            logger.error(f"Error listing traces: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error listing traces: {e}")
            raise PalimpsestError(f"Failed to list traces: {e}")

    def delete_trace(self, trace_id: str) -> bool:
        """
        Delete a trace by its ID.

        Args:
            trace_id: The ID of the trace to delete

        Returns:
            True if deleted successfully

        Raises:
            StorageError: If trace cannot be deleted
            IndexError: If trace cannot be removed from index
        """
        try:
            # Delete from storage
            deleted = self.file_manager.delete_trace(trace_id)

            if not deleted:
                raise StorageError(f"Trace {trace_id} not found")

            # Remove from index
            self.indexer.remove_trace(trace_id)

            logger.info(f"Deleted trace: {trace_id}")
            return True

        except (StorageError, IndexError) as e:
            logger.error(f"Error deleting trace {trace_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error deleting trace {trace_id}: {e}")
            raise PalimpsestError(f"Failed to delete trace {trace_id}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored traces.

        Returns:
            Dictionary with stats like count, size, tags, etc.

        Raises:
            PalimpsestError: If stats cannot be computed
        """
        try:
            # Get trace count
            trace_count = len(self.file_manager.list_traces())

            # Get storage size
            storage_size = sum(
                f.stat().st_size for f in self.traces_dir.glob("*.json") if f.is_file()
            )

            # Get most common tags
            common_tags = self.indexer.get_common_tags(10)

            return {
                "count": trace_count,
                "storage_size_bytes": storage_size,
                "common_tags": common_tags,
                "updated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.exception(f"Error getting stats: {e}")
            raise PalimpsestError(f"Failed to get stats: {e}")

    def rebuild_index(self) -> int:
        """
        Rebuild the search index from trace files.

        This is useful after importing traces or if index corruption occurs.

        Returns:
            Number of traces indexed

        Raises:
            IndexError: If index rebuild fails
        """
        try:
            # Clear existing index
            self.indexer.clear_index()

            # List all traces
            trace_ids = self.file_manager.list_traces()

            # Reindex each trace
            indexed_count = 0
            for trace_id in trace_ids:
                try:
                    trace = self.file_manager.load_trace(trace_id)
                    self.indexer.index_trace(trace)
                    indexed_count += 1
                except Exception as e:
                    logger.warning(f"Error indexing trace {trace_id}: {e}")

            logger.info(f"Rebuilt index with {indexed_count} traces")
            return indexed_count

        except IndexError as e:
            logger.error(f"Index rebuild error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error rebuilding index: {e}")
            raise PalimpsestError(f"Failed to rebuild index: {e}")

    @property
    def traces_dir(self) -> Path:
        """Get the traces directory path."""
        return self.file_manager.traces_dir

    def _collect_environment_data(self) -> Dict[str, Any]:
        """
        Collect environment data for trace context.

        Returns:
            Dictionary with environment data (git, dependencies, etc.)
        """
        # This would be expanded to collect real environment data
        # For now, return a minimal placeholder
        import platform

        return {
            "python_version": platform.python_version(),
            "os_platform": platform.platform(),
            "timestamp": self._get_timestamp(),
        }

    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        return datetime.now().isoformat()
