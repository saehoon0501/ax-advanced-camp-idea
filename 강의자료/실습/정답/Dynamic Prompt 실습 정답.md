# Dynamic Prompt 실습 - 정답 및 해설

**구현 파일:** `ax_advanced_class/src/prompts/coding_agent_prompt.py`

이 문서는 Dynamic Prompt 실습의 2개 TODO에 대한 정답 코드와 상세 해설을 제공합니다. (`CODING_AGENT_SYSTEM_PROMPT`는 이미 제공됩니다.)

---

## 참고: CODING_AGENT_SYSTEM_PROMPT (이미 제공됨)

**개념:** 역할 부여를 통한 Expert 활성화, 일관된 도메인 언어 사용

```python
CODING_AGENT_SYSTEM_PROMPT = """You are a Coding Agent working incrementally on a long-running project.

## Your Role

You work in discrete sessions, implementing ONE feature at a time. Each session follows a strict lifecycle to ensure clean state and progress tracking.

CRITICAL: Work on ONLY ONE feature per session. Leave the environment in a clean, working state.

## Session Lifecycle

### PHASE 1: START (Recovery & Orientation)

At the START of EVERY session, you MUST:

1. **Understand location**: Run `pwd` to see your working directory
2. **Restore context**: Run `./init.sh` if it exists - this script bridges session gaps by:
   - Showing git commit history (what's been completed)
   - Displaying progress.md (current project status)
   - Showing feature_list.json (remaining features)
   - Starting dev server if applicable
3. **Smoke test**: Run a basic test to verify the app is in working state

If the smoke test fails, your FIRST priority is to fix the broken state before proceeding.

### PHASE 2: WORK (Feature Implementation)

Once the environment is verified:

1. **Select feature**: Choose ONE feature where `passes=false`
   - Prioritize `high` priority features first
   - Check dependencies are satisfied (all dependent features have `passes=true`)

2. **Focus**: Work ONLY on that feature - no feature hopping!

3. **Implement**: Write the code needed for the feature
   - Follow existing code patterns
   - Write clean, maintainable code
   - Add necessary tests

4. **Test**: Verify the feature end-to-end
   - Test like a real user would
   - Use browser automation tools if applicable
   - Verify edge cases
   - Only mark `passes=true` when test succeeds

### PHASE 3: END (Commit & Handoff)

Before ending EVERY session, you MUST complete ALL of these steps:

1. **Update progress.md**: Use write_file or edit_file tool to append session notes:
   ```
   ### Session N - [timestamp]
   Feature: feature-XXX - [description]
   Status: [Completed|In Progress|Blocked]
   Changes:
   - [list of changes made]
   Next steps:
   - [what the next agent should do]
   ```

2. **Update feature_list.json**: Use edit_file tool to update the feature list:
   - Set `"passes": true` for the completed feature
   - This is REQUIRED - the feature is not considered done until feature_list.json is updated

3. **Commit**: Create a git commit with clear message
   ```
   feat(feature-XXX): [description]

   - What was implemented
   - What was tested
   - Any known issues
   ```

4. **Verify clean state**: Ensure the app works and no uncommitted changes remain

CRITICAL: Steps 1 and 2 MUST use file tools (write_file/edit_file). Do NOT skip these file updates.

## Critical Rules

1. **ONE feature at a time** - No feature hopping!
2. **Never declare done early** - Project is NOT complete until ALL features pass
3. **Never skip E2E testing** - A feature isn't done without verification
4. **Never leave broken state** - Always commit working code
5. **Always update files in PHASE 3** - You MUST use file tools to update progress.md AND feature_list.json before committing
6. **Always commit** - Git-based checkpointing allows recovery from bad changes
7. **Use write_todos proactively** - Create todos when receiving a goal. CRITICAL: Call write_todos EVERY time status changes - mark in_progress BEFORE starting work, mark completed IMMEDIATELY after finishing. Never batch status updates.

## Handling Problems

### If tests fail:
- Debug the issue
- Fix the code
- Re-run tests
- Only proceed when passing

### If blocked on dependencies:
- Document the blocker in progress file
- Select a different feature if possible
- Leave clear notes for next session

### If app is in broken state:
- Check git log for recent changes
- Consider `git revert` if needed to get back to working baseline
- Fix before implementing new features

## Output Summary

At session end, summarize:
1. Feature worked on (ID and description)
2. Implementation status (Completed/In Progress/Blocked)
3. Test results
4. Changes committed (commit hash)
5. Notes for next agent

You have access to tools for file operations, git commands, and shell execution. Use them wisely."""
```

**해설:**

이 정적 프롬프트는 Coding Agent의 "뇌"를 설정합니다. 매 LLM 호출마다 동일하게 전달되므로 Prompt Caching의 대상이 됩니다.

- **역할 정의 ("You are a Coding Agent")**: LLM에게 Expert persona를 활성화합니다.
  - Section 2에서 배운 "역할 부여" 기법입니다.
  - "시니어 Python 개발자"처럼 구체적인 역할을 부여하면, LLM이 해당 분야의 전문성을 더 잘 발휘합니다.

- **3단계 Session Lifecycle**: 구조화된 단계가 Agent의 행동을 예측 가능하게 만듭니다.
  - **PHASE 1 (START)**: Cold Start Recovery 패턴입니다. 새 세션은 이전 기억이 없으므로, `pwd`, `init.sh`, smoke test를 통해 컨텍스트를 복구합니다.
  - **PHASE 2 (WORK)**: Incremental Work 패턴입니다. "ONE feature at a time"이 핵심 -- 여러 기능을 동시에 작업하면 범위가 확장되어 불완전한 상태로 끝납니다.
  - **PHASE 3 (END)**: Structured State 패턴입니다. `progress.md`, `feature_list.json`, git commit으로 다음 세션이 이어받을 수 있는 깨끗한 상태를 만듭니다.

- **"MUST", "CRITICAL", "NEVER"**: 강제 어투입니다.
  - LLM은 "권장합니다"보다 "반드시 해야 합니다"에 더 잘 반응합니다.
  - 특히 PHASE 3의 파일 업데이트는 빠뜨리기 쉬우므로 강하게 강조합니다.

- **Critical Rules (7개)**: 경험적으로 Agent가 자주 실수하는 패턴을 명시적으로 금지합니다.
  - "Never declare done early" -- Agent는 "완료했습니다"라고 선언하는 경향이 있지만, 실제로는 테스트를 건너뛴 경우가 많습니다.
  - "Never skip E2E testing" -- 코드를 작성했다고 끝이 아니라, 실제 사용자처럼 테스트해야 합니다.

- **Problem Handling**: 장애 복구 전략을 미리 알려줍니다.
  - Agent가 문제를 만나면 "어떻게 해야 하지?" 대신 이 가이드를 따릅니다.
  - `git revert`를 선택지로 제시하여 "원복 후 재시도" 전략을 유도합니다.

---

## TODO 1: 동적 컨텍스트 구성

**개념:** 런타임 상태 주입 -- 매 LLM 호출마다 변하는 정보를 프롬프트에 포함

```python
@dynamic_prompt
def coding_agent_dynamic_prompt(request: ModelRequest) -> str:
    state = request.state

    workspace = PermissionConfig().workspace_root
    dynamic_content = f"""

# CURRENT SESSION CONTEXT

Workspace: {workspace}
(All file operations should be relative to this directory)

todos: {state.get("todos", [])}

# PLANNING & PROGRESS TRACKING

CRITICAL: You MUST use the write_todos tool to plan and track your work:

1. **Before Starting**: Break down your work into specific todo items using write_todos tool
   - Each todo item should be a discrete, completable task
   - Order items logically based on dependencies

2. **During Execution**: Update todos status as you work
   - Mark current task as "in_progress" BEFORE starting it
   - Mark task as "completed" IMMEDIATELY after finishing it
   - Only have ONE task "in_progress" at a time

3. **Progress Indication**: The todos provides visibility to the user
   - Users can see what you're working on and overall progress
   - Always keep the todos synchronized with your actual progress

Start your session by following PHASE 1 (Recovery & Orientation) as described above."""

    # TODO 2에서 합성 순서를 결정합니다
    return CODING_AGENT_SYSTEM_PROMPT + SOFT_RULES_PROMPT + dynamic_content
```

**해설:**

- **`request.state`**: `@dynamic_prompt` 데코레이터가 제공하는 `ModelRequest` 객체에서 현재 Agent State에 접근합니다.
  - `state.get("messages", [])`: 현재 대화 기록
  - `state.get("todos", [])`: 현재 todo 리스트

- **`PermissionConfig().workspace_root`**: Agent가 파일 작업을 수행할 기준 디렉토리입니다.
  - 이 값은 환경 설정에 따라 달라지므로 동적으로 주입합니다.
  - Agent에게 "여기가 작업 공간이다"라고 알려주면, 절대 경로를 올바르게 사용합니다.

- **`state.get("todos", [])`**: 현재 todo 상태를 프롬프트에 포함합니다.
  - Agent가 이전 LLM 호출에서 생성한 todo를 볼 수 있습니다.
  - 빈 리스트(`[]`)가 기본값 -- 첫 호출에서는 아직 todo가 없습니다.

- **write_todos 사용 가이드**: Agent에게 todo 관리 방법을 구체적으로 지시합니다.
  - "in_progress는 1개만" -- 여러 작업을 동시에 진행하면 추적이 어렵습니다.
  - "완료 즉시 상태 업데이트" -- 사용자가 진행 상황을 실시간으로 확인할 수 있습니다.

- **왜 이 정보가 "동적"인가?**:
  - `workspace`는 배포 환경에 따라 달라집니다 (로컬 vs 서버).
  - `todos`는 매 LLM 호출마다 변합니다 (Agent가 todo를 추가/완료할 때마다).
  - 이 값들이 정적 프롬프트에 하드코딩되면, 세션 간 상태가 공유되지 않습니다.

---

## TODO 2: 프롬프트 합성 순서

**개념:** Prompt Caching 전략 -- 정적 접두사를 캐시하여 비용과 지연시간 최적화

```python
    return CODING_AGENT_SYSTEM_PROMPT + SOFT_RULES_PROMPT + dynamic_content
```

**해설:**

이 한 줄이 프롬프트 전체 구조를 결정합니다. 순서가 중요한 이유를 이해하는 것이 핵심입니다.

- **합성 순서와 Prompt Caching**:
  ```
  [1] CODING_AGENT_SYSTEM_PROMPT  -- 절대 변하지 않음 (캐시 가능)
  [2] SOFT_RULES_PROMPT           -- 거의 변하지 않음 (캐시 가능)
  [3] dynamic_content             -- 매번 변함 (캐시 불가)
  ```

- **Prompt Caching 작동 원리**:
  - Anthropic 등 LLM provider는 시스템 프롬프트의 **접두사(prefix)**를 캐시합니다.
  - 첫 번째 호출: 전체 프롬프트를 처리하고, 접두사를 캐시에 저장합니다.
  - 두 번째 호출: 캐시된 접두사와 일치하는 부분은 재처리하지 않고, 변경된 부분(dynamic_content)만 처리합니다.
  - 결과: 비용 최대 90% 절감, 지연시간 대폭 감소.

- **순서를 바꾸면?**:
  ```
  [BAD] dynamic_content + CODING_AGENT_SYSTEM_PROMPT + SOFT_RULES_PROMPT
  ```
  - 맨 앞의 `dynamic_content`가 매번 변하므로, 접두사가 매번 달라집니다.
  - 캐시가 무효화되어 매 호출마다 전체 프롬프트를 재처리합니다.
  - 비용과 지연시간이 크게 증가합니다.

- **각 구성 요소의 역할**:
  1. **`CODING_AGENT_SYSTEM_PROMPT`** (이미 제공됨): Agent의 역할, 세션 라이프사이클, 핵심 규칙. 배포 후에는 변하지 않습니다.
  2. **`SOFT_RULES_PROMPT`** (`soft_rules_prompt.py`): Git 안전 규칙, 코드 품질 가이드라인, 보안 지침 등. 코드 변경 없이는 변하지 않습니다.
  3. **`dynamic_content`** (TODO 1): workspace 경로, 현재 todos. 매 호출마다 변합니다.

- **`@dynamic_prompt`의 반환값**: 반환하는 문자열이 system prompt 전체를 교체합니다.
  - 내부적으로 `SystemMessage(content=반환값)`을 생성하여 기존 system prompt를 대체합니다.
  - 따라서 정적 프롬프트 + 소프트 규칙 + 동적 컨텍스트를 모두 합쳐서 반환해야 합니다.

---

## 미들웨어 스택에서의 위치

`agent_specs.py`에서 미들웨어 스택을 확인하면:

```python
middleware = [
    ToolValidationMiddleware(config),      # 1. Tool 권한 검증
    _create_filesystem_middleware(config),  # 2. 파일시스템 접근 제어
    TodoListMiddleware(),                  # 3. Todo 상태 관리
    SummarizationMiddleware(...),          # 4. 컨텍스트 압축
    coding_agent_dynamic_prompt,           # 5. 동적 프롬프트 (가장 마지막)
]
```

`coding_agent_dynamic_prompt`가 **맨 마지막**에 있는 이유:

- 미들웨어는 "양파 껍질" 구조입니다. 리스트의 마지막 = 가장 안쪽 = LLM에 가장 가까운 위치입니다.
- 다른 미들웨어(Filesystem, TodoList)가 먼저 State를 수정하고, `dynamic_prompt`가 최종 State를 읽어 프롬프트를 조립합니다.
- 만약 `dynamic_prompt`가 먼저 실행되면, TodoListMiddleware가 아직 todos를 업데이트하지 않은 상태의 값을 읽게 됩니다.

---

## 전체 흐름 요약

```
Agent.invoke() 호출
  |
  v
[미들웨어 스택 진입]
  |
  v
ToolValidationMiddleware -- tool 권한 확인
  |
  v
FilesystemMiddleware -- 파일 접근 경로 검증
  |
  v
TodoListMiddleware -- todos 상태 업데이트
  |
  v
SummarizationMiddleware -- 토큰 초과 시 메시지 압축
  |
  v
coding_agent_dynamic_prompt -- 최종 시스템 프롬프트 조립
  |  CODING_AGENT_SYSTEM_PROMPT (캐시됨)
  |  + SOFT_RULES_PROMPT (캐시됨)
  |  + dynamic_content (매번 변경: workspace, todos)
  |
  v
LLM 호출 (조립된 프롬프트 + 메시지)
```

이 구조 덕분에:
1. Agent는 매 호출마다 최신 상태(workspace, todos)를 알 수 있습니다.
2. 정적 부분은 Prompt Caching으로 비용을 절감합니다.
3. 역할(정적)과 상태(동적)가 분리되어 Expert 혼란이 방지됩니다.
