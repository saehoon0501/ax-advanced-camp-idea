# Dynamic Prompt Lab
## Sentence-by-Sentence Translation Map
---
### Section: Title and Problem Statement
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Dynamic Prompt 실습 | Dynamic Prompt Lab |
| 2 | Agent가 매번 같은 시스템 프롬프트로 LLM을 호출합니다. | The Agent calls the LLM with the same system prompt every time. |
| 3 | 하지만 실제로는 "지금 workspace가 어디인지", "현재 todo 상태가 뭔지"를 매 호출마다 알려줘야 agent가 맥락을 잃지 않습니다. | However, in practice, the agent needs to be told "where the current workspace is" and "what the current todo status is" on every call so it doesn't lose context. |
| 4 | 이 실습에서는 프롬프트 구성 전략을 적용하여, 정적 프롬프트에 런타임 상태를 동적으로 주입하는 미들웨어를 구현합니다. | In this lab, you will apply a prompt composition strategy to implement middleware that dynamically injects runtime state into a static prompt. |
| 5 | **구현 파일:** `ax_advanced_class/src/prompts/coding_agent_prompt.py` | **Implementation file:** `ax_advanced_class/src/prompts/coding_agent_prompt.py` |

---
### Section: Concept-to-Lab Connection
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 6 | 배운 개념과 실습의 연결 | Connection Between Learned Concepts and This Lab |
| 7 | Section 2 개념 | Section 2 Concept |
| 8 | 이 실습에서 적용하는 방법 | How It Is Applied in This Lab |
| 9 | 역할 부여 → Expert 활성화 | Role assignment -> Expert activation |
| 10 | 정적 프롬프트에서 "You are a Coding Agent" 역할을 명확히 정의 | Clearly define the "You are a Coding Agent" role in the static prompt |
| 11 | 일관된 도메인 언어 사용 | Consistent domain language usage |
| 12 | 코딩 컨텍스트를 유지하는 프롬프트 구성 | Prompt composition that maintains the coding context |
| 13 | Prompt Caching 전략 | Prompt Caching strategy |
| 14 | 정적 부분을 앞에, 동적 부분을 뒤에 배치하여 캐시 적중률 최대화 | Place the static part first and the dynamic part last to maximize cache hit rate |
| 15 | 혼합 요청 주의 | Caution with mixed requests |
| 16 | 역할(정적) + 현재 상태(동적)를 분리하여 Expert 혼란 방지 | Separate role (static) and current state (dynamic) to prevent Expert confusion |

---
### Section: What We Will Build
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 17 | 우리가 만들 것 | What We Will Build |
| 18 | Agent 역할과 규칙 (변하지 않음) | Agent role and rules (unchanging) |
| 19 | 매 LLM 호출마다 현재 상태 추가 | Add current state on every LLM call |
| 20 | 합쳐져서 | Combined into |
| 21 | 최종 프롬프트 = 정적 + 소프트 규칙 + 동적 컨텍스트 | Final prompt = static + soft rules + dynamic context |
| 22 | Prompt Caching이 왜 중요한가: | Why Prompt Caching matters: |
| 23 | 정적 부분 (캐시됨, 비용 절감) | Static part (cached, cost savings) |
| 24 | 동적 부분 (매번 변경) | Dynamic part (changes every time) |
| 25 | 정적 부분이 **앞에** 있으면, LLM provider(Anthropic 등)가 이 접두사를 캐시하여 비용과 지연시간을 줄입니다. | If the static part is **in front**, the LLM provider (Anthropic, etc.) caches this prefix to reduce cost and latency. |
| 26 | 동적 부분이 앞에 오면 매번 전체가 새로 처리됩니다. | If the dynamic part comes first, the entire prompt is reprocessed every time. |

---
### Section: Background - @dynamic_prompt Decorator
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 27 | 사전 지식: @dynamic_prompt 데코레이터 | Background: The @dynamic_prompt Decorator |
| 28 | LangChain의 `@dynamic_prompt`는 `wrap_model_call`의 간편 버전입니다: | LangChain's `@dynamic_prompt` is a convenience version of `wrap_model_call`: |
| 29 | 반환하는 문자열이 system prompt 전체를 교체합니다 | The returned string replaces the entire system prompt |
| 30 | 내부적으로는 이렇게 동작합니다: | Internally, it works like this: |
| 31 | 개발자가 작성한 함수 호출 | Calls the developer-written function |
| 32 | `request` 객체에서 접근할 수 있는 것: | What you can access from the `request` object: |
| 33 | `request.state` — 현재 agent state (`messages`, `todos` 등) | `request.state` -- the current agent state (`messages`, `todos`, etc.) |
| 34 | `request.system_message` — 현재 system prompt | `request.system_message` -- the current system prompt |

---
### Section: Lab Structure
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 35 | 실습 구조 | Lab Structure |
| 36 | 2개의 TODO를 순서대로 구현합니다. | You will implement 2 TODOs in order. |
| 37 | `CODING_AGENT_SYSTEM_PROMPT`(정적 프롬프트)는 이미 제공되어 있으므로, 동적 컨텍스트 구성과 프롬프트 합성에 집중합니다. | `CODING_AGENT_SYSTEM_PROMPT` (the static prompt) is already provided, so focus on dynamic context composition and prompt synthesis. |
| 38 | 동적 컨텍스트 구성 | Dynamic context composition |
| 39 | 런타임 상태 주입 | Runtime state injection |
| 40 | 프롬프트 합성 순서 | Prompt synthesis order |
| 41 | Prompt Caching 전략 (정적 → 동적) | Prompt Caching strategy (static -> dynamic) |

---
### Section: TODO 1 - Dynamic Context Composition
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 42 | TODO 1: 동적 컨텍스트 구성 | TODO 1: Dynamic Context Composition |
| 43 | 배울 개념: 런타임 상태 주입, Information Density | Concept to learn: Runtime state injection, Information Density |
| 44 | Agent가 매 LLM 호출마다 알아야 하는 **현재 상태**를 구성합니다. | Compose the **current state** that the Agent needs to know on every LLM call. |
| 45 | `request.state`에서 정보를 추출합니다. | Extract information from `request.state`. |
| 46 | # TODO 1: 동적 컨텍스트를 구성하세요 | # TODO 1: Compose the dynamic context |
| 47 | # 포함해야 할 정보: | # Information to include: |
| 48 | # 1. Workspace 경로 | # 1. Workspace path |
| 49 | # Agent가 파일 작업할 때 기준이 되는 디렉토리 | # The directory that serves as the base for the Agent's file operations |
| 50 | # 힌트: workspace 변수 사용 | # Hint: use the workspace variable |
| 51 | # 2. 현재 todos 상태 | # 2. Current todos status |
| 52 | # Agent가 진행 중인 작업 목록을 확인할 수 있어야 함 | # The Agent must be able to check the list of in-progress tasks |
| 53 | # 힌트: state.get("todos", []) | # Hint: state.get("todos", []) |
| 54 | # 3. write_todos 사용 가이드 | # 3. write_todos usage guide |
| 55 | # Agent에게 todo를 어떻게 관리해야 하는지 지시 | # Instruct the Agent on how to manage todos |
| 56 | # 작업 시작 전 todo 생성 | # Create a todo before starting work |
| 57 | # in_progress는 1개만 | # Only 1 in_progress at a time |
| 58 | # 완료 즉시 상태 업데이트 | # Update status immediately upon completion |
| 59 | **확인:** `state.get("todos", [])`로 현재 todo 상태를 포함했는지 확인하세요. | **Verify:** Check that the current todo status is included using `state.get("todos", [])`. |
| 60 | 이 정보가 없으면 Agent가 이전에 만든 todo를 모르는 상태로 작업합니다. | Without this information, the Agent works without knowing the todos it previously created. |

---
### Section: TODO 2 - Prompt Synthesis Order
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 61 | TODO 2: 프롬프트 합성 순서 | TODO 2: Prompt Synthesis Order |
| 62 | 배울 개념: Prompt Caching 전략 — 정적 접두사를 캐시하여 비용/지연 최적화 | Concept to learn: Prompt Caching strategy -- cache the static prefix to optimize cost/latency |
| 63 | `@dynamic_prompt`는 반환하는 문자열이 system prompt 전체를 교체합니다. | `@dynamic_prompt` replaces the entire system prompt with the returned string. |
| 64 | 따라서 정적 부분 + 소프트 규칙 + 동적 부분을 올바른 순서로 합쳐야 합니다. | Therefore, the static part + soft rules + dynamic part must be combined in the correct order. |
| 65 | # TODO 2: 세 부분을 올바른 순서로 합치세요 | # TODO 2: Combine the three parts in the correct order |
| 66 | # 사용 가능한 변수: | # Available variables: |
| 67 | # CODING_AGENT_SYSTEM_PROMPT — 정적 시스템 프롬프트 (이미 제공됨) | # CODING_AGENT_SYSTEM_PROMPT -- static system prompt (already provided) |
| 68 | # SOFT_RULES_PROMPT — git 안전, 코드 품질 등 소프트 규칙 | # SOFT_RULES_PROMPT -- soft rules for git safety, code quality, etc. |
| 69 | # dynamic_content — TODO 1에서 구성한 런타임 컨텍스트 | # dynamic_content -- runtime context composed in TODO 1 |
| 70 | # 순서가 왜 중요한가? | # Why does the order matter? |
| 71 | # LLM provider는 시스템 프롬프트의 "접두사(prefix)"를 캐시합니다. | # The LLM provider caches the "prefix" of the system prompt. |
| 72 | # 변하지 않는 부분을 앞에 놓으면 → 캐시 적중 → 비용/지연 절감 | # Putting the unchanging part first -> cache hit -> cost/latency savings |
| 73 | # 변하는 부분을 앞에 놓으면 → 매번 전체 재처리 → 비용/지연 증가 | # Putting the changing part first -> full reprocessing every time -> cost/latency increase |
| 74 | # 올바른 순서: | # Correct order: |
| 75 | # 1. ??? ← 절대 안 변하는 것 (Agent 역할, 규칙) | # 1. ??? <- What never changes (Agent role, rules) |
| 76 | # 2. ??? ← 거의 안 변하는 것 (소프트 규칙) | # 2. ??? <- What rarely changes (soft rules) |
| 77 | # 3. ??? ← 매번 변하는 것 (현재 workspace, todos) | # 3. ??? <- What changes every time (current workspace, todos) |
| 78 | **확인:** 반환값이 `CODING_AGENT_SYSTEM_PROMPT + SOFT_RULES_PROMPT + dynamic_content` 순서인지 확인하세요. | **Verify:** Check that the return value follows the order `CODING_AGENT_SYSTEM_PROMPT + SOFT_RULES_PROMPT + dynamic_content`. |
| 79 | 순서를 바꾸면 캐싱이 깨집니다. | Changing the order breaks caching. |

---
### Section: Connecting Middleware to the Agent
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 80 | Agent에 미들웨어 연결하기 | Connecting Middleware to the Agent |
| 81 | 구현이 끝나면, `agent_specs.py`에서 미들웨어 스택에 `coding_agent_dynamic_prompt`가 이미 등록되어 있는지 확인합니다: | After implementation, verify that `coding_agent_dynamic_prompt` is already registered in the middleware stack in `agent_specs.py`: |
| 82 | **왜 맨 마지막인가?** | **Why is it last?** |
| 83 | `@dynamic_prompt`는 내부적으로 `wrap_model_call`입니다. | `@dynamic_prompt` is internally a `wrap_model_call`. |
| 84 | 미들웨어 리스트의 마지막 = 가장 안쪽 = system prompt의 최종 형태를 결정합니다. | Last in the middleware list = innermost = determines the final form of the system prompt. |
| 85 | 다른 미들웨어(Filesystem, TodoList)가 먼저 prompt를 수정하고, `dynamic_prompt`가 이를 포함한 최종 버전을 조립합니다. | Other middleware (Filesystem, TodoList) modify the prompt first, then `dynamic_prompt` assembles the final version including those modifications. |

---
### Section: Verification
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 86 | 검증 방법 | Verification Method |
| 87 | 전체 동작 테스트: | Full integration test: |
| 88 | 프롬프트에서 `"블로그 플랫폼 만들어줘"` 입력 → coding 에이전트가 PHASE 1(Recovery)부터 시작하는지 확인 | Enter `"Build me a blog platform"` at the prompt -> verify the coding agent starts from PHASE 1 (Recovery) |

---
### Section: Common Failures and Solutions
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 89 | 흔한 실패와 대처 | Common Failures and Solutions |
| 90 | Agent가 Phase 순서를 무시함 | Agent ignores the Phase order |
| 91 | 프롬프트가 "권장"으로 작성됨 | The prompt is written as a "recommendation" |
| 92 | "MUST", "ALWAYS", "NEVER"로 강제 어투 사용 (예: "You MUST run pwd first") | Use mandatory language with "MUST", "ALWAYS", "NEVER" (e.g., "You MUST run pwd first") |
| 93 | Prompt Caching이 작동 안 함 | Prompt Caching is not working |
| 94 | 동적 내용이 정적 부분 앞에 위치 | Dynamic content is placed before the static part |
| 95 | TODO 2의 합성 순서 확인: `STATIC + SOFT_RULES + dynamic` 순서 유지 | Check the synthesis order from TODO 2: maintain the `STATIC + SOFT_RULES + dynamic` order |
| 96 | Dynamic context에 todos가 비어있음 | Todos are empty in the dynamic context |
| 97 | Agent가 아직 `write_todos`를 호출 안 함 | The Agent hasn't called `write_todos` yet |
| 98 | 초기 상태에서 todos가 빈 리스트인 건 정상 — "No active todos" 표시 | An empty todo list in the initial state is normal -- display "No active todos" |
| 99 | Agent가 PHASE 3를 건너뜀 | Agent skips PHASE 3 |
| 100 | 프롬프트에 종료 조건이 불명확 | The exit conditions in the prompt are unclear |
| 101 | "PHASE 3 is NOT optional. You MUST complete all steps before ending." 명시 | Specify "PHASE 3 is NOT optional. You MUST complete all steps before ending." |

---
### Section: Concept Connection Map
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 102 | 배운 개념 → 이 실습에서 구현한 것 | Learned concepts -> What was implemented in this lab |
| 103 | 런타임 상태 주입 | Runtime state injection |
| 104 | "매 호출마다 변하는 정보" | "Information that changes on every call" |
| 105 | workspace, todos, 사용 가이드 | workspace, todos, usage guide |
| 106 | Prompt Caching 전략 | Prompt Caching strategy |
| 107 | "고정을 앞에, 동적을 뒤에" | "Fixed in front, dynamic at the back" |
| 108 | 정적/동적 분리 | Static/dynamic separation |
| 109 | "Expert 선택 혼란 방지" | "Prevent Expert selection confusion" |
| 110 | 역할(정적) ≠ 상태(동적) | Role (static) != State (dynamic) |
