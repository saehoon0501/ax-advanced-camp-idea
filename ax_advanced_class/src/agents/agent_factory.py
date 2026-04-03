from dataclasses import dataclass, field
from typing import Optional, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentMiddleware
from langchain.chat_models import BaseChatModel
from langchain_core.tools import BaseTool


@dataclass(frozen=True)
class AgentSpec:
    name: str
    tools: Sequence[BaseTool] = field(default_factory=tuple)
    middleware: Sequence[AgentMiddleware] = field(default_factory=tuple)
    system_prompt: str = ""


class AgentFactory:
    def __init__(self, model: BaseChatModel):
        self.model = model

    def create(self, spec: AgentSpec):
        if not spec.name:
            raise ValueError("Agent name is required")
        if spec.system_prompt == "":
            raise ValueError("System prompt is required")

        kwargs = {
            "model": self.model,
            "middleware": list(spec.middleware),
            "name": spec.name,
        }
        if spec.tools:
            kwargs["tools"] = list(spec.tools)

        # Subgraphs that call interrupt() must have checkpointer=True
        # to avoid TracerException errors when interrupt bubbles up
        agent = create_agent(**kwargs, checkpointer=True)
        return agent.with_config({"recursion_limit": 500, "tags": [spec.name]})
