"""
Initializer Agent

Responsible for setting up the foundation for a long-running project.
Uses LangGraph's create_agent for the agent loop.

Based on Anthropic's article - The Initializer Agent:
- Sets up the environment on first run
- Creates init.sh script for dev server
- Creates claude-progress.txt for logging completed work
- Creates feature_list.json with 50-200 granular features
- Makes initial git commit documenting foundational setup

Uses @dynamic_prompt middleware for cache-optimized dynamic prompting:
- Static system prompt is cached (placed first)
- Dynamic project context is appended via middleware (placed last)
"""

from typing import Any, Optional

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

from ax_advanced_class.src.prompts import initializer_agent_dynamic_prompt
from ax_advanced_class.src.tools import ShellTool, FileOperationTool


def create_initializer_agent(
    llm: Any,
    middleware: Optional[list] = None,
) -> CompiledStateGraph:
    """
    Create an Initializer Agent using LangGraph's create_agent.

    The Initializer Agent is responsible for:
    1. Analyzing the user's project request
    2. Breaking it down into specific, testable features (50-200)
    3. Creating feature_list.json with proper structure
    4. Initializing git repository
    5. Creating claude-progress.txt for tracking
    6. Setting up init.sh for dev server

    Args:
        llm: The language model to use (ChatModel instance)
        tools: Optional list of tools (file operations, git, etc.)
        middleware: Optional list of middleware (defaults to initializer_agent_dynamic_prompt)

    Returns:
        Compiled agent graph (CompiledStateGraph)
    """
    tools = [ShellTool().get_langchain_tools()]
    tools.extend(FileOperationTool().get_langchain_tools())
    # Use default dynamic prompt middleware if none provided
    agent_middleware = (
        middleware if middleware is not None else [initializer_agent_dynamic_prompt]
    )

    return create_agent(
        model=llm,
        tools=tools,
        middleware=agent_middleware,
        name="initializer_agent",
    )


class InitializerAgentState:
    """
    State management for the Initializer Agent.

    Tracks:
    - Project metadata (name, description)
    - Generated feature list
    - Initialization progress
    """

    def __init__(self):
        self.project_name: Optional[str] = None
        self.project_description: Optional[str] = None
        self.feature_list: list = []
        self.is_git_initialized: bool = False
        self.is_progress_file_created: bool = False
        self.is_init_script_created: bool = False

    def is_complete(self) -> bool:
        """Check if initialization is complete."""
        return (
            self.feature_list
            and self.is_git_initialized
            and self.is_progress_file_created
        )

    def to_dict(self) -> dict:
        """Convert state to dictionary for serialization."""
        return {
            "project_name": self.project_name,
            "project_description": self.project_description,
            "feature_count": len(self.feature_list),
            "is_git_initialized": self.is_git_initialized,
            "is_progress_file_created": self.is_progress_file_created,
            "is_init_script_created": self.is_init_script_created,
            "is_complete": self.is_complete(),
        }
