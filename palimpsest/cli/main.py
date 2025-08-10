"""
CLI interface for Palimpsest.

Provides human-friendly command-line interface for managing execution traces.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger

from ..api.core import (
    create_trace as api_create_trace,
    get_stats as api_get_stats,
    get_trace as api_get_trace,
    list_traces as api_list_traces,
    search_traces as api_search_traces,
)
from ..exceptions import PalimpsestError, ValidationError
from ..mcp import run_server as mcp_run_server
from .config import (
    CLIConfig,
    load_config,
    save_config,
    create_default_config,
    setup_completion,
)
from .utils import (
    format_trace_summary,
    format_trace_details,
    print_error,
    print_success,
    print_info,
)


@click.group()
@click.option(
    "--base-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Base path for trace storage (defaults to current directory)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--config", type=click.Path(path_type=Path), help="Path to config file")
@click.pass_context
def cli(ctx, base_path: Optional[Path], verbose: bool, config: Optional[Path]):
    """
    Palimpsest - Preserve your AI development workflows.

    Their model. Your code. Your work.
    """
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)
    ctx.obj["base_path"] = base_path

    # Load configuration
    try:
        cli_config = load_config()
        ctx.obj["config"] = cli_config
    except Exception as e:
        logger.warning(f"Failed to load config: {e}, using defaults")
        ctx.obj["config"] = CLIConfig()

    # Configure logging
    log_level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        sink=lambda msg: click.echo(msg, err=True),
        level=log_level,
        format="<level>{level}: {message}</level>",
    )


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize .palimpsest directory in current project."""
    base_path = ctx.obj.get("base_path") or Path.cwd()
    palimpsest_dir = base_path / ".palimpsest"

    try:
        if palimpsest_dir.exists():
            print_info(f"Palimpsest directory already exists at {palimpsest_dir}")
            return

        # Create directory structure
        palimpsest_dir.mkdir(parents=True, exist_ok=True)
        (palimpsest_dir / "traces").mkdir(exist_ok=True)
        (palimpsest_dir / "logs").mkdir(exist_ok=True)

        # Create basic config file
        config_file = palimpsest_dir / "config.yaml"
        config_content = """# Palimpsest Configuration
# Customize your trace collection and storage settings

# Default tags to apply to new traces
default_tags: []

# Default domain for traces
default_domain: ""

# MCP server settings
mcp:
  server_name: "Palimpsest"
  transport_type: "stdio"
  default_search_limit: 20
"""
        config_file.write_text(config_content)

        print_success(f"Initialized Palimpsest at {palimpsest_dir}")
        print_info(
            "You can now start creating traces with 'palimpsest add <trace-file>'"
        )

    except Exception as e:
        print_error(f"Failed to initialize Palimpsest: {e}")
        sys.exit(1)


@cli.command()
@click.argument(
    "trace_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--auto-context/--no-auto-context",
    default=True,
    help="Automatically collect environment context",
)
@click.pass_context
def add(ctx, trace_file: Path, auto_context: bool):
    """Add trace from JSON file."""
    base_path = ctx.obj.get("base_path")

    try:
        # Load trace data from file
        with open(trace_file, "r", encoding="utf-8") as f:
            trace_data = json.load(f)

        # Create trace
        trace_id = api_create_trace(
            trace_data, auto_context=auto_context, base_path=base_path
        )

        print_success(f"Created trace: {trace_id}")
        print_info(f"Problem: {trace_data.get('problem_statement', 'N/A')}")

    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in {trace_file}: {e}")
        sys.exit(1)
    except ValidationError as e:
        print_error(f"Invalid trace data: {e}")
        sys.exit(1)
    except PalimpsestError as e:
        print_error(f"Failed to create trace: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--limit", "-l", default=10, help="Maximum number of results")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--domain", help="Filter by domain")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def search(
    ctx,
    query: str,
    limit: int,
    tags: Optional[str],
    domain: Optional[str],
    output_format: str,
):
    """Search traces with query."""
    base_path = ctx.obj.get("base_path")

    try:
        # Build filters
        filters = {}
        if tags:
            filters["tags"] = [tag.strip() for tag in tags.split(",")]
        if domain:
            filters["domain"] = domain

        # Search traces
        results = api_search_traces(
            query, filters if filters else None, limit, base_path
        )

        if not results:
            print_info("No traces found matching your query")
            return

        if output_format == "json":
            click.echo(json.dumps(results, indent=2))
        else:
            print_info(f"Found {len(results)} traces:")
            for trace in results:
                click.echo(format_trace_summary(trace))
                click.echo()

    except PalimpsestError as e:
        print_error(f"Search failed: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


@cli.command()
@click.option("--limit", "-l", default=10, help="Maximum number of traces to show")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list(ctx, limit: int, output_format: str):
    """List recent traces."""
    base_path = ctx.obj.get("base_path")

    try:
        traces = api_list_traces(limit, base_path)

        if not traces:
            print_info("No traces found")
            return

        if output_format == "json":
            click.echo(json.dumps(traces, indent=2))
        else:
            print_info(f"Recent {len(traces)} traces:")
            for trace in traces:
                click.echo(format_trace_summary(trace))
                click.echo()

    except PalimpsestError as e:
        print_error(f"Failed to list traces: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


@cli.command()
@click.argument("trace_id")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["detailed", "json"]),
    default="detailed",
    help="Output format",
)
@click.pass_context
def show(ctx, trace_id: str, output_format: str):
    """Display full trace details."""
    base_path = ctx.obj.get("base_path")

    try:
        trace = api_get_trace(trace_id, base_path)

        if output_format == "json":
            click.echo(json.dumps(trace, indent=2))
        else:
            click.echo(format_trace_details(trace))

    except PalimpsestError as e:
        print_error(f"Failed to get trace {trace_id}: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show statistics about stored traces."""
    base_path = ctx.obj.get("base_path")

    try:
        stats_data = api_get_stats(base_path)

        click.echo(click.style("=== Palimpsest Statistics ===", bold=True))
        click.echo(f"Total traces: {stats_data.get('trace_count', 0)}")
        click.echo(f"Total size: {stats_data.get('total_size_mb', 0):.2f} MB")

        if "tags" in stats_data and stats_data["tags"]:
            click.echo(f"Tags: {', '.join(stats_data['tags'][:10])}")
            if len(stats_data["tags"]) > 10:
                click.echo(f"  ... and {len(stats_data['tags']) - 10} more")

        if "domains" in stats_data and stats_data["domains"]:
            click.echo(f"Domains: {', '.join(stats_data['domains'])}")

        if "oldest_trace" in stats_data:
            click.echo(f"Oldest trace: {stats_data['oldest_trace']}")
        if "newest_trace" in stats_data:
            click.echo(f"Newest trace: {stats_data['newest_trace']}")

    except PalimpsestError as e:
        print_error(f"Failed to get statistics: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


@cli.group()
def server():
    """MCP server management commands."""
    pass


@server.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    help="Transport type for MCP server",
)
@click.pass_context
def start(ctx, transport: str):
    """Start MCP server for AI agent access."""
    base_path = ctx.obj.get("base_path")

    try:
        print_info(f"Starting Palimpsest MCP server with {transport} transport...")
        print_info(f"Base path: {base_path or 'current directory'}")

        # Import and configure MCP server
        from ..mcp.config import MCPServerConfig

        config = MCPServerConfig(transport_type=transport, base_path=base_path)

        # Run server
        mcp_run_server(config)

    except KeyboardInterrupt:
        print_info("Server stopped by user")
    except Exception as e:
        print_error(f"Failed to start MCP server: {e}")
        sys.exit(1)


@server.command()
def stop():
    """Stop running MCP server."""
    try:
        # Try to find and stop running server process
        result = subprocess.run(
            ["pgrep", "-f", "palimpsest.*server.*start"], capture_output=True, text=True
        )

        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid:
                    subprocess.run(["kill", pid])
                    print_success(f"Stopped server process {pid}")
        else:
            print_info("No running MCP server found")

    except Exception as e:
        print_error(f"Failed to stop server: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"]),
    default="bash",
    help="Shell type for completion script",
)
def completion(shell: str):
    """Generate shell completion script."""
    if shell in ["bash", "zsh"]:
        click.echo(setup_completion())
    else:
        print_info(f"Completion for {shell} not yet supported. Use bash or zsh.")


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command(name="init")
@click.option(
    "--type",
    "config_type",
    type=click.Choice(["project", "user"]),
    default="user",
    help="Configuration type to create",
)
def config_init(config_type: str):
    """Initialize configuration file."""
    try:
        from .config import get_config_paths

        config_paths = get_config_paths()
        config_path = config_paths[config_type]

        if config_path.exists():
            if not click.confirm(
                f"Config file {config_path} already exists. Overwrite?"
            ):
                return

        create_default_config(config_path)
        print_success(f"Created {config_type} config at {config_path}")

    except Exception as e:
        print_error(f"Failed to create config: {e}")
        sys.exit(1)


@config.command(name="show")
def config_show():
    """Show current configuration."""
    try:
        cli_config = load_config()
        config_dict = cli_config.to_dict()

        click.echo(click.style("=== Current Configuration ===", bold=True))
        click.echo(json.dumps(config_dict, indent=2))

    except Exception as e:
        print_error(f"Failed to load config: {e}")
        sys.exit(1)


@config.command()
@click.argument("key")
@click.argument("value")
@click.option(
    "--type",
    "config_type",
    type=click.Choice(["project", "user"]),
    default="user",
    help="Configuration type to update",
)
def set(key: str, value: str, config_type: str):
    """Set configuration value."""
    try:
        cli_config = load_config()

        # Parse value type
        if value.lower() in ("true", "false"):
            parsed_value = value.lower() == "true"
        elif value.isdigit():
            parsed_value = int(value)
        elif "," in value:
            parsed_value = [item.strip() for item in value.split(",")]
        else:
            parsed_value = value

        # Update config
        config_dict = cli_config.to_dict()
        config_dict[key] = parsed_value

        updated_config = CLIConfig.from_dict(config_dict)
        save_config(updated_config, config_type)

        print_success(f"Updated {key} = {parsed_value} in {config_type} config")

    except Exception as e:
        print_error(f"Failed to update config: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
