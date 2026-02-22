# 📂 MCP File Server

**MCP File Server** is a secure, sandboxed file server providing controlled access to filesystem operations via the **Model Control Protocol (MCP)**. It supports reading, writing, listing, creating, and deleting files and directories within a configurable working directory while enforcing strict security checks. Git operations are also available for repositories in the working directory.

## Table of Contents
- [Features](#features)
- [Installation & Quick Start](#installation--quick-start)
- [Command‑Line Options](#commandline-options)
- [Integration with LM Studio](#integration-with-lm-studio)
- [MCP API Overview](#mcp-api-overview)
  - [`initialize`](#initialize)
  - [`tools/list`](#toolslist)
  - [`tools/call`](#toolscall)
- [Available Tools](#available-tools)
  - [File Operations](#file-operations)
    - [`read_file`](#read_file)
    - [`write_file`](#write_file)
    - [`list_files`](#list_files)
    - [`create_directory`](#create_directory)
    - [`delete_file`](#delete_file)
    - [`delete_directory`](#delete_directory)
    - [`search_in_file`](#search_in_file)
  - [Git Operations](#git-operations)
    - [`git_status`](#git_status)
    - [`git_log`](#git_log)
    - [`git_checkout`](#git_checkout)
    - [`git_branch_create`](#git_branch_create)
    - [`git_branch_delete`](#git_branch_delete)
    - [`git_branch_list`](#git_branch_list)
    - [`git_add`](#git_add)
    - [`git_commit`](#git_commit)
    - [`git_push`](#git_push)
    - [`git_pull`](#git_pull)
    - [`git_diff`](#git_diff)
    - [`git_clone`](#git_clone)
    - [`git_submodule_add`](#git_submodule_add)
    - [`git_submodule_update`](#git_submodule_update)
    - [`git_submodule_list`](#git_submodule_list)
- [Security Features](#security-features)

## 🎯 Features
- **Sandboxed operations** – all paths are confined to a user‑specified working directory.
- **Path traversal protection**, file‑size limits, and blocked extensions.
- Binary support via Base64 encoding for safe transport of non‑text data.
- Git operations (status, log, branches, commit/push/pull) for repositories in the working directory.
- Simple line‑delimited JSON‑RPC protocol suitable for stdin/stdout integration.
- Ready‑to‑use with **LM Studio** through a minimal `mcp.json` configuration.

## 📦 Installation & Quick Start
```bash
# Clone the repository (if not already done)
git clone https://github.com/undici77/MCPFileServer.git
cd MCPFileServer

# Ensure git is installed on your system (required for git operations)
git --version

# Run the startup script – it creates a virtual environment,
# installs dependencies, and starts the server.
./run.sh -d /path/to/working/directory
```
The script will:
- Verify that Python 3 is available.
- Create a `.venv` virtual environment (if missing).
- Install required packages (`aiofiles`).
- Start `main.py` with the supplied working directory.

> 📌 **Note for Git Operations**: The git operations use Python's `subprocess` to call the system `git` CLI. Git must be installed and available in your PATH.
>
> 📌 **Tip:** Ensure the script has execution permission:
> `chmod +x run.sh`

## ⚙️ Command‑Line Options
| Option | Description |
|--------|-------------|
| `-d`, `--directory` | Path to the **working directory**. If omitted, the server uses the current process directory. The directory must exist and be readable/writable. |

## 🤝 Integration with LM Studio
Add an entry for the file server in your project's `mcp.json`:
```json
{
  "mcpServers": {
    "file-server": {
      "command": "/absolute/path/to/MCPFileServer/run.sh",
      "args": [
        "-d",
        "/absolute/path/to/working/directory"
      ],
      "env": {
        "WORKING_DIR": "."
      }
    }
  }
}
```
- Replace the paths with absolute locations on your machine.
- Ensure `run.sh` is executable (`chmod +x run.sh`) and dependencies are installed.

## 📡 MCP API Overview
All communication follows **JSON‑RPC 2.0** over stdin/stdout.

### `initialize`
Sent by the client to obtain server capabilities.
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```
The server responds with protocol version, capabilities, and its name/version.

### `tools/list`
Retrieves a machine‑readable list of supported tools.
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```
The response contains an array of tool definitions (name, description, input schema).

### `tools/call`
Invokes a specific tool.
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "<tool_name>",
    "arguments": { … }
  }
}
```
> **Note:** The key for the tool name is `**name**`, not `tool`. This matches the server implementation.

## 🛠️ Available Tools

### File Operations

| Tool | Description |
|------|-------------|
| `read_file` | Read a file's contents (text or binary). |
| `write_file` | Write text or Base64‑encoded binary data to a file. |
| `list_files` | List files and directories with optional filtering. |
| `create_directory` | Create a new sub‑directory (parents created as needed). |
| `delete_file` | Delete a single file. |
| `delete_directory` | Remove a directory; optionally force deletion of non‑empty trees. |
| `search_in_file` | Search for a string in a file or recursively in a directory, returning contextual excerpts. |

### read_file
Read the contents of a file inside the working directory.
**Parameters**
| Name   | Type    | Required | Description |
|--------|---------|----------|-------------|
| `path` | string  | ✅ | Relative path to the target file. |
| `binary` | boolean | ❌ (default: `false`) | Set to `true` to read the file as binary; the result is Base64‑encoded. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "example.txt",
      "binary": false
    }
  }
}
```

### write_file
Write content to a file (creating intermediate directories if needed).
**Parameters**
| Name   | Type    | Required | Description |
|--------|---------|----------|-------------|
| `path` | string  | ✅ | Relative path of the target file. |
| `content` | string | ✅ | Text to write, or Base64‑encoded binary data when `binary=true`. |
| `binary` | boolean | ❌ (default: `false`) | Set to `true` to treat `content` as Base64‑encoded binary. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "write_file",
    "arguments": {
      "path": "output.txt",
      "content": "Hello, world!",
      "binary": false
    }
  }
}
```

### list_files
List files and directories under the working directory.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `extensions` | array of strings | ❌ | Filter by file extensions (e.g., `[".py", ".txt"]`). If omitted, all files are listed. |
| `recursive` | boolean | ❌ (default: `true`) | Search sub‑directories recursively when `true`. |
| `show_empty_dirs` | boolean | ❌ (default: `true`) | Include directories that contain no matching files. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "list_files",
    "arguments": {
      "extensions": [".py", ".txt"],
      "recursive": true,
      "show_empty_dirs": false
    }
  }
}
```

### create_directory
Create a new directory (including any missing parent directories).
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✅ | Relative path of the directory to create. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "create_directory",
    "arguments": { "path": "new_folder/subfolder" }
  }
}
```

### delete_file
Delete a file inside the working directory.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✅ | Relative path of the file to delete. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "delete_file",
    "arguments": { "path": "temp.txt" }
  }
}
```

### delete_directory
Delete a directory, optionally forcing removal of its contents.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✅ | Relative path of the directory to delete. |
| `force` | boolean | ❌ (default: `false`) | When `true`, deletes non‑empty directories recursively. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "delete_directory",
    "arguments": { "path": "old_folder", "force": true }
  }
}
```

### search_in_file
Search for a string in a file or recursively in all files within a directory, returning contextual excerpts.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ✅ | Relative path to a file **or** directory. |
| `search_string` | string | ✅ | Text to search for. |
| `context_lines` | integer | ❌ (default: `3`) | Number of lines before and after each match to include. |
| `case_sensitive` | boolean | ❌ (default: `false`) | Perform a case‑sensitive search when `true`. |
| `max_matches` | integer | ❌ (default: `50`) | Maximum matches returned per file. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_in_file",
    "arguments": {
      "path": "log.txt",
      "search_string": "ERROR",
      "context_lines": 2,
      "case_sensitive": false,
      "max_matches": 10
    }
  }
}
```

---

### Git Operations

All git operations work on the working directory by default. To operate on a nested repository, use the `repo_path` parameter.

| Tool | Description |
|------|-------------|
| `git_status` | Show the working tree status. |
| `git_log` | Show commit log history. |
| `git_checkout` | Switch to a different branch or commit. |
| `git_branch_create` | Create a new branch. |
| `git_branch_delete` | Delete a branch. |
| `git_branch_list` | List all branches in the repository. |
| `git_add` | Add file contents to the staging area. |
| `git_commit` | Record changes to the repository. |
| `git_push` | Push changes to a remote repository. |
| `git_pull` | Fetch from and integrate with a remote repository. |
| `git_diff` | Show changes between commits, commit and working tree. |
| `git_clone` | Clone a repository into a new directory. |
| `git_submodule_add` | Add a submodule to the repository. |
| `git_submodule_update` | Update existing submodules. |
| `git_submodule_list` | List all submodules in the repository. |

**Note:** All git tools support an optional `repo_path` parameter to operate on a repository in a subdirectory (e.g., `"repo_path": "vendor/my-repo"`). When omitted, operations target the working directory directly.

### git_status
Show the working tree status.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `short` | boolean | ❌ (default: `true`) | Use short format output. |
| `repo_path` | string | ❌ | Path to repository relative to working directory (uses working directory if omitted). |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_status",
    "arguments": { 
      "short": true,
      "repo_path": "vendor/my-repo"
    }
  }
}
```

### git_log
Show commit log history.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `max_count` | integer | ❌ (default: `20`) | Maximum number of commits to show. |
| `oneline` | boolean | ❌ (default: `true`) | Show compact one-line format. |
| `repo_path` | string | ❌ | Path to repository relative to working directory (uses working directory if omitted). |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_log",
    "arguments": { 
      "max_count": 10, 
      "oneline": true,
      "repo_path": "vendor/my-repo"
    }
  }
}
```

### git_checkout
Switch to a different branch or commit.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `branch` | string | ✅ | Branch name or commit hash to checkout. |
| `repo_path` | string | ❌ | Path to repository relative to working directory (uses working directory if omitted). |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_checkout",
    "arguments": { 
      "branch": "main",
      "repo_path": "vendor/my-repo"
    }
  }
}
```

### git_branch_create
Create a new branch.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `branch` | string | ✅ | Name of the new branch. |
| `start_point` | string | ❌ | Starting point (branch or commit) for the new branch. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_branch_create",
    "arguments": { 
      "branch": "feature/new-ui",
      "start_point": "main"
    }
  }
}
```

### git_branch_delete
Delete a branch.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `branch` | string | ✅ | Name of the branch to delete. |
| `force` | boolean | ❌ (default: `false`) | Force deletion even if branch has unmerged changes. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_branch_delete",
    "arguments": { 
      "branch": "old-branch",
      "force": true
    }
  }
}
```

### git_branch_list
List all branches in the repository.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `all` | boolean | ❌ (default: `false`) | List both local and remote branches. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_branch_list",
    "arguments": { "all": true }
  }
}
```

### git_add
Add file contents to the staging area.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `paths` | array of strings | ✅ | List of file paths to add. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_add",
    "arguments": { 
      "paths": ["src/main.py", "tests/test_main.py"] 
    }
  }
}
```

### git_commit
Record changes to the repository.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message` | string | ✅ | Commit message. |
| `all` | boolean | ❌ (default: `false`) | Automatically stage all modified and deleted files. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_commit",
    "arguments": { 
      "message": "Add new feature",
      "all": true
    }
  }
}
```

### git_push
Push changes to a remote repository.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `remote` | string | ❌ (default: `origin`) | Remote repository name. |
| `branch` | string | ❌ | Branch to push (defaults to current branch). |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_push",
    "arguments": { 
      "remote": "origin",
      "branch": "main"
    }
  }
}
```

### git_pull
Fetch from and integrate with a remote repository.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `remote` | string | ❌ (default: `origin`) | Remote repository name. |
| `branch` | string | ❌ | Branch to pull (defaults to current branch). |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_pull",
    "arguments": { 
      "remote": "origin",
      "branch": "main"
    }
  }
}
```

### git_diff
Show changes between commits, commit and working tree.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | ❌ | Specific file or directory to show diff for. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_diff",
    "arguments": {
      "path": "src/main.py"
    }
  }
}
```

### git_clone
Clone a repository into a new directory.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | ✅ | URL of the repository to clone (HTTPS or SSH). |
| `path` | string | ✅ | Directory name where the repository will be cloned (relative to working directory). |
| `branch` | string | ❌ | Specific branch to checkout after cloning. |
| `recursive` | boolean | ❌ (default: `false`) | Clone submodules recursively. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_clone",
    "arguments": {
      "url": "https://github.com/owner/repo.git",
      "path": "vendor/repo",
      "branch": "main"
    }
  }
}
```

### git_submodule_add
Add a submodule to the repository.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | ✅ | URL of the repository to add as submodule. |
| `path` | string | ✅ | Path where the submodule will be placed. |
| `name` | string | ❌ | Name for the submodule (optional, defaults to path). |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_submodule_add",
    "arguments": {
      "url": "https://github.com/owner/lib.git",
      "path": "vendor/lib"
    }
  }
}
```

### git_submodule_update
Update existing submodules.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `init` | boolean | ❌ (default: `true`) | Initialize submodules before updating. |
| `recursive` | boolean | ❌ (default: `true`) | Update submodules recursively. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_submodule_update",
    "arguments": {
      "init": true,
      "recursive": true
    }
  }
}
```

### git_submodule_list
List all submodules in the repository.
**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `summary` | boolean | ❌ (default: `true`) | Show summary of submodule status. |

**Example**
```json
{
  "method": "tools/call",
  "params": {
    "name": "git_submodule_list",
    "arguments": { "summary": true }
  }
}
```

---

## 🔐 Security Features
- **Path traversal protection** – all paths are resolved against the working directory; attempts to escape result in an error.
- **Blocked extensions & sensitive filenames** – files such as `.exe`, `.bat`, `passwd`, etc., are rejected.
- **File‑size limits** – reads/writes exceeding `100 MiB` (`MAX_FILE_SIZE`) are denied.
- **Null byte and dangerous pattern checks** – prevent malformed input attacks.
- **Git command validation** – branch names and paths are validated to prevent injection attacks.

---

*© 2025 Undici77 – All rights reserved.*
