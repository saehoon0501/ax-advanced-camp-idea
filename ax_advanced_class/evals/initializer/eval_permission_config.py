"""
Test-specific PermissionConfig for initializer agent evals.

Design principles:
- File operations within workspace: ALLOW
- Git operations: DENY (no interrupt, just error message)
- No ASK permissions (would cause test to hang)
"""

from ax_advanced_class.src.config.tool_permission_config import PermissionConfig


def create_eval_permission_config(workspace_root: str) -> PermissionConfig:
    """
    Create a PermissionConfig suitable for automated testing.

    Key differences from default config:
    - workspace_root set to test workspace
    - git commands added to blocked_commands (DENY instead of ASK)
    - This ensures no interrupt() calls during testing

    Args:
        workspace_root: Absolute path to the test workspace directory

    Returns:
        PermissionConfig configured for eval
    """
    # Start with default blocked commands
    default_blocked = {
        "cd",
        "mkfs", "fdisk", "dd", "mount", "umount",
        "shutdown", "reboot", "init", "systemctl", "service",
        "sudo", "su",
    }

    # Add git commands to blocked list (DENY instead of ASK)
    # This prevents interrupt() from being called during tests
    git_commands_to_block = {
        "git",  # Block all git commands
    }

    blocked_commands = frozenset(default_blocked | git_commands_to_block)

    return PermissionConfig(
        workspace_root=workspace_root,
        blocked_commands=blocked_commands,
    )
