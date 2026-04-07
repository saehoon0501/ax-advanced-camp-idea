"""Planning and task management middleware for agents.

This is a learning file for implementing TodoListMiddleware.
Complete the 5 TODOs in order.
"""

from collections.abc import Callable
from typing import Annotated, Any, Literal, cast

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.types import Command
from typing_extensions import NotRequired, TypedDict

from langchain.agents.middleware.types import (
    AgentState,
    ContextT,
    ModelRequest,
    ModelResponse,
    OmitFromInput,
    ResponseT,
)
from langchain.tools import ToolRuntime

from ax_advanced_class.src.middleware._internals.todo_helpers import (
    WRITE_TODOS_SYSTEM_PROMPT,
    TodoListMiddlewareBase,
    WriteTodosInput,
)

# ===========================================================================
# TODO 1: Define the Todo type and PlanningState
# ===========================================================================
# Todo: TypedDict — content: str, status: Literal["pending", "in_progress", "completed"]
# PlanningState: Extend AgentState[ResponseT] by adding a todos field
#   todos: Annotated[NotRequired[list[Todo]], OmitFromInput]


class Todo(TypedDict):
    """A single todo item with content and status."""
    # TODO 1a: Define the content (str) and status (Literal["pending", "in_progress", "completed"]) fields
    pass


class PlanningState(AgentState[ResponseT]):
    """State schema for the todo middleware."""
    # TODO 1b: Add the todos field
    #   todos: Annotated[NotRequired[list[Todo]], OmitFromInput]
    pass


# ===========================================================================
# TODO 2: Return a Command that updates the todo list in state
# ===========================================================================
# Command(update={"todos": todos, "messages": [ToolMessage(...)]})
# The ToolMessage must include runtime.tool_call_id


def _write_todos(
    runtime: ToolRuntime[ContextT, PlanningState[ResponseT]], todos: list[Todo]
) -> Command[Any]:
    """Create and manage a structured task list for your current work session."""
    # TODO 2: Return a Command that updates the todo list in state
    #
    # Using Command(update={...}):
    #   1. Set the new todo list on the "todos" key
    #   2. Add a ToolMessage to the "messages" key (so the LLM can see the result)
    #      Hint: ToolMessage(content=f"Updated todo list to {todos}",
    #                        tool_call_id=runtime.tool_call_id)
    #
    # Why Command?
    #   Normal tools return a string, but tools that need to modify state
    #   must return a Command so the update goes through LangGraph's state reducer.
    #
    return Command(update={})


# ===========================================================================
# TODO 3: Write the description for the write_todos tool
# ===========================================================================
# Include:
# - When to Use (complex tasks with 3+ steps)
# - When NOT to Use (simple tasks)
# - Task States (pending, in_progress, completed)
# - "Only 1 in_progress at a time"
# - Completion criteria (mark completed only when finished without errors)

WRITE_TODOS_TOOL_DESCRIPTION = ""
# TODO 3: Write the description for the write_todos tool
#
# Include:
# - When to Use (complex tasks with 3+ steps)
# - When NOT to Use (simple tasks)
# - How to Use (full list replacement approach)
# - Task States (pending, in_progress, completed)
# - "Only 1 in_progress at a time"
# - Completion criteria (mark completed only when finished without errors)


# ===========================================================================
# TODO 4 & 5: TodoListMiddleware class
# ===========================================================================


class TodoListMiddleware(TodoListMiddlewareBase):
    """Middleware that provides todo list management capabilities to agents.

    Adds the write_todos tool and provides usage instructions via the system prompt.
    """

    state_schema = PlanningState  # type: ignore[assignment]

    # =======================================================================
    # TODO 4: Initialize the middleware
    # =======================================================================
    # Step 1: super().__init__()
    # Step 2: Save self.system_prompt, self.tool_description
    # Step 3: self.tools = [StructuredTool.from_function(
    #     name="write_todos", description=tool_description,
    #     func=_write_todos, args_schema=WriteTodosInput, infer_schema=False)]

    def __init__(
        self,
        *,
        system_prompt: str = WRITE_TODOS_SYSTEM_PROMPT,
        tool_description: str = WRITE_TODOS_TOOL_DESCRIPTION,
    ) -> None:
        # TODO 4: Initialize the middleware
        #
        # Step 1: Call super().__init__()
        #
        # Step 2: Save system_prompt and tool_description as instance variables
        #
        # Step 3: Register write_todos tool in self.tools <- Tool axis
        #   Hint: StructuredTool.from_function(
        #       name="write_todos",
        #       description=tool_description,
        #       func=_write_todos,
        #       args_schema=WriteTodosInput,
        #       infer_schema=False,
        #   )
        #
        pass

    # =======================================================================
    # TODO 5: Add todo usage instructions to the system prompt
    # =======================================================================
    # Step 1: If request.system_message exists, add to content_blocks; otherwise create new
    #   Format: {"type": "text", "text": f"\n\n{self.system_prompt}"}
    # Step 2: SystemMessage(content=cast("list[str | dict[str, str]]", new_content))
    # Step 3: handler(request.override(system_message=new_system_message))

    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT] | AIMessage:
        # TODO 5: Add todo usage instructions to the system prompt
        #
        # Step 1: Check if an existing system message exists
        #   request.system_message is not None
        #
        # Step 2: Add self.system_prompt to the existing content blocks
        #   new_system_content = [
        #       *request.system_message.content_blocks,
        #       {"type": "text", "text": f"\n\n{self.system_prompt}"},
        #   ]
        #
        # Step 3: Wrap in a SystemMessage
        #   new_system_message = SystemMessage(content=new_system_content)
        #
        # Step 4: Pass the modified request to the handler with
        #         request.override(system_message=new_system_message)
        #
        return handler(request)  # <- needs modification
