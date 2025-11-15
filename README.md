# 📂 MCP File Server

**MCP File Server** is a secure, sandboxed file server providing controlled access to filesystem operations via the **Model Control Protocol (MCP)**. It supports reading, writing, listing, creating, and deleting files and directories within a configurable working directory while enforcing strict security checks.

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
  - [read_file](#read_file)
  - [write_file](#write_file)
  - [list_files](#list_files)
  - [create_directory](#create_directory)
  - [delete_file](#delete_file)
  - [delete_directory](#delete_directory)
  - [search_in_file](#search_in_file)
- [Security Features](#security-features)

## 🎯 Features
- **Sandboxed operations** – all paths are confined to a user‑specified working directory.
- **Path traversal protection**, file‑size limits, and blocked extensions.
- Binary support via Base64 encoding for safe transport of non‑text data.
- Simple line‑delimited JSON‑RPC protocol suitable for stdin/stdout integration.
- Ready‑to‑use with **LM Studio** through a minimal `mcp.json` configuration.

## 📦 Installation & Quick Start
```bash
# Clone the repository (if not already done)
git clone https://github.com/undici77/MCPFileServer.git
cd MCPFileServer

# Run the startup script – it creates a virtual environment,
# installs dependencies, and starts the server.
./run.sh -d /path/to/working/directory
```
The script will:
- Verify that Python 3 is available.
- Create a `.venv` virtual environment (if missing).
- Install required packages (`aiofiles`).
- Start `main.py` with the supplied working directory.

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
| Tool | Description |
|------|-------------|
| `read_file` | Read a file’s contents (text or binary). |
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
The response lists entries prefixed with `DIR:` or `FILE:` and includes a summary line.

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
The response contains formatted excerpts with line numbers and a summary of total matches.

---

## 🔐 Security Features
- **Path traversal protection** – all paths are resolved against the working directory; attempts to escape result in an error.
- **Blocked extensions & sensitive filenames** – files such as `.exe`, `.bat`, `passwd`, etc., are rejected.
- **File‑size limits** – reads/writes exceeding `100 MiB` (`MAX_FILE_SIZE`) are denied.
- **Null byte and dangerous pattern checks** – prevent malformed input attacks.

---

*© 2025 Undici77 – All rights reserved.*