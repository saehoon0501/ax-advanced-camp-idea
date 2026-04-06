"""Internal helpers for TodoListMiddleware — pre-implemented logic.

This module contains the parts of the todo middleware that students do NOT need
to implement themselves:
- The system prompt injected into the model context
- The WriteTodosInput Pydantic model
- The async wrapper for _write_todos
- TodoListMiddlewareBase with parallel-call detection (after_model / aafter_model)
"""

from collections.abc import Awaitable, Callable
from typing import Any, cast

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.runtime import Runtime
from langgraph.types import Command
from pydantic import BaseModel
from typing_extensions import TypedDict, override

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ModelRequest,
    ModelResponse,
    ResponseT,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WRITE_TODOS_SYSTEM_PROMPT = """## `write_todos`

You have access to the `write_todos` tool to help you manage and plan complex objectives.
Use this tool for complex objectives to ensure that you are tracking each necessary step and giving the user visibility into your progress.
This tool is very helpful for planning complex objectives, and for breaking down these larger complex objectives into smaller steps.

It is critical that you mark todos as completed as soon as you are done with a step. Do not batch up multiple steps before marking them as completed.
For simple objectives that only require a few steps, it is better to just complete the objective directly and NOT use this tool.
Writing todos takes time and tokens, use it when it is helpful for managing complex many-step problems! But not for simple few-step requests.

## Important To-Do List Usage Notes to Remember
- The `write_todos` tool should never be called multiple times in parallel.
- Exactly ONE task must be in_progress at any time (not less, not more). Complete current tasks before starting new ones.
- Each call to write_todos replaces the entire todo list. Always provide the complete list with current statuses.
- Don't be afraid to revise the To-Do list as you go. New information may reveal new tasks that need to be done, or old tasks that are irrelevant.
- Never skip status updates - the UI depends on accurate status tracking."""  # noqa: E501

# ---------------------------------------------------------------------------
# Pydantic input schema (used by StructuredTool)
# ---------------------------------------------------------------------------


class WriteTodosInput(BaseModel):
    """Input schema for the ``write_todos`` tool."""

    todos: list[dict[str, str]]
    # Note: kept as list[dict] so StructuredTool serialisation stays simple.
    # The actual Todo TypedDict is defined by the student in todo_middleware.py.


# ---------------------------------------------------------------------------
# Async coroutine companion for _write_todos (delegates to sync version)
# ---------------------------------------------------------------------------


async def _awrite_todos(runtime: Any, todos: list[Any]) -> Command[Any]:
    """Async wrapper — imports the sync ``_write_todos`` at call-time to
    avoid circular imports (student defines it in todo_middleware.py)."""
    from ax_advanced_class.src.middleware.todo_middleware import _write_todos

    return _write_todos(runtime, todos)


# ---------------------------------------------------------------------------
# Base class with pre-implemented parallel-call detection
# ---------------------------------------------------------------------------


class TodoListMiddlewareBase(AgentMiddleware[Any, ContextT, ResponseT]):
    """Base class that provides ``after_model`` / ``aafter_model`` hooks.

    Students extend this via ``TodoListMiddleware`` and fill in:
    - ``__init__``
    - ``wrap_model_call``
    """

    # Will be overridden by the student's PlanningState
    state_schema: type = AgentState  # type: ignore[assignment]

    # -- default pass-through implementations (overridden by student) ------

    def __init__(self) -> None:  # noqa: D401
        super().__init__()
        self.system_prompt: str = WRITE_TODOS_SYSTEM_PROMPT
        self.tool_description: str = ""
        self.tools: list[StructuredTool] = []

    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT] | AIMessage:
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT] | AIMessage:
        """Async variant — delegates to the sync ``wrap_model_call``.

        Students only need to implement the sync version; the async path
        mirrors it automatically via ``request.override`` (which is sync-safe).
        """
        if request.system_message is not None:
            new_system_content = [
                *request.system_message.content_blocks,
                {"type": "text", "text": f"\n\n{self.system_prompt}"},
            ]
        else:
            new_system_content = [{"type": "text", "text": self.system_prompt}]
        new_system_message = SystemMessage(
            content=cast("list[str | dict[str, str]]", new_system_content)
        )
        return await handler(request.override(system_message=new_system_message))

    # -- parallel-call detection (pre-implemented) -------------------------

    @override
    def after_model(
        self, state: Any, runtime: Runtime[ContextT]
    ) -> dict[str, Any] | None:
        """Reject responses that call ``write_todos`` more than once.

        The todo list is replaced wholesale on each call, so parallel calls
        would create ambiguity about which update takes precedence.
        """
        messages = state.get("messages", [])
        if not messages:
            return None

        last_ai_msg = next(
            (msg for msg in reversed(messages) if isinstance(msg, AIMessage)), None
        )
        if not last_ai_msg or not last_ai_msg.tool_calls:
            return None

        write_todos_calls = [
            tc for tc in last_ai_msg.tool_calls if tc["name"] == "write_todos"
        ]

        if len(write_todos_calls) > 1:
            error_messages = [
                ToolMessage(
                    content=(
                        "Error: The `write_todos` tool should never be called multiple "
                        "times in parallel. Please call it only once per model "
                        "invocation to update the todo list."
                    ),
                    tool_call_id=tc["id"],
                    status="error",
                )
                for tc in write_todos_calls
            ]
            return {"messages": error_messages}

        return None

    @override
    async def aafter_model(
        self, state: Any, runtime: Runtime[ContextT]
    ) -> dict[str, Any] | None:
        """Async variant of ``after_model``."""
        return self.after_model(state, runtime)
