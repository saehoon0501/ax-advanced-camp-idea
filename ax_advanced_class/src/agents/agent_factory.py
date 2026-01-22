from dataclasses import dataclass, field
from typing import Optional, Sequence, TypedDict

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


class DefaultAgentState(TypedDict):
    """
    State for the Default Agent.

    This TypedDict defines the agent's internal state, separate from OrchestratorState.
    The todo_list is managed by the agent via TodoWriteTool.
    """

    messages: Annotated[list[BaseMessage], operator.add]
    todo_list: list[TodoItem]  # Agent's task tracking list


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

        agent = create_agent(**kwargs)
        return agent.with_config({"recursion_limit": 500})
