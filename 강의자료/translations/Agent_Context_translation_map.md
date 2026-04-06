# Agent Context

## Sentence-by-Sentence Translation Map

---

### Section: References

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | 참고 자료: | References: |
| 2 | Anthropic: Advanced Tool Use | Anthropic: Advanced Tool Use |
| 3 | Anthropic: Code Execution with MCP | Anthropic: Code Execution with MCP |
| 4 | Anthropic: Effective Context Engineering for AI Agents | Anthropic: Effective Context Engineering for AI Agents |
| 5 | 12-Factor Agents: Own Your Context Window | 12-Factor Agents: Own Your Context Window |

---

### Section: Table of Contents

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 6 | 목차 | Table of Contents |
| 7 | Context의 확장 | Expansion of Context |
| 8 | Agent context 구성요소 | Agent Context Components |
| 9 | Context 관리의 중요성 | Importance of Context Management |
| 10 | 유한한 Context Window | Finite Context Window |
| 11 | Context rot 현상 | Context Rot Phenomenon |
| 12 | Attention Budget | Attention Budget |
| 13 | 비용과 지연 시간 | Cost and Latency |
| 14 | 섹션 별 페이지 링크 | Section Page Links |

---

### Section: Expansion of Context

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 15 | Context의 확장 | Expansion of Context |
| 16 | 한두 번 호출로 끝나는 task에서는 시스템/유저 프롬프트를 잘 쓰는 것이 핵심이었습니다. | For tasks that finished with one or two calls, writing good system/user prompts was the key. |
| 17 | → System prompt == Context | → System prompt == Context |
| 18 | 하지만 tool 호출, memory/외부 데이터 읽고, 수십수백 턴을 도는 agent loop가 기본 패턴이 되면서, 결과적으로 context window는 이전보다 더욱 빠르게 채워집니다. | But as the standard pattern became agent loops that call tools, read memory/external data, and run for dozens or hundreds of turns, the context window fills up faster than before. |

---

### Section: Agent Context Components

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 19 | Agent context 구성요소 | Agent Context Components |
| 20 | Agent의 Context는 다음 요소들로 구성됩니다. | An Agent's Context is composed of the following elements. |
| 21 | System prompt — Agent의 역할, 성격, 규칙 정의 | System prompt — Defines the Agent's role, personality, and rules |
| 22 | "당신은 코딩 에이전트입니다..." | "You are a coding agent..." |
| 23 | Tool 정의 — 사용 가능한 도구들에 대한 설명 및 스키마 | Tool definitions — Descriptions and schemas of available tools |
| 24 | 파라미터, 반환값, 사용법 설명 | Parameters, return values, and usage descriptions |
| 25 | Retrieved Data(RAG) — 외부에서 검색해온 문서, 코드, 정보 | Retrieved Data (RAG) — Documents, code, and information retrieved from external sources |
| 26 | 벡터 DB, 파일 시스템 등에서 가져옴 | Fetched from vector databases, file systems, etc. |
| 27 | Conversation History(대화 이력) — 이전 메세지들(User, Assistant, Tool 결과) | Conversation History — Previous messages (User, Assistant, Tool results) |
| 28 | 작업이 길어질수록 급격히 증가 | Grows rapidly as tasks get longer |
| 29 | Working Memory — Todo 리스트, 현재 작업 상태 | Working Memory — Todo list, current task status |
| 30 | 관련 대화에서 가져온 메모리 | Memory retrieved from related conversations |
| 31 | Output Format Instructions — 응답 형식 지정(JSON, Markdown 등) | Output Format Instructions — Specifying response format (JSON, Markdown, etc.) |
| 32 | 매 요청마다 이 모든 요소가 하나의 프롬프트로 조합되어 LLM에 전달됩니다. | With every request, all these elements are combined into a single prompt and sent to the LLM. |

---

### Section: Integrated Diagram

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 33 | 통합 다이어그램: 하나의 LLM 호출에 들어가는 것 | Integrated Diagram: What Goes Into a Single LLM Call |
| 34 | [Code block] | [Code block] |
| 35 | System Prompt — 역할, 규칙, 행동 지침 | System Prompt — Role, rules, behavioral guidelines |
| 36 | ← Section 2에서 다룸 | ← Covered in Section 2 |
| 37 | Tool Definitions — 도구 스키마, 설명, 파라미터 | Tool Definitions — Tool schemas, descriptions, parameters |
| 38 | ← Section 3에서 다룸 | ← Covered in Section 3 |
| 39 | Conversation History — 이전 메시지, Tool 결과 | Conversation History — Previous messages, Tool results |
| 40 | (턴이 쌓일수록 증가) | (Grows as turns accumulate) |
| 41 | ← Section 1에서 다룸 | ← Covered in Section 1 |
| 42 | Working Memory — Todos, 작업 상태 | Working Memory — Todos, task status |
| 43 | Retrieved Data (RAG) + Output Format Instructions | Retrieved Data (RAG) + Output Format Instructions |
| 44 | 이 6가지 요소가 합쳐져 하나의 Context Window를 구성합니다. | These 6 elements combine to form a single Context Window. |
| 45 | 문제는 이 공간이 유한하다는 것입니다. | The problem is that this space is finite. |

---

### Section: Strategic Context Management

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 46 | 이 과정에서는 3가지 섹션을 통해 Context를 전략적으로 관리하는 방법을 배웁니다: | In this course, you will learn how to strategically manage Context through 3 sections: |
| 47 | **Section 1: 토큰** — 컨텍스트를 어떻게 **줄이는가**? — 토큰 효율성, Prompt Caching, 압축(Truncation/Summarization) | **Section 1: Tokens** — How do you **reduce** context? — Token efficiency, Prompt Caching, compression (Truncation/Summarization) |
| 48 | **Section 2: 프롬프트** — 컨텍스트를 어떻게 **넣는가**? — Expert Activation, Reasoning 모델 활용, 동적 주입 | **Section 2: Prompts** — How do you **insert** context? — Expert Activation, leveraging Reasoning models, dynamic injection |
| 49 | **Section 3: 도구** — 컨텍스트를 어떻게 **통제하는가**? — Defer Loading, Tool Output 크기 제한 | **Section 3: Tools** — How do you **control** context? — Defer Loading, Tool Output size limits |

---

### Section: Importance of Context Management

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 50 | Context 관리의 중요성 | Importance of Context Management |

---

### Section: Finite Context Window

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 51 | 유한한 Context Window | Finite Context Window |
| 52 | 모든 LLM은 처리할 수 있는 토큰 수에 Hard Limit이 있습니다. | Every LLM has a Hard Limit on the number of tokens it can process. |
| 53 | GPT 5.2 — 400K 토큰 | GPT 5.2 — 400K tokens |
| 54 | Claude 4.5 Opus — 200K 토큰 | Claude 4.5 Opus — 200K tokens |
| 55 | Gemini 3.0 pro — 1M 토큰 | Gemini 3.0 pro — 1M tokens |
| 56 | 많아 보이지만, Agent가 Tool을 적극적으로 사용하면 금방 소진됩니다. | This seems like a lot, but it is quickly exhausted when an Agent actively uses Tools. |

---

### Section: Context Rot Phenomenon

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 57 | Context rot 현상 | Context Rot Phenomenon |
| 58 | 모델이 발전할 수록 context window의 크기는 증가합니다. | As models advance, the context window size increases. |
| 59 | 하지만, 이를 "Context window의 크기를 전부 채워서 활용할 수 있다."라 이해한다면, 특정 token 양을 넘었을 때, 성능 저하를 경험할 수 있습니다. | However, if you interpret this as "you can fill and utilize the entire context window," you may experience performance degradation once a certain token count is exceeded. |
| 60 | 이렇게 길이가 길어질수록 필요한 정보를 정확히 찾아 사용하지 못하는 이른바 context rot 현상이라고 합니다. | This phenomenon where the model fails to accurately find and use necessary information as the length grows is called context rot. |
| 61 | 이론적인 최대 길이와는 별개로 모델이 안정적으로 집중할 수 있는 실질적인 구간이 존재합니다. | Separately from the theoretical maximum length, there is a practical range where the model can reliably focus. |
| 62 | 결과적으로, 내용을 가능한 한 많이 넣는 것이 아니라, 적절히 짧으면서도 영양가 있는 부분만 선별해 넣는 것이 성능과 안정성 면에서 더 유리한 경우가 많습니다. | As a result, rather than cramming in as much content as possible, selectively including only appropriately short yet substantive portions is often more advantageous in terms of performance and stability. |

---

### Section: Attention Budget

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 63 | Attention Budget | Attention Budget |
| 64 | Context rot과 연결되는 개념입니다. | This is a concept connected to context rot. |
| 65 | LLM이 실질적으로 집중할 수 있는 token 양을 의미합니다. | It refers to the amount of tokens the LLM can effectively focus on. |

---

### Section: Cost and Latency

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 66 | 비용과 지연 시간 | Cost and Latency |
| 67 | 토큰 = 비용: 입력 토큰도 과금됩니다 | Tokens = cost: Input tokens are also billed |
| 68 | 토큰 = 지연: 더 많은 토큰 = 더 긴 응답 시간 | Tokens = latency: More tokens = longer response time |
| 69 | 따라서 단순히 프롬프트를 잘 쓰는 것을 넘어서, Context의 6가지 구성 요소를 전략적으로 설계하고 관리하는 것이 중요합니다. | Therefore, beyond simply writing good prompts, it is important to strategically design and manage the 6 components of Context. |

---

### Section: Section Page Links

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 70 | 섹션 별 페이지 링크 | Section Page Links |
| 71 | Token — Section 1: 토큰 (Token) | Token — Section 1: Tokens (Token) |
| 72 | Prompt — Section 2: 프롬프트 (Prompt) 심화 | Prompt — Section 2: Prompts (Prompt) Advanced |
| 73 | Tool — Section 3: 도구 (Tool) | Tool — Section 3: Tools (Tool) |
