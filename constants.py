#!/usr/bin/env python3
"""Security and configuration constants for the MCP file server."""

# ----------------------------------------------------------------------
# Security Constants
# ----------------------------------------------------------------------
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB max file size
MAX_PATH_LENGTH = 4096  # Maximum path length
BLOCKED_EXTENSIONS = {'.exe', '.bat', '.cmd', '.com', '.scr', '.dll', '.so'}
SENSITIVE_FILENAMES = {'passwd', 'shadow', 'hosts', '.ssh', '.env', 'id_rsa', 'id_dsa', 'private.key'}