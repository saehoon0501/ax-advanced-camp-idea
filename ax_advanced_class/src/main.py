"""
Long-Running Agent Harness - Main Entry Point

Based on Anthropic's "Building effective harnesses for long-running agents" article.
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

Interactive CLI for running the orchestrator with the two-agent
architecture (Initializer + Coding Agent).
"""

import os
import asyncio
import uuid
from typing import Optional

from ax_advanced_class.src.orchestrator import create_orchestrator
from ax_advanced_class.src.llm.bedrock_client import BedrockClient, LLMConfig
from ax_advanced_class.src.tools import (
    FileOperationTool,
    BashTool,
)
from ax_advanced_class.src.config.tool_permission_config import PermissionConfig
from ax_advanced_class.src.ui import (
    console,
    print_welcome,
    print_status,
    run_streaming_session,
    print_prompt,
)


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


def main():
    """Main CLI entry point - REPL loop."""
    # Default settings
    workspace = "./workspace"

    print_welcome(workspace)
    model_id = None

    # Project state
    project_name = None
    project_description = None
    orchestrator = None
    config = {"configurable": {"thread_id": "cli-session"}}
    interrupt_count = 0

    while True:
        try:
            user_input = print_prompt()
            interrupt_count = 0

            if not user_input:
                continue

            # Exit commands
            if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
                console.print("[dim]Goodbye![/dim]")
                break

            # Help command
            if user_input.lower() in ("help", "/help", "?"):
                print_welcome(workspace)
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

            # Run prompt(default)
            console.print()
            console.print(f"[info]Starting session for:[/info] {project_name}")

            # Generate unique thread_id for this session
            thread_id = f"session_{uuid.uuid4().hex[:8]}"
            config = {"configurable": {"thread_id": thread_id}}
            console.print(f"[dim]Thread ID: {thread_id}[/dim]")

            # Run the async streaming session
            asyncio.run(
                run_streaming_session(
                    orchestrator=orchestrator,
                    project_name=project_name,
                    project_description=project_description,
                    repository_path=workspace,
                    config=config,
                )
            )
            continue

        except KeyboardInterrupt:
            console.print()
            interrupt_count += 1
            if interrupt_count >= 2:
                console.print("[dim]Goodbye![/dim]")
                break
            console.print("[warning]Press Ctrl+C again to exit.[/warning]")
            continue

        except Exception as e:
            console.print(f"[error]Error: {e}[/error]")
            continue


if __name__ == "__main__":
    main()
