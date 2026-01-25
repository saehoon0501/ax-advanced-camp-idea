"""
Long-Running Agent Harness - Main Entry Point

Based on Anthropic's "Building effective harnesses for long-running agents" article.
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

Interactive CLI for running the orchestrator with the two-agent
architecture (Initializer + Coding Agent).
"""

import os
import sys
import asyncio
import uuid
from typing import Optional

# Suppress noisy urllib3 exception in Python 3.13
original_unraisablehook = sys.unraisablehook


def _handle_unraisable(unraisable):
    # Suppress ValueError: I/O operation on closed file from urllib3/http.client
    if unraisable.exc_type is ValueError and str(unraisable.exc_value) == "I/O operation on closed file":
        return
    original_unraisablehook(unraisable)


sys.unraisablehook = _handle_unraisable

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
    print_prompt,
    StreamingSession,
    prompt_permission,
    print_session_complete,
)
from ax_advanced_class.src.services import AgentStreamingService


def load_dotenv() -> None:
    """Load environment variables from a local .env file if present."""
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
    ]
    seen = set()
    for path in candidates:
        path = os.path.abspath(path)
        if path in seen or not os.path.isfile(path):
            continue
        seen.add(path)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("export "):
                        line = line[7:].strip()
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                        value = value[1:-1]
                    if key and key not in os.environ:
                        os.environ[key] = value
        except OSError:
            continue


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
    """Main CLI entry point - Stateful REPL loop."""
    load_dotenv()
    # Default settings
    workspace = "./workspace"

    print_welcome(workspace)

    # Initialize orchestrator at startup
    with console.status("[thinking]Setting up LLM and orchestrator...[/thinking]"):
        llm = create_llm()
        os.makedirs(workspace, exist_ok=True)
        orchestrator = create_orchestrator(llm=llm)

    console.print("[success]Ready![/success]")
    console.print()

    # Create a single session for the entire run
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    console.print(f"[dim]Session: {session_id}[/dim]")
    console.print()

    # Create service once with persistent config
    service = AgentStreamingService(orchestrator=orchestrator, config=config)

    # Conversation history - only user inputs and final responses
    conversation_history: list[dict] = []

    interrupt_count = 0

    while True:
        try:
            user_input = print_prompt()
            if user_input == "__interrupt__":
                console.print()
                interrupt_count += 1
                if interrupt_count >= 2:
                    console.print("[dim]Goodbye![/dim]")
                    break
                console.print("[warning]Press Ctrl+C again to exit.[/warning]")
                continue
            interrupt_count = 0

            if not user_input:
                continue

            # Exit commands
            if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
                console.print("[dim]Goodbye![/dim]")
                break

            # Clear the prompt lines to let the Live display take over
            from ax_advanced_class.src.ui import clear_last_prompt_lines

            clear_last_prompt_lines()

            # Run session
            console.print()

            async def run_session():
                session = StreamingSession()

                # Stream with the persistent service, passing conversation history
                event_generator = service.astream(
                    user_message=user_input,
                    message_history=conversation_history,
                )
                final_event = await session.display_events(event_generator, user_input)

                # Handle permission requests with resume loop
                while final_event and final_event.type == "permission_required":
                    is_approved = prompt_permission(final_event.content)
                    resume_generator = service.aresume(is_approved)
                    final_event = await session.display_events(resume_generator, user_input)

                # Print final content and completion message
                print_session_complete()

            asyncio.run(run_session())
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
    # Best-effort cleanup to avoid noisy urllib3 shutdown errors.
    try:
        if hasattr(llm, "client") and llm.client:
            llm.client.close()
        if hasattr(llm, "bedrock_client") and llm.bedrock_client:
            llm.bedrock_client.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
