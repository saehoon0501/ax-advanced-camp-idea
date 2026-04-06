# Filesystem Middleware 실습 정답

이 문서는 `ax_advanced_class/src/middleware/filesystem_middleware.py`의 3개 TODO에 대한 정답과 해설입니다.

---

## TODO 1: `_get_edit_file_description()` -- Tool 설명 작성

### 정답 코드

```python
def _get_edit_file_description(self) -> str:
    return self._custom_tool_descriptions.get("edit_file") or EDIT_FILE_TOOL_DESCRIPTION
```

### 해설

#### 1. Tool Description이 가장 중요한 이유

LLM은 함수의 코드를 볼 수 없습니다. LLM이 도구를 선택할 때 읽는 것은 오직 **description**뿐입니다. `EDIT_FILE_TOOL_DESCRIPTION`의 내용을 보면:

```python
EDIT_FILE_TOOL_DESCRIPTION = """Performs exact string replacements in files.

Usage:
- You must read the file before editing. This tool will error if you attempt an edit without reading the file first.
- When editing, preserve the exact indentation (tabs/spaces) from the read output. Never include line number prefixes in old_string or new_string.
- ALWAYS prefer editing existing files over creating new ones.
- Only use emojis if the user explicitly requests it."""
```

이 description은 Tool 설계 가이드의 체크리스트를 모두 충족합니다:
- **목적(Purpose)**: "Performs exact string replacements in files" -- 무엇을 하는지
- **사용 조건(When to use)**: "read the file before editing" -- 사전 조건
- **실패 케이스(Failure)**: "will error if you attempt an edit without reading" -- 실패 시나리오

#### 2. 왜 설명 문자열만 반환하는가?

도구의 실행 로직(`_sync_edit_file`, `_async_edit_file`)과 `StructuredTool` 생성은 부모 클래스(`FilesystemMiddlewareBase`)가 처리합니다. 학생은 **"LLM이 이 도구를 올바르게 사용하도록 어떻게 안내할 것인가"** 라는 핵심 질문에만 집중합니다.

빈 문자열을 반환하면 edit_file 도구가 생성되지 않습니다 — 설명이 없으면 도구도 없다는 것이 이 설계의 메시지입니다.

#### 3. `_custom_tool_descriptions` 우선 체크

```python
self._custom_tool_descriptions.get("edit_file") or EDIT_FILE_TOOL_DESCRIPTION
```

사용자가 `FilesystemMiddleware(custom_tool_descriptions={"edit_file": "custom..."})`로 커스텀 설명을 전달하면 그것을 우선 사용합니다. 없으면 기본 상수(`EDIT_FILE_TOOL_DESCRIPTION`)를 사용합니다.

---

## TODO 2: `wrap_model_call()` -- 시스템 프롬프트로 도구 선택 유도

### 정답 코드

```python
def wrap_model_call(
    self,
    request: ModelRequest[ContextT],
    handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
) -> ModelResponse[ResponseT]:
    # Step 1: execute 도구가 request.tools에 있는지 확인
    has_execute_tool = any(
        (tool.name if hasattr(tool, "name") else tool.get("name")) == "execute"
        for tool in request.tools
    )

    backend_supports_execution = False
    if has_execute_tool:
        # Step 2: backend가 execution을 지원하는지 확인
        backend = self._get_backend(request.runtime)
        backend_supports_execution = _supports_execution(backend)

        # 지원하지 않으면 execute 도구를 목록에서 제거
        if not backend_supports_execution:
            filtered_tools = [
                tool for tool in request.tools
                if (tool.name if hasattr(tool, "name") else tool.get("name")) != "execute"
            ]
            request = request.override(tools=filtered_tools)
            has_execute_tool = False

    # Step 3: 시스템 프롬프트 조립
    if self._custom_system_prompt is not None:
        system_prompt = self._custom_system_prompt
    else:
        prompt_parts = [FILESYSTEM_SYSTEM_PROMPT]

        # execute가 사용 가능할 때만 EXECUTION_SYSTEM_PROMPT 추가
        if has_execute_tool and backend_supports_execution:
            prompt_parts.append(EXECUTION_SYSTEM_PROMPT)

        system_prompt = "\n\n".join(prompt_parts).strip()

    # Step 4: 시스템 메시지에 프롬프트 추가
    if system_prompt:
        new_system_message = append_to_system_message(request.system_message, system_prompt)
        request = request.override(system_message=new_system_message)

    # Step 5: 다음 middleware/LLM에 전달
    return handler(request)
```

### 해설

#### 1. 두 가지 역할: Tool 필터링 + Soft Rules 주입

`wrap_model_call`은 LLM 호출 **직전에** 실행됩니다. 여기서 두 가지를 수행합니다:

**역할 A -- Tool 필터링 (Hard Rule):**
```python
if not backend_supports_execution:
    filtered_tools = [t for t in request.tools if t.name != "execute"]
    request = request.override(tools=filtered_tools)
```
backend가 `StateBackend`(메모리 전용)인 경우 shell 실행이 불가능합니다. 이때 `execute` 도구를 아예 목록에서 제거하여 LLM이 호출할 수 없게 만듭니다. 이것은 "존재하지 않는 도구는 호출할 수 없다"는 Hard Rule입니다.

**역할 B -- Soft Rules 주입:**
```python
prompt_parts = [FILESYSTEM_SYSTEM_PROMPT]
```
`FILESYSTEM_SYSTEM_PROMPT`에 포함된 핵심 Soft Rule:
```
AVOID using execute for: find (use glob), grep/rg (use grep), cat/head/tail (use read_file)...
USE execute for: Git commands, package managers (npm, pip, uv), running scripts/tests
```
이 규칙은 코드로 강제하지 않지만, LLM에게 "file 작업은 전용 도구를 쓰고, bash는 git/npm에만 써라"라고 유도합니다.

#### 2. 조건부 프롬프트 추가 패턴

```python
if has_execute_tool and backend_supports_execution:
    prompt_parts.append(EXECUTION_SYSTEM_PROMPT)
```

`execute` 도구가 없는데 사용법 프롬프트를 주입하면 LLM이 혼란스러워합니다 -- "execute를 쓰라고 했는데 도구 목록에 없네?" 이런 상황을 방지하기 위해, 도구가 **실제로 사용 가능할 때만** 해당 프롬프트를 추가합니다.

#### 3. `request.override()` -- 불변(Immutable) 패턴

```python
request = request.override(system_message=new_system_message)
```

`request`를 직접 수정하지 않고 `override()`로 새 request를 만듭니다. 이 불변 패턴은 middleware 체인에서 중요합니다 -- 다른 middleware가 원본 request를 참조할 수 있기 때문입니다.

#### 4. `self._custom_system_prompt` 우선 체크

```python
if self._custom_system_prompt is not None:
    system_prompt = self._custom_system_prompt
else:
    # 동적 조립
```

사용자가 `FilesystemMiddleware(system_prompt="custom...")`로 커스텀 프롬프트를 전달하면, 내장 프롬프트 대신 그것을 사용합니다. 이 패턴은 middleware의 유연성을 보장합니다.

---

## TODO 3: `wrap_tool_call()` -- 대형 Tool 결과를 파일로 교체

### 정답 코드

```python
def wrap_tool_call(
    self,
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    # Step 1: 교체 로직을 건너뛸지 판단
    if self._tool_token_limit_before_evict is None or request.tool_call["name"] in TOOLS_EXCLUDED_FROM_EVICTION:
        return handler(request)

    # Step 2: Tool 실행
    tool_result = handler(request)

    # Step 3: 대형 결과 처리
    return self._intercept_large_tool_result(tool_result, request.runtime)
```

### 해설

#### 1. 왜 일부 도구를 제외하는가?

```python
TOOLS_EXCLUDED_FROM_EVICTION = ("ls", "glob", "grep", "read_file", "edit_file", "write_file")
```

각 도구를 제외하는 이유가 다릅니다:

| 도구 | 제외 이유 |
|------|----------|
| `ls`, `glob`, `grep` | **자체 truncation이 내장됨.** 결과가 크면 이미 잘려서 반환됩니다. 이 경우 "결과가 너무 많으니 더 구체적인 패턴을 사용하라"가 올바른 대응이지, 파일에 저장하는 것이 아닙니다. |
| `read_file` | **무한 루프 위험.** 결과를 파일로 교체하면, LLM이 그 파일을 다시 `read_file`로 읽으려 하고, 또 교체되고... 이 루프가 발생합니다. 또한 `read_file`은 이미 `offset`/`limit` pagination을 지원합니다. |
| `edit_file`, `write_file` | **결과가 항상 짧음.** "Successfully replaced 1 instance(s)" 같은 확인 메시지만 반환하므로 크기 제한이 필요 없습니다. |

#### 2. "실행 후 처리" 패턴

```python
tool_result = handler(request)  # 먼저 실행
return self._intercept_large_tool_result(tool_result, request.runtime)  # 결과 검사
```

핵심은 **먼저 도구를 실행하고, 그 결과를 검사**한다는 점입니다. 실행 전에는 결과 크기를 알 수 없으므로, "실행 후 가로채기(intercept)" 패턴을 사용합니다.

#### 3. `_intercept_large_tool_result`가 하는 일

이 헬퍼 메서드는 이미 구현되어 있으며, 내부적으로 다음을 수행합니다:

1. 결과의 텍스트 크기를 `NUM_CHARS_PER_TOKEN * tool_token_limit_before_evict`와 비교
2. 임계값을 초과하면:
   - 결과를 `/large_tool_results/<tool_call_id>` 경로에 파일로 저장
   - head 5줄 + tail 5줄의 미리보기 생성
   - 원본 `ToolMessage`를 "파일에 저장됨 + 미리보기" 메시지로 교체

이 전략의 효과:
- **Before**: `npm test` 결과 50KB가 컨텍스트의 25%를 차지
- **After**: 미리보기 + 파일 경로가 약 1KB만 차지. LLM이 필요한 부분만 `read_file(offset=..., limit=...)`로 읽을 수 있음

#### 4. `None` 체크의 의미

```python
if self._tool_token_limit_before_evict is None:
    return handler(request)
```

`tool_token_limit_before_evict=None`으로 설정하면 eviction 기능 자체가 비활성화됩니다. 모든 결과가 그대로 LLM에게 전달됩니다. 이것은 테스트 환경이나 컨텍스트가 충분히 큰 경우에 유용합니다.

---

## 전체 흐름 요약

```
LLM 호출 전 (wrap_model_call)
  1. execute 도구가 있고 backend가 미지원? -> 도구 목록에서 제거
  2. FILESYSTEM_SYSTEM_PROMPT 주입 (항상)
  3. EXECUTION_SYSTEM_PROMPT 주입 (execute 사용 가능할 때만)
  4. -> handler(request) -> LLM 호출

LLM이 edit_file 호출 (Tool Definition)
  1. file_path 검증 (validate_path)
  2. backend.edit() 실행
  3. 결과를 Command 또는 string으로 반환

Tool 실행 후 (wrap_tool_call)
  1. 제외 대상 도구? -> 그대로 반환
  2. 결과 크기가 임계값 초과? -> 파일로 저장 + 미리보기 반환
  3. 임계값 이하? -> 그대로 반환
```
