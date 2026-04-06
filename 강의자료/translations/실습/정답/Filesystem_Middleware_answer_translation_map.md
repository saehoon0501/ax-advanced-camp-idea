# Filesystem Middleware Lab - Answers and Explanations
## Sentence-by-Sentence Translation Map
---
### Section: Title and Introduction
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Filesystem Middleware 실습 정답 | Filesystem Middleware Lab Answers |
| 2 | 이 문서는 `ax_advanced_class/src/middleware/filesystem_middleware.py`의 3개 TODO에 대한 정답과 해설입니다. | This document provides the answers and explanations for the 3 TODOs in `ax_advanced_class/src/middleware/filesystem_middleware.py`. |
---
### Section: TODO 1 - _get_edit_file_description()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 3 | Tool 설명 작성 | Writing the Tool description |
| 4 | Tool Description이 가장 중요한 이유 | Why Tool Description is the most important |
| 5 | LLM은 함수의 코드를 볼 수 없습니다. | The LLM cannot see the function's code. |
| 6 | LLM이 도구를 선택할 때 읽는 것은 오직 description뿐입니다. | The only thing the LLM reads when selecting a tool is the description. |
| 7 | 이 description은 Tool 설계 가이드의 체크리스트를 모두 충족합니다: | This description satisfies all items in the Tool design guide checklist: |
| 8 | "Performs exact string replacements in files" -- 무엇을 하는지 | "Performs exact string replacements in files" -- what it does |
| 9 | "read the file before editing" -- 사전 조건 | "read the file before editing" -- precondition |
| 10 | "will error if you attempt an edit without reading" -- 실패 시나리오 | "will error if you attempt an edit without reading" -- failure scenario |
| 11 | 왜 설명 문자열만 반환하는가? | Why does it return only the description string? |
| 12 | 도구의 실행 로직(`_sync_edit_file`, `_async_edit_file`)과 `StructuredTool` 생성은 부모 클래스(`FilesystemMiddlewareBase`)가 처리합니다. | The tool's execution logic (`_sync_edit_file`, `_async_edit_file`) and `StructuredTool` creation are handled by the parent class (`FilesystemMiddlewareBase`). |
| 13 | 학생은 "LLM이 이 도구를 올바르게 사용하도록 어떻게 안내할 것인가" 라는 핵심 질문에만 집중합니다. | Students focus solely on the core question: "How do I guide the LLM to use this tool correctly?" |
| 14 | 빈 문자열을 반환하면 edit_file 도구가 생성되지 않습니다 — 설명이 없으면 도구도 없다는 것이 이 설계의 메시지입니다. | Returning an empty string prevents the edit_file tool from being created -- no description means no tool is the design's message. |
| 15 | 사용자가 `FilesystemMiddleware(custom_tool_descriptions={"edit_file": "custom..."})`로 커스텀 설명을 전달하면 그것을 우선 사용합니다. | If a user passes a custom description via `FilesystemMiddleware(custom_tool_descriptions={"edit_file": "custom..."})`, it takes priority. |
| 16 | 없으면 기본 상수(`EDIT_FILE_TOOL_DESCRIPTION`)를 사용합니다. | If absent, the default constant (`EDIT_FILE_TOOL_DESCRIPTION`) is used. |
---
### Section: TODO 2 - wrap_model_call()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 17 | 시스템 프롬프트로 도구 선택 유도 | Guiding tool selection through the system prompt |
| 18 | 두 가지 역할: Tool 필터링 + Soft Rules 주입 | Two roles: Tool filtering + Soft Rules injection |
| 19 | `wrap_model_call`은 LLM 호출 직전에 실행됩니다. | `wrap_model_call` runs just before the LLM call. |
| 20 | 여기서 두 가지를 수행합니다: | It performs two things here: |
| 21 | backend가 `StateBackend`(메모리 전용)인 경우 shell 실행이 불가능합니다. | When the backend is `StateBackend` (memory only), shell execution is not possible. |
| 22 | 이때 `execute` 도구를 아예 목록에서 제거하여 LLM이 호출할 수 없게 만듭니다. | At this point, the `execute` tool is removed entirely from the list so the LLM cannot call it. |
| 23 | 이것은 "존재하지 않는 도구는 호출할 수 없다"는 Hard Rule입니다. | This is a Hard Rule: "a tool that doesn't exist cannot be called." |
| 24 | 이 규칙은 코드로 강제하지 않지만, LLM에게 "file 작업은 전용 도구를 쓰고, bash는 git/npm에만 써라"라고 유도합니다. | This rule is not enforced by code, but guides the LLM to "use dedicated tools for file operations and bash only for git/npm." |
| 25 | 조건부 프롬프트 추가 패턴 | Conditional prompt addition pattern |
| 26 | `execute` 도구가 없는데 사용법 프롬프트를 주입하면 LLM이 혼란스러워합니다 -- "execute를 쓰라고 했는데 도구 목록에 없네?" | If the usage prompt is injected when the `execute` tool does not exist, the LLM gets confused -- "I was told to use execute, but it's not in the tool list?" |
| 27 | 이런 상황을 방지하기 위해, 도구가 실제로 사용 가능할 때만 해당 프롬프트를 추가합니다. | To prevent this situation, the relevant prompt is only added when the tool is actually available. |
| 28 | `request`를 직접 수정하지 않고 `override()`로 새 request를 만듭니다. | Instead of modifying `request` directly, a new request is created using `override()`. |
| 29 | 이 불변 패턴은 middleware 체인에서 중요합니다 -- 다른 middleware가 원본 request를 참조할 수 있기 때문입니다. | This immutable pattern is important in the middleware chain -- other middleware may reference the original request. |
| 30 | 사용자가 `FilesystemMiddleware(system_prompt="custom...")`로 커스텀 프롬프트를 전달하면, 내장 프롬프트 대신 그것을 사용합니다. | If a user passes a custom prompt via `FilesystemMiddleware(system_prompt="custom...")`, it is used instead of the built-in prompt. |
| 31 | 이 패턴은 middleware의 유연성을 보장합니다. | This pattern ensures the middleware's flexibility. |
---
### Section: TODO 3 - wrap_tool_call()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 32 | 대형 Tool 결과를 파일로 교체 | Replacing large Tool results with files |
| 33 | 왜 일부 도구를 제외하는가? | Why are some tools excluded? |
| 34 | 각 도구를 제외하는 이유가 다릅니다: | The reason for excluding each tool differs: |
| 35 | 자체 truncation이 내장됨. | Built-in truncation is included. |
| 36 | 결과가 크면 이미 잘려서 반환됩니다. | If the result is large, it is already truncated before being returned. |
| 37 | 이 경우 "결과가 너무 많으니 더 구체적인 패턴을 사용하라"가 올바른 대응이지, 파일에 저장하는 것이 아닙니다. | In this case, the correct response is "too many results, use a more specific pattern," not saving to a file. |
| 38 | 무한 루프 위험. | Risk of infinite loop. |
| 39 | 결과를 파일로 교체하면, LLM이 그 파일을 다시 `read_file`로 읽으려 하고, 또 교체되고... 이 루프가 발생합니다. | If the result is replaced with a file, the LLM tries to read that file with `read_file` again, which gets replaced again... this loop occurs. |
| 40 | 또한 `read_file`은 이미 `offset`/`limit` pagination을 지원합니다. | Additionally, `read_file` already supports `offset`/`limit` pagination. |
| 41 | 결과가 항상 짧음. | Results are always short. |
| 42 | "Successfully replaced 1 instance(s)" 같은 확인 메시지만 반환하므로 크기 제한이 필요 없습니다. | Only confirmation messages like "Successfully replaced 1 instance(s)" are returned, so no size limit is needed. |
| 43 | "실행 후 처리" 패턴 | "Execute then process" pattern |
| 44 | 핵심은 먼저 도구를 실행하고, 그 결과를 검사한다는 점입니다. | The key point is that the tool is executed first, then the result is inspected. |
| 45 | 실행 전에는 결과 크기를 알 수 없으므로, "실행 후 가로채기(intercept)" 패턴을 사용합니다. | Since the result size is unknown before execution, the "execute then intercept" pattern is used. |
| 46 | 이 헬퍼 메서드는 이미 구현되어 있으며, 내부적으로 다음을 수행합니다: | This helper method is already implemented and internally performs the following: |
| 47 | 결과의 텍스트 크기를 `NUM_CHARS_PER_TOKEN * tool_token_limit_before_evict`와 비교 | Compares the text size of the result against `NUM_CHARS_PER_TOKEN * tool_token_limit_before_evict` |
| 48 | 임계값을 초과하면: | If the threshold is exceeded: |
| 49 | 결과를 `/large_tool_results/<tool_call_id>` 경로에 파일로 저장 | Saves the result as a file at the `/large_tool_results/<tool_call_id>` path |
| 50 | head 5줄 + tail 5줄의 미리보기 생성 | Generates a preview of the first 5 lines and last 5 lines |
| 51 | 원본 `ToolMessage`를 "파일에 저장됨 + 미리보기" 메시지로 교체 | Replaces the original `ToolMessage` with a "saved to file + preview" message |
| 52 | `npm test` 결과 50KB가 컨텍스트의 25%를 차지 | 50KB of `npm test` results occupying 25% of the context |
| 53 | 미리보기 + 파일 경로가 약 1KB만 차지. | Preview + file path occupies only about 1KB. |
| 54 | LLM이 필요한 부분만 `read_file(offset=..., limit=...)`로 읽을 수 있음 | The LLM can read only the needed parts with `read_file(offset=..., limit=...)` |
| 55 | `tool_token_limit_before_evict=None`으로 설정하면 eviction 기능 자체가 비활성화됩니다. | Setting `tool_token_limit_before_evict=None` disables the eviction feature entirely. |
| 56 | 모든 결과가 그대로 LLM에게 전달됩니다. | All results are passed to the LLM as-is. |
| 57 | 이것은 테스트 환경이나 컨텍스트가 충분히 큰 경우에 유용합니다. | This is useful in test environments or when the context is sufficiently large. |
---
### Section: Overall Flow Summary
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 58 | 전체 흐름 요약 | Overall Flow Summary |
| 59 | LLM 호출 전 | Before LLM call |
| 60 | execute 도구가 있고 backend가 미지원? -> 도구 목록에서 제거 | Is the execute tool present and the backend unsupported? -> Remove from tool list |
| 61 | FILESYSTEM_SYSTEM_PROMPT 주입 (항상) | Inject FILESYSTEM_SYSTEM_PROMPT (always) |
| 62 | EXECUTION_SYSTEM_PROMPT 주입 (execute 사용 가능할 때만) | Inject EXECUTION_SYSTEM_PROMPT (only when execute is available) |
| 63 | LLM이 edit_file 호출 (Tool Definition) | LLM calls edit_file (Tool Definition) |
| 64 | file_path 검증 | file_path validation |
| 65 | 결과를 Command 또는 string으로 반환 | Returns result as Command or string |
| 66 | Tool 실행 후 | After Tool execution |
| 67 | 제외 대상 도구? -> 그대로 반환 | Excluded tool? -> Return as-is |
| 68 | 결과 크기가 임계값 초과? -> 파일로 저장 + 미리보기 반환 | Result size exceeds threshold? -> Save to file + return preview |
| 69 | 임계값 이하? -> 그대로 반환 | Below threshold? -> Return as-is |
