# Dynamic Prompt Practice - Answers and Explanations
## Sentence-by-Sentence Translation Map
---
### Section: Title and Introduction
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Dynamic Prompt 실습 - 정답 및 해설 | Dynamic Prompt Practice - Answers and Explanations |
| 2 | 이 문서는 Dynamic Prompt 실습의 2개 TODO에 대한 정답 코드와 상세 해설을 제공합니다. | This document provides the answer code and detailed explanations for the 2 TODOs in the Dynamic Prompt practice. |
| 3 | (`CODING_AGENT_SYSTEM_PROMPT`는 이미 제공됩니다.) | (`CODING_AGENT_SYSTEM_PROMPT` is already provided.) |
---
### Section: Reference - CODING_AGENT_SYSTEM_PROMPT
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 4 | 참고: CODING_AGENT_SYSTEM_PROMPT (이미 제공됨) | Reference: CODING_AGENT_SYSTEM_PROMPT (already provided) |
| 5 | 역할 부여를 통한 Expert 활성화, 일관된 도메인 언어 사용 | Expert activation through role assignment, consistent domain language usage |
| 6 | 이 정적 프롬프트는 Coding Agent의 "뇌"를 설정합니다. | This static prompt sets up the Coding Agent's "brain." |
| 7 | 매 LLM 호출마다 동일하게 전달되므로 Prompt Caching의 대상이 됩니다. | Since it is passed identically with every LLM call, it becomes a candidate for Prompt Caching. |
| 8 | LLM에게 Expert persona를 활성화합니다. | Activates an Expert persona in the LLM. |
| 9 | Section 2에서 배운 "역할 부여" 기법입니다. | This is the "role assignment" technique learned in Section 2. |
| 10 | "시니어 Python 개발자"처럼 구체적인 역할을 부여하면, LLM이 해당 분야의 전문성을 더 잘 발휘합니다. | Assigning a specific role like "senior Python developer" helps the LLM demonstrate greater expertise in that domain. |
| 11 | 구조화된 단계가 Agent의 행동을 예측 가능하게 만듭니다. | Structured phases make the Agent's behavior predictable. |
| 12 | Cold Start Recovery 패턴입니다. | This is the Cold Start Recovery pattern. |
| 13 | 새 세션은 이전 기억이 없으므로, `pwd`, `init.sh`, smoke test를 통해 컨텍스트를 복구합니다. | Since a new session has no prior memory, context is recovered through `pwd`, `init.sh`, and a smoke test. |
| 14 | Incremental Work 패턴입니다. | This is the Incremental Work pattern. |
| 15 | "ONE feature at a time"이 핵심 -- 여러 기능을 동시에 작업하면 범위가 확장되어 불완전한 상태로 끝납니다. | "ONE feature at a time" is the key -- working on multiple features simultaneously causes scope creep and ends in an incomplete state. |
| 16 | Structured State 패턴입니다. | This is the Structured State pattern. |
| 17 | `progress.md`, `feature_list.json`, git commit으로 다음 세션이 이어받을 수 있는 깨끗한 상태를 만듭니다. | Creates a clean state that the next session can pick up from using `progress.md`, `feature_list.json`, and git commit. |
| 18 | 강제 어투입니다. | These are imperative expressions. |
| 19 | LLM은 "권장합니다"보다 "반드시 해야 합니다"에 더 잘 반응합니다. | LLMs respond better to "you must" than to "it is recommended." |
| 20 | 특히 PHASE 3의 파일 업데이트는 빠뜨리기 쉬우므로 강하게 강조합니다. | The PHASE 3 file updates are especially easy to skip, so they are emphasized strongly. |
| 21 | 경험적으로 Agent가 자주 실수하는 패턴을 명시적으로 금지합니다. | Explicitly prohibits patterns that Agents empirically make mistakes on frequently. |
| 22 | Agent는 "완료했습니다"라고 선언하는 경향이 있지만, 실제로는 테스트를 건너뛴 경우가 많습니다. | Agents tend to declare "done," but in practice they often skip testing. |
| 23 | 코드를 작성했다고 끝이 아니라, 실제 사용자처럼 테스트해야 합니다. | Writing code is not the end -- you must test like a real user would. |
| 24 | 장애 복구 전략을 미리 알려줍니다. | Provides failure recovery strategies in advance. |
| 25 | Agent가 문제를 만나면 "어떻게 해야 하지?" 대신 이 가이드를 따릅니다. | When the Agent encounters a problem, it follows this guide instead of wondering "what should I do?" |
| 26 | `git revert`를 선택지로 제시하여 "원복 후 재시도" 전략을 유도합니다. | By offering `git revert` as an option, it encourages a "revert then retry" strategy. |
---
### Section: TODO 1 - Dynamic Context Construction
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 27 | 동적 컨텍스트 구성 | Dynamic context construction |
| 28 | 런타임 상태 주입 -- 매 LLM 호출마다 변하는 정보를 프롬프트에 포함 | Runtime state injection -- including information that changes with every LLM call in the prompt |
| 29 | `@dynamic_prompt` 데코레이터가 제공하는 `ModelRequest` 객체에서 현재 Agent State에 접근합니다. | Accesses the current Agent State from the `ModelRequest` object provided by the `@dynamic_prompt` decorator. |
| 30 | Agent가 파일 작업을 수행할 기준 디렉토리입니다. | This is the base directory for the Agent's file operations. |
| 31 | 이 값은 환경 설정에 따라 달라지므로 동적으로 주입합니다. | Since this value varies depending on the environment configuration, it is injected dynamically. |
| 32 | Agent에게 "여기가 작업 공간이다"라고 알려주면, 절대 경로를 올바르게 사용합니다. | Telling the Agent "this is your workspace" ensures it uses absolute paths correctly. |
| 33 | 현재 todo 상태를 프롬프트에 포함합니다. | Includes the current todo state in the prompt. |
| 34 | Agent가 이전 LLM 호출에서 생성한 todo를 볼 수 있습니다. | The Agent can see todos created in previous LLM calls. |
| 35 | 빈 리스트(`[]`)가 기본값 -- 첫 호출에서는 아직 todo가 없습니다. | An empty list (`[]`) is the default -- there are no todos yet on the first call. |
| 36 | Agent에게 todo 관리 방법을 구체적으로 지시합니다. | Provides the Agent with specific instructions on how to manage todos. |
| 37 | "in_progress는 1개만" -- 여러 작업을 동시에 진행하면 추적이 어렵습니다. | "Only one in_progress" -- tracking becomes difficult when multiple tasks are progressed simultaneously. |
| 38 | "완료 즉시 상태 업데이트" -- 사용자가 진행 상황을 실시간으로 확인할 수 있습니다. | "Update status immediately upon completion" -- users can check progress in real time. |
| 39 | `workspace`는 배포 환경에 따라 달라집니다 (로컬 vs 서버). | `workspace` varies depending on the deployment environment (local vs. server). |
| 40 | `todos`는 매 LLM 호출마다 변합니다 (Agent가 todo를 추가/완료할 때마다). | `todos` changes with every LLM call (each time the Agent adds or completes a todo). |
| 41 | 이 값들이 정적 프롬프트에 하드코딩되면, 세션 간 상태가 공유되지 않습니다. | If these values are hardcoded in the static prompt, state is not shared across sessions. |
---
### Section: TODO 2 - Prompt Composition Order
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 42 | 프롬프트 합성 순서 | Prompt composition order |
| 43 | Prompt Caching 전략 -- 정적 접두사를 캐시하여 비용과 지연시간 최적화 | Prompt Caching strategy -- optimizing cost and latency by caching the static prefix |
| 44 | 이 한 줄이 프롬프트 전체 구조를 결정합니다. | This single line determines the entire prompt structure. |
| 45 | 순서가 중요한 이유를 이해하는 것이 핵심입니다. | Understanding why the order matters is the key point. |
| 46 | 절대 변하지 않음 (캐시 가능) | Never changes (cacheable) |
| 47 | 거의 변하지 않음 (캐시 가능) | Rarely changes (cacheable) |
| 48 | 매번 변함 (캐시 불가) | Changes every time (not cacheable) |
| 49 | Anthropic 등 LLM provider는 시스템 프롬프트의 접두사(prefix)를 캐시합니다. | LLM providers like Anthropic cache the prefix of the system prompt. |
| 50 | 첫 번째 호출: 전체 프롬프트를 처리하고, 접두사를 캐시에 저장합니다. | First call: processes the full prompt and stores the prefix in the cache. |
| 51 | 두 번째 호출: 캐시된 접두사와 일치하는 부분은 재처리하지 않고, 변경된 부분(dynamic_content)만 처리합니다. | Second call: the portion matching the cached prefix is not reprocessed; only the changed portion (dynamic_content) is processed. |
| 52 | 결과: 비용 최대 90% 절감, 지연시간 대폭 감소. | Result: up to 90% cost reduction and significant latency decrease. |
| 53 | 맨 앞의 `dynamic_content`가 매번 변하므로, 접두사가 매번 달라집니다. | Since `dynamic_content` at the beginning changes every time, the prefix differs each time. |
| 54 | 캐시가 무효화되어 매 호출마다 전체 프롬프트를 재처리합니다. | The cache is invalidated and the entire prompt is reprocessed on every call. |
| 55 | 비용과 지연시간이 크게 증가합니다. | Cost and latency increase significantly. |
| 56 | Agent의 역할, 세션 라이프사이클, 핵심 규칙. | The Agent's role, session lifecycle, and core rules. |
| 57 | 배포 후에는 변하지 않습니다. | Does not change after deployment. |
| 58 | Git 안전 규칙, 코드 품질 가이드라인, 보안 지침 등. | Git safety rules, code quality guidelines, security instructions, etc. |
| 59 | 코드 변경 없이는 변하지 않습니다. | Does not change without a code change. |
| 60 | workspace 경로, 현재 todos. | Workspace path, current todos. |
| 61 | 매 호출마다 변합니다. | Changes with every call. |
| 62 | 반환하는 문자열이 system prompt 전체를 교체합니다. | The returned string replaces the entire system prompt. |
| 63 | 내부적으로 `SystemMessage(content=반환값)`을 생성하여 기존 system prompt를 대체합니다. | Internally creates `SystemMessage(content=return_value)` to replace the existing system prompt. |
| 64 | 따라서 정적 프롬프트 + 소프트 규칙 + 동적 컨텍스트를 모두 합쳐서 반환해야 합니다. | Therefore, the static prompt + soft rules + dynamic context must all be combined and returned together. |
---
### Section: Position in Middleware Stack
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 65 | 미들웨어 스택에서의 위치 | Position in the Middleware Stack |
| 66 | `agent_specs.py`에서 미들웨어 스택을 확인하면: | If you check the middleware stack in `agent_specs.py`: |
| 67 | `coding_agent_dynamic_prompt`가 맨 마지막에 있는 이유: | The reason `coding_agent_dynamic_prompt` is at the very end: |
| 68 | 미들웨어는 "양파 껍질" 구조입니다. | Middleware follows an "onion skin" structure. |
| 69 | 리스트의 마지막 = 가장 안쪽 = LLM에 가장 가까운 위치입니다. | The last item in the list = the innermost layer = the position closest to the LLM. |
| 70 | 다른 미들웨어(Filesystem, TodoList)가 먼저 State를 수정하고, `dynamic_prompt`가 최종 State를 읽어 프롬프트를 조립합니다. | Other middleware (Filesystem, TodoList) modifies the State first, then `dynamic_prompt` reads the final State and assembles the prompt. |
| 71 | 만약 `dynamic_prompt`가 먼저 실행되면, TodoListMiddleware가 아직 todos를 업데이트하지 않은 상태의 값을 읽게 됩니다. | If `dynamic_prompt` runs first, it would read the todos value before TodoListMiddleware has updated it. |
---
### Section: Overall Flow Summary
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 72 | 전체 흐름 요약 | Overall Flow Summary |
| 73 | 미들웨어 스택 진입 | Enter middleware stack |
| 74 | tool 권한 확인 | Check tool permissions |
| 75 | 파일 접근 경로 검증 | Validate file access paths |
| 76 | todos 상태 업데이트 | Update todos state |
| 77 | 토큰 초과 시 메시지 압축 | Compress messages when tokens are exceeded |
| 78 | 최종 시스템 프롬프트 조립 | Assemble the final system prompt |
| 79 | 캐시됨 | Cached |
| 80 | 매번 변경: workspace, todos | Changes every time: workspace, todos |
| 81 | LLM 호출 (조립된 프롬프트 + 메시지) | LLM call (assembled prompt + messages) |
| 82 | 이 구조 덕분에: | Thanks to this structure: |
| 83 | Agent는 매 호출마다 최신 상태(workspace, todos)를 알 수 있습니다. | The Agent can know the latest state (workspace, todos) with every call. |
| 84 | 정적 부분은 Prompt Caching으로 비용을 절감합니다. | The static portion reduces cost through Prompt Caching. |
| 85 | 역할(정적)과 상태(동적)가 분리되어 Expert 혼란이 방지됩니다. | Separating role (static) from state (dynamic) prevents Expert confusion. |
