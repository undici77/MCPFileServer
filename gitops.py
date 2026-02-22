#!/usr/bin/env python3
"""Git operations for the MCP file server."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class GitOps:
    """Wrapper for git operations within a working directory."""

    def __init__(self, work_dir: Path):
        self.work_dir = work_dir.resolve()
        git_path = shutil.which("git")
        if not git_path:
            raise RuntimeError("Git is not installed or not in PATH")
        self._git_executable = git_path
        self._ensure_git_repo()

    def _run_git(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command in the working directory."""
        cmd = [self._git_executable] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if check and result.returncode != 0:
                logger.error(f"Git command failed: {' '.join(cmd)}")
                logger.error(f"stderr: {result.stderr}")
            return result
        except FileNotFoundError:
            raise RuntimeError("Git is not installed or not in PATH")
        except Exception as e:
            logger.error(f"Error running git command: {e}")
            raise

    def _ensure_git_repo(self) -> bool:
        """Check if the working directory is a git repository."""
        result = self._run_git(["rev-parse", "--git-dir"], check=False)
        if result.returncode != 0:
            logger.warning(f"Directory {self.work_dir} is not a git repository")
            return False
        return True

    def is_repo(self) -> bool:
        """Return whether the working directory is a git repository."""
        return self._run_git(["rev-parse", "--git-dir"], check=False).returncode == 0

    def get_status(self, short: bool = True) -> Dict[str, Any]:
        """Get git status."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        args = ["status"]
        if short:
            args.append("--short")

        result = self._run_git(args)
        return {
            "is_repo": True,
            "status": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def get_log(self, max_count: int = 20, oneline: bool = True) -> Dict[str, Any]:
        """Get git commit log."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        args = ["log"]
        if oneline:
            args.append("--oneline")
        args.extend(["-n", str(max_count)])

        result = self._run_git(args)
        return {
            "is_repo": True,
            "commits": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def get_current_branch(self) -> Dict[str, Any]:
        """Get the current branch name."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False, "branch": None}

        result = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        branch = result.stdout.strip() if result.stdout else None
        return {
            "is_repo": True,
            "branch": branch,
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def checkout_branch(self, branch: str) -> Dict[str, Any]:
        """Checkout a branch."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        result = self._run_git(["checkout", branch])
        return {
            "is_repo": True,
            "success": result.returncode == 0,
            "message": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def create_branch(self, branch: str, start_point: Optional[str] = None) -> Dict[str, Any]:
        """Create a new branch."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        args = ["branch", branch]
        if start_point:
            args.append(start_point)

        result = self._run_git(args)
        return {
            "is_repo": True,
            "success": result.returncode == 0,
            "message": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def delete_branch(self, branch: str, force: bool = False) -> Dict[str, Any]:
        """Delete a branch."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        args = ["branch", "-d" if not force else "-D", branch]
        result = self._run_git(args)
        return {
            "is_repo": True,
            "success": result.returncode == 0,
            "message": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def get_branches(self, all: bool = False) -> Dict[str, Any]:
        """List branches."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        args = ["branch"]
        if all:
            args.append("-a")

        result = self._run_git(args)
        branches = []
        for line in result.stdout.strip().split("\n"):
            if line:
                # Remove current branch marker (*)
                branch = line.strip().lstrip("* ").lstrip()
                branches.append(branch)

        return {
            "is_repo": True,
            "branches": branches,
            "current_branch": self.get_current_branch()["branch"],
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def add_files(self, paths: List[str]) -> Dict[str, Any]:
        """Add files to staging area."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        if not paths:
            return {"error": "No files specified", "is_repo": True, "success": False}

        result = self._run_git(["add"] + paths)
        return {
            "is_repo": True,
            "success": result.returncode == 0,
            "message": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def commit(self, message: str, all: bool = False) -> Dict[str, Any]:
        """Create a commit."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        args = ["commit", "-m", message]
        if all:
            args.append("-a")

        result = self._run_git(args)
        return {
            "is_repo": True,
            "success": result.returncode == 0,
            "message": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def push(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """Push to remote repository."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        if branch is None:
            branch_result = self.get_current_branch()
            branch = branch_result.get("branch")
            if not branch:
                return {"error": "Could not determine current branch", "is_repo": True, "success": False}

        result = self._run_git(["push", remote, branch])
        return {
            "is_repo": True,
            "success": result.returncode == 0,
            "message": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """Pull from remote repository."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        if branch is None:
            branch_result = self.get_current_branch()
            branch = branch_result.get("branch")
            if not branch:
                return {"error": "Could not determine current branch", "is_repo": True, "success": False}

        result = self._run_git(["pull", remote, branch])
        return {
            "is_repo": True,
            "success": result.returncode == 0,
            "message": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def diff(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Show changes."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        args = ["diff"]
        if path:
            args.append(path)

        result = self._run_git(args)
        return {
            "is_repo": True,
            "diff": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def show_file(self, path: str, ref: Optional[str] = None) -> Dict[str, Any]:
        """Show file contents at a specific reference."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}

        args = ["show"]
        if ref:
            args.append(f"{ref}:{path}")
        else:
            args.append(path)

        result = self._run_git(args)
        return {
            "is_repo": True,
            "content": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def clone_repo(self, url: str, path: str, branch: Optional[str] = None, recursive: bool = False) -> Dict[str, Any]:
        """Clone a repository into a new directory."""
        # Build clone command
        args = ["clone"]
        
        if branch:
            args.extend(["--branch", branch])
        
        if recursive:
            args.append("--recursive")
        
        args.extend([url, str(path)])
        
        result = self._run_git(args)
        
        # The clone command runs in the working directory context
        # so path is relative to self.work_dir
        full_path = self.work_dir / path
        
        return {
            "success": result.returncode == 0,
            "message": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode,
            "cloned_path": str(full_path),
            "is_repo": result.returncode == 0 and (full_path / ".git").exists()
        }

    def submodule_add(self, url: str, path: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Add a submodule to the repository."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}
        
        args = ["submodule", "add"]
        
        if name:
            args.extend(["--name", name])
        
        args.extend([url, path])
        
        result = self._run_git(args)
        
        return {
            "is_repo": True,
            "success": result.returncode == 0,
            "message": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def submodule_update(self, init: bool = True, recursive: bool = True) -> Dict[str, Any]:
        """Update existing submodules."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}
        
        args = ["submodule", "update"]
        
        if init:
            args.append("--init")
        
        if recursive:
            args.append("--recursive")
        
        result = self._run_git(args)
        
        return {
            "is_repo": True,
            "success": result.returncode == 0,
            "message": result.stdout.strip() if result.stdout else "",
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }

    def submodule_list(self, summary: bool = True) -> Dict[str, Any]:
        """List all submodules in the repository."""
        if not self.is_repo():
            return {"error": "Not a git repository", "is_repo": False}
        
        args = ["submodule", "status"]
        if not summary:
            args.append("--recursive")
        
        result = self._run_git(args)
        
        submodules = []
        for line in result.stdout.strip().split("\n"):
            if line:
                # Parse submodule status output
                # Format: <status><sha1> <path>(<branch>) <message>
                parts = line.split(None, 3)
                if len(parts) >= 2:
                    status_char = parts[0][0] if parts[0] else " "
                    sha1 = parts[0][1:] if len(parts[0]) > 1 else ""
                    submodule_path = parts[1] if len(parts) > 1 else ""
                    submodule_name = parts[2] if len(parts) > 2 else ""
                    
                    status_map = {
                        " ": "uninitialized",
                        "-": "not cloned",
                        "+": "modified",
                        "U": "updated"
                    }
                    
                    submodules.append({
                        "status": status_map.get(status_char, "unknown"),
                        "sha1": sha1,
                        "path": submodule_path,
                        "name": submodule_name
                    })
        
        return {
            "is_repo": True,
            "submodules": submodules,
            "count": len(submodules),
            "error": result.stderr.strip() if result.stderr and result.returncode != 0 else None,
            "returncode": result.returncode
        }
