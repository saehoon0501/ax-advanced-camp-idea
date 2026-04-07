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

from ax_advanced_class.src.agents import (
    AgentFactory,
    coding_agent_spec,
    initializer_agent_spec,
)
from ax_advanced_class.src.prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT

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
        description="Direct response for general/non-coding questions (only when route='finish' for general questions)",
    )


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
        permission_config: Optional[Any] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            llm: The language model to use for routing and agents
            checkpointer: Optional LangGraph checkpointer for state persistence
            permission_config: Optional PermissionConfig for tool validation
        """
        self.llm = llm
        self.checkpointer = checkpointer or MemorySaver()

        factory = AgentFactory(self.llm)
        self.initializer_agent = factory.create(initializer_agent_spec(permission_config))
        self.coding_agent = factory.create(coding_agent_spec(permission_config))

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph:
        """Build the LangGraph workflow: START -> router -> [agent] -> router -> ... -> END"""
        # TODO 1: Assemble the StateGraph
        #
        # Step 1: Create a graph with StateGraph(OrchestratorState)
        #
        # Step 2: Add 3 nodes
        #   - "router" -> self._router_node
        #   - "initializer" -> self._initializer_node
        #   - "coding" -> self._coding_node
        #   Hint: workflow.add_node("name", function)
        #
        # Step 3: Connect edges
        #   - START -> "router" (Normal Edge)
        #   - "router" -> conditional branching (Conditional Edge)
        #     Branching function: self._route_decision
        #     Mapping: AgentRoute.INITIALIZER -> "initializer"
        #              AgentRoute.CODING -> "coding"
        #              AgentRoute.FINISH -> END
        #   - "initializer" -> END (Normal Edge)
        #   - "coding" -> END (Normal Edge)
        #   Hint: add_edge(), add_conditional_edges()
        #
        # Step 4: compile(checkpointer=self.checkpointer)
        #
        return  # CompiledStateGraph

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
        # TODO 2: Make a routing decision using the LLM
        #
        # Step 1: Extract messages from state
        #
        # Step 2: Wrap the LLM with with_structured_output(RouterDecision)
        #   structured_llm = self.llm.with_structured_output(RouterDecision)
        #
        # Step 3: Invoke the LLM
        #   Input: [{"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT}, *messages]
        #   Hint: structured_llm.invoke([...])
        #   Result: RouterDecision object (decision.route, decision.reason, decision.response)
        #
        # Step 4: Convert decision.route to an AgentRoute enum
        #   "initializer" -> AgentRoute.INITIALIZER
        #   "coding" -> AgentRoute.CODING
        #   "finish" -> AgentRoute.FINISH
        #
        # Step 5: Compose the return value
        #   return {
        #       "next_agent": route,
        #       "messages": [AIMessage(content=appropriate_message)],
        #   }
        #   Hint: Use decision.response if available, otherwise use reason
        #
        return {}

    def _route_decision(self, state: OrchestratorState) -> AgentRoute:
        """Extract routing decision from state."""
        # TODO 3: Extract and return next_agent from state
        #
        # Hint: state.get("next_agent", default_value)
        # If next_agent is missing, default to AgentRoute.FINISH
        #
        return  # AgentRoute

    def _initializer_node(self, state: OrchestratorState) -> dict:
        """
        Initializer agent node.
        """
        result = self.initializer_agent.invoke(
            {
                "messages": state.get("messages", []),
            }
        )
        return {"messages": [AIMessage(content=result["messages"][-1].content)]}

    def _coding_node(self, state: OrchestratorState) -> dict:
        """
        Coding agent node.
        """
        # TODO 4: Run the coding agent and return the result
        #
        # Step 1: Extract messages from the orchestrator state
        #
        # Step 2: Compose the agent input
        #   The coding agent requires todos in addition to messages
        #   {"messages": messages, "todos": []}
        #
        # Step 3: Execute self.coding_agent.invoke(agent_input)
        #
        # Step 4: Return only the agent's final response to the orchestrator
        #   The agent may have dozens of conversation turns,
        #   but only the last message is returned to the orchestrator
        #   return {"messages": [AIMessage(content=last_message)]}
        #
        #   Why? Putting the agent's entire conversation into the orchestrator
        #        pollutes the context window
        #
        return {"messages": []}

    def invoke(
        self,
        messages: Optional[list[BaseMessage]] = None,
        config: Optional[dict] = None,
    ) -> OrchestratorState:
        """
        Start or resume a long-running project.

        Args:
            messages: Optional initial messages to seed the workflow
            config: Optional LangGraph config (for thread_id, etc.)

        Returns:
            Final orchestrator state
        """
        if messages is None:
            messages = []
        initial_state: OrchestratorState = {
            "messages": messages,
        }

        config = config or {"configurable": {"thread_id": "default"}}

        return self.workflow.invoke(initial_state, config)

    async def astream_events(
        self,
        config: Optional[dict] = None,
        resume_value: Optional[Any] = None,
        user_message: Optional[str] = None,
        message_history: Optional[list] = None,
    ):
        """
        Async stream events with the custom stream_event_handler.

        Args:
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
    permission_config: Optional[Any] = None,
) -> LongRunningOrchestrator:
    """
    Factory function to create a configured orchestrator.

    Args:
        llm: The language model to use for routing and agents
        checkpointer: Optional checkpointer for state persistence
        permission_config: Optional PermissionConfig for tool validation

    Returns:
        Configured LongRunningOrchestrator instance
    """
    return LongRunningOrchestrator(
        llm=llm,
        checkpointer=checkpointer,
        permission_config=permission_config,
    )
