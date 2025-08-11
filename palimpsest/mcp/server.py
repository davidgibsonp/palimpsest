"""
MCP Server implementation for Palimpsest.

Provides Model Context Protocol server that exposes Palimpsest functionality
as tools that AI agents can use to create, search, and manage execution traces.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from mcp.server.fastmcp import FastMCP

from ..api.core import create_trace as api_create_trace
from ..api.core import get_stats as api_get_stats
from ..api.core import get_trace as api_get_trace
from ..api.core import list_traces as api_list_traces
from ..api.core import search_traces as api_search_traces
from ..exceptions import PalimpsestError, ValidationError


class PalimpsestMCPServer:
    """MCP Server for Palimpsest trace management."""

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the MCP server.

        Args:
            base_path: Optional base path for trace storage
        """
        self.base_path = base_path
        self.mcp = FastMCP("Palimpsest")
        self._register_tools()

    def _register_tools(self) -> None:
        """Register MCP tools with the FastMCP server."""

        @self.mcp.tool()
        def create_trace(trace_data: Dict[str, Any]) -> str:
            """
            Create a new execution trace.

            Args:
                trace_data: Dictionary containing trace data with:
                    - problem_statement: Description of the problem being solved
                    - outcome: Result or outcome of the execution
                    - execution_steps: List of steps taken during execution
                    - tags: Optional list of tags for categorization
                    - domain: Optional domain classification

            Returns:
                trace_id: The unique identifier of the created trace

            Raises:
                ValidationError: If trace data is invalid
                PalimpsestError: If trace creation fails
            """
            try:
                logger.info(f"MCP: Creating trace with keys: {list(trace_data.keys())}")
                trace_id = api_create_trace(
                    trace_data, auto_context=True, base_path=self.base_path
                )
                logger.info(f"MCP: Created trace {trace_id}")
                return trace_id
            except (ValidationError, PalimpsestError) as e:
                logger.error(f"MCP: Failed to create trace: {e}")
                raise
            except Exception as e:
                logger.error(f"MCP: Unexpected error creating trace: {e}")
                raise PalimpsestError(f"Failed to create trace: {e}")

        @self.mcp.tool()
        def search_traces(
            query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 20
        ) -> List[Dict[str, Any]]:
            """
            Search for traces matching the query.

            Args:
                query: Search query to match against trace content
                filters: Optional filters (tags, domain, etc.)
                limit: Maximum number of results to return (default: 20)

            Returns:
                List of trace dictionaries matching the search criteria

            Raises:
                PalimpsestError: If search operation fails
            """
            try:
                logger.info(
                    f"MCP: Searching traces with query: '{query}', limit: {limit}"
                )
                results = api_search_traces(query, filters, limit, self.base_path)
                logger.info(f"MCP: Found {len(results)} traces")
                return results
            except PalimpsestError as e:
                logger.error(f"MCP: Failed to search traces: {e}")
                raise
            except Exception as e:
                logger.error(f"MCP: Unexpected error searching traces: {e}")
                raise PalimpsestError(f"Search failed: {e}")

        @self.mcp.tool()
        def get_trace(trace_id: str) -> Dict[str, Any]:
            """
            Retrieve a specific trace by its ID.

            Args:
                trace_id: The unique identifier of the trace to retrieve

            Returns:
                Complete trace dictionary with all details

            Raises:
                PalimpsestError: If trace cannot be found or retrieved
            """
            try:
                logger.info(f"MCP: Getting trace {trace_id}")
                trace = api_get_trace(trace_id, self.base_path)
                logger.info(f"MCP: Retrieved trace {trace_id}")
                return trace
            except PalimpsestError as e:
                logger.error(f"MCP: Failed to get trace {trace_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"MCP: Unexpected error getting trace {trace_id}: {e}")
                raise PalimpsestError(f"Failed to get trace {trace_id}: {e}")

        @self.mcp.tool()
        def list_traces(limit: int = 20) -> List[Dict[str, Any]]:
            """
            List recent traces in chronological order.

            Args:
                limit: Maximum number of traces to return (default: 20)

            Returns:
                List of trace dictionaries ordered by creation time (newest first)

            Raises:
                PalimpsestError: If traces cannot be listed
            """
            try:
                logger.info(f"MCP: Listing traces with limit: {limit}")
                traces = api_list_traces(limit, self.base_path)
                logger.info(f"MCP: Listed {len(traces)} traces")
                return traces
            except PalimpsestError as e:
                logger.error(f"MCP: Failed to list traces: {e}")
                raise
            except Exception as e:
                logger.error(f"MCP: Unexpected error listing traces: {e}")
                raise PalimpsestError(f"Failed to list traces: {e}")

        @self.mcp.tool()
        def get_stats() -> Dict[str, Any]:
            """
            Get statistics about stored traces.

            Returns:
                Dictionary with statistics like count, size, tags, etc.

            Raises:
                PalimpsestError: If stats cannot be computed
            """
            try:
                logger.info("MCP: Getting trace statistics")
                stats = api_get_stats(self.base_path)
                logger.info(
                    f"MCP: Retrieved stats for {stats.get('trace_count', 0)} traces"
                )
                return stats
            except PalimpsestError as e:
                logger.error(f"MCP: Failed to get stats: {e}")
                raise
            except Exception as e:
                logger.error(f"MCP: Unexpected error getting stats: {e}")
                raise PalimpsestError(f"Failed to get stats: {e}")

    def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting Palimpsest MCP server")
        self.mcp.run()


def create_server(base_path: Optional[Path] = None) -> PalimpsestMCPServer:
    """
    Create a new MCP server instance.

    Args:
        base_path: Optional base path for trace storage

    Returns:
        Configured PalimpsestMCServer instance
    """
    return PalimpsestMCPServer(base_path)


def main() -> None:
    """Main entry point for running the MCP server."""
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
