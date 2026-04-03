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
    - git commands added to deny_rules (DENY instead of ASK)
    - This ensures no interrupt() calls during testing

    Args:
        workspace_root: Absolute path to the test workspace directory

    Returns:
        PermissionConfig configured for eval
    """
    default = PermissionConfig()

    # Add git to deny rules (DENY instead of ASK during tests)
    extra_deny = ["execute(git:*)"]

    return PermissionConfig(
        workspace_root=workspace_root,
        deny_rules=default.deny_rules + extra_deny,
    )
