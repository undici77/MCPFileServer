#!/usr/bin/env python3
"""Tool handlers for git operations."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from models import MCPMessage, ContentBlock, GitResult
from gitops import GitOps

logger = logging.getLogger(__name__)


class GitHandlers:
    """Collection of git operation handlers."""

    def __init__(self, working_directory: Path):
        self.working_directory = working_directory.resolve()

    def _get_git_ops(self, repo_path: Optional[str] = None) -> GitOps:
        """Get or create the GitOps instance for a specific repository."""
        if repo_path:
            # Use relative path from working directory
            target = self.working_directory / repo_path
        else:
            target = self.working_directory
        return GitOps(target)

    def create_error_response(self, message_id: Any, code: int, message: str) -> MCPMessage:
        """Create a JSON-RPC error response."""
        from models import MCPError
        return MCPMessage(id=message_id, error=MCPError(code, message).to_dict())

    def handle_git_status(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_status tool call."""
        try:
            short = arguments.get("short", True)
            repo_path = arguments.get("repo_path")
            result = self._get_git_ops(repo_path).get_status(short=short)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            status_text = result.get("status", "")
            if result.get("error"):
                content = ContentBlock("text", f"Git status failed: {result['error']}")
            else:
                content = ContentBlock("text", f"Git Status:\n\n{status_text}" if status_text else "Git Status: No changes")
            return MCPMessage(id=message_id, result=GitResult([content]).to_dict())

        except Exception as e:
            logger.error(f"Error getting git status: {e}")
            return self.create_error_response(message_id, -32603, f"Error getting git status: {str(e)}")

    def handle_git_log(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_log tool call."""
        try:
            max_count = arguments.get("max_count", 20)
            oneline = arguments.get("oneline", True)
            repo_path = arguments.get("repo_path")

            result = self._get_git_ops(repo_path).get_log(max_count=max_count, oneline=oneline)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            commits = result.get("commits", "")
            if result.get("error"):
                content = ContentBlock("text", f"Git log failed: {result['error']}")
            else:
                content = ContentBlock("text", f"Commit Log (max {max_count} commits):\n\n{commits}" if commits else "No commits in repository")
            return MCPMessage(id=message_id, result=GitResult([content]).to_dict())

        except Exception as e:
            logger.error(f"Error getting git log: {e}")
            return self.create_error_response(message_id, -32603, f"Error getting git log: {str(e)}")

    def handle_git_checkout(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_checkout tool call."""
        try:
            branch = arguments.get("branch")
            if not branch:
                return self.create_error_response(message_id, -32602, "Missing required parameter: branch")

            repo_path = arguments.get("repo_path")
            result = self._get_git_ops(repo_path).checkout_branch(branch)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            if result.get("success"):
                content = ContentBlock("text", f"Successfully checked out branch '{branch}'")
            else:
                content = ContentBlock("text", f"Failed to checkout branch '{branch}': {result.get('error', 'Unknown error')}")
            return MCPMessage(id=message_id, result=GitResult([content], is_error=not result.get("success", False)).to_dict())

        except Exception as e:
            logger.error(f"Error checking out branch: {e}")
            return self.create_error_response(message_id, -32603, f"Error checking out branch: {str(e)}")

    def handle_git_branch_create(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_branch_create tool call."""
        try:
            branch = arguments.get("branch")
            if not branch:
                return self.create_error_response(message_id, -32602, "Missing required parameter: branch")

            repo_path = arguments.get("repo_path")
            start_point = arguments.get("start_point")
            result = self._get_git_ops(repo_path).create_branch(branch, start_point=start_point)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            if result.get("success"):
                content = ContentBlock("text", f"Successfully created branch '{branch}'")
            else:
                content = ContentBlock("text", f"Failed to create branch '{branch}': {result.get('error', 'Unknown error')}")
            return MCPMessage(id=message_id, result=GitResult([content], is_error=not result.get("success", False)).to_dict())

        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            return self.create_error_response(message_id, -32603, f"Error creating branch: {str(e)}")

    def handle_git_branch_delete(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_branch_delete tool call."""
        try:
            branch = arguments.get("branch")
            if not branch:
                return self.create_error_response(message_id, -32602, "Missing required parameter: branch")

            repo_path = arguments.get("repo_path")
            force = arguments.get("force", False)
            result = self._get_git_ops(repo_path).delete_branch(branch, force=force)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            if result.get("success"):
                content = ContentBlock("text", f"Successfully deleted branch '{branch}'")
            else:
                content = ContentBlock("text", f"Failed to delete branch '{branch}': {result.get('error', 'Unknown error')}")
            return MCPMessage(id=message_id, result=GitResult([content], is_error=not result.get("success", False)).to_dict())

        except Exception as e:
            logger.error(f"Error deleting branch: {e}")
            return self.create_error_response(message_id, -32603, f"Error deleting branch: {str(e)}")

    def handle_git_branch_list(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_branch_list tool call."""
        try:
            all_branches = arguments.get("all", False)
            repo_path = arguments.get("repo_path")

            result = self._get_git_ops(repo_path).get_branches(all=all_branches)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            branches = result.get("branches", [])
            current_branch = result.get("current_branch")

            if not branches:
                content = ContentBlock("text", "No branches found")
            else:
                branch_list = "\n".join(f"{'*' if b == current_branch else ' '} {b}" for b in branches)
                content = ContentBlock("text", f"Branches:\n\n{branch_list}")

            return MCPMessage(id=message_id, result=GitResult([content]).to_dict())

        except Exception as e:
            logger.error(f"Error listing branches: {e}")
            return self.create_error_response(message_id, -32603, f"Error listing branches: {str(e)}")

    def handle_git_add(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_add tool call."""
        try:
            paths = arguments.get("paths", [])
            if not paths:
                return self.create_error_response(message_id, -32602, "Missing required parameter: paths")

            repo_path = arguments.get("repo_path")
            result = self._get_git_ops(repo_path).add_files(paths)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            if result.get("success"):
                content = ContentBlock("text", f"Successfully added {len(paths)} file(s) to staging area")
            else:
                content = ContentBlock("text", f"Failed to add files: {result.get('error', 'Unknown error')}")
            return MCPMessage(id=message_id, result=GitResult([content], is_error=not result.get("success", False)).to_dict())

        except Exception as e:
            logger.error(f"Error adding files: {e}")
            return self.create_error_response(message_id, -32603, f"Error adding files: {str(e)}")

    def handle_git_commit(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_commit tool call."""
        try:
            message = arguments.get("message")
            if not message:
                return self.create_error_response(message_id, -32602, "Missing required parameter: message")

            repo_path = arguments.get("repo_path")
            all_files = arguments.get("all", False)
            result = self._get_git_ops(repo_path).commit(message, all=all_files)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            if result.get("success"):
                content = ContentBlock("text", f"Successfully committed: {message}")
            else:
                content = ContentBlock("text", f"Failed to commit: {result.get('error', 'Unknown error')}")
            return MCPMessage(id=message_id, result=GitResult([content], is_error=not result.get("success", False)).to_dict())

        except Exception as e:
            logger.error(f"Error committing: {e}")
            return self.create_error_response(message_id, -32603, f"Error committing: {str(e)}")

    def handle_git_push(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_push tool call."""
        try:
            remote = arguments.get("remote", "origin")
            branch = arguments.get("branch")

            repo_path = arguments.get("repo_path")
            result = self._get_git_ops(repo_path).push(remote=remote, branch=branch)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            if result.get("success"):
                content = ContentBlock("text", f"Successfully pushed to {remote}/{branch or 'current branch'}")
            else:
                content = ContentBlock("text", f"Failed to push: {result.get('error', 'Unknown error')}")
            return MCPMessage(id=message_id, result=GitResult([content], is_error=not result.get("success", False)).to_dict())

        except Exception as e:
            logger.error(f"Error pushing: {e}")
            return self.create_error_response(message_id, -32603, f"Error pushing: {str(e)}")

    def handle_git_pull(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_pull tool call."""
        try:
            remote = arguments.get("remote", "origin")
            branch = arguments.get("branch")

            repo_path = arguments.get("repo_path")
            result = self._get_git_ops(repo_path).pull(remote=remote, branch=branch)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            if result.get("success"):
                content = ContentBlock("text", f"Successfully pulled from {remote}/{branch or 'current branch'}")
            else:
                content = ContentBlock("text", f"Failed to pull: {result.get('error', 'Unknown error')}")
            return MCPMessage(id=message_id, result=GitResult([content], is_error=not result.get("success", False)).to_dict())

        except Exception as e:
            logger.error(f"Error pulling: {e}")
            return self.create_error_response(message_id, -32603, f"Error pulling: {str(e)}")

    def handle_git_diff(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_diff tool call."""
        try:
            path = arguments.get("path")

            repo_path = arguments.get("repo_path")
            result = self._get_git_ops(repo_path).diff(path=path)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            diff_content = result.get("diff", "")
            if not diff_content:
                content = ContentBlock("text", "No changes to display")
            else:
                content = ContentBlock("text", f"Diff:\n\n{diff_content}")
            return MCPMessage(id=message_id, result=GitResult([content]).to_dict())

        except Exception as e:
            logger.error(f"Error getting diff: {e}")
            return self.create_error_response(message_id, -32603, f"Error getting diff: {str(e)}")

    def handle_git_clone(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_clone tool call."""
        try:
            url = arguments.get("url")
            path = arguments.get("path")

            if not url:
                return self.create_error_response(message_id, -32602, "Missing required parameter: url")
            if not path:
                return self.create_error_response(message_id, -32602, "Missing required parameter: path")

            branch = arguments.get("branch")
            recursive = arguments.get("recursive", False)

            # security check: path should not escape working directory
            if ".." in path or path.startswith("/"):
                content = ContentBlock("text", "Invalid path: cannot contain '..' or start with '/'")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            # For clone operations, we use the working directory git_ops and pass path to clone_repo
            git_ops = GitOps(self.working_directory)
            # Bypass the repo check since we're creating a new clone
            git_ops._ensure_git_repo = lambda: True

            result = git_ops.clone_repo(url, path, branch=branch, recursive=recursive)

            if result.get("success"):
                content = ContentBlock("text", f"Successfully cloned repository to '{path}'")
            else:
                content = ContentBlock("text", f"Failed to clone repository: {result.get('error', 'Unknown error')}")
            return MCPMessage(id=message_id, result=GitResult([content], is_error=not result.get("success", False)).to_dict())

        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            return self.create_error_response(message_id, -32603, f"Error cloning repository: {str(e)}")

    def handle_git_submodule_add(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_submodule_add tool call."""
        try:
            url = arguments.get("url")
            path = arguments.get("path")

            if not url:
                return self.create_error_response(message_id, -32602, "Missing required parameter: url")
            if not path:
                return self.create_error_response(message_id, -32602, "Missing required parameter: path")

            name = arguments.get("name")

            result = self._get_git_ops().submodule_add(url, path, name=name)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            if result.get("success"):
                content = ContentBlock("text", f"Successfully added submodule '{path}'")
            else:
                content = ContentBlock("text", f"Failed to add submodule: {result.get('error', 'Unknown error')}")
            return MCPMessage(id=message_id, result=GitResult([content], is_error=not result.get("success", False)).to_dict())

        except Exception as e:
            logger.error(f"Error adding submodule: {e}")
            return self.create_error_response(message_id, -32603, f"Error adding submodule: {str(e)}")

    def handle_git_submodule_update(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_submodule_update tool call."""
        try:
            init = arguments.get("init", True)
            recursive = arguments.get("recursive", True)

            result = self._get_git_ops().submodule_update(init=init, recursive=recursive)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            if result.get("success"):
                content = ContentBlock("text", "Successfully updated submodules")
            else:
                content = ContentBlock("text", f"Failed to update submodules: {result.get('error', 'Unknown error')}")
            return MCPMessage(id=message_id, result=GitResult([content], is_error=not result.get("success", False)).to_dict())

        except Exception as e:
            logger.error(f"Error updating submodules: {e}")
            return self.create_error_response(message_id, -32603, f"Error updating submodules: {str(e)}")

    def handle_git_submodule_list(self, message_id: Any, arguments: Dict[str, Any]) -> MCPMessage:
        """Handle git_submodule_list tool call."""
        try:
            summary = arguments.get("summary", True)

            result = self._get_git_ops().submodule_list(summary=summary)

            if not result.get("is_repo", False):
                content = ContentBlock("text", "Not a git repository")
                return MCPMessage(id=message_id, result=GitResult([content], is_error=True).to_dict())

            submodules = result.get("submodules", [])
            count = result.get("count", 0)

            if not submodules:
                content = ContentBlock("text", "No submodules found in repository")
            else:
                lines = [f"Submodules ({count} total):"]
                for sm in submodules:
                    status_symbol = {"uninitialized": "?", "not cloned": "-", "modified": "+", "updated": " "}.get(sm.get("status", "?"), "?")
                    lines.append(f"  [{status_symbol}] {sm.get('path', 'unknown')} ({sm.get('sha1', '')[:8]})")
                content = ContentBlock("text", "\n".join(lines))

            return MCPMessage(id=message_id, result=GitResult([content]).to_dict())

        except Exception as e:
            logger.error(f"Error listing submodules: {e}")
            return self.create_error_response(message_id, -32603, f"Error listing submodules: {str(e)}")
