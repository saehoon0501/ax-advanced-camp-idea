"""
PermissionConfig for coding agent evals.

Design principles:
- File operations within workspace: ALLOW
- Git operations: ALLOW (coding agent needs git for commits)
- ./init.sh: ALLOW (session recovery script)
- No ASK permissions (would cause eval to hang)
- 10 minute timeout
"""

from ax_advanced_class.src.config.tool_permission_config import PermissionConfig


def create_eval_permission_config(workspace_root: str) -> PermissionConfig:
    """
    Create a PermissionConfig for coding agent eval.

    Key differences from initializer eval:
    - Git commands ALLOWED (coding agent needs to commit)
    - ./init.sh ALLOWED (session recovery script)

    Args:
        workspace_root: Absolute path to the eval workspace directory

    Returns:
        PermissionConfig configured for coding agent eval
    """
    default_blocked = {
        "cd",
        "mkfs", "fdisk", "dd", "mount", "umount",
        "shutdown", "reboot", "init", "systemctl", "service",
        "sudo", "su",
    }

    # Additional allowed commands for coding agent eval
    eval_allowed_commands = frozenset({
        # Default safe commands
        "ls", "pwd", "echo", "wc", "sort", "uniq", "diff", "file",
        "which", "whereis", "man", "help", "type", "alias",
        "env", "printenv", "date", "cal", "whoami", "id", "uname", "hostname",
        # Coding agent specific
        "chmod",
        "cat",
        "mkdir",
        "touch",
        "cp",
        "mv",
        "rm",
        "python",
        "python3",
        "pip",
        "node",
        "npm",
    })

    # Allow patterns for coding agent eval
    eval_allow_patterns = [
        # Default patterns
        "npm run *",
        "npm test*",
        "yarn *",
        "uv *",
        "python -m pytest*",
        "pytest *",
        # Coding agent specific - init.sh execution
        "./init.sh",
        "./init.sh *",
        "bash init.sh",
        "bash ./init.sh",
        "sh init.sh",
        "sh ./init.sh",
        "chmod +x init.sh*",
        "chmod +x ./init.sh*",
        "chmod * init.sh*",
        # Python execution
        "python *.py",
        "python3 *.py",
    ]

    return PermissionConfig(
        workspace_root=workspace_root,
        blocked_commands=frozenset(default_blocked),
        allowed_commands=eval_allowed_commands,
        allow_patterns=eval_allow_patterns,
    )
