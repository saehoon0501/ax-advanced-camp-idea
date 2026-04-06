# Tool Validation Middleware 실습

사용자가 에이전트에게 "테스트 파일 전부 삭제해줘"라고 요청합니다. 에이전트는 `rm -rf test_*`를 실행하려 합니다. 아무런 검증 없이 이 명령이 실행된다면?

이 실습에서는 **Two-Layer Permission System**의 **Hard Rules 레이어**를 직접 구현합니다. Soft Rules(프롬프트 기반)는 이미 시스템 프롬프트에 포함되어 있고, 여기서는 코드로 강제하는 검증 미들웨어를 만듭니다.

**구현 파일:** `ax_advanced_class/src/middleware/tool_validation_middleware.py`

## 배운 개념과 실습의 연결

| 개념 | 이 실습에서 적용하는 방법 |
|----------------------------|-------------------------|
| DENY > ALLOW > ASK 패턴 | `validate_command()`에서 3단��� 검증 로직 구현 |
| 경로 기반 권한 제어 | `validate_path()`에서 워크스페이스 경계 검증 |
| Human-in-the-loop (ASK) | `interrupt()`로 사용자 승인 UI + always-allow 패턴 |
| 읽기 선행 확인 | `wrap_tool_call()`에�� read-before-write 체크 |
| Stale Read 감지 | 파일 수정 시간 비교로 동시 편집 방지 |

## 우리가 만들 것

```
에이전트가 Tool 호출 요청
  ↓
┌─ wrap_tool_call() ─────────────────────────────────┐
│                                                      │
│  Bash 명령? ──→ validate_command()                   │
│                  ├─ DENY? → 에러 반환 (차단)          │
│                  ├─ ALLOW? → 통과                     │
│                  └─ ASK? → interrupt() (사용자에게 질문)│
│                                                      │
│  파일 도구? ──→ validate_path()                       │
│                  ├─ 차단 경로? → DENY                  │
│                  ├─ 워크스페이스 안? → ALLOW            │
│                  └─ 밖에 쓰기? → ASK                   │
│                                                      │
│  쓰기 도구? ──→ read-before-write 체크                │
│                  ├─ 읽은 적 없는 파일? → 에러           │
│                  └�� 읽은 후 변경됨? → 에러 (stale)      │
│                                                      │
│  모든 검증 통과 → handler(request) → 실제 실행          │
└──────────────────────────────────────────────────────┘
```

## 실습 구조

3개의 TODO를 순서대로 구현합니다.

| TODO | 메서드 | 구현할 것 | 대응하는 개념 |
|------|--------|----------|-------------|
| TODO 1 | `validate_command()` | DENY → ALLOW → ASK 3단계 검증 | DENY > ALLOW > ASK 패턴 |
| TODO 2 | `wrap_tool_call()` bash 블록 | interrupt + always-allow | Human-in-the-loop |
| TODO 3 | `wrap_tool_call()` 파일 블록 | read-before-write + stale 감지 | 파일 안전 장치 |

---

## 사전 제공 코드

TODO 1-3을 구현하기 전에, `validate_path()`의 구현을 먼저 읽으세요. TODO 2, 3에서 이 함수를 호출합니다.

### validate_path() — 워크스페이스 경계 검증

경로 기반 권한 — 워크스페이스 안은 자유롭게, 밖은 제한적으로:

```
/etc/passwd          → DENY (시스템 경로, 항상 차단)
./workspace/src/     → ALLOW (워크스페이스 안)
/home/user/other.py  → 읽기: ALLOW, 쓰기: ASK
```

```python
def validate_path(self, path: str, is_write: bool = True) -> CommandValidationResult:
    # Step 1: 빈 경로 → ALLOW (기본값은 워크스페이스)
    if not path or not path.strip():
        return CommandValidationResult(level=PermissionLevel.ALLOW, ...)

    # Step 2: 경로 정규화 — symlink 공격 방지
    normalized = os.path.abspath(os.path.expanduser(path))

    # Step 3: DENY — 차단 경로 체크 (읽기/쓰기 무관)
    for blocked in self.config.blocked_paths:
        if normalized.startswith(os.path.abspath(os.path.expanduser(blocked))):
            return CommandValidationResult(level=PermissionLevel.DENY, ...)

    # Step 4: ALLOW — 워크스페이스 + 허용 경로 체크
    for allowed in [self.config.workspace_root] + self.config.allowed_paths:
        if normalized.startswith(os.path.abspath(allowed)):
            return CommandValidationResult(level=PermissionLevel.ALLOW, ...)

    # Step 5: 워크스페이스 밖 → 읽기는 ALLOW, 쓰기는 ASK
    if not is_write:
        return CommandValidationResult(level=PermissionLevel.ALLOW, ...)
    return CommandValidationResult(level=PermissionLevel.ASK, ...)
```

**이해 포인트:**
- **`os.path.abspath(os.path.expanduser(...))`** — `~/.ssh`를 `/home/user/.ssh`로 정규화. symlink 우회 공격을 방지
- **DENY가 ALLOW보다 먼저** — `blocked_paths`를 먼저 체크하므로, 워크스페이스 안에 있어도 blocked 경로면 차단
- **읽기/쓰기 구분** — 워크스페이스 밖 읽기는 허용 (로그 파일 확인 등), 쓰기만 ASK

---

## TODO 1: validate_command() — DENY > ALLOW > ASK 3단계 검증

**배울 개념:** Hard Rules의 핵심 로직 — 모든 bash 명령은 이 3단계를 거칩니다.

```
1. DENY 목록 확인 → 매치되면 즉시 차단 (rm -rf /, sudo 등)
2. ALLOW 목록 확인 → 매치되면 허용 (ls, pwd, git status 등)
3. 그 외 → ASK (사용자에게 승인 요청)
```

기본값이 **ASK**라는 점이 핵심입니다 — 모든 것을 차단하면 에이전트가 무용지물이 되고, 모든 것을 허용하면 위험합니다.

**이미 제공된 것:**
- `self.config.blocked_raw_patterns` — 파싱 전 차단할 패턴 (포크 폭탄 등)
- `self._check_rules(command)` — PermissionRule 기반 DENY/ALLOW 매칭 (이미 구현됨)
- `self._parser.parse(command)` — tree-sitter 기반 명령어 파싱 (이미 구현됨)
- `self._validate_parsed_command(parsed)` — 파싱된 명령어 개별 검증 (이미 구현됨)
- `self._get_highest_priority_result(results, command)` — 여러 결과 중 최고 우선순위 반환

**구현할 코드:**

```python
def validate_command(self, command: str) -> CommandValidationResult:
    # TODO 1: DENY → ALLOW → ASK 3단계 검증을 구현하세요
    #
    # Step 1: 빈 명령어 체크
    #   비어있으면 ALLOW 반환 (실행할 게 없음)
    #
    # Step 2: 원시 패턴 차단 (파싱 전)
    #   self.config.blocked_raw_patterns를 순회하며 command 안에 포함되어 있는지 확인
    #   매치되면 DENY 반환
    #   왜 파싱 전에? → ":(){ :|:& };:" 같은 포크 폭탄은 파서가 제대로 처리 못 함
    #
    # Step 3: PermissionRule 기반 매칭
    #   self._check_rules(command) 호출
    #   결과가 있으면 (DENY 또는 ALLOW) 그대로 반환
    #
    # Step 4: 명령어 파싱 + 개별 검증
    #   self._parser.parse(command)로 파싱
    #   파싱 실패하면 DENY (알 수 없는 구조는 차단)
    #   각 파싱된 명령어에 대해 self._validate_parsed_command(parsed) 호출
    #   DENY가 나오면 즉시 반환 (early exit)
    #
    # Step 5: 최종 결과
    #   self._get_highest_priority_result(results, command) 반환
    #   우선순위: DENY > ALLOW > ASK
    #
    return CommandValidationResult(level=PermissionLevel.ASK, command=command, reason="")
```

**확인 포인트:**
- `sudo rm -rf /` → Step 2 또는 Step 3에서 DENY
- `ls` → Step 3에서 ALLOW (PermissionRule `execute(ls:*)` 매칭)
- `python script.py` → 어떤 rule에도 매치 안 됨 → ASK

---

## TODO 2: wrap_tool_call() Bash 블록 — interrupt + always-allow

**배울 개념:** Human-in-the-loop — ASK 결과가 나오면 `interrupt()`로 사용자에게 묻고, "always" 응답 시 세션 동안 같은 패턴을 허용합니다.

**이미 제공된 것:**
- `self._validator.validate_command()` — TODO 1에서 구현
- `self._is_allowed(tool_name, command)` — 세션 allow 규칙 매칭 (이미 구현됨)
- `self._add_allow_rule(tool_name, command)` — 세션 allow 규칙 추가 (이미 구현됨)
- `self._enforce_timeout_limits(args)` — 타임아웃 강제 (이미 구현됨)
- `interrupt()` — LangGraph의 실행 일시 정지 함수

**구현할 코드:**

```python
# wrap_tool_call() 안의 Bash 검증 블록
if tool_name in _BASH_TOOL_NAMES:
    # TODO 2: Bash 명령어 검증 + ASK 처리를 구현하세요
    #
    # Step 1: 타임아웃 제한 강제 (Hard limit)
    #   self._enforce_timeout_limits(args)
    #
    # Step 2: validate_command()로 검증
    #   result.level == DENY → ToolMessage(status="error") 반환
    #
    # Step 3: ASK 처리 — interrupt + always-allow 패턴
    #   result.level == ASK이면:
    #   a) self._is_allowed()로 세션 규칙 확인 — 이미 허용됐으면 건너뛰기
    #   b) interrupt()로 사용자에게 질문
    #      payload에 allow_rule을 포함 (UI에서 "Always allow execute(python:*)" 표시)
    #   c) response == "always" → self._add_allow_rule()
    #   d) response == False 또는 "deny:..." → ToolMessage(status="error") 반환
    #   e) response == True → 통과 (이번만 허용)
    #
    pass
```

**확인 포인트:**
- DENY된 명령은 `interrupt()` 없이 즉시 에러 반환하는지
- ASK 명령이 이미 세션 규칙에 있으면 `interrupt()` 호출 없이 통과하는지
- "always" 응답 시 같은 명령어가 다음에는 자동 통과하는지

---

## TODO 3: wrap_tool_call() 파일 블록 — Read-before-Write + Stale 감지

**배울 개념:** 파일 안전 장치 — 읽지 않은 파일을 수정하면 기존 내용을 덮어쓸 수 있고, 다른 프로세스가 수정한 파일을 모르고 편집하면 변경이 충돌합니다.

**이미 제공된 것:**
- `self._read_files: dict[str, float]` — `{경로: 마지막_읽은_시간}` 추적 딕셔너리
- `self._validator.validate_path()` — 사전 제공 코드에서 확인
- `_WRITE_FILE_TOOLS` — `("write_file", "edit_file")`

**구현할 코드:**

```python
# wrap_tool_call() 안의 File 검증 블록
elif tool_name in _FILE_TOOL_NAMES:
    # TODO 3: 파일 경로 검증 + read-before-write를 구현하세요
    #
    # Part A: 경로 검증 (사전 제공된 validate_path 활용)
    #   1. args에서 경로 추출 (file_path, path, validated_path 중 존재하는 키)
    #   2. 상대경로면 workspace_root 기준 절대경로로 변환
    #   3. validate_path(path, is_write) 호출
    #   4. DENY → 에러, ASK → interrupt (TODO 2과 같은 패턴)
    #
    # Part B: Read-before-write 체크 (쓰기 도구일 때만)
    #   tool_name이 _WRITE_FILE_TOOLS에 있고, 파일이 이미 존재할 때:
    #
    #   1. 읽은 적 있는지 확인
    #      normalized_path가 self._read_files에 없으면 → 에러
    #      "Error: You must read the file first before editing it."
    #
    #   2. Stale read 감지
    #      현재 파일의 mtime과 self._read_files[path]를 비교
    #      mtime이 더 크면 (읽은 후 변경됨) → 에러
    #      "Error: File has been modified since you last read it."
    #
    # Part C: 실행 후 추적 업데이트
    #   handler(request) 실행 후:
    #   - read_file 성공 시 → self._read_files[path] = os.path.getmtime(path)
    #   - write/edit 성공 시 → self._read_files[path] = os.path.getmtime(path) (갱신)
    #
    pass
```

**확인 포인트:**
- 존재하는 파일을 읽지 않고 `edit_file` 시도 → 에러
- 파일을 읽고, 다른 프로세스가 수정한 후 `edit_file` 시도 → 에러 (stale)
- 파일을 읽고 바로 `edit_file` → 성공

---

## 검증 방법

```bash
uv run python -c "
from ax_advanced_class.src.middleware.tool_validation_middleware import ToolValidationMiddleware
from ax_advanced_class.src.config.tool_permission_config import PermissionConfig

config = PermissionConfig()
mw = ToolValidationMiddleware(config)
v = mw._validator

# 1. DENY 테스트
r = v.validate_command('sudo rm -rf /')
assert r.level.value == 'deny', f'sudo: expected deny, got {r.level}'
print('sudo rm -rf / → DENY — OK')

# 2. ALLOW 테스트  
r = v.validate_command('ls')
assert r.level.value == 'allow', f'ls: expected allow, got {r.level}'
print('ls → ALLOW — OK')

# 3. ASK 테스트
r = v.validate_command('python script.py')
assert r.level.value == 'ask', f'python: expected ask, got {r.level}'
print('python script.py → ASK — OK')

# 4. 경로 검증
r = v.validate_path('/etc/passwd', is_write=True)
assert r.level.value == 'deny', f'/etc: expected deny, got {r.level}'
print('/etc/passwd → DENY — OK')

r = v.validate_path(config.workspace_root + '/test.py', is_write=True)
assert r.level.value == 'allow', f'workspace: expected allow, got {r.level}'
print('workspace/test.py → ALLOW — OK')

print('All tests passed')
"
```

---

## 흔한 실패와 대처

| 증상 | 원인 | 해결 |
|------|------|------|
| 모든 명령이 DENY됨 | `deny_rules`가 너무 넓은 패턴으로 매칭 | 규칙을 구체적으로 (예: `rm` 전체 차단 대신 `rm -rf /` 패턴만 차단) |
| `interrupt()` 호출 시 `GraphRecursionError` | `checkpointer=True` 미설정 | `create_agent()` 또는 `compile()`에서 checkpointer 활성화 확인 |
| always-allow가 다음 세션에도 적용됨 | 세션 규칙을 영구 저장 | `_session_allow_rules`는 인스턴스 변수 → 세션 종료 시 자동 리셋 확인 |
| symlink로 blocked_paths 우회 가능 | `Path.resolve()` 미사용 | `validate_path()`에서 반드시 `.resolve()`로 실제 경로 정규화 후 비교 |
| `mtime` 비교가 항상 stale 판정 | 파일을 읽은 후 다른 프로세스가 수정 | mtime 비교 시 1초 이내 차이는 허용하거나, 읽기 직후 mtime 갱신 |

---

## 개념 연결 맵

```
배운 개념  →  이 실습에서 구현한 것
│
├─ DENY > ALLOW > ASK 패턴 ─────→ validate_command() (TODO 1)
│   "차단 → 허용 → 사용자에게 묻기"    3단계: raw 패턴 → rule 매칭 → 파싱 검증
│
├─ 워크스페이스 경계 보호 ───────→ validate_path() (사전 제공 코드)
│   "안은 자유, 밖은 제한"              blocked_paths → workspace → 외부 읽기/쓰기 구분
│
├─ Human-in-the-loop ───────────→ interrupt() + always-allow (TODO 2)
│   "ASK = 사용자에게 승인 요청"        interrupt() → response 처리 → 세션 규칙 저장
│
├─ Read-before-write ───────────→ _read_files 추적 (TODO 3)
│   "읽기 선행, 변경 감지"              mtime 비교로 stale 감지
│
└─ Two-Layer 아키텍처 ──────────→ Soft(프롬프트) + Hard(이 미들웨어)
    "LLM이 결정, 코드가 통제"           Soft Rules는 시스템 프롬프트에,
                                       Hard Rules는 이 코드에 구현
```
