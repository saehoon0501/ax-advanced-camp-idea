# Agent Harness Lab
## Sentence-by-Sentence Translation Map
---
### Section: Title and Introduction
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Agent Harness 실습 | Agent Harness Lab |
| 2 | Dynamic Prompt 실습에서 Coding Agent의 정적 프롬프트(`CODING_AGENT_SYSTEM_PROMPT`)와 동적 컨텍스트 주입을 구현했습니다. | In the Dynamic Prompt lab, you implemented the Coding Agent's static prompt (`CODING_AGENT_SYSTEM_PROMPT`) and dynamic context injection. |
| 3 | 하지만 프롬프트만으로는 agent의 행동을 충분히 제어할 수 없습니다 — agent가 "작업 목록을 관리하라"는 지시를 받아도, **관리할 도구가 없으면** 아무것도 할 수 없습니다. | However, prompts alone cannot sufficiently control the agent's behavior -- even if the agent is told to "manage a task list," it **can't do anything without the tools** to manage it. |
| 4 | 이 실습에서는 **Harness 패턴**을 두 가지 방향으로 구현합니다: | In this lab, you will implement the **Harness pattern** in two directions: |
| 5 | **TodoListMiddleware** — agent에게 작업 추적 도구를 제공하는 middleware (State + Tool + Prompt 패키지) | **TodoListMiddleware** -- middleware that provides the agent with task tracking tools (State + Tool + Prompt package) |
| 6 | **Harness Prompting** — Dynamic Prompt 실습의 CODING_AGENT_SYSTEM_PROMPT를 Harness behavior로 보강 | **Harness Prompting** -- augmenting the Dynamic Prompt lab's CODING_AGENT_SYSTEM_PROMPT with Harness behavior |
| 7 | **구현 파일:** | **Implementation files:** |
| 8 | `ax_advanced_class/src/middleware/todo_middleware.py` (신규 생성) | `ax_advanced_class/src/middleware/todo_middleware.py` (newly created) |
| 9 | `ax_advanced_class/src/prompts/coding_agent_prompt.py` (Dynamic Prompt 실습에서 이어서) | `ax_advanced_class/src/prompts/coding_agent_prompt.py` (continued from the Dynamic Prompt lab) |

---
### Section: Concept-to-Lab Connection
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 10 | 배운 개념과 실습의 연결 | Connection Between Learned Concepts and This Lab |
| 11 | Agent Harness 개념 | Agent Harness Concept |
| 12 | 이 실습에서 적용하는 방법 | How It Is Applied in This Lab |
| 13 | 암묵적 기억 → 명시적 상태 | Implicit memory -> explicit state |
| 14 | Todo를 agent state에 명시적으로 저장 (메시지 히스토리에 의존하지 않음) | Store todos explicitly in agent state (not relying on message history) |
| 15 | 컨텍스트 해석 프로토콜 | Context interpretation protocol |
| 16 | PHASE 1에서 pwd → init.sh → progress.md → feature_list.json 순서 강제 | Force the order pwd -> init.sh -> progress.md -> feature_list.json in PHASE 1 |
| 17 | 작업 단위 격리 | Work unit isolation |
| 18 | PHASE 2에서 하나의 feature만 선택, todo로 세부 단계 추적 | Select only one feature in PHASE 2, track detailed steps with todos |
| 19 | Git 안전망 + E2E 테스트 강제 | Git safety net + forced E2E testing |
| 20 | PHASE 3에서 progress.md 업데이트 → feature_list.json 업데이트 → git commit 순서 강제 | Force the order progress.md update -> feature_list.json update -> git commit in PHASE 3 |
| 21 | Compound Reliability | Compound Reliability |
| 22 | todo를 통해 작업 단위를 작게 유지하여 step당 성공률 유지 | Keep work units small through todos to maintain success rate per step |

---
### Section: Lab Position
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 23 | 이 실습의 위치 | Position of This Lab |
| 24 | Dynamic Prompt 실습 (이전) | Dynamic Prompt lab (previous) |
| 25 | Agent Harness 실습 (이번) ← 여기 | Agent Harness lab (current) <- here |
| 26 | Part 1: TodoListMiddleware 구현 — agent에게 작업 추적 "도구" 제공 | Part 1: TodoListMiddleware implementation -- provide the agent with task tracking "tools" |
| 27 | Part 2: Harness Prompting — Phase 1/2/3의 구체적 행동 규칙 작성 | Part 2: Harness Prompting -- write specific behavior rules for Phase 1/2/3 |

---
### Section: Part 1 - What We Will Build
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 28 | Part 1: TodoListMiddleware 구현 | Part 1: TodoListMiddleware Implementation |
| 29 | 우리가 만들 것 | What We Will Build |
| 30 | Middleware의 3가지 축을 **하나의 middleware에 모두 적용**합니다: | Apply all **3 axes of Middleware in a single middleware**: |
| 31 | State: todos 필드를 agent state에 추가 | State: Add a todos field to the agent state |
| 32 | Tool: write_todos 도구를 agent에 등록 | Tool: Register the write_todos tool with the agent |
| 33 | Prompt: "write_todos를 이렇게 써라"를 system prompt에 주입 | Prompt: Inject "use write_todos like this" into the system prompt |
| 34 | middleware를 `agent_specs.py`에 추가하면, agent가 자동으로: | When middleware is added to `agent_specs.py`, the agent automatically: |
| 35 | `todos` state 필드를 갖게 되고 | Gets a `todos` state field |
| 36 | `write_todos` tool을 사용할 수 있게 되고 | Can use the `write_todos` tool |
| 37 | system prompt에 사용법이 주입됩니다 | Gets usage instructions injected into the system prompt |

---
### Section: Part 1 - Lab Structure
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 38 | 실습 구조 | Lab Structure |
| 39 | 3개의 TODO를 순서대로 구현합니다. | You will implement 3 TODOs in order. |
| 40 | `write_todos` tool 함수 | `write_todos` tool function |
| 41 | **Tool** 주입 — 도구의 동작 | **Tool** injection -- the tool's behavior |
| 42 | 3가지 축 조립 | 3-axis assembly |
| 43 | **Prompt** 주입 | **Prompt** injection |

---
### Section: Pre-provided Code
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 44 | 사전 제공 코드 | Pre-provided Code |
| 45 | TODO 1-3을 구현하기 전에, 아래 코드를 먼저 읽으세요. | Before implementing TODOs 1-3, first read the code below. |
| 46 | 이 코드는 이미 구현되어 있습니다. | This code is already implemented. |
| 47 | `Todo`는 `TypedDict` — content(내용)과 status(상태) 두 필드 | `Todo` is a `TypedDict` -- two fields: content and status |
| 48 | 3가지 상태만 허용 | Only 3 states are allowed |
| 49 | `PlanningState`가 `AgentState`를 상속 — `create_agent`가 기존 `messages` 필드와 자동 머지 | `PlanningState` inherits from `AgentState` -- `create_agent` automatically merges it with the existing `messages` field |
| 50 | 초기값 없이 시작 가능 (첫 `write_todos` 호출 전까지 비어있음) | Can start without initial values (empty until the first `write_todos` call) |
| 51 | `invoke()` 시 입력에서 제외 (내부 관리 필드) | Excluded from input during `invoke()` (internally managed field) |
| 52 | **"EXACTLY ONE at a time!"** — 이 규칙이 없으면 agent가 여러 작업을 동시에 `in_progress`로 표시 | **"EXACTLY ONE at a time!"** -- without this rule, the agent marks multiple tasks as `in_progress` simultaneously |
| 53 | **"replaces the existing list entirely"** — append가 아니라 전체 교체 방식임을 명시 | **"replaces the existing list entirely"** -- specifies that it's a full replacement, not an append |
| 54 | **When to Use / When NOT to use** — 사용 조건과 미사용 조건 모두 명시해야 LLM이 정확히 판단 | **When to Use / When NOT to use** -- both usage and non-usage conditions must be specified for the LLM to judge accurately |

---
### Section: TODO 1 - write_todos Function
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 55 | TODO 1: Tool 동작 — `write_todos` 함수 | TODO 1: Tool Behavior -- `write_todos` function |
| 56 | 배울 개념: Tool이 `Command`를 반환하여 agent state를 업데이트 | Concept to learn: Tool returns a `Command` to update agent state |
| 57 | `write_todos` tool은 호출되면 전체 todo 리스트를 교체합니다. | The `write_todos` tool replaces the entire todo list when called. |
| 58 | 핵심은 **`Command(update=...)`를 반환**하여 agent state의 `todos` 필드를 업데이트하는 것입니다. | The key is **returning `Command(update=...)`** to update the `todos` field in the agent state. |
| 59 | # TODO 1: todo 리스트를 state에 업데이트하는 Command를 반환하세요 | # TODO 1: Return a Command that updates the todo list in state |
| 60 | # Command(update={...})를 사용하여: | # Using Command(update={...}): |
| 61 | # 1. "todos" 키에 새 todo 리스트를 설정 | # 1. Set the new todo list on the "todos" key |
| 62 | # 2. "messages" 키에 ToolMessage를 추가 (LLM이 결과를 볼 수 있도록) | # 2. Add a ToolMessage to the "messages" key (so the LLM can see the result) |
| 63 | # 왜 Command인가? | # Why Command? |
| 64 | # 일반 tool은 문자열을 반환하지만, state를 수정해야 하는 tool은 Command를 반환해야 LangGraph의 state reducer를 통해 업데이트됩니다. | # Normal tools return a string, but tools that need to modify state must return a Command so the update goes through LangGraph's state reducer. |
| 65 | **확인:** `Command(update={"todos": todos, "messages": [ToolMessage(...)]})`를 반환하는지 확인하세요. | **Verify:** Check that `Command(update={"todos": todos, "messages": [ToolMessage(...)]})` is returned. |
| 66 | `messages`를 포함하지 않으면 LLM이 tool 결과를 볼 수 없습니다. | Without including `messages`, the LLM cannot see the tool result. |

---
### Section: TODO 2 - __init__ Assembly
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 67 | TODO 2: 3가지 축 조립 — `__init__` | TODO 2: 3-Axis Assembly -- `__init__` |
| 68 | 배울 개념: Middleware가 State + Tool + Prompt를 하나의 패키지로 제공 | Concept to learn: Middleware provides State + Tool + Prompt as a single package |
| 69 | `__init__`에서 `state_schema`, `self.tools`, prompt 설정을 모두 조립합니다. | Assemble `state_schema`, `self.tools`, and prompt configuration all in `__init__`. |
| 70 | # TODO 2: middleware를 초기화하세요 | # TODO 2: Initialize the middleware |
| 71 | # Step 1: super().__init__() 호출 | # Step 1: Call super().__init__() |
| 72 | # Step 2: system_prompt와 tool_description을 인스턴스 변수로 저장 | # Step 2: Save system_prompt and tool_description as instance variables |
| 73 | # Step 3: self.tools에 write_todos tool 등록 ← Tool 축 | # Step 3: Register write_todos tool in self.tools <- Tool axis |
| 74 | **확인:** `self.tools = [...]`에 tool이 등록되었는지 확인하세요. | **Verify:** Check that a tool is registered in `self.tools = [...]`. |
| 75 | 이 리스트가 비어있으면 agent가 write_todos를 사용할 수 없습니다. | If this list is empty, the agent cannot use write_todos. |

---
### Section: TODO 3 - wrap_model_call Prompt Injection
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 76 | TODO 3: Prompt 주입 — `wrap_model_call` | TODO 3: Prompt Injection -- `wrap_model_call` |
| 77 | 배울 개념: `wrap_model_call`에서 `request.override(system_message=...)`로 매 LLM 호출마다 prompt 주입 | Concept to learn: Inject prompt on every LLM call using `request.override(system_message=...)` in `wrap_model_call` |
| 78 | agent가 LLM을 호출할 때마다, 기존 system prompt 뒤에 "write_todos 사용법"을 추가합니다. | Every time the agent calls the LLM, append "how to use write_todos" after the existing system prompt. |
| 79 | # TODO 3: system prompt에 todo 사용법을 추가하세요 | # TODO 3: Add todo usage instructions to the system prompt |
| 80 | # Step 1: 기존 system message가 있는지 확인 | # Step 1: Check if an existing system message exists |
| 81 | # Step 2: 기존 content blocks에 self.system_prompt 추가 | # Step 2: Add self.system_prompt to the existing content blocks |
| 82 | # Step 3: SystemMessage로 감싸기 | # Step 3: Wrap in a SystemMessage |
| 83 | # Step 4: request.override(system_message=new_system_message)로 수정된 request를 handler에 전달 | # Step 4: Pass the modified request to the handler with request.override(system_message=new_system_message) |
| 84 | **확인:** `request.override(system_message=...)`를 사용했는지 확인하세요. | **Verify:** Check that `request.override(system_message=...)` was used. |
| 85 | `request`를 직접 수정하면 안 됩니다 — `override()`로 새 request를 만들어야 합니다. | Do not modify `request` directly -- you must create a new request with `override()`. |

---
### Section: Part 1 to Part 2 Transition
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 86 | Part 1 → Part 2 전환: 메커니즘에서 행동 규칙으로 | Part 1 -> Part 2 Transition: From Mechanism to Behavior Rules |
| 87 | Part 1에서 TodoListMiddleware를 통해 agent에게 작업 추적 **메커니즘**(State + Tool + Prompt)을 제공했습니다. | In Part 1, you provided the agent with a task tracking **mechanism** (State + Tool + Prompt) through TodoListMiddleware. |
| 88 | 이제 Part 2에서는 이 메커니즘을 **언제, 어떻게 활용할지**를 Coding Agent의 시스템 프롬프트에 행동 규칙으로 정의합니다. | Now in Part 2, you will define **when and how to use** this mechanism as behavior rules in the Coding Agent's system prompt. |
| 89 | Part 1: 메커니즘 (HOW) | Part 1: Mechanism (HOW) |
| 90 | Part 2: 행동 규칙 (WHEN & WHY) | Part 2: Behavior Rules (WHEN & WHY) |
| 91 | 메커니즘 없는 행동 규칙은 무력하고, 행동 규칙 없는 메커니즘은 방향을 잃습니다 — **둘 다 있어야 Harness가 완성**됩니다. | Behavior rules without a mechanism are powerless, and a mechanism without behavior rules loses direction -- **both are needed for the Harness to be complete**. |

---
### Section: Part 2 - Harness Prompting Introduction
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 92 | Part 2: Harness Prompting — Coding Agent의 행동 규칙 | Part 2: Harness Prompting -- Behavior Rules for the Coding Agent |
| 93 | Dynamic Prompt 실습에서 `CODING_AGENT_SYSTEM_PROMPT`의 Phase 1/2/3 헤더를 작성했습니다. | In the Dynamic Prompt lab, you wrote the Phase 1/2/3 headers for `CODING_AGENT_SYSTEM_PROMPT`. |
| 94 | 이제 각 Phase에 **Harness behavior**의 구체적 규칙을 채웁니다. | Now you will fill in each Phase with specific **Harness behavior** rules. |

---
### Section: Why Implement Harness via Prompts
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 95 | 왜 프롬프트로 Harness를 구현하는가 | Why Implement the Harness via Prompts |
| 96 | Agent Harness의 4가지 전략을 프롬프트로 강제합니다: | Enforce the 4 strategies of Agent Harness through prompts: |
| 97 | Harness 전략 | Harness Strategy |
| 98 | 프롬프트에서 구현 | Implementation in Prompt |
| 99 | Context 외부화 | Context externalization |
| 100 | PHASE 3에서 progress.md, feature_list.json 업데이트 강제 | Force progress.md and feature_list.json updates in PHASE 3 |
| 101 | 해석 프로토콜 | Interpretation protocol |
| 102 | PHASE 1에서 pwd → init.sh → progress.md → feature_list.json 순서 강제 | Force the order pwd -> init.sh -> progress.md -> feature_list.json in PHASE 1 |
| 103 | 작업 단위 격리 | Work unit isolation |
| 104 | "ONE feature per session" + write_todos로 세부 추적 | "ONE feature per session" + detailed tracking with write_todos |
| 105 | E2E 테스트 강제 | Forced E2E testing |
| 106 | PHASE 2에서 "passes=true는 테스트 통과 후에만" | "passes=true only after tests pass" in PHASE 2 |

---
### Section: Prompt Writing Guide
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 107 | 프롬프트 작성 가이드: 무엇이 다른가 | Prompt Writing Guide: What Makes the Difference |
| 108 | TODO 4-5을 시작하기 전에, Agent가 **실제로 따르는 프롬프트**와 **무시하는 프롬프트**의 차이를 이해합니다. | Before starting TODOs 4-5, understand the difference between prompts the Agent **actually follows** and prompts it **ignores**. |
| 109 | 나쁜 프롬프트 vs 좋은 프롬프트 | Bad Prompts vs Good Prompts |
| 110 | 나쁜 프롬프트 (모호함): | Bad prompt (ambiguous): |
| 111 | 세션을 시작할 때 프로젝트 상태를 확인하세요. | Check the project status when starting a session. |
| 112 | → Agent가 "상태를 확인하겠습니다"라고 **말만** 하고 실제로 파일을 안 읽음. | -> The Agent just **says** "I'll check the status" without actually reading any files. |
| 113 | 모델이 **추론으로 추측**함. | The model **guesses through inference**. |
| 114 | 좋은 프롬프트 (구체적 행동 강제): | Good prompt (forces specific actions): |
| 115 | → Agent가 실제로 4개의 tool을 순서대로 호출. | -> The Agent actually calls 4 tools in order. |
| 116 | **외부 상태를 읽어서** 파악. | Learns by **reading external state**. |
| 117 | 핵심 원칙 | Core Principles |
| 118 | "상태를 확인하세요" | "Check the status" |
| 119 | 추론으로 추측 | Guesses through inference |
| 120 | 틀린 가정으로 시작 | Starts with wrong assumptions |
| 121 | "이 tool로 이 파일을 읽으세요" | "Read this file with this tool" |
| 122 | 도구를 호출하여 실제 확인 | Calls tools to actually verify |
| 123 | 정확한 상태로 시작 | Starts with accurate state |
| 124 | "적절히 처리하세요" | "Handle it appropriately" |
| 125 | 모델이 자의적으로 판단 | Model makes arbitrary decisions |
| 126 | 예측 불가능한 행동 | Unpredictable behavior |
| 127 | "X하세요. 실패하면 Y하세요." | "Do X. If it fails, do Y." |
| 128 | 명확한 분기 처리 | Clear branching logic |
| 129 | 실패에도 복구 가능 | Recoverable even on failure |
| 130 | **원칙: 추론하게 하지 말고, 읽게 만들어라. 판단하게 하지 말고, 절차를 따르게 하라.** | **Principle: Don't let it infer -- make it read. Don't let it judge -- make it follow procedures.** |

---
### Section: Part 2 Lab Structure
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 131 | 2개의 TODO를 구현합니다. | You will implement 2 TODOs. |
| 132 | 작업 단위 격리 규칙 | Work unit isolation rules |
| 133 | 작업 단위 격리 + Compound Reliability | Work unit isolation + Compound Reliability |
| 134 | Context 외부화 규칙 | Context externalization rules |
| 135 | Context 외부화 + Git 안전망 | Context externalization + Git safety net |

---
### Section: Pre-provided Code - PHASE 1
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 136 | TODO 4-5을 작성할 때 아래 PHASE 1을 **패턴**으로 참고하세요. | When writing TODOs 4-5, refer to PHASE 1 below as a **pattern**. |
| 137 | 이 프롬프트는 이미 작성되어 있습니다. | This prompt is already written. |
| 138 | PHASE 1: START — 컨텍스트 해석 프로토콜 | PHASE 1: START -- Context Interpretation Protocol |
| 139 | 이 프롬프트가 좋은 이유 (TODO 4-5에 같은 패턴을 적용하세요): | Why this prompt is good (apply the same pattern to TODOs 4-5): |
| 140 | **구체적 도구 명시** — "확인하세요" 대신 `pwd`, `read_file`, `./init.sh` 등 정확한 tool call 지정 | **Specific tool names** -- instead of "check it," specify exact tool calls like `pwd`, `read_file`, `./init.sh` |
| 141 | **실패 분기 포함** — "permission error면 chmod", "테스트 실패면 먼저 수정" 등 fallback 제공 | **Includes failure branches** -- provides fallbacks like "if permission error, chmod," "if tests fail, fix first" |
| 142 | **강제 어투** — "You MUST", "Do NOT skip" — 권장이 아닌 의무 | **Mandatory language** -- "You MUST", "Do NOT skip" -- obligation, not recommendation |
| 143 | **순서 강제** — 번호로 순서를 명시하여 agent가 건너뛰지 못하게 함 | **Forced ordering** -- numbering makes the order explicit so the agent cannot skip steps |

---
### Section: TODO 4 - PHASE 2
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 144 | TODO 4: PHASE 2 구체화 — 작업 단위 격리 | TODO 4: PHASE 2 Detailed -- Work Unit Isolation |
| 145 | # TODO 4: 하나의 feature를 선택하고 구현하는 단계를 작성하세요 | # TODO 4: Write the steps for selecting and implementing a single feature |
| 146 | # Agent Harness.md의 "작업 단위 격리" 참고: | # Refer to "Work Unit Isolation" in Agent Harness.md: |
| 147 | # 1. Feature 선택 — passes=false인 것 중 high priority 선택 | # 1. Feature selection -- select high priority among those with passes=false |
| 148 | # dependencies가 모두 passes=true인지 확인 | # Verify that all dependencies have passes=true |
| 149 | # 2. write_todos로 세부 단계 생성 — feature의 steps를 todo로 변환 | # 2. Create detailed steps with write_todos -- convert feature steps to todos |
| 150 | # 3. 구현 — 하나의 feature만 집중 | # 3. Implementation -- focus on only one feature |
| 151 | # 4. 테스트 — E2E로 검증, passes=true는 테스트 통과 후에만 | # 4. Testing -- verify with E2E, passes=true only after tests pass |
| 152 | # Compound Reliability 관점: | # From a Compound Reliability perspective: |
| 153 | # 여러 feature를 한 세션에 시도하면 0.95^50 = 실패 확실 | # Attempting multiple features in one session: 0.95^50 = certain failure |
| 154 | # 하나만 집중하면 0.95^5 = 77.4% + git revert 안전망 | # Focusing on one: 0.95^5 = 77.4% + git revert safety net |

---
### Section: TODO 5 - PHASE 3
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 155 | TODO 5: PHASE 3 구체화 — Context 외부화 | TODO 5: PHASE 3 Detailed -- Context Externalization |
| 156 | # TODO 5: 세션 종료 전 반드시 수행할 단계를 작성하세요 | # TODO 5: Write the steps that must be performed before ending the session |
| 157 | # Agent Harness.md의 "Context 외부화" 참고: | # Refer to "Context Externalization" in Agent Harness.md: |
| 158 | # 1. progress.md 업데이트 — 세션 기록 (edit_file 또는 write_file 사용) | # 1. Update progress.md -- session record (use edit_file or write_file) |
| 159 | # 2. feature_list.json 업데이트 — passes=true로 변경 (edit_file 사용) | # 2. Update feature_list.json -- change to passes=true (use edit_file) |
| 160 | # 테스트를 통과한 feature만! | # Only for features that passed tests! |
| 161 | # 3. Git commit — 깨끗한 상태 고정 | # 3. Git commit -- lock in a clean state |
| 162 | # 4. Clean state 확인 — uncommitted changes 없는지 확인 | # 4. Verify clean state -- confirm no uncommitted changes |
| 163 | # 왜 이 순서인가? | # Why this order? |
| 164 | # 파일 업데이트 → commit 순서가 아니면, 다음 세션 agent가 progress.md를 읽어도 최신 정보가 없는 상태로 시작합니다. | # If the order isn't file update -> commit, the next session's agent starts without the latest information even after reading progress.md. |

---
### Section: Connecting Middleware to the Agent
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 165 | Agent에 미들웨어 연결하기 | Connecting Middleware to the Agent |
| 166 | TodoListMiddleware를 구현한 후, `agent_specs.py`에서 미들웨어 스택에 추가합니다: | After implementing TodoListMiddleware, add it to the middleware stack in `agent_specs.py`: |
| 167 | **왜 FilesystemMiddleware 뒤인가?** | **Why after FilesystemMiddleware?** |
| 168 | TodoListMiddleware는 `wrap_model_call`에서 prompt를 주입합니다. | TodoListMiddleware injects prompts in `wrap_model_call`. |
| 169 | FilesystemMiddleware보다 안쪽(뒤)에 있으므로, filesystem prompt 위에 todo prompt가 추가됩니다. | Since it is inner (after) FilesystemMiddleware, the todo prompt is added on top of the filesystem prompt. |

---
### Section: Verification
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 170 | 검증 방법 | Verification Method |
| 171 | Part 1 검증 (TodoListMiddleware): | Part 1 verification (TodoListMiddleware): |
| 172 | Part 2 검증 (Harness Prompting): | Part 2 verification (Harness Prompting): |
| 173 | 전체 동작 테스트: | Full integration test: |
| 174 | `"블로그 플랫폼 만들어줘"` 입력 후 확인: | After entering `"Build me a blog platform"`, verify: |
| 175 | Agent가 `pwd` → `init.sh` 순서로 시작하는지 (PHASE 1) | Agent starts with `pwd` -> `init.sh` in order (PHASE 1) |
| 176 | `write_todos`를 호출하여 작업 계획을 만드는지 | Calls `write_todos` to create a work plan |
| 177 | 하나의 feature만 작업하는지 (PHASE 2) | Works on only one feature (PHASE 2) |
| 178 | `progress.md`, `feature_list.json` 업데이트 후 commit 하는지 (PHASE 3) | Updates `progress.md` and `feature_list.json` then commits (PHASE 3) |

---
### Section: Common Failures and Solutions
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 179 | 흔한 실패와 대처 | Common Failures and Solutions |
| 180 | `write_todos`가 tool 목록에 안 나옴 | `write_todos` does not appear in the tool list |
| 181 | `__init__`에서 `self.tools` 미설정 | `self.tools` not set in `__init__` |
| 182 | TODO 2에서 `self.tools = [StructuredTool.from_function(...)]` 확인 | Verify `self.tools = [StructuredTool.from_function(...)]` in TODO 2 |
| 183 | `Command(update=...)` 후 todos가 안 바뀜 | todos don't change after `Command(update=...)` |
| 184 | `messages` 키 누락 | Missing `messages` key |
| 185 | `Command(update={"todos": ..., "messages": [ToolMessage(...)]})`로 둘 다 포함 | Include both with `Command(update={"todos": ..., "messages": [ToolMessage(...)]})` |
| 186 | Agent가 모든 todo를 한꺼번에 completed로 변경 | Agent changes all todos to completed at once |
| 187 | Description에 "한 번에 1개만 in_progress" 규칙 누락 | Missing the "only 1 in_progress at a time" rule in the description |
| 188 | 사전 제공 코드의 description에 "Exactly ONE task in_progress at any time" 명시 | Specify "Exactly ONE task in_progress at any time" in the pre-provided description |
| 189 | Agent가 PHASE 1을 건너뛰고 바로 코딩 시작 | Agent skips PHASE 1 and starts coding immediately |
| 190 | 프롬프트가 "권장"으로 작성됨 | Prompt is written as a "recommendation" |
| 191 | "You MUST complete PHASE 1 before any implementation work" 강제 어투 사용 | Use mandatory language: "You MUST complete PHASE 1 before any implementation work" |
| 192 | `progress.md` 업데이트가 git commit에 안 잡힘 | `progress.md` update is not captured in git commit |
| 193 | PHASE 3 순서 오류 (commit → 파일 수정) | PHASE 3 order error (commit -> file modification) |
| 194 | 반드시 "파일 수정 → git add → git commit" 순서 강제 | Must enforce the order "file modification -> git add -> git commit" |

---
### Section: Concept Connection Map
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 195 | Agent Harness.md에서 배운 것 → 이 실습에서 구현한 것 | What was learned in Agent Harness.md -> What was implemented in this lab |
| 196 | 암묵적 기억 → 명시적 상태 | Implicit memory -> explicit state |
| 197 | "대화 속 정보를 state로" | "Information from conversations into state" |
| 198 | todos를 agent state에 명시적 저장 | Explicitly store todos in agent state |
| 199 | Middleware의 3가지 축 | Middleware's 3 axes |
| 200 | PlanningState + write_todos + system_prompt | PlanningState + write_todos + system_prompt |
| 201 | 해석 프로토콜 | Interpretation protocol |
| 202 | "pwd → git log → feature list" | "pwd -> git log -> feature list" |
| 203 | Agent가 외부 상태를 읽고 시작 | Agent starts by reading external state |
| 204 | 작업 단위 격리 | Work unit isolation |
| 205 | "한 번에 하나만" | "Only one at a time" |
| 206 | ONE feature + write_todos로 추적 | ONE feature + tracked with write_todos |
| 207 | Context 외부화 | Context externalization |
| 208 | "파일로 상태 기록" | "Record state to files" |
| 209 | progress.md + feature_list.json + commit | progress.md + feature_list.json + commit |
| 210 | Compound Reliability | Compound Reliability |
| 211 | "0.95^10 = 59.9%" | "0.95^10 = 59.9%" |
| 212 | 작업을 작게 → 성공률 유지 | Keep work small -> maintain success rate |
