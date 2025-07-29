"""
JSON file management for ExecutionTrace storage.

Handles CRUD operations for traces stored as JSON files in .palimpsest/traces/
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from loguru import logger

from ..exceptions import StorageError
from ..models.trace import ExecutionTrace


class TraceFileManager:
    """Manages JSON file storage for ExecutionTrace objects."""

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the file manager.

        Args:
            base_path: Base directory for storage (defaults to current dir)
        """
        if base_path is None:
            base_path = Path.cwd()

        self.base_path = Path(base_path).resolve()
        self.palimpsest_dir = self.base_path / ".palimpsest"
        self.traces_dir = self.palimpsest_dir / "traces"
        self.logs_dir = self.palimpsest_dir / "logs"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        try:
            self.traces_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directories exist: {self.palimpsest_dir}")
        except Exception as e:
            raise StorageError(f"Failed to create storage directories: {e}")

    def _generate_trace_id(self) -> str:
        """Generate a unique trace ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        uuid_suffix = str(uuid4())[:8]
        return f"{timestamp}_{uuid_suffix}"

    def get_trace_path(self, trace_id: str) -> Path:
        """Get the file path for a trace ID."""
        return self.traces_dir / f"{trace_id}.json"

    def save_trace(self, trace: ExecutionTrace) -> str:
        """
        Save an ExecutionTrace to a JSON file.

        Returns:
            Generated trace ID
        """
        try:
            trace_id = self._prepare_trace_for_save(trace)
            trace_path = self.get_trace_path(trace_id)
            trace_data = trace.model_dump(mode="json")

            self._write_trace_file(trace_data, trace_path)

            logger.info(f"Saved trace {trace_id}")
            return trace_id

        except Exception as e:
            raise StorageError(f"Failed to save trace: {e}")

    def _prepare_trace_for_save(self, trace: ExecutionTrace) -> str:
        """Prepare trace for saving and return trace ID."""
        if not trace.context.trace_id or trace.context.trace_id.startswith("migrated-"):
            trace_id = self._generate_trace_id()
            trace.context.trace_id = trace_id
        else:
            trace_id = trace.context.trace_id
        return trace_id

    def _write_trace_file(self, trace_data: dict, trace_path: Path) -> None:
        """Write trace data to file atomically."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", dir=self.traces_dir, delete=False
        ) as temp_file:
            json.dump(trace_data, temp_file, indent=2, ensure_ascii=False)
            temp_path = Path(temp_file.name)

        # Atomic rename
        temp_path.rename(trace_path)

    def load_trace(self, trace_id: str) -> ExecutionTrace:
        """
        Load an ExecutionTrace from a JSON file.

        Returns:
            ExecutionTrace object
        """
        try:
            trace_path = self.get_trace_path(trace_id)

            if not trace_path.exists():
                raise StorageError(f"Trace {trace_id} not found")

            trace_data = self._read_trace_file(trace_path)
            trace = ExecutionTrace.model_validate_with_migration(trace_data)

            logger.debug(f"Loaded trace {trace_id}")
            return trace

        except StorageError:
            raise  # Re-raise storage errors as-is
        except Exception as e:
            raise StorageError(f"Failed to load trace {trace_id}: {e}")

    def _read_trace_file(self, trace_path: Path) -> dict:
        """Read and parse trace file."""
        with open(trace_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete_trace(self, trace_id: str) -> bool:
        """
        Delete a trace file.

        Returns:
            True if deleted, False if not found
        """
        try:
            trace_path = self.get_trace_path(trace_id)

            if not trace_path.exists():
                return False

            trace_path.unlink()
            logger.info(f"Deleted trace {trace_id}")
            return True

        except Exception as e:
            raise StorageError(f"Failed to delete trace {trace_id}: {e}")

    def list_traces(self, limit: Optional[int] = None) -> List[str]:
        """
        List all available trace IDs.

        Returns:
            List of trace IDs sorted by modification time (newest first)
        """
        try:
            if not self.traces_dir.exists():
                return []

            json_files = self._get_trace_files()
            trace_ids = [f.stem for f in json_files]

            if limit is not None:
                trace_ids = trace_ids[:limit]

            logger.debug(f"Listed {len(trace_ids)} traces")
            return trace_ids

        except Exception as e:
            raise StorageError(f"Failed to list traces: {e}")

    def _get_trace_files(self) -> List[Path]:
        """Get all trace files sorted by modification time."""
        json_files = list(self.traces_dir.glob("*.json"))
        json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return json_files

    def trace_exists(self, trace_id: str) -> bool:
        """Check if a trace exists."""
        return self.get_trace_path(trace_id).exists()
