"""
Minimal Tool Validation Middleware for Coding Agent Evals.

Design principles:
- Block only truly dangerous commands (system destruction, privilege escalation)
- ALLOW everything else (no ASK permissions to avoid eval interrupts)
- No path restrictions (workspace is under /tmp)
- No read-before-write checking (eval environment)
"""

import fnmatch
from typing import Callable, List, Optional, FrozenSet, Set, Dict

from langchain_core.messages import ToolMessage
from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command

from ax_advanced_class.src.utils.bash_parser import BashParser, ParsedCommand

# Tool name constant matching deepagents FilesystemMiddleware + LocalShellBackend
_BASH_TOOL_NAMES = ("execute",)


# Hard limits
MAX_OUTPUT_CHARS: int = 30_000
DEFAULT_TIMEOUT_SEC: int = 120
MAX_TIMEOUT_SEC: int = 600


class EvalToolValidationMiddleware(AgentMiddleware):
    """
    Minimal middleware for eval environment.

    Only blocks dangerous commands - everything else is ALLOWED.
    No ASK permissions to prevent eval interrupts.
    """

    # Commands that are ALWAYS blocked (system destruction / privilege escalation)
    BLOCKED_COMMANDS: FrozenSet[str] = frozenset({
        # Privilege escalation
        "sudo", "su",
        # System destruction / control
        "mkfs", "fdisk", "dd", "mount", "umount",
        "shutdown", "reboot", "init", "systemctl", "service",
    })

    # Interactive commands (no TTY available)
    INTERACTIVE_COMMANDS: FrozenSet[str] = frozenset({
        "vim", "vi", "nano", "emacs", "less", "more", "top", "htop",
    })

    # Raw patterns blocked before parsing (exact string match)
    BLOCKED_RAW_PATTERNS: FrozenSet[str] = frozenset({
        ":(){ :|:& };:",  # Fork bomb
        "> /dev/sda",     # Disk destruction
        "> /dev/hda",
        ">/dev/sda",
        ">/dev/hda",
    })

    # Blocked argument patterns: command -> set of dangerous argument combinations
    BLOCKED_ARGUMENT_PATTERNS: Dict[str, Set[FrozenSet[str]]] = {
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
            frozenset({"config", "--global"}),
        },
    }

    # Interactive arguments → block
    INTERACTIVE_ARGUMENTS: Dict[str, Set[FrozenSet[str]]] = {
        "git": {frozenset({"-i"}), frozenset({"--interactive"})},
        "python": {frozenset({"-i"})},
        "node": {frozenset({"-i"})},
    }

    # Deny patterns (wildcard matching)
    DENY_PATTERNS: List[str] = [
        "curl * | bash",
        "curl * | sh",
        "wget * | bash",
        "wget * | sh",
    ]

    def __init__(self):
        self._parser = BashParser()

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Intercepts tool calls to validate bash commands."""
        tool_name = request.tool_call["name"]
        args = request.tool_call["args"]
        tool_call_id = request.tool_call["id"]

        try:
            # Only validate bash commands
            if tool_name in _BASH_TOOL_NAMES and "command" in args:
                command = args["command"]

                # Validate command
                is_blocked, reason = self._validate_command(command)

                if is_blocked:
                    return ToolMessage(
                        content=f"Error: Command denied. {reason}",
                        tool_call_id=tool_call_id,
                        status="error",
                    )

                # Enforce timeout limits
                self._enforce_timeout_limits(args)

            # If validation passes, proceed to tool execution
            handler_result = handler(request)

            # Truncate output if needed
            handler_result = self._truncate_output(handler_result)

            return handler_result

        except Exception as e:
            return ToolMessage(
                content=f"Error: Tool '{tool_name}' failed. {str(e)}",
                tool_call_id=tool_call_id,
                status="error",
            )

    def _validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate a bash command.

        Returns:
            (is_blocked, reason) - True if command should be blocked
        """
        if not command or not command.strip():
            return False, ""

        # Check raw patterns first
        for pattern in self.BLOCKED_RAW_PATTERNS:
            if pattern in command:
                return True, f"Command contains blocked pattern: {pattern}"

        # Check deny patterns (wildcard)
        for pattern in self.DENY_PATTERNS:
            if fnmatch.fnmatch(command, pattern):
                return True, f"Command matches denied pattern: {pattern}"

        # Parse the command
        parsed_commands = self._parser.parse(command)

        if not parsed_commands:
            return True, "Could not parse command structure"

        # Validate each parsed command
        for parsed in parsed_commands:
            is_blocked, reason = self._validate_parsed_command(parsed)
            if is_blocked:
                return True, reason

        return False, ""

    def _validate_parsed_command(self, parsed: ParsedCommand) -> tuple[bool, str]:
        """Validate a single parsed command."""
        cmd_name = parsed.name

        # Check interactive commands
        if cmd_name in self.INTERACTIVE_COMMANDS:
            return True, f"Interactive command '{cmd_name}' not supported (no TTY)"

        # Check interactive arguments
        interactive_args = self.INTERACTIVE_ARGUMENTS.get(cmd_name, set())
        for pattern in interactive_args:
            if pattern.issubset(set(parsed.arguments)):
                return True, "Interactive flag not supported (no TTY)"

        # Check blocked commands
        if cmd_name in self.BLOCKED_COMMANDS:
            return True, f"Command '{cmd_name}' is blocked"

        # Check blocked argument patterns
        patterns = self.BLOCKED_ARGUMENT_PATTERNS.get(cmd_name, set())
        if patterns:
            all_tokens = {cmd_name} | set(parsed.arguments)
            if parsed.has_pipe:
                all_tokens.add("|")

            for pattern in patterns:
                if pattern.issubset(all_tokens):
                    return True, f"Command matches blocked pattern: {pattern}"

        # Everything else is ALLOWED
        return False, ""

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
        """Enforce timeout limits for bash commands."""
        if "timeout" in args:
            args["timeout"] = min(args["timeout"], MAX_TIMEOUT_SEC)
        else:
            args["timeout"] = DEFAULT_TIMEOUT_SEC
