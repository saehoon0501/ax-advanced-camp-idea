# LangChain & LangGraph 101 가이드

하나의 LLM 에이전트를 만드는 것은 어렵지 않습니다. 하지만 그 에이전트가 여러 세션에 걸쳐 프로젝트를 진행하고, 위험한 명령을 실행하기 전에 사람의 승인을 받고, 실패해도 이전 상태에서 복구할 수 있어야 한다면?

이 가이드는 바로 그 문제를 해결하는 두 라이브러리 — LangChain과 LangGraph — 의 핵심 개념을 다룹니다. 이 프로젝트(`ax_advanced_class/`)의 실제 코드를 기반으로, 각 개념이 **왜 필요하고** **어떻게 사용되는지** 함께 설명합니다.

## 이 가이드에서 배울 것

- LLM과 대화하는 표준 인터페이스 (Chat Model, 메시지 타입)
- LLM이 실제 행동을 수행하게 만드는 방법 (Tool)
- 자율 에이전트를 만들고 실행하는 방법 (create_agent, invoke)
- LLM의 출력을 Python 객체로 제약하는 방법 (Structured Output)
- 에이전트의 동작을 코드 수정 없이 확장하는 방법 (미들웨어)
- 여러 에이전트를 조율하는 워크플로우 (StateGraph)
- 세션 간 상태 유지와 실패 복구 (Checkpointer)
- 위험한 작업 전 사람의 승인을 받는 방법 (interrupt + Command)

## 사전 지식

- Python 3.11+
- `TypedDict`, `Annotated`, 타입 힌트
- Pydantic `BaseModel` 기초
- `async/await` 기초

---

## 전체 그림 — 먼저 숲을 보자

우리가 만들 시스템은 이런 구조입니다. 지금은 각 부분이 뭔지 몰라도 됩니다 — 이 가이드를 읽으면서 하나씩 채워갈 겁니다.

```
사용자 입력
  ↓
┌─ StateGraph (LangGraph) ─────────────────────────┐
│                                                    │
│  router 노드 ─────→ coding 노드                   │
│  (LLM이 판단)        (에이전트가 작업 수행)         │
│       │                    │                       │
│       │              ┌─────┴──────┐                │
│       │              │  미들웨어   │                │
│       │              │  체인      │                │
│       │              └─────┬──────┘                │
│       │                    │                       │
│       │              LLM ↔ Tool 반복               │
│       │              (ReAct 루프)                   │
│                                                    │
│  checkpointer: 상태 저장/복원                       │
└────────────────────────────────────────────────────┘
```

이 그림에서 **LangChain**과 **LangGraph**의 역할:

```
LangChain = 에이전트 안에서 작동 (LLM 호출, Tool 실행, 미들웨어)
LangGraph = 에이전트 사이에서 작동 (라우팅, 상태 관리, 체크포인팅)
```

---

## Part 1: LangChain — 에이전트의 빌딩 블록

LLM provider마다 API, 메시지 포맷, 호출 방식이 다릅니다. LangChain은 이를 통합하는 **LLM SDK**로, 한 번 작성한 코드로 provider(OpenAI, Anthropic, AWS Bedrock 등)를 교체할 수 있게 합니다. 덕분에 개발자는 provider별 API 차이에 시간을 쓰는 대신, 에이전트의 실제 비즈니스 로직에 집중할 수 있습니다.

이 파트에서 다루는 컴포넌트:

```
Chat Model → 메시지 → Tool → create_agent() → Structured Output → 미들웨어
(LLM 연결)   (통신 단위)  (행동)  (에이전트 조립)   (출력 제약)       (확장)
```

### Chat Model — LLM과 대화하는 표준 인터페이스

OpenAI, Anthropic, Bedrock 각각 API가 다르지만, 애플리케이션 코드는 "메시지를 보내고 응답을 받는다"는 동일한 패턴을 반복합니다. Chat Model은 이 패턴을 표준화하여, 코드를 변경하지 않고 모델을 교체할 수 있게 합니다.

```python
from langchain_aws.chat_models import ChatBedrock
from langchain.chat_models import init_chat_model

# 방법 1: 직접 생성
llm = ChatBedrock(model_id="anthropic.claude-sonnet-4-20250514-v1:0")

# 방법 2: 문자열로 생성 — provider 교체가 한 줄
llm = init_chat_model("anthropic:claude-haiku-4-5-20251001")

# 어떤 방법이든 사용법은 동일
response = llm.invoke(messages)
```

`init_chat_model()`은 문자열 하나로 모델을 로드합니다. 나중에 "Bedrock에서 OpenAI로 바꿔야지" 할 때 이 한 줄만 수정하면 됩니다.

### 메시지 타입 — LLM 통신의 기본 단위

LLM과의 대화는 단순 문자열이 아니라, **역할(role)이 구분된 메시지 목록**입니다. 이 구조가 있어야 모델이 "누가 무엇을 말했는지" 이해하고, tool 호출과 멀티턴 대화를 지원할 수 있습니다.

```python
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
```

| 타입 | 방향 | 역할 |
|------|------|------|
| `SystemMessage` | 시스템 → LLM | AI의 행동 규칙을 설정 |
| `HumanMessage` | 사용자 → LLM | 사용자의 입력 |
| `AIMessage` | LLM → 시스템 | LLM의 응답 + `tool_calls`로 도구 호출 요청 |
| `ToolMessage` | Tool → LLM | 도구 실행 결과를 돌려줌 |

이 네 가지 메시지가 대화 안에서 어떤 순서로 흐르는지 봅시다:

```python
messages = [
    SystemMessage(content="You are a coding agent."),
    HumanMessage(content="파일 목록을 보여줘"),
    AIMessage(content="", tool_calls=[{"name": "execute", "args": {"command": "ls"}}]),
    ToolMessage(content="README.md\nsrc/\ntests/", tool_call_id="call_123"),
    AIMessage(content="현재 디렉토리에 README.md, src/, tests/가 있습니다."),
]
```

`SystemMessage`로 규칙을 설정하고, `HumanMessage`로 요청하면, LLM이 `AIMessage`에 `tool_calls`를 담아 도구를 호출합니다. 도구 결과가 `ToolMessage`로 돌아오면, LLM이 이를 보고 최종 응답을 생성합니다. 이것이 **ReAct 루프**의 한 사이클입니다.

### Tool — LLM이 텍스트를 넘어 실제 행동을 하게 만드는 도구

LLM은 텍스트만 생성할 수 있습니다. 파일을 읽거나, 코드를 실행하거나, API를 호출하려면 **Tool**이 필요합니다. Tool은 스키마가 정의된 함수로, LLM이 추론 과정에서 직접 호출할 수 있습니다.

Tool 정의에는 세 가지 요소가 필요합니다:

```python
from langchain_core.tools import tool

@tool                                           # ① 이름: "write_todos"
def write_todos(todos: list[dict]) -> Command:  # ② 스키마 — 파라미터 타입
    """에이전트의 할 일 목록을 업데이트합니다."""  # ③ 설명 — LLM이 "언제" 쓸지 판단
    return Command(update={"todos": todos})
```

LLM은 docstring을 읽고 "지금 할 일 목록을 업데이트해야 하는 상황인가?"를 **스스로 판단**합니다. 설명이 모호하면 LLM이 잘못된 시점에 도구를 호출합니다.

### create_agent() — 에이전트 조립

위의 빌딩 블록(Chat Model + 메시지 + Tool)을 조합하여 **자율적으로 동작하는 에이전트**를 만드는 함수입니다.

```python
from langchain.agents import create_agent

agent = create_agent(
    model=llm,                          # Chat Model
    middleware=[validation, filesystem], # 미들웨어 스택 (순서 중요)
    name="coding_agent",
    checkpointer=True,                  # interrupt() 사용 시 필수
)
```

이 한 줄로 자동 구성되는 것들:
- **ReAct 루프**: LLM이 tool_calls를 반환하면 → tool 실행 → 결과를 LLM에 전달 → 반복
- **미들웨어 체인**: tool/model 호출 전후를 가로채기
- **상태 관리**: messages + 커스텀 state

에이전트를 실행하고 결과를 받는 방법:

```python
result = agent.invoke({"messages": [HumanMessage("파일 목록 보여줘")]})
# result["messages"][-1].content → 에이전트의 최종 응답
```

`invoke()`는 에이전트가 ReAct 루프를 돌며 모든 tool 호출을 마치고 최종 응답을 생성할 때까지 기다린 후, 최종 상태를 반환합니다.

### with_structured_output() — LLM 판단을 코드 로직에 연결

지금까지 LLM의 출력은 자유 텍스트였습니다. 하지만 "initializer로 라우팅할까, coding으로 라우팅할까?"처럼 **코드가 분기해야 하는 판단**은 텍스트로는 불안정합니다. `with_structured_output()`은 LLM의 출력을 Pydantic 모델로 제약합니다.

먼저 원하는 출력 구조를 정의합니다:

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class RouterDecision(BaseModel):
    route: Literal["initializer", "coding", "finish"] = Field(
        description="라우팅 대상 에이전트"
    )
    reason: str = Field(
        description="라우팅 결정의 이유"
    )
    response: Optional[str] = Field(
        default=None,
        description="일반 질문에 대한 직접 응답 (route='finish'일 때만)"
    )
```

- `Literal["a", "b", "c"]` — LLM이 이 값들 중에서만 선택
- `Field(description=...)` — LLM이 각 필드의 의미를 이해하는 근거
- `Optional[str]` — 없어도 되는 필드

그 다음 LLM을 감쌉니다:

```python
structured_llm = self.llm.with_structured_output(RouterDecision)
decision: RouterDecision = structured_llm.invoke(messages)

if decision.route == "coding":
    ...  # Python 객체로 바로 분기
```

결과가 문자열이 아닌 **Python 객체**이므로, `if/else`로 바로 분기할 수 있습니다.

### 에이전트를 StateGraph 노드로 감싸는 패턴

`create_agent()`로 만든 에이전트를 LangGraph의 StateGraph 노드 안에서 실행하는 패턴입니다. 이것이 LangChain과 LangGraph가 결합되는 핵심 지점입니다.

```python
def _coding_node(self, state: OrchestratorState) -> dict:
    # 1. 오케스트레이터 상태에서 메시지 추출
    messages = state.get("messages", [])

    # 2. 에이전트 입력 구성 (에이전트는 자체 state가 더 풍부함)
    agent_input = {"messages": messages, "todos": []}

    # 3. 에이전트 실행 — 내부에서 ReAct 루프 완료
    result = self.coding_agent.invoke(agent_input)

    # 4. 최종 응답만 오케스트레이터로 반환
    return {"messages": [AIMessage(content=result["messages"][-1].content)]}
```

이 패턴은 LangGraph의 **서브그래프(Subgraph)** 개념입니다. `create_agent()`가 반환하는 에이전트는 내부적으로 자체 StateGraph(ReAct 루프)를 가진 **중첩된 그래프(nested graph)**입니다.

```
┌─ 오케스트레이터 그래프 (Parent) ─────────────┐
│                                              │
│  router 노드 ──→ coding 노드                 │
│                     │                        │
│                     ▼                        │
│              ┌─ 서브그래프 (Child) ──┐        │
│              │  model → tool        │        │
│              │    ↑       │         │        │
│              │    └───────┘         │        │
│              │  (ReAct 루프)        │        │
│              └──────────────────────┘        │
│                                              │
└──────────────────────────────────────────────┘
```

서브그래프의 핵심 특징:
- **독립된 State**: 서브그래프는 자체 State를 가집니다. 오케스트레이터는 `messages`만 관리하고, 에이전트 서브그래프는 `messages + todos` 등 더 풍부한 상태를 내부적으로 관리합니다.
- **State 격리**: 서브그래프 내부의 중간 과정(수십 턴의 tool 호출, 디버깅 등)이 부모 그래프에 노출되지 않습니다. 부모는 서브그래프의 최종 결과만 받습니다.
- **재사용성**: 같은 에이전트 서브그래프를 여러 노드에서 재사용할 수 있습니다.

이 프로젝트에서 위 코드가 하는 일: 오케스트레이터가 `messages`를 서브그래프에 전달하고, 서브그래프가 내부적으로 ReAct 루프를 완료한 후, 최종 응답 메시지 하나만 오케스트레이터로 돌려줍니다.

### 미들웨어 — 에이전트 동작을 코드 수정 없이 확장

에이전트의 기본 동작(LLM 호출, tool 실행)을 수정하고 싶을 때, 에이전트 코드 자체를 바꾸지 않고 **미들웨어로 감싸서** 동작을 변경합니다. Express나 Django의 미들웨어와 같은 개념입니다.

미들웨어는 두 가지 가로채기 지점을 제공합니다:

| 훅 | 가로채는 대상 | 용도 |
|----|-------------|------|
| `wrap_tool_call` | Tool 실행 | 명령어 검증, 권한 체크, 출력 가공 |
| `wrap_model_call` | LLM 호출 | 시스템 프롬프트 주입, 모델 교체 |

`wrap_tool_call`의 실제 사용 예시 — 위험한 명령을 차단하는 미들웨어:

```python
from langchain.agents.middleware import AgentMiddleware

class ToolValidationMiddleware(AgentMiddleware):
    def wrap_tool_call(self, request, handler):
        args = request.tool_call["args"]

        # 실행 전: 위험한 명령이면 차단
        if is_dangerous(args["command"]):
            return ToolMessage(content="Error: denied", ...)

        result = handler(request)  # 통과하면 실제 tool 실행

        # 실행 후: 출력이 너무 길면 잘라내기
        return truncate_output(result)
```

`wrap_model_call`의 실제 사용 예시 — LLM 호출 전에 시스템 프롬프트를 주입하는 미들웨어:

```python
    def wrap_model_call(self, request, handler):
        modified_request = inject_system_prompt(request)
        return handler(modified_request)
```

이 프로젝트에서는 5개의 미들웨어가 체인으로 연결됩니다:

```python
middleware = [
    ToolValidationMiddleware(config),   # 명령어 검증, 권한 체크
    FilesystemMiddleware(backend),      # 파일/실행 tool 프롬프트 주입
    TodoListMiddleware(),               # write_todos 프롬프트 주입
    SummarizationMiddleware(...),       # 컨텍스트 초과 시 자동 압축
    coding_agent_dynamic_prompt,        # 런타임 컨텍스트 주입
]
```

순서가 중요합니다 — 앞에 있을수록 먼저 실행됩니다. `ToolValidationMiddleware`가 맨 앞이므로 위험한 명령이 다른 미들웨어에 도달하기 전에 차단됩니다.

### @dynamic_prompt — 런타임 상태를 프롬프트에 주입

`wrap_model_call`의 특수한 형태로, 정적 시스템 프롬프트에 런타임 상태를 덧붙입니다:

```python
from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dynamic_prompt
def coding_agent_dynamic_prompt(request: ModelRequest) -> str:
    state = request.state  # 현재 에이전트 상태에 접근

    dynamic_content = f"""
    Workspace: {workspace}
    todos: {state.get("todos", [])}
    """

    return STATIC_SYSTEM_PROMPT + SOFT_RULES + dynamic_content
```

정적 부분을 앞에, 동적 부분을 뒤에 배치하면 LLM의 **프롬프트 캐싱**이 정적 접두사를 재사용하여 비용과 지연시간을 줄입니다.

---

## Part 2: LangGraph — 실행 흐름과 상태 관리

LLM 호출은 기본적으로 **무상태(stateless)이고 단발성(one-shot)**입니다. 하지만 실제 에이전트 애플리케이션에는 이것만으로 해결할 수 없는 문제들이 있습니다:

| 필요한 것 | 문제 | LangGraph의 해결 |
|----------|------|-----------------|
| **순환(Cycle)** | tool 결과를 보고 다음 행동을 결정해야 함 | 그래프의 순환 엣지 |
| **영속성(Persistence)** | 세션 간 상태 유지, 실패 시 복구 | Checkpointer |
| **사람의 개입** | 위험한 행동 전 승인 필요 | interrupt() + Command |

LangGraph는 에이전트 로직을 **상태를 가진 그래프**로 모델링하여 이 세 가지를 제공합니다. 핵심 차별점은 **런타임에 흐름과 데이터를 코드로 세밀하게 제어할 수 있다**는 것입니다 — 실행 중에 어떤 노드로 분기할지, 어떤 데이터를 다음 단계에 넘길지, 언제 실행을 멈추고 사람의 승인을 받을지를 개발자가 직접 설계합니다. 이 수준의 커스터마이징 덕분에 프로덕션에서 요구하는 안전성, 복구 가능성, 관찰 가능성을 갖춘 에이전트를 만들 수 있습니다.

이 파트에서 다루는 컴포넌트:

```
State → Node → Edge → compile() → Checkpointer → interrupt() + Command
(데이터)  (행동)  (흐름)  (그래프 완성)  (상태 저장)     (사람의 개입)
```

### StateGraph — 워크플로우의 뼈대

StateGraph는 노드 기반 워크플로우의 핵심 클래스입니다. 모든 노드가 **하나의 공유 상태(State)**를 통해 통신하므로 데이터 흐름이 명확하고 디버깅이 쉽습니다.

가장 단순한 형태부터 시작합시다:

```
START → 하나의_노드 → END
```

여기에 라우팅을 추가하면:

```
START → router ──→ initializer → END
                └→ coding      → END
                └→ END
```

이 그래프를 구성하는 4가지 요소를 하나씩 봅시다.

#### State — 그래프가 공유하는 데이터

State는 그래프 전체에서 공유되는 데이터 구조입니다. `TypedDict`로 정의합니다:

```python
from typing import Annotated, TypedDict, Optional
from langchain_core.messages import BaseMessage
import operator

class OrchestratorState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], operator.add]  # Reducer: 누적
    next_agent: Optional[str]                              # Reducer 없음: 덮어쓰기
```

`Annotated[list, operator.add]`가 **Reducer**입니다. 노드가 `{"messages": [new_msg]}`를 반환했을 때, 기존 메시지를 교체하지 않고 뒤에 **추가**합니다. Reducer가 없는 필드(`next_agent`)는 단순 덮어쓰기됩니다.

#### Node — 그래프의 실행 단위

노드는 State를 받아서 부분 업데이트를 반환하는 **일반 Python 함수**입니다:

```python
def router_node(state: OrchestratorState) -> dict:
    decision = structured_llm.invoke(state["messages"])
    return {"next_agent": decision.route}  # State 부분 업데이트
```

반환하는 dict는 State 전체가 아니라 **변경된 필드만** 포함하면 됩니다.

#### Edge — 노드 간 흐름 연결

**Normal Edge** — 무조건 다음 노드로:

```python
workflow.add_edge(START, "router")   # 시작하면 router로
workflow.add_edge("coding", END)     # coding 끝나면 종료
```

**Conditional Edge** — 상태 값에 따라 동적으로 분기합니다. 에이전트가 "다음에 뭘 할지" 결정하는 핵심 메커니즘입니다:

```python
def route_decision(state: OrchestratorState) -> str:
    return state.get("next_agent", "__end__")

workflow.add_conditional_edges(
    "router",              # 이 노드가 끝나면
    route_decision,        # 이 함수의 반환값으로 판단해서
    {                      # 이 매핑대로 이동
        "initializer": "initializer",
        "coding": "coding",
        "__end__": END,
    }
)
```

`route_decision` 함수가 `"coding"`을 반환하면 coding 노드로 이동합니다. LLM의 판단(`with_structured_output`)이 여기서 실행 흐름을 결정합니다.

#### 전체 조립 — compile()로 실행 가능한 그래프 만들기

지금까지의 조각들을 하나로 조립합니다:

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 1. 상태 정의된 그래프 생성
workflow = StateGraph(OrchestratorState)

# 2. 노드 추가
workflow.add_node("router", router_node)
workflow.add_node("initializer", initializer_node)
workflow.add_node("coding", coding_node)

# 3. 엣지 연결
workflow.add_edge(START, "router")
workflow.add_conditional_edges("router", route_decision, {
    "initializer": "initializer",
    "coding": "coding",
    "__end__": END,
})
workflow.add_edge("initializer", END)
workflow.add_edge("coding", END)

# 4. 컴파일 — 실행 가능한 그래프로 변환
graph = workflow.compile(checkpointer=MemorySaver())
```

`compile()`은 그래프를 검증하고 실행 가능한 객체로 변환합니다. `checkpointer`를 여기서 연결하면 상태 영속성이 활성화됩니다.

### Checkpointer — 왜 상태를 저장해야 하는가

Checkpointer는 그래프의 상태를 영구 저장하는 계층입니다. 세 가지 핵심 기능이 있습니다:

| 기능 | 설명 |
|------|------|
| **멀티턴 대화** | `thread_id` 기반으로 대화 상태를 저장/복원 |
| **실패 복구** | 마지막 성공 지점부터 재개 |
| **Human-in-the-loop** | `interrupt()`로 일시 정지 후 재개 (**필수 전제 조건**) |

멀티턴 대화의 예시 — 같은 `thread_id`를 사용하면 이전 대화가 유지됩니다:

```python
config = {"configurable": {"thread_id": "user_123"}}

# 첫 번째 대화
graph.invoke({"messages": [HumanMessage("안녕! 내 이름은 철수야")]}, config)

# 두 번째 대화 — 이전 상태가 유지됨
graph.invoke({"messages": [HumanMessage("내 이름 기억나?")]}, config)
# → "네, 철수님!"
```

사용 가능한 구현체:

| 구현체 | 용도 |
|--------|------|
| `MemorySaver` | 개발/테스트 (프로세스 종료 시 소실) |
| `SqliteSaver` | 파일 기반 영구 저장 |
| `PostgresSaver` | 프로덕션 |

**주의:** `create_agent(checkpointer=True)`를 설정하지 않으면 에이전트 내부의 `interrupt()` 호출이 실패합니다.

### interrupt() + Command — 위험한 작업 전 사람의 승인 받기

에이전트가 `rm -rf`를 실행하려고 합니다. 자동으로 실행시킬 건가요?

`interrupt()`는 그래프 실행을 **일시 정지**하고, 사용자에게 결정을 맡긴 후, `Command(resume=value)`로 **재개**합니다.

`interrupt()`가 호출되면 일어나는 일:
1. 그래프 실행이 **즉시 중단**
2. interrupt에 전달한 데이터가 **호출자(UI)에게 반환**
3. 사용자가 승인/거부를 결정
4. `Command(resume=value)`로 **실행 재개** — value가 `interrupt()`의 반환값이 됨

이 프로젝트에서의 실제 사용:

```python
# 미들웨어 안에서 — 위험한 명령 감지 시 사용자에게 질문
response = interrupt({
    "question": f"'{command}' 실행을 승인하시겠습니까?",
    "command": command,
})

if response == "always":
    self._add_allow_rule(...)  # 이 세션에서 같은 패턴 항상 허용
elif not response:
    return ToolMessage(content="Denied", status="error")
```

```python
# UI에서 — 사용자 결정을 그래프에 전달
if resume_value is not None:
    stream_input = Command(resume=resume_value)
```

### interrupt() 전체 동작 흐름 — 실제 코드에서 무슨 일이 일어나는가

위의 코드 조각들이 실제로 어떻게 연결되는지 3단계로 봅시다:

**1단계: Agent가 위험한 명령을 감지하여 interrupt**

```python
# ToolValidationMiddleware.wrap_tool_call() 안에서:
def wrap_tool_call(self, tool_call, handler):
    result = self.validate_command(tool_call.args["command"])
    
    if result.level == "ASK":
        # ← 여기서 그래프 실행이 멈춤. 상태가 checkpointer에 저장됨.
        user_response = interrupt({
            "question": f"'{tool_call.args['command']}' 실행을 승인하시겠습니까?",
            "command": tool_call.args["command"],
        })
        # ← user_response는 3단계에서 Command(resume=...)로 전달된 값
```

**2단계: 호출자(CLI/UI)가 interrupt 데이터를 받음**

```python
# main.py 또는 UI 코드에서:
config = {"configurable": {"thread_id": "session-1"}}

result = graph.invoke(input, config=config)
# → interrupt() 때문에 여기서 반환됨 (실행 완료가 아님)

# interrupt 데이터를 사용자에게 표시
print(f"Agent 요청: {result.__interrupt__}")  
user_input = input("허용? (y/n/always): ")
```

**3단계: 사용자 응답으로 resume**

```python
# 같은 thread_id로 Command(resume=...)를 보내면 interrupt 지점에서 재개
result = graph.invoke(
    Command(resume=user_input),
    config=config  # ← 같은 thread_id!
)
# → wrap_tool_call 안의 user_response = "y" or "n" or "always"
# → 승인이면 tool 실행, 거부면 ToolMessage(status="error") 반환
```

핵심: `thread_id`가 같으면 checkpointer가 이전 상태를 복원하고, `interrupt()` 호출 지점부터 재개합니다. **checkpointer 없이는 interrupt가 동작하지 않습니다.**

Command는 interrupt 재개 외에도 **상태 업데이트 + 노드 이동**을 하나의 객체로 통합합니다:

```python
return Command(
    update={"todos": new_todos},   # 상태 업데이트
    goto="next_node",               # 다음 노드로 이동
)
```

---

## 다시 전체 그림 — 이제 각 부분이 보인다

처음에 봤던 아키텍처를 다시 봅시다. 이제 각 컴포넌트가 무엇인지 알고 있습니다:

```
사용자 메시지 입력
  ↓
StateGraph (LangGraph) ─── 그래프가 전체 흐름 제어
  │
  ├─ router 노드
  │    └─ with_structured_output(RouterDecision)  ← LangChain
  │    └─ 결과: "coding" 에이전트로 라우팅
  │
  ├─ coding 노드
  │    └─ create_agent()로 만든 에이전트 실행  ← LangChain
  │         │
  │         ├─ [미들웨어 체인]
  │         │    ToolValidationMiddleware
  │         │      └─ wrap_tool_call: 명령어 검증
  │         │      └─ interrupt(): 위험한 명령 승인 요청  ← LangGraph
  │         │    FilesystemMiddleware
  │         │      └─ wrap_model_call: 파일 tool 프롬프트 주입
  │         │    TodoListMiddleware
  │         │      └─ wrap_model_call: write_todos 프롬프트 주입
  │         │    @dynamic_prompt
  │         │      └─ 정적 프롬프트 + 런타임 컨텍스트 조립
  │         │
  │         └─ ReAct 루프 (LLM ↔ Tool 반복)
  │              LLM → AIMessage(tool_calls) → Tool → ToolMessage → LLM → ...
  │
  └─ checkpointer: MemorySaver  ← LangGraph
       └─ thread_id 기반 세션 상태 저장/복원
```

---

## 요약

| 라이브러리 | 개념 | 왜 필요한가 |
|-----------|------|-----------|
| **LangChain** | Chat Model | Provider에 독립적인 LLM 인터페이스 |
| | 메시지 4종 | 역할이 구분된 대화 구조 |
| | Tool | LLM이 실제 행동을 수행 |
| | create_agent() + invoke() | 빌딩 블록을 조합한 자율 에이전트 |
| | with_structured_output() | LLM 판단을 Python 객체로 |
| | 에이전트-노드 패턴 | LangChain 에이전트를 LangGraph 노드로 결합 |
| | 미들웨어 | 에이전트 동작을 코드 수정 없이 확장 |
| | @dynamic_prompt | 런타임 상태를 프롬프트에 주입 |
| **LangGraph** | StateGraph | 노드/엣지 기반 워크플로우 |
| | State + Reducer | 타입 안전한 공유 상태 + 병합 규칙 |
| | Node | State를 받고 부분 업데이트를 반환하는 함수 |
| | Edge (Normal/Conditional) | 고정 이동 또는 상태 기반 분기 |
| | Checkpointer | 멀티턴 대화, 실패 복구, interrupt 전제 조건 |
| | interrupt() | 사람의 승인을 위해 실행을 일시 정지 |
| | Command | 상태 업데이트 + 흐름 제어 + interrupt 재개 |

## 다음 단계

이 가이드의 개념을 실제로 적용해보세요:

1. **`ax_advanced_class/src/orchestrator.py`** 를 열어서 이 가이드의 각 개념이 어디에 사용되는지 찾아보기
2. **시나리오 1 (Orchestrator-Agent Boundary)** 부터 시작 — `scenarios/` 디렉토리 참조
3. **TODO가 있는 미들웨어** 직접 구현해보기 — 이 가이드의 미들웨어 섹션이 도움이 됩니다
