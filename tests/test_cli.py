"""
Tests for CLI interface.

Tests Click commands, configuration, and integration with API layer.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from palimpsest.cli.config import CLIConfig, create_default_config
from palimpsest.cli.main import cli
from palimpsest.exceptions import PalimpsestError, ValidationError


class TestCLIConfig:
    """Tests for CLI configuration."""

    def test_default_config(self):
        """Test default CLI configuration values."""
        config = CLIConfig()

        assert config.default_tags == []
        assert config.default_domain == ""
        assert config.default_search_limit == 10
        assert config.default_list_limit == 10
        assert config.output_format == "table"
        assert config.use_colors is True
        assert config.show_progress is True
        assert config.truncate_length == 80
        assert config.mcp_server_name == "Palimpsest"
        assert config.mcp_transport_type == "stdio"
        assert config.mcp_default_search_limit == 20

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "default_tags": ["python", "test"],
            "default_domain": "testing",
            "mcp": {"server_name": "TestServer", "transport_type": "http"},
        }

        config = CLIConfig.from_dict(data)

        assert config.default_tags == ["python", "test"]
        assert config.default_domain == "testing"
        assert config.mcp_server_name == "TestServer"
        assert config.mcp_transport_type == "http"

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = CLIConfig(default_tags=["test"], mcp_server_name="TestServer")

        data = config.to_dict()

        assert data["default_tags"] == ["test"]
        assert "mcp" in data
        assert data["mcp"]["server_name"] == "TestServer"

    def test_create_default_config(self):
        """Test creating default configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"

            create_default_config(config_path)

            assert config_path.exists()
            assert "default_tags" in config_path.read_text()


class TestCLICommands:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Palimpsest" in result.output
        assert "Preserve your AI development workflows" in result.output

    def test_init_command(self, runner, temp_dir):
        """Test init command."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert "Initialized Palimpsest" in result.output

            # Check that .palimpsest directory was created
            palimpsest_dir = Path(".palimpsest")
            assert palimpsest_dir.exists()
            assert (palimpsest_dir / "traces").exists()
            assert (palimpsest_dir / "logs").exists()
            assert (palimpsest_dir / "config.yaml").exists()

    def test_init_command_existing_directory(self, runner):
        """Test init command with existing directory."""
        with runner.isolated_filesystem():
            # Create directory first
            Path(".palimpsest").mkdir()

            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert "already exists" in result.output

    @patch("palimpsest.cli.main.api_create_trace")
    def test_add_command(self, mock_create_trace, runner):
        """Test add command."""
        mock_create_trace.return_value = "test-trace-id"

        trace_data = {
            "problem_statement": "Test problem",
            "outcome": "Test outcome",
            "execution_steps": [{"action": "test", "content": "test step"}],
        }

        with runner.isolated_filesystem():
            # Create trace file
            trace_file = Path("test_trace.json")
            trace_file.write_text(json.dumps(trace_data))

            result = runner.invoke(cli, ["add", str(trace_file)])
            assert result.exit_code == 0
            assert "Created trace: test-trace-id" in result.output
            mock_create_trace.assert_called_once()

    def test_add_command_invalid_json(self, runner):
        """Test add command with invalid JSON."""
        with runner.isolated_filesystem():
            trace_file = Path("invalid.json")
            trace_file.write_text("invalid json")

            result = runner.invoke(cli, ["add", str(trace_file)])
            assert result.exit_code == 1
            assert "Invalid JSON" in result.output

    @patch("palimpsest.cli.main.api_search_traces")
    def test_search_command(self, mock_search_traces, runner):
        """Test search command."""
        mock_results = [
            {
                "trace_id": "trace-1",
                "problem_statement": "Test problem 1",
                "outcome": "Test outcome 1",
                "created_at": "2025-01-01T00:00:00Z",
                "tags": ["python"],
                "domain": "test",
            }
        ]
        mock_search_traces.return_value = mock_results

        result = runner.invoke(cli, ["search", "test query"])
        assert result.exit_code == 0
        assert "Found 1 traces" in result.output
        assert "trace-1" in result.output

    @patch("palimpsest.cli.main.api_search_traces")
    def test_search_command_with_filters(self, mock_search_traces, runner):
        """Test search command with filters."""
        mock_search_traces.return_value = []

        result = runner.invoke(
            cli, ["search", "test", "--tags", "python,web", "--domain", "backend"]
        )
        assert result.exit_code == 0

        # Verify filters were passed correctly
        call_args = mock_search_traces.call_args
        assert call_args[0][1]["tags"] == ["python", "web"]
        assert call_args[0][1]["domain"] == "backend"

    @patch("palimpsest.cli.main.api_search_traces")
    def test_search_command_json_output(self, mock_search_traces, runner):
        """Test search command with JSON output."""
        mock_results = [{"trace_id": "test"}]
        mock_search_traces.return_value = mock_results

        result = runner.invoke(cli, ["search", "test", "--format", "json"])
        assert result.exit_code == 0

        # Should contain valid JSON
        output_json = json.loads(result.output)
        assert output_json == mock_results

    @patch("palimpsest.cli.main.api_list_traces")
    def test_list_command(self, mock_list_traces, runner):
        """Test list command."""
        mock_traces = [
            {
                "trace_id": "trace-1",
                "problem_statement": "Test problem",
                "created_at": "2025-01-01T00:00:00Z",
                "tags": [],
                "domain": "",
            }
        ]
        mock_list_traces.return_value = mock_traces

        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "Recent 1 traces" in result.output

    @patch("palimpsest.cli.main.api_list_traces")
    def test_list_command_with_limit(self, mock_list_traces, runner):
        """Test list command with custom limit."""
        mock_list_traces.return_value = []

        result = runner.invoke(cli, ["list", "--limit", "5"])
        assert result.exit_code == 0

        mock_list_traces.assert_called_once_with(5, None)

    @patch("palimpsest.cli.main.api_get_trace")
    def test_show_command(self, mock_get_trace, runner):
        """Test show command."""
        mock_trace = {
            "trace_id": "test-trace-id",
            "problem_statement": "Test problem",
            "outcome": "Test outcome",
            "execution_steps": [],
            "created_at": "2025-01-01T00:00:00Z",
            "tags": [],
            "domain": "",
        }
        mock_get_trace.return_value = mock_trace

        result = runner.invoke(cli, ["show", "test-trace-id"])
        assert result.exit_code == 0
        assert "TRACE: test-trace-id" in result.output
        assert "Test problem" in result.output

    @patch("palimpsest.cli.main.api_get_trace")
    def test_show_command_json_output(self, mock_get_trace, runner):
        """Test show command with JSON output."""
        mock_trace = {"trace_id": "test"}
        mock_get_trace.return_value = mock_trace

        result = runner.invoke(cli, ["show", "test-trace-id", "--format", "json"])
        assert result.exit_code == 0

        output_json = json.loads(result.output)
        assert output_json == mock_trace

    @patch("palimpsest.cli.main.api_get_stats")
    def test_stats_command(self, mock_get_stats, runner):
        """Test stats command."""
        mock_stats = {
            "trace_count": 42,
            "total_size_mb": 1.5,
            "tags": ["python", "web"],
            "domains": ["backend"],
            "oldest_trace": "2025-01-01",
            "newest_trace": "2025-01-02",
        }
        mock_get_stats.return_value = mock_stats

        result = runner.invoke(cli, ["stats"])
        assert result.exit_code == 0
        assert "Total traces: 42" in result.output
        assert "Total size: 1.50 MB" in result.output
        assert "python, web" in result.output

    def test_server_help(self, runner):
        """Test server subcommand help."""
        result = runner.invoke(cli, ["server", "--help"])
        assert result.exit_code == 0
        assert "MCP server management" in result.output

    @patch("palimpsest.cli.main.mcp_run_server")
    def test_server_start_command(self, mock_run_server, runner):
        """Test server start command."""
        # Mock keyboard interrupt to simulate stopping
        mock_run_server.side_effect = KeyboardInterrupt()

        result = runner.invoke(cli, ["server", "start"])
        assert result.exit_code == 0
        assert "Starting Palimpsest MCP server" in result.output

    def test_completion_command(self, runner):
        """Test completion command."""
        result = runner.invoke(cli, ["completion"])
        assert result.exit_code == 0
        assert "_palimpsest_completion" in result.output
        assert "complete -F" in result.output

    def test_config_init_command(self, runner):
        """Test config init command."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["config", "init", "--type", "project"])
            assert result.exit_code == 0
            assert "Created project config" in result.output

    def test_config_show_command(self, runner):
        """Test config show command."""
        result = runner.invoke(cli, ["config", "show"])
        assert result.exit_code == 0
        assert "Current Configuration" in result.output
        # Should contain valid JSON
        lines = result.output.split("\n")
        json_start = next(
            i for i, line in enumerate(lines) if line.strip().startswith("{")
        )
        json_content = "\n".join(lines[json_start:]).strip()
        config_data = json.loads(json_content)
        assert "default_search_limit" in config_data


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @patch("palimpsest.cli.main.api_create_trace")
    def test_add_command_validation_error(self, mock_create_trace, runner):
        """Test add command with validation error."""
        mock_create_trace.side_effect = ValidationError("Invalid trace data")

        trace_data = {"invalid": "data"}

        with runner.isolated_filesystem():
            trace_file = Path("test.json")
            trace_file.write_text(json.dumps(trace_data))

            result = runner.invoke(cli, ["add", str(trace_file)])
            assert result.exit_code == 1
            assert "Invalid trace data" in result.output

    @patch("palimpsest.cli.main.api_search_traces")
    def test_search_command_error(self, mock_search_traces, runner):
        """Test search command with error."""
        mock_search_traces.side_effect = PalimpsestError("Search failed")

        result = runner.invoke(cli, ["search", "test"])
        assert result.exit_code == 1
        assert "Search failed" in result.output

    @patch("palimpsest.cli.main.api_get_trace")
    def test_show_command_not_found(self, mock_get_trace, runner):
        """Test show command with non-existent trace."""
        mock_get_trace.side_effect = PalimpsestError("Trace not found")

        result = runner.invoke(cli, ["show", "nonexistent"])
        assert result.exit_code == 1
        assert "Trace not found" in result.output


class TestCLIIntegration:
    """Integration tests for CLI with real API layer."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_cli_end_to_end_workflow(self, runner):
        """Test complete CLI workflow: init -> add -> search -> show."""
        with runner.isolated_filesystem():
            # Initialize
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0

            # Create trace file
            trace_data = {
                "problem_statement": "How to test CLI integration?",
                "outcome": "Successfully tested CLI with real workflow",
                "execution_steps": [
                    {
                        "step_number": 1,
                        "action": "implement",
                        "content": "Created comprehensive integration test",
                    }
                ],
                "tags": ["cli", "testing", "integration"],
                "domain": "development",
            }

            trace_file = Path("test_trace.json")
            trace_file.write_text(json.dumps(trace_data))

            # Add trace
            result = runner.invoke(cli, ["add", str(trace_file)])
            assert result.exit_code == 0
            assert "Created trace:" in result.output

            # Extract trace ID from output
            trace_id = result.output.split("Created trace: ")[1].split("\n")[0]

            # Search for trace
            result = runner.invoke(cli, ["search", "CLI integration"])
            assert result.exit_code == 0
            assert "Found 1 traces" in result.output
            assert "How to test CLI integration?" in result.output

            # Show specific trace
            result = runner.invoke(cli, ["show", trace_id])
            assert result.exit_code == 0
            assert "How to test CLI integration?" in result.output

            # List traces
            result = runner.invoke(cli, ["list"])
            assert result.exit_code == 0
            assert "Recent 1 traces" in result.output

            # Get stats
            result = runner.invoke(cli, ["stats"])
            assert result.exit_code == 0
            assert "Total traces:" in result.output
