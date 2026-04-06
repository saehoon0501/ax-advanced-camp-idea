AI 에이전트의 능력은 결국 사용할 수 있는 도구의 품질에 의해 결정됩니다. 아무리 뛰어난 LLM이라도 잘못 설계된 도구를 사용하면 실수를 반복하고, 안전하지 않은 결과를 만들어냅니다.
도구 설계는 단순히 "함수를 만들어 LLM에 연결하는 것"이 아닙니다. 다음과 같은 질문에 답해야 합니다:

이 도구가 범용 도구여야 하는가, 전용 도구여야 하는가?

도구의 출력이 LLM의 컨텍스트를 얼마나 소비하는가?

도구를 잘못 사용했을 때 어떤 피해가 발생하는가?

LLM이 이 도구를 올바르게 선택하도록 어떻게 유도하는가?

이 글에서는 실제 Claude Code의 도구 시스템을 분석하고, AI 에이전트 도구 설계의 핵심 원칙들을 정리합니다.



핵심 결정: Specialized vs General Tools
AI 에이전트에 도구를 제공할 때 가장 먼저 결정해야 하는 것은 "이 도구를 전용(Specialized)으로 만들 것인가, 범용(General)으로 만들 것인가" 입니다.

하이브리드 접근법
실전에서는 하나만 선택하지 않습니다. Claude Code는 하이브리드 접근법을 사용합니다:



┌──────────────────────────────────────────────────────────────────┐
│                    SPECIALIZED TOOLS (전용 도구)                   │
│            안전장치 내장, 더 나은 UX, 특정 목적                       │
├──────────────────────────────────────────────────────────────────┤
│  Read      - 파일 내용 읽기                                       │
│  Edit      - 파일 내 정확한 문자열 치환                              │
│  Write     - 파일 생성/덮어쓰기                                    │
│  Grep      - 파일 내용 검색 (regex)                                │
│  Glob      - 파일명 패턴 매칭                                      │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    GENERAL TOOL (범용 도구)                        │
│               유연함, 나머지 모든 작업 처리                           │
├──────────────────────────────────────────────────────────────────┤
│  Bash      - 모든 셸 명령어 실행                                    │
│             - Git, npm, pip, pytest 등                            │
│             - 전용 도구로 커버되지 않는 모든 것                       │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    STATE MANAGEMENT TOOLS (상태 관리 도구)           │
├──────────────────────────────────────────────────────────────────┤
│  TodoWrite - 작업 진행 상황 추적                                    │
└──────────────────────────────────────────────────────────────────┘


언제 전용 도구를 만들어야 하는가?
다음 조건 중 2개 이상을 만족하면 전용 도구를 만드는 것이 좋습니다:

자주 사용됨	파일 읽기/쓰기처럼 거의 매번 호출되는 작업
안전장치가 필요함	경로 검증, 읽기 선행 확인 등
입출력 형식이 정해져 있음	구조화된 파라미터와 결과가 필요
범용 도구로 하면 위험함	'sed'로 파일 편집 vs 전용 Edit 도구
LLM이 실수하기 쉬움	잘못된 파라미터를 넣을 가능성이 높은 작업
언제 범용 도구로 충분한가?
다음의 경우 범용 Bash 도구로 충분합니다:

종류가 너무 많음	git, npm, pip, docker... 각각 전용 도구를 만들기 비현실적
표준 CLI가 이미 잘 동작함	git status는 그 자체로 안정하고 유용
가끔 사용됨	프로젝트 초기 한 번만 실행하는 명령어


핵심 인사이트: Soft Rules로 도구 선택을 유도하라
범용 도구가 존재하더라도, 프롬프트(Soft Rules)를 통해 전용 도구를 우선 사용하도록 유도할 수 있습니다:



AVOID using Bash for:
├── find  → Use Glob tool instead
├── grep, rg  → Use Grep tool instead
├── cat, head, tail  → Use Read tool instead
├── sed, awk  → Use Edit tool instead
├── echo >, cat <<EOF  → Use Write tool instead

USE Bash for:
├── Git commands
├── Package managers (npm, pip, uv)
├── Running scripts/tests
├── System commands


이것은 Soft Rule이므로 코드가 강제하지 않습니다. 하지만 잘 훈련된 LLM은 이 지침을 성실히 따릅니다.
범용 도구를 완전히 차단하지 않으면서도, 더 안전한 전용 도구로 트래픽을 유도하는 전략입니다.



Tool 설명(Description)의 기술
도구 설명은 LLM이 도구를 올바르게 사용하는 데 가장 중요한 요소입니다. LLM은 도구의 코드 구현이 아니라, 설명(description)을 읽고 사용법을 결정합니다.



좋은 도구 설명의 구성 요소
목적(Purpose): 이 도구가 무엇을 하는지

사용 시나리오(When to use): 언제 이 도구를 선택해야 하는지

사용하면 안 되는 경우(When NOT to use): 다른 도구가 더 적합한 경우

파라미터 설명: 각 파라미터의 의미, 형식, 제약

주의사항: 실패하기 쉬운 케이스와 해결 방법


예시


@tool
def bash(command: str, timeout: int = 120) -> str:
    """
    Executes a given bash command in a persistent shell session.

    USE THIS TOOL FOR: <- LLM에게 올바른 사용 시나리오 명시
    - Git operations: git status, add, commit, push, pull
    - Package managers: npm, pip, uv
    - Running scripts/tests: pytest, npm test
    - System commands: ls, pwd, mkdir, mv, cp

    PREFER FILE TOOLS OVER BASH FOR: <- 다른 도구가 더 적합한 경우를 알려줌
    - Reading files: Use Read tool (not cat/head/tail)
    - Searching content: Use Grep tool (not grep/rg)
    - Finding files: Use Glob tool (not find)
    - Editing files: Use Edit tool (not sed/awk)
    - Writing files: Use Write tool (not echo/cat redirects)

    GIT SAFETY PROTOCOL: <- Soft Rules를 도구 설명에 직접 포함
    - NEVER update git config
    - NEVER run destructive commands (push --force, hard reset)
    - NEVER commit unless user explicitly asks
    ...
    """




@tool
def edit(validated_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """
    Performs exact string replacements in files.

    Usage:
    - You must use your Read tool at least once before editing. <- 선행 조건 명시
      This tool will error if you attempt an edit without reading.
    - The edit will FAIL if old_string is not unique in the file. <- 실패 케이스 설명
      Either provide more context or use replace_all=True. <- 해결 방법 제시

    Best Practices:
    - Read the file first before editing
    - Include enough context in old_string to ensure uniqueness
    - Preserve exact indentation (tabs/spaces)
    """


미들웨어 패턴: 도구 실행을 가로채라
미들웨어는 도구 호출과 실제 실행 사이에 위치하는 검증/변환 레이어입니다. 도구 코드를 수정하지 않고도 공통적인 검증 로직을 적용할 수 있습니다.





LLM이 도구 호출 결정
        │
        ▼
┌──────────────────┐
│   미들웨어       │ ← 검증, 변환, 차단, 승인 요청
│   (Middleware)   │
└──────────────────┘
        │
        ▼ (통과 시)
┌──────────────────┐
│   실제 도구 실행  │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│   미들웨어       │ ← 출력 잘림, 추적 업데이트
│   (후처리)       │
└──────────────────┘
        │
        ▼
    LLM에 결과 반환


DENY > ALLOW > ASK 패턴
미들웨어의 핵심 검증 로직입니다:



def validate_command(self, command: str) -> CommandValidationResult:
    """
    1. DENY 목록 확인 → 매치되면 차단
    2. ALLOW 목록 확인 → 매치되면 허용
    3. 그 외 → 사용자에게 승인 요청 (ASK)
    """
    # 1단계: 차단 패턴 확인
    for pattern in self.config.blocked_raw_patterns:
        if pattern in command:
            return CommandValidationResult(level=PermissionLevel.DENY, ...)

    # 2단계: 허용 패턴 확인
    for pattern in self.config.allow_patterns:
        if fnmatch.fnmatch(command, pattern):
            return CommandValidationResult(level=PermissionLevel.ALLOW, ...)

    # 3단계: 파싱 후 세부 검증
    parsed_commands = self._parser.parse(command)
    for parsed in parsed_commands:
        result = self._validate_parsed_command(parsed)
        if result.level == PermissionLevel.DENY:
            return result  # 조기 종료

    # 4단계: 기본값 = ASK
    return CommandValidationResult(level=PermissionLevel.ASK, ...)
허용 목록에 없는 것의 기본값은 "차단"이 아니라 "사용자에게 묻기(ASK)" 입니다. 이것은 안전성과 유용성의 균형입니다:

모든 것을 차단하면 → 에이전트가 아무것도 못 함
모든 것을 허용하면 → 위험한 명령이 무방비로 실행됨
기본값을 ASK로 → 안전하면서도 사용자가 필요한 것을 승인할 수 있음