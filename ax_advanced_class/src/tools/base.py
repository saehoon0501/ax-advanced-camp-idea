"""
Base Permission System for Tools

Provides permission control for all shell-based operations:
- Path validation (restrict to workspace)
- Command filtering (block dangerous commands)
- Permission levels (RESTRICTED, STANDARD, ELEVATED)
"""

import os
import re
import subprocess
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Set
from pathlib import Path


class PermissionLevel(str, Enum):
    """
    Permission levels for tool execution.

    RESTRICTED: Only safe read operations
    STANDARD: Normal development operations (default)
    ELEVATED: All operations including destructive ones
    """
    RESTRICTED = "restricted"
    STANDARD = "standard"
    ELEVATED = "elevated"


class PermissionDeniedError(Exception):
    """Raised when an operation is denied due to permission restrictions."""

    def __init__(self, message: str, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Permission denied: {message}")


@dataclass
class PermissionConfig:
    """
    Configuration for permission control.

    Attributes:
        workspace_root: The root directory for allowed file operations
        permission_level: The permission level for operations
        allowed_paths: Additional paths allowed outside workspace
        blocked_paths: Paths that are always blocked (e.g., system dirs)
        blocked_commands: Shell commands that are always blocked
        blocked_patterns: Regex patterns for blocked commands
    """
    workspace_root: str = "./workspace"
    permission_level: PermissionLevel = PermissionLevel.STANDARD

    # Additional allowed paths (absolute paths)
    allowed_paths: List[str] = field(default_factory=list)

    # Always blocked paths (even with ELEVATED permission)
    blocked_paths: List[str] = field(default_factory=lambda: [
        "/etc",
        "/usr",
        "/bin",
        "/sbin",
        "/var",
        "/root",
        "/home",
        "/System",
        "/Library",
        "~/.ssh",
        "~/.aws",
        "~/.config",
    ])

    # Always blocked commands
    blocked_commands: Set[str] = field(default_factory=lambda: {
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "dd if=/dev/zero",
        ":(){ :|:& };:",  # fork bomb
        "> /dev/sda",
        "chmod -R 777 /",
        "chown -R",
    })

    # Blocked command patterns (regex)
    blocked_patterns: List[str] = field(default_factory=lambda: [
        r"rm\s+-rf\s+/(?!workspace)",  # rm -rf outside workspace
        r"sudo\s+rm",  # sudo rm
        r">\s*/dev/",  # write to devices
        r"curl.*\|\s*bash",  # pipe curl to bash
        r"wget.*\|\s*bash",  # pipe wget to bash
        r"eval\s+\$",  # eval with variable
    ])

    def __post_init__(self):
        # Normalize workspace root to absolute path
        self.workspace_root = os.path.abspath(
            os.path.expanduser(self.workspace_root)
        )

        # Expand user paths in blocked_paths
        self.blocked_paths = [
            os.path.expanduser(p) for p in self.blocked_paths
        ]


class BaseShellExecutor:
    """
    Base shell executor with permission control.

    All tool operations go through this executor for permission checks.
    """

    def __init__(self, config: Optional[PermissionConfig] = None):
        self.config = config or PermissionConfig()
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.config.blocked_patterns
        ]

    def validate_path(self, path: str) -> str:
        """
        Validate and normalize a path.

        Args:
            path: The path to validate

        Returns:
            Normalized absolute path

        Raises:
            PermissionDeniedError: If path is not allowed
        """
        # Normalize path
        normalized = os.path.abspath(os.path.expanduser(path))

        # Check blocked paths
        for blocked in self.config.blocked_paths:
            blocked_abs = os.path.abspath(blocked)
            if normalized.startswith(blocked_abs):
                raise PermissionDeniedError(
                    f"Access to {normalized} is blocked",
                    operation="path_access",
                    reason=f"Path is in blocked directory: {blocked}",
                )

        # Check if within workspace or allowed paths
        allowed_roots = [self.config.workspace_root] + [
            os.path.abspath(os.path.expanduser(p))
            for p in self.config.allowed_paths
        ]

        is_allowed = any(
            normalized.startswith(root) or normalized == root
            for root in allowed_roots
        )

        if not is_allowed:
            raise PermissionDeniedError(
                f"Path {normalized} is outside allowed directories",
                operation="path_access",
                reason=f"Allowed roots: {allowed_roots}",
            )

        return normalized

    def validate_command(self, command: str) -> None:
        """
        Validate a shell command.

        Args:
            command: The command to validate

        Raises:
            PermissionDeniedError: If command is not allowed
        """
        # Check exact blocked commands
        for blocked in self.config.blocked_commands:
            if blocked in command:
                raise PermissionDeniedError(
                    f"Command contains blocked pattern: {blocked}",
                    operation="command_execution",
                    reason="Command is in blocklist",
                )

        # Check blocked patterns
        for pattern in self._compiled_patterns:
            if pattern.search(command):
                raise PermissionDeniedError(
                    f"Command matches blocked pattern",
                    operation="command_execution",
                    reason=f"Matched pattern: {pattern.pattern}",
                )

        # Permission level checks
        if self.config.permission_level == PermissionLevel.RESTRICTED:
            self._check_restricted_command(command)

    def _check_restricted_command(self, command: str) -> None:
        """
        Additional checks for RESTRICTED permission level.

        Only allows: read operations, ls, cat, head, tail, grep, find, git status/log/diff
        """
        allowed_prefixes = [
            "ls", "cat", "head", "tail", "grep", "find", "pwd", "echo",
            "git status", "git log", "git diff", "git show", "git branch",
        ]

        is_allowed = any(
            command.strip().startswith(prefix)
            for prefix in allowed_prefixes
        )

        if not is_allowed:
            raise PermissionDeniedError(
                f"Command not allowed in RESTRICTED mode",
                operation="command_execution",
                reason=f"Only read operations allowed. Command: {command[:50]}...",
            )

    def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Execute a shell command with permission checks.

        Args:
            command: The command to execute
            cwd: Working directory (defaults to workspace_root)
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess with execution results

        Raises:
            PermissionDeniedError: If command is not allowed
            subprocess.TimeoutExpired: If command times out
        """
        # Validate command
        self.validate_command(command)

        # Validate and set working directory
        if cwd:
            cwd = self.validate_path(cwd)
        else:
            cwd = self.config.workspace_root

        # Ensure workspace exists
        os.makedirs(cwd, exist_ok=True)

        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
        )

        return result

    def execute_safe(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
    ) -> dict:
        """
        Execute a command and return a safe dict result.

        Args:
            command: The command to execute
            cwd: Working directory
            timeout: Command timeout

        Returns:
            Dict with 'success', 'stdout', 'stderr', 'returncode'
        """
        try:
            result = self.execute(command, cwd=cwd, timeout=timeout)
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except PermissionDeniedError as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Permission denied: {e}",
                "returncode": -1,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "returncode": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution error: {e}",
                "returncode": -1,
            }
