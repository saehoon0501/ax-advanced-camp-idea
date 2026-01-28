from dataclasses import dataclass, field
from typing import Optional, Sequence, TypedDict, Any

from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langchain.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage
import operator
from typing import Annotated
from enum import Enum


# =============================================================================
# Agent State Definition
# =============================================================================
class TodoStatus(str, Enum):
    """Status of a todo item for task tracking."""


class TodoItem(TypedDict):
    """
    A single todo item for task tracking.

    Based on Claude Code's TodoWrite tool schema.
    """


def merge_todo_list(existing: list[TodoItem], updates: Any) -> list[TodoItem]:
    """ """

    return


class DefaultAgentState(TypedDict):
    """
    State for the Default Agent.

    This TypedDict defines the agent's internal state, separate from OrchestratorState.
    The todo_list is managed by the agent via TodoWriteTool with merge support.
    """

    messages: Annotated[list[BaseMessage], operator.add]
    todo_list: Annotated[list[TodoItem], merge_todo_list]  # Agent's task tracking list with merge reducer


@dataclass(frozen=True)
class AgentSpec:
    name: str
    tools: Sequence[BaseTool] = field(default_factory=tuple)
    middleware: Sequence[AgentMiddleware] = field(default_factory=tuple)
    state_schema: Optional[type[AgentState]] = DefaultAgentState
    system_prompt: str = ""


class AgentFactory:
    def __init__(self, model: BaseChatModel):
        self.model = model

    def create(self, spec: AgentSpec):
        if not spec.name:
            raise ValueError("Agent name is required")
        if not spec.tools:
            raise ValueError("At least one tool is required")

        kwargs = {
            "model": self.model,
            "tools": list(spec.tools),
            "middleware": list(spec.middleware),
            "name": spec.name,
        }
        if spec.state_schema is not None:
            kwargs["state_schema"] = spec.state_schema
        if spec.system_prompt == "":
            raise ValueError("System prompt is required")

        # Subgraphs that call interrupt() must have checkpointer=True
        # to avoid TracerException errors when interrupt bubbles up
        agent = create_agent(**kwargs, checkpointer=True)
        return agent.with_config({"recursion_limit": 500, "tags": [spec.name]})
