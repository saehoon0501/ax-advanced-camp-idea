# Tool Design Guide for AI Agents
## Sentence-by-Sentence Translation Map
---
### Section: Introduction
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | AI 에이전트의 능력은 결국 사용할 수 있는 도구의 품질에 의해 결정됩니다. | The capability of an AI agent is ultimately determined by the quality of the tools it can use. |
| 2 | 아무리 뛰어난 LLM이라도 잘못 설계된 도구를 사용하면 실수를 반복하고, 안전하지 않은 결과를 만들어냅니다. | No matter how advanced the LLM, using poorly designed tools leads to repeated mistakes and unsafe outcomes. |
| 3 | 도구 설계는 단순히 "함수를 만들어 LLM에 연결하는 것"이 아닙니다. | Tool design is not simply "creating a function and connecting it to an LLM." |
| 4 | 다음과 같은 질문에 답해야 합니다: | You need to answer questions like the following: |
| 5 | 이 도구가 범용 도구여야 하는가, 전용 도구여야 하는가? | Should this tool be a general-purpose tool or a specialized tool? |
| 6 | 도구의 출력이 LLM의 컨텍스트를 얼마나 소비하는가? | How much of the LLM's context does the tool's output consume? |
| 7 | 도구를 잘못 사용했을 때 어떤 피해가 발생하는가? | What damage occurs when the tool is used incorrectly? |
| 8 | LLM이 이 도구를 올바르게 선택하도록 어떻게 유도하는가? | How do you guide the LLM to select the right tool? |
| 9 | 이 글에서는 실제 Claude Code의 도구 시스템을 분석하고, AI 에이전트 도구 설계의 핵심 원칙들을 정리합니다. | In this article, we analyze the actual tool system of Claude Code and summarize the core principles of AI agent tool design. |

---
### Section: Core Decision - Specialized vs General Tools
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 10 | AI 에이전트에 도구를 제공할 때 가장 먼저 결정해야 하는 것은 "이 도구를 전용(Specialized)으로 만들 것인가, 범용(General)으로 만들 것인가" 입니다. | When providing tools to an AI agent, the first decision you must make is whether to build the tool as specialized or general-purpose. |

---
### Section: Hybrid Approach
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 11 | 실전에서는 하나만 선택하지 않습니다. | In practice, you don't choose just one. |
| 12 | Claude Code는 하이브리드 접근법을 사용합니다. | Claude Code uses a hybrid approach. |

---
### Section: When to Create Specialized Tools
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 13 | 다음 조건 중 2개 이상을 만족하면 전용 도구를 만드는 것이 좋습니다: | If two or more of the following conditions are met, it is advisable to create a specialized tool: |
| 14 | 자주 사용됨: 파일 읽기/쓰기처럼 거의 매번 호출되는 작업 | Frequently used: operations called almost every time, like file read/write |
| 15 | 안전장치가 필요함: 경로 검증, 읽기 선행 확인 등 | Safety mechanisms needed: path validation, read-before-write checks, etc. |
| 16 | 입출력 형식이 정해져 있음: 구조화된 파라미터와 결과가 필요 | Fixed input/output format: structured parameters and results are required |
| 17 | 범용 도구로 하면 위험함: sed로 파일 편집 vs 전용 Edit 도구 | Dangerous with general-purpose tools: editing files with sed vs. a dedicated Edit tool |
| 18 | LLM이 실수하기 쉬움: 잘못된 파라미터를 넣을 가능성이 높은 작업 | LLM-prone to errors: tasks where there is a high chance of passing incorrect parameters |

---
### Section: When General Tools Are Sufficient
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 19 | 종류가 너무 많음: git, npm, pip, docker... 각각 전용 도구를 만들기 비현실적 | Too many varieties: git, npm, pip, docker... creating a specialized tool for each is impractical |
| 20 | 표준 CLI가 이미 잘 동작함: git status는 그 자체로 안정하고 유용 | Standard CLIs already work well: git status is stable and useful on its own |
| 21 | 가끔 사용됨: 프로젝트 초기 한 번만 실행하는 명령어 | Infrequently used: commands that are only run once at the start of a project |

---
### Section: Key Insight - Guiding Tool Selection with Soft Rules
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 22 | 범용 도구가 존재하더라도, 프롬프트(Soft Rules)를 통해 전용 도구를 우선 사용하도록 유도할 수 있습니다. | Even when general-purpose tools exist, you can guide the agent to prioritize specialized tools through prompt-based Soft Rules. |
| 23 | 이것은 Soft Rule이므로 코드가 강제하지 않습니다. | Since this is a Soft Rule, it is not enforced by code. |
| 24 | 하지만 잘 훈련된 LLM은 이 지침을 성실히 따릅니다. | However, a well-trained LLM faithfully follows these guidelines. |
| 25 | 범용 도구를 완전히 차단하지 않으면서도, 더 안전한 전용 도구로 트래픽을 유도하는 전략입니다. | This is a strategy that directs traffic toward safer specialized tools without completely blocking general-purpose tools. |

---
### Section: The Art of Tool Descriptions
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 26 | 도구 설명은 LLM이 도구를 올바르게 사용하는 데 가장 중요한 요소입니다. | The tool description is the most important factor in enabling the LLM to use a tool correctly. |
| 27 | LLM은 도구의 코드 구현이 아니라, 설명(description)을 읽고 사용법을 결정합니다. | The LLM reads the description, not the code implementation, to determine how to use the tool. |

---
### Section: Components of a Good Tool Description
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 28 | 목적(Purpose): 이 도구가 무엇을 하는지 | Purpose: what this tool does |
| 29 | 사용 시나리오(When to use): 언제 이 도구를 선택해야 하는지 | When to use: when to choose this tool |
| 30 | 사용하면 안 되는 경우(When NOT to use): 다른 도구가 더 적합한 경우 | When NOT to use: when another tool is more appropriate |
| 31 | 파라미터 설명: 각 파라미터의 의미, 형식, 제약 | Parameter descriptions: meaning, format, and constraints of each parameter |
| 32 | 주의사항: 실패하기 쉬운 케이스와 해결 방법 | Caveats: cases prone to failure and how to resolve them |

---
### Section: Middleware Pattern - Intercepting Tool Execution
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 33 | 미들웨어는 도구 호출과 실제 실행 사이에 위치하는 검증/변환 레이어입니다. | Middleware is a validation/transformation layer that sits between the tool call and actual execution. |
| 34 | 도구 코드를 수정하지 않고도 공통적인 검증 로직을 적용할 수 있습니다. | It allows you to apply common validation logic without modifying the tool code itself. |

---
### Section: DENY > ALLOW > ASK Pattern
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 35 | 미들웨어의 핵심 검증 로직입니다. | This is the core validation logic of middleware. |
| 36 | 허용 목록에 없는 것의 기본값은 "차단"이 아니라 "사용자에게 묻기(ASK)" 입니다. | The default for anything not on the allow list is not "deny" but "ask the user (ASK)." |
| 37 | 이것은 안전성과 유용성의 균형입니다: | This is a balance between safety and usability: |
| 38 | 모든 것을 차단하면 → 에이전트가 아무것도 못 함 | If you block everything, the agent cannot do anything. |
| 39 | 모든 것을 허용하면 → 위험한 명령이 무방비로 실행됨 | If you allow everything, dangerous commands are executed without protection. |
| 40 | 기본값을 ASK로 → 안전하면서도 사용자가 필요한 것을 승인할 수 있음 | Defaulting to ASK keeps things safe while allowing the user to approve what is needed. |
