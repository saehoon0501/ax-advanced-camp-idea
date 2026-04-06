# Filesystem Middleware Lab
## Sentence-by-Sentence Translation Map
---
### Section: Title and Problem Statement
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Filesystem Middleware 실습 | Filesystem Middleware Lab |
| 2 | 에이전트가 `npm test`를 실행했습니다. | The agent ran `npm test`. |
| 3 | 테스트 결과가 5,000줄, 50KB입니다. | The test result is 5,000 lines, 50KB. |
| 4 | 이 전체가 `ToolMessage`로 LLM에 돌아가면서 컨텍스트의 25%를 차지합니다. | This entire output goes back to the LLM as a `ToolMessage`, taking up 25% of the context. |
| 5 | 다음 턴에서 에이전트는 테스트 결과에 묻혀 원래 하려던 작업을 잊어버립니다. | On the next turn, the agent gets buried in the test results and forgets the task it was originally working on. |
| 6 | 이 실습에서는 Tool 설계와 Tool Output 관리 개념을 FilesystemMiddleware에서 직접 구현합니다. | In this lab, you will implement Tool design and Tool Output management concepts directly in FilesystemMiddleware. |
| 7 | **구현 파일:** `ax_advanced_class/src/middleware/filesystem_middleware.py` | **Implementation file:** `ax_advanced_class/src/middleware/filesystem_middleware.py` |

---
### Section: Concept-to-Lab Connection
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 8 | 배운 개념과 실습의 연결 | Connection Between Learned Concepts and This Lab |
| 9 | 강의 개념 | Lecture Concept |
| 10 | 이 실습에서 적용하는 방법 | How It Is Applied in This Lab |
| 11 | Specialized vs General Tools | Specialized vs General Tools |
| 12 | `edit_file`(전용) vs `execute`(범용)의 역할 분리 | Role separation between `edit_file` (specialized) vs `execute` (general-purpose) |
| 13 | Tool Description의 기술 | The Art of Tool Descriptions |
| 14 | LLM이 올바르게 도구를 선택하도록 설명 작성 | Write descriptions so the LLM selects the right tool |
| 15 | Soft Rules로 도구 선택 유도 | Guide tool selection with Soft Rules |
| 16 | `wrap_model_call`에서 시스템 프롬프트로 도구 선호도 주입 | Inject tool preferences into the system prompt via `wrap_model_call` |
| 17 | DENY > ALLOW > ASK 패턴 | DENY > ALLOW > ASK pattern |
| 18 | `ToolValidationMiddleware`와의 연계 (이미 구현됨) | Integration with `ToolValidationMiddleware` (already implemented) |
| 19 | Tool Output 크기 제한 전략 | Tool Output size limiting strategy |
| 20 | `wrap_tool_call`에서 대형 결과를 파일로 교체 | Replace large results with files in `wrap_tool_call` |

---
### Section: What We Will Build
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 21 | 우리가 만들 것 | What We Will Build |
| 22 | FilesystemMiddleware의 세 가지 핵심 역할을 구현합니다: | Implement the three core roles of FilesystemMiddleware: |
| 23 | 역할 1: Tool 정의 — LLM이 사용할 도구의 설명과 스키마 | Role 1: Tool definition -- descriptions and schemas for tools the LLM will use |
| 24 | 역할 2: wrap_model_call — LLM 호출 전에 시스템 프롬프트 주입 | Role 2: wrap_model_call -- inject system prompt before the LLM call |
| 25 | 역할 3: wrap_tool_call — Tool 실행 후 대형 결과 처리 | Role 3: wrap_tool_call -- handle large results after Tool execution |

---
### Section: Lab Structure
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 26 | 실습 구조 | Lab Structure |
| 27 | edit_file 도구 설명 작성 | Write the edit_file tool description |
| 28 | Tool Description의 기술 | The Art of Tool Descriptions |
| 29 | 시스템 프롬프트 주입 | System prompt injection |
| 30 | Soft Rules로 도구 선택 유도 | Guide tool selection with Soft Rules |
| 31 | 대형 Tool 결과 처리 | Large Tool result handling |
| 32 | Tool Output 크기 제한 전략 | Tool Output size limiting strategy |

---
### Section: TODO 1 - _get_edit_file_description()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 33 | TODO 1: _get_edit_file_description() — Tool 설명 작성 | TODO 1: _get_edit_file_description() -- Write the Tool Description |
| 34 | 배울 개념: Tool Description의 기술 — LLM은 도구의 코드가 아니라 **설명(description)**을 읽고 사용법을 결정합니다. | Concept to learn: The Art of Tool Descriptions -- the LLM reads the tool's **description**, not its code, to decide how to use it. |
| 35 | `edit_file`은 파일 내 정확한 문자열을 치환하는 **전용 도구**입니다. | `edit_file` is a **specialized tool** that replaces exact strings within a file. |
| 36 | 도구의 실행 로직과 `StructuredTool` 생성은 부모 클래스가 처리합니다. | The parent class handles the tool's execution logic and `StructuredTool` creation. |
| 37 | 여기서는 **설명 문자열만 반환**하면 됩니다. | Here, you only need to **return the description string**. |
| 38 | `self._custom_tool_descriptions` — 커스텀 설명 오버라이드 (있으면 우선 사용) | `self._custom_tool_descriptions` -- custom description override (used first if available) |
| 39 | `EDIT_FILE_TOOL_DESCRIPTION` — 기본 도구 설명 상수 (참고용) | `EDIT_FILE_TOOL_DESCRIPTION` -- default tool description constant (for reference) |
| 40 | 부모 클래스가 반환된 설명으로 `StructuredTool`을 자동 생성합니다 | The parent class automatically creates a `StructuredTool` with the returned description |
| 41 | # TODO 1: edit_file 도구의 설명(description)을 반환하세요 | # TODO 1: Return the description for the edit_file tool |
| 42 | # self._custom_tool_descriptions.get("edit_file")이 있으면 그것을 우선 사용 | # Use self._custom_tool_descriptions.get("edit_file") first if it exists |
| 43 | # 없으면 EDIT_FILE_TOOL_DESCRIPTION 사용 (또는 직접 작성) | # Otherwise use EDIT_FILE_TOOL_DESCRIPTION (or write your own) |
| 44 | # 빈 문자열을 반환하면 edit_file 도구가 생성되지 않습니다. | # Returning an empty string means the edit_file tool will not be created. |
| 45 | 확인 포인트 — 좋은 Tool 설명의 체크리스트: | Verification points -- checklist for a good Tool description: |
| 46 | 목적(Purpose): 이 도구가 무엇을 하는지 | Purpose: What this tool does |
| 47 | 사용 조건(When to use): "Read tool을 먼저 사용해야 함" | When to use: "Must use the Read tool first" |
| 48 | 실패 케이스(Failure): "old_string이 고유하지 않으면 실패" | Failure case: "Fails if old_string is not unique" |
| 49 | 해결 방법(Resolution): "더 많은 컨텍스트를 포함하거나 replace_all 사용" | Resolution: "Include more context or use replace_all" |

---
### Section: TODO 2 - wrap_model_call()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 50 | TODO 2: wrap_model_call() — 시스템 프롬프트로 도구 선택 유도 | TODO 2: wrap_model_call() -- Guide tool selection via system prompt |
| 51 | 배울 개념: Soft Rules — 범용 도구(`execute`)가 존재하더라도, 시스템 프롬프트를 통해 전용 도구를 우선 사용하도록 유도합니다. | Concept to learn: Soft Rules -- even though a general-purpose tool (`execute`) exists, guide the LLM to prefer specialized tools through the system prompt. |
| 52 | 이 메서드는 LLM 호출 직전에 실행되어, 시스템 프롬프트에 도구 사용 가이드라인을 주입합니다. | This method runs just before the LLM call, injecting tool usage guidelines into the system prompt. |
| 53 | 또한 백엔드가 실행(execution)을 지원하지 않으면 `execute` 도구를 필터링합니다. | It also filters out the `execute` tool if the backend does not support execution. |
| 54 | `request.tools` — 현재 사용 가능한 도구 목록 | `request.tools` -- the currently available list of tools |
| 55 | `request.system_message` — 현재 시스템 메시지 | `request.system_message` -- the current system message |
| 56 | `request.override(tools=..., system_message=...)` — request를 수정하는 메서드 | `request.override(tools=..., system_message=...)` -- method to modify the request |
| 57 | `FILESYSTEM_SYSTEM_PROMPT` — 파일 도구 사용 가이드 (Soft Rules 포함) | `FILESYSTEM_SYSTEM_PROMPT` -- file tool usage guide (includes Soft Rules) |
| 58 | `EXECUTION_SYSTEM_PROMPT` — execute 도구 사용 가이드 | `EXECUTION_SYSTEM_PROMPT` -- execute tool usage guide |
| 59 | `append_to_system_message()` — 시스템 메시지에 텍스트를 추가하는 헬퍼 | `append_to_system_message()` -- helper that appends text to the system message |
| 60 | `_supports_execution(backend)` — 백엔드가 실행을 지원하는지 확인 | `_supports_execution(backend)` -- checks if the backend supports execution |
| 61 | # TODO 2: 시스템 프롬프트를 주입하고 도구를 필터링하세요 | # TODO 2: Inject the system prompt and filter tools |
| 62 | # Step 1: execute 도구가 request.tools에 있는지 확인 | # Step 1: Check if the execute tool is in request.tools |
| 63 | # Step 2: 백엔드가 execution을 지원하는지 확인 | # Step 2: Check if the backend supports execution |
| 64 | # execute 도구가 있지만 백엔드가 지원하지 않으면: | # If the execute tool exists but the backend doesn't support it: |
| 65 | # → request.tools에서 execute를 제거 (request.override(tools=filtered)) | # -> Remove execute from request.tools (request.override(tools=filtered)) |
| 66 | # Step 3: 시스템 프롬프트 조립 | # Step 3: Assemble the system prompt |
| 67 | # 기본: FILESYSTEM_SYSTEM_PROMPT (항상 포함) | # Base: FILESYSTEM_SYSTEM_PROMPT (always included) |
| 68 | # 조건부: EXECUTION_SYSTEM_PROMPT (execute가 사용 가능할 때만 추가) | # Conditional: EXECUTION_SYSTEM_PROMPT (added only when execute is available) |
| 69 | # 두 프롬프트를 "\n\n"으로 합치기 | # Join the two prompts with "\n\n" |
| 70 | # 이 프롬프트에 포함된 Soft Rules: | # Soft Rules included in this prompt: |
| 71 | # Step 4: 시스템 메시지에 프롬프트 추가 | # Step 4: Append the prompt to the system message |
| 72 | # Step 5: handler(request)로 다음 미들웨어/LLM에 전달 | # Step 5: Pass to the next middleware/LLM with handler(request) |
| 73 | `execute` 도구가 없거나 백엔드가 지원 안 하면 `EXECUTION_SYSTEM_PROMPT`를 추가하지 않는지 | Check that `EXECUTION_SYSTEM_PROMPT` is not added if the `execute` tool is absent or the backend doesn't support it |
| 74 | `FILESYSTEM_SYSTEM_PROMPT`는 항상 추가되는지 | Check that `FILESYSTEM_SYSTEM_PROMPT` is always added |
| 75 | `self._custom_system_prompt`가 있으면 동적 조립 대신 그것을 사용하는지 | Check that if `self._custom_system_prompt` exists, it is used instead of dynamic assembly |

---
### Section: TODO 3 - wrap_tool_call()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 76 | TODO 3: wrap_tool_call() — 대형 Tool 결과를 파일로 교체 | TODO 3: wrap_tool_call() -- Replace large Tool results with files |
| 77 | 배울 개념: Tool Output 크기 제한 전략 — `npm test` 결과가 50KB면 컨텍스트를 오염시킵니다. | Concept to learn: Tool Output size limiting strategy -- if the `npm test` result is 50KB, it pollutes the context. |
| 78 | 대형 결과를 파일 시스템에 저장하고, LLM에게는 미리보기 + 파일 경로만 전달합니다. | Save large results to the file system, and pass only a preview + file path to the LLM. |
| 79 | 결과가 /large_tool_results/call_123에 저장됨. | The result has been saved to /large_tool_results/call_123. |
| 80 | 미리보기: [처음 5줄 + 마지막 5줄] | Preview: [first 5 lines + last 5 lines] |
| 81 | read_file로 필요한 부분만 읽으세요. | Read only the parts you need with read_file. |
| 82 | `self._tool_token_limit_before_evict` — 토큰 임계값 (기본 20,000) | `self._tool_token_limit_before_evict` -- token threshold (default 20,000) |
| 83 | `TOOLS_EXCLUDED_FROM_EVICTION` — 교체 대상에서 제외할 도구 (`ls`, `glob`, `grep` 등) | `TOOLS_EXCLUDED_FROM_EVICTION` -- tools to exclude from replacement (`ls`, `glob`, `grep`, etc.) |
| 84 | `self._intercept_large_tool_result()` — 대형 결과를 파일로 교체하는 헬퍼 (이미 구현됨) | `self._intercept_large_tool_result()` -- helper that replaces large results with files (already implemented) |
| 85 | # TODO 3: Tool 실행 결과가 너무 크면 파일로 교체하세요 | # TODO 3: Replace Tool execution results with files if they are too large |
| 86 | # Step 1: 교체 로직을 건너뛸지 판단 | # Step 1: Determine whether to skip the replacement logic |
| 87 | # 조건 1: self._tool_token_limit_before_evict가 None이면 → 교체 비활성 | # Condition 1: If self._tool_token_limit_before_evict is None -> replacement disabled |
| 88 | # 조건 2: request.tool_call["name"]이 TOOLS_EXCLUDED_FROM_EVICTION에 있으면 → 건너뛰기 | # Condition 2: If request.tool_call["name"] is in TOOLS_EXCLUDED_FROM_EVICTION -> skip |
| 89 | # 왜 일부 도구를 제외하는가? | # Why are some tools excluded? |
| 90 | # - ls, glob, grep: 자체 truncation이 있음 → 이미 크기가 제한됨 | # - ls, glob, grep: have built-in truncation -> size is already limited |
| 91 | # - read_file: 교체하면 에이전트가 다시 read_file을 시도 → 무한 루프 | # - read_file: replacing it causes the agent to try read_file again -> infinite loop |
| 92 | # - edit_file, write_file: 결과가 항상 짧음 ("Success" 등) | # - edit_file, write_file: results are always short ("Success", etc.) |
| 93 | # 제외 대상이면 → handler(request) 직접 반환 | # If excluded -> return handler(request) directly |
| 94 | # Step 2: Tool 실행 | # Step 2: Execute the Tool |
| 95 | # Step 3: 대형 결과 처리 | # Step 3: Handle large results |
| 96 | # (이 메서드가 토큰 수 체크 → 파일 저장 → 미리보기 생성을 처리) | # (This method handles token count check -> file saving -> preview generation) |
| 97 | `TOOLS_EXCLUDED_FROM_EVICTION`에 포함된 도구는 교체 로직을 건너뛰는지 | Check that tools in `TOOLS_EXCLUDED_FROM_EVICTION` skip the replacement logic |
| 98 | `_tool_token_limit_before_evict`가 `None`이면 모든 결과를 그대로 통과시키는지 | Check that if `_tool_token_limit_before_evict` is `None`, all results pass through as-is |
| 99 | handler를 먼저 호출한 후 결과를 교체하는지 (실행 전이 아니라 **실행 후** 처리) | Check that the handler is called first and results are replaced afterward (processing **after** execution, not before) |

---
### Section: Verification
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 100 | 검증 방법 | Verification Method |
| 101 | 모든 TODO를 구현한 후: | After implementing all TODOs: |

---
### Section: Common Failures and Solutions
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 102 | 흔한 실패와 대처 | Common Failures and Solutions |
| 103 | Agent가 `edit_file` 대신 `bash`로 파일 수정 | Agent modifies files using `bash` instead of `edit_file` |
| 104 | Tool description이 모호하거나 bash가 더 익숙 | Tool description is ambiguous or bash is more familiar |
| 105 | `edit_file` description에 "PREFER this over bash for file modifications" 명시 | Specify "PREFER this over bash for file modifications" in the `edit_file` description |
| 106 | `wrap_tool_call`이 `read_file` 결과를 파일로 교체 | `wrap_tool_call` replaces `read_file` results with a file |
| 107 | TOOLS_EXCLUDED_FROM_EVICTION에 누락 | Missing from TOOLS_EXCLUDED_FROM_EVICTION |
| 108 | `read_file`, `ls`, `glob`, `grep`은 반드시 제외 목록에 포함 | `read_file`, `ls`, `glob`, `grep` must be included in the exclusion list |
| 109 | 대형 결과 미리보기가 너무 짧음 | Large result preview is too short |
| 110 | 미리보기 라인 수가 부족 | Preview line count is insufficient |
| 111 | 미리보기를 첫 50줄 + "... (전체는 {path}에 저장됨)" 형태로 조정 | Adjust the preview to first 50 lines + "... (full output saved to {path})" format |
| 112 | Soft Rules 주입 후 system prompt가 깨짐 | System prompt breaks after Soft Rules injection |
| 113 | content blocks 합성 오류 | Content blocks composition error |
| 114 | `request.system_message.content_blocks`가 None인 경우 빈 리스트로 fallback | Fall back to an empty list if `request.system_message.content_blocks` is None |

---
### Section: Concept Connection Map
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 115 | 배운 개념 → 이 실습에서 구현한 것 | Learned concepts -> What was implemented in this lab |
| 116 | Tool Description의 기술 | The Art of Tool Descriptions |
| 117 | "목적, 사용 시나리오, 주의사항" | "Purpose, usage scenarios, precautions" |
| 118 | edit_file의 설명 문자열 작성 | Write the description string for edit_file |
| 119 | Soft Rules로 도구 선택 유도 | Guide tool selection with Soft Rules |
| 120 | FILESYSTEM_SYSTEM_PROMPT 주입 | Inject FILESYSTEM_SYSTEM_PROMPT |
| 121 | EXECUTION_SYSTEM_PROMPT 조건부 추가 | Conditionally add EXECUTION_SYSTEM_PROMPT |
| 122 | Specialized vs General | Specialized vs General |
| 123 | "전용 도구에 안전장치 내장" | "Built-in safeguards in specialized tools" |
| 124 | 고유성 검증, 읽기 선행 확인 등 | Uniqueness validation, read-before-write check, etc. |
| 125 | Tool Output 크기 제한 | Tool Output size limiting |
| 126 | 대형 결과 → 파일 저장 + 미리보기 | Large results -> file saving + preview |
| 127 | Intermediate Result Pollution | Intermediate Result Pollution |
| 128 | "Tool 결과가 Context를 오염" | "Tool results pollute the Context" |
| 129 | 제외 대상: ls, glob, grep, read_file | Excluded targets: ls, glob, grep, read_file |
