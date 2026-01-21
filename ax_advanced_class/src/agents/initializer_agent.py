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

from typing import Annotated, Any, Optional, TypedDict
import operator
from enum import Enum

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage
from langgraph.graph.state import CompiledStateGraph

from ax_advanced_class.src.prompts import initializer_agent_dynamic_prompt
from ax_advanced_class.src.tools import BashTool, FileOperationTool, TodoWriteTool


# =============================================================================
# Agent State Definition
# =============================================================================
class TodoStatus(str, Enum):
    """Status of a todo item for task tracking."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TodoItem(TypedDict):
    """
    A single todo item for task tracking.

    Based on Claude Code's TodoWrite tool schema.
    """

    content: str  # Imperative form: "Create feature_list.json"
    activeForm: str  # Present continuous: "Creating feature_list.json"
    status: TodoStatus  # TodoStatus enum value


class InitializerAgentState(TypedDict):
    """
    State for the Initializer Agent.

    This TypedDict defines the agent's internal state, separate from OrchestratorState.
    The todo_list is managed by the agent via TodoWriteTool.
    """

    messages: Annotated[list[BaseMessage], operator.add]
    todo_list: list[dict]  # Agent's task tracking list


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
        middleware: Optional list of middleware (defaults to initializer_agent_dynamic_prompt)

    Returns:
        Compiled agent graph (CompiledStateGraph)
    """
    # Collect all tools
    tools = []
    tools.extend(BashTool().get_langchain_tools())
    tools.extend(FileOperationTool().get_langchain_tools())
    tools.extend(TodoWriteTool().get_langchain_tools())

    # Use default dynamic prompt middleware if none provided
    agent_middleware = middleware if middleware is not None else [initializer_agent_dynamic_prompt]

    return create_agent(
        model=llm,
        tools=tools,
        middleware=agent_middleware,
        name="initializer_agent",
        state_schema=InitializerAgentState,
    )
