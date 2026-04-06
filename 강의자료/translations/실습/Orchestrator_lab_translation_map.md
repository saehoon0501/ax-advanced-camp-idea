# Orchestrator Configuration Lab
## Sentence-by-Sentence Translation Map
---
### Section: Title and Introduction
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Orchestrator 구성 실습 | Orchestrator Configuration Lab |
| 2 | 이 실습에서는 LangChain & LangGraph의 핵심 개념을 직접 코드로 구현합니다. | In this lab, you will implement the core concepts of LangChain & LangGraph directly in code. |
| 3 | **구현 파일:** `ax_advanced_class/src/orchestrator.py` | **Implementation file:** `ax_advanced_class/src/orchestrator.py` |

---
### Section: What We Will Build
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 4 | 우리가 만들 것 | What We Will Build |
| 5 | 사용자의 메시지를 받아 적절한 에이전트로 라우팅하는 오케스트레이터입니다: | An orchestrator that receives the user's message and routes it to the appropriate agent: |
| 6 | 사용자: "블로그 플랫폼 만들어줘" | User: "Build me a blog platform" |
| 7 | router 노드 (LLM이 판단: "이건 초기 설정이 필요하다") | router node (LLM decides: "This requires initial setup") |
| 8 | initializer 노드 (프로젝트 구조를 잡는 에이전트) | initializer node (agent that sets up the project structure) |
| 9 | 사용자: "로그인 기능 구현해줘" | User: "Implement the login feature" |
| 10 | router 노드 (LLM이 판단: "이건 코딩 작업이다") | router node (LLM decides: "This is a coding task") |
| 11 | coding 노드 (기능을 구현하는 에이전트) | coding node (agent that implements features) |

---
### Section: Lab Structure
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 12 | 실습 구조 | Lab Structure |
| 13 | 4개의 TODO를 순서대로 구현합니다. | You will implement 4 TODOs in order. |
| 14 | 구현할 것 | What to Implement |
| 15 | 대응하는 개념 | Corresponding Concept |
| 16 | StateGraph 조립 | StateGraph assembly |
| 17 | Structured Output + 메시지 생성 | Structured Output + message creation |
| 18 | Conditional Edge 분기 함수 | Conditional Edge branching function |
| 19 | 에이전트-노드 연결 패턴 | Agent-node connection pattern |

---
### Section: Pre-provided Code
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 20 | 사전 제공 코드 | Pre-provided Code |
| 21 | TODO 1-4를 구현하기 전에, 아래 두 클래스가 어떻게 정의되어 있는지 먼저 읽으세요. | Before implementing TODOs 1-4, first read how the two classes below are defined. |
| 22 | 이 코드는 이미 구현되어 있습니다. | This code is already implemented. |
| 23 | `operator.add`가 reducer 역할. 노드가 `{"messages": [msg]}`를 반환하면 기존 리스트 뒤에 추가됩니다 | `operator.add` serves as the reducer. When a node returns `{"messages": [msg]}`, it appends to the existing list. |
| 24 | `next_agent`에는 reducer가 없음 — 새 값이 오면 이전 값을 **덮어씁니다** | `next_agent` has no reducer -- when a new value arrives, it **overwrites** the previous value. |
| 25 | 모든 필드가 optional (초기값 없이 시작 가능) | All fields are optional (can start without initial values). |
| 26 | LLM이 반환할 수 있는 값을 3개로 제한합니다 | Restricts the values the LLM can return to three options. |
| 27 | LLM이 각 필드의 의미를 이해하는 데 사용. description이 없으면 LLM이 잘못된 값을 반환할 수 있습니다 | Used for the LLM to understand the meaning of each field. Without descriptions, the LLM may return incorrect values. |
| 28 | LLM 출력을 이 Pydantic 모델로 강제 파싱합니다 | Forces the LLM output to be parsed into this Pydantic model. |

---
### Section: TODO 1 - _build_workflow()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 29 | TODO 1: _build_workflow() 구현 | TODO 1: Implement _build_workflow() |
| 30 | 배울 개념: StateGraph 조립 | Concept to learn: StateGraph assembly |
| 31 | 그래프를 조립하는 전체 과정을 구현합니다. | Implement the entire process of assembling the graph. |
| 32 | 완성되면 이런 구조가 됩니다: | When complete, it will have this structure: |
| 33 | 구현할 코드: | Code to implement: |
| 34 | # TODO 1: StateGraph를 조립하세요 | # TODO 1: Assemble the StateGraph |
| 35 | # Step 1: StateGraph(OrchestratorState)로 그래프 생성 | # Step 1: Create a graph with StateGraph(OrchestratorState) |
| 36 | # Step 2: 노드 3개 추가 | # Step 2: Add 3 nodes |
| 37 | # 힌트: workflow.add_node("이름", 함수) | # Hint: workflow.add_node("name", function) |
| 38 | # Step 3: 엣지 연결 | # Step 3: Connect edges |
| 39 | # 분기 함수: self._route_decision | # Branching function: self._route_decision |
| 40 | # 힌트: add_edge(), add_conditional_edges() | # Hint: add_edge(), add_conditional_edges() |
| 41 | **확인:** `add_conditional_edges`의 세 번째 인자(매핑 dict)에서 `AgentRoute.FINISH`가 `END`로 매핑되는지 확인하세요. | **Verify:** Check that `AgentRoute.FINISH` maps to `END` in the third argument (mapping dict) of `add_conditional_edges`. |

---
### Section: TODO 2 - _router_node()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 42 | TODO 2: _router_node() 구현 | TODO 2: Implement _router_node() |
| 43 | 배울 개념: with_structured_output 사용 + 메시지 생성 | Concept to learn: Using with_structured_output + message creation |
| 44 | LLM에게 시스템 프롬프트와 대화 메시지를 보내서 라우팅 결정을 받고, 그 결과를 State에 반영합니다. | Send the system prompt and conversation messages to the LLM to get a routing decision, then reflect the result in the State. |
| 45 | # TODO 2: LLM으로 라우팅 결정을 내리세요 | # TODO 2: Make a routing decision using the LLM |
| 46 | # Step 1: state에서 messages 추출 | # Step 1: Extract messages from state |
| 47 | # Step 2: with_structured_output(RouterDecision)으로 LLM 감싸기 | # Step 2: Wrap the LLM with with_structured_output(RouterDecision) |
| 48 | # Step 3: LLM 호출 | # Step 3: Invoke the LLM |
| 49 | # 입력: [{"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT}, *messages] | # Input: [{"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT}, *messages] |
| 50 | # 결과: RouterDecision 객체 (decision.route, decision.reason, decision.response) | # Result: RouterDecision object (decision.route, decision.reason, decision.response) |
| 51 | # Step 4: decision.route를 AgentRoute enum으로 변환 | # Step 4: Convert decision.route to an AgentRoute enum |
| 52 | # Step 5: 반환값 구성 | # Step 5: Compose the return value |
| 53 | # 힌트: decision.response가 있으면 그걸 사용, 없으면 reason 사용 | # Hint: Use decision.response if available, otherwise use reason |
| 54 | **확인:** `with_structured_output`의 결과가 `RouterDecision` 객체인지, `decision.route`로 접근 가능한지 확인하세요. | **Verify:** Check that the result of `with_structured_output` is a `RouterDecision` object and that `decision.route` is accessible. |

---
### Section: TODO 3 - _route_decision()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 55 | TODO 3: _route_decision() 구현 | TODO 3: Implement _route_decision() |
| 56 | 배울 개념: Conditional Edge 분기 함수 | Concept to learn: Conditional Edge branching function |
| 57 | `add_conditional_edges`에 전달하는 분기 함수입니다. | This is the branching function passed to `add_conditional_edges`. |
| 58 | State에서 `next_agent` 값을 읽어서 반환하면, 그 값에 따라 다음 노드가 결정됩니다. | It reads the `next_agent` value from the State and returns it, which determines the next node. |
| 59 | # TODO 3: state에서 next_agent를 추출하여 반환하세요 | # TODO 3: Extract and return next_agent from state |
| 60 | # 힌트: state.get("next_agent", 기본값) | # Hint: state.get("next_agent", default_value) |
| 61 | # next_agent가 없으면 AgentRoute.FINISH를 기본값으로 | # If next_agent is missing, default to AgentRoute.FINISH |
| 62 | **확인:** 이 함수의 반환값이 TODO 1의 `add_conditional_edges` 매핑 dict의 **키**와 일치하는지 확인하세요. | **Verify:** Check that the return value of this function matches the **keys** in the `add_conditional_edges` mapping dict from TODO 1. |

---
### Section: TODO 4 - _coding_node()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 63 | TODO 4: _coding_node() 구현 | TODO 4: Implement _coding_node() |
| 64 | 배울 개념: 에이전트-노드 연결 패턴 (서브그래프) | Concept to learn: Agent-node connection pattern (subgraph) |
| 65 | `create_agent()`로 만든 에이전트를 노드 안에서 `invoke()`합니다. | Invoke the agent created with `create_agent()` using `invoke()` inside the node. |
| 66 | 핵심은 **오케스트레이터 State와 에이전트 State가 다르다**는 것입니다. | The key point is that **the orchestrator State and the agent State are different**. |
| 67 | # TODO 4: coding 에이전트를 실행하고 결과를 반환하세요 | # TODO 4: Run the coding agent and return the result |
| 68 | # Step 1: 오케스트레이터 state에서 messages 추출 | # Step 1: Extract messages from the orchestrator state |
| 69 | # Step 2: 에이전트 입력 구성 | # Step 2: Compose the agent input |
| 70 | # coding 에이전트는 messages 외에 todos도 필요합니다 | # The coding agent requires todos in addition to messages |
| 71 | # Step 3: self.coding_agent.invoke(agent_input) 실행 | # Step 3: Execute self.coding_agent.invoke(agent_input) |
| 72 | # Step 4: 에이전트의 최종 응답만 오케스트레이터로 반환 | # Step 4: Return only the agent's final response to the orchestrator |
| 73 | # 에이전트는 수십 턴의 대화를 할 수 있지만, 오케스트레이터에는 마지막 메시지만 돌려줍니다 | # The agent may have dozens of conversation turns, but only the last message is returned to the orchestrator |
| 74 | # 왜? → 에이전트의 전체 대화를 오케스트레이터에 넣으면 컨텍스트 윈도우가 오염됩니다 | # Why? Putting the agent's entire conversation into the orchestrator pollutes the context window |
| 75 | **확인:** `result["messages"][-1].content`로 마지막 메시지를 추출했는지 확인하세요. | **Verify:** Check that you extracted the last message with `result["messages"][-1].content`. |
| 76 | 전체 messages를 반환하면 컨텍스트 오염이 발생합니다. | Returning all messages causes context pollution. |
| 77 | **참고:** `_initializer_node()`도 같은 패턴입니다. 다만 `todos` 필드가 필요 없다는 차이만 있습니다. | **Note:** `_initializer_node()` follows the same pattern. The only difference is that the `todos` field is not needed. |

---
### Section: Verification
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 78 | 검증 방법 | Verification Method |
| 79 | 모든 TODO를 구현한 후: | After implementing all TODOs: |
| 80 | 프롬프트에서 다음을 테스트: | Test the following at the prompt: |
| 81 | `"블로그 플랫폼 만들어줘"` → initializer로 라우팅되는지 | `"Build me a blog platform"` -> Check if it routes to initializer |
| 82 | `"로그인 기능 구현해줘"` → coding으로 라우팅되는지 | `"Implement the login feature"` -> Check if it routes to coding |
| 83 | `"안녕하세요"` → finish로 라우팅되고 직접 응답하는지 | `"Hello"` -> Check if it routes to finish and responds directly |

---
### Section: Common Failures and Solutions
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 84 | 흔한 실패와 대처 | Common Failures and Solutions |
| 85 | LLM이 `Literal` 밖의 값 반환 | LLM returns a value outside the `Literal` options |
| 86 | `with_structured_output`이 자동 재시도함. `Field(description=...)`을 더 명확히 작성 | `with_structured_output` retries automatically. Write `Field(description=...)` more clearly |
| 87 | Router가 항상 같은 agent로 보냄 | Router always routes to the same agent |
| 88 | `ORCHESTRATOR_SYSTEM_PROMPT`가 모호 | `ORCHESTRATOR_SYSTEM_PROMPT` is ambiguous |
| 89 | 라우팅 조건을 더 구체적으로 (예: "feature_list.json이 없으면 initializer") | Make routing conditions more specific (e.g., "if feature_list.json doesn't exist, use initializer") |
| 90 | Agent가 응답 없이 멈춤 | Agent hangs without responding |
| 91 | `recursion_limit` 초과 (기본 25) | `recursion_limit` exceeded (default 25) |
| 92 | `create_agent(recursion_limit=100)` 조정 또는 tool 로직 확인 | Adjust `create_agent(recursion_limit=100)` or check tool logic |
| 93 | `_route_decision()`이 None 반환 | `_route_decision()` returns None |
| 94 | `state.get("next_agent", AgentRoute.FINISH)`로 기본값 설정 | Set a default with `state.get("next_agent", AgentRoute.FINISH)` |
| 95 | Orchestrator에 agent 대화가 전부 쌓임 | All agent conversations accumulate in the Orchestrator |
| 96 | `_coding_node()`가 전체 messages 반환 | `_coding_node()` returns all messages |
| 97 | `result["messages"][-1]`만 반환하는지 확인 (컨텍스트 격리) | Verify that only `result["messages"][-1]` is returned (context isolation) |

---
### Section: Concept Connection Map
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 98 | 개념 연결 맵 | Concept Connection Map |
| 99 | 이 실습에서 구현한 코드가 어떤 개념을 사용하는지 정리: | Summary of which concepts the code implemented in this lab uses: |
| 100 | 에이전트 안에서 | Within the agent |
| 101 | 메시지 타입 | Message types |
| 102 | 에이전트-노드 패턴 | Agent-node pattern |
| 103 | invoke() + 최종 응답만 반환 | invoke() + return only the final response |
| 104 | 에이전트 사이에서 | Between agents |
| 105 | 사전 제공 코드 참고 | Refer to the pre-provided code |
| 106 | 이미 구현됨 | Already implemented |
