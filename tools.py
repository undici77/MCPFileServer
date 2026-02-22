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
        Tool(
            name="git_status",
            description="Show the working tree status. Returns a short summary of changes in the repository.",
            input_schema={
                "type": "object",
                "properties": {
                    "short": {
                        "type": "boolean",
                        "description": "Use short format output (default: true)",
                        "default": True
                    }
                },
            },
        ),
        Tool(
            name="git_log",
            description="Show commit log history. Displays commits in a compact format.",
            input_schema={
                "type": "object",
                "properties": {
                    "max_count": {
                        "type": "integer",
                        "description": "Maximum number of commits to show (default: 20)",
                        "default": 20
                    },
                    "oneline": {
                        "type": "boolean",
                        "description": "Show compact one-line format (default: true)",
                        "default": True
                    }
                },
            },
        ),
        Tool(
            name="git_checkout",
            description="Switch to a different branch or commit.",
            input_schema={
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": "Branch name or commit hash to checkout"
                    }
                },
                "required": ["branch"],
            },
        ),
        Tool(
            name="git_branch_create",
            description="Create a new branch.",
            input_schema={
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": "Name of the new branch"
                    },
                    "start_point": {
                        "type": "string",
                        "description": "Starting point (branch or commit) for the new branch"
                    }
                },
                "required": ["branch"],
            },
        ),
        Tool(
            name="git_branch_delete",
            description="Delete a branch.",
            input_schema={
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": "Name of the branch to delete"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force deletion even if branch has unmerged changes (default: false)",
                        "default": False
                    }
                },
                "required": ["branch"],
            },
        ),
        Tool(
            name="git_branch_list",
            description="List all branches in the repository.",
            input_schema={
                "type": "object",
                "properties": {
                    "all": {
                        "type": "boolean",
                        "description": "List both local and remote branches (default: false)",
                        "default": False
                    }
                },
            },
        ),
        Tool(
            name="git_add",
            description="Add file contents to the staging area.",
            input_schema={
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to add"
                    }
                },
                "required": ["paths"],
            },
        ),
        Tool(
            name="git_commit",
            description="Record changes to the repository.",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Commit message"
                    },
                    "all": {
                        "type": "boolean",
                        "description": "Automatically stage all modified and deleted files (default: false)",
                        "default": False
                    }
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="git_push",
            description="Push changes to a remote repository.",
            input_schema={
                "type": "object",
                "properties": {
                    "remote": {
                        "type": "string",
                        "description": "Remote repository name (default: origin)",
                        "default": "origin"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch to push (default: current branch)"
                    }
                },
            },
        ),
        Tool(
            name="git_pull",
            description="Fetch from and integrate with a remote repository.",
            input_schema={
                "type": "object",
                "properties": {
                    "remote": {
                        "type": "string",
                        "description": "Remote repository name (default: origin)",
                        "default": "origin"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch to pull (default: current branch)"
                    }
                },
            },
        ),
        Tool(
            name="git_diff",
            description="Show changes between commits, commit and working tree, etc.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Specific file or directory to show diff for"
                    }
                },
            },
        ),
        Tool(
            name="git_clone",
            description="Clone a repository into a new directory. Use with caution - will overwrite existing directories.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the repository to clone (HTTPS or SSH)"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory name where the repository will be cloned (relative to working directory)"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Specific branch to checkout after cloning"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Clone submodules recursively (default: false)",
                        "default": False
                    }
                },
                "required": ["url", "path"],
            },
        ),
        Tool(
            name="git_submodule_add",
            description="Add a submodule to the repository.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the repository to add as submodule"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path where the submodule will be placed"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name for the submodule (optional, defaults to path)"
                    }
                },
                "required": ["url", "path"],
            },
        ),
        Tool(
            name="git_submodule_update",
            description="Update existing submodules.",
            input_schema={
                "type": "object",
                "properties": {
                    "init": {
                        "type": "boolean",
                        "description": "Initialize submodules before updating (default: true)",
                        "default": True
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Update submodules recursively (default: true)",
                        "default": True
                    }
                },
            },
        ),
        Tool(
            name="git_submodule_list",
            description="List all submodules in the repository.",
            input_schema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "boolean",
                        "description": "Show summary of submodule status (default: true)",
                        "default": True
                    }
                },
            },
        ),
    ]