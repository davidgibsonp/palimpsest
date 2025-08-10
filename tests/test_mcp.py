"""
Tests for MCP (Model Context Protocol) server implementation.

Tests MCP tools, configuration, and integration with PalimpsestEngine.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from palimpsest.mcp import MCPServerConfig, PalimpsestMCPServer, load_config
from palimpsest.exceptions import PalimpsestError, ValidationError


class TestMCPServerConfig:
    """Tests for MCP server configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MCPServerConfig()

        assert config.server_name == "Palimpsest"
        assert config.transport_type == "stdio"
        assert config.base_path is None
        assert config.auto_context is True
        assert config.default_search_limit == 20
        assert config.max_search_limit == 100
        assert config.log_level == "INFO"
        assert config.log_to_file is True

    def test_config_from_env(self, monkeypatch):
        """Test configuration loading from environment variables."""
        monkeypatch.setenv("PALIMPSEST_MCP_SERVER_NAME", "TestServer")
        monkeypatch.setenv("PALIMPSEST_MCP_TRANSPORT_TYPE", "http")
        monkeypatch.setenv("PALIMPSEST_MCP_DEFAULT_SEARCH_LIMIT", "50")
        monkeypatch.setenv("PALIMPSEST_MCP_LOG_LEVEL", "DEBUG")

        config = MCPServerConfig()

        assert config.server_name == "TestServer"
        assert config.transport_type == "http"
        assert config.default_search_limit == 50
        assert config.log_level == "DEBUG"

    def test_configure_logging(self):
        """Test logging configuration."""
        config = MCPServerConfig()

        # Should not raise exception
        config.configure_logging()

    def test_load_config(self):
        """Test config loading function."""
        config = load_config()
        assert isinstance(config, MCPServerConfig)


class TestPalimpsestMCPServer:
    """Tests for Palimpsest MCP server."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mcp_server(self, temp_dir):
        """Create MCP server instance for testing."""
        return PalimpsestMCPServer(base_path=temp_dir)

    def test_server_initialization(self, temp_dir):
        """Test MCP server initialization."""
        server = PalimpsestMCPServer(base_path=temp_dir)

        assert server.base_path == temp_dir
        assert server.mcp is not None
        assert hasattr(server.mcp, "_tool_manager")

    def test_server_tools_registered(self, mcp_server):
        """Test that all required tools are registered."""
        # Get registered tools from tool manager's internal storage
        registered_tools = mcp_server.mcp._tool_manager._tools
        tool_names = list(registered_tools.keys())

        expected_tools = [
            "create_trace",
            "search_traces",
            "get_trace",
            "list_traces",
            "get_stats",
        ]

        for tool in expected_tools:
            assert tool in tool_names

    def test_create_trace_tool(self, mcp_server):
        """Test create_trace MCP tool via real API integration."""
        trace_data = {
            "problem_statement": "Test problem",
            "outcome": "Test outcome",
            "execution_steps": [
                {"step_number": 1, "action": "test", "content": "test step"}
            ],
        }

        # Import and test the actual create_trace function
        from palimpsest.api.core import create_trace
        
        trace_id = create_trace(trace_data, auto_context=True, base_path=mcp_server.base_path)
        assert trace_id is not None
        assert len(trace_id) > 0

    def test_create_trace_validation_error(self, mcp_server):
        """Test create_trace tool with validation error."""
        from palimpsest.api.core import create_trace
        
        with pytest.raises(ValidationError):
            create_trace({"invalid": "data"}, base_path=mcp_server.base_path)

    def test_search_traces_tool(self, mcp_server):
        """Test search_traces via API integration."""
        # First create a trace to search for
        trace_data = {
            "problem_statement": "Search test problem",
            "outcome": "Search test outcome",
            "execution_steps": [
                {"step_number": 1, "action": "test", "content": "searchable content"}
            ],
        }
        
        from palimpsest.api.core import create_trace, search_traces
        
        trace_id = create_trace(trace_data, base_path=mcp_server.base_path)
        results = search_traces("search test", base_path=mcp_server.base_path)
        
        assert len(results) >= 1
        assert any(result["trace_id"] == trace_id for result in results)

    def test_get_trace_tool(self, mcp_server):
        """Test get_trace via API integration."""
        # Create a trace first
        trace_data = {
            "problem_statement": "Get test problem",
            "outcome": "Get test outcome",
            "execution_steps": [
                {"step_number": 1, "action": "test", "content": "get test content"}
            ],
        }
        
        from palimpsest.api.core import create_trace, get_trace
        
        trace_id = create_trace(trace_data, base_path=mcp_server.base_path)
        retrieved_trace = get_trace(trace_id, base_path=mcp_server.base_path)
        
        assert retrieved_trace["trace_id"] == trace_id
        assert retrieved_trace["problem_statement"] == "Get test problem"

    def test_get_trace_not_found(self, mcp_server):
        """Test get_trace tool with non-existent trace."""
        from palimpsest.api.core import get_trace
        
        with pytest.raises(PalimpsestError):
            get_trace("nonexistent-id", base_path=mcp_server.base_path)

    def test_list_traces_tool(self, mcp_server):
        """Test list_traces via API integration.""" 
        from palimpsest.api.core import list_traces
        
        traces = list_traces(base_path=mcp_server.base_path)
        assert isinstance(traces, list)

    def test_get_stats_tool(self, mcp_server):
        """Test get_stats via API integration."""
        from palimpsest.api.core import get_stats
        
        stats = get_stats(base_path=mcp_server.base_path)
        assert "trace_count" in stats
        assert isinstance(stats["trace_count"], int)


class TestMCPIntegration:
    """Integration tests for MCP server with real PalimpsestEngine."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_mcp_create_and_search_integration(self, temp_dir):
        """Test end-to-end trace creation and search via MCP tools."""
        server = PalimpsestMCPServer(base_path=temp_dir)

        # Test data
        trace_data = {
            "problem_statement": "How to implement MCP server?",
            "outcome": "Successfully implemented FastMCP server with tools",
            "execution_steps": [
                {
                    "action": "research",
                    "content": "Researched MCP documentation and examples",
                },
                {
                    "action": "implement",
                    "content": "Created server.py with FastMCP and tools",
                },
                {
                    "action": "test",
                    "content": "Wrote comprehensive tests for MCP tools",
                },
            ],
            "tags": ["mcp", "server", "python"],
            "domain": "development",
        }

        # Create trace
        trace_id = server.mcp.call_tool("create_trace", trace_data)
        assert trace_id is not None
        assert len(trace_id) > 0

        # Search for created trace
        results = server.mcp.call_tool("search_traces", "MCP server")
        assert len(results) == 1
        assert results[0]["trace_id"] == trace_id
        assert "MCP server" in results[0]["problem_statement"]

    def test_mcp_performance_with_multiple_traces(self, temp_dir):
        """Test MCP server performance with multiple traces."""
        server = PalimpsestMCPServer(base_path=temp_dir)

        # Create multiple traces
        trace_ids = []
        for i in range(10):
            trace_data = {
                "problem_statement": f"Test problem {i}",
                "outcome": f"Test outcome {i}",
                "execution_steps": [{"action": "test", "content": f"Test step {i}"}],
                "tags": [f"tag{i}"],
                "domain": "test",
            }
            trace_id = server.mcp.call_tool("create_trace", trace_data)
            trace_ids.append(trace_id)

        # Test search
        results = server.mcp.call_tool("search_traces", "Test problem")
        assert len(results) == 10

        # Test list
        traces = server.mcp.call_tool("list_traces", limit=5)
        assert len(traces) == 5

        # Verify all traces were created
        all_traces = server.mcp.call_tool("list_traces", limit=20)
        assert len(all_traces) == 10

        # Check trace IDs match
        result_ids = {trace["trace_id"] for trace in all_traces}
        assert result_ids == set(trace_ids)
