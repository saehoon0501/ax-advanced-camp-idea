"""
Configuration for permission control.

Defines the configuration and error classes for permission management.
Supports tree-sitter based command parsing and validation.
"""

import os
from enum import Enum
from dataclasses import dataclass, field
from typing import List, FrozenSet, Set, Dict


# =============================================================================
# Hard Limits (code-enforced, cannot be bypassed)
# =============================================================================
DEFAULT_TIMEOUT_MS: int = 120_000  # 2 minutes
MAX_TIMEOUT_MS: int = 600_000  # 10 minutes (absolute max)
MAX_OUTPUT_CHARS: int = 30_000  # Output truncation limit


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
class CommandValidationResult:
    """
    Result of command validation.

    Attributes:
        level: The permission level (DENY/ALLOW/ASK)
        command: The command that was validated
        reason: Explanation for the decision
        blocked_items: List of specific items that caused DENY (if applicable)
    """

    level: PermissionLevel
    command: str
    reason: str
    blocked_items: List[str] = field(default_factory=list)


@dataclass
class PermissionConfig:
    """
    Configuration for permission control.

    Validation logic:
    1. Check DENY list → if listed, DENY
    2. Check ALLOW list → if listed, ALLOW
    3. Otherwise → ASK (default)

    Attributes:
        workspace_root: The root directory for allowed file operations
        allowed_paths: Additional paths allowed outside workspace
        blocked_paths: Paths that are always blocked (e.g., system dirs)
        blocked_commands: Command names that are DENIED
        allowed_commands: Command names that are ALLOWED
        blocked_argument_patterns: Dangerous argument combinations → DENY
        allowed_git_subcommands: Git subcommands that are ALLOWED
    """

    workspace_root: str = "./workspace"

    # Additional allowed paths (absolute paths)
    allowed_paths: List[str] = field(default_factory=list)

    # Always blocked paths → DENY
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

    # Commands that are DENIED (hard-blocked)
    # Note: File operation commands (cat, grep, find, sed, awk) are NOT blocked here.
    # They are "soft-blocked" via the prompt, which discourages their use and
    # recommends specialized file tools (Read, Grep, Glob, Edit) instead.
    blocked_commands: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {
                # System destruction / control
                "mkfs",
                "fdisk",
                "dd",
                "mount",
                "umount",
                "shutdown",
                "reboot",
                "init",
                "systemctl",
                "service",
                # Privilege escalation
                "sudo",
                "su",
            }
        )
    )

    # Commands that are ALLOWED (safe operations)
    allowed_commands: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {
                "ls",
                "pwd",
                "echo",
                "wc",
                "sort",
                "uniq",
                "diff",
                "file",
                "which",
                "whereis",
                "man",
                "help",
                "type",
                "alias",
                "env",
                "printenv",
                "date",
                "cal",
                "whoami",
                "id",
                "uname",
                "hostname",
            }
        )
    )

    # Git subcommands that are ALLOWED
    # Note: Dangerous patterns like "push --force origin main" are blocked via blocked_argument_patterns
    allowed_git_subcommands: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {
                # Read-only operations
                "status",
                "log",
                "diff",
                "show",
                "branch",
                "tag",
                "remote",
                "stash",
                # Standard workflow operations
                "add",
                "commit",
                "checkout",
                "fetch",
                "pull",
                "push",
                # Config (global changes blocked via blocked_argument_patterns)
                "config",
            }
        )
    )

    # Raw patterns blocked before parsing (exact string match)
    # These catch patterns that may not parse correctly
    blocked_raw_patterns: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {
                ":(){ :|:& };:",  # Fork bomb
                "> /dev/sda",  # Disk destruction
                "> /dev/hda",
                ">/dev/sda",
                ">/dev/hda",
            }
        )
    )

    # Blocked argument patterns: command -> set of dangerous argument combinations
    # If ANY of these patterns match → DENY
    blocked_argument_patterns: Dict[str, Set[FrozenSet[str]]] = field(
        default_factory=lambda: {
            "rm": {
                frozenset({"-rf", "/"}),
                frozenset({"-rf", "/*"}),
                frozenset({"-rf", "~"}),
                frozenset({"-r", "-f", "/"}),
                frozenset({"--recursive", "--force", "/"}),
            },
            "chmod": {
                frozenset({"-R", "777", "/"}),
                frozenset({"777", "/"}),
                frozenset({"-R", "777", "/*"}),
            },
            "chown": {
                frozenset({"-R", "/"}),
                frozenset({"-R", "/*"}),
            },
            "dd": {
                frozenset({"if=/dev/zero"}),
                frozenset({"if=/dev/random"}),
                frozenset({"of=/dev/sda"}),
                frozenset({"of=/dev/hda"}),
            },
            "curl": {
                frozenset({"|", "bash"}),
                frozenset({"|", "sh"}),
                frozenset({"|", "/bin/bash"}),
                frozenset({"|", "/bin/sh"}),
            },
            "wget": {
                frozenset({"|", "bash"}),
                frozenset({"|", "sh"}),
            },
            "git": {
                frozenset({"push", "--force", "origin", "main"}),
                frozenset({"push", "--force", "origin", "master"}),
                frozenset({"push", "-f", "origin", "main"}),
                frozenset({"push", "-f", "origin", "master"}),
                frozenset({"config", "--global"}),  # Block global config changes
            },
        }
    )

    # Commands that require TTY (will be DENIED - no TTY available)
    interactive_commands: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {
                "vim",
                "vi",
                "nano",
                "emacs",
                "less",
                "more",
                "top",
                "htop",
            }
        )
    )

    # Arguments that make commands interactive → DENY
    interactive_arguments: Dict[str, Set[FrozenSet[str]]] = field(
        default_factory=lambda: {
            "git": {frozenset({"-i"}), frozenset({"--interactive"})},
            "python": {frozenset({"-i"})},
            "node": {frozenset({"-i"})},
        }
    )

    # Pattern rules for ALLOW (command patterns with wildcards)
    # Format: "command arg_pattern" where * is wildcard
    allow_patterns: List[str] = field(
        default_factory=lambda: [
            "npm run *",
            "npm test*",
            "yarn *",
            "uv *",
            "python -m pytest*",
            "pytest *",
        ]
    )

    # Pattern rules for DENY (command patterns with wildcards)
    deny_patterns: List[str] = field(
        default_factory=lambda: [
            "curl * | bash",
            "curl * | sh",
            "wget * | bash",
            "wget * | sh",
        ]
    )

    def __post_init__(self):
        # Normalize workspace root to absolute path
        self.workspace_root = os.path.abspath(os.path.expanduser(self.workspace_root))

        # Expand user paths in blocked_paths
        self.blocked_paths = [os.path.expanduser(p) for p in self.blocked_paths]
