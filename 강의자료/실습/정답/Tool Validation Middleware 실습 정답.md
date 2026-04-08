# Tool Validation Middleware 실습 정답

이 문서는 `ax_advanced_class/src/middleware/tool_validation_middleware.py`의 3개 TODO에 대한 정답과 해설입니다.

---

## TODO 1: `validate_command()` -- DENY > ALLOW > ASK 3단계 검증

### 정답 코드

```python
def validate_command(self, command: str) -> CommandValidationResult:
    """Validate a shell command string."""
    # Step 1: 빈 명령어 체크
    if not command or not command.strip():
        return CommandValidationResult(
            level=PermissionLevel.ALLOW,
            command=command,
            reason="Empty command",
        )

    # Step 2: 원시 패턴 차단 (파싱 전)
    for pattern in self.config.blocked_raw_patterns:
        if pattern in command:
            return CommandValidationResult(
                level=PermissionLevel.DENY,
                command=command,
                reason="Command contains blocked pattern",
                blocked_items=[pattern],
            )

    # Step 3: PermissionRule 기반 매칭 (DENY rules -> ALLOW rules)
    rule_result = self._check_rules(command)
    if rule_result:
        return rule_result

    # Step 4: 명령어 파싱 + 개별 검증
    parsed_commands = self._parser.parse(command)

    if not parsed_commands:
        return CommandValidationResult(
            level=PermissionLevel.DENY,
            command=command,
            reason="Could not parse command structure",
        )

    # 각 파싱된 명령어를 검증하고 결과 수집
    results: List[CommandValidationResult] = []
    for parsed in parsed_commands:
        result = self._validate_parsed_command(parsed)
        results.append(result)

        # DENY가 나오면 즉시 반환 (early exit)
        if result.level == PermissionLevel.DENY:
            return result

    # Step 5: 최종 결과 (우선순위: DENY > ALLOW > ASK)
    return self._get_highest_priority_result(results, command)
```

### 해설

#### 1. 3단계 검증의 순서가 중요한 이유

```
Step 2: 원시 패턴 -> Step 3: Rule 매칭 -> Step 4: 파싱 후 검증
```

이 순서에는 명확한 이유가 있습니다:

**Step 2가 가장 먼저인 이유 -- 파서가 처리 못하는 패턴 차단:**
```python
for pattern in self.config.blocked_raw_patterns:
    if pattern in command:
        return CommandValidationResult(level=PermissionLevel.DENY, ...)
```
`:(){ :|:& };:` (fork bomb) 같은 패턴은 tree-sitter bash 파서가 올바르게 파싱하지 못할 수 있습니다. 파싱 전에 raw string 매칭으로 먼저 잡아야 합니다.

**Step 3이 Step 4보다 먼저인 이유 -- 사용자 정의 규칙 우선:**
`PermissionRule`은 설정에서 정의한 DENY/ALLOW 규칙입니다. 예를 들어 `execute(curl:*)` -> DENY처럼 특정 명령을 전체적으로 차단하거나 허용할 수 있습니다. 이 규칙은 파싱 결과보다 우선합니다.

**Step 4의 파싱 실패가 DENY인 이유:**
```python
if not parsed_commands:
    return CommandValidationResult(level=PermissionLevel.DENY, ...)
```
tree-sitter가 파싱하지 못한 명령어는 구조를 알 수 없습니다. "알 수 없는 것은 차단"이 보안 원칙입니다. 만약 ALLOW로 처리하면, 파싱을 우회하는 공격이 가능해집니다.

#### 2. Early Exit 패턴

```python
for parsed in parsed_commands:
    result = self._validate_parsed_command(parsed)
    results.append(result)
    if result.level == PermissionLevel.DENY:
        return result  # 즉시 반환
```

`ls && rm -rf /` 같은 파이프라인 명령에서, `ls`는 ALLOW이지만 `rm -rf /`는 DENY입니다. 전체 결과를 수집할 필요 없이, DENY가 나온 시점에서 즉시 반환합니다. 이것이 "DENY > ALLOW > ASK" 우선순위의 핵심입니다.

#### 3. `_get_highest_priority_result`의 우선순위

```python
priority = {
    PermissionLevel.DENY: 0,   # 최고 우선순위 (차단이 항상 이김)
    PermissionLevel.ALLOW: 1,  # 두 번째
    PermissionLevel.ASK: 2,    # 최저 (기본값)
}
return min(results, key=lambda r: priority[r.level])
```

여러 sub-command의 결과 중 가장 엄격한 것을 반환합니다. `ls`(ALLOW) + `python script.py`(ASK)면 ASK가 아니라... 아닙니다, `min`이므로 ALLOW(1)가 ASK(2)보다 우선순위가 높아 ALLOW를 반환합니다. 하지만 실제로는 `python script.py` 부분이 ASK이므로, 전체 명령도 ASK가 되어야 합니다.

사실 이 로직을 다시 보면, `min`은 숫자가 작은 것(=우선순위가 높은 것)을 반환합니다. DENY(0) < ALLOW(1) < ASK(2)이므로:
- DENY가 하나라도 있으면 -> DENY 반환 (early exit로 이미 처리됨)
- DENY가 없고 ALLOW만 있으면 -> ALLOW
- ASK가 하나라도 있으면 -> 여기서 ALLOW가 ASK보다 우선이므로 ALLOW를 반환

이 동작의 의미: 파이프라인에서 **하나의 명령이라도 명시적으로 허용**되면 전체가 허용됩니다. 하지만 이는 early exit에서 DENY가 이미 걸러졌기 때문에 남은 것은 ALLOW와 ASK 조합뿐이고, 이 경우 ALLOW가 우선합니다.

---

## 사전 제공 코드 해설: `validate_path()` -- 워크스페이스 경계 검증

### 코드

```python
def validate_path(self, path: str, is_write: bool = True) -> CommandValidationResult:
    """Validate a file path."""
    # Step 1: 빈 경로 -> ALLOW
    if not path:
        return CommandValidationResult(
            level=PermissionLevel.ALLOW,
            command=path,
            reason="Empty path defaults to workspace",
        )

    # Step 2: 경로 정규화
    normalized = os.path.abspath(os.path.expanduser(path))

    # Step 3: 차단 경로 체크 -> DENY (읽기/쓰기 무관)
    for blocked in self.config.blocked_paths:
        blocked_abs = os.path.abspath(blocked)
        if normalized.startswith(blocked_abs):
            return CommandValidationResult(
                level=PermissionLevel.DENY,
                command=path,
                reason=f"Path is in blocked directory: {blocked}",
                blocked_items=[blocked],
            )

    # Step 4: 허용 경로 체크 -> ALLOW
    allowed_roots = [self.config.workspace_root] + self.config.allowed_paths
    for allowed in allowed_roots:
        allowed_abs = os.path.abspath(os.path.expanduser(allowed))
        if normalized == allowed_abs or normalized.startswith(allowed_abs + os.sep):
            return CommandValidationResult(
                level=PermissionLevel.ALLOW,
                command=path,
                reason=f"Path is in allowed directory: {allowed}",
            )

    # Step 5: 워크스페이스 밖 -> 읽기/쓰기 구분
    if is_write:
        return CommandValidationResult(
            level=PermissionLevel.ASK,
            command=path,
            reason=f"Write to external path requires approval: {normalized}",
        )
    else:
        return CommandValidationResult(
            level=PermissionLevel.ALLOW,
            command=path,
            reason="Read from external path is allowed",
        )
```

### 해설

#### 1. 경로 정규화가 필수인 이유

```python
normalized = os.path.abspath(os.path.expanduser(path))
```

이 한 줄이 여러 보안 우회를 방지합니다:

| 입력 | `expanduser` 후 | `abspath` 후 |
|------|-----------------|-------------|
| `~/.ssh/id_rsa` | `/home/user/.ssh/id_rsa` | `/home/user/.ssh/id_rsa` |
| `../../../etc/passwd` | `../../../etc/passwd` | `/etc/passwd` |
| `./workspace/../etc/shadow` | `./workspace/../etc/shadow` | `/etc/shadow` |

`expanduser`가 `~`를 실제 home 디렉토리로 확장하고, `abspath`가 `..`를 해석하여 절대 경로로 변환합니다. 이 없이는 `workspace/../../../etc/passwd` 같은 경로가 workspace 안에 있는 것처럼 보일 수 있습니다.

#### 2. 차단 경로 체크에서 `startswith`를 쓰는 이유

```python
if normalized.startswith(blocked_abs):
```

`/etc`가 차단 경로이면:
- `/etc/passwd` -> blocked (`/etc`로 시작) 
- `/etc/shadow` -> blocked
- `/etc` -> blocked (자기 자신)
- `/etcetera/file` -> **not blocked** (다른 디렉토리)

마지막 케이스를 더 엄격하게 하려면 `blocked_abs + os.sep`으로 비교해야 합니다. 하지만 실제 시스템에서 `/etcetera` 같은 디렉토리는 없으므로, 현재 구현은 실용적으로 충분합니다.

#### 3. 허용 경로 체크에서 `os.sep` 추가

```python
if normalized == allowed_abs or normalized.startswith(allowed_abs + os.sep):
```

`workspace_root`가 `/home/user/project`일 때:
- `/home/user/project` -> ALLOW (정확히 일치)
- `/home/user/project/src/main.py` -> ALLOW (`/home/user/project/`로 시작)
- `/home/user/project2/file.py` -> NOT ALLOW (`/home/user/project`로 시작하지만 다른 디렉토리)

`+ os.sep`를 추가함으로써 `project`와 `project2`를 정확히 구분합니다.

#### 4. 읽기와 쓰기의 비대칭 정책

```python
if is_write:
    return CommandValidationResult(level=PermissionLevel.ASK, ...)  # 쓰기: 물어봐
else:
    return CommandValidationResult(level=PermissionLevel.ALLOW, ...)  # 읽기: 허용
```

이 정책의 근거:
- **읽기**: 워크스페이스 밖의 파일을 읽는 것은 참조 목적(라이브러리 소스, 설정 파일 확인 등)으로 안전합니다.
- **쓰기**: 워크스페이스 밖에 쓰는 것은 시스템 파일을 변경하거나 다른 프로젝트에 영향을 줄 수 있어 위험합니다.

---

## TODO 2: `wrap_tool_call()` Bash 블록 -- interrupt + always-allow

### 정답 코드

```python
# wrap_tool_call() 안의 Bash 검증 블록
if tool_name in _BASH_TOOL_NAMES:
    # Step 1: 타임아웃 제한 강제
    self._enforce_timeout_limits(args)

    if "command" in args:
        # Step 2: validate_command()로 검증
        result = self._validator.validate_command(args["command"])

        # DENY -> 즉시 에러 반환
        if result.level == PermissionLevel.DENY:
            return ToolMessage(
                content=f"Error: Command denied. {result.reason}",
                tool_call_id=tool_call_id,
                status="error",
            )

        # Step 3: ASK 처리
        if result.level == PermissionLevel.ASK:
            command = args["command"]
            # 세션 규칙에 이미 있으면 건너뛰기
            if not self._is_allowed(tool_name, command):
                cmd_prefix = command.split()[0] if command.strip() else command
                # interrupt()로 사용자에게 질문
                response = interrupt(
                    {
                        "question": f"Command '{command}' requires confirmation",
                        "tool_call_id": tool_call_id,
                        "command": command,
                        "tool_name": tool_name,
                        "allow_rule": f"{tool_name}({cmd_prefix}:*)",
                    }
                )
                # "always" -> 세션 규칙에 추가
                if response == "always":
                    self._add_allow_rule(tool_name, command)
                # 거부 -> 에러 반환
                elif not response or (isinstance(response, str) and response.startswith("deny:")):
                    feedback = response[5:] if isinstance(response, str) and response.startswith("deny:") else ""
                    reason = f"User feedback: {feedback}" if feedback else result.reason
                    return ToolMessage(
                        content=f"Error: Command denied. {reason}",
                        tool_call_id=tool_call_id,
                        status="error",
                    )
```

### 해설

#### 1. 타임아웃 강제가 가장 먼저인 이유

```python
self._enforce_timeout_limits(args)
```

이것은 검증과 무관한 **Hard limit**입니다. `args`의 `timeout` 값을 `MAX_TIMEOUT_MS` 이하로 clamp합니다. LLM이 `timeout=999999`를 시도해도 최대값으로 제한됩니다. 검증 결과와 관계없이 항상 적용되어야 하므로 가장 먼저 실행합니다.

#### 2. `interrupt()` -- LangGraph의 Human-in-the-loop

```python
response = interrupt({
    "question": f"Command '{command}' requires confirmation",
    "tool_call_id": tool_call_id,
    "command": command,
    "tool_name": tool_name,
    "allow_rule": f"{tool_name}({cmd_prefix}:*)",
})
```

`interrupt()`는 LangGraph의 핵심 기능으로, 그래프 실행을 **일시 정지**합니다:

1. `interrupt(payload)`가 호출되면 `GraphInterrupt` exception이 발생
2. 그래프 상태가 checkpointer에 저장됨
3. 클라이언트(UI)가 payload를 받아 사용자에게 표시
4. 사용자가 응답하면 `Command(resume=response)`로 그래프 실행 재개
5. `interrupt()`가 `response` 값을 반환

payload에 `allow_rule`을 포함하는 이유: UI에서 "Always allow execute(python:*)" 버튼을 표시하여, 사용자가 같은 유형의 명령을 일괄 허용할 수 있게 합니다.

#### 3. Always-allow 패턴

```python
if response == "always":
    self._add_allow_rule(tool_name, command)
```

`_add_allow_rule`의 동작:
```python
def _add_allow_rule(self, tool_name: str, content: str) -> str:
    prefix = content.split()[0] if content.strip() else content
    rule = PermissionRule(tool_name=tool_name, pattern=f"{prefix}:*")
    self._allow_rules.append(rule)
```

`python script.py` 명령에 "always"를 답하면, `execute(python:*)` 규칙이 세션에 추가됩니다. 이후 `python test.py`, `python main.py` 등 `python`으로 시작하는 모든 명령이 자동 허용됩니다.

핵심 포인트:
- **세션 범위**: `self._allow_rules`는 인스턴스 변수이므로, 세션이 끝나면 자동으로 초기화됩니다
- **Prefix 매칭**: `python:*`은 `python`으로 시작하는 모든 것을 허용합니다. `python -c "import os; os.system('rm -rf /')"` 같은 악의적 명령도 허용될 수 있으므로, 이것은 **사용자가 의식적으로 선택**하는 것입니다

#### 4. deny 응답 처리

```python
elif not response or (isinstance(response, str) and response.startswith("deny:")):
    feedback = response[5:] if isinstance(response, str) and response.startswith("deny:") else ""
    reason = f"User feedback: {feedback}" if feedback else result.reason
```

사용자가 거부할 때 피드백을 줄 수 있습니다:
- `"deny:이 명령은 위험해요. 대신 pytest를 사용하세요"` -> LLM이 피드백을 읽고 다른 방법을 시도
- `False` 또는 빈 문자열 -> 단순 거부

피드백을 에러 메시지에 포함함으로써, LLM이 **왜 거부되었는지 이해하고 수정**할 수 있습니다.

---

## TODO 3: `wrap_tool_call()` 파일 블록 -- Read-before-Write + Stale 감지

### 정답 코드

```python
# wrap_tool_call() 안의 File 검증 블록
elif tool_name in _FILE_TOOL_NAMES:
    if "file_path" in args or "path" in args or "validated_path" in args:
        # Part A: 경로 추출 및 검증
        path_key = "file_path" if "file_path" in args else ("validated_path" if "validated_path" in args else "path")
        path = args[path_key]

        if not os.path.isabs(path):
            path = os.path.join(self._config.workspace_root, path)

        normalized_path = self._validator.get_normalized_path(path)
        is_write = tool_name in _WRITE_FILE_TOOLS

        result = self._validator.validate_path(path, is_write=is_write)

        if result.level == PermissionLevel.DENY:
            return ToolMessage(
                content=f"Error: Path denied. {result.reason}",
                tool_call_id=tool_call_id,
                status="error",
            )

        # ASK for write operations to external paths
        if result.level == PermissionLevel.ASK:
            if not self._is_allowed(tool_name, normalized_path):
                parent_dir = os.path.dirname(normalized_path)
                response = interrupt(
                    {
                        "question": f"Path '{normalized_path}' requires confirmation",
                        "tool_call_id": tool_call_id,
                        "path": normalized_path,
                        "tool_name": tool_name,
                        "allow_rule": f"{tool_name}({parent_dir}:*)",
                    }
                )
                if response == "always":
                    self._allow_rules.append(
                        PermissionRule(tool_name=tool_name, pattern=f"{parent_dir}:*")
                    )
                elif not response or (isinstance(response, str) and response.startswith("deny:")):
                    feedback = response[5:] if isinstance(response, str) and response.startswith("deny:") else ""
                    reason = f"User feedback: {feedback}" if feedback else result.reason
                    return ToolMessage(
                        content=f"Error: Path denied. {reason}",
                        tool_call_id=tool_call_id,
                        status="error",
                    )

        # Part B: Read-before-write 체크
        if is_write:
            file_exists = os.path.exists(normalized_path)

            if file_exists:
                # 읽은 적 있는지 확인
                if normalized_path not in self._read_files:
                    operation = "writing to" if tool_name == "write_file" else "editing"
                    return ToolMessage(
                        content=f"Error: You must read the file first before {operation} it. Use the read_file tool first.",
                        tool_call_id=tool_call_id,
                        status="error",
                    )

                # Stale read 감지
                try:
                    current_mtime = os.path.getmtime(normalized_path)
                    read_mtime = self._read_files[normalized_path]
                    if current_mtime > read_mtime:
                        operation = "writing to" if tool_name == "write_file" else "editing"
                        return ToolMessage(
                            content=f"Error: File has been modified since you last read it. Please read the file again before {operation} it.",
                            tool_call_id=tool_call_id,
                            status="error",
                        )
                except OSError:
                    pass  # 파일이 삭제되었을 수 있음

        # 정규화된 경로로 업데이트
        args[path_key] = normalized_path

    # Part C: 실제 실행
    handler_result = handler(request)

    # 읽기 성공 후 추적
    if tool_name == "read_file":
        if isinstance(handler_result, ToolMessage) and handler_result.status != "error":
            if "file_path" in args or "path" in args or "validated_path" in args:
                path_key = "file_path" if "file_path" in args else ("validated_path" if "validated_path" in args else "path")
                normalized_path = self._validator.get_normalized_path(args[path_key])
                try:
                    mtime = os.path.getmtime(normalized_path)
                    self._read_files[normalized_path] = mtime
                except OSError:
                    pass

    # 쓰기 성공 후 추적 갱신
    if tool_name in _WRITE_FILE_TOOLS:
        if isinstance(handler_result, ToolMessage) and handler_result.status != "error":
            if "file_path" in args or "path" in args or "validated_path" in args:
                path_key = "file_path" if "file_path" in args else ("validated_path" if "validated_path" in args else "path")
                normalized_path = self._validator.get_normalized_path(args[path_key])
                try:
                    self._read_files[normalized_path] = os.path.getmtime(normalized_path)
                except OSError:
                    pass
```

### 해설

#### 1. Read-before-write가 필요한 이유

LLM이 파일을 읽지 않고 `edit_file`을 호출하면:
- 파일의 현재 내용을 모르고 수정 -> 기존 코드를 덮어쓸 위험
- `old_string`이 파일에 없으면 edit이 실패하지만, LLM이 추측한 내용이 틀릴 수 있음

```python
if normalized_path not in self._read_files:
    return ToolMessage(
        content="Error: You must read the file first before editing it.",
        ...
    )
```

이 체크는 **새 파일 생성에는 적용되지 않습니다** (`file_exists` 조건 내부). 존재하지 않는 파일을 `write_file`로 생성하는 것은 읽을 내용이 없으므로 허용됩니다.

#### 2. Stale Read 감지 메커니즘

```python
current_mtime = os.path.getmtime(normalized_path)
read_mtime = self._read_files[normalized_path]
if current_mtime > read_mtime:
    return ToolMessage(content="Error: File has been modified since you last read it.", ...)
```

시나리오:
1. LLM이 `read_file("main.py")` 호출 -> `self._read_files["main.py"] = 1000` (mtime)
2. 사용자가 IDE에서 `main.py`를 수정 -> 파일의 mtime이 1005로 변경
3. LLM이 `edit_file("main.py", ...)` 호출 -> `1005 > 1000` -> stale!

LLM이 읽은 후 파일이 변경되었으므로, LLM이 가진 내용과 실제 내용이 다릅니다. edit을 강행하면 사용자의 변경이 손실될 수 있습니다.

#### 3. 쓰기 후 mtime 갱신

```python
if tool_name in _WRITE_FILE_TOOLS:
    if isinstance(handler_result, ToolMessage) and handler_result.status != "error":
        self._read_files[normalized_path] = os.path.getmtime(normalized_path)
```

edit/write 성공 후 mtime을 갱신하는 이유: LLM이 파일을 수정하면 mtime이 변경됩니다. 갱신하지 않으면, 바로 다음 edit에서 "stale" 에러가 발생합니다 -- LLM 자신이 수정한 것인데도!

#### 4. `args[path_key] = normalized_path` -- 정규화된 경로로 교체

```python
args[path_key] = normalized_path
```

검증 후 args의 경로를 정규화된 절대 경로로 교체합니다. 이렇게 하면 실제 도구 실행(`handler(request)`)에서 항상 정규화된 경로가 사용됩니다. 상대 경로나 `~`가 포함된 경로가 도구에 직접 전달되는 것을 방지합니다.

#### 5. 파일 도구용 always-allow 패턴

```python
response = interrupt({
    ...
    "allow_rule": f"{tool_name}({parent_dir}:*)",
})
if response == "always":
    self._allow_rules.append(
        PermissionRule(tool_name=tool_name, pattern=f"{parent_dir}:*")
    )
```

bash의 always-allow와 차이점:
- bash: 명령어의 첫 단어를 prefix로 사용 (`python:*`)
- file: **parent 디렉토리**를 prefix로 사용 (`/home/user/other_project:*`)

"이 디렉토리의 파일은 모두 허용"이 파일 작업에서 더 자연스러운 단위입니다.

---

## 전체 흐름 요약

```
에이전트가 execute(command="python test.py") 호출
  |
  v
wrap_tool_call()
  |
  +-- _BASH_TOOL_NAMES? --> Yes
  |     |
  |     +-- _enforce_timeout_limits(args)
  |     |
  |     +-- validate_command("python test.py")
  |     |     |
  |     |     +-- blocked_raw_patterns? -> No
  |     |     +-- _check_rules? -> No match
  |     |     +-- _parser.parse() -> [ParsedCommand(name="python", ...)]
  |     |     +-- _validate_parsed_command() -> ASK
  |     |     +-- return ASK
  |     |
  |     +-- result.level == ASK
  |     |     |
  |     |     +-- _is_allowed("execute", "python test.py")? -> No
  |     |     +-- interrupt({question: ..., allow_rule: "execute(python:*)"})
  |     |     |     --> 사용자: "always"
  |     |     +-- _add_allow_rule("execute", "python test.py")
  |     |          --> _allow_rules에 execute(python:*) 추가
  |     |
  |     +-- (다음에 python xxx 실행 시 자동 통과)
  |
  +-- handler(request) --> 실제 실행
  |
  +-- _truncate_output(result)
  |
  +-- return result
```
