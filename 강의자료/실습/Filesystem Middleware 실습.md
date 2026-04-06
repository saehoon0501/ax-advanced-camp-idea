# Filesystem Middleware 실습

에이전트가 `npm test`를 실행했습니다. 테스트 결과가 5,000줄, 50KB입니다. 이 전체가 `ToolMessage`로 LLM에 돌아가면서 컨텍스트의 25%를 차지합니다. 다음 턴에서 에이전트는 테스트 결과에 묻혀 원래 하려던 작업을 잊어버립니다.

이 실습에서는 Tool 설계와 Tool Output 관리 개념을 FilesystemMiddleware에서 직접 구현합니다.

**구현 파일:** `ax_advanced_class/src/middleware/filesystem_middleware.py`

## 배운 개념과 실습의 연결

| 강의 개념 | 이 실습에서 적용하는 방법 |
|----------|-------------------------|
| Specialized vs General Tools | `edit_file`(전용) vs `execute`(범용)의 역할 분리 |
| Tool Description의 기술 | LLM이 올바르게 도구를 선택하도록 설명 작성 |
| Soft Rules로 도구 선택 유도 | `wrap_model_call`에서 시스템 프롬프트로 도구 선호도 주입 |
| DENY > ALLOW > ASK 패턴 | `ToolValidationMiddleware`와의 연계 (이미 구현됨) |
| Tool Output 크기 제한 전략 | `wrap_tool_call`에서 대형 결과를 파일로 교체 |

## 우리가 만들 것

FilesystemMiddleware의 세 가지 핵심 역할을 구현합니다:

```
역할 1: Tool 정의 — LLM이 사용할 도구의 설명과 스키마
역할 2: wrap_model_call — LLM 호출 전에 시스템 프롬프트 주입
역할 3: wrap_tool_call — Tool 실행 후 대형 결과 처리
```

## 실습 구조

| TODO | 메서드 | 구현할 것 | 대응하는 개념 |
|------|--------|----------|-------------|
| TODO 1 | `_get_edit_file_description()` | edit_file 도구 설명 작성 | Tool Description의 기술 |
| TODO 2 | `wrap_model_call()` | 시스템 프롬프트 주입 | Soft Rules로 도구 선택 유도 |
| TODO 3 | `wrap_tool_call()` | 대형 Tool 결과 처리 | Tool Output 크기 제한 전략 |

---

## TODO 1: _get_edit_file_description() — Tool 설명 작성

**배울 개념:** Tool Description의 기술 — LLM은 도구의 코드가 아니라 **설명(description)**을 읽고 사용법을 결정합니다.

`edit_file`은 파일 내 정확한 문자열을 치환하는 **전용 도구**입니다. 도구의 실행 로직과 `StructuredTool` 생성은 부모 클래스가 처리합니다. 여기서는 **설명 문자열만 반환**하면 됩니다.

**이미 제공된 것:**
- `self._custom_tool_descriptions` — 커스텀 설명 오버라이드 (있으면 우선 사용)
- `EDIT_FILE_TOOL_DESCRIPTION` — 기본 도구 설명 상수 (참고용)
- 부모 클래스가 반환된 설명으로 `StructuredTool`을 자동 생성합니다

**구현할 코드:**

```python
def _get_edit_file_description(self) -> str:
    # TODO 1: edit_file 도구의 설명(description)을 반환하세요
    #
    # self._custom_tool_descriptions.get("edit_file")이 있으면 그것을 우선 사용
    # 없으면 EDIT_FILE_TOOL_DESCRIPTION 사용 (또는 직접 작성)
    #
    # 빈 문자열을 반환하면 edit_file 도구가 생성되지 않습니다.
    return ""
```

**확인 포인트 — 좋은 Tool 설명의 체크리스트:**
- [ ] 목적(Purpose): 이 도구가 무엇을 하는지
- [ ] 사용 조건(When to use): "Read tool을 먼저 사용해야 함"
- [ ] 실패 케이스(Failure): "old_string이 고유하지 않으면 실패"
- [ ] 해결 방법(Resolution): "더 많은 컨텍스트를 포함하거나 replace_all 사용"

---

## TODO 2: wrap_model_call() — 시스템 프롬프트로 도구 선택 유도

**배울 개념:** Soft Rules — 범용 도구(`execute`)가 존재하더라도, 시스템 프롬프트를 통해 전용 도구를 우선 사용하도록 유도합니다.

이 메서드는 LLM 호출 직전에 실행되어, 시스템 프롬프트에 도구 사용 가이드라인을 주입합니다. 또한 백엔드가 실행(execution)을 지원하지 않으면 `execute` 도구를 필터링합니다.

**이미 제공된 것:**
- `request.tools` — 현재 사용 가능한 도구 목록
- `request.system_message` — 현재 시스템 메시지
- `request.override(tools=..., system_message=...)` — request를 수정하는 메서드
- `FILESYSTEM_SYSTEM_PROMPT` — 파일 도구 사용 가이드 (Soft Rules 포함)
- `EXECUTION_SYSTEM_PROMPT` — execute 도구 사용 가이드
- `append_to_system_message()` — 시스템 메시지에 텍스트를 추가하는 헬퍼
- `_supports_execution(backend)` — 백엔드가 실행을 지원하는지 확인

**구현할 코드:**

```python
def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
    # TODO 2: 시스템 프롬프트를 주입하고 도구를 필터링하세요
    #
    # Step 1: execute 도구가 request.tools에 있는지 확인
    #   has_execute_tool = any(tool.name == "execute" for tool in request.tools)
    #
    # Step 2: 백엔드가 execution을 지원하는지 확인
    #   execute 도구가 있지만 백엔드가 지원하지 않으면:
    #   → request.tools에서 execute를 제거 (request.override(tools=filtered))
    #   → has_execute_tool = False로 설정
    #
    # Step 3: 시스템 프롬프트 조립
    #   기본: FILESYSTEM_SYSTEM_PROMPT (항상 포함)
    #   조건부: EXECUTION_SYSTEM_PROMPT (execute가 사용 가능할 때만 추가)
    #   두 프롬프트를 "\n\n"으로 합치기
    #
    #   이 프롬프트에 포함된 Soft Rules:
    #   "AVOID using execute for: find (use glob), grep/rg (use grep)..."
    #   "USE execute for: Git commands, package managers..."
    #
    # Step 4: 시스템 메시지에 프롬프트 추가
    #   new_system = append_to_system_message(request.system_message, system_prompt)
    #   request = request.override(system_message=new_system)
    #
    # Step 5: handler(request)로 다음 미들웨어/LLM에 전달
    #
    return handler(request)
```

**확인 포인트:**
- `execute` 도구가 없거나 백엔드가 지원 안 하면 `EXECUTION_SYSTEM_PROMPT`를 추가하지 않는지
- `FILESYSTEM_SYSTEM_PROMPT`는 항상 추가되는지
- `self._custom_system_prompt`가 있으면 동적 조립 대신 그것을 사용하는지

---

## TODO 3: wrap_tool_call() — 대형 Tool 결과를 파일로 교체

**배울 개념:** Tool Output 크기 제한 전략 — `npm test` 결과가 50KB면 컨텍스트를 오염시킵니다. 대형 결과를 파일 시스템에 저장하고, LLM에게는 미리보기 + 파일 경로만 전달합니다.

```
[Before] ToolMessage: "... 5000줄 테스트 결과 ..." (50KB → 컨텍스트 오염)

[After]  ToolMessage: "결과가 /large_tool_results/call_123에 저장됨.
                       미리보기: [처음 5줄 + 마지막 5줄]
                       read_file로 필요한 부분만 읽으세요." (1KB)
```

**이미 제공된 것:**
- `self._tool_token_limit_before_evict` — 토큰 임계값 (기본 20,000)
- `TOOLS_EXCLUDED_FROM_EVICTION` — 교체 대상에서 제외할 도구 (`ls`, `glob`, `grep` 등)
- `self._intercept_large_tool_result()` — 대형 결과를 파일로 교체하는 헬퍼 (이미 구현됨)

**구현할 코드:**

```python
def wrap_tool_call(self, request: ToolCallRequest, handler) -> ToolMessage | Command:
    # TODO 3: Tool 실행 결과가 너무 크면 파일로 교체하세요
    #
    # Step 1: 교체 로직을 건너뛸지 판단
    #   조건 1: self._tool_token_limit_before_evict가 None이면 → 교체 비활성
    #   조건 2: request.tool_call["name"]이 TOOLS_EXCLUDED_FROM_EVICTION에 있으면 → 건너뛰기
    #
    #   왜 일부 도구를 제외하는가?
    #   - ls, glob, grep: 자체 truncation이 있음 → 이미 크기가 제한됨
    #   - read_file: 교체하면 에이전트가 다시 read_file을 시도 → 무한 루프
    #   - edit_file, write_file: 결과가 항상 짧음 ("Success" 등)
    #
    #   제외 대상이면 → handler(request) 직접 반환
    #
    # Step 2: Tool 실행
    #   tool_result = handler(request)
    #
    # Step 3: 대형 결과 처리
    #   return self._intercept_large_tool_result(tool_result, request.runtime)
    #   (이 메서드가 토큰 수 체크 → 파일 저장 → 미리보기 생성을 처리)
    #
    return handler(request)
```

**확인 포인트:**
- `TOOLS_EXCLUDED_FROM_EVICTION`에 포함된 도구는 교체 로직을 건너뛰는지
- `_tool_token_limit_before_evict`가 `None`이면 모든 결과를 그대로 통과시키는지
- handler를 먼저 호출한 후 결과를 교체하는지 (실행 전이 아니라 **실행 후** 처리)

---

## 검증 방법

모든 TODO를 구현한 후:

```bash
uv run python -c "
from ax_advanced_class.src.middleware.filesystem_middleware import FilesystemMiddleware
from deepagents.backends import LocalShellBackend

# 1. Tool 생성 확인
backend = LocalShellBackend(root_dir='/tmp', inherit_env=True)
mw = FilesystemMiddleware(backend=backend)
tool_names = [t.name for t in mw.tools]
assert 'edit_file' in tool_names, 'edit_file tool missing'
assert 'execute' in tool_names, 'execute tool missing'
print(f'Tools created: {tool_names}')

# 2. edit_file 설명에 핵심 내용이 있는지 확인
edit_tool = next(t for t in mw.tools if t.name == 'edit_file')
desc = edit_tool.description
assert 'old_string' in desc or 'replacement' in desc, 'Missing parameter description'
print(f'edit_file description length: {len(desc)} chars — OK')

print('All checks passed')
"
```

---

## 흔한 실패와 대처

| 증상 | 원인 | 해결 |
|------|------|------|
| Agent가 `edit_file` 대신 `bash`로 파일 수정 | Tool description이 모호하거나 bash가 더 익숙 | `edit_file` description에 "PREFER this over bash for file modifications" 명시 |
| `wrap_tool_call`이 `read_file` 결과를 파일로 교체 | TOOLS_EXCLUDED_FROM_EVICTION에 누락 | `read_file`, `ls`, `glob`, `grep`은 반드시 제외 목록에 포함 |
| 대형 결과 미리보기가 너무 짧음 | 미리보기 라인 수가 부족 | 미리보기를 첫 50줄 + "... (전체는 {path}에 저장됨)" 형태로 조정 |
| Soft Rules 주입 후 system prompt가 깨짐 | content blocks 합성 오류 | `request.system_message.content_blocks`가 None인 경우 빈 리스트로 fallback |

---

## 개념 연결 맵

```
배운 개념  →  이 실습에서 구현한 것
│
├─ Tool Description의 기술 ──────────→ _get_edit_file_description() (TODO 1)
│   "목적, 사용 시나리오, 주의사항"       edit_file의 설명 문자열 작성
│
├─ Soft Rules로 도구 선택 유도 ──────→ wrap_model_call() (TODO 2)
│   "AVOID bash for file ops"            FILESYSTEM_SYSTEM_PROMPT 주입
│   "USE bash for git, npm"              EXECUTION_SYSTEM_PROMPT 조건부 추가
│
├─ Specialized vs General ───────────→ edit_file(전용) vs execute(범용)
│   "전용 도구에 안전장치 내장"           고유성 검증, 읽기 선행 확인 등
│
├─ Tool Output 크기 제한 ───────────→ wrap_tool_call() (TODO 3)
│   "Hard Truncation, Sampling"          대형 결과 → 파일 저장 + 미리보기
│
└─ Intermediate Result Pollution ───→ TOOLS_EXCLUDED_FROM_EVICTION
    "Tool 결과가 Context를 오염"         제외 대상: ls, glob, grep, read_file
```
