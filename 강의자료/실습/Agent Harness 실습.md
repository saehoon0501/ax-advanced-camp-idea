# Agent Harness 실습

Dynamic Prompt 실습에서 Coding Agent의 정적 프롬프트(`CODING_AGENT_SYSTEM_PROMPT`)와 동적 컨텍스트 주입을 구현했습니다. 하지만 프롬프트만으로는 agent의 행동을 충분히 제어할 수 없습니다 — agent가 "작업 목록을 관리하라"는 지시를 받아도, **관리할 도구가 없으면** 아무것도 할 수 없습니다.

이 실습에서는 **Harness 패턴**을 두 가지 방향으로 구현합니다:

1. **TodoListMiddleware** — agent에게 작업 추적 도구를 제공하는 middleware (State + Tool + Prompt 패키지)
2. **Harness Prompting** — Dynamic Prompt 실습의 CODING_AGENT_SYSTEM_PROMPT를 Harness behavior로 보강

**구현 파일:**
- `ax_advanced_class/src/middleware/todo_middleware.py` (신규 생성)
- `ax_advanced_class/src/prompts/coding_agent_prompt.py` (Dynamic Prompt 실습에서 이어서)

## 배운 개념과 실습의 연결

| Agent Harness 개념 | 이 실습에서 적용하는 방법 |
|-------------------|-------------------------|
| 암묵적 기억 → 명시적 상태 | Todo를 agent state에 명시적으로 저장 (메시지 히스토리에 의존하지 않음) |
| 컨텍스트 해석 프로토콜 | PHASE 1에서 pwd → init.sh → progress.md → feature_list.json 순서 강제 |
| 작업 단위 격리 | PHASE 2에서 하나의 feature만 선택, todo로 세부 단계 추적 |
| Git 안전망 + E2E 테스트 강제 | PHASE 3에서 progress.md 업데이트 → feature_list.json 업데이트 → git commit 순서 강제 |
| Compound Reliability | todo를 통해 작업 단위를 작게 유지하여 step당 성공률 유지 |

## 이 실습의 위치

```
Dynamic Prompt 실습 (이전)
  └─ TODO 1-2: dynamic context + 합성 순서

Agent Harness 실습 (이번) ← 여기
  └─ Part 1: TodoListMiddleware 구현 — agent에게 작업 추적 "도구" 제공
  └─ Part 2: Harness Prompting — Phase 1/2/3의 구체적 행동 규칙 작성
```

---

# Part 1: TodoListMiddleware 구현

## 우리가 만들 것

Middleware의 3가지 축을 **하나의 middleware에 모두 적용**합니다:

```
TodoListMiddleware
  ├─ State: todos 필드를 agent state에 추가
  ├─ Tool:  write_todos 도구를 agent에 등록
  └─ Prompt: "write_todos를 이렇게 써라"를 system prompt에 주입
```

middleware를 `agent_specs.py`에 추가하면, agent가 자동으로:
- `todos` state 필드를 갖게 되고
- `write_todos` tool을 사용할 수 있게 되고
- system prompt에 사용법이 주입됩니다

## 실습 구조

3개의 TODO를 순서대로 구현합니다.

| TODO | 구현할 것 | Middleware 축 |
|------|----------|--------------|
| TODO 1 | `write_todos` tool 함수 | **Tool** 주입 — 도구의 동작 |
| TODO 2 | `TodoListMiddleware.__init__` | 3가지 축 조립 |
| TODO 3 | `TodoListMiddleware.wrap_model_call` | **Prompt** 주입 |

---

## 사전 제공 코드

TODO 1-3을 구현하기 전에, 아래 코드를 먼저 읽으세요. 이 코드는 이미 구현되어 있습니다.

### Todo & PlanningState — State 확장

```python
class Todo(TypedDict):
    content: str                                              # 할 일 내용
    status: Literal["pending", "in_progress", "completed"]    # 상태

class PlanningState(AgentState[ResponseT]):
    todos: Annotated[NotRequired[list[Todo]], OmitFromInput]  # agent state에 추가되는 필드
```

- `Todo`는 `TypedDict` — content(내용)과 status(상태) 두 필드
- `Literal["pending", "in_progress", "completed"]` — 3가지 상태만 허용
- `PlanningState`가 `AgentState`를 상속 — `create_agent`가 기존 `messages` 필드와 자동 머지
- `NotRequired` — 초기값 없이 시작 가능 (첫 `write_todos` 호출 전까지 비어있음)
- `OmitFromInput` — `invoke()` 시 입력에서 제외 (내부 관리 필드)

### WRITE_TODOS_TOOL_DESCRIPTION — Tool 설명

```python
WRITE_TODOS_TOOL_DESCRIPTION = """Create and manage a todo list to track progress on complex tasks.

When to Use:
- Tasks requiring 3+ steps
- When the user requests multiple related changes
- Do NOT use for simple, single-step tasks

How to Use:
- Before starting a task: mark it as in_progress
- After completing a task: immediately mark it as completed
- Always provide the FULL list (this replaces the existing list entirely)

Task States:
- pending: not yet started
- in_progress: currently being worked on (EXACTLY ONE at a time!)
- completed: finished successfully

Completion Rules:
- Only mark completed when fully done with no errors
- If blocked or errored, keep as in_progress
"""
```

- **"EXACTLY ONE at a time!"** — 이 규칙이 없으면 agent가 여러 작업을 동시에 `in_progress`로 표시
- **"replaces the existing list entirely"** — append가 아니라 전체 교체 방식임을 명시
- **When to Use / When NOT to use** — 사용 조건과 미사용 조건 모두 명시해야 LLM이 정확히 판단

---

## TODO 1: Tool 동작 — `write_todos` 함수

**배울 개념:** Tool이 `Command`를 반환하여 agent state를 업데이트

`write_todos` tool은 호출되면 전체 todo 리스트를 교체합니다. 핵심은 **`Command(update=...)`를 반환**하여 agent state의 `todos` 필드를 업데이트하는 것입니다.

**구현할 코드:**

```python
class WriteTodosInput(BaseModel):
    """Input schema for the write_todos tool."""
    todos: list[Todo]


def _write_todos(
    runtime: ToolRuntime[ContextT, PlanningState[ResponseT]], todos: list[Todo]
) -> Command[Any]:
    # TODO 1: todo 리스트를 state에 업데이트하는 Command를 반환하세요
    #
    # Command(update={...})를 사용하여:
    #   1. "todos" 키에 새 todo 리스트를 설정
    #   2. "messages" 키에 ToolMessage를 추가 (LLM이 결과를 볼 수 있도록)
    #      힌트: ToolMessage(content=f"Updated todo list to {todos}",
    #                        tool_call_id=runtime.tool_call_id)
    #
    # 왜 Command인가?
    #   일반 tool은 문자열을 반환하지만, state를 수정해야 하는 tool은
    #   Command를 반환해야 LangGraph의 state reducer를 통해 업데이트됩니다.
    #
    return Command(update={})
```

**확인:** `Command(update={"todos": todos, "messages": [ToolMessage(...)]})`를 반환하는지 확인하세요. `messages`를 포함하지 않으면 LLM이 tool 결과를 볼 수 없습니다.

---

## TODO 2: 3가지 축 조립 — `__init__`

**배울 개념:** Middleware가 State + Tool + Prompt를 하나의 패키지로 제공

`__init__`에서 `state_schema`, `self.tools`, prompt 설정을 모두 조립합니다.

**구현할 코드:**

```python
# WRITE_TODOS_SYSTEM_PROMPT는 _internals/todo_helpers.py에서 import됩니다 (이미 제공됨)

class TodoListMiddleware(TodoListMiddlewareBase):

    state_schema = PlanningState  # ← State 축: create_agent가 자동 머지

    def __init__(
        self,
        *,
        system_prompt: str = WRITE_TODOS_SYSTEM_PROMPT,
        tool_description: str = WRITE_TODOS_TOOL_DESCRIPTION,
    ) -> None:
        # TODO 2: middleware를 초기화하세요
        #
        # Step 1: super().__init__() 호출
        #
        # Step 2: system_prompt와 tool_description을 인스턴스 변수로 저장
        #
        # Step 3: self.tools에 write_todos tool 등록 ← Tool 축
        #   힌트: StructuredTool.from_function(
        #       name="write_todos",
        #       description=tool_description,
        #       func=_write_todos,
        #       args_schema=WriteTodosInput,
        #       infer_schema=False,
        #   )
        #
        pass
```

**확인:** `self.tools = [...]`에 tool이 등록되었는지 확인하세요. 이 리스트가 비어있으면 agent가 write_todos를 사용할 수 없습니다.

---

## TODO 3: Prompt 주입 — `wrap_model_call`

**배울 개념:** `wrap_model_call`에서 `request.override(system_message=...)`로 매 LLM 호출마다 prompt 주입

agent가 LLM을 호출할 때마다, 기존 system prompt 뒤에 "write_todos 사용법"을 추가합니다.

**구현할 코드:**

```python
    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT] | AIMessage:
        # TODO 3: system prompt에 todo 사용법을 추가하세요
        #
        # Step 1: 기존 system message가 있는지 확인
        #   request.system_message is not None
        #
        # Step 2: 기존 content blocks에 self.system_prompt 추가
        #   new_system_content = [
        #       *request.system_message.content_blocks,
        #       {"type": "text", "text": f"\n\n{self.system_prompt}"},
        #   ]
        #
        # Step 3: SystemMessage로 감싸기
        #   new_system_message = SystemMessage(content=new_system_content)
        #
        # Step 4: request.override(system_message=new_system_message)로
        #         수정된 request를 handler에 전달
        #
        return handler(request)  # ← 수정 필요
```

**확인:** `request.override(system_message=...)`를 사용했는지 확인하세요. `request`를 직접 수정하면 안 됩니다 — `override()`로 새 request를 만들어야 합니다.

---

## Part 1 → Part 2 전환: 메커니즘에서 행동 규칙으로

Part 1에서 TodoListMiddleware를 통해 agent에게 작업 추적 **메커니즘**(State + Tool + Prompt)을 제공했습니다.

이제 Part 2에서는 이 메커니즘을 **언제, 어떻게 활용할지**를 Coding Agent의 시스템 프롬프트에 행동 규칙으로 정의합니다.

```
Part 1: 메커니즘 (HOW)              Part 2: 행동 규칙 (WHEN & WHY)
┌─────────────────────┐            ┌─────────────────────────────┐
│ PlanningState.todos  │            │ PHASE 1: pwd → init.sh      │
│ write_todos tool     │ ────────→  │ PHASE 2: 1 feature + todos  │
│ system prompt 주입    │            │ PHASE 3: commit + handoff   │
└─────────────────────┘            └─────────────────────────────┘
```

메커니즘 없는 행동 규칙은 무력하고, 행동 규칙 없는 메커니즘은 방향을 잃습니다 — **둘 다 있어야 Harness가 완성**됩니다.

---

# Part 2: Harness Prompting — Coding Agent의 행동 규칙

Dynamic Prompt 실습에서 `CODING_AGENT_SYSTEM_PROMPT`의 Phase 1/2/3 헤더를 작성했습니다. 이제 각 Phase에 **Harness behavior**의 구체적 규칙을 채웁니다.

## 왜 프롬프트로 Harness를 구현하는가

Agent Harness의 4가지 전략을 프롬프트로 강제합니다:

| Harness 전략 | 프롬프트에서 구현 |
|---|---|
| Context 외부화 | PHASE 3에서 progress.md, feature_list.json 업데이트 강제 |
| 해석 프로토콜 | PHASE 1에서 pwd → init.sh → progress.md → feature_list.json 순서 강제 |
| 작업 단위 격리 | "ONE feature per session" + write_todos로 세부 추적 |
| E2E 테스트 강제 | PHASE 2에서 "passes=true는 테스트 통과 후에만" |

## 프롬프트 작성 가이드: 무엇이 다른가

TODO 4-5을 시작하기 전에, Agent가 **실제로 따르는 프롬프트**와 **무시하는 프롬프트**의 차이를 이해합니다.

### 나쁜 프롬프트 vs 좋은 프롬프트

**나쁜 프롬프트 (모호함):**
```
세션을 시작할 때 프로젝트 상태를 확인하세요.
```
→ Agent가 "상태를 확인하겠습니다"라고 **말만** 하고 실제로 파일을 안 읽음. 모델이 **추론으로 추측**함.

**좋은 프롬프트 (구체적 행동 강제):**
```
1. Run `pwd` to confirm your working directory.
2. Run `./init.sh`. If it fails with permission error, run `chmod +x init.sh` first.
3. Use `read_file` to read `progress.md`. Check the last session's Status field.
4. Use `read_file` to read `feature_list.json`. Identify features with passes=false.
```
→ Agent가 실제로 4개의 tool을 순서대로 호출. **외부 상태를 읽어서** 파악.

### 핵심 원칙

| 프롬프트 스타일 | Agent 행동 | 결과 |
|---------------|-----------|------|
| "상태를 확인하세요" | 추론으로 추측 | 틀린 가정으로 시작 |
| "이 tool로 이 파일을 읽으세요" | 도구를 호출하여 실제 확인 | 정확한 상태로 시작 |
| "적절히 처리하세요" | 모델이 자의적으로 판단 | 예측 불가능한 행동 |
| "X하세요. 실패하면 Y하세요." | 명확한 분기 처리 | 실패에도 복구 가능 |

**원칙: 추론하게 하지 말고, 읽게 만들어라. 판단하게 하지 말고, 절차를 따르게 하라.**

이 원칙을 아래 TODO 4-5에 적용합니다.

## 실습 구조

2개의 TODO를 구현합니다.

| TODO | Phase | 구현할 것 | Harness 전략 |
|------|-------|----------|-------------|
| TODO 4 | PHASE 2 | 작업 단위 격리 규칙 | 작업 단위 격리 + Compound Reliability |
| TODO 5 | PHASE 3 | Context 외부화 규칙 | Context 외부화 + Git 안전망 |

---

## 사전 제공 코드

TODO 4-5을 작성할 때 아래 PHASE 1을 **패턴**으로 참고하세요. 이 프롬프트는 이미 작성되어 있습니다.

### PHASE 1: START — 컨텍스트 해석 프로토콜

```
### PHASE 1: START (Recovery & Orientation)

You MUST complete ALL of these steps before any implementation work:

1. Run `pwd` to confirm your working directory.
2. Run `./init.sh` to restore context from the previous session.
   - If it fails with permission error, run `chmod +x init.sh` first.
   - This script shows: git log, progress.md summary, and feature_list.json status.
3. Use `read_file` to read `progress.md`. Check the last session's Status field.
   - If Status was "Blocked" or "In Progress", read the Next Steps section.
4. Use `read_file` to read `feature_list.json`. Identify features where passes=false.
5. Run the smoke test: `npm test` (or the project's test command).
   - If tests fail, you MUST fix the failure before implementing new features.
   - Do NOT skip this step — broken tests mean the previous session left bad state.
```

**이 프롬프트가 좋은 이유 (TODO 4-5에 같은 패턴을 적용하세요):**
- **구체적 도구 명시** — "확인하세요" 대신 `pwd`, `read_file`, `./init.sh` 등 정확한 tool call 지정
- **실패 분기 포함** — "permission error면 chmod", "테스트 실패면 먼저 수정" 등 fallback 제공
- **강제 어투** — "You MUST", "Do NOT skip" — 권장이 아닌 의무
- **순서 강제** — 번호로 순서를 명시하여 agent가 건너뛰지 못하게 함

---

## TODO 4: PHASE 2 구체화 — 작업 단위 격리

**구현 파일:** `coding_agent_prompt.py` — `CODING_AGENT_SYSTEM_PROMPT` 안의 PHASE 2 섹션

```python
### PHASE 2: WORK (Feature Implementation)

# TODO 4: 하나의 feature를 선택하고 구현하는 단계를 작성하세요
#
# Agent Harness.md의 "작업 단위 격리" 참고:
#
# 1. Feature 선택 — passes=false인 것 중 high priority 선택
#    dependencies가 모두 passes=true인지 확인
# 2. write_todos로 세부 단계 생성 — feature의 steps를 todo로 변환
# 3. 구현 — 하나의 feature만 집중
# 4. 테스트 — E2E로 검증, passes=true는 테스트 통과 후에만
#
# Compound Reliability 관점:
#   여러 feature를 한 세션에 시도하면 0.95^50 = 실패 확실
#   하나만 집중하면 0.95^5 = 77.4% + git revert 안전망
```

## TODO 5: PHASE 3 구체화 — Context 외부화

```python
### PHASE 3: END (Commit & Handoff)

# TODO 5: 세션 종료 전 반드시 수행할 단계를 작성하세요
#
# Agent Harness.md의 "Context 외부화" 참고:
#
# 1. progress.md 업데이트 — 세션 기록 (edit_file 또는 write_file 사용)
#    ### Session N - [timestamp]
#    Feature: feature-XXX
#    Status: Completed|In Progress|Blocked
#    Changes: [변경 목록]
#    Next steps: [다음 agent가 할 일]
#
# 2. feature_list.json 업데이트 — passes=true로 변경 (edit_file 사용)
#    테스트를 통과한 feature만!
#
# 3. Git commit — 깨끗한 상태 고정
#
# 4. Clean state 확인 — uncommitted changes 없는지 확인
#
# 왜 이 순서인가?
#   파일 업데이트 → commit 순서가 아니면,
#   다음 세션 agent가 progress.md를 읽어도
#   최신 정보가 없는 상태로 시작합니다.
```

---

## Agent에 미들웨어 연결하기

TodoListMiddleware를 구현한 후, `agent_specs.py`에서 미들웨어 스택에 추가합니다:

```python
# ax_advanced_class/src/agents/agent_specs.py

from ax_advanced_class.src.middleware.todo_middleware import TodoListMiddleware

middleware = [
    ToolValidationMiddleware(config),
    _create_filesystem_middleware(config),
    TodoListMiddleware(),                 # ← Part 1에서 구현
    SummarizationMiddleware(...),
    coding_agent_dynamic_prompt,          # ← Dynamic Prompt 실습 + Part 2
]
```

**왜 FilesystemMiddleware 뒤인가?** TodoListMiddleware는 `wrap_model_call`에서 prompt를 주입합니다. FilesystemMiddleware보다 안쪽(뒤)에 있으므로, filesystem prompt 위에 todo prompt가 추가됩니다.

---

## 검증 방법

### Part 1 검증 (TodoListMiddleware):

```python
uv run python -c "
from ax_advanced_class.src.middleware.todo_middleware import (
    TodoListMiddleware, Todo, PlanningState
)

# State 확인
assert 'todos' in PlanningState.__annotations__
print('PlanningState has todos field — OK')

# Tool 확인
mw = TodoListMiddleware()
assert len(mw.tools) == 1
assert mw.tools[0].name == 'write_todos'
print('write_todos tool registered — OK')

# Prompt 확인
assert 'write_todos' in mw.system_prompt
print('System prompt includes write_todos guidance — OK')
"
```

### Part 2 검증 (Harness Prompting):

```python
uv run python -c "
from ax_advanced_class.src.prompts.coding_agent_prompt import CODING_AGENT_SYSTEM_PROMPT

# Phase 내용이 채워져 있는지
assert 'pwd' in CODING_AGENT_SYSTEM_PROMPT        # PHASE 1
assert 'init.sh' in CODING_AGENT_SYSTEM_PROMPT     # PHASE 1
assert 'passes' in CODING_AGENT_SYSTEM_PROMPT      # PHASE 2
assert 'progress.md' in CODING_AGENT_SYSTEM_PROMPT # PHASE 3
assert 'git commit' in CODING_AGENT_SYSTEM_PROMPT  # PHASE 3
print('All harness behaviors present — OK')
"
```

### 전체 동작 테스트:

```bash
uv run python -m ax_advanced_class.src.main
```

`"블로그 플랫폼 만들어줘"` 입력 후 확인:
1. Agent가 `pwd` → `init.sh` 순서로 시작하는지 (PHASE 1)
2. `write_todos`를 호출하여 작업 계획을 만드는지
3. 하나의 feature만 작업하는지 (PHASE 2)
4. `progress.md`, `feature_list.json` 업데이트 후 commit 하는지 (PHASE 3)

---

## 흔한 실패와 대처

| 증상 | 원인 | 해결 |
|------|------|------|
| `write_todos`가 tool 목록에 안 나옴 | `__init__`에서 `self.tools` 미설정 | TODO 2에서 `self.tools = [StructuredTool.from_function(...)]` 확인 |
| `Command(update=...)` 후 todos가 안 바뀜 | `messages` 키 누락 | `Command(update={"todos": ..., "messages": [ToolMessage(...)]})`로 둘 다 포함 |
| Agent가 모든 todo를 한꺼번에 completed로 변경 | Description에 "한 번에 1개만 in_progress" 규칙 누락 | 사전 제공 코드의 description에 "Exactly ONE task in_progress at any time" 명시 |
| Agent가 PHASE 1을 건너뛰고 바로 코딩 시작 | 프롬프트가 "권장"으로 작성됨 | "You MUST complete PHASE 1 before any implementation work" 강제 어투 사용 |
| `progress.md` 업데이트가 git commit에 안 잡힘 | PHASE 3 순서 오류 (commit → 파일 수정) | 반드시 "파일 수정 → git add → git commit" 순서 강제 |

---

## 개념 연결 맵

```
Agent Harness.md에서 배운 것     →  이 실습에서 구현한 것
│
├─ 암묵적 기억 → 명시적 상태 ────→ TodoListMiddleware (Part 1)
│   "대화 속 정보를 state로"         todos를 agent state에 명시적 저장
│
├─ Middleware의 3가지 축 ────────→ TODO 1, 2, 3 (Part 1)
│   State + Tool + Prompt           PlanningState + write_todos + system_prompt
│
├─ 해석 프로토콜 ────────────────→ PHASE 1 (사전 제공 코드)
│   "pwd → git log → feature list"  Agent가 외부 상태를 읽고 시작
│
├─ 작업 단위 격리 ───────────────→ PHASE 2 (TODO 4)
│   "한 번에 하나만"                 ONE feature + write_todos로 추적
│
├─ Context 외부화 ───────────────→ PHASE 3 (TODO 5)
│   "파일로 상태 기록"               progress.md + feature_list.json + commit
│
└─ Compound Reliability ─────────→ 전체 설계
    "0.95^10 = 59.9%"               작업을 작게 → 성공률 유지
```
