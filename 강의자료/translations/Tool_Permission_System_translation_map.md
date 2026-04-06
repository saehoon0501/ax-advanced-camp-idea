# Tool Permission System
## Sentence-by-Sentence Translation Map
---
### Section: Introduction
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | AI 에이전트는 사용자 대신 코드를 작성하고, 파일을 수정하고 명령어를 실행합니다. | AI agents write code, modify files, and execute commands on behalf of the user. |
| 2 | 이 과정에서 한 가지 근본적인 질문이 등장합니다. | In this process, one fundamental question arises. |
| 3 | AI가 잘못된 판단을 하면 어떻게 막을 것인가? | How do you prevent AI from making wrong decisions? |
| 4 | 전통적인 소프트웨어에서는 'if-else'문 하나로 권한을 통제할 수 있었습니다. | In traditional software, permissions could be controlled with a single if-else statement. |
| 5 | 하지만 AI 에이전트는 자연어를 해석하고 스스로 도구를 선택하는 자율적 시스템입니다. | However, AI agents are autonomous systems that interpret natural language and select tools on their own. |
| 6 | 기존 방식으로는 모든 상황에 대처할 수 없습니다. | Existing approaches cannot handle every situation. |
| 7 | 이 문제를 해결하기 위해 등장한 방법이 Two-Layer Permission System 입니다. | The method that emerged to solve this problem is the Two-Layer Permission System. |
| 8 | 이 글에서는 이 시스템의 핵심인 Soft Rules와 Hard Rules 개념을 살펴봅니다. | In this article, we examine the core concepts of this system: Soft Rules and Hard Rules. |

---
### Section: Overall Architecture
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 9 | AI 에이전트의 행동을 두 개의 독립적인 레이어로 통제합니다. | The behavior of AI agents is controlled by two independent layers. |
| 10 | 핵심 원칙은 간단합니다: | The core principle is simple: |
| 11 | LLM이 "무엇을 할지" 결정하고, 코드가 "할 수 있는지"를 통제한다. | The LLM decides "what to do," and code controls "whether it can." |

---
### Section: Layer 1 - Soft Rules
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 12 | Soft Rules는 시스템 프롬프트에 포함된 지침입니다. | Soft Rules are guidelines included in the system prompt. |
| 13 | 즉, AI에게 전달하는 "이렇게 행동해야 한다"는 안내문입니다. | In other words, they are instructions telling the AI "this is how you should behave." |

---
### Section: Soft Rules - Examples
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 14 | 도구 선택: 'sed' 대신 Edit 도구 사용 - 전용 도구가 더 안전하므로 우선 사용 | Tool selection: use Edit tool instead of sed - prioritize specialized tools as they are safer |
| 15 | 작업 순서: 파일 수정 전 반드시 Read 먼저 - 기존 내용을 확인하고 수정해야 함 | Work order: always Read before modifying a file - verify existing content before making changes |
| 16 | Git 안전: 사용자가 명시적으로 요청하지 않으면 commit 금지 - 의도치 않은 커밋 방지 | Git safety: no commits unless explicitly requested by the user - prevent unintended commits |
| 17 | 경로 관리: 지정된 워크스페이스 내에서만 작업 - 외부 파일 보호 | Path management: work only within the designated workspace - protect external files |
| 18 | 파일 관리: 삭제 전 확인 요청 - 실수로 인한 데이터 손실 방지 | File management: request confirmation before deletion - prevent accidental data loss |
| 19 | 코드 품질: 요청된 변경만 수행, 과도한 리펙토링 금지 - 불필요한 수정 최소화 | Code quality: only make requested changes, no excessive refactoring - minimize unnecessary modifications |

---
### Section: Soft Rules - Strengths
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 20 | 유연성: 상황에 따라 적절히 판단하여 적용할 수 있습니다. | Flexibility: can be applied with appropriate judgment depending on the situation. |
| 21 | 자연어로 표현 가능: 복잡한 조건 분기를 코드로 작성하지 않아도, 자연어 한 줄로 정의할 수 있습니다. | Expressible in natural language: complex conditional logic can be defined in a single line of natural language without writing code. |
| 22 | 확장 용이: 새로운 규칙을 프롬프트에 한 줄 추가하는 것만으로 적용됩니다. | Easy to extend: applied simply by adding a single line to the prompt. |

---
### Section: Soft Rules - Limitations
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 23 | 프롬프트 인젝션 공격에 의해 우회될 수 있습니다. | Can be bypassed by prompt injection attacks. |
| 24 | 모델의 판단 오류로 규칙을 무시할 수 있습니다. | Rules can be ignored due to model judgment errors. |

---
### Section: Layer 2 - Hard Rules
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 25 | 실제 코드로 구현된 제약입니다. | These are constraints implemented in actual code. |
| 26 | AI와 무관하게 시스템 레벨에서 강제 적용됩니다. | They are enforced at the system level regardless of the AI. |

---
### Section: Hard Rules - Examples
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 27 | 명령어 차단: rm -rf/, rm -rf ~, 포크 폭탄 등 - 코드가 패턴 매칭으로 실행 자체를 차단 | Command blocking: rm -rf/, rm -rf ~, fork bombs, etc. - code blocks execution itself via pattern matching |
| 28 | 타임아웃: 최대 600,000ms(10분) - 이 시간을 초과하면 프로세스 강제 종료 | Timeout: maximum 600,000ms (10 minutes) - process is forcibly terminated if this time is exceeded |
| 29 | 출력 제한: 최대 30,000자 - 초과 시 자동 잘림 or 요약 | Output limit: maximum 30,000 characters - automatically truncated or summarized when exceeded |
| 30 | 사용자 승인: 워크스페이스 외부 파일 쓰기 - 승인 팝업이 뜨고, 사용자가 허용 | User approval: writing files outside the workspace - an approval popup appears and the user grants permission |
| 31 | 읽기 선행: Edit/Write 전 반드시 Read 이력 필요 - 읽지 않은 파일 수정 시 에러 반환 | Read-first: Read history required before Edit/Write - returns an error when modifying an unread file |
| 32 | 변경 감지: 마지막 Read 이후 파일이 변경되면 Edit 실패 - Stale 상태으로 인한 작업 오류 방지 | Change detection: Edit fails if the file has changed since the last Read - prevents errors caused by stale state |
| 33 | 대화형 명령: TTY가 없어 대화형 입력 불가 - git rebase -i 같은 명령은 자동 실패 | Interactive commands: no TTY available so interactive input is impossible - commands like git rebase -i automatically fail |

---
### Section: Hard Rules - Strengths and Limitations
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 34 | 강점: 절대적 보장: AI가 무엇을 시도하든 동작합니다. | Strength: absolute guarantee - works regardless of what the AI attempts. |
| 35 | 한계: 유연하지 않음: 모든 가능한 상황을 코드로 미리 정의해야 합니다. | Limitation: inflexible - every possible situation must be predefined in code. |
| 36 | 예외 처리가 어려움: 정당한 사용 케이스까지 차단될 수 있음. | Exception handling is difficult: even legitimate use cases can be blocked. |

---
### Section: Two-Layer Summary
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 37 | Two-Layer Permission System은 AI 에이전트 개발에서 안전성과 유연성의 균형을 달성하기 위한 베스트 프랙티스입니다. | The Two-Layer Permission System is a best practice for achieving a balance between safety and flexibility in AI agent development. |
| 38 | Soft Rules는 AI의 강점인 자연어 이해와 맥락 파악 능력을 활용하여 대부분의 상황을 유연하게 처리합니다. | Soft Rules leverage the AI's strengths in natural language understanding and context awareness to handle most situations flexibly. |
| 39 | Hard Rules는 전통적인 소프트웨어 보안의 확실성으로 치명적인 상황을 물리적으로 차단합니다. | Hard Rules physically block critical situations with the certainty of traditional software security. |
| 40 | 이 두 레이어를 함께 사용함으로써, AI 에이전트는: | By using these two layers together, AI agents can: |
| 41 | 일상적인 작업에서는 사용자 경험을 저해하지 않으면서 | Handle everyday tasks without degrading user experience, |
| 42 | 위험한 상황에서는 확실한 보호를 제공할 수 있습니다. | while providing reliable protection in dangerous situations. |
| 43 | AI 에이전트를 개발할 때, "Soft Rules만으로 충분하다"거나 "모든 것을 Hard Rules로 통제해야 한다"는 극단적인 접근은 피하세요. | When developing AI agents, avoid extreme approaches like "Soft Rules alone are sufficient" or "everything must be controlled with Hard Rules." |
| 44 | 두 레이어의 조합이야말로, 안전하면서도 실용적인 AI 에이전트를 만드는 핵심입니다. | The combination of both layers is the key to building AI agents that are both safe and practical. |
