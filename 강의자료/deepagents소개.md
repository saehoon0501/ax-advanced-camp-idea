# Deepagents: LangChain 네이티브 에이전트 하네스

`create_agent()`로 에이전트를 만들 수 있다는 건 배웠습니다. 하지만 실제로 에이전트가 파일을 읽고, 코드를 실행하고, 할 일을 관리하고, 긴 대화를 압축하려면 — 이 모든 기능을 하나하나 구현해야 할까요?

**Deepagents**는 이런 프로덕션 에이전트에 필요한 기능을 **미들웨어와 백엔드**로 패키징한 LangChain 확장 라이브러리입니다. `create_agent()`의 middleware에 꽂기만 하면 됩니다.

## 이 가이드에서 배울 것

- `create_agent()`가 내부적으로 어떻게 동작하는지 (ReAct 루프)
- 미들웨어가 에이전트 루프의 어디에 끼어드는지 (실행 순서)
- Deepagents가 제공하는 미들웨어 3종 (Filesystem, TodoList, Summarization)
- 백엔드 패턴 — 실제 파일/명령 실행을 추상화하는 계층

## 사전 지식

- `LangChain & LangGraph 설명.md`의 Part 1 (create_agent, 미들웨어, 메시지 타입)
- Python `TypedDict`, 타입 힌트

---

## create_agent() 내부 — ReAct 루프

`create_agent()`는 내부적으로 LangGraph `StateGraph`를 만들어 **ReAct 루프**를 구성합니다.

```
input → [model] → tool_calls 있나? ─ Yes → [tool 실행] → [model] → 반복
                                     └ No → 최종 응답 반환
```

이 루프의 매 단계에 미들웨어가 끼어듭니다:

```
┌─ Agent 시작 ─────────────────────────────────────────────────┐
│  before_agent (한 번)                                         │
│                                                               │
│  ┌─ ReAct 루프 (반복) ────────────────────────────────────┐  │
│  │                                                         │  │
│  │  before_model → wrap_model_call( LLM 호출 ) → after_model │
│  │       ↓                                                 │  │
│  │  tool_calls가 있으면:                                    │  │
│  │  wrap_tool_call( Tool 실행 ) × tool 개수만큼              │  │
│  │       ↓                                                 │  │
│  │  결과를 messages에 추가 → 다시 model로                    │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  after_agent (한 번)                                          │
└───────────────────────────────────────────────────────────────┘
```

### 미들웨어 실행 순서

`middleware=[A, B, C]`일 때:

| 훅 종류 | 실행 순서 | 이유 |
|--------|----------|------|
| `before_*` | A → B → C | 앞에 있을수록 먼저 |
| `wrap_*` | A( B( C( 실제 실행 ) ) ) | 양파 껍질처럼 중첩 |
| `after_*` | C → B → A | 역순 (안쪽부터 바깥으로) |

이 프로젝트의 미들웨어 스택:

```python
middleware = [
    ToolValidationMiddleware(config),     # 1. 명령어 검증 (wrap_tool_call)
    FilesystemMiddleware(backend),        # 2. 파일/실행 도구 (wrap_model_call + wrap_tool_call)
    TodoListMiddleware(),                 # 3. write_todos 도구 (wrap_model_call)
    SummarizationMiddleware(...),         # 4. 컨텍스트 압축 (before_model)
    coding_agent_dynamic_prompt,          # 5. 런타임 프롬프트 (wrap_model_call)
]
```

`ToolValidationMiddleware`가 맨 앞이므로 — wrap이 가장 바깥 껍질입니다. 위험한 명령이 다른 미들웨어에 도달하기 전에 차단됩니다.

---

## 미들웨어가 에이전트에 기여하는 세 가지

미들웨어는 에이전트에 **도구(Tools)**, **상태(State)**, **동작 변경(Hooks)**을 주입합니다. `create_agent()`가 이를 자동으로 병합합니다.

```python
agent = create_agent(
    model=llm,
    middleware=[filesystem, todos, summarization],
)
# create_agent()가 자동으로:
# 1. 각 middleware.tools를 합침 → [ls, read_file, ..., write_todos]
# 2. 각 middleware.state_schema를 합침 → {messages, files, todos}
# 3. 각 middleware의 hook을 체이닝 → before_model, wrap_model_call, ...
```

수동 병합이 필요 없습니다 — 미들웨어 리스트만 넘기면 됩니다.

---

## Deepagents가 제공하는 미들웨어 3종

### 1. FilesystemMiddleware — 파일과 명령 실행

에이전트가 파일을 읽고, 쓰고, 검색하고, 셸 명령을 실행할 수 있게 합니다.

**제공하는 도구 7개:**

| 도구 | 기능 | 분류 |
|------|------|------|
| `ls` | 디렉토리 파일 목록 | 전용 |
| `read_file` | 파일 읽기 (offset/limit 페이지네이션) | 전용 |
| `write_file` | 새 파일 생성 | 전용 |
| `edit_file` | 기존 파일 문자열 치환 | 전용 |
| `glob` | 파일명 패턴 검색 | 전용 |
| `grep` | 파일 내용 정규식 검색 | 전용 |
| `execute` | 셸 명령 실행 | 범용 |

**미들웨어 훅 2개:**

`wrap_model_call` — LLM 호출 전에 도구 사용 가이드라인(Soft Rules)을 시스템 프롬프트에 주입합니다. 백엔드가 실행을 지원하지 않으면 `execute` 도구를 목록에서 제거합니다.

`wrap_tool_call` — Tool 실행 후 결과가 너무 크면 (20,000토큰 초과) 파일 시스템에 저장하고, LLM에게는 미리보기 + 파일 경로만 전달합니다.

**사용법:**

```python
from deepagents.backends import LocalShellBackend
from ax_advanced_class.src.middleware.filesystem_middleware import FilesystemMiddleware

backend = LocalShellBackend(
    root_dir="./workspace",  # 파일 작업의 루트 경로
    inherit_env=True,        # 환경변수 상속
)

middleware = FilesystemMiddleware(
    backend=backend,
    tool_token_limit_before_evict=20000,  # 이 토큰 초과 시 파일로 교체
)
```

### 2. TodoListMiddleware — 작업 계획과 진행 추적

에이전트가 복잡한 작업을 계획하고 진행 상황을 추적할 수 있게 합니다.

**제공하는 도구 1개:** `write_todos`

**제공하는 상태:** `todos: list[dict]` (에이전트 state에 추가)

`wrap_model_call` — LLM 호출 전에 write_todos 도구의 사용 가이드라인을 시스템 프롬프트에 주입합니다.

```python
from ax_advanced_class.src.middleware.todo_middleware import TodoListMiddleware

middleware = TodoListMiddleware()
# write_todos 도구가 자동 등록됨
# agent state에 "todos" 필드가 자동 추가됨
```

에이전트가 `write_todos`를 호출하면:

```python
# 에이전트가 생성하는 tool call
write_todos([
    {"content": "파일 구조 분석", "status": "completed"},
    {"content": "API 엔드포인트 구현", "status": "in_progress"},
    {"content": "테스트 작성", "status": "pending"},
])
```

이 도구는 `Command(update={"todos": [...]})` 를 반환하여 에이전트 상태를 직접 업데이트합니다.

### 3. SummarizationMiddleware — 컨텍스트 자동 압축

대화가 길어지면 자동으로 오래된 메시지를 요약하여 토큰을 절약합니다.

**제공하는 도구:** 없음 (도구가 아닌 `before_model` 훅으로 동작)

`before_model` — LLM 호출 직전에 토큰 수를 확인하고, threshold를 초과하면 오래된 메시지를 별도 LLM(Haiku)으로 요약하여 교체합니다.

```python
from ax_advanced_class.src.middleware.summarization_middleware import SummarizationMiddleware

middleware = SummarizationMiddleware(
    model="anthropic:claude-haiku-4-5-20251001",  # 요약에 쓸 가벼운 모델
    trigger=("tokens", 60000),                     # 60K 토큰 초과 시 압축
    keep=("messages", 20),                         # 최근 20개는 원문 유지
)
```

압축 전후:

```
Before: [30턴 대화, 60,000 토큰]
After:  [요약 1개] + [최근 20개 메시지] → ~15,000 토큰
```

---

## 백엔드 패턴 — 실행 환경 추상화

FilesystemMiddleware는 파일을 직접 읽고 쓰지 않습니다. **백엔드**에 위임합니다. 이 추상화 덕분에 실행 환경을 바꿔도 미들웨어 코드는 동일합니다.

```
FilesystemMiddleware
    └─ backend.read_file("/workspace/main.py")
    └─ backend.write_file("/workspace/test.py", content)
    └─ backend.execute("npm test")

백엔드를 교체하면:
    LocalShellBackend  → 로컬 OS에서 직접 실행
    StateBackend       → 메모리에만 저장 (테스트용)
    CompositeBackend   → 경로별로 다른 백엔드 라우팅
    DockerSandbox      → 격리된 컨테이너에서 실행
```

**이 프로젝트에서 사용하는 백엔드:**

```python
from deepagents.backends import LocalShellBackend

backend = LocalShellBackend(
    root_dir="./workspace",  # 모든 파일 작업의 루트
    inherit_env=True,        # 현재 프로세스의 환경변수 상속 (git, npm 등 사용 가능)
)
```

`LocalShellBackend`는 `SandboxBackendProtocol`을 구현하므로 `execute` 도구가 활성화됩니다. `StateBackend`는 이를 구현하지 않으므로 `execute` 도구가 자동 비활성화됩니다.

---

## 전체 조립 — agent_specs.py

이 프로젝트에서 실제로 에이전트를 조립하는 코드:

```python
# ax_advanced_class/src/agents/agent_specs.py

def coding_agent_spec(config):
    backend = LocalShellBackend(root_dir=config.workspace_root, inherit_env=True)

    middleware = [
        ToolValidationMiddleware(config),          # Hard Rules: 명령어 검증
        FilesystemMiddleware(                       # 파일/실행 도구 7개
            backend=backend,
            tool_token_limit_before_evict=20000,
        ),
        TodoListMiddleware(),                       # write_todos 도구
        SummarizationMiddleware(                    # 자동 컨텍스트 압축
            model="anthropic:claude-haiku-4-5-20251001",
            trigger=("tokens", 60000),
            keep=("messages", 20),
        ),
        coding_agent_dynamic_prompt,                # 런타임 프롬프트 주입
    ]

    return AgentSpec(
        name="coding_agent",
        middleware=middleware,
        system_prompt=CODING_AGENT_SYSTEM_PROMPT,
    )
```

`AgentFactory.create()`가 이 spec을 받아 `create_agent()`를 호출합니다:

```python
# ax_advanced_class/src/agents/agent_factory.py

agent = create_agent(
    model=self.model,
    middleware=list(spec.middleware),
    name=spec.name,
    checkpointer=True,
)
```

`create_agent()`가 자동으로 병합하는 것들:

| 미들웨어 | 추가되는 도구 | 추가되는 상태 | 훅 |
|---------|-------------|-------------|-----|
| ToolValidationMiddleware | 없음 | 없음 | wrap_tool_call |
| FilesystemMiddleware | ls, read_file, write_file, edit_file, glob, grep, execute | files | wrap_model_call, wrap_tool_call |
| TodoListMiddleware | write_todos | todos | wrap_model_call |
| SummarizationMiddleware | 없음 | 없음 | before_model |
| dynamic_prompt | 없음 | 없음 | wrap_model_call |

최종 에이전트 상태:

```python
{
    "messages": [...],   # 기본 (BaseMessage 리스트)
    "files": {...},      # FilesystemMiddleware가 추가
    "todos": [...],      # TodoListMiddleware가 추가
}
```

---

## 요약

| 개념 | 설명 |
|------|------|
| **ReAct 루프** | model → tool_calls → tool 실행 → model → 반복. `create_agent()`가 구성 |
| **미들웨어 훅** | before_model, wrap_model_call, wrap_tool_call, after_model 등 |
| **실행 순서** | before: 앞→뒤, wrap: 양파 중첩, after: 뒤→앞 |
| **자동 병합** | create_agent()가 tools + state + hooks를 미들웨어에서 자동 수집 |
| **FilesystemMiddleware** | 파일 7개 도구 + 대형 결과 교체 + Soft Rules 주입 |
| **TodoListMiddleware** | write_todos 1개 도구 + todos 상태 관리 |
| **SummarizationMiddleware** | 토큰 초과 시 자동 요약 (도구 없음, before_model로 동작) |
| **백엔드 패턴** | LocalShellBackend (로컬), StateBackend (메모리), CompositeBackend (하이브리드) |

## 과정 마무리 — 전체 통합 리뷰

### 2일간 배운 것

| 일차 | 주제 | 핵심 질문 |
|------|------|----------|
| 4일차 오전 | Context Engineering + LangChain/LangGraph | "왜 컨텍스트를 설계해야 하는가?" |
| 4일차 오후 | Token/Prompt/Tool + Middleware | "컨텍스트를 어떻게 줄이고, 넣고, 통제하는가?" |
| 5일차 오전 | Tool Permission System | "Agent의 행동을 어떻게 안전하게 제한하는가?" |
| 5일차 오후 | Agent Harness + deepagents | "다중 세션에서 어떻게 일관성을 유지하는가?" |

### 전체 아키텍처 — 모든 개념이 합쳐지는 곳

```
사용자 요청: "블로그 플랫폼 만들어줘"
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Orchestrator (LangGraph StateGraph)          [4일차 오전]   │
│  ├─ Router Node: with_structured_output → 어디로 보낼지 결정  │
│  ├─ Conditional Edge: initializer | coding | finish         │
│  └─ Checkpointer: 상태 저장 + interrupt 지원                 │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent (create_agent + Middleware Stack)                     │
│                                                              │
│  ┌─ ToolValidationMiddleware ──────────────┐  [5일차 오전]   │
│  │  DENY > ALLOW > ASK                     │                │
│  │  위험한 명령 차단, 경로 검증               │                │
│  │                                          │                │
│  │  ┌─ FilesystemMiddleware ────────────┐  │  [4일차 오후]   │
│  │  │  7개 도구 + Soft Rules 주입         │  │                │
│  │  │  대형 결과 → 파일 저장 + 미리보기    │  │                │
│  │  │                                    │  │                │
│  │  │  ┌─ TodoListMiddleware ─────────┐ │  │  [5일차 오후]   │
│  │  │  │  write_todos + state 관리     │ │  │                │
│  │  │  │                              │ │  │                │
│  │  │  │  ┌─ SummarizationMW ──────┐ │ │  │  [4일차 오후]   │
│  │  │  │  │  60K 토큰 초과 시 압축   │ │ │  │                │
│  │  │  │  │                        │ │ │  │                │
│  │  │  │  │  ┌─ DynamicPrompt ──┐ │ │ │  │  [4일차 오후]   │
│  │  │  │  │  │  Static + Runtime │ │ │ │  │                │
│  │  │  │  │  │  [LLM 호출]       │ │ │ │  │                │
│  │  │  │  │  └──────────────────┘ │ │ │  │                │
│  │  │  │  └────────────────────────┘ │ │  │                │
│  │  │  └──────────────────────────────┘ │  │                │
│  │  └────────────────────────────────────┘  │                │
│  └──────────────────────────────────────────┘                │
│                                                              │
│  Harness Prompting: PHASE 1→2→3 lifecycle      [5일차 오후]  │
└─────────────────────────────────────────────────────────────┘
```

이 과정에서 구현한 모든 것은 Anthropic의 두 가지 핵심 아티클에 기반합니다:
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — Agent 패턴과 아키텍처
- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — 다중 세션 Harness 패턴

**핵심 메시지:** Agent의 품질은 모델의 지능이 아니라 **인프라(Harness)의 품질**이 결정합니다. 같은 모델이라도 Harness를 개선하면 83% → 96%로 성능이 향상됩니다.
