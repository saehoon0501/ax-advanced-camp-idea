"""
Tool Validation Middleware

Provides validation for all tool calls using LangChain's @wrap_tool_call middleware.
Uses tree-sitter-bash for robust command parsing and security validation.

Learning objectives:
- Understand the DENY -> ALLOW -> ASK 3-stage validation pattern
- Implement path-based permission validation
- Implement user confirmation flow using interrupt()
- Ensure file safety with the Read-before-write pattern
"""

import os
from typing import Callable, List

from langchain_core.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.errors import GraphInterrupt
from langgraph.types import Command, interrupt

from ax_advanced_class.src.config.tool_permission_config import (
    PermissionLevel,
    PermissionConfig,
    PermissionRule,
    CommandValidationResult,
)
from ax_advanced_class.src.middleware._internals.tool_validation_helpers import (
    _BashValidatorBase,
    ToolValidationMiddlewareBase,
    _BASH_TOOL_NAMES,
    _FILE_TOOL_NAMES,
    _WRITE_FILE_TOOLS,
)


class _BashValidator(_BashValidatorBase):
    """
    Bash command & path validator.

    validate_command: Validates a command string and returns DENY/ALLOW/ASK
    validate_path: Validates a file path and returns DENY/ALLOW/ASK

    Hint: The parent class (_BashValidatorBase) has the following helpers:
    - self.config: PermissionConfig (blocked_raw_patterns, blocked_paths, allowed_paths, etc.)
    - self._parser: BashParser (parses commands via the parse method)
    - self._check_rules(command): deny/allow rule matching
    - self._validate_parsed_command(parsed): individual parsed command validation
    - self._get_highest_priority_result(results, command): returns the highest priority result
    """

    def validate_command(self, command: str) -> CommandValidationResult:
        """
        Validates a shell command.

        Returns:
            CommandValidationResult - DENY, ALLOW, or ASK
        """
        # TODO 1: DENY -> ALLOW -> ASK 3-stage validation
        #
        # Step 1: Empty command -> ALLOW (return CommandValidationResult)
        # Step 2: Iterate through self.config.blocked_raw_patterns -> DENY if matched
        #         (include matched pattern in blocked_items)
        # Step 3: self._check_rules(command) -> return the result if any
        # Step 4: self._parser.parse(command) -> DENY if parsing fails (empty list)
        #         (reason: "Could not parse command structure")
        # Step 5: Call self._validate_parsed_command() for each parsed command
        #         -> return immediately if DENY, otherwise add to results list
        # Step 6: self._get_highest_priority_result(results, command)
        return CommandValidationResult(level=PermissionLevel.ASK, command=command, reason="")

    def validate_path(self, path: str, is_write: bool = True) -> CommandValidationResult:
        """
        Validates a file path.

        Args:
            path: The file path to validate
            is_write: True for write operations, False for read operations

        Returns:
            CommandValidationResult - DENY, ALLOW, or ASK
        """
        # Step 1: Empty path -> ALLOW
        if not path:
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=path,
                reason="Empty path defaults to workspace",
            )

        # Step 2: Normalize path -- prevents symlink bypass attacks
        normalized = os.path.abspath(os.path.expanduser(path))

        # Step 3: Check blocked paths -> DENY (regardless of read/write)
        for blocked in self.config.blocked_paths:
            blocked_abs = os.path.abspath(blocked)
            if normalized.startswith(blocked_abs):
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=path,
                    reason=f"Path is in blocked directory: {blocked}",
                    blocked_items=[blocked],
                )

        # Step 4: Check workspace + allowed paths -> ALLOW
        allowed_roots = [self.config.workspace_root] + self.config.allowed_paths
        for allowed in allowed_roots:
            allowed_abs = os.path.abspath(os.path.expanduser(allowed))
            if normalized == allowed_abs or normalized.startswith(allowed_abs + os.sep):
                return CommandValidationResult(
                    level=PermissionLevel.ALLOW,
                    command=path,
                    reason=f"Path is in allowed directory: {allowed}",
                )

        # Step 5: Outside workspace -> read is ALLOW, write is ASK
        if is_write:
            return CommandValidationResult(
                level=PermissionLevel.ASK,
                command=path,
                reason=f"Write to external path requires approval: {normalized}",
            )
        else:
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=path,
                reason="Read from external path is allowed",
            )


class ToolValidationMiddleware(ToolValidationMiddlewareBase):
    """
    Middleware that intercepts and validates tool calls.

    Features:
    - Bash commands: DENY/ALLOW/ASK validation via validate_command
    - File tools: path validation via validate_path + read-before-write guarantee
    - For ASK results, requests user confirmation via interrupt()

    Hint: The parent class (ToolValidationMiddlewareBase) has the following helpers:
    - self._validator: _BashValidator instance
    - self._read_files: dict[str, float] (path -> mtime at the time it was read)
    - self._is_allowed(tool_name, content): check session rule matching
    - self._add_allow_rule(tool_name, content): add session rule
    - self._enforce_timeout_limits(args): enforce timeout limits
    - self._truncate_output(result): truncate output
    - self._format_tool_error(tool_name, args, error): format error message
    """

    def __init__(self, config: PermissionConfig):
        super().__init__(config)
        self._validator = _BashValidator(config)  # uses the student-implemented validator

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Intercepts and validates tool calls."""
        tool_name = request.tool_call["name"]
        args = request.tool_call["args"]
        tool_call_id = request.tool_call["id"]

        try:
            # --- Bash Tool Validation ---
            if tool_name in _BASH_TOOL_NAMES:
                # TODO 2: Bash validation + ASK handling
                #
                # Step 1: self._enforce_timeout_limits(args)
                # Step 2: If "command" is in args, call self._validator.validate_command(args["command"])
                # Step 3: result.level == DENY -> return ToolMessage(status="error")
                #         content: f"Error: Command denied. {result.reason}"
                # Step 4: result.level == ASK:
                #   4a. If self._is_allowed(tool_name, command) is False:
                #       - cmd_prefix = command.split()[0] (use command as-is if empty string)
                #       - Call interrupt() (include question, tool_call_id, command, tool_name, allow_rule)
                #       - response == "always" -> self._add_allow_rule(tool_name, command)
                #       - response is falsy or starts with "deny:" -> return ToolMessage(status="error")
                pass

            # --- File Tool Validation ---
            elif tool_name in _FILE_TOOL_NAMES:
                # TODO 3: Path validation + Read-before-write
                #
                # Part A: Path validation
                #   A1. Extract path from args (key priority: "file_path" > "validated_path" > "path")
                #   A2. If not absolute path, os.path.join(self._config.workspace_root, path)
                #   A3. normalized_path = self._validator.get_normalized_path(path)
                #   A4. is_write = tool_name in _WRITE_FILE_TOOLS
                #   A5. self._validator.validate_path(path, is_write=is_write)
                #   A6. DENY -> ToolMessage(status="error", content="Error: Path denied. ...")
                #   A7. ASK -> check self._is_allowed -> interrupt() -> process response
                #       (use parent_dir for allow_rule: os.path.dirname(normalized_path))
                #       response == "always" -> self._allow_rules.append(PermissionRule(...))
                #   A8. args[path_key] = normalized_path (update with normalized path)
                #
                # Part B: Read-before-write check (only when is_write is True)
                #   B1. Check os.path.exists(normalized_path)
                #   B2. File exists + normalized_path not in self._read_files
                #       -> ToolMessage(status="error") "You must read the file first..."
                #   B3. File exists + os.path.getmtime > self._read_files[normalized_path]
                #       -> ToolMessage(status="error") "File has been modified since..."
                pass

            # --- Execute handler + post-processing ---
            handler_result = handler(request)

            # Track reads after successful read operations
            if tool_name == "read_file":
                if isinstance(handler_result, ToolMessage) and handler_result.status != "error":
                    if "file_path" in args or "path" in args or "validated_path" in args:
                        path_key = "file_path" if "file_path" in args else ("validated_path" if "validated_path" in args else "path")
                        normalized_path = self._validator.get_normalized_path(args[path_key])
                        try:
                            self._read_files[normalized_path] = os.path.getmtime(normalized_path)
                        except OSError:
                            pass

            # Update tracking after successful write/edit
            if tool_name in _WRITE_FILE_TOOLS:
                if isinstance(handler_result, ToolMessage) and handler_result.status != "error":
                    if "file_path" in args or "path" in args or "validated_path" in args:
                        path_key = "file_path" if "file_path" in args else ("validated_path" if "validated_path" in args else "path")
                        normalized_path = self._validator.get_normalized_path(args[path_key])
                        try:
                            self._read_files[normalized_path] = os.path.getmtime(normalized_path)
                        except OSError:
                            pass

            # Apply output truncation (hard limit)
            handler_result = self._truncate_output(handler_result)

            return handler_result

        except GraphInterrupt:
            raise
        except Exception as e:
            error_msg = self._format_tool_error(tool_name, args, e)
            return ToolMessage(
                content=error_msg,
                tool_call_id=tool_call_id,
                status="error",
            )
