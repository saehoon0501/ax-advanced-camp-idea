"""Planning and task management middleware for agents.

이 파일은 TodoListMiddleware를 구현하는 학습용 파일입니다.
5개의 TODO를 순서대로 완성하세요.
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
# TODO 1: Todo 타입과 PlanningState를 정의하세요
# ===========================================================================
# Todo: TypedDict — content: str, status: Literal["pending", "in_progress", "completed"]
# PlanningState: AgentState[ResponseT]를 확장하여 todos 필드 추가
#   todos: Annotated[NotRequired[list[Todo]], OmitFromInput]


class Todo(TypedDict):
    """A single todo item with content and status."""

    content: str
    status: Literal["pending", "in_progress", "completed"]


class PlanningState(AgentState[ResponseT]):
    """State schema for the todo middleware."""

    todos: Annotated[NotRequired[list[Todo]], OmitFromInput]


# ===========================================================================
# TODO 2: todo 리스트를 state에 업데이트하는 Command를 반환하세요
# ===========================================================================
# Command(update={"todos": todos, "messages": [ToolMessage(...)]})
# ToolMessage에 runtime.tool_call_id를 포함해야 합니다


def _write_todos(
    runtime: ToolRuntime[ContextT, PlanningState[ResponseT]], todos: list[Todo]
) -> Command[Any]:
    """Create and manage a structured task list for your current work session."""
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(f"Updated todo list to {todos}", tool_call_id=runtime.tool_call_id)
            ],
        }
    )


# ===========================================================================
# TODO 3: write_todos 도구의 설명을 작성하세요
# ===========================================================================
# 포함할 내용:
# - When to Use (3+ step의 복잡한 작업)
# - When NOT to Use (단순 작업)
# - Task States (pending, in_progress, completed)
# - "in_progress는 한 번에 1개만"
# - 완료 조건 (에러 없이 끝났을 때만 completed)

WRITE_TODOS_TOOL_DESCRIPTION = """Use this tool to create and manage a structured task list for your current work session.

Only use this tool if you think it will be helpful in staying organized. If the user's request is trivial and takes less than 3 steps, just do the task directly.

## When to Use
1. Complex multi-step tasks (3+ distinct steps)
2. User provides multiple tasks
3. The plan may need future revisions based on results

## When NOT to Use
1. Single, straightforward task
2. Task can be completed in less than 3 trivial steps
3. Purely conversational or informational task

## How to Use
1. Mark current task as "in_progress" BEFORE starting work
2. Mark task as "completed" IMMEDIATELY after finishing
3. Each call replaces the entire todo list — always provide the complete list

## Task States
- pending: Not yet started
- in_progress: Currently working on (limit to ONE at a time)
- completed: Finished successfully

## Completion Rules
- ONLY mark completed when FULLY accomplished with no errors
- If blocked, keep as in_progress and create a new task for the blocker
- Never skip status updates — the UI depends on accurate tracking"""


# ===========================================================================
# TODO 4 & 5: TodoListMiddleware 클래스
# ===========================================================================


class TodoListMiddleware(TodoListMiddlewareBase):
    """Middleware that provides todo list management capabilities to agents.

    write_todos 도구를 추가하고, 시스템 프롬프트로 사용법을 안내합니다.
    """

    state_schema = PlanningState  # type: ignore[assignment]

    # =======================================================================
    # TODO 4: middleware를 초기화하세요
    # =======================================================================
    # Step 1: super().__init__()
    # Step 2: self.system_prompt, self.tool_description 저장
    # Step 3: self.tools = [StructuredTool.from_function(
    #     name="write_todos", description=tool_description,
    #     func=_write_todos, args_schema=WriteTodosInput, infer_schema=False)]

    def __init__(
        self,
        *,
        system_prompt: str = WRITE_TODOS_SYSTEM_PROMPT,
        tool_description: str = WRITE_TODOS_TOOL_DESCRIPTION,
    ) -> None:
        super().__init__()
        self.system_prompt = system_prompt
        self.tool_description = tool_description

        self.tools = [
            StructuredTool.from_function(
                name="write_todos",
                description=tool_description,
                func=_write_todos,
                args_schema=WriteTodosInput,
                infer_schema=False,
            )
        ]

    # =======================================================================
    # TODO 5: system prompt에 todo 사용법을 추가하세요
    # =======================================================================
    # Step 1: request.system_message가 있으면 content_blocks에 추가, 없으면 새로 생성
    #   추가 형식: {"type": "text", "text": f"\n\n{self.system_prompt}"}
    # Step 2: SystemMessage(content=cast("list[str | dict[str, str]]", new_content))
    # Step 3: handler(request.override(system_message=new_system_message))

    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT] | AIMessage:
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
        return handler(request.override(system_message=new_system_message))
