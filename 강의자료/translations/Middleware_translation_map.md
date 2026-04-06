# LangChain v1.0 — Controlling Agents with Middleware

## Sentence-by-Sentence Translation Map

---

### Section: Title and Problem Statement

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Langchain v1.0 — Middleware로 Agent 제어하기 | LangChain v1.0 — Controlling Agents with Middleware |
| 2 | 문제: Agent는 유연하지만, 그래서 불안하다 | Problem: Agents Are Flexible, and That Is Why They Are Unreliable |
| 3 | Agent에게 "프로젝트 셋업해줘"라고 하면 알아서 파일을 만들고, 코드를 쓰고, 테스트까지 돌립니다. | When you tell an agent "set up the project," it creates files, writes code, and even runs tests on its own. |
| 4 | 그런데 이런 일이 생깁니다: | But things like this happen: |
| 5 | `rm -rf /` 같은 위험한 명령을 실행하려 한다 | It tries to execute dangerous commands like `rm -rf /` |
| 6 | 대화가 길어지면 이전 작업을 잊어버린다 | As conversations get longer, it forgets previous work |
| 7 | 어떤 tool을 언제 써야 하는지 일관성이 없다 | There is no consistency in when to use which tool |
| 8 | 세션이 바뀌면 진행 상황을 추적할 방법이 없다 | When the session changes, there is no way to track progress |
| 9 | Workflow라면 모든 경로를 하드코딩해서 예방할 수 있지만, Agent의 유연함을 잃게 됩니다. | With a Workflow, you can prevent this by hardcoding all paths, but you lose the Agent's flexibility. |
| 10 | **정의** — Workflow: LLM과 도구가 사전에 정의된 코드 경로를 따르는 시스템 | **Definition** — Workflow: A system where the LLM and tools follow pre-defined code paths |
| 11 | **정의** — Agent: LLM이 스스로 프로세스와 도구 사용을 지시하며 제어권을 가짐 | **Definition** — Agent: The LLM directs its own process and tool usage, retaining control |
| 12 | **특징** — Workflow: 예측 가능, 일관성 | **Characteristics** — Workflow: Predictable, consistent |
| 13 | **특징** — Agent: 유연, 모델 주도적 의사결정 | **Characteristics** — Agent: Flexible, model-driven decision making |
| 14 | **한계** — Workflow: 모든 step, 모든 exception을 미리 구현해야 함 | **Limitations** — Workflow: Every step and every exception must be implemented in advance |
| 15 | **한계** — Agent: 일관성 없는 결과, 보안 위험 | **Limitations** — Agent: Inconsistent results, security risks |
| 16 | Reasoning Model의 등장으로 LLM이 스스로 복잡한 문제를 단계별로 해결할 수 있게 됐습니다. | With the emergence of Reasoning Models, LLMs can now solve complex problems step by step on their own. |
| 17 | 문제는 **유연함은 유지하면서, 일관성과 안전성을 어떻게 확보할 것인가** — 이것이 Context Engineering입니다. | The question is **how to maintain flexibility while ensuring consistency and safety** — this is Context Engineering. |

---

### Section: What This Article Covers

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 18 | 이 글에서 다루는 것 | What This Article Covers |
| 19 | `create_agent`와 Middleware가 무엇이고 왜 필요한지 | What `create_agent` and Middleware are and why they are needed |
| 20 | Middleware가 제어하는 3가지 축: **State, Tools, Prompt** | The 3 axes that Middleware controls: **State, Tools, Prompt** |
| 21 | Node-style vs Wrap-style 훅의 차이와 선택 기준 | The difference between Node-style and Wrap-style hooks and criteria for choosing |
| 22 | 여러 middleware를 조합할 때의 실행 순서 | The execution order when combining multiple middlewares |
| 23 | **사전 지식**: Python 기본 문법, LangChain/LangGraph 기초 개념 | **Prerequisites**: Basic Python syntax, foundational LangChain/LangGraph concepts |

---

### Section: create_agent — The Agent's Internal Structure Is Always the Same

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 24 | create_agent — Agent의 내부 구조는 항상 같다 | create_agent — The Agent's Internal Structure Is Always the Same |
| 25 | 대부분의 Agent는 같은 패턴을 반복합니다: | Most Agents repeat the same pattern: |
| 26 | LLM 호출 → tool_calls 있으면 → Tool 실행 → 결과를 messages에 추가 → 다시 LLM 호출 → ... → 종료 | LLM call → if tool_calls exist → Tool execution → add result to messages → call LLM again → ... → end |
| 27 | 이 루프를 매번 LangGraph의 `StateGraph`로 직접 만들 필요 없이, `create_agent`가 기본 구조를 제공합니다. | Instead of building this loop manually with LangGraph's `StateGraph` every time, `create_agent` provides the basic structure. |
| 28 | 그리고 **이 루프의 각 시점에 개입하는 것**이 Middleware입니다. | And **intervening at each point in this loop** is what Middleware does. |
| 29 | [Code block] | [Code block] |

---

### Section: Middleware Hooks — Where Do You Intervene in the Agent Loop

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 30 | Middleware 훅 — Agent 루프의 어디에 개입하는가 | Middleware Hooks — Where Do You Intervene in the Agent Loop |
| 31 | Middleware는 Agent 루프의 6개 시점에 코드를 삽입합니다: | Middleware inserts code at 6 points in the Agent loop: |
| 32 | [Code block] | [Code block] |
| 33 | `before_agent` — Agent 시작 전 (1회) — Node — 메모리 로드, 세션 초기화 | `before_agent` — Before Agent starts (once) — Node — Load memory, initialize session |
| 34 | `before_model` — 매 LLM 호출 전 — Node — 토큰 초과 시 메시지 요약 | `before_model` — Before every LLM call — Node — Summarize messages when tokens are exceeded |
| 35 | `wrap_model_call` — LLM 호출을 감싸서 — Wrap — prompt 주입, tool 필터링, retry | `wrap_model_call` — Wraps the LLM call — Wrap — Prompt injection, tool filtering, retry |
| 36 | `wrap_tool_call` — Tool 호출을 감싸서 — Wrap — 보안 검증, 실행 차단 | `wrap_tool_call` — Wraps the Tool call — Wrap — Security validation, execution blocking |
| 37 | `after_model` — 매 LLM 응답 후 — Node — guardrail, parallel 호출 감지 | `after_model` — After every LLM response — Node — Guardrail, parallel call detection |
| 38 | `after_agent` — Agent 완료 후 (1회) — Node — 결과 저장, cleanup | `after_agent` — After Agent completes (once) — Node — Save results, cleanup |
| 39 | 이 테이블에서 "Node"와 "Wrap" 두 종류가 보입니다. | In this table, you can see two types: "Node" and "Wrap." |
| 40 | 이 차이가 중요한데, 잠시 후 다룹니다. | This difference is important, and we will cover it shortly. |
| 41 | 먼저 middleware가 **무엇을 제어할 수 있는지**부터 봅시다. | First, let us look at **what middleware can control**. |

---

### Section: Three Axes of Middleware — State, Tools, Prompt

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 42 | Middleware의 3가지 축 — State, Tools, Prompt | Three Axes of Middleware — State, Tools, Prompt |
| 43 | Middleware는 단순한 전처리/후처리 훅이 아닙니다. | Middleware is not just a simple pre/post-processing hook. |
| 44 | Agent의 핵심 구성 요소 3가지를 **동적으로 주입하고 수정**합니다. | It **dynamically injects and modifies** the 3 core components of an Agent. |
| 45 | [Code block] | [Code block] |
| 46 | 하나씩 살펴봅니다. | Let us look at each one. |

---

### Section: 1. State Extension — state_schema

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 47 | State 확장 — `state_schema` | State Extension — `state_schema` |
| 48 | Middleware는 `state_schema` 클래스 속성으로 agent state에 필드를 추가합니다. | Middleware adds fields to the agent state via the `state_schema` class attribute. |
| 49 | [Code block] | [Code block] |
| 50 | 여러 middleware의 `state_schema`는 `create_agent`가 **자동 머지**합니다. | Multiple middleware `state_schema` definitions are **automatically merged** by `create_agent`. |
| 51 | 개발자가 직접 합칠 필요가 없습니다. | Developers do not need to merge them manually. |
| 52 | 기본 `AgentState` — `messages: list[BaseMessage]` | Default `AgentState` — `messages: list[BaseMessage]` |
| 53 | `TodoListMiddleware` — `todos: list[Todo]` | `TodoListMiddleware` — `todos: list[Todo]` |
| 54 | `FilesystemMiddleware` — `files: dict[str, FileData]` | `FilesystemMiddleware` — `files: dict[str, FileData]` |

---

### Section: 2. Tool Injection — self.tools

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 55 | Tool 주입 — `self.tools` | Tool Injection — `self.tools` |
| 56 | Middleware는 `__init__`에서 `self.tools`를 정의하면, agent의 tool set에 자동 등록됩니다. | When Middleware defines `self.tools` in `__init__`, they are automatically registered in the agent's tool set. |
| 57 | [Code block] | [Code block] |
| 58 | `create_agent`의 `tools` 파라미터와 middleware의 `self.tools`가 합쳐집니다. | The `tools` parameter of `create_agent` and middleware's `self.tools` are combined. |
| 59 | 즉, **middleware만으로** agent의 모든 tool을 구성할 수도 있습니다: | In other words, you can configure all of an agent's tools **using middleware alone**: |
| 60 | [Code block] | [Code block] |

---

### Section: 3. Prompt Injection — wrap_model_call with request.override()

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 61 | Prompt 주입 — `wrap_model_call`에서 `request.override()` | Prompt Injection — `request.override()` in `wrap_model_call` |
| 62 | Middleware는 매 LLM 호출마다 system prompt를 동적으로 수정합니다. | Middleware dynamically modifies the system prompt on every LLM call. |
| 63 | [Code block] | [Code block] |
| 64 | 여러 middleware가 각각 `wrap_model_call`을 구현하면, prompt가 체이닝되어 누적됩니다: | If multiple middlewares each implement `wrap_model_call`, the prompts are chained and accumulated: |
| 65 | [Code block] | [Code block] |
| 66 | **핵심**: Tool + 사용법 + State가 middleware 하나에 완전한 패키지로 제공됩니다. | **Key point**: Tool + usage instructions + State are provided as a complete package in a single middleware. |
| 67 | 새로운 기능을 추가할 때 agent 코드를 수정할 필요 없이, middleware를 하나 추가하면 됩니다. | When adding new functionality, you just add one middleware instead of modifying the agent code. |

---

### Section: Runtime State Access and Manipulation

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 68 | 런타임 State 접근과 조작 | Runtime State Access and Manipulation |
| 69 | 위의 3가지 축(State, Tools, Prompt)은 **설정 시점**의 이야기입니다 — agent를 만들 때 "어떤 필드가 있고, 어떤 도구를 쓸 수 있는가"를 정의합니다. | The 3 axes above (State, Tools, Prompt) are about the **configuration stage** — defining "what fields exist and what tools can be used" when creating the agent. |
| 70 | 하지만 middleware의 진짜 힘은 **런타임**에 있습니다. | But the real power of middleware lies in **runtime**. |
| 71 | Agent가 실행되는 동안, 매 LLM 호출과 매 tool 호출 시점에서 middleware가 **현재 state를 읽고, 판단하고, 수정**할 수 있습니다. | While the Agent is running, at every LLM call and every tool call, middleware can **read, evaluate, and modify the current state**. |

---

### Section: Reading State — Understanding the Current Situation

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 72 | State 읽기 — 현재 상황 파악 | Reading State — Understanding the Current Situation |
| 73 | Node-style 훅(`before_model`, `after_model`)은 첫 번째 인자로 현재 state를 받습니다: | Node-style hooks (`before_model`, `after_model`) receive the current state as their first argument: |
| 74 | [Code block] | [Code block] |
| 75 | Wrap-style 훅(`wrap_model_call`)은 `request.state`로 접근합니다: | Wrap-style hooks (`wrap_model_call`) access it via `request.state`: |
| 76 | [Code block] | [Code block] |

---

### Section: Modifying State — Changing State at Runtime

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 77 | State 수정 — 런타임에 상태 변경 | Modifying State — Changing State at Runtime |
| 78 | Node-style 훅은 **dict를 반환**하여 state를 업데이트합니다: | Node-style hooks update state by **returning a dict**: |
| 79 | [Code block] | [Code block] |
| 80 | Tool이 `Command`를 반환하면 state를 직접 업데이트할 수도 있습니다: | When a Tool returns a `Command`, it can also update state directly: |
| 81 | [Code block] | [Code block] |

---

### Section: Why This Matters — Connection to Exercises

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 82 | 왜 이것이 중요한가 — 실습 연결 | Why This Matters — Connection to Exercises |
| 83 | 이 런타임 state 제어가 없으면, middleware는 단순한 전처리/후처리에 불과합니다. | Without this runtime state control, middleware would be nothing more than simple pre/post-processing. |
| 84 | 런타임에 state를 읽고 쓸 수 있기 때문에: | Because it can read and write state at runtime: |
| 85 | **Summarizer 실습** — `state["messages"]` — 토큰 수를 계산하고, 임계값을 넘으면 오래된 메시지를 요약으로 교체 | **Summarizer exercise** — `state["messages"]` — Calculates the token count and replaces old messages with a summary when the threshold is exceeded |
| 86 | **Dynamic Prompt 실습** — `request.state["todos"]` — 현재 todo 상태를 프롬프트에 주입하여 agent가 진행 상황을 인식 | **Dynamic Prompt exercise** — `request.state["todos"]` — Injects the current todo state into the prompt so the agent is aware of progress |
| 87 | [Code block] | [Code block] |
| 88 | 핵심: Middleware는 agent 루프가 돌 때마다 state를 **관찰하고 개입**합니다. | Key point: Middleware **observes and intervenes** in the state every time the agent loop runs. |
| 89 | 정적인 설정이 아니라, **매 턴마다 반응하는 제어 루프**입니다. | It is not a static configuration but a **control loop that reacts on every turn**. |

---

### Section: Node-style vs Wrap-style — Why Two Types of Hooks Are Needed

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 90 | Node-style vs Wrap-style — 왜 두 종류의 훅이 필요한가 | Node-style vs Wrap-style — Why Two Types of Hooks Are Needed |
| 91 | 앞의 훅 테이블에서 "Node"와 "Wrap" 두 가지 스타일이 있었습니다. | In the earlier hook table, there were two styles: "Node" and "Wrap." |
| 92 | 이 구분이 middleware 설계의 핵심입니다. | This distinction is the core of middleware design. |

---

### Section: Node-style — Observe and React

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 93 | Node-style — 관찰하고 반응한다 | Node-style — Observe and React |
| 94 | `before_model`, `after_model` 등은 실행 흐름을 **제어하지 않습니다**. | `before_model`, `after_model`, and others **do not control** the execution flow. |
| 95 | State를 읽고, 필요하면 dict를 반환해서 state를 업데이트할 뿐입니다. | They simply read the State and, if needed, return a dict to update the state. |
| 96 | 대화가 길어지면 토큰이 초과됩니다. | As conversations get longer, tokens are exceeded. |
| 97 | `SummarizationMiddleware`는 `before_model`에서 이를 감지하고, 오래된 메시지를 요약으로 교체합니다: | `SummarizationMiddleware` detects this in `before_model` and replaces old messages with a summary: |
| 98 | [Code block] | [Code block] |
| 99 | LLM 호출 자체는 항상 실행됩니다. | The LLM call itself always executes. |
| 100 | middleware는 그 **전후에 state를 조정**할 뿐입니다. | Middleware only **adjusts state before and after** it. |

---

### Section: Wrap-style — Control the Execution Itself

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 101 | Wrap-style — 실행 자체를 제어한다 | Wrap-style — Control the Execution Itself |
| 102 | `wrap_model_call`, `wrap_tool_call`은 **handler를 직접 감쌉니다**. | `wrap_model_call` and `wrap_tool_call` **directly wrap the handler**. |
| 103 | 실행 여부, 횟수, 입출력을 모두 제어할 수 있습니다. | You can control whether to execute, how many times, and all input/output. |
| 104 | Agent가 `rm -rf /`를 실행하려 할 때, `ToolValidationMiddleware`는 handler를 **호출하지 않고 차단**합니다: | When the Agent tries to execute `rm -rf /`, `ToolValidationMiddleware` **blocks it without calling** the handler: |
| 105 | [Code block] | [Code block] |
| 106 | handler를 여러 번 호출하는 것도 가능합니다: | It is also possible to call the handler multiple times: |
| 107 | [Code block] | [Code block] |

---

### Section: Comparison

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 108 | 비교 | Comparison |
| 109 | Node-style — **handler 제어**: 불가 — 항상 실행됨 | Node-style — **Handler control**: Not possible — always executed |
| 110 | Wrap-style — **handler 제어**: 가능 — 0회, 1회, N회 | Wrap-style — **Handler control**: Possible — 0, 1, or N times |
| 111 | Node-style — **반환**: `dict` → state 업데이트 | Node-style — **Returns**: `dict` → state update |
| 112 | Wrap-style — **반환**: handler 결과를 변환 | Wrap-style — **Returns**: transforms the handler result |
| 113 | Node-style — **용도**: 로깅, 요약, state 추적 | Node-style — **Use cases**: Logging, summarization, state tracking |
| 114 | Wrap-style — **용도**: 보안 게이트, retry, prompt 주입 | Wrap-style — **Use cases**: Security gate, retry, prompt injection |
| 115 | Node-style — **비유**: 감시 카메라 | Node-style — **Analogy**: Security camera |
| 116 | Wrap-style — **비유**: 보안 게이트 | Wrap-style — **Analogy**: Security gate |
| 117 | **선택 기준**: "실행을 막거나 바꿔야 하는가?" → Wrap. "실행 전후에 state만 조정하면 되는가?" → Node. | **Selection criteria**: "Do you need to block or change execution?" → Wrap. "Do you only need to adjust state before and after execution?" → Node. |

---

### Section: Middleware Execution Order — The Onion Model

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 118 | Middleware 실행 순서 — 양파 모델 | Middleware Execution Order — The Onion Model |
| 119 | 여러 middleware를 조합하면, 실행 순서가 중요해집니다. | When combining multiple middlewares, the execution order becomes important. |
| 120 | [Code block] | [Code block] |
| 121 | `before_*` — 리스트 순서대로 (1 → 2 → 3) | `before_*` — In list order (1 → 2 → 3) |
| 122 | `wrap_*` — 중첩 — 1이 가장 바깥, 마지막이 가장 안쪽 | `wrap_*` — Nested — 1 is the outermost, last is the innermost |
| 123 | `after_*` — 역순 (3 → 2 → 1) | `after_*` — Reverse order (3 → 2 → 1) |

---

### Section: Middleware Stack in the Actual Project

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 124 | 실제 프로젝트의 Middleware 스택 | Middleware Stack in the Actual Project |
| 125 | 이 순서가 실제로 어떻게 적용되는지 봅시다: | Let us see how this order is actually applied: |
| 126 | [Code block] | [Code block] |
| 127 | 1 (가장 바깥) — `ToolValidationMiddleware` — `wrap_tool_call`이 **모든** tool 호출을 감싸므로, 어떤 tool도 보안 검증 없이 실행되지 않음 | 1 (outermost) — `ToolValidationMiddleware` — Since `wrap_tool_call` wraps **all** tool calls, no tool executes without security validation |
| 128 | 2 — `FilesystemMiddleware` — tool 제공 + 실행 후 대형 출력 자동 압축 | 2 — `FilesystemMiddleware` — Provides tools + automatically compresses large output after execution |
| 129 | 3 — `TodoListMiddleware` — todo tool + system prompt에 사용법 주입 | 3 — `TodoListMiddleware` — Todo tool + injects usage instructions into the system prompt |
| 130 | 4 — `SummarizationMiddleware` — `before_model`에서 토큰 초과 감지 → 오래된 메시지 요약 | 4 — `SummarizationMiddleware` — Detects token overflow in `before_model` → summarizes old messages |
| 131 | 5 (가장 안쪽) — `dynamic_prompt` — 최종 prompt 끝에 현재 세션 컨텍스트 추가 | 5 (innermost) — `dynamic_prompt` — Appends current session context at the end of the final prompt |
| 132 | **원칙**: 보안은 바깥, 기능은 안쪽. | **Principle**: Security on the outside, features on the inside. |
| 133 | 가장 바깥 middleware의 `wrap_tool_call`이 모든 tool 실행의 최종 gate입니다. | The outermost middleware's `wrap_tool_call` is the final gate for all tool executions. |

---

### Section: Summary — Middleware Is the Modularization of Context Engineering

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 134 | 정리 — Middleware는 Context Engineering의 모듈화다 | Summary — Middleware Is the Modularization of Context Engineering |
| 135 | Agent의 ReAct 루프 자체는 변경하지 않습니다. | The Agent's ReAct loop itself is not modified. |
| 136 | Middleware 조합을 바꾸는 것만으로, 같은 agent에 완전히 다른 도구/프롬프트/보안/메모리를 적용합니다. | Just by changing the middleware combination, you apply entirely different tools/prompts/security/memory to the same agent. |
| 137 | [Code block] | [Code block] |
| 138 | Agent에 새 tool 추가 — `self.tools` — `__init__` | Add a new tool to the Agent — `self.tools` — `__init__` |
| 139 | Agent state에 필드 추가 — `state_schema` — 클래스 속성 | Add a field to Agent state — `state_schema` — class attribute |
| 140 | System prompt 동적 수정 — `request.override()` — `wrap_model_call` | Dynamically modify system prompt — `request.override()` — `wrap_model_call` |
| 141 | Tool 실행 전 검증/차단 — handler 호출 제어 — `wrap_tool_call` | Validate/block before tool execution — handler call control — `wrap_tool_call` |
| 142 | 컨텍스트 윈도우 관리 — 메시지 요약/삭제 — `before_model` | Manage context window — message summarization/deletion — `before_model` |
| 143 | 모델 응답 검증 — state 업데이트 — `after_model` | Validate model response — state update — `after_model` |
