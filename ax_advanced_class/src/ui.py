"""
UI Helper Module

Pretty printing utilities for the CLI interface.
Uses Rich library for styled terminal output.
"""

import os

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.theme import Theme
from rich.table import Table
from rich.box import ROUNDED

from ax_advanced_class.src.orchestrator import LongRunningOrchestrator


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

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(width=95)
    table.add_column()
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


async def run_streaming_session(
    orchestrator: LongRunningOrchestrator,
    project_name: str,
    project_description: str,
    repository_path: str,
):
    """Run a streaming session and display events in Claude Code style."""
    console.print()

    current_tool = None
    streaming_content = ""

    with Live(console=console, refresh_per_second=10, transient=True) as live:
        live.update(Text("Thinking...", style="thinking"))

        async for event in orchestrator.astream_events(
            project_name=project_name,
            project_description=project_description,
            repository_path=repository_path,
        ):
            event_type = event.get("event", "")
            node = event.get("langgraph_node") or event.get("name") or ""
            data = event.get("data", {}) or {}

            # Handle tool start
            if event_type == "on_tool_start":
                tool_name = data.get("name") or event.get("name") or "unknown"
                tool_input = data.get("input", {})
                current_tool = tool_name

                # Format tool input for display
                input_preview = str(tool_input)[:100]
                if len(str(tool_input)) > 100:
                    input_preview += "..."

                live.update(Text(f"Executing: {tool_name}", style="tool"))

            # Handle tool end
            elif event_type == "on_tool_end":
                output = data.get("output", "")
                output_preview = str(output)[:200] if output else ""
                if len(str(output)) > 200:
                    output_preview += "..."

                if current_tool:
                    console.print(f"[tool]Tool:[/tool] {current_tool}")
                    if output_preview:
                        console.print(f"[dim]{output_preview}[/dim]")
                    console.print()
                current_tool = None
                live.update(Text("Thinking...", style="thinking"))

            # Handle streaming tokens
            elif event_type in ("on_chat_model_stream", "on_llm_stream"):
                chunk = data.get("chunk")
                if chunk:
                    text = ""
                    if hasattr(chunk, "content"):
                        text = chunk.content
                    elif isinstance(chunk, dict):
                        text = chunk.get("content", "")
                    elif isinstance(chunk, str):
                        text = chunk

                    if text:
                        streaming_content += text
                        live.update(Text(streaming_content[-500:], style="white"))

            # Handle chain events for agent transitions
            elif event_type == "on_chain_start":
                if node in ("initializer", "coding", "router"):
                    console.print(f"[agent]Agent:[/agent] {node}")

    # Print final content if any
    if streaming_content:
        console.print()
        console.print(Markdown(streaming_content))

    console.print()
    console.print("[success]Session complete.[/success]")
    console.print()
