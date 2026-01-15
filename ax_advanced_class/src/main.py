"""
Long-Running Agent Harness - Main Entry Point

Based on Anthropic's "Building effective harnesses for long-running agents" article.
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

This is the main entry point for running the orchestrator with the two-agent
architecture (Initializer + Coding Agent).
"""

import os
import sys
import argparse
from typing import Optional

from ax_advanced_class.src.orchestrator import create_orchestrator, LongRunningOrchestrator
from ax_advanced_class.src.llm.bedrock_client import BedrockClient, LLMConfig
from ax_advanced_class.src.tools import (
    create_default_tools,
    PermissionLevel,
    PermissionConfig,
    FileOperationTool,
    GitTool,
    ShellTool,
)


def create_llm(model_id: Optional[str] = None):
    """
    Create a language model instance using BedrockClient.

    Args:
        model_id: Optional model ID override

    Returns:
        ChatBedrock instance
    """
    config = LLMConfig()
    if model_id:
        config = LLMConfig(model_id=model_id)

    client = BedrockClient(config=config)
    return client.get_core()


def create_tools(
    workspace_path: str = "./workspace",
    permission_level: PermissionLevel = PermissionLevel.STANDARD,
) -> list:
    """
    Create tools for the agents with permission control.

    Args:
        workspace_path: The root workspace path
        permission_level: Permission level for operations

    Returns:
        List of LangChain tools
    """
    config = PermissionConfig(
        workspace_root=os.path.abspath(workspace_path),
        permission_level=permission_level,
    )

    # Create tool instances
    file_tool = FileOperationTool(config=config)
    git_tool = GitTool(config=config)
    shell_tool = ShellTool(config=config)

    # Collect all LangChain tools
    tools = []
    tools.extend(file_tool.get_langchain_tools())
    tools.extend(git_tool.get_langchain_tools())
    tools.extend(shell_tool.get_langchain_tools())

    return tools


def run_orchestrator(
    project_name: str,
    project_description: str,
    repository_path: str = "./workspace",
    model_id: Optional[str] = None,
    permission_level: str = "standard",
    stream: bool = False,
) -> None:
    """
    Run the orchestrator with the given project parameters.

    Args:
        project_name: Name of the project
        project_description: Full description of what to build
        repository_path: Path to the git repository
        model_id: Optional model ID override
        permission_level: Permission level (restricted, standard, elevated)
        stream: Whether to stream output events
    """
    # Parse permission level
    perm_level = PermissionLevel(permission_level.lower())

    # Create LLM
    print(f"Initializing LLM...")
    llm = create_llm(model_id=model_id)

    # Create tools
    print(f"Creating tools with {perm_level.value} permission level...")
    tools = create_tools(
        workspace_path=repository_path,
        permission_level=perm_level,
    )
    print(f"  Loaded {len(tools)} tools")

    # Ensure workspace exists
    os.makedirs(repository_path, exist_ok=True)

    # Create orchestrator
    print(f"Creating orchestrator...")
    orchestrator = create_orchestrator(llm=llm, tools=tools)

    # Run the orchestrator
    print(f"\n{'='*60}")
    print(f"Starting project: {project_name}")
    print(f"Repository: {os.path.abspath(repository_path)}")
    print(f"Permission level: {perm_level.value}")
    print(f"{'='*60}\n")

    if stream:
        for event in orchestrator.stream(
            project_name=project_name,
            project_description=project_description,
            repository_path=repository_path,
        ):
            # Print event info
            for node_name, node_output in event.items():
                print(f"\n[{node_name}]")
                if "messages" in node_output:
                    for msg in node_output["messages"]:
                        content = str(msg.content) if hasattr(msg, 'content') else str(msg)
                        print(f"  {content[:500]}...")
                if "next_agent" in node_output:
                    print(f"  Next: {node_output['next_agent']}")
    else:
        result = orchestrator.invoke(
            project_name=project_name,
            project_description=project_description,
            repository_path=repository_path,
        )

        print(f"\n{'='*60}")
        print(f"Orchestration complete!")
        print(f"{'='*60}")
        print(f"Sessions: {result.get('session_count', 0)}")
        print(f"Features: {len(result.get('feature_list', []))}")
        print(f"Initialized: {result.get('is_initialized', False)}")

        # Print feature summary
        features = result.get('feature_list', [])
        if features:
            completed = sum(1 for f in features if f.get('passes', False))
            print(f"Completed features: {completed}/{len(features)}")


def main():
    """
    Main entry point for the Long-Running Agent Harness.

    Usage:
        python main.py run --name "My Project" --description "Build a web app"
        python main.py run --name "My Project" --description "Build a web app" --stream
        python main.py run --name "My Project" --description "Build a web app" --permission elevated
    """
    parser = argparse.ArgumentParser(
        description="Long-Running Agent Harness based on Anthropic's architecture"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the orchestrator")
    run_parser.add_argument(
        "--name", "-n",
        required=True,
        help="Project name"
    )
    run_parser.add_argument(
        "--description", "-d",
        required=True,
        help="Project description"
    )
    run_parser.add_argument(
        "--repository", "-r",
        default="./workspace",
        help="Repository path (default: ./workspace)"
    )
    run_parser.add_argument(
        "--model", "-m",
        default=None,
        help="Model ID override"
    )
    run_parser.add_argument(
        "--permission", "-p",
        default="standard",
        choices=["restricted", "standard", "elevated"],
        help="Permission level for tools (default: standard)"
    )
    run_parser.add_argument(
        "--stream", "-s",
        action="store_true",
        help="Stream output events"
    )

    args = parser.parse_args()

    if args.command == "run":
        run_orchestrator(
            project_name=args.name,
            project_description=args.description,
            repository_path=args.repository,
            model_id=args.model,
            permission_level=args.permission,
            stream=args.stream,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
