#!/usr/bin/env python3
"""Security validation utilities for path and file operations."""

from pathlib import Path
from typing import Optional
import logging

from constants import (
    MAX_FILE_SIZE,
    MAX_PATH_LENGTH,
    BLOCKED_EXTENSIONS,
    SENSITIVE_FILENAMES,
)

logger = logging.getLogger(__name__)


def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe (no sensitive files or dangerous extensions)."""
    filename_lower = filename.lower()
    
    # Check for sensitive filenames
    if any(sensitive in filename_lower for sensitive in SENSITIVE_FILENAMES):
        return False
        
    # Check for blocked extensions
    file_ext = Path(filename).suffix.lower()
    if file_ext in BLOCKED_EXTENSIONS:
        return False
        
    # Check for path traversal attempts in filename itself
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        return False
        
    return True


def validate_path_security(file_path: str) -> Optional[str]:
    """Validate path for security issues. Returns error message if unsafe, None if safe."""
    # Check path length
    if len(file_path) > MAX_PATH_LENGTH:
        return f"Path too long (max {MAX_PATH_LENGTH} characters)"
    
    # Check for null bytes
    if '\0' in file_path:
        return "Invalid null byte in path"
    
    # Check for dangerous patterns
    dangerous_patterns = ['../', '..\\', '/./', '\\.\\']
    for pattern in dangerous_patterns:
        if pattern in file_path:
            return f"Dangerous path pattern detected: {pattern}"
    
    # Check individual path components
    try:
        path_obj = Path(file_path)
        for part in path_obj.parts:
            if not is_safe_filename(part):
                return f"Unsafe filename component: {part}"
    except Exception:
        return "Invalid path format"
    
    return None


def resolve_path(file_path: str, working_directory: Path) -> Optional[Path]:
    """
    Resolve file_path relative to the working directory and verify that the result
    stays inside the sandbox.

    Returns the absolute resolved path if safe, otherwise None.
    """
    try:
        # First validate path security
        security_error = validate_path_security(file_path)
        if security_error:
            logger.warning(f"Path security validation failed for '{file_path}': {security_error}")
            return None

        # Accept both relative and absolute user input.
        p = Path(file_path)

        # If an absolute path is given (e.g. "/etc/passwd"), strip the leading slash
        # so that it becomes a *relative* path inside the sandbox.
        if p.is_absolute():
            p = p.relative_to(p.anchor)   # removes root component

        full_path = (working_directory / p).resolve()

        # Ensure the resolved path is still within the working directory
        if full_path.is_relative_to(working_directory):
            return full_path
        else:
            logger.warning(f"Path '{file_path}' resolves outside working directory")
            
    except Exception as exc:
        logger.debug(f"Path resolution error for '{file_path}': {exc}")

    # Anything that raises or falls outside the sandbox is unsafe.
    return None


def check_file_size(file_path: Path) -> bool:
    """Check if file size is within allowed limits."""
    try:
        if file_path.exists() and file_path.is_file():
            size = file_path.stat().st_size
            return size <= MAX_FILE_SIZE
    except Exception as e:
        logger.debug(f"Error checking file size for {file_path}: {e}")
    return True  # If we can't check, allow the operation