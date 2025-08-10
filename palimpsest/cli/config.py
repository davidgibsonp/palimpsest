"""
CLI configuration management for Palimpsest.

Handles user preferences, settings, and configuration files.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field


class CLIConfig(BaseModel):
    """Configuration model for Palimpsest CLI."""

    # Default settings
    default_tags: List[str] = Field(
        default_factory=list, description="Default tags for new traces"
    )
    default_domain: str = Field(default="", description="Default domain for new traces")

    # Display preferences
    default_search_limit: int = Field(
        default=10, description="Default number of search results"
    )
    default_list_limit: int = Field(
        default=10, description="Default number of traces to list"
    )
    output_format: str = Field(default="table", description="Default output format")

    # UI preferences
    use_colors: bool = Field(default=True, description="Enable colored output")
    show_progress: bool = Field(default=True, description="Show progress bars")
    truncate_length: int = Field(default=80, description="Text truncation length")

    # MCP server preferences
    mcp_server_name: str = Field(default="Palimpsest", description="MCP server name")
    mcp_transport_type: str = Field(default="stdio", description="MCP transport type")
    mcp_default_search_limit: int = Field(
        default=20, description="MCP default search limit"
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CLIConfig":
        """Create config from dictionary, handling nested structures."""
        # Flatten MCP settings if they exist
        if "mcp" in data:
            mcp_data = data.pop("mcp")
            for key, value in mcp_data.items():
                data[f"mcp_{key}"] = value

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary with nested MCP structure."""
        data = self.model_dump()

        # Group MCP settings
        mcp_settings = {}
        regular_settings = {}

        for key, value in data.items():
            if key.startswith("mcp_"):
                mcp_key = key.replace("mcp_", "")
                mcp_settings[mcp_key] = value
            else:
                regular_settings[key] = value

        if mcp_settings:
            regular_settings["mcp"] = mcp_settings

        return regular_settings


def get_config_paths() -> Dict[str, Path]:
    """
    Get configuration file paths.

    Returns:
        Dictionary with config file paths
    """
    # Project-specific config
    project_config = Path.cwd() / ".palimpsest" / "config.yaml"

    # User global config
    user_config_dir = Path.home() / ".palimpsest"
    user_config = user_config_dir / "config.yaml"

    # System config (fallback)
    system_config = Path("/etc/palimpsest/config.yaml")

    return {"project": project_config, "user": user_config, "system": system_config}


def load_config() -> CLIConfig:
    """
    Load configuration from files and environment variables.

    Priority order:
    1. Environment variables (PALIMPSEST_*)
    2. Project config (.palimpsest/config.yaml)
    3. User config (~/.palimpsest/config.yaml)
    4. System config (/etc/palimpsest/config.yaml)
    5. Default values

    Returns:
        Loaded CLIConfig instance
    """
    config_data = {}
    config_paths = get_config_paths()

    # Load from config files (lowest to highest priority)
    for config_type, config_path in config_paths.items():
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    file_data = yaml.safe_load(f) or {}
                config_data.update(file_data)
                logger.debug(f"Loaded {config_type} config from {config_path}")
            except Exception as e:
                logger.warning(
                    f"Failed to load {config_type} config from {config_path}: {e}"
                )

    # Override with environment variables
    env_overrides = _load_env_overrides()
    config_data.update(env_overrides)

    # Create config instance
    return CLIConfig.from_dict(config_data)


def save_config(config: CLIConfig, config_type: str = "user") -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration to save
        config_type: Type of config ('project', 'user', 'system')
    """
    config_paths = get_config_paths()
    config_path = config_paths[config_type]

    # Create directory if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Save config
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config.to_dict(), f, default_flow_style=False, indent=2)

    logger.info(f"Saved {config_type} config to {config_path}")


def _load_env_overrides() -> Dict[str, Any]:
    """Load configuration overrides from environment variables."""
    overrides = {}
    prefix = "PALIMPSEST_"

    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix) :].lower()

            # Convert string values to appropriate types
            if value.lower() in ("true", "false"):
                overrides[config_key] = value.lower() == "true"
            elif value.isdigit():
                overrides[config_key] = int(value)
            elif "," in value:  # List values
                overrides[config_key] = [item.strip() for item in value.split(",")]
            else:
                overrides[config_key] = value

    return overrides


def create_default_config(config_path: Path) -> None:
    """
    Create a default configuration file.

    Args:
        config_path: Path where to create the config file
    """
    default_config = CLIConfig()

    # Create directory if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Create config file with comments
    config_content = f"""# Palimpsest CLI Configuration
# Customize your trace collection and display settings

# Default tags to apply to new traces
default_tags: {default_config.default_tags}

# Default domain for traces
default_domain: "{default_config.default_domain}"

# Display preferences
default_search_limit: {default_config.default_search_limit}
default_list_limit: {default_config.default_list_limit}
output_format: "{default_config.output_format}"

# UI preferences
use_colors: {default_config.use_colors}
show_progress: {default_config.show_progress}
truncate_length: {default_config.truncate_length}

# MCP server settings
mcp:
  server_name: "{default_config.mcp_server_name}"
  transport_type: "{default_config.mcp_transport_type}"
  default_search_limit: {default_config.mcp_default_search_limit}
"""

    config_path.write_text(config_content)
    logger.info(f"Created default config at {config_path}")


def get_trace_id_completions(base_path: Optional[Path] = None) -> List[str]:
    """
    Get list of trace IDs for tab completion.

    Args:
        base_path: Base path for traces

    Returns:
        List of trace ID strings
    """
    try:
        from ..api.core import list_traces

        # Get recent traces for completion
        traces = list_traces(limit=100, base_path=base_path)
        return [trace["trace_id"] for trace in traces]

    except Exception as e:
        logger.debug(f"Failed to get trace completions: {e}")
        return []


def setup_completion() -> str:
    """
    Generate shell completion script.

    Returns:
        Shell completion script
    """
    return """
# Palimpsest CLI completion script
# Add this to your shell profile (.bashrc, .zshrc, etc.)

_palimpsest_completion() {
    local cur prev words cword
    _init_completion || return

    case "$prev" in
        show|get)
            # Complete trace IDs
            COMPREPLY=( $(compgen -W "$(palimpsest list --format=json 2>/dev/null | jq -r '.[].trace_id' 2>/dev/null)" -- "$cur") )
            return
            ;;
        --format)
            COMPREPLY=( $(compgen -W "table json detailed" -- "$cur") )
            return
            ;;
        --transport)
            COMPREPLY=( $(compgen -W "stdio http" -- "$cur") )
            return
            ;;
    esac

    case "$cur" in
        --*)
            COMPREPLY=( $(compgen -W "--help --base-path --verbose --limit --tags --domain --format --transport --auto-context --no-auto-context" -- "$cur") )
            return
            ;;
        *)
            COMPREPLY=( $(compgen -W "init add search list show stats server" -- "$cur") )
            return
            ;;
    esac
}

complete -F _palimpsest_completion palimpsest
"""
