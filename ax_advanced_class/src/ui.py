"""
UI Helper Module

Pretty printing utilities for the CLI interface.
Uses Rich library for styled terminal output.
"""

import os
import sys
import time
from typing import Optional

from rich.console import Console, Group
from rich.control import Control
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.theme import Theme
from rich.table import Table
from rich.box import ROUNDED, MINIMAL
from rich.spinner import Spinner
from rich.style import Style
from rich.syntax import Syntax

from typing import AsyncGenerator

from ax_advanced_class.src.orchestrator import LongRunningOrchestrator
from ax_advanced_class.src.services import StreamEvent


VERSION = "0.1.0"

# Icons for different event types
ICONS = {
    "thinking": "◐",
    "tool_start": "⚡",
    "tool_done": "✓",
    "tool_error": "✗",
    "route": "→",
    "agent": "🤖",
    "file_read": "📖",
    "file_write": "✏️",
    "bash": "💻",
    "search": "🔍",
}

custom_theme = Theme(
    {
        "info": "dim red",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "tool": "bright_red",
        "tool.name": "bold cyan",
        "tool.input": "dim white",
        "tool.output": "dim green",
        "tool.time": "dim yellow",
        "thinking": "dim white",
        "prompt": "bold bright_red",
        "agent": "red",
        "accent": "bright_red",
        "route": "dim cyan",
        "spinner": "cyan",
    }
)

console = Console(theme=custom_theme)


def print_welcome(workspace: str = "./workspace"):
    """Print the welcome banner."""
    mascot = """
       ∩  ∩
      ( ˘ω˘ )ノ  [dim]안녕하세요 여러분 반갑습니다~[/dim] [red]♥[/red]
      /     つ   [dim]이번 실습을 도와드릴 갓찌입니다~[/dim]
      """

    left_content = (
        "\n[bold]Welcome to Incubation Camp![/bold]\n" f"{mascot}\n\n" f"[dim]{os.path.abspath(workspace)}[/dim]"
    )

    right_content = (
        "[bold]Commands[/bold]\n"
        "[dim]─────────────────────────────────────[/dim]\n"
        "[bold]/init[/bold] <name> <desc>  Initialize project\n"
        "[bold]/status[/bold]             Show project status\n"
        "[bold]/run[/bold]                Run coding session\n"
        "[bold]/workspace[/bold] <path>   Set workspace path\n"
        "[bold]exit[/bold]                Exit the CLI"
    )

    table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    table.add_column(ratio=2)
    table.add_column(ratio=1)
    table.add_row(left_content, right_content)

    console.print()
    console.print(
        Panel(
            table,
            title=f"[bold bright_red]Incubation Camp CLI v{VERSION}[/bold bright_red]",
            title_align="left",
            border_style="bright_red",
            box=ROUNDED,
        )
    )
    console.print()


def print_prompt():
    """
    Display input prompt and get user input.

    After user presses enter:
    - The input becomes part of conversation history
    - Progress messages will appear BELOW the user input
    """
    console.rule(style="dim")
    console.print()
    console.rule(style="dim")

    console.print(Control.move(0, -2))

    prompt_text = "[prompt]❯[/prompt] "
    user_input = console.input(prompt_text).strip()

    console.print(Control.move(0, 1))

    return user_input


def print_status(orchestrator: LongRunningOrchestrator, config: dict, workspace: str):
    """Print current project status."""
    state = orchestrator.get_state(config)

    console.print()
    console.print("[bold]Project Status[/bold]", style="info")
    console.print(f"  Workspace: [dim]{os.path.abspath(workspace)}[/dim]")

    if state:
        console.print(f"  Project: [bold]{state.get('project_name', 'N/A')}[/bold]")
        console.print(
            f"  Initialized: {'[green]Yes[/green]' if state.get('is_initialized') else '[yellow]No[/yellow]'}"
        )
        console.print(f"  Sessions: {state.get('session_count', 0)}")

        features = state.get("feature_list", [])
        if features:
            completed = sum(1 for f in features if f.get("passes", False))
            console.print(f"  Features: {completed}/{len(features)} completed")
    else:
        console.print("  [dim]No active project. Use /init to start.[/dim]")
    console.print()


def _get_tool_icon(tool_name: str) -> str:
    """Get the appropriate icon for a tool."""
    tool_lower = tool_name.lower()
    if "bash" in tool_lower:
        return ICONS["bash"]
    elif "read" in tool_lower:
        return ICONS["file_read"]
    elif "write" in tool_lower:
        return ICONS["file_write"]
    elif "grep" in tool_lower or "glob" in tool_lower or "search" in tool_lower:
        return ICONS["search"]
    return ICONS["tool_start"]


def _format_tool_input(tool_name: str, tool_input: dict) -> str:
    """Format tool input for display."""
    tool_lower = tool_name.lower()

    if "bash" in tool_lower:
        cmd = tool_input.get("command", "")
        if len(cmd) > 80:
            cmd = cmd[:77] + "..."
        return f"$ {cmd}"
    elif "read" in tool_lower:
        path = tool_input.get("validated_path", tool_input.get("path", ""))
        # Shorten path for display
        if len(path) > 60:
            path = "..." + path[-57:]
        return path
    elif "write" in tool_lower:
        path = tool_input.get("validated_path", tool_input.get("path", ""))
        if len(path) > 60:
            path = "..." + path[-57:]
        content_len = len(tool_input.get("content", ""))
        return f"{path} ({content_len} bytes)"
    elif "grep" in tool_lower:
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", ".")
        return f'"{pattern}" in {path}'
    elif "glob" in tool_lower:
        pattern = tool_input.get("pattern", "")
        return f'"{pattern}"'
    else:
        # Generic: show first key-value pair
        preview = str(tool_input)[:60]
        if len(str(tool_input)) > 60:
            preview += "..."
        return preview


def _format_tool_output(output: str, max_lines: int = 5) -> str:
    """Format tool output for compact display."""
    lines = output.strip().split("\n")
    if len(lines) <= max_lines:
        return output.strip()

    # Show first few and last few lines
    shown = lines[:3] + ["  ..."] + lines[-2:]
    return "\n".join(shown)


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.0f}s"


class StreamingSession:
    """Manages streaming display state across multiple event generators."""

    def __init__(self):
        self.streaming_content = ""
        self.current_segment = ""  # New: Track text since last flush
        self.current_tool = None
        self.current_tool_input = {}
        self.tool_start_time = None
        self.final_response = ""
        self.spinner_frames = ["◐", "◓", "◑", "◒"]
        self.spinner_idx = 0
        self.header_printed = False

    def _get_spinner(self) -> str:
        """Get the next spinner frame."""
        frame = self.spinner_frames[self.spinner_idx % len(self.spinner_frames)]
        self.spinner_idx += 1
        return frame

    def _create_status_line(self, status: str, style: str = "thinking") -> Text:
        """Create a status line with spinner."""
        spinner = self._get_spinner()
        text = Text()
        text.append(f"{spinner} ", style="spinner")
        text.append(status, style=style)
        return text

    def _create_tool_panel(self, tool_name: str, tool_input: dict) -> Panel:
        """Create a compact panel showing tool execution."""
        icon = _get_tool_icon(tool_name)
        input_preview = _format_tool_input(tool_name, tool_input)

        content = Text()
        content.append(f"{icon} ", style="tool")
        content.append(tool_name, style="tool.name")
        content.append(f"  {input_preview}", style="tool.input")

        return Panel(
            content,
            box=MINIMAL,
            padding=(0, 1),
            style="dim",
        )

    def _create_view(self, user_input: str, status_renderable) -> Group:
        """Create the full view with content and status."""
        # Show current segment instead of full streaming content
        display_text = self.current_segment

        body = Text(display_text, style="white")

        # Layout: Content (Top) -> Status (Bottom)
        return Group(
            body,
            Text(""),  # Padding below body
            status_renderable,
        )

    def _flush_segment(self):
        """Flush the current text segment to the console."""
        if self.current_segment:
            console.print(Markdown(self.current_segment))
            console.print()  # Add gap after text block
            self.current_segment = ""

    async def display_events(
        self, event_generator: AsyncGenerator[StreamEvent, None], user_input: str
    ) -> Optional[StreamEvent]:
        """
        Display events from a generator until interrupted or complete.
        """
        if not self.header_printed and user_input:
            console.print(f"[prompt]❯[/prompt] {user_input}")
            console.print()  # Add gap between prompt and response
            self.header_printed = True

        current_status = self._create_status_line("Thinking...")

        # Initial print of user input is handled above
        # We rely on Live view to show content and status

        with Live(console=console, refresh_per_second=10, transient=True) as live:
            live.update(self._create_view(user_input, current_status))

            async for event in event_generator:
                if event.type == "thinking":
                    current_status = self._create_status_line("Thinking...")
                    live.update(self._create_view(user_input, current_status))

                elif event.type == "token":
                    self.streaming_content += event.content
                    self.current_segment += event.content
                    live.update(self._create_view(user_input, current_status))

                elif event.type == "tool_call":
                    # Flush text before tool
                    self._flush_segment()
                    # Clear Live view body (handled by _create_view reading empty current_segment)

                    self.current_tool = event.metadata.get("tool_name", "unknown")
                    self.current_tool_input = event.metadata.get("tool_input", {})
                    self.tool_start_time = time.time()

                    # Show tool execution with preview
                    icon = _get_tool_icon(self.current_tool)
                    input_preview = _format_tool_input(self.current_tool, self.current_tool_input)

                    status = Text()
                    status.append(f"{self._get_spinner()} ", style="spinner")
                    status.append(f"{icon} ", style="tool")
                    status.append(self.current_tool, style="tool.name")
                    status.append(f"  {input_preview}", style="tool.input")

                    current_status = status
                    live.update(self._create_view(user_input, current_status))

                elif event.type == "tool_result":
                    if self.current_tool:
                        duration = time.time() - self.tool_start_time if self.tool_start_time else 0
                        icon = _get_tool_icon(self.current_tool)

                        # Print completed tool with result
                        result_line = Text()
                        result_line.append(f"{ICONS['tool_done']} ", style="success")
                        result_line.append(f"{icon} ", style="tool")
                        result_line.append(self.current_tool, style="tool.name")

                        input_preview = _format_tool_input(self.current_tool, self.current_tool_input)
                        result_line.append(f"  {input_preview}", style="tool.input")
                        result_line.append(f"  ({_format_duration(duration)})", style="tool.time")

                        # Show output if meaningful
                        if event.content and event.content.strip():
                            output = _format_tool_output(event.content)
                            if output:
                                result_line.append(f"\n  {output}", style="tool.output")

                        console.print(result_line)
                        console.print()  # Add gap after tool execution

                    self.current_tool = None
                    self.current_tool_input = {}
                    self.tool_start_time = None

                    current_status = self._create_status_line("Thinking...")
                    live.update(self._create_view(user_input, current_status))

                elif event.type == "agent_transition":
                    if event.content:
                        # Flush before transition message
                        self._flush_segment()

                        # Parse routing decision
                        if "[Router] Routing to" in event.content:
                            # Extract agent name and reason
                            parts = event.content.replace("[Router] Routing to ", "").split(": ", 1)
                            agent = parts[0] if parts else "unknown"
                            reason = parts[1] if len(parts) > 1 else ""

                            route_text = Text()
                            route_text.append(f"{ICONS['route']} ", style="route")
                            route_text.append(agent, style="bold cyan")
                            if reason:
                                (
                                    route_text.append(f"  {reason[:60]}...", style="dim")
                                    if len(reason) > 60
                                    else route_text.append(f"  {reason}", style="dim")
                                )
                            console.print(route_text)
                        else:
                            self._update_final_response(event.content)
                            # Also treat as a segment to be displayed/flushed
                            if self.final_response:
                                # Only append if it's new content (avoid duplication if mixed with tokens)
                                if self.final_response not in self.streaming_content:
                                    self.streaming_content += self.final_response
                                    self.current_segment += self.final_response
                                    live.update(self._create_view(user_input, current_status))

                elif event.type == "message":
                    if event.content:
                        self._update_final_response(event.content)
                        # Also treat as a segment to be displayed/flushed
                        if self.final_response:
                            if self.final_response not in self.streaming_content:
                                self.streaming_content += self.final_response
                                self.current_segment += self.final_response
                                live.update(self._create_view(user_input, current_status))

                elif event.type == "permission_required":
                    self._flush_segment()
                    return event

                elif event.type == "complete":
                    self._flush_segment()
                    return event

                elif event.type == "error":
                    self._flush_segment()
                    error_text = Text()
                    error_text.append(f"{ICONS['tool_error']} ", style="error")
                    error_text.append(f"Error: {event.content}", style="error")
                    console.print(error_text)
                    return event

            # End of generator
            self._flush_segment()

        return None

    def _update_final_response(self, content: str) -> None:
        """Update final response, stripping agent prefixes and ignoring routing messages."""
        if not content:
            return
        # Skip intermediate routing messages
        if content.startswith("[Router] Routing to"):
            return
        # Strip agent prefixes
        if content.startswith("[Router] "):
            self.final_response = content[9:]
        elif content.startswith("[Initializer] "):
            self.final_response = content[14:]
        elif content.startswith("[Coding] "):
            self.final_response = content[9:]
        else:
            self.final_response = content

    def print_final_content(self):
        """Print accumulated content (streaming tokens or final response) as markdown."""
        # User Input header was printed at start.

        # If we have a final response but nothing was streamed (e.g. non-streaming router message),
        # we need to print it now.
        if self.final_response and not self.streaming_content:
            console.print(Markdown(self.final_response))
            console.print()

        # Flush any remaining segment just in case
        self._flush_segment()


def clear_last_prompt_lines(lines: int = 4):
    """Clear the last N lines of output (used to remove prompt artifacts)."""
    # Move cursor up N lines
    console.print(Control.move(0, -lines))
    # Clear from cursor to end of screen (J=0)
    # Using standard ANSI escape sequence for clear after cursor
    # Note: Rich's Control doesn't expose raw ANSI easily, so we use console.out directly
    # or rely on the fact that Control constructor takes codes.

    # \x1b[0J is "Erase in Display" (0 = cursor to end)
    sys.stdout.write("\x1b[0J")
    sys.stdout.flush()


def prompt_permission(message: str) -> bool:
    """
    Display permission dialog and get user approval.

    Args:
        message: The permission request message to display

    Returns:
        True if user approved, False otherwise
    """
    console.print()
    console.print(
        Panel(
            f"[warning]{message}[/warning]",
            title="[bold yellow]Permission Required[/bold yellow]",
            border_style="yellow",
        )
    )

    user_response = console.input("[prompt]Allow? (yes/no):[/prompt] ").strip().lower()
    is_approved = user_response in ("yes", "y", "true", "1")

    if is_approved:
        console.print("[success]Approved. Resuming...[/success]")
    else:
        console.print("[error]Denied. Continuing with error...[/error]")

    return is_approved


def print_session_complete():
    """Print session complete message."""
    console.print()
