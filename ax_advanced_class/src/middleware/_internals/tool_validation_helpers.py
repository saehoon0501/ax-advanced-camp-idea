"""Internal helpers for ToolValidationMiddleware -- pre-implemented logic.

This module contains the parts that students do NOT need to implement:
- Constants for tool name matching
- _BashValidatorBase with all helper/utility methods
- ToolValidationMiddlewareBase with utility methods and default wrap_tool_call
"""

import os
from typing import Callable, List, Optional

from langchain_core.messages import ToolMessage
from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from ax_advanced_class.src.config.tool_permission_config import (
    PermissionConfig,
    PermissionLevel,
    PermissionRule,
    CommandValidationResult,
    MAX_OUTPUT_CHARS,
    DEFAULT_TIMEOUT_MS,
    MAX_TIMEOUT_MS,
)
from ax_advanced_class.src.utils.bash_parser import BashParser, ParsedCommand

# ============================================================================
# Tool name constants matching deepagents FilesystemMiddleware + LocalShellBackend
# ============================================================================
_BASH_TOOL_NAMES = ("execute",)
_FILE_TOOL_NAMES = ("read_file", "write_file", "edit_file", "glob", "grep", "ls")
_WRITE_FILE_TOOLS = ("write_file", "edit_file")


class _BashValidatorBase:
    """
    Base validator for bash commands.

    Provides all helper methods for command validation.
    Students override ``validate_command`` and ``validate_path`` in a subclass.

    Validation logic:
    1. Check DENY list -> if listed, DENY
    2. Check ALLOW list -> if listed, ALLOW
    3. Otherwise -> ASK (default)

    Uses BashParser for tree-sitter based command parsing.
    """

    # Commands that modify files/directories (write operations)
    _WRITE_COMMANDS = frozenset(
        {
            "rm", "rmdir", "mkdir", "touch", "mv", "cp", "ln", "chmod", "chown",
            "tar", "zip", "unzip", "gzip", "gunzip",
            "tee", "truncate", "shred", "install", "patch", "split",
            "rsync", "scp", "wget", "curl",
            "mktemp", "mkfifo", "mknod",
        }
    )

    # Commands that only read files (read operations)
    _READ_COMMANDS = frozenset(
        {
            "cat", "head", "tail", "less", "more",
            "grep", "rg", "ag", "find", "locate",
            "ls", "tree", "du", "df",
            "file", "stat", "wc", "diff", "cmp",
        }
    )

    def __init__(self, config: PermissionConfig):
        self.config = config
        self._parser = BashParser()
        self._allow_rules = [PermissionRule.parse(r) for r in config.allow_rules]
        self._deny_rules = [PermissionRule.parse(r) for r in config.deny_rules]

    # =========================================================================
    # Default public API (students override these)
    # =========================================================================

    def validate_command(self, command: str) -> CommandValidationResult:
        """Default: returns ASK for everything. Students override this."""
        return CommandValidationResult(
            level=PermissionLevel.ASK,
            command=command,
            reason="Default: requires confirmation",
        )

    def validate_path(self, path: str, is_write: bool = True) -> CommandValidationResult:
        """Default: returns ASK for everything. Students override this."""
        return CommandValidationResult(
            level=PermissionLevel.ASK,
            command=path,
            reason="Default: requires confirmation",
        )

    # =========================================================================
    # Utility methods (used by student implementations)
    # =========================================================================

    def get_normalized_path(self, path: str) -> str:
        """Return normalized absolute path."""
        if not path:
            return self.config.workspace_root
        return os.path.abspath(os.path.expanduser(path))

    def _is_write_command(self, cmd_name: str) -> bool:
        """
        Determine if a command is a write operation.

        Returns:
            True if the command modifies files (write operation)
            False if the command only reads files (read operation)

        For unknown commands, defaults to True (write) for safety.
        """
        if cmd_name in self._READ_COMMANDS:
            return False
        if cmd_name in self._WRITE_COMMANDS:
            return True
        return True  # Default to write (safer) for unknown commands

    def _check_rules(self, command: str) -> Optional[CommandValidationResult]:
        """
        Check command against PermissionRule-based deny/allow rules.

        Order: DENY rules -> ALLOW rules
        """
        for rule in self._deny_rules:
            if rule.matches("execute", command):
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=command,
                    reason=f"Command matches deny rule: {rule}",
                    blocked_items=[str(rule)],
                )

        for rule in self._allow_rules:
            if rule.matches("execute", command):
                return CommandValidationResult(
                    level=PermissionLevel.ALLOW,
                    command=command,
                    reason=f"Command matches allow rule: {rule}",
                )

        return None

    def _validate_parsed_command(self, parsed: ParsedCommand) -> CommandValidationResult:
        """
        Validate a single parsed command.

        Logic:
        1. Check DENY (interactive, blocked commands, blocked patterns, blocked paths)
        2. Check ALLOW (allowed commands, allowed git subcommands)
        3. Otherwise -> ASK
        """
        cmd_name = parsed.name

        # === DENY CHECKS ===

        # 1a. Check interactive commands (no TTY available)
        if cmd_name in self.config.interactive_commands:
            return CommandValidationResult(
                level=PermissionLevel.DENY,
                command=parsed.raw_text,
                reason=f"Interactive command '{cmd_name}' not supported (no TTY)",
                blocked_items=[cmd_name],
            )

        # 1b. Check interactive arguments
        interactive_args = self.config.interactive_arguments.get(cmd_name, set())
        for pattern in interactive_args:
            if pattern.issubset(set(parsed.arguments)):
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=parsed.raw_text,
                    reason="Interactive flag not supported (no TTY)",
                    blocked_items=list(pattern),
                )

        # 1c. Check deny rules for this command
        for rule in self._deny_rules:
            if rule.matches("execute", cmd_name) or rule.matches("execute", parsed.raw_text):
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=parsed.raw_text,
                    reason=f"Command matches deny rule: {rule}",
                    blocked_items=[str(rule)],
                )

        # 1d. Check blocked argument patterns
        pattern_result = self._check_blocked_patterns(parsed)
        if pattern_result:
            return pattern_result

        # 1e. Validate paths in arguments
        is_write = self._is_write_command(cmd_name)

        for path in parsed.paths:
            path_result = self.validate_path(path, is_write=is_write)

            if path_result.level == PermissionLevel.DENY:
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=parsed.raw_text,
                    reason=f"Command contains blocked path: {path}",
                    blocked_items=[path],
                )

            if path_result.level == PermissionLevel.ASK:
                return CommandValidationResult(
                    level=PermissionLevel.ASK,
                    command=parsed.raw_text,
                    reason=f"Write to external path requires approval: {path}",
                )

        # === ALLOW CHECKS ===

        # 2a. Special handling for git commands
        if cmd_name == "git":
            return self._validate_git_command(parsed)

        # 2b. Check allow rules for this command
        for rule in self._allow_rules:
            if rule.matches("execute", cmd_name) or rule.matches("execute", parsed.raw_text):
                return CommandValidationResult(
                    level=PermissionLevel.ALLOW,
                    command=parsed.raw_text,
                    reason=f"Command matches allow rule: {rule}",
                )

        # === DEFAULT: ASK ===
        return CommandValidationResult(
            level=PermissionLevel.ASK,
            command=parsed.raw_text,
            reason=f"Command '{cmd_name}' requires confirmation",
        )

    def _check_blocked_patterns(self, parsed: ParsedCommand) -> Optional[CommandValidationResult]:
        """Check if the command matches any blocked argument patterns."""
        cmd_name = parsed.name
        patterns = self.config.blocked_argument_patterns.get(cmd_name, set())

        if not patterns:
            return None

        all_tokens = {cmd_name} | set(parsed.arguments)
        if parsed.has_pipe:
            all_tokens.add("|")

        for pattern in patterns:
            if pattern.issubset(all_tokens):
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=parsed.raw_text,
                    reason=f"Command matches blocked pattern: {pattern}",
                    blocked_items=list(pattern),
                )

        return None

    def _validate_git_command(self, parsed: ParsedCommand) -> CommandValidationResult:
        """
        Special validation for git commands.

        Logic:
        1. Check blocked patterns -> DENY
        2. Check allowed git subcommands -> ALLOW
        3. Otherwise -> ASK
        """
        pattern_result = self._check_blocked_patterns(parsed)
        if pattern_result:
            return pattern_result

        subcommand = parsed.arguments[0] if parsed.arguments else None

        if not subcommand:
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=parsed.raw_text,
                reason="Git command without subcommand",
            )

        if subcommand in self.config.allowed_git_subcommands:
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=parsed.raw_text,
                reason=f"Git subcommand '{subcommand}' is allowed",
            )

        return CommandValidationResult(
            level=PermissionLevel.ASK,
            command=parsed.raw_text,
            reason=f"Git subcommand '{subcommand}' requires confirmation",
        )

    def _get_highest_priority_result(
        self, results: List[CommandValidationResult], original_command: str
    ) -> CommandValidationResult:
        """
        Get the highest priority result from a list.

        Priority: DENY > ALLOW > ASK
        """
        if not results:
            return CommandValidationResult(
                level=PermissionLevel.ASK,
                command=original_command,
                reason="No commands found",
            )

        priority = {
            PermissionLevel.DENY: 0,
            PermissionLevel.ALLOW: 1,
            PermissionLevel.ASK: 2,
        }

        return min(results, key=lambda r: priority[r.level])


class ToolValidationMiddlewareBase(AgentMiddleware):
    """
    Base middleware for validating all tool calls.

    Provides utility methods and default wrap_tool_call.
    Students override ``wrap_tool_call`` to implement validation logic.

    Features:
    - Read-before-write/edit check: Existing files must be read before write/edit
    - Stale read detection: Detects if a file was modified since last read
    """

    def __init__(self, config: PermissionConfig):
        self._validator = _BashValidatorBase(config)
        self._config = config
        # Track read files: {normalized_path: modification_time_at_read}
        self._read_files: dict[str, float] = {}
        # Session-scoped permission rules: Tool(pattern) format
        self._allow_rules: list[PermissionRule] = []

    def _is_allowed(self, tool_name: str, content: str) -> bool:
        """Check if any session rule matches this tool call."""
        return any(rule.matches(tool_name, content) for rule in self._allow_rules)

    def _add_allow_rule(self, tool_name: str, content: str) -> str:
        """Create a prefix rule from content and add it. Returns the rule string."""
        prefix = content.split()[0] if content.strip() else content
        rule = PermissionRule(tool_name=tool_name, pattern=f"{prefix}:*")
        self._allow_rules.append(rule)
        return str(rule)

    def _format_tool_error(self, tool_name: str, args: dict, error: Exception) -> str:
        """
        Format tool errors with actionable guidance for the agent.

        Parses validation errors to provide clear instructions on how to fix them.
        """
        error_str = str(error)

        # Check for Pydantic ValidationError (missing required fields)
        if "validation error" in error_str.lower() and "field required" in error_str.lower():
            lines = error_str.split("\n")
            missing_fields = []
            for i, line in enumerate(lines):
                if "Field required" in line and i > 0:
                    field_name = lines[i - 1].strip()
                    if field_name:
                        missing_fields.append(field_name)

            if missing_fields:
                provided = ", ".join(f'"{k}"' for k in args.keys()) if args else "none"
                missing = ", ".join(f'"{f}"' for f in missing_fields)
                return (
                    f"Error: Missing required parameter(s) for '{tool_name}' tool.\n"
                    f"Missing: {missing}\n"
                    f"Provided: {provided}\n"
                    f"Action: Retry the tool call with ALL required parameters included."
                )

        # Check for type errors
        if "type=" in error_str and "input_value=" in error_str:
            return (
                f"Error: Invalid parameter type for '{tool_name}' tool.\n"
                f"Details: {error_str}\n"
                f"Action: Check parameter types and retry with correct types."
            )

        return (
            f"Error: Tool '{tool_name}' failed.\n"
            f"Details: {error_str}\n"
            f"Action: Review the error and retry with corrected parameters."
        )

    def _truncate_output(self, result: ToolMessage | Command) -> ToolMessage | Command:
        """Truncate output if it exceeds MAX_OUTPUT_CHARS."""
        if isinstance(result, ToolMessage) and len(result.content) > MAX_OUTPUT_CHARS:
            truncated_content = (
                result.content[:MAX_OUTPUT_CHARS]
                + f"\n\n[Output truncated at {MAX_OUTPUT_CHARS} characters]"
            )
            return ToolMessage(
                content=truncated_content,
                tool_call_id=result.tool_call_id,
                status=result.status,
            )
        return result

    def _enforce_timeout_limits(self, args: dict) -> None:
        """Enforce timeout limits for bash commands (hard limit)."""
        max_timeout_sec = MAX_TIMEOUT_MS // 1000
        default_timeout_sec = DEFAULT_TIMEOUT_MS // 1000

        if "timeout" in args:
            args["timeout"] = min(args["timeout"], max_timeout_sec)
        else:
            args["timeout"] = default_timeout_sec

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Default: just calls handler with no validation. Students override this."""
        return handler(request)
