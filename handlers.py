#!/usr/bin/env python3
"""Tool handlers for file operations."""

import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Set
import aiofiles
import base64

from models import MCPMessage, ContentBlock, ToolResult
from security import resolve_path, check_file_size
from constants import MAX_FILE_SIZE

logger = logging.getLogger(__name__)


class FileHandlers:
    """Collection of file operation handlers."""

    def __init__(self, working_directory: Path):
        self.working_directory = working_directory

    def create_error_response(self, message_id: Any, code: int, message: str) -> MCPMessage:
        """Create a JSON‑RPC error response."""
        from models import MCPError
        return MCPMessage(id=message_id, error=MCPError(code, message).to_dict())

    async def handle_read_file(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Read the contents of a file."""
        try:
            file_path = arguments.get("path")
            if not file_path:
                return self.create_error_response(message_id, -32602,
                                                  "Missing required parameter: path")

            binary_mode = arguments.get("binary", False)

            full_path = resolve_path(file_path, self.working_directory)
            if full_path is None:
                return self.create_error_response(
                    message_id, -32602, "Access denied: path outside working directory or security violation"
                )

            if not full_path.exists():
                return self.create_error_response(message_id, -32602,
                                                  f"File not found: {file_path}")

            if not full_path.is_file():
                return self.create_error_response(message_id, -32602,
                                                  f"Path is not a file: {file_path}")

            # Check file size before reading
            if not check_file_size(full_path):
                return self.create_error_response(message_id, -32602,
                                                  f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)")

            if binary_mode:
                # Read as binary data and encode in base64
                async with aiofiles.open(full_path, "rb") as f:
                    content = await f.read()
                # Encode binary data in base64
                b64_content = base64.b64encode(content).decode('ascii')
                result = ToolResult(
                    [ContentBlock("text", f"Base64-encoded binary content of {file_path} (size: {len(content)} bytes):\n\n{b64_content}")]
                )
            else:
                # Read as text (UTF-8)
                async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
                    content = await f.read()

                result = ToolResult(
                    [ContentBlock("text", f"Content of {file_path}:\n\n{content}")]
                )

            return MCPMessage(id=message_id, result=result.to_dict())

        except UnicodeDecodeError:
            if binary_mode:
                return self.create_error_response(message_id, -32602,
                                                  f"Error reading binary file: {file_path}")
            else:
                return self.create_error_response(message_id, -32602,
                                                  f"File is not valid UTF-8 text: {file_path}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return self.create_error_response(message_id, -32603,
                                              f"Error reading file: {str(e)}")

    async def handle_write_file(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Write content to a file (creating intermediate directories if needed)."""
        try:
            file_path = arguments.get("path")
            content = arguments.get("content")

            if not file_path:
                return self.create_error_response(message_id, -32602,
                                                  "Missing required parameter: path")
            if content is None:
                return self.create_error_response(message_id, -32602,
                                                  "Missing required parameter: content")

            binary_mode = arguments.get("binary", False)

            # Check content size
            if binary_mode:
                # Decode base64 to get actual byte count
                try:
                    decoded_content = base64.b64decode(content)
                    content_size = len(decoded_content)
                except Exception:
                    return self.create_error_response(message_id, -32602,
                                                      "Invalid base64 encoding for binary content")
            else:
                # Text mode - check UTF-8 encoded size
                content_size = len(content.encode('utf-8'))

            if content_size > MAX_FILE_SIZE:
                return self.create_error_response(message_id, -32602,
                                                  f"Content too large (max {MAX_FILE_SIZE // (1024*1024)}MB)")

            full_path = resolve_path(file_path, self.working_directory)
            if full_path is None:
                return self.create_error_response(
                    message_id, -32602, "Access denied: path outside working directory or security violation"
                )

            # Ensure parent directories exist.
            full_path.parent.mkdir(parents=True, exist_ok=True)

            if binary_mode:
                # Write as binary data (decode base64 first)
                try:
                    decoded_content = base64.b64decode(content)
                    async with aiofiles.open(full_path, "wb") as f:
                        await f.write(decoded_content)
                    result = ToolResult(
                        [ContentBlock("text",
                                      f"Successfully wrote {len(decoded_content)} bytes of binary data to {file_path}")]
                    )
                except Exception as e:
                    return self.create_error_response(message_id, -32602,
                                                      f"Invalid base64 encoding: {str(e)}")
            else:
                # Write as text
                async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                    await f.write(content)

                result = ToolResult(
                    [ContentBlock("text",
                                  f"Successfully wrote {len(content)} characters to {file_path}")]
                )

            return MCPMessage(id=message_id, result=result.to_dict())

        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return self.create_error_response(message_id, -32603,
                                              f"Error writing file: {str(e)}")

    def _has_matching_files(self, directory: Path, extensions: Set[str]) -> bool:
        """
        Check if a directory contains any files matching the extension filter.
        Returns True if no extension filter is specified or if matching files are found.
        """
        if not extensions:
            # No filter, check if directory has any files
            try:
                return any(p.is_file() for p in directory.rglob("*"))
            except Exception:
                return False
        
        # Check for files with matching extensions
        try:
            for p in directory.rglob("*"):
                if p.is_file() and p.suffix.lower() in extensions:
                    return True
            return False
        except Exception:
            return False

    def handle_list_files(self, message_id: Any, arguments: Dict[str, Any] = None) -> MCPMessage:
        """
        Return a newline‑separated list of files and directories under the working directory.
        
        Parameters:
        - extensions: List of file extensions to filter by (e.g., ['.py', '.txt']). 
                     If empty or None, all files are included.
        - recursive: Whether to search recursively in subdirectories (default: True)
        - show_empty_dirs: Whether to show directories that contain no matching files (default: True)
        """
        try:
            if arguments is None:
                arguments = {}
                
            # Parse arguments
            extensions = arguments.get("extensions", [])
            recursive = arguments.get("recursive", True)
            show_empty_dirs = arguments.get("show_empty_dirs", True)
            
            # Normalize extensions to lowercase and ensure they start with '.'
            if extensions:
                normalized_extensions = set()
                for ext in extensions:
                    ext = str(ext).lower()
                    if not ext.startswith('.'):
                        ext = '.' + ext
                    normalized_extensions.add(ext)
                extensions = normalized_extensions
            
            files = []
            directories = []
            empty_directories = []
            
            # Choose iteration method based on recursive flag
            if recursive:
                iterator = self.working_directory.rglob("*")
            else:
                iterator = self.working_directory.iterdir()
            
            for p in iterator:
                try:
                    rel_path = str(p.relative_to(self.working_directory))
                    
                    if p.is_file():
                        # Apply extension filter if specified
                        if extensions:
                            file_ext = p.suffix.lower()
                            if file_ext not in extensions:
                                continue
                        files.append(f"FILE: {rel_path}")
                    elif p.is_dir():
                        # For directories, check if they should be included
                        if show_empty_dirs:
                            # Always show directories if show_empty_dirs is True
                            directories.append(f"DIR:  {rel_path}")
                        else:
                            # Only show directories that contain matching files
                            if self._has_matching_files(p, extensions):
                                directories.append(f"DIR:  {rel_path}")
                            else:
                                empty_directories.append(rel_path)
                        
                except Exception as e:
                    logger.debug(f"Error processing path {p}: {e}")
                    continue
            
            # Sort results
            files.sort()
            directories.sort()
            
            # Combine results
            all_items = directories + files
            
            # Generate summary message
            summary_parts = []
            if directories:
                summary_parts.append(f"{len(directories)} directories")
            if files:
                summary_parts.append(f"{len(files)} files")
            
            # Add info about hidden empty directories
            if not show_empty_dirs and empty_directories:
                summary_parts.append(f"{len(empty_directories)} empty directories hidden")
            
            if extensions:
                ext_str = ", ".join(sorted(extensions))
                summary_parts.append(f"(filtered by extensions: {ext_str})")
            
            recursive_str = "recursively" if recursive else "non-recursively"
            summary = f"Found {', '.join(summary_parts)} {recursive_str}"
            
            if all_items:
                item_list = f"{summary}:\n\n" + "\n".join(all_items)
            else:
                item_list = f"No files or directories found {recursive_str}"
                if extensions:
                    item_list += f" with extensions {', '.join(sorted(extensions))}"

            result = ToolResult([ContentBlock("text", item_list)])
            return MCPMessage(id=message_id, result=result.to_dict())

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return self.create_error_response(message_id, -32603,
                                              f"Error listing files: {str(e)}")

    def handle_create_directory(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Create a new directory (including intermediate directories)."""
        try:
            dir_path = arguments.get("path")
            if not dir_path:
                return self.create_error_response(message_id, -32602,
                                                  "Missing required parameter: path")

            full_path = resolve_path(dir_path, self.working_directory)
            if full_path is None:
                return self.create_error_response(
                    message_id, -32602, "Access denied: path outside working directory or security violation"
                )

            full_path.mkdir(parents=True, exist_ok=True)

            result = ToolResult([ContentBlock("text",
                                              f"Directory created successfully: {dir_path}")])
            return MCPMessage(id=message_id, result=result.to_dict())

        except Exception as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
            return self.create_error_response(message_id, -32603,
                                              f"Error creating directory: {str(e)}")

    async def handle_delete_file(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Delete a file."""
        try:
            target_path = arguments.get("path")
            if not target_path:
                return self.create_error_response(message_id, -32602,
                                                  "Missing required parameter: path")

            full_path = resolve_path(target_path, self.working_directory)
            if full_path is None:
                return self.create_error_response(
                    message_id, -32602, "Access denied: path outside working directory or security violation"
                )

            if not full_path.exists():
                return self.create_error_response(message_id, -32602,
                                                  f"File not found: {target_path}")

            if not full_path.is_file():
                return self.create_error_response(message_id, -32602,
                                                  f"Path is not a file: {target_path}")

            full_path.unlink()
            result = ToolResult([ContentBlock("text", f"File deleted successfully: {target_path}")])
            return MCPMessage(id=message_id, result=result.to_dict())

        except Exception as e:
            logger.error(f"Error deleting file {target_path}: {e}")
            return self.create_error_response(message_id, -32603,
                                              f"Error deleting file: {str(e)}")

    async def handle_delete_directory(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Delete a directory and optionally all its contents."""
        try:
            target_path = arguments.get("path")
            force = arguments.get("force", False)
            
            if not target_path:
                return self.create_error_response(message_id, -32602,
                                                  "Missing required parameter: path")

            full_path = resolve_path(target_path, self.working_directory)
            if full_path is None:
                return self.create_error_response(
                    message_id, -32602, "Access denied: path outside working directory or security violation"
                )

            if not full_path.exists():
                return self.create_error_response(message_id, -32602,
                                                  f"Directory not found: {target_path}")

            if not full_path.is_dir():
                return self.create_error_response(message_id, -32602,
                                                  f"Path is not a directory: {target_path}")

            # Prevent deletion of the working directory itself
            if full_path == self.working_directory:
                return self.create_error_response(message_id, -32602,
                                                  "Cannot delete the working directory itself")

            if force:
                # Delete directory and all contents
                shutil.rmtree(full_path)
                msg = f"Directory and all contents deleted successfully: {target_path}"
            else:
                # Only delete if empty
                try:
                    full_path.rmdir()  # only works on empty directories
                    msg = f"Empty directory deleted successfully: {target_path}"
                except OSError:
                    return self.create_error_response(message_id, -32602,
                                                      f"Directory not empty (use force=true to delete contents): {target_path}")

            result = ToolResult([ContentBlock("text", msg)])
            return MCPMessage(id=message_id, result=result.to_dict())

        except Exception as e:
            logger.error(f"Error deleting directory {target_path}: {e}")
            return self.create_error_response(message_id, -32603,
                                              f"Error deleting directory: {str(e)}")

    async def handle_search_in_file(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Search for a string in a file or all files in a directory and return excerpts around each match.
        If path is a directory, search recursively in all files within the directory."""
        try:
            file_path = arguments.get("path")
            search_string = arguments.get("search_string")
            context_lines = arguments.get("context_lines", 3)
            case_sensitive = arguments.get("case_sensitive", False)
            max_matches = arguments.get("max_matches", 50)

            # Validate parameters
            if not file_path:
                return self.create_error_response(message_id, -32602,
                                                  "Missing required parameter: path")
            if not search_string:
                return self.create_error_response(message_id, -32602,
                                                  "Missing required parameter: search_string")
            
            if context_lines < 0:
                context_lines = 0
            if max_matches < 1:
                max_matches = 1

            # Resolve and validate path
            full_path = resolve_path(file_path, self.working_directory)
            if full_path is None:
                return self.create_error_response(
                    message_id, -32602, "Access denied: path outside working directory or security violation"
                )

            if not full_path.exists():
                return self.create_error_response(message_id, -32602,
                                                  f"Path not found: {file_path}")

            # Check if path is a directory or file
            results = []
            total_matches = 0
            
            if full_path.is_dir():
                # Search in all files within the directory recursively
                search_pattern = f"**/*"
                # Get all files in the directory (recursively)
                for file in full_path.rglob(search_pattern):
                    if not file.is_file():
                        continue
                    
                    # Check file size before reading
                    if not check_file_size(file):
                        results.append(f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB): {file.relative_to(self.working_directory)}")
                        continue
                    
                    try:
                        # Read file content
                        async with aiofiles.open(file, "r", encoding="utf-8") as f:
                            content = await f.read()
                    except UnicodeDecodeError:
                        results.append(f"File is not valid UTF-8 text: {file.relative_to(self.working_directory)}")
                        continue
                    except Exception as e:
                        results.append(f"Error reading file {file.relative_to(self.working_directory)}: {str(e)}")
                        continue
                    
                    lines = content.splitlines()
                    search_str = search_string if case_sensitive else search_string.lower()
                    matches_in_file = []
                    
                    # Find all matching lines in this file
                    for line_num, line in enumerate(lines, start=1):
                        compare_line = line if case_sensitive else line.lower()
                        if search_str in compare_line:
                            matches_in_file.append(line_num)
                            if len(matches_in_file) >= max_matches:
                                break
                    
                    if matches_in_file:
                        total_matches += len(matches_in_file)
                        # Build excerpts with context
                        excerpts = []
                        for idx, line_num in enumerate(matches_in_file[:max_matches], start=1):
                            # Calculate context window
                            start_line = max(1, line_num - context_lines)
                            end_line = min(len(lines), line_num + context_lines)
                            
                            # Extract lines with context
                            excerpt_lines = []
                            for i in range(start_line - 1, end_line):
                                prefix = ">>> " if (i + 1) == line_num else "    "
                                excerpt_lines.append(f"{prefix}{i + 1:4d} | {lines[i]}")
                            
                            excerpt = "\n".join(excerpt_lines)
                            excerpts.append(f"Match {idx} at line {line_num}:\n{excerpt}")
                        
                        # Combine excerpts for this file
                        separator = "\n" + "=" * 60 + "\n\n"
                        file_results = (
                            f"Found {len(matches_in_file)} match(es) for '{search_string}' in {file.relative_to(self.working_directory)}\n"
                            f"(showing {len(excerpts)} match(es) with {context_lines} lines of context)\n\n"
                            + separator.join(excerpts)
                        )
                        
                        if len(matches_in_file) > len(excerpts):
                            file_results += f"\n\n(Showing first {len(excerpts)} of {len(matches_in_file)} matches)"
                        
                        results.append(file_results)
            else:
                # Original behavior for files
                if not full_path.is_file():
                    return self.create_error_response(message_id, -32602,
                                                      f"Path is not a file or directory: {file_path}")

                # Check file size before reading
                if not check_file_size(full_path):
                    return self.create_error_response(message_id, -32602,
                                                      f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)")

                # Read file content
                async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
                    content = await f.read()

                lines = content.splitlines()
                
                # Prepare search string based on case sensitivity
                search_str = search_string if case_sensitive else search_string.lower()
                
                # Find all matching lines
                matches = []
                for line_num, line in enumerate(lines, start=1):
                    compare_line = line if case_sensitive else line.lower()
                    if search_str in compare_line:
                        matches.append(line_num)
                        if len(matches) >= max_matches:
                            break
                
                # Build result
                if not matches:
                    result_text = f"No matches found for '{search_string}' in {file_path}"
                    result = ToolResult([ContentBlock("text", result_text)])
                    return MCPMessage(id=message_id, result=result.to_dict())
                
                # Build excerpts with context
                excerpts = []
                total_matches = len(matches)
                
                for idx, line_num in enumerate(matches, start=1):
                    # Calculate context window
                    start_line = max(1, line_num - context_lines)
                    end_line = min(len(lines), line_num + context_lines)
                    
                    # Extract lines with context
                    excerpt_lines = []
                    for i in range(start_line - 1, end_line):
                        prefix = ">>> " if (i + 1) == line_num else "    "
                        excerpt_lines.append(f"{prefix}{i + 1:4d} | {lines[i]}")
                    
                    excerpt = "\n".join(excerpt_lines)
                    excerpts.append(f"Match {idx} at line {line_num}:\n{excerpt}")
                
                # Combine all excerpts
                separator = "\n" + "=" * 60 + "\n\n"
                result_text = (
                    f"Found {total_matches} match(es) for '{search_string}' in {file_path}\n"
                    f"(showing {len(excerpts)} match(es) with {context_lines} lines of context)\n\n"
                    + separator.join(excerpts)
                )
                
                if total_matches > len(excerpts):
                    result_text += f"\n\n(Showing first {len(excerpts)} of {total_matches} matches)"
                
                result = ToolResult([ContentBlock("text", result_text)])
                return MCPMessage(id=message_id, result=result.to_dict())

            # Handle directory search results
            if not results:
                result_text = f"No matches found for '{search_string}' in any files within {file_path}"
                result = ToolResult([ContentBlock("text", result_text)])
                return MCPMessage(id=message_id, result=result.to_dict())
            
            # Combine all results
            separator = "\n" + "=" * 80 + "\n\n"
            result_text = (
                f"Search results for '{search_string}' in directory: {file_path}\n"
                f"Total matches found: {total_matches}\n\n"
                + separator.join(results)
            )
            
            result = ToolResult([ContentBlock("text", result_text)])
            return MCPMessage(id=message_id, result=result.to_dict())

        except UnicodeDecodeError:
            return self.create_error_response(message_id, -32602,
                                              f"File is not valid UTF-8 text: {file_path}")
        except Exception as e:
            logger.error(f"Error searching in path {file_path}: {e}")
            return self.create_error_response(message_id, -32603,
                                              f"Error searching in path: {str(e)}")