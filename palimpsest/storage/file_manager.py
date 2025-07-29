"""
JSON file management for ExecutionTrace storage.

Handles CRUD operations for traces stored as JSON files in .palimpsest/traces/
"""

import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from ..exceptions import StorageError
from ..models.trace import ExecutionTrace

logger = logging.getLogger(__name__)


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
        """
        Generate a unique trace ID.
        
        Returns:
            Unique trace identifier
        """
        # Use timestamp + UUID for uniqueness and rough chronological ordering
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        uuid_suffix = str(uuid4())[:8]
        return f"{timestamp}_{uuid_suffix}"
    
    def get_trace_path(self, trace_id: str) -> Path:
        """
        Get the file path for a trace ID.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            Path to the trace file
        """
        return self.traces_dir / f"{trace_id}.json"
    
    def save_trace(self, trace: ExecutionTrace) -> str:
        """
        Save an ExecutionTrace to a JSON file.
        
        Args:
            trace: ExecutionTrace object to save
            
        Returns:
            Generated trace ID
            
        Raises:
            StorageError: If save operation fails
        """
        try:
            # Generate trace ID if not already set
            if not trace.context.trace_id or trace.context.trace_id.startswith("migrated-"):
                trace_id = self._generate_trace_id()
                # Update the trace context with new ID
                trace.context.trace_id = trace_id
            else:
                trace_id = trace.context.trace_id
            
            trace_path = self.get_trace_path(trace_id)
            
            # Convert to JSON
            trace_data = trace.model_dump(mode='json')
            
            # Atomic write using temporary file + rename
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                dir=self.traces_dir,
                delete=False
            ) as temp_file:
                json.dump(trace_data, temp_file, indent=2, ensure_ascii=False)
                temp_path = Path(temp_file.name)
            
            # Atomic rename
            temp_path.rename(trace_path)
            
            logger.info(f"Saved trace {trace_id} to {trace_path}")
            return trace_id
            
        except Exception as e:
            raise StorageError(f"Failed to save trace: {e}")
    
    def load_trace(self, trace_id: str) -> ExecutionTrace:
        """
        Load an ExecutionTrace from a JSON file.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            ExecutionTrace object
            
        Raises:
            StorageError: If load operation fails or trace not found
        """
        try:
            trace_path = self.get_trace_path(trace_id)
            
            if not trace_path.exists():
                raise StorageError(f"Trace {trace_id} not found")
            
            with open(trace_path, 'r', encoding='utf-8') as f:
                trace_data = json.load(f)
            
            # Use migration-aware validation
            trace = ExecutionTrace.model_validate_with_migration(trace_data)
            
            logger.debug(f"Loaded trace {trace_id} from {trace_path}")
            return trace
            
        except StorageError:
            raise  # Re-raise storage errors as-is
        except Exception as e:
            raise StorageError(f"Failed to load trace {trace_id}: {e}")
    
    def delete_trace(self, trace_id: str) -> bool:
        """
        Delete a trace file.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            StorageError: If delete operation fails
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
        
        Args:
            limit: Maximum number of traces to return
            
        Returns:
            List of trace IDs sorted by modification time (newest first)
            
        Raises:
            StorageError: If listing operation fails
        """
        try:
            if not self.traces_dir.exists():
                return []
            
            # Get all JSON files
            json_files = list(self.traces_dir.glob("*.json"))
            
            # Sort by modification time (newest first)
            json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Extract trace IDs
            trace_ids = [f.stem for f in json_files]
            
            # Apply limit if specified
            if limit is not None:
                trace_ids = trace_ids[:limit]
            
            logger.debug(f"Listed {len(trace_ids)} traces")
            return trace_ids
            
        except Exception as e:
            raise StorageError(f"Failed to list traces: {e}")
    
    def trace_exists(self, trace_id: str) -> bool:
        """
        Check if a trace exists.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            True if trace exists
        """
        return self.get_trace_path(trace_id).exists()
    
    def get_trace_stats(self) -> dict:
        """
        Get statistics about stored traces.
        
        Returns:
            Dictionary with trace statistics
        """
        try:
            trace_ids = self.list_traces()
            total_count = len(trace_ids)
            
            if total_count == 0:
                return {
                    "total_traces": 0,
                    "storage_size_bytes": 0,
                    "oldest_trace": None,
                    "newest_trace": None
                }
            
            # Calculate total storage size
            total_size = sum(
                self.get_trace_path(trace_id).stat().st_size 
                for trace_id in trace_ids
            )
            
            # Get oldest and newest (list is already sorted newest first)
            newest_trace = trace_ids[0] if trace_ids else None
            oldest_trace = trace_ids[-1] if trace_ids else None
            
            return {
                "total_traces": total_count,
                "storage_size_bytes": total_size,
                "oldest_trace": oldest_trace,
                "newest_trace": newest_trace,
                "storage_directory": str(self.traces_dir)
            }
            
        except Exception as e:
            raise StorageError(f"Failed to get trace statistics: {e}")
    
    def cleanup_corrupted_files(self) -> List[str]:
        """
        Find and remove corrupted JSON files.
        
        Returns:
            List of removed file names
            
        Raises:
            StorageError: If cleanup operation fails
        """
        removed_files = []
        
        try:
            if not self.traces_dir.exists():
                return removed_files
            
            for json_file in self.traces_dir.glob("*.json"):
                try:
                    # Try to load and validate the JSON
                    with open(json_file, 'r', encoding='utf-8') as f:
                        trace_data = json.load(f)
                    
                    # Try to validate as ExecutionTrace
                    ExecutionTrace.model_validate_with_migration(trace_data)
                    
                except Exception as e:
                    # File is corrupted, remove it
                    logger.warning(f"Removing corrupted trace file {json_file}: {e}")
                    json_file.unlink()
                    removed_files.append(json_file.name)
            
            if removed_files:
                logger.info(f"Cleaned up {len(removed_files)} corrupted files")
            
            return removed_files
            
        except Exception as e:
            raise StorageError(f"Failed to cleanup corrupted files: {e}")