"""
Tool Validation Middleware

Provides validation for all tool calls using LangChain's @wrap_tool_call middleware.
Intercepts shell and file commands to ensure they are safe and authorized.
"""

import os
import re
from typing import Callable, Optional

from langchain_core.messages import ToolMessage
from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command

from ax_advanced_class.src.config.tool_permission_config import (
    PermissionConfig,
    PermissionLevel,
    PermissionDeniedError,
)


def _validate_path_safety(path: str, config: PermissionConfig) -> str:
    """
    Validate and normalize a path against permission config.
    Returns normalized path or raises PermissionDeniedError.
    """
    if not path:
        return config.workspace_root

    # Normalize path
    normalized = os.path.abspath(os.path.expanduser(path))

    # Check blocked paths
    for blocked in config.blocked_paths:
        blocked_abs = os.path.abspath(blocked)
        if normalized.startswith(blocked_abs):
            raise PermissionDeniedError(
                f"Access to {normalized} is blocked",
                operation="path_access",
                reason=f"Path is in blocked directory: {blocked}",
            )

    # Check if within workspace or allowed paths
    allowed_roots = [config.workspace_root] + [os.path.abspath(os.path.expanduser(p)) for p in config.allowed_paths]

    is_allowed = any(normalized.startswith(root) or normalized == root for root in allowed_roots)

    if not is_allowed:
        raise PermissionDeniedError(
            f"Path {normalized} is outside allowed directories",
            operation="path_access",
            reason=f"Allowed roots: {allowed_roots}",
        )

    return normalized


def _validate_command_safety(command: str, config: PermissionConfig) -> None:
    """
    Validate a shell command against permission config.
    Raises PermissionDeniedError if invalid.
    """
    if not command:
        return

    # Check exact blocked commands
    for blocked in config.blocked_commands:
        if blocked in command:
            raise PermissionDeniedError(
                f"Command contains blocked pattern: {blocked}",
                operation="command_execution",
                reason="Command is in blocklist",
            )

    # Check blocked patterns
    for pattern_str in config.blocked_patterns:
        if re.search(pattern_str, command, re.IGNORECASE):
            raise PermissionDeniedError(
                f"Command matches blocked pattern",
                operation="command_execution",
                reason=f"Matched pattern: {pattern_str}",
            )

    # Check for command chaining operators if not in RESTRICTED mode (which whitelists commands)
    # In restricted mode, we only allow specific starting commands, so chained commands are effectively blocked
    # unless they are args to the allowed command (which is risky but 'ls; rm' is caught by startswith check failure usually).
    # However, for STANDARD/ELEVATED, we might want to be careful.
    # Current config doesn't explicitly block chaining, but let's add a check for dangerous chaining if needed.
    # For now, we rely on the regex patterns in config which include things like "| bash".

    # Git Specific Validations (merged from git_tool.py)
    # We apply these checks if the command looks like a git command
    if "git " in command:
        # Check force push
        if "push" in command and ("--force" in command or "-f" in command):
            # This logic assumes we want to block force push generally or check config
            # Since we merged git_tool, we assume standard config applies or we add specific checks
            # For now, let's block force push to main/master as a safe default in standard mode
            if "origin main" in command or "origin master" in command:
                raise PermissionDeniedError(
                    "Force push to protected branch is not allowed",
                    operation="git_push",
                    reason="Protected branch safety check",
                )

    # Permission level checks (RESTRICTED)
    if config.permission_level == PermissionLevel.RESTRICTED:
        allowed_prefixes = [
            "ls",
            "cat",
            "head",
            "tail",
            "grep",
            "find",
            "pwd",
            "echo",
            "git status",
            "git log",
            "git diff",
            "git show",
            "git branch",
        ]
        is_allowed = any(command.strip().startswith(prefix) for prefix in allowed_prefixes)
        if not is_allowed:
            raise PermissionDeniedError(
                f"Command not allowed in RESTRICTED mode",
                operation="command_execution",
                reason=f"Only read operations allowed. Command: {command[:50]}...",
            )


class ToolValidationMiddleware(AgentMiddleware):
    """
    Middleware for validating all tool calls (Shell, File).
    Uses a class to hold configuration state.
    """

    def __init__(self, permission_config: PermissionConfig):
        self.permission_config = permission_config

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """
        Intercepts tool calls to validate arguments before execution.
        """
        tool_name = request.tool_call["name"]
        args = request.tool_call["args"]
        tool_call_id = request.tool_call["id"]

        try:
            # --- Shell Tool Validation ---
            if tool_name in ["bash", "shell_run", "shell_script"]:
                # 1. Validate Command
                if "command" in args:
                    _validate_command_safety(args["command"], self.config)

                # 2. Validate Script Path
                if "script_path" in args:
                    _validate_path_safety(args["script_path"], self.config)

                # 3. Validate CWD
                if "cwd" in args and args["cwd"]:
                    _validate_path_safety(args["cwd"], self.config)

            # --- File Tool Validation ---
            elif tool_name in ["read", "write", "edit", "glob", "grep"]:
                if "path" in args:
                    # Resolve relative paths relative to workspace root before validation
                    path = args["path"]
                    if not os.path.isabs(path):
                        path = os.path.join(self.config.workspace_root, path)

                    # Validate the fully resolved path
                    normalized_path = _validate_path_safety(path, self.config)

                    # Update request args with safe normalized path
                    args["path"] = normalized_path

            # If validation passes, proceed to next middleware or tool call.
            return handler(request)

        except PermissionDeniedError as e:
            return ToolMessage(
                content=f"Error: Permission denied. {str(e)}",
                tool_call_id=tool_call_id,
                status="error",
            )
        except Exception as e:
            return ToolMessage(
                content=f"Error: Validation failed. {str(e)}",
                tool_call_id=tool_call_id,
                status="error",
            )
