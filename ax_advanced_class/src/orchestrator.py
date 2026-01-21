"""
Long-Running Agent Orchestrator

Simple router-based architecture using LangGraph:
- Router: LLM-based decision maker that routes to appropriate agents
- Initializer Agent: Sets up project foundation
- Coding Agent: Implements features

The router is intentionally simple - it only decides which agent to route to
based on the user message. All complex logic is delegated to the specialized agents.
"""

from typing import Annotated, TypedDict, Literal, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field
from langgraph.graph import END, StateGraph, START
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
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


class OrchestratorState(TypedDict, total=False):
    """
    State managed by the orchestrator across agent sessions.

    The router simply decides which agent to invoke based on the user message.
    All complex logic is delegated to the specialized agents.
    """

    # Conversation messages (accumulates across turns)
    messages: Annotated[list[BaseMessage], operator.add]

    # Project metadata
    project_name: str
    project_description: str
    repository_path: str

    # Routing decision (set by router node)
    next_agent: Optional["AgentRoute"]


# =============================================================================
# Agent Routing
# =============================================================================


class AgentRoute(str, Enum):
    """Possible routing destinations for the orchestrator."""

    INITIALIZER = "initializer"
    CODING = "coding"
    FINISH = "__end__"


class RouterDecision(BaseModel):
    """Structured output for router decisions."""

    route: Literal["initializer", "coding", "finish"] = Field(
        description="The agent to route to: 'initializer' for project setup, 'coding' for feature implementation, 'finish' when done"
    )
    reason: str = Field(description="Brief explanation for the routing decision")


ROUTER_SYSTEM_PROMPT = """You are a routing agent that decides which specialized agent should handle the current task.

Based on the user's message and project state, decide:
- "initializer": Route here when the project needs initial setup (creating feature lists, progress tracking, project foundation)
- "coding": Route here when features need to be implemented or code needs to be written
- "finish": Route here when all tasks are complete or the user explicitly wants to end

Keep your reasoning brief. The specialized agents will handle all the complex work."""


# =============================================================================
# Orchestrator Implementation
# =============================================================================


class LongRunningOrchestrator:
    """
    Simple orchestrator with LLM-based routing.

    Architecture:
    ```
    START -> router -> [initializer|coding] -> router -> ... -> END
    ```

    The router uses structured output to decide which agent to invoke.
    All complex logic is delegated to the specialized agents.
    """

    def __init__(
        self,
        llm: Any,
        checkpointer: Optional[Any] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            llm: The language model to use for routing and agents
            checkpointer: Optional LangGraph checkpointer for state persistence
        """
        self.llm = llm
        self.checkpointer = checkpointer or MemorySaver()

        self.initializer_agent = create_initializer_agent(self.llm, [initializer_agent_dynamic_prompt])
        self.coding_agent = create_coding_agent(self.llm, [coding_agent_dynamic_prompt])

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph:
        """Build the LangGraph workflow: START -> router -> [agent] -> router -> ... -> END"""
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

    def _router_node(self, state: OrchestratorState) -> dict:
        """
        Simple router node that decides which agent should handle the task.

        Uses structured output from the LLM to make routing decisions.
        All complex logic is delegated to the specialized agents.
        """
        # Build context from state for the router
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else state.get("project_description", "")

        router_input = f"""Project: {state.get("project_name", "Unknown")}
                        Description: {state.get("project_description", "No description")}
                        Current request: {last_message}"""

        # Use structured output for clear routing decision
        structured_llm = self.llm.with_structured_output(RouterDecision)
        decision: RouterDecision = structured_llm.invoke(
            [
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": router_input},
            ]
        )

        # Map decision to AgentRoute
        route_map = {
            "initializer": AgentRoute.INITIALIZER,
            "coding": AgentRoute.CODING,
            "finish": AgentRoute.FINISH,
        }

        return {"next_agent": route_map.get(decision.route, AgentRoute.FINISH)}

    def _route_decision(self, state: OrchestratorState) -> AgentRoute:
        """Extract routing decision from state."""
        return state.get("next_agent", AgentRoute.FINISH)

    def _initializer_node(self, state: OrchestratorState) -> dict:
        """
        Initializer agent node.

        Simply invokes the initializer agent with project context.
        The agent handles all complex initialization logic.
        """
        input_message = HumanMessage(content="Initialize the project.")

        agent_config = {
            "recursion_limit": 100,
            "context": {
                "project_name": state.get("project_name", "Unnamed Project"),
                "project_description": state.get("project_description", "No description"),
                "repository_path": state.get("repository_path", "./workspace"),
            },
        }

        result = self.initializer_agent.invoke({"messages": [input_message]}, config=agent_config)

        output = result.get("output", "Initialization complete.")
        if isinstance(output, list):
            output = output[-1] if output else "Initialization complete."

        return {"messages": [AIMessage(content=str(output))]}

    def _coding_node(self, state: OrchestratorState) -> dict:
        """
        Coding agent node.

        Simply invokes the coding agent with project context.
        The agent handles feature selection, implementation, and progress tracking.
        """
        input_message = HumanMessage(content="Start the coding session.")

        agent_config = {
            "recursion_limit": 100,
            "context": {
                "project_name": state.get("project_name", "Unnamed Project"),
                "project_description": state.get("project_description", "No description"),
                "repository_path": state.get("repository_path", "./workspace"),
            },
        }

        result = self.coding_agent.invoke({"messages": [input_message]}, config=agent_config)

        output = result.get("output", "Session complete.")
        if isinstance(output, list):
            output = output[-1] if output else "Session complete."

        return {"messages": [AIMessage(content=str(output))]}

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
        }

        config = config or {"configurable": {"thread_id": "default"}}

        return self.workflow.invoke(initial_state, config)

    async def astream_events(
        self,
        project_name: str,
        project_description: str,
        repository_path: str = "./workspace",
        config: Optional[dict] = None,
        resume_value: Optional[Any] = None,
    ):
        """
        Async stream events with the custom stream_event_handler.

        Args:
            project_name: Name of the project
            project_description: Description of the project
            repository_path: Path to the repository
            config: LangGraph config with thread_id for checkpointing
            resume_value: If provided, resume from interrupt with this value
                         (typically True/False for permission approval)
        """
        from ax_advanced_class.src.utils.stream_event_handler import (
            process_stream_event,
        )

        config = config or {"configurable": {"thread_id": "default"}}
        chain_stack = []

        # Determine input: either initial state or resume command
        if resume_value is not None:
            # Resume from interrupt with the provided value
            stream_input = Command(resume=resume_value)
        else:
            # Initial run with minimal state
            stream_input: OrchestratorState = {
                "messages": [],
                "project_name": project_name,
                "project_description": project_description,
                "repository_path": repository_path,
            }

        # Use astream_events from the compiled workflow
        # 'v2' version is standard for LangGraph
        async for event in self.workflow.astream_events(stream_input, config, version="v2"):
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

    def update_state(self, config: dict, updates: Optional[dict] = None, as_node: Optional[str] = None) -> None:
        """
        Update the state for a given thread.

        Useful for manual interventions, state corrections, or resuming from interrupts.

        Args:
            config: LangGraph config with thread_id
            updates: State updates to apply (can be None for resume operations)
            as_node: Optional node name to resume from (used for interrupt handling)
        """
        if updates is not None:
            self.workflow.update_state(config, updates, as_node=as_node)


# =============================================================================
# Factory Function
# =============================================================================


def create_orchestrator(
    llm: Any,
    checkpointer: Optional[Any] = None,
) -> LongRunningOrchestrator:
    """
    Factory function to create a configured orchestrator.

    Args:
        llm: The language model to use for routing and agents
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Configured LongRunningOrchestrator instance
    """
    return LongRunningOrchestrator(
        llm=llm,
        checkpointer=checkpointer,
    )
