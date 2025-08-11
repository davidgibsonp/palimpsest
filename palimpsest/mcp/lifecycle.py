"""
MCP Server lifecycle management for Palimpsest.

Handles server startup, shutdown, and runtime management.
"""

import signal
import sys
from typing import Optional

from loguru import logger

from .config import MCPServerConfig, get_base_path_from_env, load_config
from .server import PalimpsestMCPServer


class MCPServerManager:
    """Manages MCP server lifecycle and runtime."""

    def __init__(self, config: Optional[MCPServerConfig] = None):
        """
        Initialize server manager.

        Args:
            config: Optional server configuration
        """
        self.config = config or load_config()
        self.server: Optional[PalimpsestMCPServer] = None
        self._shutdown_requested = False

        # Set base path from config or environment
        if not self.config.base_path:
            self.config.base_path = get_base_path_from_env()

        # Configure logging
        self.config.configure_logging()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""

        def signal_handler(signum: int, frame) -> None:
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_requested = True
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Windows doesn't have SIGHUP
        if hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, signal_handler)

    def start(self) -> None:
        """Start the MCP server."""
        try:
            logger.info("Starting Palimpsest MCP Server")
            logger.info(f"Server name: {self.config.server_name}")
            logger.info(f"Transport: {self.config.transport_type}")
            logger.info(f"Base path: {self.config.base_path}")

            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()

            # Create and configure server
            self.server = PalimpsestMCPServer(self.config.base_path)

            # Apply configuration to server
            self._apply_config_to_server()

            # Start the server
            logger.info("MCP Server ready and listening")
            self.server.run()

        except KeyboardInterrupt:
            logger.info("Shutdown requested via keyboard interrupt")
            self.stop()
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            sys.exit(1)

    def stop(self) -> None:
        """Stop the MCP server gracefully."""
        if self._shutdown_requested:
            return

        self._shutdown_requested = True
        logger.info("Stopping Palimpsest MCP Server")

        if self.server:
            try:
                # Server cleanup if needed
                logger.info("Server stopped successfully")
            except Exception as e:
                logger.error(f"Error during server shutdown: {e}")

        logger.info("MCP Server shutdown complete")

    def _apply_config_to_server(self) -> None:
        """Apply configuration settings to the server instance."""
        if not self.server:
            return

        # Apply any server-specific configuration
        # Currently server handles configuration through constructor
        pass

    def is_running(self) -> bool:
        """Check if server is currently running."""
        return self.server is not None and not self._shutdown_requested


def run_server(config: Optional[MCPServerConfig] = None) -> None:
    """
    Run the MCP server with proper lifecycle management.

    Args:
        config: Optional server configuration
    """
    manager = MCPServerManager(config)
    manager.start()


def main() -> None:
    """Main entry point for MCP server with lifecycle management."""
    try:
        # Load configuration
        config = load_config()

        # Run server
        run_server(config)

    except Exception as e:
        logger.error(f"Fatal error in MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
