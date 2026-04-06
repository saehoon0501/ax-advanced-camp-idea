# Langchain v1.0 — Middleware로 Agent 제어하기

## 문제: Agent는 유연하지만, 그래서 불안하다

Agent에게 "프로젝트 셋업해줘"라고 하면 알아서 파일을 만들고, 코드를 쓰고, 테스트까지 돌립니다.
그런데 이런 일이 생깁니다:

- `rm -rf /` 같은 위험한 명령을 실행하려 한다
- 대화가 길어지면 이전 작업을 잊어버린다
- 어떤 tool을 언제 써야 하는지 일관성이 없다
- 세션이 바뀌면 진행 상황을 추적할 방법이 없다

Workflow라면 모든 경로를 하드코딩해서 예방할 수 있지만, Agent의 유연함을 잃게 됩니다.

|  | Workflow | Agent |
|---|---|---|
| **정의** | LLM과 도구가 사전에 정의된 코드 경로를 따르는 시스템 | LLM이 스스로 프로세스와 도구 사용을 지시하며 제어권을 가짐 |
| **특징** | 예측 가능, 일관성 | 유연, 모델 주도적 의사결정 |
| **한계** | 모든 step, 모든 exception을 미리 구현해야 함 | 일관성 없는 결과, 보안 위험 |

Reasoning Model의 등장으로 LLM이 스스로 복잡한 문제를 단계별로 해결할 수 있게 됐습니다.
문제는 **유연함은 유지하면서, 일관성과 안전성을 어떻게 확보할 것인가** — 이것이 Context Engineering입니다.

---

## 이 글에서 다루는 것

- `create_agent`와 Middleware가 무엇이고 왜 필요한지
- Middleware가 제어하는 3가지 축: **State, Tools, Prompt**
- Node-style vs Wrap-style 훅의 차이와 선택 기준
- 여러 middleware를 조합할 때의 실행 순서

**사전 지식**: Python 기본 문법, LangChain/LangGraph 기초 개념

---

## create_agent — Agent의 내부 구조는 항상 같다

대부분의 Agent는 같은 패턴을 반복합니다:

```
LLM 호출 → tool_calls 있으면 → Tool 실행 → 결과를 messages에 추가 → 다시 LLM 호출 → ... → 종료
```

이 루프를 매번 LangGraph의 `StateGraph`로 직접 만들 필요 없이, `create_agent`가 기본 구조를 제공합니다.
그리고 **이 루프의 각 시점에 개입하는 것**이 Middleware입니다.

```python
from langchain.agents import create_agent

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[my_tool],
    system_prompt="You are a helpful assistant",
    middleware=[security, filesystem, todo_tracking],  # ← 여기서 Context Engineering
)
```

---

## Middleware 훅 — Agent 루프의 어디에 개입하는가

Middleware는 Agent 루프의 6개 시점에 코드를 삽입합니다:

```
Agent 시작
  │
  ├─ before_agent          ← 메모리 로드, 입력 검증
  │
  │  ┌─── Agent Loop ──────────────────────────┐
  │  │                                          │
  │  │  before_model       ← 메시지 트리밍/요약  │
  │  │  wrap_model_call    ← prompt/tool 수정    │
  │  │      → LLM 호출 ←                        │
  │  │  after_model        ← 출력 검증           │
  │  │                                          │
  │  │  wrap_tool_call     ← 보안 검증           │
  │  │      → Tool 실행 ←                        │
  │  │                                          │
  │  └──────────────────────────────────────────┘
  │
  ├─ after_agent           ← 결과 저장, 정리
  │
Agent 종료
```

| Hook | 실행 시점 | 스타일 | 실제 사용 예 |
|------|----------|--------|------------|
| `before_agent` | Agent 시작 전 (1회) | Node | 메모리 로드, 세션 초기화 |
| `before_model` | 매 LLM 호출 전 | Node | 토큰 초과 시 메시지 요약 |
| `wrap_model_call` | LLM 호출을 감싸서 | Wrap | prompt 주입, tool 필터링, retry |
| `wrap_tool_call` | Tool 호출을 감싸서 | Wrap | 보안 검증, 실행 차단 |
| `after_model` | 매 LLM 응답 후 | Node | guardrail, parallel 호출 감지 |
| `after_agent` | Agent 완료 후 (1회) | Node | 결과 저장, cleanup |

이 테이블에서 "Node"와 "Wrap" 두 종류가 보입니다. 이 차이가 중요한데, 잠시 후 다룹니다.
먼저 middleware가 **무엇을 제어할 수 있는지**부터 봅시다.

---

## Middleware의 3가지 축 — State, Tools, Prompt

Middleware는 단순한 전처리/후처리 훅이 아닙니다.
Agent의 핵심 구성 요소 3가지를 **동적으로 주입하고 수정**합니다.

```
┌────────────────────────────────────────────────────┐
│  create_agent(middleware=[A, B])                   │
│                                                    │
│  Middleware A ──→  state: todos 필드 추가           │
│                    tools: [write_todos]             │
│                    prompt: "todo 사용법 주입"        │
│                                                    │
│  Middleware B ──→  state: files 필드 추가           │
│                    tools: [read_file, edit_file...] │
│                    prompt: "파일 도구 사용법 주입"    │
│                                                    │
│  → create_agent가 자동으로 머지                     │
│    State  = messages + todos + files               │
│    Tools  = write_todos + read_file + edit_file... │
│    Prompt = 원본 + "todo 사용법" + "파일 도구 사용법" │
└────────────────────────────────────────────────────┘
```

하나씩 살펴봅니다.

### 1. State 확장 — `state_schema`

Middleware는 `state_schema` 클래스 속성으로 agent state에 필드를 추가합니다.

```python
class PlanningState(AgentState):
    todos: list[Todo]  # middleware가 추가하는 필드

class TodoListMiddleware(AgentMiddleware[PlanningState]):
    state_schema = PlanningState
```

여러 middleware의 `state_schema`는 `create_agent`가 **자동 머지**합니다. 개발자가 직접 합칠 필요가 없습니다.

| Middleware | 추가되는 필드 |
|---|---|
| 기본 `AgentState` | `messages: list[BaseMessage]` |
| `TodoListMiddleware` | `todos: list[Todo]` |
| `FilesystemMiddleware` | `files: dict[str, FileData]` |

### 2. Tool 주입 — `self.tools`

Middleware는 `__init__`에서 `self.tools`를 정의하면, agent의 tool set에 자동 등록됩니다.

```python
# TodoListMiddleware.__init__
self.tools = [
    StructuredTool.from_function(
        name="write_todos",
        func=_write_todos,
        args_schema=WriteTodosInput,
    )
]
```

`create_agent`의 `tools` 파라미터와 middleware의 `self.tools`가 합쳐집니다.
즉, **middleware만으로** agent의 모든 tool을 구성할 수도 있습니다:

```python
agent = create_agent(
    model=llm,
    middleware=[
        FilesystemMiddleware(backend=backend),  # → ls, read_file, write_file, edit_file, glob, grep, execute
        TodoListMiddleware(),                    # → write_todos
    ],
    # tools 파라미터 없음 — 8개 tool이 모두 middleware에서 온다
)
```

### 3. Prompt 주입 — `wrap_model_call`에서 `request.override()`

Middleware는 매 LLM 호출마다 system prompt를 동적으로 수정합니다.

```python
# TodoListMiddleware.wrap_model_call
def wrap_model_call(self, request, handler):
    new_system_content = [
        *request.system_message.content_blocks,           # 기존 prompt 유지
        {"type": "text", "text": self.system_prompt},     # todo 사용법 추가
    ]
    return handler(request.override(
        system_message=SystemMessage(content=new_system_content)
    ))
```

여러 middleware가 각각 `wrap_model_call`을 구현하면, prompt가 체이닝되어 누적됩니다:

```
원본 system_prompt
  + FilesystemMiddleware: "read_file, edit_file 사용법..."
  + TodoListMiddleware: "write_todos 사용법..."
  + @dynamic_prompt: "현재 workspace 경로, 현재 todos 상태..."
```

> **핵심**: Tool + 사용법 + State가 middleware 하나에 완전한 패키지로 제공됩니다.
> 새로운 기능을 추가할 때 agent 코드를 수정할 필요 없이, middleware를 하나 추가하면 됩니다.

---

## 런타임 State 접근과 조작

위의 3가지 축(State, Tools, Prompt)은 **설정 시점**의 이야기입니다 — agent를 만들 때 "어떤 필드가 있고, 어떤 도구를 쓸 수 있는가"를 정의합니다.

하지만 middleware의 진짜 힘은 **런타임**에 있습니다. Agent가 실행되는 동안, 매 LLM 호출과 매 tool 호출 시점에서 middleware가 **현재 state를 읽고, 판단하고, 수정**할 수 있습니다.

### State 읽기 — 현재 상황 파악

Node-style 훅(`before_model`, `after_model`)은 첫 번째 인자로 현재 state를 받습니다:

```python
def before_model(self, state, runtime):
    messages = state["messages"]       # 현재까지의 대화 기록
    todos = state.get("todos", [])     # 현재 todo 상태
    # state를 읽어서 판단 → 필요하면 수정
```

Wrap-style 훅(`wrap_model_call`)은 `request.state`로 접근합니다:

```python
def wrap_model_call(self, request, handler):
    current_todos = request.state.get("todos", [])
    workspace = request.state.get("workspace", "")
    # 현재 상태를 기반으로 프롬프트를 동적으로 구성
```

### State 수정 — 런타임에 상태 변경

Node-style 훅은 **dict를 반��**하여 state를 업데이트합니다:

```python
def before_model(self, state, runtime):
    messages = state["messages"]
    if self._too_many_tokens(messages):
        summary = self._summarize(messages[:-20])
        # 오래된 메시지를 요약으로 교체 → state의 messages가 변경됨
        return {"messages": [RemoveMessage(id=REMOVE_ALL), summary, *messages[-20:]]}
    return None  # 변경 없음
```

Tool이 `Command`를 반환하면 state를 직접 업데이트할 수도 있습니다:

```python
def _write_todos(runtime, todos):
    # tool 실행 결과로 state.todos를 교체
    return Command(update={"todos": todos, "messages": [ToolMessage(...)]})
```

### 왜 이것이 중요한가 — 실습 연결

이 런타임 state 제어가 없으면, middleware는 단순한 전처리/후처리에 불과합��다. 런타임에 state를 읽고 쓸 수 있기 때문에:

| 실습 | 읽는 state | 하는 일 |
|------|-----------|--------|
| **Summarizer 실습** | `state["messages"]` | 토큰 수를 계산하고, 임계값을 넘으면 오���된 메시지를 요약으로 교체 |
| **Dynamic Prompt 실습** | `request.state["todos"]` | 현재 todo 상태를 프롬프트에 주입하여 agent가 진행 상황을 인식 |

```
Agent 루프의 매 턴마다:

  before_model(state) ← messages를 읽어서 토큰 체크, 필요시 압축
       ↓
  wrap_model_call(request) ← state에서 todos를 읽어서 프롬프트에 주입
       ↓
  LLM 호출 (압축된 messages + 최신 todos가 반영된 프롬프트)
       ↓
  Tool 실행 → write_todos → Command(update={"todos": [...]}) ← state.todos 업데이트
       ↓
  다음 턴의 before_model에서 업데이트된 state를 다시 읽음 → 반복
```

핵심: Middleware는 agent 루프가 돌 때���다 state를 **관찰하고 개입**합니다. 정적인 설정이 아니라, **매 턴마다 반응하는 제어 루프**입니다.

---

## Node-style vs Wrap-style — 왜 두 종류의 훅이 필요한가

앞의 훅 테이블에서 "Node"와 "Wrap" 두 가지 스타일이 있었습니다. 이 구분이 middleware 설계의 핵심입니다.

### Node-style — 관찰하고 반응한다

`before_model`, `after_model` 등은 실행 흐름을 **제어하지 않습니다**.
State를 읽고, 필요하면 dict를 반환해서 state를 업데이트할 뿐입니다.

대화가 길어지면 토큰이 초과됩니다. `SummarizationMiddleware`는 `before_model`에서 이를 감지하고, 오래된 메시지를 요약으로 교체합니다:

```python
def before_model(self, state, runtime):
    messages = state["messages"]
    if self._should_summarize(messages, total_tokens):
        summary = self._create_summary(messages_to_summarize)
        return {
            "messages": [RemoveMessage(id=m.id) for m in old] + [summary_msg]
        }
    return None  # 조건 미충족 시 아무것도 안 함
```

LLM 호출 자체는 항상 실행됩니다. middleware는 그 **전후에 state를 조정**할 뿐입니다.

### Wrap-style — 실행 자체를 제어한다

`wrap_model_call`, `wrap_tool_call`은 **handler를 직접 감쌉니다**.
실행 여부, 횟수, 입출력을 모두 제어할 수 있습니다.

Agent가 `rm -rf /`를 실행하려 할 때, `ToolValidationMiddleware`는 handler를 **호출하지 않고 차단**합니다:

```python
def wrap_tool_call(self, request, handler):
    tool_name = request.tool_call["name"]

    if tool_name in _BASH_TOOL_NAMES:
        result = self._validator.validate_command(args["command"])

        if result.level == PermissionLevel.DENY:
            return ToolMessage(content="Error: Command denied.", status="error")
            # ↑ handler 호출 안 함 — tool 실행 완전 차단

        if result.level == PermissionLevel.ASK:
            approved = interrupt({...})    # 사용자에게 승인 요청
            if not approved:
                return ToolMessage(content="Error: Denied.", status="error")

    return handler(request)  # 검증 통과 시에만 실제 실행
```

handler를 여러 번 호출하는 것도 가능합니다:

```python
# RetryMiddleware — 실패 시 최대 3회 재시도
def wrap_model_call(self, request, handler):
    for attempt in range(3):
        try:
            return handler(request)     # handler를 N번 호출 가능
        except Exception as e:
            if attempt == 2:
                raise
```

### 비교

|  | Node-style | Wrap-style |
|---|---|---|
| **handler 제어** | 불가 — 항상 실행됨 | 가능 — 0회, 1회, N회 |
| **반환** | `dict` → state 업데이트 | handler 결과를 변환 |
| **용도** | 로깅, 요약, state 추적 | 보안 게이트, retry, prompt 주입 |
| **비유** | 감시 카메라 | 보안 게이트 |

**선택 기준**: "실행을 막거나 바꿔야 하는가?" → Wrap. "실행 전후에 state만 조정하면 되는가?" → Node.

---

## Middleware 실행 순서 — 양파 모델

여러 middleware를 조합하면, 실행 순서가 중요해집니다.

```python
agent = create_agent(
    middleware=[middleware1, middleware2, middleware3],
)
```

```
──── Agent 시작 ────────────────────────────────────────
  middleware1.before_agent()        ← 순서대로 (1→2→3)
  middleware2.before_agent()
  middleware3.before_agent()

──── Agent Loop (반복) ─────────────────────────────────
  middleware1.before_model()        ← 순서대로 (1→2→3)
  middleware2.before_model()
  middleware3.before_model()

  middleware1.wrap_model_call       ← 중첩: 1이 바깥, 3이 안쪽
    middleware2.wrap_model_call
      middleware3.wrap_model_call
        → LLM 호출 ←

  middleware3.after_model()         ← 역순 (3→2→1)
  middleware2.after_model()
  middleware1.after_model()

  middleware1.wrap_tool_call        ← 중첩: 1이 바깥
    middleware2.wrap_tool_call
      middleware3.wrap_tool_call
        → Tool 실행 ←

──── Agent 종료 ────────────────────────────────────────
  middleware3.after_agent()         ← 역순 (3→2→1)
  middleware2.after_agent()
  middleware1.after_agent()
```

| 훅 타입 | 실행 순서 |
|--------|----------|
| `before_*` | 리스트 순서대로 (1 → 2 → 3) |
| `wrap_*` | 중첩 — 1이 가장 바깥, 마지막이 가장 안쪽 |
| `after_*` | 역순 (3 → 2 → 1) |

### 실제 프로젝트의 Middleware 스택

이 순서가 실제로 어떻게 적용되는지 봅시다:

```python
middleware = [
    ToolValidationMiddleware(config),    # 1
    FilesystemMiddleware(backend),        # 2
    TodoListMiddleware(),                 # 3
    SummarizationMiddleware(model),       # 4
    coding_agent_dynamic_prompt,          # 5
]
```

| 순서 | Middleware | 왜 이 위치인가 |
|---|---|---|
| 1 (가장 바깥) | `ToolValidationMiddleware` | `wrap_tool_call`이 **모든** tool 호출을 감싸므로, 어떤 tool도 보안 검증 없이 실행되지 않음 |
| 2 | `FilesystemMiddleware` | tool 제공 + 실행 후 대형 출력 자동 압축 |
| 3 | `TodoListMiddleware` | todo tool + system prompt에 사용법 주입 |
| 4 | `SummarizationMiddleware` | `before_model`에서 토큰 초과 감지 → 오래된 메시지 요약 |
| 5 (가장 안쪽) | `dynamic_prompt` | 최종 prompt 끝에 현재 세션 컨텍스트 추가 |

> **원칙**: 보안은 바깥, 기능은 안쪽.
> 가장 바깥 middleware의 `wrap_tool_call`이 모든 tool 실행의 최종 gate입니다.

---

## 정리 — Middleware는 Context Engineering의 모듈화다

Agent의 ReAct 루프 자체는 변경하지 않습니다.
Middleware 조합을 바꾸는 것만으로, 같은 agent에 완전히 다른 도구/프롬프트/보안/메모리를 적용합니다.

```
┌─ create_agent ──────────────────────────────────┐
│                                                  │
│  system_prompt  ← 정적 지침 (agent의 역할)       │
│                                                  │
│  middleware = [                                  │
│    ToolValidation  ← 보안 (wrap_tool_call)       │
│    Filesystem      ← 도구 + State + Prompt       │
│    TodoList        ← 도구 + State + Prompt       │
│    Summarization   ← 컨텍스트 압축 (before_model) │
│    dynamic_prompt  ← 런타임 컨텍스트 (wrap_model) │
│  ]                                               │
│                                                  │
│  Agent는 항상 같은 ReAct 루프를 돌지만,          │
│  middleware 조합에 따라 완전히 다르게 동작한다     │
└──────────────────────────────────────────────────┘
```

| 하고 싶은 것 | 사용할 축 | Hook |
|---|---|---|
| Agent에 새 tool 추가 | `self.tools` | `__init__` |
| Agent state에 필드 추가 | `state_schema` | 클래스 속성 |
| System prompt 동적 수정 | `request.override()` | `wrap_model_call` |
| Tool 실행 전 검증/차단 | handler 호출 제어 | `wrap_tool_call` |
| 컨텍스트 윈도우 관리 | 메시지 요약/삭제 | `before_model` |
| 모델 응답 검증 | state 업데이트 | `after_model` |
