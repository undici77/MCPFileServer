#!/usr/bin/env python3
"""Data models for MCP protocol messages and responses."""

from typing import Dict, Any, List, Optional, Union


class MCPMessage:
    """Representation of a JSON‑RPC 2.0 message."""

    def __init__(
        self,
        jsonrpc: str = "2.0",
        id: Optional[Union[str, int]] = None,
        method: Optional[str] = None,
        params: Optional[Any] = None,
        result: Optional[Any] = None,
        error: Optional[Any] = None,
    ):
        self.jsonrpc = jsonrpc
        self.id = id
        self.method = method
        self.params = params
        self.result = result
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        data = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            data["id"] = self.id
        if self.method is not None:
            data["method"] = self.method
        if self.params is not None:
            data["params"] = self.params
        if self.result is not None:
            data["result"] = self.result
        if self.error is not None:
            data["error"] = self.error
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMessage":
        """Create an instance from a dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error"),
        )


class MCPError:
    """Simple JSON‑RPC error container."""

    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


class Tool:
    """Metadata for a tool exposed by the server."""

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class ContentBlock:
    """A single block of textual content returned by a tool."""

    def __init__(self, type: str, text: str):
        self.type = type
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "text": self.text}


class ToolResult:
    """Result wrapper for a tool call."""

    def __init__(self, content: List[ContentBlock], is_error: bool = False):
        self.content = content
        self.is_error = is_error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": [block.to_dict() for block in self.content],
            "isError": self.is_error,
        }