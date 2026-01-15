"""
Coding Agent

Responsible for incrementally implementing features one at a time.
Uses LangGraph's create_react_agent for the agent loop.

Based on Anthropic's article - The Coding Agent:
- Operates with incremental feature-by-feature progression
- Produces clean, mergeable code at session end
- Performs comprehensive testing before marking features complete
- Commits with descriptive messages for git-based checkpointing
"""

from typing import Any, Optional, Sequence, Callable

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

from ax_advanced_class.src.prompts.coding_agent_prompt import CODING_AGENT_SYSTEM_PROMPT


def create_coding_agent(
    llm: Any,
    tools: Optional[Sequence[BaseTool | Callable | dict[str, Any]]] = None,
) -> CompiledStateGraph:
    """
    Create a Coding Agent using LangGraph's create_react_agent.

    The Coding Agent is responsible for:
    1. Reading current state (git logs, progress file, feature list)
    2. Selecting the next high-priority feature
    3. Implementing the feature (code + tests)
    4. Running E2E tests to verify
    5. Committing changes and updating progress

    Args:
        llm: The language model to use (ChatModel instance)
        tools: Optional list of tools (file ops, git, shell, etc.)

    Returns:
        Compiled agent graph (CompiledStateGraph)
    """
    return create_react_agent(
        model=llm,
        tools=tools or [],
        prompt=CODING_AGENT_SYSTEM_PROMPT,
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
        return (
            self.tests_passed
            and self.changes_committed
            and self.progress_updated
        )

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


class SessionLifecycle:
    """
    Manages the lifecycle of a coding session.

    Based on Anthropic's recommended patterns:
    1. Start: Read state, run smoke tests
    2. Work: Implement feature, run tests
    3. End: Commit, update progress, leave notes

    From the article:
    "Each session follows:
    1. Run `pwd` to confirm working directory
    2. Read progress files and git logs
    3. Select highest-priority incomplete feature
    4. Implement incrementally
    5. Verify end-to-end functionality
    6. Commit with progress updates"
    """

    PHASE_START = "start"
    PHASE_WORK = "work"
    PHASE_END = "end"

    def __init__(self):
        self.current_phase = self.PHASE_START
        self.smoke_test_passed: bool = False
        self.feature_implemented: bool = False
        self.e2e_test_passed: bool = False

    def advance_phase(self) -> str:
        """Advance to the next phase if conditions are met."""
        if self.current_phase == self.PHASE_START and self.smoke_test_passed:
            self.current_phase = self.PHASE_WORK
        elif self.current_phase == self.PHASE_WORK and self.e2e_test_passed:
            self.current_phase = self.PHASE_END
        return self.current_phase

    def get_phase_instructions(self) -> str:
        """Get instructions for the current phase."""
        instructions = {
            self.PHASE_START: """
START PHASE (Recovery & Orientation):
1. Run `pwd` to see your working directory
2. Read git logs: `git log --oneline -10`
3. Read claude-progress.txt to understand what happened
4. Read feature_list.json to see all features
5. Run init.sh to start the dev server
6. Run basic smoke test to verify the app works
""",
            self.PHASE_WORK: """
WORK PHASE (Feature Implementation):
1. Select ONE feature where passes=false (highest priority)
2. Work ONLY on that feature
3. Implement it completely (code + tests + docs)
4. Test it end-to-end (like a real user would)
5. Only mark passes=true after E2E test succeeds
""",
            self.PHASE_END: """
END PHASE (Commit & Handoff):
1. Commit your work with clear message
2. Update claude-progress.txt with what you did
3. Ensure the app is in a working state
4. Leave clear notes for the next agent
5. Update feature_list.json if feature is complete
""",
        }
        return instructions.get(self.current_phase, "")
