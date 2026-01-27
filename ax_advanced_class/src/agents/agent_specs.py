"""
Agent specs and state schemas for the long-running orchestrator.
"""

from typing import Optional, Sequence

from langchain_core.tools import BaseTool

from ax_advanced_class.src.agents.agent_factory import AgentSpec, DefaultAgentState
from ax_advanced_class.src.config.tool_permission_config import PermissionConfig
from ax_advanced_class.src.middleware.tool_validation_middleware import (
    ToolValidationMiddleware,
)
from ax_advanced_class.src.prompts import (
    CODING_AGENT_SYSTEM_PROMPT,
    INITIALIZER_SYSTEM_PROMPT,
    coding_agent_dynamic_prompt,
    initializer_agent_dynamic_prompt,
)
from ax_advanced_class.src.tools import BashTool, FileOperationTool, TodoWriteTool


def _default_tools() -> list[BaseTool]:
    tools = []
    tools.extend(BashTool().get_langchain_tools())
    tools.extend(FileOperationTool().get_langchain_tools())
    tools.extend(TodoWriteTool().get_langchain_tools())
    return tools


def coding_agent_spec(config: PermissionConfig | None = None) -> AgentSpec:
    if config is None:
        config = PermissionConfig()
    agent_middleware = [
        coding_agent_dynamic_prompt,
        ToolValidationMiddleware(config),
    ]
    return AgentSpec(
        name="coding_agent",
        tools=_default_tools(),
        middleware=agent_middleware,
        state_schema=DefaultAgentState,
        system_prompt=CODING_AGENT_SYSTEM_PROMPT,
    )


def initializer_agent_spec(config: PermissionConfig | None = None) -> AgentSpec:
    if config is None:
        config = PermissionConfig()
    agent_middleware = [
        initializer_agent_dynamic_prompt,
        ToolValidationMiddleware(config),
    ]
    return AgentSpec(
        name="initializer_agent",
        tools=_default_tools(),
        middleware=agent_middleware,
        state_schema=DefaultAgentState,
        system_prompt=INITIALIZER_SYSTEM_PROMPT,
    )
