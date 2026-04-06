# Agent Harness Practice - Answers and Explanations
## Sentence-by-Sentence Translation Map
---
### Section: Title and Introduction
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Agent Harness 실습 정답 | Agent Harness Practice Answers |
| 2 | 이 문서는 Agent Harness 실습의 8개 TODO에 대한 정답과 해설입니다. | This document provides the answers and explanations for the 8 TODOs in the Agent Harness practice. |
---
### Section: Part 1 - TodoListMiddleware Implementation
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 3 | TodoListMiddleware 구현 | TodoListMiddleware Implementation |
---
### Section: TODO 1 - Todo TypedDict + PlanningState
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 4 | `TypedDict` vs `dataclass` vs `BaseModel` | `TypedDict` vs `dataclass` vs `BaseModel` |
| 5 | `Todo`를 `TypedDict`로 정의하는 이유: | The reason for defining `Todo` as a `TypedDict`: |
| 6 | LangGraph의 state는 딕셔너리 기반으로 동작합니다. | LangGraph's state operates on a dictionary basis. |
| 7 | `TypedDict`는 타입 안전성을 제공하면서도 일반 딕셔너리와 호환됩니다. | `TypedDict` provides type safety while remaining compatible with regular dictionaries. |
| 8 | `dataclass`나 `BaseModel`을 사용하면 직렬화/역직렬화 단계가 추가로 필요합니다. | Using `dataclass` or `BaseModel` requires additional serialization/deserialization steps. |
| 9 | `Literal` 타입으로 상태 제한 | Restricting state with `Literal` type |
| 10 | `str` 대신 `Literal`을 사용하면: | Using `Literal` instead of `str`: |
| 11 | LLM이 tool schema에서 허용된 값 목록을 볼 수 있음 (JSON Schema의 `enum` 필드로 변환) | The LLM can see the list of allowed values in the tool schema (converted to a JSON Schema `enum` field) |
| 12 | 잘못된 상태값("done", "finished" 등)을 방지 | Prevents invalid state values ("done", "finished", etc.) |
| 13 | IDE에서 자동 완성 지원 | Supports IDE autocompletion |
| 14 | `NotRequired`와 `OmitFromInput`의 조합 | The combination of `NotRequired` and `OmitFromInput` |
| 15 | 이 두 annotation은 각각 다른 역할을 합니다: | These two annotations serve different roles: |
| 16 | 초기값 없이 시작 가능 | Can start without an initial value |
| 17 | `agent.invoke({"messages": [...]})` 호출 시 `todos` 키가 없다고 에러 | Error saying `todos` key is missing when calling `agent.invoke({"messages": [...]})` |
| 18 | `invoke()` 입력에서 제외 | Excluded from `invoke()` input |
| 19 | 사용자가 `{"messages": [...], "todos": [...]}` 형태로 직접 전달해야 함 | The user must pass it directly in the form `{"messages": [...], "todos": [...]}` |
| 20 | `OmitFromInput`이 특히 중요합니다 -- `todos`는 agent가 내부적으로 관리하는 상태이지, 사용자가 외부에서 주입하는 값이 아닙니다. | `OmitFromInput` is especially important -- `todos` is state managed internally by the agent, not a value injected externally by the user. |
| 21 | `create_agent`의 input schema 생성 시 이 필드를 건너뜁니다. | This field is skipped when generating `create_agent`'s input schema. |
| 22 | `AgentState`에는 이미 `messages` 필드가 있습니다. | `AgentState` already has a `messages` field. |
| 23 | `PlanningState`가 이를 상속하면서 `todos`를 추가합니다. | `PlanningState` inherits it and adds `todos`. |
| 24 | `create_agent`는 모든 middleware의 `state_schema`를 자동으로 머지하므로, 최종 state는 `messages + todos + files + ...`가 됩니다. | Since `create_agent` automatically merges all middleware's `state_schema`, the final state becomes `messages + todos + files + ...`. |
---
### Section: TODO 2 - _write_todos()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 25 | Tool 동작 함수 | Tool action function |
| 26 | `Command`를 반환하는 이유 | Why it returns a `Command` |
| 27 | 일반 tool은 문자열을 반환합니다: | Regular tools return strings: |
| 28 | 하지만 `write_todos`는 agent state의 `todos` 필드를 업데이트해야 합니다. | But `write_todos` needs to update the `todos` field of the agent state. |
| 29 | 문자열만 반환하면 `messages`에만 추가되고 `todos`는 변하지 않습니다. | If only a string is returned, it is only added to `messages` and `todos` remains unchanged. |
| 30 | `Command(update={...})`를 반환하면 LangGraph의 state reducer를 통해 여러 필드를 동시에 업데이트할 수 있습니다. | Returning `Command(update={...})` allows multiple fields to be updated simultaneously through LangGraph's state reducer. |
| 31 | `messages` 키를 반드시 포함해야 하는 이유 | Why the `messages` key must be included |
| 32 | LLM은 tool 호출 후 반드시 `ToolMessage`를 받아야 합니다 -- 이것이 LLM API의 규약입니다. | The LLM must receive a `ToolMessage` after a tool call -- this is the LLM API convention. |
| 33 | `messages`를 빠뜨리면: | If `messages` is omitted: |
| 34 | LLM이 tool 호출 결과를 볼 수 없음 | The LLM cannot see the tool call result |
| 35 | "tool call without response" 에러 발생 가능 | A "tool call without response" error may occur |
| 36 | LLM이 tool이 실패했다고 판단하고 재시도 | The LLM concludes the tool failed and retries |
| 37 | LLM은 여러 tool을 동시에 호출할 수 있습니다 (parallel tool calls). | The LLM can call multiple tools simultaneously (parallel tool calls). |
| 38 | `tool_call_id`는 "이 응답이 어떤 호출에 대한 것인지"를 연결하는 식별자입니다. | `tool_call_id` is an identifier that links "which call this response corresponds to." |
| 39 | 이것이 없으면 LLM이 어떤 tool call에 대한 응답인지 매칭할 수 없습니다. | Without it, the LLM cannot match which tool call the response belongs to. |
| 40 | `_write_todos`는 I/O 작업이 없습니다 (네트워크, 디스크 접근 없음). | `_write_todos` has no I/O operations (no network or disk access). |
| 41 | 단순히 `Command` 객체를 생성하여 반환할 뿐입니다. | It simply creates and returns a `Command` object. |
| 42 | 이런 경우 async 버전에서 sync 함수를 직접 호출해도 event loop을 블로킹하지 않습니다. | In this case, calling the sync function directly from the async version does not block the event loop. |
---
### Section: TODO 3 - WRITE_TODOS_TOOL_DESCRIPTION
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 43 | Tool 설명 | Tool Description |
| 44 | 이 description이 길어야 하는 이유 | Why this description needs to be long |
| 45 | Tool description의 길이는 도구의 복잡도에 비례해야 합니다. | The length of a tool description should be proportional to the tool's complexity. |
| 46 | `write_todos`는 단순히 데이터를 저장하는 것이 아니라, 특정 규칙에 따라 사용되어야 합니다: | `write_todos` is not simply storing data; it must be used according to specific rules: |
| 47 | 언제 사용하고 언제 사용하지 않는지 | When to use it and when not to |
| 48 | 상태 전이 규칙 (pending -> in_progress -> completed) | State transition rules (pending -> in_progress -> completed) |
| 49 | 동시성 제약 (in_progress는 1개만) | Concurrency constraint (only one in_progress) |
| 50 | 이 규칙들이 description에 없으면, LLM은 자의적으로 판단합니다 -- 모든 작업에 todo를 생성하거나, 여러 task를 동시에 in_progress로 만들거나, 완료되지 않은 task를 completed로 표시합니다. | If these rules are not in the description, the LLM makes arbitrary decisions -- creating todos for every task, making multiple tasks in_progress simultaneously, or marking incomplete tasks as completed. |
| 51 | "When NOT to Use" 섹션의 중요성 | The importance of the "When NOT to Use" section |
| 52 | LLM은 도구가 있으면 사용하려는 경향이 있습니다. | LLMs tend to use a tool if it is available. |
| 53 | "안녕하세요"라는 인사에도 todo를 생성할 수 있습니다. | It might create a todo even for a greeting like "Hello." |
| 54 | "사용하지 말아야 할 때"를 명시하면 불필요한 도구 호출을 줄여 token을 절약하고 응답 속도를 높입니다. | Specifying "when not to use" reduces unnecessary tool calls, saving tokens and improving response speed. |
| 55 | "in_progress는 1개만" 규칙 | The "only one in_progress" rule |
| 56 | 이 규칙이 없으면 LLM이 3개의 task를 모두 in_progress로 만들고 동시에 진행하려 합니다. | Without this rule, the LLM would mark all 3 tasks as in_progress and try to proceed simultaneously. |
| 57 | 하지만 LLM은 실제로 병렬 작업을 할 수 없으므로 -- tool 호출은 순차적 -- 이런 상태는 사용자에게 잘못된 진행 상황을 보여줍니다. | But since the LLM cannot actually work in parallel -- tool calls are sequential -- this state shows incorrect progress to the user. |
| 58 | "교체 방식" 명시 | Specifying "replacement mode" |
| 59 | 이것을 명시하지 않으면 LLM이 변경된 task만 전달하려 합니다: | Without specifying this, the LLM tries to pass only the changed tasks: |
---
### Section: TODO 4 - TodoListMiddleware.__init__()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 60 | 3가지 축 조립 | Assembling the 3 axes |
| 61 | Middleware의 3가지 축이 `__init__`에서 만나는 지점 | The point where Middleware's 3 axes meet in `__init__` |
| 62 | `create_agent`는 middleware 목록을 받아 이 3가지를 자동으로 조합합니다: | `create_agent` receives the middleware list and automatically combines these 3: |
| 63 | `state_schema`들을 머지하여 최종 state 타입 생성 | Merges `state_schema`s to generate the final state type |
| 64 | `self.tools`를 수집하여 LLM에게 제공할 도구 목록 구성 | Collects `self.tools` to build the tool list provided to the LLM |
| 65 | `wrap_model_call`을 체이닝하여 시스템 프롬프트 조립 | Chains `wrap_model_call` to assemble the system prompt |
| 66 | `AgentMiddleware`의 `__init__`은 내부 상태를 초기화합니다. | `AgentMiddleware`'s `__init__` initializes internal state. |
| 67 | 이것을 빠뜨리면 middleware 체이닝이 올바르게 동작하지 않을 수 있습니다. | Omitting this may cause middleware chaining to not work correctly. |
| 68 | 기본적으로 `StructuredTool`은 함수의 type hints에서 schema를 자동 추론합니다. | By default, `StructuredTool` automatically infers the schema from the function's type hints. |
| 69 | 하지만 `_write_todos`에는 `runtime` 파라미터가 있고, 이것은 LLM에게 노출되어서는 안 됩니다 (`runtime`은 시스템이 자동 주입하는 값). | However, `_write_todos` has a `runtime` parameter that should not be exposed to the LLM (`runtime` is a value automatically injected by the system). |
| 70 | `infer_schema=False`로 설정하고 `args_schema=WriteTodosInput`을 명시적으로 제공하면, `runtime`을 제외한 `todos` 파라미터만 LLM에게 노출됩니다. | Setting `infer_schema=False` and explicitly providing `args_schema=WriteTodosInput` exposes only the `todos` parameter to the LLM, excluding `runtime`. |
| 71 | `*` 이후의 파라미터는 반드시 키워드로 전달해야 합니다: | Parameters after `*` must be passed as keywords: |
| 72 | 이 패턴은 실수로 인자 순서를 바꾸는 것을 방지합니다. | This pattern prevents accidentally swapping argument order. |
---
### Section: TODO 5 - wrap_model_call()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 73 | Prompt 주입 | Prompt injection |
| 74 | `content_blocks`로 기존 프롬프트 보존 | Preserving the existing prompt with `content_blocks` |
| 75 | 시스템 메시지는 여러 content block으로 구성될 수 있습니다 (text, image 등). | System messages can consist of multiple content blocks (text, image, etc.). |
| 76 | `content_blocks`를 사용하면 기존 block들을 그대로 유지하면서 새 텍스트를 추가합니다. | Using `content_blocks` keeps existing blocks intact while adding new text. |
| 77 | 만약 `request.system_message.content`(문자열)에 직접 concat하면 non-text block이 손실될 수 있습니다. | If you directly concatenate to `request.system_message.content` (a string), non-text blocks may be lost. |
| 78 | Middleware 체인에서의 프롬프트 누적 | Prompt accumulation in the Middleware chain |
| 79 | 각 middleware가 `request.system_message`에 자신의 프롬프트를 추가하므로, 최종 시스템 메시지는 모든 프롬프트의 합입니다. | Since each middleware appends its own prompt to `request.system_message`, the final system message is the sum of all prompts. |
| 80 | `request`를 직접 수정하지 않고 `override()`로 새 request를 만듭니다. | Instead of modifying `request` directly, a new request is created with `override()`. |
| 81 | 이 패턴은: | This pattern: |
| 82 | 원본 request를 보존하여 디버깅 용이 | Preserves the original request for easier debugging |
| 83 | 다른 middleware가 동일한 request를 참조해도 안전 | Safe even when other middleware references the same request |
| 84 | 함수형 프로그래밍의 immutability 원칙 준수 | Adheres to the immutability principle of functional programming |
---
### Section: Part 2 - Harness Prompting
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 85 | Harness Prompting -- Coding Agent의 행동 규칙 | Harness Prompting -- Behavioral rules for the Coding Agent |
---
### Section: TODO 6 - PHASE 1 Context Interpretation Protocol
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 86 | PHASE 1 -- 컨텍스트 해석 프로토콜 | PHASE 1 -- Context interpretation protocol |
| 87 | 왜 이 순서인가: | Why this order: |
| 88 | 작업 디렉토리 확인 | Verify working directory |
| 89 | 기본 orientation -- LLM이 "어디에 있는지" 추론하지 않고 확인 | Basic orientation -- the LLM confirms "where it is" rather than guessing |
| 90 | 이전 세션 컨텍스트 복구 | Restore previous session context |
| 91 | Context 외부화 -- init.sh가 git log, progress.md, feature_list.json을 보여줌 | Context externalization -- init.sh shows git log, progress.md, and feature_list.json |
| 92 | 앱이 정상인지 확인 | Verify the app is healthy |
| 93 | 안전망 -- 깨진 상태에서 새 기능 추가는 더 큰 문제를 만듦 | Safety net -- adding new features on a broken state creates bigger problems |
| 94 | "추론하게 하지 말고, 읽게 만들어라." | "Don't make it guess -- make it read." |
| 95 | 나쁜 프롬프트: "프로젝트 상태를 확인하세요" -> LLM이 추측 | Bad prompt: "Check the project status" -> LLM guesses |
| 96 | 좋은 프롬프트: "Run `./init.sh`" -> LLM이 실제로 실행하고 출력을 읽음 | Good prompt: "Run `./init.sh`" -> LLM actually executes it and reads the output |
| 97 | `init.sh`는 Cold Start Recovery의 핵심입니다. | `init.sh` is the core of Cold Start Recovery. |
| 98 | 새 세션의 LLM은 이전 세션의 대화 내용을 전혀 모릅니다. | The LLM in a new session has no knowledge of the previous session's conversation. |
| 99 | 하지만 `init.sh`가 git log, progress.md, feature_list.json을 출력하면, LLM은 이 외부 상태를 읽고 현재 프로젝트 상황을 파악할 수 있습니다. | But when `init.sh` outputs git log, progress.md, and feature_list.json, the LLM can read this external state and understand the current project situation. |
---
### Section: TODO 7 - PHASE 2 Work Unit Isolation
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 100 | PHASE 2 -- 작업 단위 격리 | PHASE 2 -- Work unit isolation |
| 101 | 왜 "하나만"인가 -- Compound Reliability: | Why "only one" -- Compound Reliability: |
| 102 | Agent의 각 step 성공률이 95%라고 가정하면: | Assuming each step of the Agent has a 95% success rate: |
| 103 | 여러 feature를 한 세션에서 시도하면 실패 확률이 급격히 증가합니다. | Attempting multiple features in a single session dramatically increases the probability of failure. |
| 104 | 하나의 feature만 작업하고 git commit으로 고정하면, 실패해도 `git revert`로 깨끗한 상태로 돌아갈 수 있습니다. | Working on only one feature and locking it with a git commit means you can return to a clean state with `git revert` even if it fails. |
| 105 | Feature 선택 규칙이 구체적인 이유: | Why the Feature selection rules are specific: |
| 106 | 이 규칙 없이 "적절한 feature를 선택하세요"라고 하면: | Without these rules, saying "select an appropriate feature" would result in: |
| 107 | LLM이 가장 쉬운 feature를 선택 (의존성 있는 feature 건너뛰기) | The LLM selects the easiest feature (skipping features with dependencies) |
| 108 | 이미 완료된 feature를 다시 작업 | Reworking already completed features |
| 109 | low priority feature를 먼저 구현 | Implementing low priority features first |
| 110 | 구체적인 기준을 제시하면 LLM의 선택이 예측 가능해집니다. | Providing specific criteria makes the LLM's choices predictable. |
| 111 | LLM은 코드를 작성한 후 "완료"라고 선언하는 경향이 있습니다. | LLMs tend to declare "done" after writing code. |
| 112 | 하지만 코드 작성과 동작 확인은 다릅니다. | But writing code and verifying it works are different things. |
| 113 | 이 규칙이 E2E 테스트를 강제하여, 실제로 동작하는 코드만 "완료"로 표시되게 합니다. | This rule enforces E2E testing, ensuring only actually working code is marked as "done." |
---
### Section: TODO 8 - PHASE 3 Context Externalization
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 114 | PHASE 3 -- Context 외부화 | PHASE 3 -- Context externalization |
| 115 | 이 순서가 중요한 이유: | Why this order matters: |
| 116 | 다음 세션이 git log와 파일을 읽으면 최신 정보가 있음 | When the next session reads the git log and files, the latest information is there |
| 117 | 다음 세션이 commit을 체크아웃하면 progress.md에 최신 정보가 없음 | When the next session checks out the commit, progress.md does not have the latest information |
| 118 | 왜 file tool을 명시하는가: | Why file tools are specified explicitly: |
| 119 | 이 강조가 없으면 LLM이: | Without this emphasis, the LLM may: |
| 120 | "progress.md를 업데이트했습니다"라고 말만 하고 실제로 파일을 수정하지 않음 | Merely say "I updated progress.md" without actually modifying the file |
| 121 | bash의 `echo >> progress.md`로 시도 (ToolValidationMiddleware가 차단할 수 있음) | Try with bash `echo >> progress.md` (which ToolValidationMiddleware may block) |
| 122 | git commit message에 내용을 넣고 파일 업데이트를 건너뜀 | Put the content in the git commit message and skip the file update |
| 123 | Conventional Commits 형식을 따릅니다. | Follows the Conventional Commits format. |
| 124 | 다음 세션의 LLM이 `git log`를 읽을 때, 각 commit이 어떤 feature와 관련되었는지 즉시 파악할 수 있습니다. | When the next session's LLM reads `git log`, it can immediately identify which feature each commit relates to. |
| 125 | 이것은 다음 세션을 위한 배려입니다. | This is consideration for the next session. |
| 126 | uncommitted changes가 남아있으면 다음 세션의 LLM이 "이 변경은 의도한 것인가 실수인가?" 판단해야 하며, 이는 불필요한 컨텍스트 소비입니다. | If uncommitted changes remain, the next session's LLM must decide "was this change intentional or a mistake?", which is unnecessary context consumption. |
---
### Section: Dynamic Prompt Connection
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 127 | Dynamic Prompt와의 연결 | Connection with Dynamic Prompt |
| 128 | `coding_agent_prompt.py`에는 `CODING_AGENT_SYSTEM_PROMPT` (정적) 외에 `coding_agent_dynamic_prompt` (동적)도 있습니다: | In `coding_agent_prompt.py`, besides the static `CODING_AGENT_SYSTEM_PROMPT`, there is also the dynamic `coding_agent_dynamic_prompt`: |
| 129 | 정적 프롬프트(PHASE 1/2/3 규칙)는 Prompt Caching의 이점을 받습니다 -- 매번 같은 내용이므로 캐시됩니다. | The static prompt (PHASE 1/2/3 rules) benefits from Prompt Caching -- it is cached because the content is the same every time. |
| 130 | 동적 프롬프트(현재 todos, workspace 등)는 매 호출마다 변경되므로 캐시 접두사 뒤에 배치됩니다. | The dynamic prompt (current todos, workspace, etc.) changes with every call, so it is placed after the cache prefix. |
| 131 | Cache 가능한 부분 | Cacheable portion |
| 132 | 매번 변경되는 부분 | Portion that changes every time |
---
### Section: Overall Flow Summary
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 133 | 전체 흐름 요약 | Overall Flow Summary |
| 134 | Session 시작 | Session start |
| 135 | git log, progress.md, feature_list.json 출력 | Output git log, progress.md, feature_list.json |
| 136 | 실패하면 먼저 수정 | Fix first if failure occurs |
| 137 | feature 선택 | Feature selection |
| 138 | 구현 | Implementation |
| 139 | 테스트 | Testing |
| 140 | 매 step 완료 시 status 업데이트 | Update status upon completing each step |
| 141 | git status로 확인 | Verify with git status |
| 142 | Session N 기록 | Session N record |
| 143 | Session 종료 (다음 세션의 init.sh가 이 상태를 읽음) | Session end (the next session's init.sh reads this state) |
