# Orchestrator 구성 실습

이 실습에서는 LangChain & LangGraph의 핵심 개념을 직접 코드로 구현합니다.

**구현 파일:** `ax_advanced_class/src/orchestrator.py`

## 우리가 만들 것

사용자의 메시지를 받아 적절한 에이전트로 라우팅하는 오케스트레이터입니다:

```
사용자: "블로그 플랫폼 만들어줘"
  ↓
router 노드 (LLM이 판단: "이건 초기 설정이 필요하다")
  ↓
initializer 노드 (프로젝트 구조를 잡는 에이전트)
  ↓
END
```

```
사용자: "로그인 기능 구현해줘"
  ↓
router 노드 (LLM이 판단: "이건 코딩 작업이다")
  ↓
coding ��드 (기능을 구현하는 에이전트)
  ↓
END
```

## 실습 구조

4개의 TODO를 순서대로 구현합니다.

| TODO | 구현할 것 | 대응하는 개념 |
|------|----------|-------------|
| TODO 1 | `_build_workflow()` | StateGraph 조립 |
| TODO 2 | `_router_node()` | Structured Output + 메시지 생성 |
| TODO 3 | `_route_decision()` | Conditional Edge 분기 함수 |
| TODO 4 | `_coding_node()` | 에이전트-노드 연결 패턴 |

---

## 사전 제공 코드

TODO 1-4를 구현하기 전에, 아래 두 클래스가 어떻게 정의되어 있는지 먼저 읽으세요. 이 코드는 이미 구현되어 있습니다.

### OrchestratorState — State + Reducer

```python
class OrchestratorState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], operator.add]  # ← reducer: 리스트를 합침 (append)
    next_agent: Optional[AgentRoute]                      # ← reducer 없음: 덮어쓰기
```

- `Annotated[..., operator.add]` — `operator.add`가 reducer 역할. 노드가 `{"messages": [msg]}`를 반환��면 기존 리스트 뒤에 추가됩니다
- `next_agent`에는 reducer가 없음 — 새 값이 오면 이전 값을 **덮어씁니다**
- `total=False` — 모든 필드가 optional (초기값 없이 시작 가능)

### RouterDecision — with_structured_output + Pydantic

```python
class RouterDecision(BaseModel):
    route: Literal["initializer", "coding", "finish"] = Field(
        description="Choose: 'initializer' for new project setup, 'coding' for feature work, 'finish' for simple responses"
    )
    reason: str = Field(description="Why this route was chosen")
    response: Optional[str] = Field(default=None, description="Direct response when route='finish'")
```

- `Literal[...]` — LLM이 반환할 수 있는 값을 3개로 제한합니다
- `Field(description=...)` — LLM이 각 필드의 의미를 이해하는 데 사용. description이 없으면 LLM이 잘못된 값을 반환할 수 있습니다
- `with_structured_output(RouterDecision)` — LLM 출력을 이 Pydantic 모델로 강제 파싱합니다

---

## TODO 1: _build_workflow() 구현

**파일:** `orchestrator.py` — `_build_workflow()` 메서드

**배울 개념:** StateGraph 조립

그래프를 조립하는 전체 과정을 구현합니다. 완성되면 이런 구조가 됩니다:

```
START → router ──→ initializer → END
                └→ coding      → END
                └→ END
```

**구현할 코드:**

```python
def _build_workflow(self) -> CompiledStateGraph:
    # TODO 1: StateGraph를 조립하세요
    #
    # Step 1: StateGraph(OrchestratorState)로 그래프 생성
    #
    # Step 2: 노드 3개 추가
    #   - "router" → self._router_node
    #   - "initializer" → self._initializer_node
    #   - "coding" → self._coding_node
    #   힌트: workflow.add_node("이름", 함수)
    #
    # Step 3: 엣지 연결
    #   - START → "router" (Normal Edge)
    #   - "router" → 조건부 분기 (Conditional Edge)
    #     분기 함수: self._route_decision
    #     매핑: AgentRoute.INITIALIZER → "initializer"
    #           AgentRoute.CODING → "coding"
    #           AgentRoute.FINISH → END
    #   - "initializer" → END (Normal Edge)
    #   - "coding" → END (Normal Edge)
    #   힌트: add_edge(), add_conditional_edges()
    #
    # Step 4: compile(checkpointer=self.checkpointer)
    #
    return  # CompiledStateGraph
```

**확인:** `add_conditional_edges`의 세 번째 인자(매핑 dict)에서 `AgentRoute.FINISH`가 `END`로 매핑되는지 확인하세요.

---

## TODO 2: _router_node() 구현

**파일:** `orchestrator.py` — `_router_node()` 메서드

**배울 개념:** with_structured_output 사용 + 메시지 생성

LLM에게 시스템 프롬프트와 대화 메시지를 보내서 라우팅 결정을 받고, 그 결과를 State에 반영합니다.

**구현할 코드:**

```python
def _router_node(self, state: OrchestratorState) -> dict:
    # TODO 2: LLM으로 라우팅 결정을 내리세요
    #
    # Step 1: state에서 messages 추출
    #
    # Step 2: with_structured_output(RouterDecision)으로 LLM 감싸기
    #   structured_llm = self.llm.with_structured_output(RouterDecision)
    #
    # Step 3: LLM 호출
    #   입력: [{"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT}, *messages]
    #   힌트: structured_llm.invoke([...])
    #   결과: RouterDecision 객체 (decision.route, decision.reason, decision.response)
    #
    # Step 4: decision.route를 AgentRoute enum으로 변환
    #   "initializer" → AgentRoute.INITIALIZER
    #   "coding" → AgentRoute.CODING
    #   "finish" → AgentRoute.FINISH
    #
    # Step 5: 반환값 구성
    #   return {
    #       "next_agent": route,
    #       "messages": [AIMessage(content=적절한_메시지)],
    #   }
    #   힌트: decision.response가 있으면 그걸 사용, 없으면 reason 사용
    #
    return {}
```

**확인:** `with_structured_output`의 결과가 `RouterDecision` 객체인지, `decision.route`로 접근 가능한지 확인하세요.

---

## TODO 3: _route_decision() 구현

**파일:** `orchestrator.py` — `_route_decision()` 메서드

**배울 개념:** Conditional Edge 분기 함수

`add_conditional_edges`에 전달하는 분기 함수입니다. State에서 `next_agent` 값을 읽어서 반환하면, 그 값에 따라 다음 노드가 결정됩니다.

**구현할 코드:**

```python
def _route_decision(self, state: OrchestratorState) -> AgentRoute:
    # TODO 3: state에서 next_agent를 추출하여 반환하세요
    #
    # 힌트: state.get("next_agent", 기본값)
    # next_agent가 없으면 AgentRoute.FINISH를 기본값으로
    #
    return  # AgentRoute
```

**확인:** 이 함수의 반환값이 TODO 1의 `add_conditional_edges` 매핑 dict의 **키**와 일치하는지 확인하세요.

---

## TODO 4: _coding_node() 구현

**파일:** `orchestrator.py` — `_coding_node()` 메서드

**배울 개념:** 에이전트-노드 연결 패턴 (서브그래프)

`create_agent()`로 만든 에이전트를 노드 안에서 `invoke()`합니다. 핵��은 **오케스트레이터 State와 에이전트 State가 다르다**는 것입니다.

**구현할 코드:**

```python
def _coding_node(self, state: OrchestratorState) -> dict:
    # TODO 4: coding 에이전트를 실행하고 결과를 반환하세요
    #
    # Step 1: 오케스트레이터 state에서 messages 추출
    #
    # Step 2: 에이전트 입력 구성
    #   coding 에이전트는 messages 외에 todos도 필요합니다
    #   {"messages": messages, "todos": []}
    #
    # Step 3: self.coding_agent.invoke(agent_input) 실행
    #
    # Step 4: 에이전트의 최종 응답만 오케스트레이터로 반환
    #   에이전트는 수십 턴의 대화를 할 수 있지만,
    #   오케스트레이터에는 마지막 메시지만 돌려줍니다
    #   return {"messages": [AIMessage(content=마지막_메시지)]}
    #
    #   왜? → 에이전트의 전체 대화를 오케스트레이터에 넣으면
    #         컨텍스트 윈���우가 오염됩니다
    #
    return {"messages": []}
```

**확인:** `result["messages"][-1].content`로 마지막 메시지를 추출했는지 확인하세요. 전체 messages를 반환하면 컨텍스트 오염이 발생합니다.

**참고:** `_initializer_node()`도 같은 패턴입니다. 다만 `todos` 필드가 필요 없다는 차이만 있습니다.

---

## 검증 방법

모든 TODO를 구현한 후:

```bash
uv run python -m ax_advanced_class.src.main
```

프롬프트에서 다음을 테스트:
1. `"블로그 플랫폼 만들어줘"` → initializer로 라우팅되는지
2. `"로그인 기능 구현해줘"` → coding으로 라우팅되는지
3. `"안녕하세요"` → finish로 라우팅되고 직접 응답하는지

---

## 흔한 실패와 대처

| 증상 | 원인 | 해결 |
|------|------|------|
| `ValidationError` on RouterDecision | LLM이 `Literal` 밖의 값 반환 | `with_structured_output`이 자동 재시도함. `Field(description=...)`을 더 명확히 작성 |
| Router가 항상 같은 agent로 보냄 | `ORCHESTRATOR_SYSTEM_PROMPT`가 모호 | 라우팅 조건을 더 구체적으로 (예: "feature_list.json이 없으면 initializer") |
| Agent가 응답 없이 멈춤 | `recursion_limit` 초과 (기본 25) | `create_agent(recursion_limit=100)` 조정 또는 tool 로직 확인 |
| `KeyError: 'next_agent'` | `_route_decision()`이 None 반환 | `state.get("next_agent", AgentRoute.FINISH)`로 기본값 설정 |
| Orchestrator에 agent 대화가 전부 쌓임 | `_coding_node()`가 전체 messages 반환 | `result["messages"][-1]`만 반환하는지 확인 (컨텍스트 격리) |

---

## 개념 연결 맵

이 실습에서 구현한 코드가 어떤 개념을 사용���는지 정리:

```
orchestrator.py에서 사용하는 개념
│
├─ LangChain (에이전트 안에서)
│   ├─ Chat Model ─────────── self.llm (TODO 2에서 사용)
│   ├─ 메시지 타입 ──────────── HumanMessage, AIMessage (TODO 2, 4)
│   ├─ with_structured_output ─ RouterDecision (사전 제공 코드 참고)
│   └─ 에이전트-노드 패턴 ───── invoke() + 최종 응답만 반환 (TODO 4)
│
└─ LangGraph (에이전트 사이에서)
    ├─ State + Reducer ──────── OrchestratorState (사전 제공 코드 참고)
    ├─ Node ─────────────────── add_node() (TODO 1)
    ├─ Edge (Normal) ────────── add_edge(START, "router") (TODO 1)
    ├─ Edge (Conditional) ───── add_conditional_edges() (TODO 1, 3)
    ├─ Checkpointer ─────────── compile(checkpointer=) (TODO 1)
    └─ Command ──────────────── astream_events (이미 구현됨)
```
