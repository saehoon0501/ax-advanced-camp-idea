"""
Long-Running Agent Harness - Main Entry Point

Based on Anthropic's "Building effective harnesses for long-running agents" article.
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

Interactive CLI for running the orchestrator with the two-agent
architecture (Initializer + Coding Agent).
"""

import os
import asyncio
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.theme import Theme

from ax_advanced_class.src.orchestrator import (
    create_orchestrator,
    LongRunningOrchestrator,
)
from ax_advanced_class.src.llm.bedrock_client import BedrockClient, LLMConfig
from ax_advanced_class.src.tools import (
    FileOperationTool,
    BashTool,
)
from ax_advanced_class.src.config.tool_permission_config import PermissionConfig


# Custom theme similar to Claude Code CLI
custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "tool": "yellow",
        "thinking": "dim white",
        "prompt": "bold blue",
        "agent": "magenta",
    }
)

console = Console(theme=custom_theme)


def create_llm(model_id: Optional[str] = None):
    """Create a language model instance using BedrockClient."""
    config = LLMConfig()
    if model_id:
        config = LLMConfig(model_id=model_id)
    client = BedrockClient(config=config)
    return client.get_core()


def create_tools(
    workspace_path: str = "./workspace",
) -> list:
    """Create tools for the agents with permission control."""
    config = PermissionConfig(
        workspace_root=os.path.abspath(workspace_path),
    )

    file_tool = FileOperationTool()
    bash_tool = BashTool(config=config)

    tools = []
    tools.extend(file_tool.get_langchain_tools())
    tools.extend(bash_tool.get_langchain_tools())

    return tools


def print_welcome():
    """Print the welcome banner."""
    console.print()
    console.print(
        Panel.fit(
            "[bold]Incubation Camp CLI[/bold]\n" "[dim]Long-running agent harness based on Anthropic's architecture[/dim]",
            border_style="blue",
        )
    )
    console.print()
    console.print("[dim]Commands:[/dim]")
    console.print("  [bold]/init[/bold] <name> <description>  - Initialize a new project")
    console.print("  [bold]/status[/bold]                     - Show current project status")
    console.print("  [bold]/run[/bold]                        - Run the next coding session")
    console.print("  [bold]/workspace[/bold] <path>           - Set workspace path")
    console.print("  [bold]exit[/bold] or [bold]quit[/bold]               - Exit the CLI")
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


def main():
    """Main CLI entry point - REPL loop."""
    print_welcome()

    # Default settings
    workspace = "./workspace"
    model_id = None

    # Project state
    project_name = None
    project_description = None
    orchestrator = None
    config = {"configurable": {"thread_id": "cli-session"}}

    while True:
        try:
            # Prompt with current workspace indicator
            workspace_name = os.path.basename(os.path.abspath(workspace))
            prompt_text = f"[prompt]{workspace_name}[/prompt] > "
            user_input = console.input(prompt_text).strip()

            if not user_input:
                continue

            # Exit commands
            if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
                console.print("[dim]Goodbye![/dim]")
                break

            # Help command
            if user_input.lower() in ("help", "/help", "?"):
                print_welcome()
                continue

            # Init command: /init <name> <description>
            if user_input.startswith("/init"):
                parts = user_input.split(maxsplit=2)
                if len(parts) < 3:
                    console.print("[error]Usage: /init <project_name> <description>[/error]")
                    continue

                project_name = parts[1]
                project_description = parts[2]

                console.print()
                console.print(f"[info]Initializing project:[/info] {project_name}")
                console.print(f"[dim]{project_description}[/dim]")

                # Create LLM and tools
                with console.status("[thinking]Setting up LLM and tools...[/thinking]"):
                    llm = create_llm(model_id=model_id)
                    tools = create_tools(
                        workspace_path=workspace,
                    )
                    os.makedirs(workspace, exist_ok=True)
                    orchestrator = create_orchestrator(llm=llm, tools=tools)

                console.print(f"[success]Ready![/success] Loaded {len(tools)} tools")
                console.print("[dim]Use /run to start the session[/dim]")
                console.print()
                continue

            # Status command
            if user_input.lower() in ("/status", "status"):
                if orchestrator:
                    print_status(orchestrator, config, workspace)
                else:
                    console.print("[dim]No project initialized. Use /init first.[/dim]")
                continue

            # Workspace command
            if user_input.startswith("/workspace"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    console.print(f"[info]Current workspace:[/info] {os.path.abspath(workspace)}")
                else:
                    workspace = parts[1]
                    console.print(f"[info]Workspace set to:[/info] {os.path.abspath(workspace)}")
                continue

            # Run command
            if user_input.lower() in ("/run", "run"):
                if not orchestrator or not project_name:
                    console.print("[error]No project initialized. Use /init first.[/error]")
                    continue

                console.print()
                console.print(f"[info]Starting session for:[/info] {project_name}")

                # Run the async streaming session
                asyncio.run(
                    run_streaming_session(
                        orchestrator=orchestrator,
                        project_name=project_name,
                        project_description=project_description,
                        repository_path=workspace,
                    )
                )
                continue

            # If no command matched, treat as a direct message (future: chat mode)
            console.print("[dim]Unknown command. Type /help for available commands.[/dim]")

        except KeyboardInterrupt:
            console.print()
            console.print("[warning]Interrupted. Type 'exit' to quit.[/warning]")
            continue

        except Exception as e:
            console.print(f"[error]Error: {e}[/error]")
            continue


if __name__ == "__main__":
    main()
