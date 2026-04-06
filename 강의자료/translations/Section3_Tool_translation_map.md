# Section 3: Tools

## Sentence-by-Sentence Translation Map

---

### Section: Tool Definition Problem

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Anthropic의 연구에 따르면, Tool 정의만으로 50,000+ 토큰이 소비될 수 있습니다. | According to Anthropic's research, Tool definitions alone can consume over 50,000 tokens. |

---

### Section: Real-World Scenario

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 2 | MCP(Model Context Protocol) 서버 여러 개를 연결한 개발 환경을 생각해보겠습니다. | Let's consider a development environment with multiple MCP (Model Context Protocol) servers connected. |
| 3 | GitHub 15 ~8,000 / Slack 10 ~5,000 / Sentry 8 ~4,000 / Grafana 12 ~6,000 / Splunk 10 ~5,000 / 합계 55 ~28,000 | GitHub 15 ~8,000 / Slack 10 ~5,000 / Sentry 8 ~4,000 / Grafana 12 ~6,000 / Splunk 10 ~5,000 / Total 55 ~28,000 |
| 4 | 여기에 각 Tool의 상세 스키마까지 포함하면, 많은 Tool만으로 Context의 많은 부분을 차지합니다. | When detailed schemas for each Tool are included on top of this, the Tools alone occupy a large portion of the Context. |

---

### Section: What Is MCP?

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 5 | MCP 서버는 LLM이 동적으로 발견(discover)하고 호출할 수 있는 Tool들을 표준 형식으로 제공하는 레지스트리(registry) 겸 실행 엔드포인트입니다. | An MCP server is a registry and execution endpoint that provides Tools in a standard format that LLMs can dynamically discover and invoke. |
| 6 | 즉, 에이전트가 런타임에 list_tools()로 사용 가능한 Tool 목록을 조회한 뒤, Function Calling을 통해 필요한 Tool을 MCP 서버에 요청하면 서버가 실제 로직을 실행하고 결과를 반환하는 구조입니다. | In other words, the agent queries the available Tool list at runtime using list_tools(), then requests the needed Tool from the MCP server via Function Calling, and the server executes the actual logic and returns the result. |

---

### Section: The Problem

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 7 | 사용자가 Input을 넣기도 전에 Context의 절반이 이미 차 있습니다. | Half of the Context is already filled before the user even provides any input. |

---

### Section: Tool Search Tool (Defer Loading)

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 8 | Anthropic이 제안한 해결책은 필요할 때만 도구를 로드하는 것입니다. | The solution proposed by Anthropic is to load tools only when needed. |
| 9 | 기존 방식: 시작 시 모든 Tool 로드 → 77K 토큰 소비 → 작업 시작 | Traditional approach: Load all Tools at startup → 77K tokens consumed → Begin work |
| 10 | 새로운 방식: 핵심 Tool만 로드 (5개) → 8.7K 토큰, 필요 시 Tool 검색 → 해당 Tool만 추가 로드 | New approach: Load only core Tools (5) → 8.7K tokens, search for Tools when needed → Load only the relevant Tool on demand |

---

### Section: defer_loading Pattern

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 11 | 효과: 토큰만 절약되는 게 아니라 정확도도 상승합니다. | The effect: Not only are tokens saved, but accuracy also improves. |
| 12 | Context가 깔끔해지면서 모델이 더 집중할 수 있기 때문입니다. | This is because a cleaner Context allows the model to focus better. |
| 13 | 초기 토큰 77K→8.7K, 감소율 88.7%, Opus 4 정확도 49%→74%, Opus 4.5 정확도 79.5%→88.1% | Initial tokens 77K→8.7K, reduction rate 88.7%, Opus 4 accuracy 49%→74%, Opus 4.5 accuracy 79.5%→88.1% |

---

### Section: Evolution into Claude Skills

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 14 | Tool Search Tool 개념은 Claude Code의 Skill 시스템으로 발전했습니다. | The Tool Search Tool concept evolved into Claude Code's Skill system. |
| 15 | defer loading 관점에서, Claude Skills는 Tool Search Tool의 확장된 개념입니다. | From a defer loading perspective, Claude Skills is an extended concept of the Tool Search Tool. |
| 16 | 복잡한 워크플로우, 도메인 지식, Tool 등을 캡슐화하여 재사용 가능하도록 합니다. | It encapsulates complex workflows, domain knowledge, Tools, and more to make them reusable. |

---

### Section: Programmatic Tool Calling (Code-Based Orchestration) — Advanced Reference

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 17 | 이 패턴은 심화 참고자료입니다. | This pattern is advanced reference material. |
| 18 | Context를 급직적으로 최적화는 방법으로 Agent가 단순 Tool 호출 대신 코드를 작성하여 Tool을 조율하는 것입니다. | A method to dramatically optimize Context is for the Agent to write code to orchestrate Tools instead of making simple Tool calls. |

---

### Section: Problem with Traditional LLM-Tool Interaction

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 19 | Agent가 2,000개의 경비 항목을 분석해야 한다고 가정하겠습니다. | Let's assume the Agent needs to analyze 2,000 expense items. |

---

### Section: Programmatic Approach

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 20 | 기존처럼 Tool 결과 하나하나 LLM에서 처리하는 대신 코드로 처리하게 작업 효율성과 Context 최적화를 극대화 했습니다. | Instead of processing each Tool result one by one in the LLM as before, processing them via code maximizes both work efficiency and Context optimization. |
| 21 | Programmatic 방식을 위해서는 Sandbox 환경 및 Permission Control을 통해 코드를 수행할 수 있도록 하여, 자칫 발생할 수 있는 사고를 사전에 예방할 수 있어야 합니다. | For the Programmatic approach, code execution must be enabled through a Sandbox environment and Permission Control to prevent potential accidents in advance. |

---

### Section: Programmatic Approach Application Conditions

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 22 | 대량 데이터 집계/필터링 | Aggregating/filtering large volumes of data |
| 23 | 다단계 종속(Dependency) 작업(A결과로 B 호출) | Multi-step dependency tasks (calling B with the result of A) |
| 24 | 병렬 처리 가능한 작업 | Tasks that can be processed in parallel |
| 25 | 데이터 변화 후 모델에 전달 | Passing data to the model after transformation |

---

### Section: Tool Output Management

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 26 | Tool이 Return하는 결과는 기본적으로 메세지 형태로 LLM에 제공됩니다. | Results returned by Tools are provided to the LLM in message form by default. |
| 27 | 때문에 Tool 결과의 형태에 문제가 있다면, Context에 일부분으로서 최적화 대상입니다. | Therefore, if there are issues with the format of Tool results, they are optimization targets as part of the Context. |

---

### Section: Tool Output Size Limiting Strategies

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 28 | Hard Truncation: 최대 문자 수 제한 - output[:1000] | Hard Truncation: Limit maximum character count - output[:1000] |
| 29 | Schema Extraction: 필요한 필드만 추출 | Schema Extraction: Extract only the necessary fields |
| 30 | Summarization: LLM으로 요약 - 에러 로그 요약 | Summarization: Summarize with the LLM - error log summarization |
| 31 | Sampling: 대표 샘플만 - 1000개 중 10개만 Message에 | Sampling: Only representative samples - only 10 out of 1,000 in the Message |

---

### Section: Hands-on Connection: Application in Filesystem Middleware Practice

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 32 | Defer Loading: FilesystemMiddleware가 핵심 도구 7개만 등록 | Defer Loading: FilesystemMiddleware registers only 7 core tools |
| 33 | Tool Output 크기 제한: wrap_tool_call에서 대형 결과(20K+ 토큰)를 파일로 저장하고 미리보기만 반환 | Tool Output size limiting: wrap_tool_call saves large results (20K+ tokens) to a file and returns only a preview |
| 34 | Schema Extraction: 전용 도구(edit_file 등)가 구조화된 입출력으로 불필요한 데이터 최소화 | Schema Extraction: Dedicated tools (edit_file, etc.) minimize unnecessary data through structured input/output |
| 35 | Soft Rules: wrap_model_call에서 "파일 작업에는 bash 대신 전용 도구 사용" 가이드라인 주입 | Soft Rules: Injecting the guideline "use dedicated tools instead of bash for file operations" in wrap_model_call |
