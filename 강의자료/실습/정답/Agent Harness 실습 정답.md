# Agent Harness 실습 정답

이 문서는 Agent Harness 실습의 5개 TODO에 대한 정답과 해설입니다.

**구현 파일:**
- `ax_advanced_class/src/middleware/todo_middleware.py` (TODO 1-3)
- `ax_advanced_class/src/prompts/coding_agent_prompt.py` (TODO 4-5)

---

# Part 1: TodoListMiddleware 구현

## 사전 제공 코드 해설: `Todo` TypedDict + `PlanningState`

### 코드

```python
class Todo(TypedDict):
    """A single todo item with content and status."""

    content: str
    """The content/description of the todo item."""

    status: Literal["pending", "in_progress", "completed"]
    """The current status of the todo item."""


class PlanningState(AgentState[ResponseT]):
    """State schema for the todo middleware."""

    todos: Annotated[NotRequired[list[Todo]], OmitFromInput]
    """List of todo items for tracking task progress."""
```

### 해설

#### 1. `TypedDict` vs `dataclass` vs `BaseModel`

`Todo`를 `TypedDict`로 정의하는 이유:

```python
class Todo(TypedDict):
    content: str
    status: Literal["pending", "in_progress", "completed"]
```

LangGraph의 state는 딕셔너리 기반으로 동작합니다. `TypedDict`는 타입 안전성을 제공하면서도 일반 딕셔너리와 호환됩니다. `dataclass`나 `BaseModel`을 사용하면 직렬화/역직렬화 단계가 추가로 필요합니다.

#### 2. `Literal` 타입으로 상태 제한

```python
status: Literal["pending", "in_progress", "completed"]
```

`str` 대신 `Literal`을 사용하면:
- LLM이 tool schema에서 허용된 값 목록을 볼 수 있음 (JSON Schema의 `enum` 필드로 변환)
- 잘못된 상태값("done", "finished" 등)을 방지
- IDE에서 자동 완성 지원

#### 3. `NotRequired`와 `OmitFromInput`의 조합

```python
todos: Annotated[NotRequired[list[Todo]], OmitFromInput]
```

이 두 annotation은 각각 다른 역할을 합니다:

| Annotation | 역할 | 없으면 발생하는 문제 |
|-----------|------|-------------------|
| `NotRequired` | 초기값 없이 시작 가능 | `agent.invoke({"messages": [...]})` 호출 시 `todos` 키가 없다고 에러 |
| `OmitFromInput` | `invoke()` 입력에서 제외 | 사용자가 `{"messages": [...], "todos": [...]}` 형태로 직접 전달해야 함 |

`OmitFromInput`이 특히 중요합니다 -- `todos`는 agent가 내부적으로 관리하는 상태이지, 사용자가 외부에서 주입하는 값이 아닙니다. `create_agent`의 input schema 생성 시 이 필드를 건너뜁니다.

#### 4. `AgentState[ResponseT]` 상속

```python
class PlanningState(AgentState[ResponseT]):
```

`AgentState`에는 이미 `messages` 필드가 있습니다. `PlanningState`가 이를 상속하면서 `todos`를 추가합니다. `create_agent`는 모든 middleware의 `state_schema`를 자동으로 머지하므로, 최종 state는 `messages + todos + files + ...`가 됩니다.

---

## TODO 1: `_write_todos()` -- Tool 동작 함수

### 정답 코드

```python
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


async def _awrite_todos(
    runtime: ToolRuntime[ContextT, PlanningState[ResponseT]], todos: list[Todo]
) -> Command[Any]:
    """Create and manage a structured task list for your current work session."""
    return _write_todos(runtime, todos)
```

### 해설

#### 1. `Command`를 반환하는 이유

일반 tool은 문자열을 반환합니다:
```python
def my_tool(query: str) -> str:
    return f"Result: {query}"
# -> ToolMessage(content="Result: ...", tool_call_id=...)로 자동 변환
```

하지만 `write_todos`는 agent state의 `todos` 필드를 업데이트해야 합니다. 문자열만 반환하면 `messages`에만 추가되고 `todos`는 변하지 않습니다. `Command(update={...})`를 반환하면 LangGraph의 state reducer를 통해 여러 필드를 동시에 업데이트할 수 있습니다.

#### 2. `messages` 키를 반드시 포함해야 하는 이유

```python
Command(update={
    "todos": todos,         # state 업데이트
    "messages": [ToolMessage(...)],  # LLM에게 결과 알림
})
```

LLM은 tool 호출 후 반드시 `ToolMessage`를 받아야 합니다 -- 이것이 LLM API의 규약입니다. `messages`를 빠뜨리면:
- LLM이 tool 호출 결과를 볼 수 없음
- "tool call without response" 에러 발생 가능
- LLM이 tool이 실패했다고 판단하고 재시도

#### 3. `runtime.tool_call_id`의 역할

```python
ToolMessage(content=..., tool_call_id=runtime.tool_call_id)
```

LLM은 여러 tool을 동시에 호출할 수 있습니다 (parallel tool calls). `tool_call_id`는 "이 응답이 어떤 호출에 대한 것인지"를 연결하는 식별자입니다. 이것이 없으면 LLM이 어떤 tool call에 대한 응답인지 매칭할 수 없습니다.

#### 4. async 버전이 sync를 호출하는 패턴

```python
async def _awrite_todos(...) -> Command[Any]:
    return _write_todos(runtime, todos)  # sync 함수 직접 호출
```

`_write_todos`는 I/O 작업이 없습니다 (네트워크, 디스크 접근 없음). 단순히 `Command` 객체를 생성하여 반환할 뿐입니다. 이런 경우 async 버전에서 sync 함수를 직접 호출해도 event loop을 블로킹하지 않습니다.

---

## 사전 제공 코드 해설: `WRITE_TODOS_TOOL_DESCRIPTION` -- Tool 설명

### 코드

```python
WRITE_TODOS_TOOL_DESCRIPTION = """Use this tool to create and manage a structured task list for your current work session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.

Only use this tool if you think it will be helpful in staying organized. If the user's request is trivial and takes less than 3 steps, it is better to NOT use this tool and just do the task directly.

## When to Use This Tool
Use this tool in these scenarios:

1. Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
3. User explicitly requests todo list - When the user directly asks you to use the todo list
4. User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
5. The plan may need future revisions or updates based on results from the first few steps

## How to Use This Tool
1. When you start working on a task - Mark it as in_progress BEFORE beginning work.
2. After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation.
3. You can also update future tasks, such as deleting them if they are no longer necessary, or adding new tasks that are necessary. Don't change previously completed tasks.
4. You can make several updates to the todo list at once. For example, when you complete a task, you can mark the next task you need to start as in_progress.

## When NOT to Use This Tool
It is important to skip using this tool when:
1. There is only a single, straightforward task
2. The task is trivial and tracking it provides no benefit
3. The task can be completed in less than 3 trivial steps
4. The task is purely conversational or informational

## Task States and Management

1. **Task States**: Use these states to track progress:
   - pending: Task not yet started
   - in_progress: Currently working on (limit to ONE task at a time -- complete current task before starting next)
   - completed: Task finished successfully

2. **Task Management**:
   - Update task status in real-time as you work
   - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
   - Complete current tasks before starting new ones
   - Remove tasks that are no longer relevant from the list entirely
   - IMPORTANT: When you write this todo list, you should mark your first task (or tasks) as in_progress immediately!.
   - IMPORTANT: Unless all tasks are completed, you should always have at least one task in_progress to show the user that you are working on something.

3. **Task Completion Requirements**:
   - ONLY mark a task as completed when you have FULLY accomplished it
   - If you encounter errors, blockers, or cannot finish, keep the task as in_progress
   - When blocked, create a new task describing what needs to be resolved
   - Never mark a task as completed if:
     - There are unresolved issues or errors
     - Work is partial or incomplete
     - You encountered blockers that prevent completion
     - You couldn't find necessary resources or dependencies
     - Quality standards haven't been met

4. **Task Breakdown**:
   - Create specific, actionable items
   - Break complex tasks into smaller, manageable steps
   - Use clear, descriptive task names

Being proactive with task management demonstrates attentiveness and ensures you complete all requirements successfully
Remember: If you only need to make a few tool calls to complete a task, and it is clear what you need to do, it is better to just do the task directly and NOT call this tool at all."""
```

### 해설

#### 1. 이 description이 길어야 하는 이유

Tool description의 길이는 도구의 복잡도에 비례해야 합니다. `write_todos`는 단순히 데이터를 저장하는 것이 아니라, **특정 규칙에 따라 사용**되어야 합니다:
- 언제 사용하고 언제 사용하지 않는지
- 상태 전이 규칙 (pending -> in_progress -> completed)
- 동시성 제약 (in_progress는 1개만)

이 규칙들이 description에 없으면, LLM은 자의적으로 판단합니다 -- 모든 작업에 todo를 생성하거나, 여러 task를 동시에 in_progress로 만들거나, 완료되지 않은 task를 completed로 표시합니다.

#### 2. "When NOT to Use" 섹션의 중요성

```
## When NOT to Use This Tool
1. There is only a single, straightforward task
2. The task is trivial and tracking it provides no benefit
3. The task can be completed in less than 3 trivial steps
```

LLM은 도구가 있으면 사용하려는 경향이 있습니다. "안녕하세요"라는 인사에도 todo를 생성할 수 있습니다. "사용하지 말아야 할 때"를 명시하면 불필요한 도구 호출을 줄여 token을 절약하고 응답 속도를 높입니다.

#### 3. "in_progress는 1개만" 규칙

```
limit to ONE task at a time -- complete current task before starting next
```

이 규칙이 없으면 LLM이 3개의 task를 모두 in_progress로 만들고 동시에 진행하려 합니다. 하지만 LLM은 실제로 병렬 작업을 할 수 없으므로 -- tool 호출은 순차적 -- 이런 상태는 사용자에게 잘못된 진행 상황을 보여줍니다.

#### 4. "교체 방식" 명시

```
Each call to write_todos replaces the entire todo list. Always provide the complete list with current statuses.
```

이것을 명시하지 않으면 LLM이 변경된 task만 전달하려 합니다:
```python
# 잘못된 사용 (delta만 전달)
write_todos([{"content": "Task 2", "status": "completed"}])

# 올바른 사용 (전체 리스트 전달)
write_todos([
    {"content": "Task 1", "status": "completed"},
    {"content": "Task 2", "status": "completed"},
    {"content": "Task 3", "status": "in_progress"},
])
```

---

## TODO 2: `TodoListMiddleware.__init__()` -- 3가지 축 조립

### 정답 코드

```python
class TodoListMiddleware(TodoListMiddlewareBase):

    state_schema = PlanningState  # State 축

    def __init__(
        self,
        *,
        system_prompt: str = WRITE_TODOS_SYSTEM_PROMPT,
        tool_description: str = WRITE_TODOS_TOOL_DESCRIPTION,
    ) -> None:
        super().__init__()
        self.system_prompt = system_prompt
        self.tool_description = tool_description

        self.tools = [  # Tool 축
            StructuredTool.from_function(
                name="write_todos",
                description=tool_description,
                func=_write_todos,
                coroutine=_awrite_todos,
                args_schema=WriteTodosInput,
                infer_schema=False,
            )
        ]
```

### 해설

#### 1. Middleware의 3가지 축이 `__init__`에서 만나는 지점

```python
state_schema = PlanningState      # (1) State: agent state에 todos 추가
self.tools = [...]                # (2) Tool: write_todos 도구 등록
self.system_prompt = system_prompt # (3) Prompt: wrap_model_call에서 사용
```

`create_agent`는 middleware 목록을 받아 이 3가지를 자동으로 조합합니다:
- `state_schema`들을 머지하여 최종 state 타입 생성
- `self.tools`를 수집하여 LLM에게 제공할 도구 목록 구성
- `wrap_model_call`을 체이닝하여 시스템 프롬프트 조립

#### 2. `super().__init__()` 호출

```python
super().__init__()
```

`AgentMiddleware`의 `__init__`은 내부 상태를 초기화합니다. 이것을 빠뜨리면 middleware 체이닝이 올바르게 동작하지 않을 수 있습니다.

#### 3. `infer_schema=False`의 의미

```python
StructuredTool.from_function(
    ...
    args_schema=WriteTodosInput,
    infer_schema=False,
)
```

기본적으로 `StructuredTool`은 함수의 type hints에서 schema를 자동 추론합니다. 하지만 `_write_todos`에는 `runtime` 파라미터가 있고, 이것은 LLM에게 노출되어서는 안 됩니다 (`runtime`은 시스템이 자동 주입하는 값). `infer_schema=False`로 설정하고 `args_schema=WriteTodosInput`을 명시적으로 제공하면, `runtime`을 제외한 `todos` 파라미터만 LLM에게 노출됩니다.

```python
class WriteTodosInput(BaseModel):
    todos: list[Todo]  # LLM에게 보이는 파라미터는 이것뿐
```

#### 4. keyword-only arguments (`*`)

```python
def __init__(self, *, system_prompt=..., tool_description=...):
```

`*` 이후의 파라미터는 반드시 키워드로 전달해야 합니다:
```python
TodoListMiddleware(system_prompt="custom...")  # OK
TodoListMiddleware("custom...")                # Error
```

이 패턴은 실수로 인자 순서를 바꾸는 것을 방지합니다.

---

## TODO 3: `wrap_model_call()` -- Prompt 주입

### 정답 코드

```python
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
```

### 해설

#### 1. `content_blocks`로 기존 프롬프트 보존

```python
new_system_content = [
    *request.system_message.content_blocks,  # 기존 content blocks 전부 유지
    {"type": "text", "text": f"\n\n{self.system_prompt}"},  # 새로운 block 추가
]
```

시스템 메시지는 여러 content block으로 구성될 수 있습니다 (text, image 등). `content_blocks`를 사용하면 기존 block들을 그대로 유지하면서 새 텍스트를 **추가**합니다. 만약 `request.system_message.content`(문자열)에 직접 concat하면 non-text block이 손실될 수 있습니다.

#### 2. Middleware 체인에서의 프롬프트 누적

middleware가 `[FilesystemMiddleware, TodoListMiddleware, dynamic_prompt]` 순서로 등록되면:

```
최초 system message: "You are a helpful assistant."
    |
    v
FilesystemMiddleware.wrap_model_call():
    + FILESYSTEM_SYSTEM_PROMPT
    + EXECUTION_SYSTEM_PROMPT (조건부)
    |
    v
TodoListMiddleware.wrap_model_call():
    + WRITE_TODOS_SYSTEM_PROMPT
    |
    v
dynamic_prompt:
    + CODING_AGENT_SYSTEM_PROMPT
    + SOFT_RULES_PROMPT
    + dynamic context
    |
    v
최종 system message (LLM에게 전달)
```

각 middleware가 `request.system_message`에 자신의 프롬프트를 추가하므로, 최종 시스템 메시지는 모든 프롬프트의 합입니다.

#### 3. `request.override()` -- 불변 패턴

```python
return handler(request.override(system_message=new_system_message))
```

`request`를 직접 수정하지 않고 `override()`로 새 request를 만듭니다. 이 패턴은:
- 원본 request를 보존하여 디버깅 용이
- 다른 middleware가 동일한 request를 참조해도 안전
- 함수형 프로그래밍의 immutability 원칙 준수

---

# Part 2: Harness Prompting -- Coding Agent의 행동 규칙

## TODO 4-5: PHASE 2/3 구체화 (PHASE 1은 사전 제공)

### 정답 코드

실제 `CODING_AGENT_SYSTEM_PROMPT`의 전체 내용입니다 (`coding_agent_prompt.py` 20-134행):

```python
CODING_AGENT_SYSTEM_PROMPT = """You are a Coding Agent working incrementally on a long-running project.

## Your Role

You work in discrete sessions, implementing ONE feature at a time. Each session follows a strict lifecycle to ensure clean state and progress tracking.

CRITICAL: Work on ONLY ONE feature per session. Leave the environment in a clean, working state.

## Session Lifecycle

### PHASE 1: START (Recovery & Orientation)

At the START of EVERY session, you MUST:

1. **Understand location**: Run `pwd` to see your working directory
2. **Restore context**: Run `./init.sh` if it exists - this script bridges session gaps by:
   - Showing git commit history (what's been completed)
   - Displaying progress.md (current project status)
   - Showing feature_list.json (remaining features)
   - Starting dev server if applicable
3. **Smoke test**: Run a basic test to verify the app is in working state

If the smoke test fails, your FIRST priority is to fix the broken state before proceeding.

### PHASE 2: WORK (Feature Implementation)

Once the environment is verified:

1. **Select feature**: Choose ONE feature where `passes=false`
   - Prioritize `high` priority features first
   - Check dependencies are satisfied (all dependent features have `passes=true`)

2. **Focus**: Work ONLY on that feature - no feature hopping!

3. **Implement**: Write the code needed for the feature
   - Follow existing code patterns
   - Write clean, maintainable code
   - Add necessary tests

4. **Test**: Verify the feature end-to-end
   - Test like a real user would
   - Use browser automation tools if applicable
   - Verify edge cases
   - Only mark `passes=true` when test succeeds

### PHASE 3: END (Commit & Handoff)

Before ending EVERY session, you MUST complete ALL of these steps:

1. **Update progress.md**: Use write_file or edit_file tool to append session notes:
   ### Session N - [timestamp]
   Feature: feature-XXX - [description]
   Status: [Completed|In Progress|Blocked]
   Changes:
   - [list of changes made]
   Next steps:
   - [what the next agent should do]

2. **Update feature_list.json**: Use edit_file tool to update the feature list:
   - Set "passes": true for the completed feature
   - This is REQUIRED - the feature is not considered done until feature_list.json is updated

3. **Commit**: Create a git commit with clear message
   feat(feature-XXX): [description]
   - What was implemented
   - What was tested
   - Any known issues

4. **Verify clean state**: Ensure the app works and no uncommitted changes remain

CRITICAL: Steps 1 and 2 MUST use file tools (write_file/edit_file). Do NOT skip these file updates.

## Critical Rules

1. **ONE feature at a time** - No feature hopping!
2. **Never declare done early** - Project is NOT complete until ALL features pass
3. **Never skip E2E testing** - A feature isn't done without verification
4. **Never leave broken state** - Always commit working code
5. **Always update files in PHASE 3** - You MUST use file tools to update progress.md AND feature_list.json before committing
6. **Always commit** - Git-based checkpointing allows recovery from bad changes
7. **Use write_todos proactively** - Create todos when receiving a goal. CRITICAL: Call write_todos EVERY time status changes - mark in_progress BEFORE starting work, mark completed IMMEDIATELY after finishing. Never batch status updates."""
```

### 해설

#### 사전 제공: PHASE 1 -- 컨텍스트 해석 프로토콜

```
1. Run `pwd` to see your working directory
2. Run `./init.sh` if it exists
3. Run a basic test to verify the app is in working state
```

**왜 이 순서인가:**

| 단계 | 목적 | Harness 개념 |
|------|------|-------------|
| `pwd` | 작업 디렉토리 확인 | 기본 orientation -- LLM이 "어디에 있는지" 추론하지 않고 확인 |
| `./init.sh` | 이전 세션 컨텍스트 복구 | Context 외부화 -- init.sh가 git log, progress.md, feature_list.json을 보여줌 |
| Smoke test | 앱이 정상인지 확인 | 안전망 -- 깨진 상태에서 새 기능 추가는 더 큰 문제를 만듦 |

**핵심 원칙**: "추론하게 하지 말고, 읽게 만들어라."

나쁜 프롬프트: "프로젝트 상태를 확인하세요" -> LLM이 추측
좋은 프롬프트: "Run `./init.sh`" -> LLM이 실제로 실행하고 출력을 읽음

`init.sh`는 Cold Start Recovery의 핵심입니다. 새 세션의 LLM은 이전 세션의 대화 내용을 전혀 모릅니다. 하지만 `init.sh`가 git log, progress.md, feature_list.json을 출력하면, LLM은 이 외부 상태를 읽고 현재 프로젝트 상황을 파악할 수 있습니다.

#### TODO 4: PHASE 2 -- 작업 단위 격리

```
1. Select ONE feature where passes=false
   - Prioritize high priority features first
   - Check dependencies are satisfied
2. Focus: Work ONLY on that feature
3. Implement
4. Test: Verify end-to-end
   - Only mark passes=true when test succeeds
```

**왜 "하나만"인가 -- Compound Reliability:**

Agent의 각 step 성공률이 95%라고 가정하면:
- 1개 feature (5 steps): 0.95^5 = 77.4% 성공률
- 3개 features (15 steps): 0.95^15 = 46.3% 성공률
- 5개 features (25 steps): 0.95^25 = 27.7% 성공률

여러 feature를 한 세션에서 시도하면 실패 확률이 급격히 증가합니다. 하나의 feature만 작업하고 git commit으로 고정하면, 실패해도 `git revert`로 깨끗한 상태로 돌아갈 수 있습니다.

**Feature 선택 규칙이 구체적인 이유:**

```
passes=false인 것 중 high priority 선택
dependencies가 모두 passes=true인지 확인
```

이 규칙 없이 "적절한 feature를 선택하세요"라고 하면:
- LLM이 가장 쉬운 feature를 선택 (의존성 있는 feature 건너뛰기)
- 이미 완료된 feature를 다시 작업
- low priority feature를 먼저 구현

구체적인 기준을 제시하면 LLM의 선택이 예측 가능해집니다.

**`passes=true`는 테스트 후에만:**

```
Only mark passes=true when test succeeds
```

LLM은 코드를 작성한 후 "완료"라고 선언하는 경향이 있습니다. 하지만 코드 작성과 동작 확인은 다릅니다. 이 규칙이 E2E 테스트를 강제하여, 실제로 동작하는 코드만 "완료"로 표시되게 합니다.

#### TODO 5: PHASE 3 -- Context 외부화

```
1. Update progress.md (write_file or edit_file)
2. Update feature_list.json (edit_file)
3. Git commit
4. Verify clean state
```

**이 순서가 중요한 이유:**

```
[올바른 순서]
progress.md 수정 -> feature_list.json 수정 -> git add -> git commit
-> 다음 세션이 git log와 파일을 읽으면 최신 정보가 있음

[잘못된 순서]
git commit -> progress.md 수정
-> 다음 세션이 commit을 체크아웃하면 progress.md에 최신 정보가 없음
```

**왜 file tool을 명시하는가:**

```
Steps 1 and 2 MUST use file tools (write_file/edit_file). Do NOT skip these file updates.
```

이 강조가 없으면 LLM이:
- "progress.md를 업데이트했습니다"라고 말만 하고 실제로 파일을 수정하지 않음
- bash의 `echo >> progress.md`로 시도 (ToolValidationMiddleware가 차단할 수 있음)
- git commit message에 내용을 넣고 파일 업데이트를 건너뜀

**Git commit의 메시지 형식:**

```
feat(feature-XXX): [description]
- What was implemented
- What was tested
- Any known issues
```

Conventional Commits 형식을 따릅니다. 다음 세션의 LLM이 `git log`를 읽을 때, 각 commit이 어떤 feature와 관련되었는지 즉시 파악할 수 있습니다.

**Clean state 확인:**

```
Verify clean state: Ensure the app works and no uncommitted changes remain
```

이것은 다음 세션을 위한 배려입니다. uncommitted changes가 남아있으면 다음 세션의 LLM이 "이 변경은 의도한 것인가 실수인가?" 판단해야 하며, 이는 불필요한 컨텍스트 소비입니다.

---

## Dynamic Prompt와의 연결

`coding_agent_prompt.py`에는 `CODING_AGENT_SYSTEM_PROMPT` (정적) 외에 `coding_agent_dynamic_prompt` (동적)도 있습니다:

```python
@dynamic_prompt
def coding_agent_dynamic_prompt(request: ModelRequest) -> str:
    state = request.state
    workspace = PermissionConfig().workspace_root
    dynamic_content = f"""
# CURRENT SESSION CONTEXT
Workspace: {workspace}
todos: {state.get("todos", [])}
...
"""
    return CODING_AGENT_SYSTEM_PROMPT + SOFT_RULES_PROMPT + dynamic_content
```

정적 프롬프트(PHASE 1/2/3 규칙)는 **Prompt Caching**의 이점을 받습니다 -- 매번 같은 내용이므로 캐시됩니다. 동적 프롬프트(현재 todos, workspace 등)는 **매 호출마다 변경**되므로 캐시 접두사 뒤에 배치됩니다.

```
[Cache 가능한 부분]                  [매번 변경되는 부분]
CODING_AGENT_SYSTEM_PROMPT  +  SOFT_RULES  +  dynamic_content
(PHASE 1/2/3 규칙)            (도구 사용 규칙)  (todos, workspace)
```

---

## 전체 흐름 요약

```
Session 시작
  |
  v
PHASE 1: pwd -> init.sh -> smoke test
  |                |
  |                +-- git log, progress.md, feature_list.json 출력
  |                +-- 실패하면 먼저 수정
  |
  v
PHASE 2: feature 선택 -> write_todos -> 구현 -> 테스트
  |                          |
  |                          +-- todos: [{content: "Step 1", status: "in_progress"}, ...]
  |                          +-- 매 step 완료 시 status 업데이트
  |
  v
PHASE 3: progress.md -> feature_list.json -> git commit -> clean state
  |           |                |                  |
  |           |                |                  +-- git status로 확인
  |           |                +-- passes: true
  |           +-- Session N 기록
  |
  v
Session 종료 (다음 세션의 init.sh가 이 상태를 읽음)
```
