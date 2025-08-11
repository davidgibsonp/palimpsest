"""
CLI utility functions for formatting and output.

Provides helper functions for human-friendly display of trace data.
"""

from datetime import datetime
from typing import Any, Dict, List

import click


def truncate_text(text: str, max_length: int = 80) -> str:
    """
    Truncate text to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_timestamp(timestamp_str: str) -> str:
    """
    Format timestamp string for human readability.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        Human-readable timestamp
    """
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return timestamp_str


def format_tags(tags: List[str]) -> str:
    """
    Format list of tags for display.

    Args:
        tags: List of tag strings

    Returns:
        Formatted tag string
    """
    if not tags:
        return "No tags"

    if len(tags) <= 3:
        return ", ".join(tags)

    return f"{', '.join(tags[:3])} (+{len(tags) - 3} more)"


def format_execution_steps(steps: List[Dict[str, Any]], max_steps: int = 3) -> str:
    """
    Format execution steps for summary display.

    Args:
        steps: List of execution step dictionaries
        max_steps: Maximum number of steps to show

    Returns:
        Formatted steps string
    """
    if not steps:
        return "No steps"

    formatted_steps = []
    for i, step in enumerate(steps[:max_steps]):
        action = step.get("action", "unknown")
        content = step.get("content", "")
        truncated_content = truncate_text(content, 50)
        formatted_steps.append(f"{i + 1}. [{action}] {truncated_content}")

    if len(steps) > max_steps:
        formatted_steps.append(f"... and {len(steps) - max_steps} more steps")

    return "\n    ".join(formatted_steps)


def format_trace_summary(trace: Dict[str, Any]) -> str:
    """
    Format trace data as a summary for list/search display.

    Args:
        trace: Trace dictionary

    Returns:
        Formatted trace summary string
    """
    trace_id = trace.get("trace_id", "unknown")
    problem = trace.get("problem_statement", "No problem statement")
    outcome = trace.get("outcome", "No outcome")
    created_at = trace.get("created_at", "")
    tags = trace.get("tags", [])
    domain = trace.get("domain", "")

    # Format components
    header = click.style(f"🔍 {trace_id[:12]}...", bold=True, fg="cyan")
    timestamp = click.style(f"[{format_timestamp(created_at)}]", dim=True)
    domain_str = click.style(f"({domain})", fg="blue") if domain else ""

    problem_line = click.style("Problem: ", bold=True) + truncate_text(problem, 70)
    outcome_line = click.style("Outcome: ", bold=True) + truncate_text(outcome, 70)
    tags_line = click.style("Tags: ", bold=True) + format_tags(tags)

    return f"{header} {timestamp} {domain_str}\n  {problem_line}\n  {outcome_line}\n  {tags_line}"


def format_trace_details(trace: Dict[str, Any]) -> str:
    """
    Format complete trace data for detailed display.

    Args:
        trace: Trace dictionary

    Returns:
        Formatted detailed trace string
    """
    trace_id = trace.get("trace_id", "unknown")
    problem = trace.get("problem_statement", "No problem statement")
    outcome = trace.get("outcome", "No outcome")
    steps = trace.get("execution_steps", [])
    created_at = trace.get("created_at", "")
    tags = trace.get("tags", [])
    domain = trace.get("domain", "")

    # Build detailed view
    lines = []

    # Header
    lines.append(click.style("=" * 80, bold=True))
    lines.append(click.style(f"TRACE: {trace_id}", bold=True, fg="cyan"))
    lines.append(click.style("=" * 80, bold=True))

    # Metadata
    lines.append(f"{click.style('Created:', bold=True)} {format_timestamp(created_at)}")
    if domain:
        lines.append(f"{click.style('Domain:', bold=True)} {domain}")
    if tags:
        lines.append(f"{click.style('Tags:', bold=True)} {', '.join(tags)}")

    lines.append("")

    # Problem statement
    lines.append(click.style("PROBLEM STATEMENT:", bold=True, fg="yellow"))
    lines.append("-" * 20)
    lines.append(problem)
    lines.append("")

    # Execution steps
    lines.append(click.style("EXECUTION STEPS:", bold=True, fg="green"))
    lines.append("-" * 20)
    if steps:
        for i, step in enumerate(steps, 1):
            action = step.get("action", "unknown")
            content = step.get("content", "")

            step_header = click.style(f"Step {i}: [{action.upper()}]", bold=True)
            lines.append(step_header)
            lines.append(content)
            lines.append("")
    else:
        lines.append("No execution steps recorded")
        lines.append("")

    # Outcome
    lines.append(click.style("OUTCOME:", bold=True, fg="magenta"))
    lines.append("-" * 20)
    lines.append(outcome)
    lines.append("")

    # Environment context if available
    if "context" in trace:
        context = trace["context"]
        lines.append(click.style("ENVIRONMENT CONTEXT:", bold=True, fg="blue"))
        lines.append("-" * 20)

        for key, value in context.items():
            if key not in ["trace_id", "created_at"]:  # Skip redundant info
                lines.append(f"{key}: {value}")
        lines.append("")

    lines.append(click.style("=" * 80, bold=True))

    return "\n".join(lines)


def print_success(message: str) -> None:
    """Print success message with green color."""
    click.echo(click.style(f"✅ {message}", fg="green"))


def print_error(message: str) -> None:
    """Print error message with red color."""
    click.echo(click.style(f"❌ {message}", fg="red"), err=True)


def print_warning(message: str) -> None:
    """Print warning message with yellow color."""
    click.echo(click.style(f"⚠️  {message}", fg="yellow"))


def print_info(message: str) -> None:
    """Print info message with blue color."""
    click.echo(click.style(f"ℹ️  {message}", fg="blue"))


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation.

    Args:
        message: Confirmation message
        default: Default value if user just presses Enter

    Returns:
        True if user confirms, False otherwise
    """
    return click.confirm(message, default=default)


def prompt_for_input(message: str, default: str = None) -> str:
    """
    Prompt user for text input.

    Args:
        message: Prompt message
        default: Default value if user just presses Enter

    Returns:
        User input string
    """
    return click.prompt(message, default=default)


def create_progress_bar(iterable, length: int = None, label: str = "Processing") -> Any:
    """
    Create a progress bar for iteration.

    Args:
        iterable: Iterable to wrap with progress bar
        length: Total length if known
        label: Label for progress bar

    Returns:
        Progress bar wrapped iterable
    """
    return click.progressbar(iterable, length=length, label=label)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.2 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
