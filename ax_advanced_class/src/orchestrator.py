"""
Long-Running Agent Orchestrator

Based on Anthropic's "Building effective harnesses for long-running agents" article.
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

Implements a two-agent architecture using LangGraph:
- Initializer Agent: Sets up project foundation (feature list, progress tracking)
- Coding Agent: Iteratively implements features one at a time

Key patterns from the article:
1. Feature list tracking with structured JSON (50-200 features)
2. Git-based checkpointing for recovery
3. Progress tracking for session continuity
4. Incremental feature-by-feature implementation
"""

from typing import Annotated, TypedDict, Literal, Optional, Any
from enum import Enum
from datetime import datetime
import json
import os

from langgraph.graph import END, StateGraph, START
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator

from ax_advanced_class.src.prompts import (
    coding_agent_dynamic_prompt,
    initializer_agent_dynamic_prompt,
)
from ax_advanced_class.src.agents import (
    create_coding_agent,
    create_initializer_agent,
)

# =============================================================================
# State Definitions
# =============================================================================


class FeatureStatus(str, Enum):
    """Status of a feature in the feature list."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Feature(TypedDict):
    """
    A single feature in the feature list.

    Based on the article's recommendation for structured JSON tracking
    with 50-200 granular features.
    """

    id: str
    category: str  # functional, ui, performance, security
    description: str
    priority: str  # high, medium, low
    steps: list[str]
    passes: bool
    dependencies: list[str]


class ProgressEntry(TypedDict):
    """A single entry in the progress log (claude-progress.txt)."""

    timestamp: str
    agent: str  # initializer or coding
    action: str
    details: str
    commit_hash: Optional[str]


class OrchestratorState(TypedDict):
    """
    State managed by the orchestrator across agent sessions.

    This state bridges context windows between sessions, providing:
    - Feature list for tracking project requirements (persisted to feature_list.json)
    - Progress log for session continuity (persisted to claude-progress.txt)
    - Current feature being worked on
    - Git state for recovery

    Key insight from article: "Each new session begins with no memory of what came before"
    so we persist state through structured artifacts.
    """

    # Conversation messages (accumulates across turns)
    messages: Annotated[list[BaseMessage], operator.add]

    # Project metadata
    project_name: str
    project_description: str
    repository_path: str

    # Feature tracking (persisted to feature_list.json)
    feature_list: list[Feature]
    current_feature_id: Optional[str]

    # Progress tracking (persisted to claude-progress.txt)
    progress_log: list[ProgressEntry]

    # Session state
    is_initialized: bool
    session_count: int
    last_commit_hash: Optional[str]

    # Orchestrator routing
    next_agent: Optional[str]
    should_continue: bool

    # Error handling
    last_error: Optional[str]


# =============================================================================
# Agent Routing
# =============================================================================


class AgentRoute(str, Enum):
    """Possible routing destinations for the orchestrator."""

    INITIALIZER = "initializer"
    CODING = "coding"
    FINISH = "__end__"


# =============================================================================
# Orchestrator Implementation
# =============================================================================


class LongRunningOrchestrator:
    """
    Orchestrator for long-running coding agent sessions.

    Based on Anthropic's recommended patterns:
    1. Initializer agent handles setup (feature list, progress tracking)
    2. Coding agent works incrementally (one feature per session)
    3. State is persisted between sessions via git and progress files

    Architecture:
    ```
    START -> router -> [initializer|coding] -> router -> ... -> END
    ```

    The router decides which agent to invoke based on:
    - Not initialized? -> Initializer
    - All features complete? -> END
    - Otherwise -> Coding Agent
    """

    def __init__(
        self,
        llm: Any,
        checkpointer: Optional[Any] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            llm: The language model to use for agents
            tools: Optional list of tools (file ops, git, shell, etc.)
            checkpointer: Optional LangGraph checkpointer for state persistence
        """
        self.llm = llm
        self.checkpointer = checkpointer or MemorySaver()

        self.initializer_agent = create_initializer_agent(
            self.llm, [initializer_agent_dynamic_prompt]
        )
        self.coding_agent = create_coding_agent(self.llm, [coding_agent_dynamic_prompt])

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph:
        """
        Build the LangGraph workflow for orchestration.

        Graph structure:
        ```
        START
          |
          v
        router -----> END (if all features complete)
          |
          +---> initializer (if not initialized)
          |         |
          |         v
          |      router
          |
          +---> coding (if initialized, features remaining)
                    |
                    v
                 router
        ```
        """
        workflow = StateGraph(OrchestratorState)

        # Add nodes
        workflow.add_node("router", self._router_node)
        workflow.add_node("initializer", self._initializer_node)
        workflow.add_node("coding", self._coding_node)

        # Entry point
        workflow.add_edge(START, "router")

        # Conditional routing from router
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                AgentRoute.INITIALIZER: "initializer",
                AgentRoute.CODING: "coding",
                AgentRoute.FINISH: END,
            },
        )

        # After agents complete, route back to router for next decision
        workflow.add_edge("initializer", "router")
        workflow.add_edge("coding", "router")

        return workflow.compile(checkpointer=self.checkpointer)

    def _load_feature_list(self, repository_path: str) -> list[Feature]:
        """
        Load feature list from file.

        The agents write feature_list.json to the repository.
        This method reads it to sync state with actual files.
        """
        feature_file = os.path.join(repository_path, "feature_list.json")
        if os.path.exists(feature_file):
            try:
                with open(feature_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _check_progress_file(self, repository_path: str) -> bool:
        """Check if progress file exists (indicates initialization is done)."""
        progress_file = os.path.join(repository_path, "claude-progress.txt")
        return os.path.exists(progress_file)

    def _router_node(self, state: OrchestratorState) -> dict:
        """
        Router node that decides which agent should act next.

        Decision logic (from the article):
        1. If not initialized -> Initializer Agent
           "Sets up the environment on first run"
        2. If all features complete -> Finish
           "Prevents premature project completion"
        3. Otherwise -> Coding Agent
           "Subsequent sessions operate with incremental feature-by-feature progression"
        """
        repository_path = state.get("repository_path", "./workspace")

        # Sync feature_list from file (agents write to files)
        file_feature_list = self._load_feature_list(repository_path)
        has_progress_file = self._check_progress_file(repository_path)

        # Check if project is initialized
        # Consider initialized if progress file exists OR is_initialized is True
        is_initialized = state.get("is_initialized", False) or has_progress_file

        if not is_initialized:
            return {
                "next_agent": AgentRoute.INITIALIZER,
                "should_continue": True,
            }

        # Use feature list from file if available, otherwise from state
        feature_list = (
            file_feature_list if file_feature_list else state.get("feature_list", [])
        )

        # Check if all features are complete
        if feature_list:
            all_complete = all(f.get("passes", False) for f in feature_list)
            if all_complete:
                return {
                    "next_agent": AgentRoute.FINISH,
                    "should_continue": False,
                    "feature_list": feature_list,  # Update state with file contents
                }

            # Continue with coding agent
            return {
                "next_agent": AgentRoute.CODING,
                "should_continue": True,
                "feature_list": feature_list,  # Update state with file contents
                "is_initialized": True,
            }

        # No features yet but initialized - something went wrong or initialization incomplete
        # Give it one more try with coding agent, which will detect empty features
        if state.get("session_count", 0) > 2:
            # Prevent infinite loop - finish if we've tried too many times
            return {
                "next_agent": AgentRoute.FINISH,
                "should_continue": False,
            }

        return {
            "next_agent": AgentRoute.CODING,
            "should_continue": True,
            "is_initialized": True,
        }

    def _route_decision(self, state: OrchestratorState) -> AgentRoute:
        """Extract routing decision from state."""
        return state.get("next_agent", AgentRoute.FINISH)

    def _initializer_node(self, state: OrchestratorState) -> dict:
        """
        Initializer agent node.

        From the article - Initializer Agent responsibilities:
        1. Create init.sh script for dev server
        2. Create claude-progress.txt for logging completed work
        3. Create feature_list.json with 50-200 granular features
        4. Initial git commit documenting foundational file setup

        Uses @dynamic_prompt middleware - context is passed via runtime.context
        """
        # Prepare input message (minimal - dynamic content comes from middleware)
        input_message = HumanMessage(content="Initialize the project.")

        # Pass dynamic context via config for @dynamic_prompt middleware
        # The middleware will append project-specific context to the static system prompt
        agent_config = {
            "recursion_limit": 100,
            "context": {
                "project_name": state.get("project_name", "Unnamed Project"),
                "project_description": state.get(
                    "project_description", "No description provided"
                ),
                "repository_path": state.get("repository_path", "./workspace"),
            },
        }

        result = self.initializer_agent.invoke(
            {"messages": [input_message]}, config=agent_config
        )

        # Extract output
        output = result.get("output", "Initialization complete.")
        if isinstance(output, list):
            output = output[-1] if output else "Initialization complete."

        # Add progress entry
        new_progress: ProgressEntry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "initializer",
            "action": "project_initialized",
            "details": f"Set up project: {state.get('project_name')}",
            "commit_hash": None,
        }

        return {
            "messages": [AIMessage(content=str(output))],
            "is_initialized": True,
            "session_count": state.get("session_count", 0) + 1,
            "progress_log": [new_progress],
        }

    def _coding_node(self, state: OrchestratorState) -> dict:
        """
        Coding agent node.

        From the article - Each session follows:
        1. Run `pwd` to confirm working directory
        2. Read progress files and git logs
        3. Select highest-priority incomplete feature
        4. Implement incrementally
        5. Verify end-to-end functionality
        6. Commit with progress updates

        Key insight: "Structure prompts to work on single features within each
        context window, leaving the environment in a clean state"

        Uses @dynamic_prompt middleware - context is passed via runtime.context
        """
        # Sync feature list from file first
        repository_path = state.get("repository_path", "./workspace")
        file_feature_list = self._load_feature_list(repository_path)
        if file_feature_list:
            state = {**state, "feature_list": file_feature_list}

        # Find the next feature to work on
        current_feature = self._select_next_feature(state)

        if current_feature is None:
            # Check if there are actually features or if initialization failed
            feature_list = state.get("feature_list", [])
            if not feature_list:
                return {
                    "messages": [
                        AIMessage(
                            content="No features found. Initialization may have failed or feature_list.json is missing."
                        )
                    ],
                    "should_continue": False,
                }
            return {
                "messages": [
                    AIMessage(content="All features are complete! Project finished.")
                ],
                "should_continue": False,
            }

        # Prepare input message (minimal - dynamic content comes from middleware)
        input_message = HumanMessage(content="Start the coding session.")

        # Pass dynamic context via config for @dynamic_prompt middleware
        # The middleware will append feature/session context to the static system prompt
        agent_config = {
            "recursion_limit": 100,
            "context": {
                "feature_id": current_feature.get("id", ""),
                "feature_description": current_feature.get("description", ""),
                "feature_category": current_feature.get("category", ""),
                "feature_priority": current_feature.get("priority", ""),
                "feature_steps": current_feature.get("steps", []),
                "feature_dependencies": current_feature.get("dependencies", []),
                "session_number": state.get("session_count", 0) + 1,
                "repository_path": state.get("repository_path", "./workspace"),
            },
        }

        result = self.coding_agent.invoke(
            {"messages": [input_message]}, config=agent_config
        )

        # Extract output
        output = result.get("output", "Session complete.")
        if isinstance(output, list):
            output = output[-1] if output else "Session complete."

        # Add progress entry
        new_progress: ProgressEntry = {
            "timestamp": datetime.now().isoformat(),
            "agent": "coding",
            "action": "feature_work",
            "details": f"Worked on: {current_feature.get('id')} - {current_feature.get('description')}",
            "commit_hash": None,
        }

        return {
            "messages": [AIMessage(content=str(output))],
            "current_feature_id": current_feature.get("id"),
            "session_count": state.get("session_count", 0) + 1,
            "progress_log": [new_progress],
        }

    def _select_next_feature(self, state: OrchestratorState) -> Optional[Feature]:
        """
        Select the next feature to work on.

        Priority order:
        1. High priority features with satisfied dependencies
        2. Medium priority features with satisfied dependencies
        3. Low priority features with satisfied dependencies
        """
        feature_list = state.get("feature_list", [])
        completed_ids = {f["id"] for f in feature_list if f.get("passes", False)}

        for priority in ["high", "medium", "low"]:
            for feature in feature_list:
                if feature.get("passes", False):
                    continue
                if feature.get("priority") != priority:
                    continue
                # Check dependencies
                deps = feature.get("dependencies", [])
                if all(dep in completed_ids for dep in deps):
                    return feature

        return None

    def invoke(
        self,
        project_name: str,
        project_description: str,
        repository_path: str = "./workspace",
        config: Optional[dict] = None,
    ) -> OrchestratorState:
        """
        Start or resume a long-running project.

        Args:
            project_name: Name of the project
            project_description: Full description of what to build
            repository_path: Path to the git repository
            config: Optional LangGraph config (for thread_id, etc.)

        Returns:
            Final orchestrator state
        """
        initial_state: OrchestratorState = {
            "messages": [],
            "project_name": project_name,
            "project_description": project_description,
            "repository_path": repository_path,
            "feature_list": [],
            "current_feature_id": None,
            "progress_log": [],
            "is_initialized": False,
            "session_count": 0,
            "last_commit_hash": None,
            "next_agent": None,
            "should_continue": True,
            "last_error": None,
        }

        config = config or {"configurable": {"thread_id": "default"}}

        return self.workflow.invoke(initial_state, config)

    async def astream_events(
        self,
        project_name: str,
        project_description: str,
        repository_path: str = "./workspace",
        config: Optional[dict] = None,
    ):
        """
        Async stream events with the custom stream_event_handler.
        """
        from ax_advanced_class.src.utils.stream_event_handler import (
            process_stream_event,
        )

        initial_state: OrchestratorState = {
            "messages": [],
            "project_name": project_name,
            "project_description": project_description,
            "repository_path": repository_path,
            "feature_list": [],
            "current_feature_id": None,
            "progress_log": [],
            "is_initialized": False,
            "session_count": 0,
            "last_commit_hash": None,
            "next_agent": None,
            "should_continue": True,
            "last_error": None,
        }

        config = config or {"configurable": {"thread_id": "default"}}
        chain_stack = []

        # Use astream_events from the compiled workflow
        # 'v2' version is standard for LangGraph
        async for event in self.workflow.astream_events(
            initial_state, config, version="v2"
        ):
            # Process with our custom handler
            await process_stream_event(event, chain_stack)
            # Re-yield the original event so downstream consumers still see it
            yield event

    def get_state(self, config: dict) -> Optional[OrchestratorState]:
        """
        Get the current state for a given thread.

        Useful for inspecting progress or resuming from a checkpoint.
        """
        state = self.workflow.get_state(config)
        return state.values if state else None

    def update_state(self, config: dict, updates: dict) -> None:
        """
        Update the state for a given thread.

        Useful for manual interventions or state corrections.
        """
        self.workflow.update_state(config, updates)


# =============================================================================
# Factory Function
# =============================================================================


def create_orchestrator(
    llm: Any,
    tools: Optional[list] = None,
    checkpointer: Optional[Any] = None,
) -> LongRunningOrchestrator:
    """
    Factory function to create a configured orchestrator.

    Args:
        llm: The language model to use
        tools: Optional list of tools for agents
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Configured LongRunningOrchestrator instance
    """
    return LongRunningOrchestrator(
        llm=llm,
        tools=tools,
        checkpointer=checkpointer,
    )
