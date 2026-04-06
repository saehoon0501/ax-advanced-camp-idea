# Tool Validation Middleware Lab
## Sentence-by-Sentence Translation Map
---
### Section: Title and Problem Statement
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Tool Validation Middleware 실습 | Tool Validation Middleware Lab |
| 2 | 사용자가 에이전트에게 "테스트 파일 전부 삭제해줘"라고 요청합니다. | The user asks the agent to "delete all test files." |
| 3 | 에이전트는 `rm -rf test_*`를 실행하려 합니다. | The agent attempts to execute `rm -rf test_*`. |
| 4 | 아무런 검증 없이 이 명령이 실행된다면? | What if this command runs without any validation? |
| 5 | 이 실습에서는 **Two-Layer Permission System**의 **Hard Rules 레이어**를 직접 구현합니다. | In this lab, you will implement the **Hard Rules layer** of the **Two-Layer Permission System** directly. |
| 6 | Soft Rules(프롬프트 기반)는 이미 시스템 프롬프트에 포함되어 있고, 여기서는 코드로 강제하는 검증 미들웨어를 만듭니다. | Soft Rules (prompt-based) are already included in the system prompt; here you will build validation middleware that enforces rules through code. |
| 7 | **구현 파일:** `ax_advanced_class/src/middleware/tool_validation_middleware.py` | **Implementation file:** `ax_advanced_class/src/middleware/tool_validation_middleware.py` |

---
### Section: Concept-to-Lab Connection
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 8 | 배운 개념과 실습의 연결 | Connection Between Learned Concepts and This Lab |
| 9 | DENY > ALLOW > ASK 패턴 | DENY > ALLOW > ASK pattern |
| 10 | `validate_command()`에서 3단계 검증 로직 구현 | Implement 3-stage validation logic in `validate_command()` |
| 11 | 경로 기반 권한 제어 | Path-based permission control |
| 12 | `validate_path()`에서 워크스페이스 경계 검증 | Validate workspace boundaries in `validate_path()` |
| 13 | Human-in-the-loop (ASK) | Human-in-the-loop (ASK) |
| 14 | `interrupt()`로 사용자 승인 UI + always-allow 패턴 | User approval UI via `interrupt()` + always-allow pattern |
| 15 | 읽기 선행 확인 | Read-before-write check |
| 16 | `wrap_tool_call()`에서 read-before-write 체크 | Read-before-write check in `wrap_tool_call()` |
| 17 | Stale Read 감지 | Stale Read detection |
| 18 | 파일 수정 시간 비교로 동시 편집 방지 | Prevent concurrent edits by comparing file modification times |

---
### Section: What We Will Build
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 19 | 우리가 만들 것 | What We Will Build |
| 20 | 에이전트가 Tool 호출 요청 | Agent requests a Tool call |
| 21 | Bash 명령? → validate_command() | Bash command? -> validate_command() |
| 22 | DENY? → 에러 반환 (차단) | DENY? -> return error (blocked) |
| 23 | ALLOW? → 통과 | ALLOW? -> pass through |
| 24 | ASK? → interrupt() (사용자에게 질문) | ASK? -> interrupt() (ask the user) |
| 25 | 파일 도구? → validate_path() | File tool? -> validate_path() |
| 26 | 차단 경로? → DENY | Blocked path? -> DENY |
| 27 | 워크스페이스 안? → ALLOW | Inside workspace? -> ALLOW |
| 28 | 밖에 쓰기? → ASK | Write outside? -> ASK |
| 29 | 쓰기 도구? → read-before-write 체크 | Write tool? -> read-before-write check |
| 30 | 읽은 적 없는 파일? → 에러 | File never read? -> error |
| 31 | 읽은 후 변경됨? → 에러 (stale) | Modified since last read? -> error (stale) |
| 32 | 모든 검증 통과 → handler(request) → 실제 실행 | All validations passed -> handler(request) -> actual execution |

---
### Section: Lab Structure
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 33 | 실습 구조 | Lab Structure |
| 34 | 3개의 TODO를 순서대로 구현합니다. | You will implement 3 TODOs in order. |
| 35 | DENY → ALLOW → ASK 3단계 검증 | DENY -> ALLOW -> ASK 3-stage validation |
| 36 | DENY > ALLOW > ASK 패턴 | DENY > ALLOW > ASK pattern |
| 37 | interrupt + always-allow | interrupt + always-allow |
| 38 | Human-in-the-loop | Human-in-the-loop |
| 39 | read-before-write + stale 감지 | read-before-write + stale detection |
| 40 | 파일 안전 장치 | File safety mechanisms |

---
### Section: Pre-provided Code - validate_path()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 41 | 사전 제공 코드 | Pre-provided Code |
| 42 | TODO 1-3을 구현하기 전에, `validate_path()`의 구현을 먼저 읽으세요. | Before implementing TODOs 1-3, first read the implementation of `validate_path()`. |
| 43 | TODO 2, 3에서 이 함수를 호출합니다. | This function is called in TODOs 2 and 3. |
| 44 | validate_path() — 워크스페이스 경계 검증 | validate_path() -- Workspace boundary validation |
| 45 | 경로 기반 권한 — 워크스페이스 안은 자유롭게, 밖은 제한적으로: | Path-based permissions -- free within the workspace, restricted outside: |
| 46 | /etc/passwd → DENY (시스템 경로, 항상 차단) | /etc/passwd -> DENY (system path, always blocked) |
| 47 | ./workspace/src/ → ALLOW (워크스페이스 안) | ./workspace/src/ -> ALLOW (inside workspace) |
| 48 | /home/user/other.py → 읽기: ALLOW, 쓰기: ASK | /home/user/other.py -> read: ALLOW, write: ASK |
| 49 | Step 1: 빈 경로 → ALLOW (기본값은 워크스페이스) | Step 1: Empty path -> ALLOW (defaults to workspace) |
| 50 | Step 2: 경로 정규화 — symlink 공격 방지 | Step 2: Path normalization -- prevent symlink attacks |
| 51 | Step 3: DENY — 차단 경로 체크 (읽기/쓰기 무관) | Step 3: DENY -- check blocked paths (regardless of read/write) |
| 52 | Step 4: ALLOW — 워크스페이스 + 허용 경로 체크 | Step 4: ALLOW -- check workspace + allowed paths |
| 53 | Step 5: 워크스페이스 밖 → 읽기는 ALLOW, 쓰기는 ASK | Step 5: Outside workspace -> read is ALLOW, write is ASK |
| 54 | 이해 포인트: | Key points to understand: |
| 55 | `os.path.abspath(os.path.expanduser(...))` — `~/.ssh`를 `/home/user/.ssh`로 정규화. symlink 우회 공격을 방지 | `os.path.abspath(os.path.expanduser(...))` -- normalizes `~/.ssh` to `/home/user/.ssh`. Prevents symlink bypass attacks |
| 56 | DENY가 ALLOW보다 먼저 — `blocked_paths`를 먼저 체크하므로, 워크스페이스 안에 있어도 blocked 경로면 차단 | DENY comes before ALLOW -- `blocked_paths` are checked first, so even paths inside the workspace are blocked if they are in blocked_paths |
| 57 | 읽기/쓰기 구분 — 워크스페이스 밖 읽기는 허용 (로그 파일 확인 등), 쓰기만 ASK | Read/write distinction -- reads outside the workspace are allowed (checking log files, etc.), only writes trigger ASK |

---
### Section: TODO 1 - validate_command()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 58 | TODO 1: validate_command() — DENY > ALLOW > ASK 3단계 검증 | TODO 1: validate_command() -- DENY > ALLOW > ASK 3-stage validation |
| 59 | 배울 개념: Hard Rules의 핵심 로직 — 모든 bash 명령은 이 3단계를 거칩니다. | Concept to learn: Core logic of Hard Rules -- all bash commands go through these 3 stages. |
| 60 | 1. DENY 목록 확인 → 매치되면 즉시 차단 (rm -rf /, sudo 등) | 1. Check the DENY list -> block immediately if matched (rm -rf /, sudo, etc.) |
| 61 | 2. ALLOW 목록 확인 → 매치되면 허용 (ls, pwd, git status 등) | 2. Check the ALLOW list -> allow if matched (ls, pwd, git status, etc.) |
| 62 | 3. 그 외 → ASK (사용자에게 승인 요청) | 3. Everything else -> ASK (request user approval) |
| 63 | 기본값이 **ASK**라는 점이 핵심입니다 — 모든 것을 차단하면 에이전트가 무용지물이 되고, 모든 것을 허용하면 위험합니다. | The key point is that the default is **ASK** -- blocking everything makes the agent useless, and allowing everything is dangerous. |
| 64 | `self.config.blocked_raw_patterns` — 파싱 전 차단할 패턴 (포크 폭탄 등) | `self.config.blocked_raw_patterns` -- patterns to block before parsing (fork bombs, etc.) |
| 65 | `self._check_rules(command)` — PermissionRule 기반 DENY/ALLOW 매칭 (이미 구현됨) | `self._check_rules(command)` -- PermissionRule-based DENY/ALLOW matching (already implemented) |
| 66 | `self._parser.parse(command)` — tree-sitter 기반 명령어 파싱 (이미 구현됨) | `self._parser.parse(command)` -- tree-sitter based command parsing (already implemented) |
| 67 | `self._validate_parsed_command(parsed)` — 파싱된 명령어 개별 검증 (이미 구현됨) | `self._validate_parsed_command(parsed)` -- individual validation of parsed commands (already implemented) |
| 68 | `self._get_highest_priority_result(results, command)` — 여러 결과 중 최고 우선순위 반환 | `self._get_highest_priority_result(results, command)` -- returns the highest priority among multiple results |
| 69 | # TODO 1: DENY → ALLOW → ASK 3단계 검증을 구현하세요 | # TODO 1: Implement the DENY -> ALLOW -> ASK 3-stage validation |
| 70 | # Step 1: 빈 명령어 체크 | # Step 1: Check for empty commands |
| 71 | # 비어있으면 ALLOW 반환 (실행할 게 없음) | # If empty, return ALLOW (nothing to execute) |
| 72 | # Step 2: 원시 패턴 차단 (파싱 전) | # Step 2: Raw pattern blocking (before parsing) |
| 73 | # self.config.blocked_raw_patterns를 순회하며 command 안에 포함되어 있는지 확인 | # Iterate through self.config.blocked_raw_patterns and check if they are contained in the command |
| 74 | # 매치되면 DENY 반환 | # If matched, return DENY |
| 75 | # 왜 파싱 전에? → ":(){ :\|:& };:" 같은 포크 폭탄은 파서가 제대로 처리 못 함 | # Why before parsing? -> Fork bombs like ":(){ :\|:& };:" cannot be properly handled by the parser |
| 76 | # Step 3: PermissionRule 기반 매칭 | # Step 3: PermissionRule-based matching |
| 77 | # self._check_rules(command) 호출 | # Call self._check_rules(command) |
| 78 | # 결과가 있으면 (DENY 또는 ALLOW) 그대로 반환 | # If there is a result (DENY or ALLOW), return it as-is |
| 79 | # Step 4: 명령어 파싱 + 개별 검증 | # Step 4: Command parsing + individual validation |
| 80 | # self._parser.parse(command)로 파싱 | # Parse with self._parser.parse(command) |
| 81 | # 파싱 실패하면 DENY (알 수 없는 구조는 차단) | # If parsing fails, DENY (block unknown structures) |
| 82 | # 각 파싱된 명령어에 대해 self._validate_parsed_command(parsed) 호출 | # Call self._validate_parsed_command(parsed) for each parsed command |
| 83 | # DENY가 나오면 즉시 반환 (early exit) | # If DENY is returned, exit immediately (early exit) |
| 84 | # Step 5: 최종 결과 | # Step 5: Final result |
| 85 | # self._get_highest_priority_result(results, command) 반환 | # Return self._get_highest_priority_result(results, command) |
| 86 | # 우선순위: DENY > ALLOW > ASK | # Priority: DENY > ALLOW > ASK |
| 87 | 확인 포인트: | Verification points: |
| 88 | `sudo rm -rf /` → Step 2 또는 Step 3에서 DENY | `sudo rm -rf /` -> DENY at Step 2 or Step 3 |
| 89 | `ls` → Step 3에서 ALLOW (PermissionRule `execute(ls:*)` 매칭) | `ls` -> ALLOW at Step 3 (matches PermissionRule `execute(ls:*)`) |
| 90 | `python script.py` → 어떤 rule에도 매치 안 됨 → ASK | `python script.py` -> doesn't match any rule -> ASK |

---
### Section: TODO 2 - wrap_tool_call() Bash Block
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 91 | TODO 2: wrap_tool_call() Bash 블록 — interrupt + always-allow | TODO 2: wrap_tool_call() Bash block -- interrupt + always-allow |
| 92 | 배울 개념: Human-in-the-loop — ASK 결과가 나오면 `interrupt()`로 사용자에게 묻고, "always" 응답 시 세션 동안 같은 패턴을 허용합니다. | Concept to learn: Human-in-the-loop -- when an ASK result occurs, ask the user with `interrupt()`, and if the response is "always", allow the same pattern for the rest of the session. |
| 93 | `self._validator.validate_command()` — TODO 1에서 구현 | `self._validator.validate_command()` -- implemented in TODO 1 |
| 94 | `self._is_allowed(tool_name, command)` — 세션 allow 규칙 매칭 (이미 구현됨) | `self._is_allowed(tool_name, command)` -- session allow rule matching (already implemented) |
| 95 | `self._add_allow_rule(tool_name, command)` — 세션 allow 규칙 추가 (이미 구현됨) | `self._add_allow_rule(tool_name, command)` -- add session allow rule (already implemented) |
| 96 | `self._enforce_timeout_limits(args)` — 타임아웃 강제 (이미 구현됨) | `self._enforce_timeout_limits(args)` -- enforce timeout (already implemented) |
| 97 | `interrupt()` — LangGraph의 실행 일시 정지 함수 | `interrupt()` -- LangGraph's execution pause function |
| 98 | # TODO 2: Bash 명령어 검증 + ASK 처리를 구현하세요 | # TODO 2: Implement Bash command validation + ASK handling |
| 99 | # Step 1: 타임아웃 제한 강제 (Hard limit) | # Step 1: Enforce timeout limits (Hard limit) |
| 100 | # Step 2: validate_command()로 검증 | # Step 2: Validate with validate_command() |
| 101 | # result.level == DENY → ToolMessage(status="error") 반환 | # result.level == DENY -> return ToolMessage(status="error") |
| 102 | # Step 3: ASK 처리 — interrupt + always-allow 패턴 | # Step 3: ASK handling -- interrupt + always-allow pattern |
| 103 | # a) self._is_allowed()로 세션 규칙 확인 — 이미 허용됐으면 건너뛰기 | # a) Check session rules with self._is_allowed() -- skip if already allowed |
| 104 | # b) interrupt()로 사용자에게 질문 | # b) Ask the user with interrupt() |
| 105 | # payload에 allow_rule을 포함 (UI에서 "Always allow execute(python:*)" 표시) | # Include allow_rule in the payload (UI displays "Always allow execute(python:*)") |
| 106 | # c) response == "always" → self._add_allow_rule() | # c) response == "always" -> self._add_allow_rule() |
| 107 | # d) response == False 또는 "deny:..." → ToolMessage(status="error") 반환 | # d) response == False or "deny:..." -> return ToolMessage(status="error") |
| 108 | # e) response == True → 통과 (이번만 허용) | # e) response == True -> pass through (allow this time only) |
| 109 | DENY된 명령은 `interrupt()` 없이 즉시 에러 반환하는지 | Check that DENY'd commands return an error immediately without calling `interrupt()` |
| 110 | ASK 명령이 이미 세션 규칙에 있으면 `interrupt()` 호출 없이 통과하는지 | Check that ASK commands already in session rules pass through without calling `interrupt()` |
| 111 | "always" 응답 시 같은 명령어가 다음에는 자동 통과하는지 | Check that after an "always" response, the same command passes automatically next time |

---
### Section: TODO 3 - wrap_tool_call() File Block
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 112 | TODO 3: wrap_tool_call() 파일 블록 — Read-before-Write + Stale 감지 | TODO 3: wrap_tool_call() file block -- Read-before-Write + Stale detection |
| 113 | 배울 개념: 파일 안전 장치 — 읽지 않은 파일을 수정하면 기존 내용을 덮어쓸 수 있고, 다른 프로세스가 수정한 파일을 모르고 편집하면 변경이 충돌합니다. | Concept to learn: File safety mechanisms -- modifying a file without reading it first can overwrite existing content, and unknowingly editing a file modified by another process causes conflicting changes. |
| 114 | `self._read_files: dict[str, float]` — `{경로: 마지막_읽은_시간}` 추적 딕셔너리 | `self._read_files: dict[str, float]` -- tracking dictionary of `{path: last_read_time}` |
| 115 | `self._validator.validate_path()` — 사전 제공 코드에서 확인 | `self._validator.validate_path()` -- see the pre-provided code |
| 116 | `_WRITE_FILE_TOOLS` — `("write_file", "edit_file")` | `_WRITE_FILE_TOOLS` -- `("write_file", "edit_file")` |
| 117 | # TODO 3: 파일 경로 검증 + read-before-write를 구현하세요 | # TODO 3: Implement file path validation + read-before-write |
| 118 | # Part A: 경로 검증 (사전 제공된 validate_path 활용) | # Part A: Path validation (using the pre-provided validate_path) |
| 119 | # 1. args에서 경로 추출 (file_path, path, validated_path 중 존재하는 키) | # 1. Extract the path from args (whichever key exists among file_path, path, validated_path) |
| 120 | # 2. 상대경로면 workspace_root 기준 절대경로로 변환 | # 2. If it's a relative path, convert to absolute path based on workspace_root |
| 121 | # 3. validate_path(path, is_write) 호출 | # 3. Call validate_path(path, is_write) |
| 122 | # 4. DENY → 에러, ASK → interrupt (TODO 2과 같은 패턴) | # 4. DENY -> error, ASK -> interrupt (same pattern as TODO 2) |
| 123 | # Part B: Read-before-write 체크 (쓰기 도구일 때만) | # Part B: Read-before-write check (only for write tools) |
| 124 | # tool_name이 _WRITE_FILE_TOOLS에 있고, 파일이 이미 존재할 때: | # When tool_name is in _WRITE_FILE_TOOLS and the file already exists: |
| 125 | # 1. 읽은 적 있는지 확인 | # 1. Check if it has been read before |
| 126 | # normalized_path가 self._read_files에 없으면 → 에러 | # If normalized_path is not in self._read_files -> error |
| 127 | # "Error: You must read the file first before editing it." | # "Error: You must read the file first before editing it." |
| 128 | # 2. Stale read 감지 | # 2. Stale read detection |
| 129 | # 현재 파일의 mtime과 self._read_files[path]를 비교 | # Compare the current file's mtime with self._read_files[path] |
| 130 | # mtime이 더 크면 (읽은 후 변경됨) → 에러 | # If mtime is greater (modified since last read) -> error |
| 131 | # "Error: File has been modified since you last read it." | # "Error: File has been modified since you last read it." |
| 132 | # Part C: 실행 후 추적 업데이트 | # Part C: Post-execution tracking update |
| 133 | # handler(request) 실행 후: | # After executing handler(request): |
| 134 | # - read_file 성공 시 → self._read_files[path] = os.path.getmtime(path) | # - On successful read_file -> self._read_files[path] = os.path.getmtime(path) |
| 135 | # - write/edit 성공 시 → self._read_files[path] = os.path.getmtime(path) (갱신) | # - On successful write/edit -> self._read_files[path] = os.path.getmtime(path) (refresh) |
| 136 | 존재하는 파일을 읽지 않고 `edit_file` 시도 → 에러 | Attempting `edit_file` without reading an existing file -> error |
| 137 | 파일을 읽고, 다른 프로세스가 수정한 후 `edit_file` 시도 → 에러 (stale) | Reading a file, another process modifies it, then attempting `edit_file` -> error (stale) |
| 138 | 파일을 읽고 바로 `edit_file` → 성공 | Read a file then immediately `edit_file` -> success |

---
### Section: Verification
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 139 | 검증 방법 | Verification Method |

---
### Section: Common Failures and Solutions
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 140 | 흔한 실패와 대처 | Common Failures and Solutions |
| 141 | 모든 명령이 DENY됨 | All commands are DENY'd |
| 142 | `deny_rules`가 너무 넓은 패턴으로 매칭 | `deny_rules` matches with patterns that are too broad |
| 143 | 규칙을 구체적으로 (예: `rm` 전체 차단 대신 `rm -rf /` 패턴만 차단) | Make rules specific (e.g., block only the `rm -rf /` pattern instead of blocking all `rm`) |
| 144 | `interrupt()` 호출 시 `GraphRecursionError` | `GraphRecursionError` when calling `interrupt()` |
| 145 | `checkpointer=True` 미설정 | `checkpointer=True` not set |
| 146 | `create_agent()` 또는 `compile()`에서 checkpointer 활성화 확인 | Verify checkpointer is enabled in `create_agent()` or `compile()` |
| 147 | always-allow가 다음 세션에도 적용됨 | always-allow persists into the next session |
| 148 | 세션 규칙을 영구 저장 | Session rules are being permanently saved |
| 149 | `_session_allow_rules`는 인스턴스 변수 → 세션 종료 시 자동 리셋 확인 | `_session_allow_rules` is an instance variable -> verify it auto-resets when the session ends |
| 150 | symlink로 blocked_paths 우회 가능 | blocked_paths can be bypassed via symlink |
| 151 | `Path.resolve()` 미사용 | `Path.resolve()` not used |
| 152 | `validate_path()`에서 반드시 `.resolve()`로 실제 경로 정규화 후 비교 | Always normalize to the real path with `.resolve()` in `validate_path()` before comparison |
| 153 | `mtime` 비교가 항상 stale 판정 | `mtime` comparison always results in stale |
| 154 | 파일을 읽은 후 다른 프로세스가 수정 | Another process modifies the file after reading |
| 155 | mtime 비교 시 1초 이내 차이는 허용하거나, 읽기 직후 mtime 갱신 | Allow differences within 1 second for mtime comparison, or refresh mtime immediately after reading |

---
### Section: Concept Connection Map
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 156 | 배운 개념 → 이 실습에서 구현한 것 | Learned concepts -> What was implemented in this lab |
| 157 | DENY > ALLOW > ASK 패턴 | DENY > ALLOW > ASK pattern |
| 158 | "차단 → 허용 → 사용자에게 묻기" | "Block -> allow -> ask the user" |
| 159 | 3단계: raw 패턴 → rule 매칭 → 파싱 검증 | 3 stages: raw pattern -> rule matching -> parsing validation |
| 160 | 워크스페이스 경계 보호 | Workspace boundary protection |
| 161 | "안은 자유, 밖은 제한" | "Free inside, restricted outside" |
| 162 | blocked_paths → workspace → 외부 읽기/쓰기 구분 | blocked_paths -> workspace -> distinguish external read/write |
| 163 | Human-in-the-loop | Human-in-the-loop |
| 164 | "ASK = 사용자에게 승인 요청" | "ASK = request user approval" |
| 165 | interrupt() → response 처리 → 세션 규칙 저장 | interrupt() -> process response -> save session rules |
| 166 | Read-before-write | Read-before-write |
| 167 | "읽기 선행, 변경 감지" | "Read first, detect changes" |
| 168 | mtime 비교로 stale 감지 | Detect stale via mtime comparison |
| 169 | Two-Layer 아키텍처 | Two-Layer architecture |
| 170 | "LLM이 결정, 코드가 통제" | "LLM decides, code controls" |
| 171 | Soft Rules는 시스템 프롬프트에, Hard Rules는 이 코드에 구현 | Soft Rules are in the system prompt, Hard Rules are implemented in this code |
