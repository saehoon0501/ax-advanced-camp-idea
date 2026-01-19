"""
Configuration for permission control.

Defines the configuration and error classes for permission management.
Moved from base.py to avoid circular imports and support middleware architecture.
"""

import os
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Set


class PermissionLevel(str, Enum):
    """
    Permission levels for tool execution.

    DENY: Prevent any operation from being executed
    ALLOW: Allow specific operations to be executed
    ASK: Ask the user for permission to execute the operation (default)

    Priority: DENY > ALLOW > ASK
    """

    DENY = "deny"
    ALLOW = "allow"
    ASK = "ask"


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
    blocked_paths: List[str] = field(
        default_factory=lambda: [
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
        ]
    )

    # Always blocked commands
    blocked_commands: Set[str] = field(
        default_factory=lambda: {
            "rm -rf /",
            "rm -rf /*",
            "mkfs",
            "dd if=/dev/zero",
            ":(){ :|:& };:",  # fork bomb
            "> /dev/sda",
            "chmod -R 777 /",
            "chown -R",
        }
    )

    # Blocked command patterns (regex)
    blocked_patterns: List[str] = field(
        default_factory=lambda: [
            r"rm\s+.*-r.*",  # Block recursive removal broadly
            r"sudo\s+",  # Block sudo entirely
            r">\s*/dev/sd",  # Block writing to physical devices
            r"curl.*\|\s*bash",  # pipe curl to bash
            r"wget.*\|\s*bash",  # pipe wget to bash
            r"eval\s+\$",  # eval with variable
            r":\(\)\{\s*:\|:&",  # fork bomb
        ]
    )

    def __post_init__(self):
        # Normalize workspace root to absolute path
        self.workspace_root = os.path.abspath(os.path.expanduser(self.workspace_root))

        # Expand user paths in blocked_paths
        self.blocked_paths = [os.path.expanduser(p) for p in self.blocked_paths]
