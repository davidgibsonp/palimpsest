"""
MCP Server configuration management for Palimpsest.

Handles configuration loading, environment variables, and server settings.
"""

import os
from pathlib import Path
from typing import Optional

from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPServerConfig(BaseSettings):
    """Configuration settings for Palimpsest MCP Server."""

    model_config = SettingsConfigDict(
        env_prefix="PALIMPSEST_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Server settings
    server_name: str = Field(default="Palimpsest", description="MCP server name")
    transport_type: str = Field(
        default="stdio", description="Transport type (stdio, http)"
    )

    # Storage settings
    base_path: Optional[Path] = Field(
        default=None, description="Base path for trace storage"
    )
    auto_context: bool = Field(
        default=True, description="Automatically collect environment context"
    )

    # Performance settings
    default_search_limit: int = Field(
        default=20, description="Default limit for search results"
    )
    max_search_limit: int = Field(
        default=100, description="Maximum limit for search results"
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_to_file: bool = Field(default=True, description="Enable file logging")

    def configure_logging(self) -> None:
        """Configure logging after initialization."""
        # Configure console logging
        logger.remove()  # Remove default handler
        logger.add(
            sink=lambda msg: print(msg, end=""),
            level=self.log_level,
            format="<green>{time}</green> | <level>{level: <8}</level> | <cyan>MCP</cyan> | {message}",
        )

        # Add file logging if enabled
        if self.log_to_file and self.base_path:
            log_file = self.base_path / ".palimpsest" / "logs" / "mcp_server.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                sink=str(log_file),
                level=self.log_level,
                rotation="10 MB",
                retention="7 days",
                format="{time} | {level} | MCP | {message}",
            )


def load_config() -> MCPServerConfig:
    """
    Load MCP server configuration from environment and config files.

    Returns:
        Configured MCPServerConfig instance
    """
    return MCPServerConfig()


def get_base_path_from_env() -> Optional[Path]:
    """
    Get base path from environment variables or current directory.

    Returns:
        Path object for storage base path, or None for current directory
    """
    # Check for explicit environment variable
    if env_path := os.getenv("PALIMPSEST_BASE_PATH"):
        return Path(env_path).expanduser().resolve()

    # Check for project-specific .palimpsest directory
    current_dir = Path.cwd()
    palimpsest_dir = current_dir / ".palimpsest"
    if palimpsest_dir.exists():
        return current_dir

    # Default to current directory
    return None
