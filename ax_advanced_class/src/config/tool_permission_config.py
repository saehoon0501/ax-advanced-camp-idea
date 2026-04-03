"""
Configuration for permission control.

Defines the configuration and error classes for permission management.
Supports tree-sitter based command parsing and validation.
"""

import fnmatch as _fnmatch
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
class PermissionRule:
    """
    A permission rule following Claude Code's Tool(pattern) format.

    Supports:
    - Wildcard: "*" matches everything
    - Prefix:   "npm:*" matches commands starting with "npm"
    - Glob:     "npm run *" matches via fnmatch
    - Exact:    "npm test" matches only "npm test"
    """

    tool_name: str
    pattern: str

    @staticmethod
    def parse(rule_str: str) -> "PermissionRule":
        """Parse 'execute(npm:*)' → PermissionRule(tool_name='execute', pattern='npm:*')"""
        if "(" in rule_str and rule_str.endswith(")"):
            paren_idx = rule_str.index("(")
            tool_name = rule_str[:paren_idx]
            pattern = rule_str[paren_idx + 1 : -1]
        else:
            tool_name = rule_str
            pattern = "*"
        return PermissionRule(tool_name=tool_name, pattern=pattern)

    def matches(self, tool_name: str, content: str) -> bool:
        """Check if this rule matches a tool call."""
        if self.tool_name != tool_name:
            return False
        if self.pattern == "*":
            return True
        if self.pattern.endswith(":*"):
            prefix = self.pattern[:-2]
            return content == prefix or content.startswith(prefix + " ") or content.startswith(prefix + "/")
        if "*" in self.pattern:
            return _fnmatch.fnmatch(content, self.pattern)
        return content == self.pattern

    def __str__(self) -> str:
        return f"{self.tool_name}({self.pattern})"


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
        deny_rules: PermissionRule strings for commands that are DENIED
        allow_rules: PermissionRule strings for commands that are ALLOWED
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

    # Deny rules: commands that are hard-blocked.
    # Format: "execute(command:*)" for prefix match, "execute(pattern *)" for glob.
    deny_rules: List[str] = field(
        default_factory=lambda: [
            "execute(cd:*)",
            # System destruction / control
            "execute(mkfs:*)",
            "execute(fdisk:*)",
            "execute(dd:*)",
            "execute(mount:*)",
            "execute(umount:*)",
            "execute(shutdown:*)",
            "execute(reboot:*)",
            "execute(init:*)",
            "execute(systemctl:*)",
            "execute(service:*)",
            # Privilege escalation
            "execute(sudo:*)",
            "execute(su:*)",
            # Dangerous piped commands
            "execute(curl * | bash)",
            "execute(curl * | sh)",
            "execute(curl * | /bin/bash)",
            "execute(curl * | /bin/sh)",
            "execute(wget * | bash)",
            "execute(wget * | sh)",
        ]
    )

    # Allow rules: commands that are safe to run without prompting.
    # Format: "execute(command:*)" for prefix match, "execute(pattern *)" for glob.
    allow_rules: List[str] = field(
        default_factory=lambda: [
            "execute(ls:*)",
            "execute(pwd:*)",
            "execute(echo:*)",
            "execute(wc:*)",
            "execute(sort:*)",
            "execute(uniq:*)",
            "execute(diff:*)",
            "execute(file:*)",
            "execute(which:*)",
            "execute(whereis:*)",
            "execute(man:*)",
            "execute(help:*)",
            "execute(type:*)",
            "execute(alias:*)",
            "execute(env:*)",
            "execute(printenv:*)",
            "execute(date:*)",
            "execute(cal:*)",
            "execute(whoami:*)",
            "execute(id:*)",
            "execute(uname:*)",
            "execute(hostname:*)",
            # Pattern-based allow rules
            "execute(npm run *)",
            "execute(npm test*)",
            "execute(yarn *)",
            "execute(uv *)",
            "execute(python -m pytest*)",
            "execute(pytest *)",
        ]
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

    def __post_init__(self):
        # Normalize workspace root to absolute path
        self.workspace_root = os.path.abspath(os.path.expanduser(self.workspace_root))

        # Expand user paths in blocked_paths
        self.blocked_paths = [os.path.expanduser(p) for p in self.blocked_paths]
