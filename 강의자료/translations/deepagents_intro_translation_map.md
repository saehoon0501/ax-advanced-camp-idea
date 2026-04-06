# Deepagents: LangChain-Native Agent Harness

## Sentence-by-Sentence Translation Map

---

### Section: Introduction

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | `create_agent()`로 에이전트를 만들 수 있다는 건 배웠습니다. | We've learned that you can create an agent with `create_agent()`. |
| 2 | 하지만 실제로 에이전트가 파일을 읽고, 코드를 실행하고, 할 일을 관리하고, 긴 대화를 압축하려면 — 이 모든 기능을 하나하나 구현해야 할까요? | But if you actually want the agent to read files, execute code, manage tasks, and compress long conversations — do you have to implement all of these features one by one? |
| 3 | **Deepagents**는 이런 프로덕션 에이전트에 필요한 기능을 **미들웨어와 백엔드**로 패키징한 LangChain 확장 라이브러리입니다. | **Deepagents** is a LangChain extension library that packages the features needed for production agents into **middleware and backends**. |
| 4 | `create_agent()`의 middleware에 꽂기만 하면 됩니다. | Just plug them into `create_agent()`'s middleware and you're good to go. |

---

### Section: What You'll Learn

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 5 | `create_agent()`가 내부적으로 어떻게 동��하는지 (ReAct 루프) | How `create_agent()` works internally (the ReAct loop) |
| 6 | 미들웨어가 에이전트 루프의 어디에 끼어드는지 (실행 순서) | Where middleware hooks into the agent loop (execution order) |
| 7 | Deepagents가 제공하는 미들웨어 3종 (Filesystem, TodoList, Summarization) | The three middleware types Deepagents provides (Filesystem, TodoList, Summarization) |
| 8 | 백엔드 패턴 — 실제 파일/명령 실행을 추상화하는 계층 | The backend pattern — an abstraction layer for actual file and command execution |

---

### Section: Prerequisites

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 9 | `LangChain & LangGraph 설명.md`의 Part 1 (create_agent, 미들웨어, 메시지 타입) | Part 1 of `LangChain & LangGraph guide` (create_agent, middleware, message types) |
| 10 | Python `TypedDict`, 타입 힌트 | Python `TypedDict` and type hints |

---

### Section: create_agent() Internal — ReAct Loop

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 11 | `create_agent()`는 내부적��로 LangGraph `StateGraph`를 만들어 **ReAct 루프**를 구성합니다. | `create_agent()` internally creates a LangGraph `StateGraph` to set up the **ReAct loop**. |
| 12 | 이 루프의 매 단계에 미��웨어가 끼어듭니다. | Middleware hooks in at every step of this loop. |

---

### Section: Middleware Execution Order

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 13 | `middleware=[A, B, C]`일 때: | When `middleware=[A, B, C]`: |
| 14 | `before_*`: A → B → C — 앞에 있을수록 먼저 | `before_*`: A → B → C — earlier in the list runs first |
| 15 | `wrap_*`: A( B( C( 실제 실행 ) ) ) — 양파 껍질처럼 중첩 | `wrap_*`: A( B( C( actual execution ) ) ) — nested like onion layers |
| 16 | `after_*`: C → B → A — 역순 (안쪽부터 바깥으로) | `after_*`: C → B → A — reverse order (inside out) |
| 17 | `ToolValidationMiddleware`가 맨 앞이므로 — wrap이 가장 바깥 껍질입니다. | Since `ToolValidationMiddleware` is first in the list — its wrap is the outermost layer. |
| 18 | 위험한 명령이 다른 미들웨어에 도달하기 전에 차단됩니다. | Dangerous commands are blocked before they reach any other middleware. |

---

### Section: Three Contributions of Middleware to Agents

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 19 | 미들웨어는 에이���트에 **도구(Tools)**, **상태(State)**, **동작 변경(Hooks)**을 주입합니다. | Middleware injects **tools**, **state**, and **behavior modifications (hooks)** into the agent. |
| 20 | `create_agent()`가 이를 자동으로 병합합니다. | `create_agent()` merges these automatically. |
| 21 | 수동 병합이 필요 없습니다 — 미들웨어 리스트만 넘기면 됩니다. | No manual merging needed — just pass the middleware list. |

---

### Section: FilesystemMiddleware — Files and Command Execution

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 22 | 에이전트가 파일을 읽고, 쓰���, 검색하고, 셸 명령을 실행할 수 있게 합니다. | Enables the agent to read, write, and search files, and execute shell commands. |
| 23 | 제공하는 도구 7개: ls, read_file, write_file, edit_file, glob, grep, execute | Provides 7 tools: ls, read_file, write_file, edit_file, glob, grep, execute |
| 24 | `wrap_model_call` — LLM 호출 전에 도구 사용 가이드라인(Soft Rules)을 시스템 프롬프트에 주입합니다. | `wrap_model_call` — Injects tool usage guidelines (Soft Rules) into the system prompt before each LLM call. |
| 25 | 백엔드가 실행을 지원하지 않으면 `execute` 도구를 목록에서 제거합니다. | If the backend doesn't support execution, the `execute` tool is removed from the list. |
| 26 | `wrap_tool_call` — Tool 실행 후 결과가 너무 크면 (20,000토큰 초과) 파일 시스템에 저장하고, LLM에게는 미리보기 + 파일 경로만 전달합니다. | `wrap_tool_call` — If a tool result is too large (over 20,000 tokens), stores it in the filesystem and passes only a preview plus the file path to the LLM. |

---

### Section: TodoListMiddleware — Task Planning and Progress Tracking

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 27 | 에이전트가 복잡한 작업을 계획하고 진행 상황을 추적할 수 있게 합니다. | Enables the agent to plan complex tasks and track progress. |
| 28 | 제공하는 도구 1개: `write_todos` | Provides 1 tool: `write_todos` |
| 29 | 제공하는 상태: `todos: list[dict]` (에이전트 state에 추가) | Provides state: `todos: list[dict]` (added to the agent state) |
| 30 | `wrap_model_call` — LLM 호출 전에 write_todos 도구의 사용 가이드라인을 시스템 프롬프트에 주입합니다. | `wrap_model_call` — Injects usage guidelines for the write_todos tool into the system prompt before each LLM call. |
| 31 | 에이전트가 `write_todos`를 호출하면 `Command(update={"todos": [...]})` 를 반환하여 에이전트 상태를 직접 업데이트합니다. | When the agent calls `write_todos`, it returns `Command(update={"todos": [...]})` to directly update the agent's state. |

---

### Section: SummarizationMiddleware — Automatic Context Compression

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 32 | 대화가 길어지면 자동으로 오래된 메시지를 요약하여 토큰을 절약합니다. | Automatically summarizes old messages to save tokens when conversations get long. |
| 33 | 제공하는 도구: 없음 (도구가 아닌 `before_model` 훅으로 동작) | Provides tools: None (operates via the `before_model` hook, not as a tool) |
| 34 | `before_model` — LLM 호출 직전에 토큰 수를 확인하고, threshold를 초과하면 오래된 메시지를 별도 LLM(Haiku)으로 요약하여 교체합니다. | `before_model` — Checks token count just before each LLM call; if the threshold is exceeded, older messages are summarized by a separate LLM (Haiku) and replaced. |

---

### Section: Backend Pattern — Execution Environment Abstraction

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 35 | FilesystemMiddleware는 파일을 직접 읽고 쓰지 않습니다. **백엔드**에 위임합니다. | FilesystemMiddleware doesn't read and write files directly. It **delegates to a backend**. |
| 36 | 이 추상화 덕분에 실행 환경을 바꿔도 미들웨어 코드는 동일합니다. | Thanks to this abstraction, the middleware code stays the same even when you swap out the execution environment. |
| 37 | LocalShellBackend → 로컬 OS에서 직접 실행 | LocalShellBackend → Execute directly on the local OS |
| 38 | StateBackend → 메모리에만 저장 (테스트용) | StateBackend → Store in memory only (for testing) |
| 39 | CompositeBackend → 경로별로 다른 백엔드 라우팅 | CompositeBackend → Route to different backends by path |
| 40 | DockerSandbox → 격리된 컨테이너에서 실행 | DockerSandbox → Execute in an isolated container |
| 41 | `LocalShellBackend`는 `SandboxBackendProtocol`을 구현하므로 `execute` 도구가 활성화됩니다. | `LocalShellBackend` implements `SandboxBackendProtocol`, so the `execute` tool is activated. |
| 42 | `StateBackend`는 이를 구현하지 않으므로 `execute` 도구가 자동 비활성화됩니다. | `StateBackend` doesn't implement it, so the `execute` tool is automatically deactivated. |

---

### Section: Full Assembly — agent_specs.py

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 43 | `AgentFactory.create()`가 이 spec을 받아 `create_agent()`를 호출합니다. | `AgentFactory.create()` takes this spec and calls `create_agent()`. |

---

### Section: Summary Table

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 44 | ReAct 루프: model → tool_calls → tool 실행 → model → 반복. `create_agent()`가 구성 | ReAct loop: model → tool_calls → tool execution → model → repeat. Configured by `create_agent()` |
| 45 | 미들웨어 훅: before_model, wrap_model_call, wrap_tool_call, after_model 등 | Middleware hooks: before_model, wrap_model_call, wrap_tool_call, after_model, etc. |
| 46 | 실행 순서: before: 앞→뒤, wrap: 양파 중첩, after: 뒤→앞 | Execution order: before: front→back, wrap: onion nesting, after: back→front |
| 47 | 자동 병합: create_agent()가 tools + state + hooks를 미들웨어에��� 자동 수집 | Auto-merge: create_agent() automatically collects tools + state + hooks from middleware |
| 48 | FilesystemMiddleware: 파일 7개 도구 + 대형 결과 교체 + Soft Rules 주입 | FilesystemMiddleware: 7 file tools + large result replacement + Soft Rules injection |
| 49 | TodoListMiddleware: write_todos 1개 도구 + todos 상태 관리 | TodoListMiddleware: 1 write_todos tool + todos state management |
| 50 | SummarizationMiddleware: 토큰 초과 시 자동 요약 (도구 없음, before_model로 동작) | SummarizationMiddleware: Auto-summarize when tokens exceeded (no tools, operates via before_model) |
| 51 | 백엔드 패턴: LocalShellBackend (로컬), StateBackend (메모리), CompositeBackend (하이브리드) | Backend pattern: LocalShellBackend (local), StateBackend (memory), CompositeBackend (hybrid) |

---

### Section: Course Wrap-up — Full Integration Review

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 52 | 4일차 오전: Context Engineering + LangChain/LangGraph — "왜 컨텍스트를 설계해야 하는가?" | Day 4 AM: Context Engineering + LangChain/LangGraph — "Why do we need to design context?" |
| 53 | 4일차 오후: Token/Prompt/Tool + Middleware — "컨텍스트�� 어떻게 줄이고, 넣고, 통제하는가?" | Day 4 PM: Token/Prompt/Tool + Middleware — "How do we reduce, inject, and control context?" |
| 54 | 5일차 오전: Tool Permission System — "Agent의 행동을 어떻게 안전하게 제한하는가?" | Day 5 AM: Tool Permission System — "How do we safely restrict the agent's behavior?" |
| 55 | 5일차 오후: Agent Harness + deepagents — "다중 세션에서 어떻게 일관성을 유지하는가?" | Day 5 PM: Agent Harness + deepagents — "How do we maintain consistency across multiple sessions?" |
| 56 | 핵심 메시지: Agent의 품질은 모델의 지능이 아니라 **인프라(Harness)의 품질**이 결정합니다. | Core message: Agent quality is determined not by model intelligence, but by the **quality of the infrastructure (Harness)**. |
| 57 | 같은 모델이라도 Harness를 개선하면 83% → 96%로 성능이 향상됩니다. | Even with the same model, improving the Harness boosts performance from 83% → 96%. |
