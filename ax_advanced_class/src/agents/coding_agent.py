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

from typing import Any, Optional

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

from ax_advanced_class.src.prompts import coding_agent_dynamic_prompt
from ax_advanced_class.src.tools import BashTool, FileOperationTool


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
        tools: Optional list of tools (file ops, git, shell, etc.)
        middleware: Optional list of middleware (defaults to coding_agent_dynamic_prompt)

    Returns:
        Compiled agent graph (CompiledStateGraph)
    """
    tools = [BashTool().get_langchain_tools()]
    tools.extend(FileOperationTool().get_langchain_tools())

    # Use default dynamic prompt middleware if none provided
    agent_middleware = middleware if middleware is not None else [coding_agent_dynamic_prompt]

    return create_agent(
        model=llm,
        tools=tools,
        middleware=agent_middleware,
        name="coding_agent",
    )


class CodingAgentState:
    """
    State management for the Coding Agent.

    Tracks:
    - Current feature being worked on
    - Session progress
    - Test results
    - Commit history
    """

    def __init__(self):
        self.current_feature_id: Optional[str] = None
        self.current_feature_description: Optional[str] = None
        self.session_started: bool = False
        self.dev_server_running: bool = False
        self.tests_passed: bool = False
        self.changes_committed: bool = False
        self.progress_updated: bool = False

    def is_session_complete(self) -> bool:
        """Check if the current session is complete."""
        return self.tests_passed and self.changes_committed and self.progress_updated

    def reset_for_new_session(self):
        """Reset state for a new session."""
        self.session_started = False
        self.dev_server_running = False
        self.tests_passed = False
        self.changes_committed = False
        self.progress_updated = False

    def to_dict(self) -> dict:
        """Convert state to dictionary for serialization."""
        return {
            "current_feature_id": self.current_feature_id,
            "current_feature_description": self.current_feature_description,
            "session_started": self.session_started,
            "dev_server_running": self.dev_server_running,
            "tests_passed": self.tests_passed,
            "changes_committed": self.changes_committed,
            "progress_updated": self.progress_updated,
            "is_session_complete": self.is_session_complete(),
        }
