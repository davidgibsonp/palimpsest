"""
MCP (Model Context Protocol) server implementation for Palimpsest.

This module provides MCP server functionality to allow AI agents to interact
with Palimpsest execution traces through standardized protocol.
"""

from .config import MCPServerConfig, load_config
from .lifecycle import MCPServerManager, run_server
from .server import PalimpsestMCPServer

__all__ = [
    "PalimpsestMCPServer",
    "MCPServerConfig",
    "MCPServerManager",
    "load_config",
    "run_server",
]
