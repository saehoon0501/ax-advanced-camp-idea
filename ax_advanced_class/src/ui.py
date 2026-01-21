"""
UI Helper Module

Pretty printing utilities for the CLI interface.
Uses Rich library for styled terminal output.
"""

import os
from typing import Optional

from rich.console import Console
from rich.control import Control
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.theme import Theme
from rich.table import Table
from rich.box import ROUNDED

from typing import AsyncGenerator

from ax_advanced_class.src.orchestrator import LongRunningOrchestrator
from ax_advanced_class.src.services import StreamEvent


VERSION = "0.1.0"

custom_theme = Theme(
    {
        "info": "dim red",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "tool": "bright_red",
        "thinking": "dim white",
        "prompt": "bold bright_red",
        "agent": "red",
        "accent": "bright_red",
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

    left_content = "\n[bold]Welcome to Incubation Camp![/bold]\n" f"{mascot}\n\n" f"[dim]{os.path.abspath(workspace)}[/dim]"

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
    console.rule(style="dim")
    console.print()
    console.rule(style="dim")

    console.print(Control.move(0, -2))

    prompt_text = "[prompt]>[/prompt] "
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
        console.print(f"  Initialized: {'[green]Yes[/green]' if state.get('is_initialized') else '[yellow]No[/yellow]'}")
        console.print(f"  Sessions: {state.get('session_count', 0)}")

        features = state.get("feature_list", [])
        if features:
            completed = sum(1 for f in features if f.get("passes", False))
            console.print(f"  Features: {completed}/{len(features)} completed")
    else:
        console.print("  [dim]No active project. Use /init to start.[/dim]")
    console.print()


class StreamingSession:
    """Manages streaming display state across multiple event generators."""

    def __init__(self):
        self.streaming_content = ""
        self.current_tool = None

    async def display_events(
        self, event_generator: AsyncGenerator[StreamEvent, None]
    ) -> Optional[StreamEvent]:
        """
        Display events from a generator until interrupted or complete.

        Args:
            event_generator: AsyncGenerator yielding StreamEvent objects

        Returns:
            The final event (permission_required, complete, or error) or None
        """
        with Live(console=console, refresh_per_second=10, transient=True) as live:
            live.update(Text("Thinking...", style="thinking"))

            async for event in event_generator:
                if event.type == "thinking":
                    live.update(Text("Thinking...", style="thinking"))

                elif event.type == "token":
                    self.streaming_content += event.content
                    live.update(Text(self.streaming_content[-500:], style="white"))

                elif event.type == "tool_call":
                    self.current_tool = event.metadata.get("tool_name", "unknown")
                    live.update(Text(f"Executing: {self.current_tool}", style="tool"))

                elif event.type == "tool_result":
                    if self.current_tool:
                        console.print(f"[tool]Tool:[/tool] {self.current_tool}")
                        if event.content:
                            console.print(f"[dim]{event.content}[/dim]")
                        console.print()
                    self.current_tool = None
                    live.update(Text("Thinking...", style="thinking"))

                elif event.type == "agent_transition":
                    # Show routing decisions with dim styling
                    if event.content:
                        console.print(f"[dim]{event.content}[/dim]")

                elif event.type == "message":
                    # Show agent messages with dim styling
                    if event.content:
                        console.print(f"[dim]{event.content}[/dim]")

                elif event.type == "permission_required":
                    return event

                elif event.type == "complete":
                    return event

                elif event.type == "error":
                    console.print(f"[error]Error: {event.content}[/error]")
                    return event

        return None

    def print_final_content(self):
        """Print accumulated streaming content as markdown."""
        if self.streaming_content:
            console.print()
            console.print(Markdown(self.streaming_content))


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
    console.print("[success]Session complete.[/success]")
    console.print()
