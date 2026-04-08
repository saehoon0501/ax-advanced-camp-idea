# Orchestrator 구성 실습 - 정답 및 해설

**구현 파일:** `ax_advanced_class/src/orchestrator.py`

이 문서는 Orchestrator 실습의 4개 TODO에 대한 정답 코드와 상세 해설을 제공합니다.

---

## 사전 제공 코드 해설: OrchestratorState 정의

**개념:** State + Reducer

```python
class OrchestratorState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], operator.add]
    next_agent: Optional["AgentRoute"]
```

**해설:**

- **`total=False`**: TypedDict의 모든 필드를 optional로 만듭니다. 이렇게 하면 State를 초기화할 때 모든 필드를 채우지 않아도 됩니다. 예를 들어 `{"messages": [HumanMessage("hi")]}`만으로도 유효한 State가 됩니다.

- **`Annotated[list[BaseMessage], operator.add]`**: 이것이 LangGraph의 **Reducer** 패턴입니다.
  - 노드가 `{"messages": [AIMessage("응답")]}`을 반환하면, 기존 리스트를 **교체**하는 것이 아니라 기존 리스트 **뒤에 추가**합니다.
  - `operator.add`는 Python의 `+` 연산자로, 리스트끼리 합칩니다: `[기존] + [새로운] = [기존, 새로운]`
  - Reducer가 없으면 **덮어쓰기**가 기본 동작이므로, 이전 메시지가 사라집니다.

- **`next_agent: Optional["AgentRoute"]`**: Reducer가 없으므로 단순 덮어쓰기입니다.
  - Router 노드가 `{"next_agent": AgentRoute.CODING}`을 반환하면, 이전 값이 무엇이든 새 값으로 교체됩니다.
  - 이것이 의도된 동작입니다 -- 라우팅 결정은 항상 최신 값만 의미가 있습니다.

---

## 사전 제공 코드 해설: RouterDecision 정의

**개념:** with_structured_output + Pydantic

```python
class RouterDecision(BaseModel):
    route: Literal["initializer", "coding", "finish"] = Field(
        description="The agent to route to: 'initializer' for project setup, 'coding' for feature implementation, 'finish' for general questions or when done"
    )
    reason: str = Field(description="Brief explanation for the routing decision")
    response: Optional[str] = Field(
        default=None,
        description="Direct response for general/non-coding questions (only when route='finish' for general questions)",
    )
```

**해설:**

- **Pydantic `BaseModel`**: LLM의 출력을 Python 객체로 변환하기 위한 스키마입니다. `with_structured_output(RouterDecision)`으로 LLM을 감싸면, LLM이 자유 텍스트 대신 이 스키마에 맞는 JSON을 생성하고, 자동으로 Python 객체로 변환됩니다.

- **`Literal["initializer", "coding", "finish"]`**: LLM이 이 세 값 중 하나만 선택하도록 제약합니다.
  - `Literal`이 없으면 LLM이 `"init"`, `"code"` 같은 변형을 만들 수 있어 분기 로직이 깨집니다.
  - `with_structured_output`이 스키마 위반 시 자동으로 재시도하므로, 잘못된 값이 오는 경우는 거의 없습니다.

- **`Field(description=...)`**: LLM에게 각 필드의 의미를 알려줍니다.
  - description이 없으면 LLM이 필드명만 보고 추측하므로, 라우팅 정확도가 떨어집니다.
  - 특히 `route` 필드의 description에서 각 선택지의 의미를 명확히 설명하는 것이 중요합니다.

- **`response: Optional[str]`**: `route="finish"`일 때만 사용됩니다.
  - 일반 질문(예: "안녕하세요")에 대해 에이전트를 거치지 않고 직접 응답할 수 있습니다.
  - `default=None`이므로 `route="initializer"`나 `"coding"`일 때는 비어있어도 됩니다.

---

## TODO 1: _build_workflow() 구현

**개념:** StateGraph 조립

```python
def _build_workflow(self) -> CompiledStateGraph:
    workflow = StateGraph(OrchestratorState)

    # 노드 추가
    workflow.add_node("router", self._router_node)
    workflow.add_node("initializer", self._initializer_node)
    workflow.add_node("coding", self._coding_node)

    # 엣지 연결
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges(
        "router",
        self._route_decision,
        {
            AgentRoute.INITIALIZER: "initializer",
            AgentRoute.CODING: "coding",
            AgentRoute.FINISH: END,
        },
    )
    workflow.add_edge("initializer", END)
    workflow.add_edge("coding", END)

    return workflow.compile(checkpointer=self.checkpointer)
```

**해설:**

- **`StateGraph(OrchestratorState)`**: TODO 1에서 정의한 State 타입으로 그래프를 생성합니다. 이 시점에서 LangGraph는 State의 Reducer 정보를 파악합니다.

- **`add_node("이름", 함수)`**: 그래프에 노드를 등록합니다.
  - 노드 함수는 State를 받아서 State 업데이트 dict를 반환합니다.
  - 문자열 이름("router", "initializer", "coding")은 엣지 연결에 사용됩니다.

- **`add_edge(START, "router")`**: Normal Edge입니다. 그래프 실행이 시작되면 항상 "router" 노드부터 실행합니다.

- **`add_conditional_edges("router", self._route_decision, {...})`**: Conditional Edge입니다.
  - "router" 노드 실행 후 `self._route_decision(state)`를 호출합니다.
  - 반환값이 `AgentRoute.INITIALIZER`면 "initializer" 노드로, `AgentRoute.CODING`이면 "coding" 노드로, `AgentRoute.FINISH`면 `END`로 이동합니다.
  - 세 번째 인자(매핑 dict)가 분기 함수의 반환값을 실제 노드 이름으로 변환합니다.

- **`add_edge("initializer", END)` / `add_edge("coding", END)`**: 에이전트 실행이 끝나면 그래프가 종료됩니다.

- **`compile(checkpointer=self.checkpointer)`**: 그래프를 실행 가능한 형태로 컴파일합니다. `checkpointer`를 전달하면 State가 자동으로 저장/복원됩니다.

**전체 흐름:**
```
START -> router -> (조건에 따라) -> initializer -> END
                                 -> coding      -> END
                                 -> END (직접 종료)
```

---

## TODO 2: _router_node() 구현

**개념:** Structured Output + 메시지 생성

```python
def _router_node(self, state: OrchestratorState) -> dict:
    messages = state.get("messages", [])

    structured_llm = self.llm.with_structured_output(RouterDecision)
    decision: RouterDecision = structured_llm.invoke(
        [
            {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
            *messages,
        ]
    )

    route_map = {
        "initializer": AgentRoute.INITIALIZER,
        "coding": AgentRoute.CODING,
        "finish": AgentRoute.FINISH,
    }

    route = route_map.get(decision.route, AgentRoute.FINISH)

    if decision.response:
        message_content = decision.response
    else:
        message_content = f"Routing to {decision.route}: {decision.reason}"

    return {
        "next_agent": route,
        "messages": [AIMessage(content=message_content)],
    }
```

**해설:**

- **`self.llm.with_structured_output(RouterDecision)`**: LLM을 감싸서 RouterDecision 객체를 반환하도록 합니다.
  - 내부적으로 LLM에게 JSON 스키마를 전달하고, 응답을 파싱합니다.
  - 파싱 실패 시 자동 재시도합니다.

- **`structured_llm.invoke([system_message, *messages])`**: 시스템 프롬프트 + 대화 기록을 LLM에 전달합니다.
  - `*messages`로 스프레드하여 기존 대화 메시지를 모두 포함합니다.
  - 반환값은 RouterDecision 객체이므로 `decision.route`, `decision.reason`, `decision.response`로 접근합니다.

- **`route_map`**: 문자열("initializer")을 enum(`AgentRoute.INITIALIZER`)으로 변환합니다.
  - `decision.route`는 Literal 타입이므로 세 값 중 하나이지만, 안전하게 `route_map.get()`에 기본값 `AgentRoute.FINISH`를 설정합니다.

- **응답 메시지 구성**: `decision.response`가 있으면(일반 질문에 대한 직접 응답) 그것을 사용하고, 없으면 라우팅 이유를 메시지로 포함합니다.

- **반환값**: `{"next_agent": route, "messages": [AIMessage(...)]}`
  - `next_agent`는 Reducer가 없으므로 덮어쓰기됩니다 (OrchestratorState 참조).
  - `messages`는 `operator.add` Reducer에 의해 기존 리스트에 추가됩니다.

---

## TODO 3: _route_decision() 구현

**개념:** Conditional Edge 분기 함수

```python
def _route_decision(self, state: OrchestratorState) -> AgentRoute:
    return state.get("next_agent", AgentRoute.FINISH)
```

**해설:**

- 이 함수는 TODO 1의 `add_conditional_edges`에서 분기 함수로 사용됩니다.

- **역할**: State에서 `next_agent` 값을 꺼내서 반환합니다. 이 반환값이 매핑 dict의 키와 매칭되어 다음 노드가 결정됩니다.

- **`state.get("next_agent", AgentRoute.FINISH)`**: `next_agent`가 없으면 기본으로 `FINISH`(종료)를 반환합니다.
  - 예외 상황(router가 `next_agent`를 설정하지 않은 경우)에도 안전하게 동작합니다.

- **왜 별도 함수인가?**: `add_conditional_edges`는 `(state) -> str/Enum` 형태의 함수를 요구합니다. Router 노드 자체에서 분기를 결정하지 않고, State에 값을 저장한 뒤 별도 함수에서 읽는 패턴을 사용하면 로직이 분리되어 테스트와 디버깅이 쉬워집니다.

---

## TODO 4: _coding_node() 구현

**개념:** 에이전트-노드 연결 패턴 + Context 격리

```python
def _coding_node(self, state: OrchestratorState) -> dict:
    result = self.coding_agent.invoke(
        {
            "messages": state.get("messages", []),
            "todos": [],
        }
    )
    return {"messages": [AIMessage(content=result["messages"][-1].content)]}
```

**해설:**

- **에이전트 입력 구성**: Coding Agent는 `messages`와 `todos` 두 필드를 필요로 합니다.
  - `messages`: Orchestrator State에서 가져온 대화 기록
  - `todos`: 빈 리스트로 초기화 (에이전트가 내부적으로 관리)

- **`result["messages"][-1].content`**: 에이전트 실행 결과에서 **마지막 메시지만** 추출합니다.
  - 이것이 **Context 격리**의 핵심입니다.
  - Coding Agent는 내부적으로 수십 턴의 대화(tool 호출, 디버깅 등)를 수행할 수 있습니다.
  - 이 모든 내부 대화를 Orchestrator에 돌려보내면, Orchestrator의 컨텍스트 윈도우가 오염됩니다.
  - 최종 요약만 반환하면 8,000 토큰의 에이전트 내부 대화가 200 토큰의 요약으로 압축됩니다.

- **참고 -- `_initializer_node()`도 동일한 패턴입니다:**

```python
def _initializer_node(self, state: OrchestratorState) -> dict:
    result = self.initializer_agent.invoke(
        {"messages": state.get("messages", [])}
    )
    return {"messages": [AIMessage(content=result["messages"][-1].content)]}
```

차이점은 `todos` 필드가 없다는 것뿐입니다. Initializer Agent는 todo 관리가 필요하지 않기 때문입니다.

---

## 전체 흐름 요약

```
1. 사용자 메시지 -> invoke(messages=[HumanMessage("블로그 만들어줘")])
2. START -> router 노드
   - LLM이 RouterDecision 생성: route="initializer", reason="프로젝트 설정 필요"
   - State에 next_agent=AgentRoute.INITIALIZER 저장
3. _route_decision()이 AgentRoute.INITIALIZER 반환
4. initializer 노드 실행
   - Initializer Agent가 프로젝트 구조를 잡고 최종 요약 반환
   - Orchestrator는 최종 요약만 messages에 추가
5. END
```

이 패턴의 핵심은 **Orchestrator는 라우팅만 하고, 모든 복잡한 로직은 전문 에이전트에 위임**한다는 것입니다. 그리고 에이전트의 내부 대화는 Orchestrator 컨텍스트에 노출되지 않습니다.
