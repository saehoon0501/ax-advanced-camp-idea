"""
Agent specs for the long-running orchestrator.

Uses deepagents built-in middleware instead of custom tool classes:
- FilesystemMiddleware (LocalShellBackend) → replaces BashTool + FileOperationTool
- TodoListMiddleware → replaces TodoWriteTool + custom state
- SummarizationMiddleware → context compression
"""

from deepagents.backends import LocalShellBackend
from ax_advanced_class.src.middleware.filesystem_middleware import FilesystemMiddleware
from ax_advanced_class.src.middleware.todo_middleware import TodoListMiddleware
from ax_advanced_class.src.middleware.summarization_middleware import SummarizationMiddleware

from ax_advanced_class.src.agents.agent_factory import AgentSpec
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


def _create_filesystem_middleware(config: PermissionConfig) -> FilesystemMiddleware:
    """Create FilesystemMiddleware with LocalShellBackend for file ops + shell execution."""
    backend = LocalShellBackend(
        root_dir=config.workspace_root,
        inherit_env=True,
    )
    return FilesystemMiddleware(
        backend=backend,
        tool_token_limit_before_evict=20000,
    )


def coding_agent_spec(config: PermissionConfig | None = None) -> AgentSpec:
    if config is None:
        config = PermissionConfig()
    agent_middleware = [
        ToolValidationMiddleware(config),
        _create_filesystem_middleware(config),
        TodoListMiddleware(),
        SummarizationMiddleware(
            model="anthropic:claude-haiku-4-5-20251001",
            trigger=("tokens", 60000),
            keep=("messages", 20),
        ),
        coding_agent_dynamic_prompt,
    ]
    return AgentSpec(
        name="coding_agent",
        middleware=agent_middleware,
        system_prompt=CODING_AGENT_SYSTEM_PROMPT,
    )


def initializer_agent_spec(config: PermissionConfig | None = None) -> AgentSpec:
    from langchain.agents.middleware import TodoListMiddleware as LangChainTodoListMiddleware

    if config is None:
        config = PermissionConfig()
    agent_middleware = [
        ToolValidationMiddleware(config),
        _create_filesystem_middleware(config),
        LangChainTodoListMiddleware(),
        SummarizationMiddleware(
            model="anthropic:claude-haiku-4-5-20251001",
            trigger=("tokens", 60000),
            keep=("messages", 20),
        ),
        initializer_agent_dynamic_prompt,
    ]
    return AgentSpec(
        name="initializer_agent",
        middleware=agent_middleware,
        system_prompt=INITIALIZER_SYSTEM_PROMPT,
    )
