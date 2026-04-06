# LangChain & LangGraph 101 Guide

## Sentence-by-Sentence Translation Map

---

### Section: Title and Introduction

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | LangChain & LangGraph 101 가이드 | LangChain & LangGraph 101 Guide |
| 2 | 하나의 LLM 에이전트를 만드는 것은 어렵지 않습니다. | Building a single LLM agent is not difficult. |
| 3 | 하지만 그 에이전트가 여러 세션에 걸쳐 프로젝트를 진행하고, 위험한 명령을 실행하기 전에 사람의 승인을 받고, 실패해도 이전 상태에서 복구할 수 있어야 한다면? | But what if that agent needs to work on a project across multiple sessions, get human approval before executing dangerous commands, and recover from a previous state even after failure? |
| 4 | 이 가이드는 바로 그 문제를 해결하는 두 라이브러리 — LangChain과 LangGraph — 의 핵심 개념을 다룹니다. | This guide covers the core concepts of the two libraries that solve exactly this problem — LangChain and LangGraph. |
| 5 | 이 프로젝트(`ax_advanced_class/`)의 실제 코드를 기반으로, 각 개념이 **왜 필요하고** **어떻게 사용되는지** 함께 설명합니다. | Using the actual code from this project (`ax_advanced_class/`), we explain **why each concept is needed** and **how it is used**. |

---

### Section: What You Will Learn

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 6 | 이 가이드에서 배울 것 | What You Will Learn in This Guide |
| 7 | LLM과 대화하는 표준 인터페이스 (Chat Model, 메시지 타입) | The standard interface for communicating with LLMs (Chat Model, message types) |
| 8 | LLM이 실제 행동을 수행하게 만드는 방법 (Tool) | How to make LLMs perform real actions (Tool) |
| 9 | 자율 에이전트를 만들고 실행하는 방법 (create_agent, invoke) | How to build and run an autonomous agent (create_agent, invoke) |
| 10 | LLM의 출력을 Python 객체로 제약하는 방법 (Structured Output) | How to constrain LLM output to Python objects (Structured Output) |
| 11 | 에이전트의 동작을 코드 수정 없이 확장하는 방법 (미들웨어) | How to extend agent behavior without modifying code (Middleware) |
| 12 | 여러 에이전트를 조율하는 워크플로우 (StateGraph) | Workflows that coordinate multiple agents (StateGraph) |
| 13 | 세션 간 상태 유지와 실패 복구 (Checkpointer) | State persistence across sessions and failure recovery (Checkpointer) |
| 14 | 위험한 작업 전 사람의 승인을 받는 방법 (interrupt + Command) | How to get human approval before dangerous operations (interrupt + Command) |

---

### Section: Prerequisites

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 15 | 사전 지식 | Prerequisites |
| 16 | Python 3.11+ | Python 3.11+ |
| 17 | `TypedDict`, `Annotated`, 타입 힌트 | `TypedDict`, `Annotated`, type hints |
| 18 | Pydantic `BaseModel` 기초 | Pydantic `BaseModel` basics |
| 19 | `async/await` 기초 | `async/await` basics |

---

### Section: The Big Picture — See the Forest First

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 20 | 전체 그림 — 먼저 숲을 보자 | The Big Picture — See the Forest First |
| 21 | 우리가 만들 시스템은 이런 구조입니다. | The system we are building has this structure. |
| 22 | 지금은 각 부분이 뭔지 몰라도 됩니다 — 이 가이드를 읽으면서 하나씩 채워갈 겁니다. | You do not need to know what each part is right now — you will fill them in one by one as you read this guide. |
| 23 | [Code block] | [Code block] |
| 24 | 이 그림에서 **LangChain**과 **LangGraph**의 역할: | The roles of **LangChain** and **LangGraph** in this diagram: |
| 25 | LangChain = 에이전트 안에서 작동 (LLM 호출, Tool 실행, 미들웨어) | LangChain = operates inside the agent (LLM calls, Tool execution, middleware) |
| 26 | LangGraph = 에이전트 사이에서 작동 (라우팅, 상태 관리, 체크포인팅) | LangGraph = operates between agents (routing, state management, checkpointing) |

---

### Section: Part 1: LangChain — Building Blocks of an Agent

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 27 | Part 1: LangChain — 에이전트의 빌딩 블록 | Part 1: LangChain — Building Blocks of an Agent |
| 28 | LLM provider마다 API, 메시지 포맷, 호출 방식이 다릅니다. | Each LLM provider has different APIs, message formats, and invocation methods. |
| 29 | LangChain은 이를 통합하는 **LLM SDK**로, 한 번 작성한 코드로 provider(OpenAI, Anthropic, AWS Bedrock 등)를 교체할 수 있게 합니다. | LangChain is an **LLM SDK** that unifies these, allowing you to switch providers (OpenAI, Anthropic, AWS Bedrock, etc.) with code written once. |
| 30 | 덕분에 개발자는 provider별 API 차이에 시간을 쓰는 대신, 에이전트의 실제 비즈니스 로직에 집중할 수 있습니다. | This lets developers focus on the agent's actual business logic instead of spending time on provider-specific API differences. |
| 31 | 이 파트에서 다루는 컴포넌트: | Components covered in this part: |

---

### Section: Chat Model — Standard Interface for Communicating with LLMs

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 32 | Chat Model — LLM과 대화하는 표준 인터페이스 | Chat Model — Standard Interface for Communicating with LLMs |
| 33 | OpenAI, Anthropic, Bedrock 각각 API가 다르지만, 애플리케이션 코드는 "메시지를 보내고 응답을 받는다"는 동일한 패턴을 반복합니다. | OpenAI, Anthropic, and Bedrock each have different APIs, but application code repeats the same pattern of "send messages and receive responses." |
| 34 | Chat Model은 이 패턴을 표준화하여, 코드를 변경하지 않고 모델을 교체할 수 있게 합니다. | Chat Model standardizes this pattern, allowing you to swap models without changing code. |
| 35 | [Code block] | [Code block] |
| 36 | `init_chat_model()`은 문자열 하나로 모델을 로드합니다. | `init_chat_model()` loads a model with a single string. |
| 37 | 나중에 "Bedrock에서 OpenAI로 바꿔야지" 할 때 이 한 줄만 수정하면 됩니다. | When you later want to switch from Bedrock to OpenAI, you only need to change this one line. |

---

### Section: Message Types — Basic Unit of LLM Communication

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 38 | 메시지 타입 — LLM 통신의 기본 단위 | Message Types — Basic Unit of LLM Communication |
| 39 | LLM과의 대화는 단순 문자열이 아니라, **역할(role)이 구분된 메시지 목록**입니다. | Conversations with LLMs are not simple strings but **lists of messages with distinct roles**. |
| 40 | 이 구조가 있어야 모델이 "누가 무엇을 말했는지" 이해하고, tool 호출과 멀티턴 대화를 지원할 수 있습니다. | This structure is necessary for the model to understand "who said what" and support tool calls and multi-turn conversations. |
| 41 | `SystemMessage` — 시스템 → LLM — AI의 행동 규칙을 설정 | `SystemMessage` — System → LLM — Sets the AI's behavioral rules |
| 42 | `HumanMessage` — 사용자 → LLM — 사용자의 입력 | `HumanMessage` — User → LLM — User's input |
| 43 | `AIMessage` — LLM → 시스템 — LLM의 응답 + `tool_calls`로 도구 호출 요청 | `AIMessage` — LLM → System — LLM's response + tool call requests via `tool_calls` |
| 44 | `ToolMessage` — Tool → LLM — 도구 실행 결과를 돌려줌 | `ToolMessage` — Tool → LLM — Returns the tool execution result |
| 45 | 이 네 가지 메시지가 대화 안에서 어떤 순서로 흐르는지 봅시다: | Let us see in what order these four message types flow within a conversation: |
| 46 | [Code block] | [Code block] |
| 47 | `SystemMessage`로 규칙을 설정하고, `HumanMessage`로 요청하면, LLM이 `AIMessage`에 `tool_calls`를 담아 도구를 호출합니다. | You set rules with `SystemMessage`, make a request with `HumanMessage`, and the LLM calls tools by including `tool_calls` in the `AIMessage`. |
| 48 | 도구 결과가 `ToolMessage`로 돌아오면, LLM이 이를 보고 최종 응답을 생성합니다. | When the tool result comes back as a `ToolMessage`, the LLM sees it and generates the final response. |
| 49 | 이것이 **ReAct 루프**의 한 사이클입니다. | This is one cycle of the **ReAct loop**. |

---

### Section: Tool — Enabling LLMs to Take Real Actions Beyond Text

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 50 | Tool — LLM이 텍스트를 넘어 실제 행동을 하게 만드는 도구 | Tool — Enabling LLMs to Take Real Actions Beyond Text |
| 51 | LLM은 텍스트만 생성할 수 있습니다. | LLMs can only generate text. |
| 52 | 파일을 읽거나, 코드를 실행하거나, API를 호출하려면 **Tool**이 필요합니다. | To read files, execute code, or call APIs, you need **Tools**. |
| 53 | Tool은 스키마가 정의된 함수로, LLM이 추론 과정에서 직접 호출할 수 있습니다. | A Tool is a function with a defined schema that the LLM can directly call during its reasoning process. |
| 54 | Tool 정의에는 세 가지 요소가 필요합니다: | Defining a Tool requires three elements: |
| 55 | [Code block] | [Code block] |
| 56 | LLM은 docstring을 읽고 "지금 할 일 목록을 업데이트해야 하는 상황인가?"를 **스스로 판단**합니다. | The LLM reads the docstring and **decides on its own** whether "this is a situation where I should update the to-do list." |
| 57 | 설명이 모호하면 LLM이 잘못된 시점에 도구를 호출합니다. | If the description is vague, the LLM will call the tool at the wrong time. |

---

### Section: create_agent() — Assembling an Agent

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 58 | create_agent() — 에이전트 조립 | create_agent() — Assembling an Agent |
| 59 | 위의 빌딩 블록(Chat Model + 메시지 + Tool)을 조합하여 **자율적으로 동작하는 에이전트**를 만드는 함수입니다. | This is the function that combines the building blocks above (Chat Model + messages + Tool) to create an **autonomously operating agent**. |
| 60 | [Code block] | [Code block] |
| 61 | 이 한 줄로 자동 구성되는 것들: | What this single call automatically configures: |
| 62 | **ReAct 루프**: LLM이 tool_calls를 반환하면 → tool 실행 → 결과를 LLM에 전달 → 반복 | **ReAct loop**: When the LLM returns tool_calls → execute tool → pass result to LLM → repeat |
| 63 | **미들웨어 체인**: tool/model 호출 전후를 가로채기 | **Middleware chain**: Intercepts before and after tool/model calls |
| 64 | **상태 관리**: messages + 커스텀 state | **State management**: messages + custom state |
| 65 | 에이전트를 실행하고 결과를 받는 방법: | How to run the agent and get results: |
| 66 | [Code block] | [Code block] |
| 67 | `invoke()`는 에이전트가 ReAct 루프를 돌며 모든 tool 호출을 마치고 최종 응답을 생성할 때까지 기다린 후, 최종 상태를 반환합니다. | `invoke()` waits until the agent completes the ReAct loop, finishes all tool calls, generates the final response, and then returns the final state. |

---

### Section: with_structured_output() — Connecting LLM Decisions to Code Logic

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 68 | with_structured_output() — LLM 판단을 코드 로직에 연결 | with_structured_output() — Connecting LLM Decisions to Code Logic |
| 69 | 지금까지 LLM의 출력은 자유 텍스트였습니다. | Until now, LLM output has been free text. |
| 70 | 하지만 "initializer로 라우팅할까, coding으로 라우팅할까?"처럼 **코드가 분기해야 하는 판단**은 텍스트로는 불안정합니다. | But for **decisions where code must branch** — like "should I route to initializer or coding?" — text is unreliable. |
| 71 | `with_structured_output()`은 LLM의 출력을 Pydantic 모델로 제약합니다. | `with_structured_output()` constrains the LLM's output to a Pydantic model. |
| 72 | 먼저 원하는 출력 구조를 정의합니다: | First, define the desired output structure: |
| 73 | [Code block] | [Code block] |
| 74 | `Literal["a", "b", "c"]` — LLM이 이 값들 중에서만 선택 | `Literal["a", "b", "c"]` — The LLM selects only from these values |
| 75 | `Field(description=...)` — LLM이 각 필드의 의미를 이해하는 근거 | `Field(description=...)` — The basis for the LLM to understand each field's meaning |
| 76 | `Optional[str]` — 없어도 되는 필드 | `Optional[str]` — A field that can be omitted |
| 77 | 그 다음 LLM을 감쌉니다: | Then wrap the LLM: |
| 78 | [Code block] | [Code block] |
| 79 | 결과가 문자열이 아닌 **Python 객체**이므로, `if/else`로 바로 분기할 수 있습니다. | Since the result is a **Python object** rather than a string, you can branch directly with `if/else`. |

---

### Section: Wrapping an Agent as a StateGraph Node

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 80 | 에이전트를 StateGraph 노드로 감싸는 패턴 | Pattern for Wrapping an Agent as a StateGraph Node |
| 81 | `create_agent()`로 만든 에이전트를 LangGraph의 StateGraph 노드 안에서 실행하는 패턴입니다. | This is the pattern for running an agent created with `create_agent()` inside a LangGraph StateGraph node. |
| 82 | 이것이 LangChain과 LangGraph가 결합되는 핵심 지점입니다. | This is the key point where LangChain and LangGraph come together. |
| 83 | [Code block] | [Code block] |
| 84 | 이 패턴은 LangGraph의 **서브그래프(Subgraph)** 개념입니다. | This pattern is LangGraph's **Subgraph** concept. |
| 85 | `create_agent()`가 반환하는 에이전트는 내부적으로 자체 StateGraph(ReAct 루프)를 가진 **중첩된 그래프(nested graph)**입니다. | The agent returned by `create_agent()` is a **nested graph** that internally has its own StateGraph (ReAct loop). |
| 86 | [Code block] | [Code block] |
| 87 | **독립된 State**: 서브그래프는 자체 State를 가집니다. | **Independent State**: The subgraph has its own State. |
| 88 | 오케스트레이터는 `messages`만 관리하고, 에이전트 서브그래프는 `messages + todos` 등 더 풍부한 상태를 내부적으로 관리합니다. | The orchestrator only manages `messages`, while the agent subgraph internally manages richer state such as `messages + todos`. |
| 89 | **State 격리**: 서브그래프 내부의 중간 과정(수십 턴의 tool 호출, 디버깅 등)이 부모 그래프에 노출되지 않습니다. | **State isolation**: The intermediate processes inside the subgraph (dozens of turns of tool calls, debugging, etc.) are not exposed to the parent graph. |
| 90 | 부모는 서브그래프의 최종 결과만 받습니다. | The parent receives only the subgraph's final result. |
| 91 | **재사용성**: 같은 에이전트 서브그래프를 여러 노드에서 재사용할 수 있습니다. | **Reusability**: The same agent subgraph can be reused across multiple nodes. |
| 92 | 이 프로젝트에서 위 코드가 하는 일: 오케스트레이터가 `messages`를 서브그래프에 전달하고, 서브그래프가 내부적으로 ReAct 루프를 완료한 후, 최종 응답 메시지 하나만 오케스트레이터로 돌려줍니다. | What the above code does in this project: the orchestrator passes `messages` to the subgraph, the subgraph internally completes the ReAct loop, and returns only a single final response message to the orchestrator. |

---

### Section: Middleware — Extending Agent Behavior Without Modifying Code

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 93 | 미들웨어 — 에이전트 동작을 코드 수정 없이 확장 | Middleware — Extending Agent Behavior Without Modifying Code |
| 94 | 에이전트의 기본 동작(LLM 호출, tool 실행)을 수정하고 싶을 때, 에이전트 코드 자체를 바꾸지 않고 **미들웨어로 감싸서** 동작을 변경합니다. | When you want to modify the agent's basic behavior (LLM calls, tool execution), you change the behavior by **wrapping it with middleware** instead of changing the agent code itself. |
| 95 | Express나 Django의 미들웨어와 같은 개념입니다. | It is the same concept as middleware in Express or Django. |
| 96 | 미들웨어는 두 가지 가로채기 지점을 제공합니다: | Middleware provides two interception points: |
| 97 | `wrap_tool_call` — Tool 실행 — 명령어 검증, 권한 체크, 출력 가공 | `wrap_tool_call` — Tool execution — command validation, permission checks, output processing |
| 98 | `wrap_model_call` — LLM 호출 — 시스템 프롬프트 주입, 모델 교체 | `wrap_model_call` — LLM call — system prompt injection, model swapping |
| 99 | `wrap_tool_call`의 실제 사용 예시 — 위험한 명령을 차단하는 미들웨어: | Actual usage example of `wrap_tool_call` — middleware that blocks dangerous commands: |
| 100 | [Code block] | [Code block] |
| 101 | `wrap_model_call`의 실제 사용 예시 — LLM 호출 전에 시스템 프롬프트를 주입하는 미들웨어: | Actual usage example of `wrap_model_call` — middleware that injects a system prompt before the LLM call: |
| 102 | [Code block] | [Code block] |
| 103 | 이 프로젝트에서는 5개의 미들웨어가 체인으로 연결됩니다: | In this project, five middlewares are chained together: |
| 104 | [Code block] | [Code block] |
| 105 | 순서가 중요합니다 — 앞에 있을수록 먼저 실행됩니다. | Order matters — those listed first are executed first. |
| 106 | `ToolValidationMiddleware`가 맨 앞이므로 위험한 명령이 다른 미들웨어에 도달하기 전에 차단됩니다. | Since `ToolValidationMiddleware` is first, dangerous commands are blocked before reaching other middlewares. |

---

### Section: @dynamic_prompt — Injecting Runtime State into the Prompt

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 107 | @dynamic_prompt — 런타임 상태를 프롬프트에 주입 | @dynamic_prompt — Injecting Runtime State into the Prompt |
| 108 | `wrap_model_call`의 특수한 형태로, 정적 시스템 프롬프트에 런타임 상태를 덧붙입니다: | A specialized form of `wrap_model_call` that appends runtime state to the static system prompt: |
| 109 | [Code block] | [Code block] |
| 110 | 정적 부분을 앞에, 동적 부분을 뒤에 배치하면 LLM의 **프롬프트 캐싱**이 정적 접두사를 재사용하여 비용과 지연시간을 줄입니다. | Placing the static part first and the dynamic part after allows LLM **prompt caching** to reuse the static prefix, reducing cost and latency. |

---

### Section: Part 2: LangGraph — Execution Flow and State Management

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 111 | Part 2: LangGraph — 실행 흐름과 상태 관리 | Part 2: LangGraph — Execution Flow and State Management |
| 112 | LLM 호출은 기본적으로 **무상태(stateless)이고 단발성(one-shot)**입니다. | LLM calls are fundamentally **stateless and one-shot**. |
| 113 | 하지만 실제 에이전트 애플리케이션에는 이것만으로 해결할 수 없는 문제들이 있습니다: | But real agent applications have problems that cannot be solved with this alone: |
| 114 | **순환(Cycle)** — tool 결과를 보고 다음 행동을 결정해야 함 — 그래프의 순환 엣지 | **Cycles** — need to decide the next action based on tool results — cyclic edges in the graph |
| 115 | **영속성(Persistence)** — 세션 간 상태 유지, 실패 시 복구 — Checkpointer | **Persistence** — maintaining state across sessions, recovery on failure — Checkpointer |
| 116 | **사람의 개입** — 위험한 행동 전 승인 필요 — interrupt() + Command | **Human intervention** — approval needed before dangerous actions — interrupt() + Command |
| 117 | LangGraph는 에이전트 로직을 **상태를 가진 그래프**로 모델링하여 이 세 가지를 제공합니다. | LangGraph provides these three by modeling agent logic as a **stateful graph**. |
| 118 | 핵심 차별점은 **런타임에 흐름과 데이터를 코드로 세밀하게 제어할 수 있다**는 것입니다. | The key differentiator is the ability to **finely control flow and data with code at runtime**. |
| 119 | 실행 중에 어떤 노드로 분기할지, 어떤 데이터를 다음 단계에 넘길지, 언제 실행을 멈추고 사람의 승인을 받을지를 개발자가 직접 설계합니다. | Developers directly design which node to branch to during execution, what data to pass to the next step, and when to pause execution and request human approval. |
| 120 | 이 수준의 커스터마이징 덕분에 프로덕션에서 요구하는 안전성, 복구 가능성, 관찰 가능성을 갖춘 에이전트를 만들 수 있습니다. | This level of customization enables building agents with the safety, recoverability, and observability required in production. |
| 121 | 이 파트에서 다루는 컴포넌트: | Components covered in this part: |

---

### Section: StateGraph — The Backbone of a Workflow

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 122 | StateGraph — 워크플로우의 뼈대 | StateGraph — The Backbone of a Workflow |
| 123 | StateGraph는 노드 기반 워크플로우의 핵심 클래스입니다. | StateGraph is the core class for node-based workflows. |
| 124 | 모든 노드가 **하나의 공유 상태(State)**를 통해 통신하므로 데이터 흐름이 명확하고 디버깅이 쉽습니다. | Since all nodes communicate through **a single shared State**, the data flow is clear and debugging is easy. |
| 125 | 가장 단순한 형태부터 시작합시다: | Let us start from the simplest form: |
| 126 | 여기에 라우팅을 추가하면: | If we add routing: |
| 127 | 이 그래프를 구성하는 4가지 요소를 하나씩 봅시다. | Let us look at the four elements that make up this graph one by one. |

---

### Section: State — Data Shared by the Graph

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 128 | State — 그래프가 공유하는 데이터 | State — Data Shared by the Graph |
| 129 | State는 그래프 전체에서 공유되는 데이터 구조입니다. | State is the data structure shared across the entire graph. |
| 130 | `TypedDict`로 정의합니다: | It is defined using `TypedDict`: |
| 131 | [Code block] | [Code block] |
| 132 | `Annotated[list, operator.add]`가 **Reducer**입니다. | `Annotated[list, operator.add]` is the **Reducer**. |
| 133 | 노드가 `{"messages": [new_msg]}`를 반환했을 때, 기존 메시지를 교체하지 않고 뒤에 **추가**합니다. | When a node returns `{"messages": [new_msg]}`, it **appends** to the existing messages instead of replacing them. |
| 134 | Reducer가 없는 필드(`next_agent`)는 단순 덮어쓰기됩니다. | Fields without a Reducer (`next_agent`) are simply overwritten. |

---

### Section: Node — Execution Unit of the Graph

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 135 | Node — 그래프의 실행 단위 | Node — Execution Unit of the Graph |
| 136 | 노드는 State를 받아서 부분 업데이트를 반환하는 **일반 Python 함수**입니다: | A node is an **ordinary Python function** that receives State and returns a partial update: |
| 137 | [Code block] | [Code block] |
| 138 | 반환하는 dict는 State 전체가 아니라 **변경된 필드만** 포함하면 됩니다. | The returned dict only needs to contain **the changed fields**, not the entire State. |

---

### Section: Edge — Connecting Flows Between Nodes

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 139 | Edge — 노드 간 흐름 연결 | Edge — Connecting Flows Between Nodes |
| 140 | **Normal Edge** — 무조건 다음 노드로: | **Normal Edge** — unconditionally goes to the next node: |
| 141 | [Code block] | [Code block] |
| 142 | **Conditional Edge** — 상태 값에 따라 동적으로 분기합니다. | **Conditional Edge** — branches dynamically based on the state value. |
| 143 | 에이전트가 "다음에 뭘 할지" 결정하는 핵심 메커니즘입니다: | This is the core mechanism by which the agent decides "what to do next": |
| 144 | [Code block] | [Code block] |
| 145 | `route_decision` 함수가 `"coding"`을 반환하면 coding 노드로 이동합니다. | If the `route_decision` function returns `"coding"`, it moves to the coding node. |
| 146 | LLM의 판단(`with_structured_output`)이 여기서 실행 흐름을 결정합니다. | The LLM's decision (`with_structured_output`) determines the execution flow here. |

---

### Section: Full Assembly — Creating an Executable Graph with compile()

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 147 | 전체 조립 — compile()로 실행 가능한 그래프 만들기 | Full Assembly — Creating an Executable Graph with compile() |
| 148 | 지금까지의 조각들을 하나로 조립합니다: | Let us assemble all the pieces so far into one: |
| 149 | [Code block] | [Code block] |
| 150 | `compile()`은 그래프를 검증하고 실행 가능한 객체로 변환합니다. | `compile()` validates the graph and converts it into an executable object. |
| 151 | `checkpointer`를 여기서 연결하면 상태 영속성이 활성화됩니다. | Connecting a `checkpointer` here activates state persistence. |

---

### Section: Checkpointer — Why State Must Be Saved

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 152 | Checkpointer — 왜 상태를 저장해야 하는가 | Checkpointer — Why State Must Be Saved |
| 153 | Checkpointer는 그래프의 상태를 영구 저장하는 계층입니다. | Checkpointer is the layer that persistently stores the graph's state. |
| 154 | 세 가지 핵심 기능이 있습니다: | It has three core capabilities: |
| 155 | **멀티턴 대화** — `thread_id` 기반으로 대화 상태를 저장/복원 | **Multi-turn conversation** — saves/restores conversation state based on `thread_id` |
| 156 | **실패 복구** — 마지막 성공 지점부터 재개 | **Failure recovery** — resumes from the last successful point |
| 157 | **Human-in-the-loop** — `interrupt()`로 일시 정지 후 재개 (**필수 전제 조건**) | **Human-in-the-loop** — pause and resume with `interrupt()` (**required prerequisite**) |
| 158 | 멀티턴 대화의 예시 — 같은 `thread_id`를 사용하면 이전 대화가 유지됩니다: | Multi-turn conversation example — using the same `thread_id` maintains the previous conversation: |
| 159 | [Code block] | [Code block] |
| 160 | `MemorySaver` — 개발/테스트 (프로세스 종료 시 소실) | `MemorySaver` — development/testing (lost when process terminates) |
| 161 | `SqliteSaver` — 파일 기반 영구 저장 | `SqliteSaver` — file-based permanent storage |
| 162 | `PostgresSaver` — 프로덕션 | `PostgresSaver` — production |
| 163 | **주의:** `create_agent(checkpointer=True)`를 설정하지 않으면 에이전트 내부의 `interrupt()` 호출이 실패합니다. | **Warning:** If you do not set `create_agent(checkpointer=True)`, `interrupt()` calls inside the agent will fail. |

---

### Section: interrupt() + Command — Getting Human Approval Before Dangerous Operations

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 164 | interrupt() + Command — 위험한 작업 전 사람의 승인 받기 | interrupt() + Command — Getting Human Approval Before Dangerous Operations |
| 165 | 에이전트가 `rm -rf`를 실행하려고 합니다. | The agent is about to execute `rm -rf`. |
| 166 | 자동으로 실행시킬 건가요? | Will you let it run automatically? |
| 167 | `interrupt()`는 그래프 실행을 **일시 정지**하고, 사용자에게 결정을 맡긴 후, `Command(resume=value)`로 **재개**합니다. | `interrupt()` **pauses** graph execution, delegates the decision to the user, then **resumes** with `Command(resume=value)`. |
| 168 | `interrupt()`가 호출되면 일어나는 일: | What happens when `interrupt()` is called: |
| 169 | 그래프 실행이 **즉시 중단** | Graph execution is **immediately halted** |
| 170 | interrupt에 전달한 데이터가 **호출자(UI)에게 반환** | The data passed to interrupt is **returned to the caller (UI)** |
| 171 | 사용자가 승인/거부를 결정 | The user decides to approve or deny |
| 172 | `Command(resume=value)`로 **실행 재개** — value가 `interrupt()`의 반환값이 됨 | **Execution resumes** with `Command(resume=value)` — value becomes the return value of `interrupt()` |
| 173 | 이 프로젝트에서의 실제 사용: | Actual usage in this project: |
| 174 | [Code block] | [Code block] |

---

### Section: interrupt() Full Operation Flow — What Actually Happens in the Code

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 175 | interrupt() 전체 동작 흐름 — 실제 코드에서 무슨 일이 일어나는가 | interrupt() Full Operation Flow — What Actually Happens in the Code |
| 176 | 위의 코드 조각들이 실제로 어떻게 연결되는지 3단계로 봅시다: | Let us see how the code snippets above are actually connected in three steps: |
| 177 | **1단계: Agent가 위험한 명령을 감지하여 interrupt** | **Step 1: Agent detects a dangerous command and triggers interrupt** |
| 178 | [Code block] | [Code block] |
| 179 | **2단계: 호출자(CLI/UI)가 interrupt 데이터를 받음** | **Step 2: The caller (CLI/UI) receives the interrupt data** |
| 180 | [Code block] | [Code block] |
| 181 | **3단계: 사용자 응답으로 resume** | **Step 3: Resume with the user's response** |
| 182 | [Code block] | [Code block] |
| 183 | 핵심: `thread_id`가 같으면 checkpointer가 이전 상태를 복원하고, `interrupt()` 호출 지점부터 재개합니다. | Key point: If the `thread_id` is the same, the checkpointer restores the previous state and resumes from the `interrupt()` call point. |
| 184 | **checkpointer 없이는 interrupt가 동작하지 않습니다.** | **interrupt does not work without a checkpointer.** |
| 185 | Command는 interrupt 재개 외에도 **상태 업데이트 + 노드 이동**을 하나의 객체로 통합합니다: | Command also consolidates **state update + node navigation** into a single object, beyond just interrupt resumption: |
| 186 | [Code block] | [Code block] |

---

### Section: Revisiting the Big Picture — Now You Can See Each Part

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 187 | 다시 전체 그림 — 이제 각 부분이 보인다 | Revisiting the Big Picture — Now You Can See Each Part |
| 188 | 처음에 봤던 아키텍처를 다시 봅시다. | Let us look at the architecture we saw at the beginning again. |
| 189 | 이제 각 컴포넌트가 무엇인지 알고 있습니다: | Now you know what each component is: |
| 190 | [Code block] | [Code block] |

---

### Section: Summary

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 191 | 요약 | Summary |
| 192 | **LangChain** — Chat Model — Provider에 독립적인 LLM 인터페이스 | **LangChain** — Chat Model — Provider-independent LLM interface |
| 193 | 메시지 4종 — 역할이 구분된 대화 구조 | 4 message types — conversation structure with distinct roles |
| 194 | Tool — LLM이 실제 행동을 수행 | Tool — LLM performs real actions |
| 195 | create_agent() + invoke() — 빌딩 블록을 조합한 자율 에이전트 | create_agent() + invoke() — autonomous agent assembled from building blocks |
| 196 | with_structured_output() — LLM 판단을 Python 객체로 | with_structured_output() — LLM decisions as Python objects |
| 197 | 에이전트-노드 패턴 — LangChain 에이전트를 LangGraph 노드로 결합 | Agent-node pattern — combining LangChain agents as LangGraph nodes |
| 198 | 미들웨어 — 에이전트 동작을 코드 수정 없이 확장 | Middleware — extend agent behavior without code changes |
| 199 | @dynamic_prompt — 런타임 상태를 프롬프트에 주입 | @dynamic_prompt — inject runtime state into the prompt |
| 200 | **LangGraph** — StateGraph — 노드/엣지 기반 워크플로우 | **LangGraph** — StateGraph — node/edge-based workflow |
| 201 | State + Reducer — 타입 안전한 공유 상태 + 병합 규칙 | State + Reducer — type-safe shared state + merge rules |
| 202 | Node — State를 받고 부분 업데이트를 반환하는 함수 | Node — function that receives State and returns partial updates |
| 203 | Edge (Normal/Conditional) — 고정 이동 또는 상태 기반 분기 | Edge (Normal/Conditional) — fixed navigation or state-based branching |
| 204 | Checkpointer — 멀티턴 대화, 실패 복구, interrupt 전제 조건 | Checkpointer — multi-turn conversation, failure recovery, interrupt prerequisite |
| 205 | interrupt() — 사람의 승인을 위해 실행을 일시 정지 | interrupt() — pause execution for human approval |
| 206 | Command — 상태 업데이트 + 흐름 제어 + interrupt 재개 | Command — state update + flow control + interrupt resumption |

---

### Section: Next Steps

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 207 | 다음 단계 | Next Steps |
| 208 | 이 가이드의 개념을 실제로 적용해보세요: | Try applying the concepts from this guide in practice: |
| 209 | **`ax_advanced_class/src/orchestrator.py`** 를 열어서 이 가이드의 각 개념이 어디에 사용되는지 찾아보기 | Open **`ax_advanced_class/src/orchestrator.py`** and find where each concept from this guide is used |
| 210 | **시나리오 1 (Orchestrator-Agent Boundary)** 부터 시작 — `scenarios/` 디렉토리 참조 | Start with **Scenario 1 (Orchestrator-Agent Boundary)** — see the `scenarios/` directory |
| 211 | **TODO가 있는 미들웨어** 직접 구현해보기 — 이 가이드의 미들웨어 섹션이 도움이 됩니다 | Try implementing the **middlewares with TODOs** yourself — the middleware section of this guide will help |
