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
    default = PermissionConfig()

    # Coding agent needs many more commands allowed
    extra_allow = [
        # Coding agent specific commands
        "execute(chmod:*)",
        "execute(cat:*)",
        "execute(mkdir:*)",
        "execute(touch:*)",
        "execute(cp:*)",
        "execute(mv:*)",
        "execute(rm:*)",
        "execute(python:*)",
        "execute(python3:*)",
        "execute(pip:*)",
        "execute(node:*)",
        "execute(npm:*)",
        # Git operations
        "execute(git:*)",
        # init.sh execution
        "execute(./init.sh*)",
        "execute(bash init.sh*)",
        "execute(bash ./init.sh*)",
        "execute(sh init.sh*)",
        "execute(sh ./init.sh*)",
    ]

    return PermissionConfig(
        workspace_root=workspace_root,
        allow_rules=default.allow_rules + extra_allow,
    )
