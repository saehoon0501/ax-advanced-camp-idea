"""
Coding Agent

Responsible for incrementally implementing features one at a time.
Uses LangGraph's create_agent for the agent loop.

Based on Anthropic's article - The Coding Agent:
- Operates with incremental feature-by-feature progression
- Produces clean, mergeable code at session end
- Performs comprehensive testing before marking features complete
- Commits with descriptive messages for git-based checkpointing

Uses @dynamic_prompt middleware for cache-optimized dynamic prompting:
- Static system prompt is cached (placed first)
- Dynamic feature/session context is appended via middleware (placed last)
"""

from typing import Annotated, Any, Optional, TypedDict
import operator

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage
from langgraph.graph.state import CompiledStateGraph

from ax_advanced_class.src.prompts import coding_agent_dynamic_prompt
from ax_advanced_class.src.tools import BashTool, FileOperationTool, TodoWriteTool


# =============================================================================
# Agent State Definition
# =============================================================================


class CodingAgentState(TypedDict):
    """
    State for the Coding Agent.

    This TypedDict defines the agent's internal state, separate from OrchestratorState.
    The todo_list is managed by the agent via TodoWriteTool.
    """

    messages: Annotated[list[BaseMessage], operator.add]
    todo_list: list[dict]  # Agent's task tracking list


def create_coding_agent(
    llm: Any,
    middleware: Optional[list] = None,
) -> CompiledStateGraph:
    """
    Create a Coding Agent using LangGraph's create_agent.

    The Coding Agent is responsible for:
    1. Reading current state (git logs, progress file, feature list)
    2. Selecting the next high-priority feature
    3. Implementing the feature (code + tests)
    4. Running E2E tests to verify
    5. Committing changes and updating progress

    Args:
        llm: The language model to use (ChatModel instance)
        middleware: Optional list of middleware (defaults to coding_agent_dynamic_prompt)

    Returns:
        Compiled agent graph (CompiledStateGraph)
    """
    # Collect all tools
    tools = []
    tools.extend(BashTool().get_langchain_tools())
    tools.extend(FileOperationTool().get_langchain_tools())
    tools.extend(TodoWriteTool().get_langchain_tools())

    # Use default dynamic prompt middleware if none provided
    agent_middleware = middleware if middleware is not None else [coding_agent_dynamic_prompt]

    return create_agent(
        model=llm,
        tools=tools,
        middleware=agent_middleware,
        name="coding_agent",
        state_schema=CodingAgentState,
    )
