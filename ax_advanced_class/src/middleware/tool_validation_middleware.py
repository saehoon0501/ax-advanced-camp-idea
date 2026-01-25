"""
Tool Validation Middleware

Provides validation for all tool calls using LangChain's @wrap_tool_call middleware.
Uses tree-sitter-bash for robust command parsing and security validation.
"""

import fnmatch
import os
from typing import Callable, List, Optional

from langchain_core.messages import ToolMessage
from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langgraph.errors import GraphInterrupt
from langgraph.types import Command, interrupt

from ax_advanced_class.src.config.tool_permission_config import (
    PermissionConfig,
    PermissionLevel,
    CommandValidationResult,
    MAX_OUTPUT_CHARS,
    DEFAULT_TIMEOUT_MS,
    MAX_TIMEOUT_MS,
)
from ax_advanced_class.src.tools.bash_tool import BashTool
from ax_advanced_class.src.tools.file_tool import FileOperationTool
from ax_advanced_class.src.utils.bash_parser import BashParser, ParsedCommand


class _BashValidator:
    """
    Validator for bash commands.

    Validation logic:
    1. Check DENY list → if listed, DENY
    2. Check ALLOW list → if listed, ALLOW
    3. Otherwise → ASK (default)

    Uses BashParser for tree-sitter based command parsing.
    """

    # Commands that modify files/directories (write operations)
    # For these, external paths require ASK
    _WRITE_COMMANDS = frozenset(
        {
            # File/directory manipulation
            "rm",
            "rmdir",
            "mkdir",
            "touch",
            "mv",
            "cp",
            "ln",
            "chmod",
            "chown",
            # Compression
            "tar",
            "zip",
            "unzip",
            "gzip",
            "gunzip",
            # File creation/modification
            "tee",
            "truncate",
            "shred",
            "install",
            "patch",
            "split",
            # Sync/transfer (can write to destination)
            "rsync",
            "scp",
            "wget",
            "curl",
            # Special files
            "mktemp",
            "mkfifo",
            "mknod",
        }
    )

    # Commands that only read files (read operations)
    # For these, external paths are ALLOWED
    _READ_COMMANDS = frozenset(
        {
            "cat",
            "head",
            "tail",
            "less",
            "more",
            "grep",
            "rg",
            "ag",
            "find",
            "locate",
            "ls",
            "tree",
            "du",
            "df",
            "file",
            "stat",
            "wc",
            "diff",
            "cmp",
        }
    )

    def __init__(self, config: PermissionConfig):
        self.config = config
        self._parser = BashParser()

    # =========================================================================
    # Public API
    # =========================================================================

    def validate_command(self, command: str) -> CommandValidationResult:
        """
        Validate a shell command string.

        Logic:
        1. Check raw patterns (before parsing)
        2. Check DENY (blocked commands, blocked patterns, blocked paths)
        3. Check ALLOW (allowed commands)
        4. Otherwise → ASK

        Returns:
            CommandValidationResult with the highest priority level found.
            Priority: DENY > ALLOW > ASK
        """
        if not command or not command.strip():
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=command,
                reason="Empty command",
            )

        # Check raw patterns FIRST (before parsing)
        # These catch patterns that may not parse correctly (e.g., fork bomb)
        for pattern in self.config.blocked_raw_patterns:
            if pattern in command:
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=command,
                    reason="Command contains blocked pattern",
                    blocked_items=[pattern],
                )

        # Check pattern rules (DENY patterns first, then ALLOW patterns)
        pattern_result = self._check_pattern_rules(command)
        if pattern_result:
            return pattern_result

        # Parse the command
        parsed_commands = self._parser.parse(command)

        if not parsed_commands:
            return CommandValidationResult(
                level=PermissionLevel.DENY,
                command=command,
                reason="Could not parse command structure",
            )

        # Validate each parsed command and collect results
        results: List[CommandValidationResult] = []
        for parsed in parsed_commands:
            result = self._validate_parsed_command(parsed)
            results.append(result)

            # Early exit on DENY
            if result.level == PermissionLevel.DENY:
                return result

        # Return the highest priority result (DENY > ALLOW > ASK)
        return self._get_highest_priority_result(results, command)

    def validate_path(self, path: str, is_write: bool = True) -> CommandValidationResult:
        """
        Validate a file path.

        Logic:
        1. Check blocked paths → DENY
        2. Check allowed paths (workspace + allowed_paths) → ALLOW
        3. If outside workspace:
           - Read operations → ALLOW (can read any file)
           - Write operations → ASK (requires user approval)

        Args:
            path: The file path to validate
            is_write: True if this is a write operation, False for read operations
        """
        if not path:
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=path,
                reason="Empty path defaults to workspace",
            )

        normalized = os.path.abspath(os.path.expanduser(path))

        # 1. Check blocked paths → DENY (always, regardless of read/write)
        for blocked in self.config.blocked_paths:
            blocked_abs = os.path.abspath(blocked)
            if normalized.startswith(blocked_abs):
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=path,
                    reason=f"Path is in blocked directory: {blocked}",
                    blocked_items=[blocked],
                )

        # 2. Check allowed paths (workspace + allowed_paths) → ALLOW
        allowed_roots = [self.config.workspace_root] + self.config.allowed_paths
        for allowed in allowed_roots:
            allowed_abs = os.path.abspath(os.path.expanduser(allowed))
            if normalized == allowed_abs or normalized.startswith(allowed_abs + os.sep):
                return CommandValidationResult(
                    level=PermissionLevel.ALLOW,
                    command=path,
                    reason=f"Path is in allowed directory: {allowed}",
                )

        # 3. Path is outside workspace
        if is_write:
            # Write operations outside workspace → ASK
            return CommandValidationResult(
                level=PermissionLevel.ASK,
                command=path,
                reason=f"Write to external path requires approval: {normalized}",
            )
        else:
            # Read operations outside workspace → ALLOW
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=path,
                reason="Read from external path is allowed",
            )

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
        # Default to write (safer) for unknown commands
        return True

    # =========================================================================
    # Pattern Matching
    # =========================================================================

    def _check_pattern_rules(self, command: str) -> Optional[CommandValidationResult]:
        """
        Check command against pattern-based rules.

        Order: DENY patterns → ALLOW patterns
        """
        # Check deny patterns first
        for pattern in self.config.deny_patterns:
            if fnmatch.fnmatch(command, pattern):
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=command,
                    reason=f"Command matches denied pattern: {pattern}",
                    blocked_items=[pattern],
                )

        # Check allow patterns
        for pattern in self.config.allow_patterns:
            if fnmatch.fnmatch(command, pattern):
                return CommandValidationResult(
                    level=PermissionLevel.ALLOW,
                    command=command,
                    reason=f"Command matches allowed pattern: {pattern}",
                )

        return None

    # =========================================================================
    # Validation Logic: DENY → ALLOW → ASK
    # =========================================================================

    def _validate_parsed_command(self, parsed: ParsedCommand) -> CommandValidationResult:
        """
        Validate a single parsed command.

        Logic:
        1. Check DENY (interactive, blocked commands, blocked patterns, blocked paths)
        2. Check ALLOW (allowed commands, allowed git subcommands)
        3. Otherwise → ASK
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

        # 1c. Check blocked commands
        if cmd_name in self.config.blocked_commands:
            return CommandValidationResult(
                level=PermissionLevel.DENY,
                command=parsed.raw_text,
                reason=f"Command '{cmd_name}' is blocked",
                blocked_items=[cmd_name],
            )

        # 1d. Check blocked argument patterns
        pattern_result = self._check_blocked_patterns(parsed)
        if pattern_result:
            return pattern_result

        # 1e. Validate paths in arguments
        # Determine if this is a read or write command
        is_write = self._is_write_command(cmd_name)

        for path in parsed.paths:
            path_result = self.validate_path(path, is_write=is_write)

            # DENY always blocks
            if path_result.level == PermissionLevel.DENY:
                return CommandValidationResult(
                    level=PermissionLevel.DENY,
                    command=parsed.raw_text,
                    reason=f"Command contains blocked path: {path}",
                    blocked_items=[path],
                )

            # ASK for write operations to external paths
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

        # 2b. Check allowed commands
        if cmd_name in self.config.allowed_commands:
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=parsed.raw_text,
                reason=f"Command '{cmd_name}' is allowed",
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

        # Create a set of all tokens (command name + arguments)
        all_tokens = {cmd_name} | set(parsed.arguments)

        # Add pipe indicator if present
        if parsed.has_pipe:
            all_tokens.add("|")

        # Check each blocked pattern
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
        1. Check blocked patterns → DENY
        2. Check allowed git subcommands → ALLOW
        3. Otherwise → ASK
        """
        # 1. Check blocked patterns
        pattern_result = self._check_blocked_patterns(parsed)
        if pattern_result:
            return pattern_result

        # Get subcommand
        subcommand = parsed.arguments[0] if parsed.arguments else None

        if not subcommand:
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=parsed.raw_text,
                reason="Git command without subcommand",
            )

        # 2. Check allowed git subcommands → ALLOW
        if subcommand in self.config.allowed_git_subcommands:
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=parsed.raw_text,
                reason=f"Git subcommand '{subcommand}' is allowed",
            )

        # 3. Otherwise → ASK
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
            PermissionLevel.DENY: 0,  # Highest priority (wins)
            PermissionLevel.ALLOW: 1,  # Second priority
            PermissionLevel.ASK: 2,  # Lowest priority (default)
        }

        return min(results, key=lambda r: priority[r.level])


class ToolValidationMiddleware(AgentMiddleware):
    """
    Middleware for validating all tool calls.

    Facilitates validation in the agent lifecycle by intercepting tool calls
    and delegating validation to _BashValidator.

    Features:
    - Read-before-write/edit check: Existing files must be read before write/edit
    - Stale read detection: Detects if a file was modified since last read
    """

    def __init__(self, config: PermissionConfig):
        self._validator = _BashValidator(config)
        self._config = config
        # Track read files: {normalized_path: modification_time_at_read}
        self._read_files: dict[str, float] = {}

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Intercepts tool calls to validate arguments before execution."""
        tool_name = request.tool_call["name"]
        args = request.tool_call["args"]
        tool_call_id = request.tool_call["id"]

        try:
            # --- Bash Tool Validation ---
            if tool_name in BashTool.get_tool_names():
                # Enforce timeout limits (hard limit)
                self._enforce_timeout_limits(args)

                if "command" in args:
                    result = self._validator.validate_command(args["command"])

                    if result.level == PermissionLevel.DENY:
                        return ToolMessage(
                            content=f"Error: Command denied. {result.reason}",
                            tool_call_id=tool_call_id,
                            status="error",
                        )

                    # ASK level - proceed but could prompt user in future
                    if result.level == PermissionLevel.ASK:
                        is_apporved = interrupt(
                            {
                                "question": f"Command '{args['command']}' requires confirmation",
                                "tool_call_id": tool_call_id,
                                "command": args["command"],
                                "tool_name": tool_name,
                            }
                        )
                        if not is_apporved:
                            return ToolMessage(
                                content=f"Error: Command denied. {result.reason}",
                                tool_call_id=tool_call_id,
                                status="error",
                            )

            # --- File Tool Validation ---
            elif tool_name in FileOperationTool.get_tool_names():
                if "path" in args or "validated_path" in args:
                    # Handle both 'path' and 'validated_path' parameter names
                    path_key = "validated_path" if "validated_path" in args else "path"
                    path = args[path_key]

                    if not os.path.isabs(path):
                        path = os.path.join(self._config.workspace_root, path)

                    # Get normalized path for tracking
                    normalized_path = self._validator.get_normalized_path(path)

                    # Determine if this is a read or write operation
                    # read, grep, glob → read operations
                    # write, edit → write operations
                    is_write = tool_name in ("write", "edit")

                    result = self._validator.validate_path(path, is_write=is_write)

                    if result.level == PermissionLevel.DENY:
                        return ToolMessage(
                            content=f"Error: Path denied. {result.reason}",
                            tool_call_id=tool_call_id,
                            status="error",
                        )

                    # ASK for write operations to external paths
                    if result.level == PermissionLevel.ASK:
                        is_apporved = interrupt(
                            {
                                "question": f"Path '{normalized_path}' requires confirmation",
                                "tool_call_id": tool_call_id,
                                "path": normalized_path,
                                "tool_name": tool_name,
                            }
                        )
                        if not is_apporved:
                            return ToolMessage(
                                content=f"Error: Path denied. {result.reason}",
                                tool_call_id=tool_call_id,
                                status="error",
                            )

                    # --- Read-before-write/edit check and stale read detection ---
                    if is_write:
                        file_exists = os.path.exists(normalized_path)

                        if file_exists:
                            # Check if file was read first
                            if normalized_path not in self._read_files:
                                operation = "writing to" if tool_name == "write" else "editing"
                                return ToolMessage(
                                    content=f"Error: You must read the file first before {operation} it. Use the Read tool first.",
                                    tool_call_id=tool_call_id,
                                    status="error",
                                )

                            # Check for stale read (file modified since last read)
                            try:
                                current_mtime = os.path.getmtime(normalized_path)
                                read_mtime = self._read_files[normalized_path]
                                if current_mtime > read_mtime:
                                    operation = "writing to" if tool_name == "write" else "editing"
                                    return ToolMessage(
                                        content=f"Error: File has been modified since you last read it. Please read the file again before {operation} it.",
                                        tool_call_id=tool_call_id,
                                        status="error",
                                    )
                            except OSError:
                                pass  # File might have been deleted

                    # Update with normalized path
                    args[path_key] = normalized_path

            # If validation passes, proceed to next middleware or tool call
            handler_result = handler(request)

            # --- Track reads after successful read operations ---
            if tool_name == "read":
                if isinstance(handler_result, ToolMessage) and handler_result.status != "error":
                    # Track the read
                    if "path" in args or "validated_path" in args:
                        path_key = "validated_path" if "validated_path" in args else "path"
                        normalized_path = self._validator.get_normalized_path(args[path_key])
                        try:
                            mtime = os.path.getmtime(normalized_path)
                            self._read_files[normalized_path] = mtime
                        except OSError:
                            pass  # File might not exist

            # --- Update tracking after successful write/edit ---
            if tool_name in ("write", "edit"):
                if isinstance(handler_result, ToolMessage) and handler_result.status != "error":
                    # Update the tracked mtime after successful write/edit
                    if "path" in args or "validated_path" in args:
                        path_key = "validated_path" if "validated_path" in args else "path"
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
            return ToolMessage(
                content=f"Error: Validation failed. {str(e)}",
                tool_call_id=tool_call_id,
                status="error",
            )

    def _truncate_output(self, result: ToolMessage | Command) -> ToolMessage | Command:
        """Truncate output if it exceeds MAX_OUTPUT_CHARS."""
        if isinstance(result, ToolMessage) and len(result.content) > MAX_OUTPUT_CHARS:
            truncated_content = (
                result.content[:MAX_OUTPUT_CHARS] + f"\n\n[Output truncated at {MAX_OUTPUT_CHARS} characters]"
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
            # Clamp to max timeout
            args["timeout"] = min(args["timeout"], max_timeout_sec)
        else:
            # Set default timeout
            args["timeout"] = default_timeout_sec
