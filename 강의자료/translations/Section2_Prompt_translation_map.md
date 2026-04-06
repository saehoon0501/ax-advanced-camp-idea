# Section 2: Prompt Deep Dive

## Sentence-by-Sentence Translation Map

---

### Section: Reasoning Model vs Traditional Model

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Reasoning Model(Claude의 Extended Thinking, OpenAI의 o1 등)은 기존 모델과 근본적으로 다른 방식으로 작동합니다. | Reasoning Models (such as Claude's Extended Thinking and OpenAI's o1) operate in a fundamentally different way from traditional models. |

---

### Section: Traditional Model: A to Z Direct

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 2 | 기존 모델은 입력(A)을 받으면 한 번의 forward pass로 바로 출력(Z)을 생성합니다. | Traditional models receive an input (A) and generate an output (Z) directly in a single forward pass. |
| 3 | 모델의 "깊이(depth)"가 고정되어 있기 때문에, 복잡한 문제는 한 번에 풀기 어렵습니다. | Because the model's "depth" is fixed, complex problems are difficult to solve in one pass. |

---

### Section: Reasoning Model: A to B to C to D to ... to Z

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 4 | Reasoning 모델은 중간 단계를 명시적으로 열거합니다. | Reasoning models explicitly enumerate intermediate steps. |

---

### Section: Core Significance: Overcoming Depth Limitations

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 5 | LLM은 통계적 패턴 매칭 기반입니다. | LLMs are based on statistical pattern matching. |
| 6 | 모델 파라미터(가중치)가 고정되면, 한 번의 forward pass로 수행할 수 있는 "추론의 깊이"도 제한됩니다. | Once model parameters (weights) are fixed, the "depth of reasoning" achievable in a single forward pass is also limited. |
| 7 | Reasoning 모델은 이 한계를 Inference Time Compute로 극복합니다. | Reasoning models overcome this limitation through Inference Time Compute. |

---

### Section: Comparison Table

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 8 | 추론 방식: 입력 → 출력 (1단계) vs 입력 → 중간 단계들 → 출력 | Reasoning approach: Input → Output (1 step) vs Input → Intermediate steps → Output |
| 9 | 복잡한 문제: 깊이 부족으로 실패 vs 단계를 나눠서 해결 | Complex problems: Fails due to insufficient depth vs Solved by breaking into steps |
| 10 | 비용: 고정 vs 문제 복잡도에 비례 | Cost: Fixed vs Proportional to problem complexity |
| 11 | 비유: 암산 vs 종이에 풀이 과정 작성 | Analogy: Mental arithmetic vs Writing out the solution on paper |

---

### Section: Analogy

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 12 | 암기력이 좋은 사람도 복잡한 계산은 머릿속으로만 하기 어렵습니다. | Even someone with great memory finds it difficult to do complex calculations purely in their head. |
| 13 | 종이에 중간 과정을 적으면 훨씬 복잡한 문제도 풀 수 있습니다. | By writing down intermediate steps on paper, much more complex problems become solvable. |
| 14 | Reasoning 모델은 "종이에 적는" 과정을 모델 내부에서 수행합니다. | Reasoning models perform the "writing on paper" process internally within the model. |

---

### Section: Chain-of-Thought (CoT) Boosting

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 15 | 기존 모델에서는 명시적으로 "단계별로 생각해보세요"라고 요청해야 했습니다. | With traditional models, you had to explicitly request "think step by step." |
| 16 | Reasoning 모델은 내부적으로 CoT를 수행합니다. | Reasoning models perform CoT internally. |
| 17 | 단순 질문: 명시적 CoT 불필요(모델이 알아서 판단) | Simple questions: Explicit CoT is unnecessary (the model decides on its own) |
| 18 | 특정 형식 원할 때: "과정을 보여달라"고 요청 | When a specific format is desired: Request to "show the process" |
| 19 | 디버깅/검증: 사고 과정 출력 요청하여 확인 | Debugging/verification: Request the thought process output for review |

---

### Section: When Is Explicit CoT Still Useful?

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 20 | 출력 형식 지정: "풀이 과정을 마크다운으로 보여줘" | Specifying output format: "Show the solution process in markdown" |
| 21 | 교육 목적: 사용자에게 과정을 설명해야 할 때 | Educational purposes: When the process needs to be explained to the user |
| 22 | 검증 필요: 모델의 추론 과정을 확인하고 싶을 때 | Verification needed: When you want to inspect the model's reasoning process |
| 23 | 특정 방법론 강제: "귀납법으로 증명해줘" or 원하는 수행 절차 강제(phase 1, phase 2, ...) | Enforcing a specific methodology: "Prove it by induction" or enforcing a desired execution procedure (phase 1, phase 2, ...) |

---

### Section: How Prompts Activate Internal Model Expertise

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 24 | 최신 대형 LLM들은 내부적으로 여러 "전문가(Expert)" 네트워크를 가지고 있으며, 입력에 따라 적합한 전문가가 활성화됩니다 (Mixture of Experts 아키텍처). | Modern large LLMs internally contain multiple "Expert" networks, and the appropriate expert is activated based on the input (Mixture of Experts architecture). |
| 25 | 중요한 것은 프롬프트의 내용과 스타일이 어떤 전문가가 활성화되는지에 직접 영향을 준다는 점입니다. | The important point is that the content and style of the prompt directly influence which expert gets activated. |
| 26 | "def function():" → 코딩 관련 Expert | "def function():" → Coding-related Expert |
| 27 | "∫ x² dx" → 수학 관련 Expert | "∫ x² dx" → Math-related Expert |
| 28 | "번역해줘" → 다국어 Expert | "Translate this" → Multilingual Expert |
| 29 | 법률 용어 다수 → 법률/전문 분야 Expert | Numerous legal terms → Legal/specialized domain Expert |
| 30 | 프롬프트 작성 시, 맨 처음 페르소나 작성을 통해 원하는 Expert를 더 확실히 강조할 수 있습니다. | When writing prompts, defining a persona at the very beginning can more strongly emphasize the desired Expert. |
| 31 | 예: "너는 20년차 시니어 Python 개발자야" | Example: "You are a senior Python developer with 20 years of experience" |

---

### Section: Practical Implications

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 32 | 일관된 도메인 언어 사용: 코딩 작업이면 코드 컨텍스트를 풍부하게 구성합니다 | Use consistent domain language: For coding tasks, enrich the context with code-related content |
| 33 | 명확한 역할 부여: "당신은 시니어 백엔드 개발자입니다" → 코딩 Expert 활성화 유도 | Clear role assignment: "You are a senior backend developer" → Induces activation of the coding Expert |
| 34 | 혼합 요청 주의: "시를 쓰면서 코드도 작성해줘" → Expert 선택 혼란 가능 | Caution with mixed requests: "Write a poem and also write code" → Can cause confusion in Expert selection |

---

### Section: Hands-on Connection: Application in Dynamic Prompt Practice

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 35 | 이 섹션에서 배운 원칙을 Dynamic Prompt 실습에서 직접 적용합니다. | The principles learned in this section are directly applied in the Dynamic Prompt hands-on exercise. |
| 36 | Expert Activation (역할 부여): CODING_AGENT_SYSTEM_PROMPT에서 "당신은 Coding Agent입니다" → 코딩 전문가 활성화 | Expert Activation (role assignment): "You are a Coding Agent" in CODING_AGENT_SYSTEM_PROMPT → Activates the coding expert |
| 37 | 일관된 도메인 언어: Static prompt에 코딩 용어와 Phase 구조를 일관되게 사용 → 동일 Expert 유지 | Consistent domain language: Consistently using coding terminology and Phase structure in the static prompt → Maintains the same Expert |
| 38 | Prompt Caching (Section 1 연결): Static 부분을 prefix로 고정 → 캐시 재사용으로 비용/지연 절감 | Prompt Caching (connects to Section 1): Fixing the static portion as a prefix → Reduces cost/latency through cache reuse |
| 39 | Dynamic 주입: 런타임 상태(workspace, todos)는 suffix로 추가 → 캐시를 깨지 않으면서 최신 컨텍스트 반영 | Dynamic injection: Runtime state (workspace, todos) is appended as a suffix → Reflects the latest context without breaking the cache |
| 40 | Static prompt의 persona 정의는 단순한 역할극이 아닙니다 — 모델 내부의 적합한 전문가를 활성화하는 기술적 선택입니다. | Defining a persona in the static prompt is not mere role-playing — it is a technical choice that activates the appropriate expert inside the model. |
