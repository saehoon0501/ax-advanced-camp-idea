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
        description="The agent to route to: 'initializer' for project setup, 'coding' for feature implementation, 'finish' for general questions or when done"
    )
    reason: str = Field(description="Brief explanation for the routing decision")
    response: Optional[str] = Field(
        default=None,
        description="Direct response for general/non-coding questions (only when route='finish' for general questions)"
    )


ROUTER_SYSTEM_PROMPT = """You are a routing agent that decides which specialized agent should handle the current task.

Based on the user's message and conversation history, decide:
- "initializer": Route here ONLY on the first request when project needs initial setup
- "coding": Route here ONLY on the first request when code needs to be written
- "finish": Route here when:
  1. An agent has already responded (messages from [Router], [Initializer], or [Coding] indicate work is done)
  2. The user asks a general question NOT related to software engineering or coding (e.g., greetings like "hello", "how are you?", or general knowledge questions like "what's the tallest building?")

For general questions (case 2), provide a friendly direct response in the "response" field.

IMPORTANT: If you see messages starting with [Router], [Initializer], or [Coding] in the conversation, the task has been handled. Route to "finish".

Keep your reasoning brief."""


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

    def _to_str(self, value: Any) -> str:
        """Safely convert any value to string."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)

    def _router_node(self, state: OrchestratorState) -> dict:
        """
        Simple router node that decides which agent should handle the task.

        Uses structured output from the LLM to make routing decisions.
        All complex logic is delegated to the specialized agents.
        """
        # Build context from state for the router
        messages = state.get("messages", [])
        project_name = self._to_str(state.get("project_name", "Unknown"))
        project_desc = self._to_str(state.get("project_description", "No description"))

        # Build conversation history for router to see
        conversation_history = ""
        for msg in messages:
            content = self._to_str(msg.content)
            role = "User" if msg.type == "human" else "Assistant"
            conversation_history += f"{role}: {content}\n"

        router_input = f"""Project: {project_name}
Description: {project_desc}

Conversation history:
{conversation_history if conversation_history else "No messages yet."}"""

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

        route = route_map.get(decision.route, AgentRoute.FINISH)

        # Build message content - include response for general questions
        if decision.response:
            message_content = f"[Router] {decision.response}"
        else:
            message_content = f"[Router] Routing to {decision.route}: {decision.reason}"

        return {
            "next_agent": route,
            "messages": [AIMessage(content=message_content)],
        }

    def _route_decision(self, state: OrchestratorState) -> AgentRoute:
        """Extract routing decision from state."""
        return state.get("next_agent", AgentRoute.FINISH)

    def _initializer_node(self, state: OrchestratorState) -> dict:
        """
        Initializer agent node.

        TODO: Will invoke the initializer agent with project context.
        For now, returns a simple response to test the flow.
        """
        # Simple response for testing the flow
        return {
            "messages": [AIMessage(content="[Initializer] Project initialization complete.")],
        }

    def _coding_node(self, state: OrchestratorState) -> dict:
        """
        Coding agent node.

        TODO: Will invoke the coding agent with project context.
        For now, returns a simple response to test the flow.
        """
        # Simple response for testing the flow
        return {
            "messages": [AIMessage(content="[Coding] Coding session complete.")],
        }

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
        user_message: Optional[str] = None,
        message_history: Optional[list] = None,
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
            user_message: The user's input message to process
            message_history: Optional conversation history (list of {role, content} dicts)
        """
        from ax_advanced_class.src.utils.stream_event_handler import (
            process_stream_event,
            init_session_logger,
        )

        config = config or {"configurable": {"thread_id": "default"}}

        # Initialize session logger with thread_id
        session_id = config.get("configurable", {}).get("thread_id", "default")
        init_session_logger(session_id)

        chain_stack = []

        # Determine input: either initial state or resume command
        if resume_value is not None:
            # Resume from interrupt with the provided value
            stream_input = Command(resume=resume_value)
        else:
            # Build messages from history and current user input
            messages = []

            # Add conversation history
            if message_history:
                for msg in message_history:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg.get("content", "")))
                    elif msg.get("role") == "assistant":
                        messages.append(AIMessage(content=msg.get("content", "")))

            # Add current user message
            if user_message:
                messages.append(HumanMessage(content=user_message))

            # Initial run with state including messages
            stream_input: OrchestratorState = {
                "messages": messages,
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
