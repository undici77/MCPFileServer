#!/usr/bin/env python3
"""Main MCP file server class."""

import logging
from pathlib import Path
from typing import Optional, Any

from models import MCPMessage
from tools import get_tool_definitions
from handlers import FileHandlers

logger = logging.getLogger(__name__)


class MCPFileServer:
    """
    File‑system MCP server with enhanced security features.

    The working directory can be supplied on start‑up (via CLI) or defaults to the current
    process directory. All file operations are sandboxed inside this directory — any attempt
    to access a path outside results in an "Access denied" error.
    """

    def __init__(self, work_dir: Optional[Path] = None):
        # Resolve once at start‑up so we always compare absolute paths.
        self.working_directory = (work_dir or Path.cwd()).resolve()
        self.handlers = FileHandlers(self.working_directory)
        logger.info(f"Server started with working directory: {self.working_directory}")

    async def handle_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Dispatch incoming RPC messages to the appropriate handler."""
        try:
            if message.method == "initialize":
                return self.handle_initialize(message)
            elif message.method == "tools/list":
                return self.handle_tools_list(message)
            elif message.method == "tools/call":
                return await self.handle_tool_call(message)
            else:
                return self.handlers.create_error_response(
                    message.id, -32601, f"Method not found: {message.method}"
                )
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return self.handlers.create_error_response(
                message.id, -32603, f"Internal error: {str(e)}"
            )

    def handle_initialize(self, message: MCPMessage) -> MCPMessage:
        """Respond to the `initialize` request."""
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "file-server", "version": "1.2.0"},
        }
        return MCPMessage(id=message.id, result=result)

    def handle_tools_list(self, message: MCPMessage) -> MCPMessage:
        """Return the list of tools that the server supports."""
        tools = get_tool_definitions()
        result = {"tools": [tool.to_dict() for tool in tools]}
        return MCPMessage(id=message.id, result=result)

    async def handle_tool_call(self, message: MCPMessage) -> MCPMessage:
        """Dispatch a tool call to the concrete implementation."""
        try:
            params = message.params
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "read_file":
                return await self.handlers.handle_read_file(message.id, arguments)
            elif tool_name == "write_file":
                return await self.handlers.handle_write_file(message.id, arguments)
            elif tool_name == "list_files":
                return self.handlers.handle_list_files(message.id, arguments)
            elif tool_name == "create_directory":
                return self.handlers.handle_create_directory(message.id, arguments)
            elif tool_name == "delete_file":
                return await self.handlers.handle_delete_file(message.id, arguments)
            elif tool_name == "delete_directory":
                return await self.handlers.handle_delete_directory(message.id, arguments)
            elif tool_name == "search_in_file":
                return await self.handlers.handle_search_in_file(message.id, arguments)
            else:
                return self.handlers.create_error_response(
                    message.id, -32602, f"Unknown tool: {tool_name}"
                )
        except Exception as e:
            return self.handlers.create_error_response(
                message.id, -32603, f"Error processing tool call: {str(e)}"
            )