"""
SQLite indexing for ExecutionTrace search functionality.

This module provides fast full-text search across trace content using SQLite's
FTS5 (Full-Text Search) virtual tables. It implements a hybrid storage approach:
- Structured metadata in the main 'traces' table for efficient filtering
- Full-text searchable content in 'traces_fts' FTS5 virtual table

Key features:
- Full-text search across problem statements, outcomes, and execution steps
- Filtering by domain, complexity, success status, and tags
- BM25 relevance ranking for search results
- Concurrent access with SQLite WAL mode
- Performance optimized for 1000+ traces with sub-second search times
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from ..exceptions import IndexError, StorageError
from ..models.trace import ExecutionTrace


class TraceIndexer:
    """
    SQLite-based indexer for fast trace search.

    This class manages a SQLite database with FTS5 full-text search capabilities
    for ExecutionTrace objects. It provides efficient indexing and search
    operations with support for complex queries and filtering.

    The indexer creates two main structures:
    1. 'traces' table: Structured metadata for efficient filtering
    2. 'traces_fts' FTS5 table: Full-text searchable content

    Thread-safe operations are supported through SQLite's WAL mode.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the trace indexer.

        Args:
            base_path: Base directory for storage (defaults to current dir)
        """
        if base_path is None:
            base_path = Path.cwd()

        self.base_path = Path(base_path).resolve()
        self.palimpsest_dir = self.base_path / ".palimpsest"
        self.db_path = self.palimpsest_dir / "index.db"

        # Ensure directory exists and initialize database
        self._ensure_directory()
        self._init_database()

    def _ensure_directory(self) -> None:
        """Ensure the .palimpsest directory exists."""
        try:
            self.palimpsest_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(f"Failed to create indexer directory: {e}")

    def _init_database(self) -> None:
        """Initialize SQLite database with FTS5 tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                self._configure_database(conn)
                self._create_main_table(conn)
                self._create_fts_table(conn)
                self._create_indexes(conn)

                conn.commit()
                logger.debug(f"Initialized database at {self.db_path}")

        except Exception as e:
            raise IndexError(f"Failed to initialize database: {e}")

    def _configure_database(self, conn: sqlite3.Connection) -> None:
        """Configure database settings for optimal performance."""
        conn.execute("PRAGMA journal_mode=WAL")

    def _create_main_table(self, conn: sqlite3.Connection) -> None:
        """Create the main traces table for structured metadata."""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                problem_statement TEXT NOT NULL,
                outcome TEXT NOT NULL,
                domain TEXT,
                complexity TEXT,
                success BOOLEAN NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                execution_steps_count INTEGER NOT NULL
            )
        """
        )

    def _create_fts_table(self, conn: sqlite3.Connection) -> None:
        """Create FTS5 virtual table for full-text search."""
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS traces_fts USING fts5(
                trace_id UNINDEXED,
                problem_statement,
                outcome,
                execution_steps_content,
                tags
            )
        """
        )

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create indexes for commonly queried fields."""
        indexes = [
            ("idx_domain", "domain"),
            ("idx_complexity", "complexity"),
            ("idx_success", "success"),
            ("idx_timestamp", "timestamp"),
        ]

        for index_name, column in indexes:
            conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON traces({column})")

    def index_trace(self, trace: ExecutionTrace) -> None:
        """
        Add or update a trace in the search index.

        Args:
            trace: ExecutionTrace to index
        """
        try:
            trace_id = trace.context.trace_id

            with sqlite3.connect(self.db_path) as conn:
                self._insert_trace_metadata(conn, trace)
                self._insert_trace_fts(conn, trace)

                conn.commit()
                logger.debug(f"Indexed trace {trace_id}")

        except Exception as e:
            raise IndexError(f"Failed to index trace {trace.context.trace_id}: {e}")

    def _insert_trace_metadata(
        self, conn: sqlite3.Connection, trace: ExecutionTrace
    ) -> None:
        """Insert or update trace metadata in the main traces table."""
        tags_text = " ".join(trace.context.tags) if trace.context.tags else ""

        conn.execute(
            """
            INSERT OR REPLACE INTO traces (
                trace_id, problem_statement, outcome, domain, complexity,
                success, timestamp, tags, execution_steps_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace.context.trace_id,
                trace.problem_statement,
                trace.outcome,
                trace.domain,
                trace.complexity,
                trace.success,
                trace.context.timestamp.isoformat(),
                tags_text,
                len(trace.execution_steps),
            ),
        )

    def _insert_trace_fts(
        self, conn: sqlite3.Connection, trace: ExecutionTrace
    ) -> None:
        """Insert or update trace content in the FTS5 table."""
        execution_steps_content = self._extract_steps_content(trace)
        tags_text = " ".join(trace.context.tags) if trace.context.tags else ""

        conn.execute(
            """
            INSERT OR REPLACE INTO traces_fts (
                trace_id, problem_statement, outcome, 
                execution_steps_content, tags
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                trace.context.trace_id,
                trace.problem_statement,
                trace.outcome,
                execution_steps_content,
                tags_text,
            ),
        )

    def _extract_steps_content(self, trace: ExecutionTrace) -> str:
        """Extract searchable content from execution steps."""
        content_parts = []

        for step in trace.execution_steps:
            content_parts.append(f"{step.action}: {step.content}")
            if step.error_message:
                content_parts.append(f"ERROR: {step.error_message}")

        return " | ".join(content_parts)

    def remove_trace(self, trace_id: str) -> None:
        """
        Remove a trace from the search index.

        Args:
            trace_id: ID of trace to remove
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Remove from main table
                conn.execute("DELETE FROM traces WHERE trace_id = ?", (trace_id,))

                # Remove from FTS5 table
                conn.execute("DELETE FROM traces_fts WHERE trace_id = ?", (trace_id,))

                conn.commit()
                logger.debug(f"Removed trace {trace_id} from index")

        except Exception as e:
            raise IndexError(f"Failed to remove trace {trace_id}: {e}")

    def search_traces(
        self, query: str, filters: Optional[Dict[str, any]] = None, limit: int = 50
    ) -> List[str]:
        """
        Search for traces matching the query.

        Args:
            query: Search query string
            filters: Optional filters (domain, complexity, success, tags)
            limit: Maximum number of results

        Returns:
            List of trace IDs ordered by relevance
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                base_query, params = self._build_search_query(query)
                base_query, params = self._apply_search_filters(
                    base_query, params, filters
                )
                base_query = self._add_ordering_and_limit(base_query, query, limit)
                params.append(limit)

                results = self._execute_search(conn, base_query, params)

                logger.debug(
                    f"Search returned {len(results)} results for query: '{query}'"
                )
                return results

        except Exception as e:
            raise IndexError(f"Search failed: {e}")

    def _build_search_query(self, query: str) -> tuple[str, List[str]]:
        """Build the base search query and parameters."""
        if query.strip():
            # Build FTS5 query with proper escaping
            fts_query = self._build_fts_query(query.strip())
            base_query = """
                SELECT traces.trace_id, bm25(traces_fts) as rank
                FROM traces_fts
                JOIN traces ON traces.trace_id = traces_fts.trace_id
                WHERE traces_fts MATCH ?
            """
            params = [fts_query]
        else:
            # No search query, just list recent traces
            base_query = """
                SELECT trace_id, 0 as rank
                FROM traces
                WHERE 1=1
            """
            params = []

        return base_query, params

    def _build_fts_query(self, query: str) -> str:
        """Build FTS5 query with proper escaping of special characters."""
        words = query.split()
        escaped_words = []

        for word in words:
            # Quote words containing special FTS5 characters
            if any(char in word for char in [".", '"', "(", ")", "*", "^", "$"]):
                escaped_words.append(f'"{word}"')
            else:
                escaped_words.append(word)

        if len(escaped_words) == 1:
            return escaped_words[0]
        else:
            return " OR ".join(escaped_words)

    def _apply_search_filters(
        self, base_query: str, params: List[str], filters: Optional[Dict[str, any]]
    ) -> tuple[str, List[str]]:
        """Apply filters to the search query."""
        if not filters:
            return base_query, params

        filter_conditions = []

        # Domain filter
        if "domain" in filters and filters["domain"]:
            filter_conditions.append("traces.domain = ?")
            params.append(filters["domain"])

        # Complexity filter
        if "complexity" in filters and filters["complexity"]:
            filter_conditions.append("traces.complexity = ?")
            params.append(filters["complexity"])

        # Success filter
        if "success" in filters:
            filter_conditions.append("traces.success = ?")
            params.append(filters["success"])

        # Tags filter (simple substring matching)
        if "tags" in filters and filters["tags"]:
            for tag in filters["tags"]:
                filter_conditions.append("traces.tags LIKE ?")
                params.append(f"%{tag}%")

        # Add filter conditions to query
        if filter_conditions:
            base_query += " AND " + " AND ".join(filter_conditions)

        return base_query, params

    def _add_ordering_and_limit(self, base_query: str, query: str, limit: int) -> str:
        """Add ordering and limit clause to the query."""
        if query.strip():
            # Order by relevance (rank) then timestamp for FTS queries
            return base_query + " ORDER BY rank, traces.timestamp DESC LIMIT ?"
        else:
            # Order by timestamp only for non-FTS queries
            return base_query + " ORDER BY traces.timestamp DESC LIMIT ?"

    def _execute_search(
        self, conn: sqlite3.Connection, query: str, params: List[str]
    ) -> List[str]:
        """Execute the search query and return trace IDs."""
        cursor = conn.execute(query, params)
        return [row[0] for row in cursor.fetchall()]

    def get_trace_metadata(self, trace_id: str) -> Optional[Dict[str, any]]:
        """
        Get metadata for a specific trace without loading full content.

        Args:
            trace_id: Trace identifier

        Returns:
            Dictionary with trace metadata or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT trace_id, problem_statement, outcome, domain, 
                           complexity, success, timestamp, tags, execution_steps_count
                    FROM traces 
                    WHERE trace_id = ?
                """,
                    (trace_id,),
                )

                row = cursor.fetchone()
                if row:
                    metadata = dict(row)
                    # Convert SQLite integer to Python boolean
                    metadata["success"] = bool(metadata["success"])
                    return metadata
                return None

        except Exception as e:
            raise IndexError(f"Failed to get metadata for {trace_id}: {e}")

    def get_stats(self) -> Dict[str, any]:
        """
        Get database statistics.

        Returns:
            Dictionary with indexer statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM traces")
                total_traces = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM traces WHERE success = 1")
                successful_traces = cursor.fetchone()[0]

                cursor = conn.execute(
                    "SELECT domain, COUNT(*) FROM traces GROUP BY domain"
                )
                domains = dict(cursor.fetchall())

                cursor = conn.execute(
                    "SELECT complexity, COUNT(*) FROM traces GROUP BY complexity"
                )
                complexities = dict(cursor.fetchall())

                return {
                    "total_traces": total_traces,
                    "successful_traces": successful_traces,
                    "failed_traces": total_traces - successful_traces,
                    "domains": domains,
                    "complexities": complexities,
                    "database_path": str(self.db_path),
                }

        except Exception as e:
            raise IndexError(f"Failed to get stats: {e}")

    def rebuild_index(self) -> int:
        """
        Rebuild the FTS5 index (useful for maintenance).

        Returns:
            Number of traces reindexed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Rebuild FTS5 index
                conn.execute("INSERT INTO traces_fts(traces_fts) VALUES('rebuild')")

                # Get count of indexed traces
                cursor = conn.execute("SELECT COUNT(*) FROM traces")
                count = cursor.fetchone()[0]

                conn.commit()
                logger.info(f"Rebuilt index for {count} traces")
                return count

        except Exception as e:
            raise IndexError(f"Failed to rebuild index: {e}")
