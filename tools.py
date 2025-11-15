#!/usr/bin/env python3
"""Tool definitions for the MCP file server."""

from models import Tool


def get_tool_definitions():
    """Return the list of tools that the server supports."""
    return [
        Tool(
            name="read_file",
            description="Read the contents of a file inside the working directory. Use binary=True to read binary files (returns base64-encoded content).",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to read (relative to the working directory)",
                    },
                    "binary": {
                        "type": "boolean",
                        "description": "Whether to read the file as binary data (returns base64-encoded content)",
                        "default": False
                    }
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="write_file",
            description="Write content to a file inside the working directory. Use binary=True to write binary data (content should be base64-encoded).",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to write (relative to the working directory)",
                    },
                    "content": {"type": "string", "description": "Content to write (text or base64-encoded binary data)"},
                    "binary": {
                        "type": "boolean",
                        "description": "Whether the content is binary data (base64-encoded)",
                        "default": False
                    }
                },
                "required": ["path", "content"],
            },
        ),
        Tool(
            name="list_files",
            description="List files inside the working directory with optional extension filtering and recursion control.",
            input_schema={
                "type": "object",
                "properties": {
                    "extensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of file extensions to filter by (e.g., ['.py', '.txt']). If empty or omitted, all files are included."
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to search recursively in subdirectories (default: true)",
                        "default": True
                    },
                    "show_empty_dirs": {
                        "type": "boolean",
                        "description": "Whether to show directories that contain no files (either truly empty or containing no files matching the extension filter) (default: true)",
                        "default": True
                    }
                }
            },
        ),
        Tool(
            name="create_directory",
            description="Create a new sub‑directory inside the working directory.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to create"}
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="delete_file",
            description="Delete a file inside the working directory.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path of the file to delete"}
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="delete_directory",
            description="Delete a directory and all its contents inside the working directory.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path of the directory to delete"},
                    "force": {
                        "type": "boolean", 
                        "description": "Force deletion even if directory is not empty",
                        "default": False
                    }
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="search_in_file",
            description="Search for a string in a file or recursively in all files within a directory and return text excerpts around each occurrence. When path is a directory, searches through all files in the directory and its subdirectories. Useful for large files where you only need relevant sections.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File or directory path to search in (relative to the working directory). When a directory is provided, searches recursively in all files within it."
                    },
                    "search_string": {
                        "type": "string",
                        "description": "String to search for in the file(s)"
                    },
                    "context_lines": {
                        "type": "integer",
                        "description": "Number of lines to include before and after each match (default: 3)",
                        "default": 3
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether the search should be case-sensitive (default: false)",
                        "default": False
                    },
                    "max_matches": {
                        "type": "integer",
                        "description": "Maximum number of matches to return per file (default: 50)",
                        "default": 50
                    }
                },
                "required": ["path", "search_string"],
            },
        ),
    ]