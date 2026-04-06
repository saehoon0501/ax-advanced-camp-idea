# Dynamic Prompt 실습

Agent가 매번 같은 시스템 프롬프트로 LLM을 호출합니다. 하지만 실제로는 "지금 workspace가 어디인지", "현재 todo 상태가 뭔지"를 매 호출마다 알려줘야 agent가 맥락을 잃지 않습니다.

이 실습에서는 프롬프트 구성 전략을 적용하여, 정적 프롬프트에 런타임 상태를 동적으로 주입하는 미들웨어를 구현합니다.

**구현 파일:** `ax_advanced_class/src/prompts/coding_agent_prompt.py`

## 배운 개념과 실습의 연결

| Section 2 개념 | 이 실습에서 적용하는 방법 |
|----------------|-------------------------|
| 역할 부여 → Expert 활성화 | 정적 프롬프트에서 "You are a Coding Agent" 역할을 명확히 정의 |
| 일관된 도메인 언어 사용 | 코딩 컨텍스트를 유지하는 프롬프트 구성 |
| Prompt Caching 전략 | 정적 부분을 앞에, 동적 부분을 뒤에 배치하여 캐시 적중률 최대화 |
| 혼합 요청 주의 | 역할(정적) + 현재 상태(동적)를 분리하여 Expert 혼란 방지 |

## 우리가 만들 것

```
create_agent(system_prompt=STATIC_PROMPT, middleware=[dynamic_prompt])
                    ↓                                      ↓
    Agent 역할과 규칙 (변하지 않음)          매 LLM 호출마다 현재 상태 추가
                    ↓                                      ↓
                    └────────────── 합쳐져서 ──────────────┘
                                     ↓
              최종 프롬프트 = 정적 + 소프트 규칙 + 동적 컨텍스트
```

**Prompt Caching이 왜 중요한가:**

```
┌────────────────────────────────────┐
│  정적 부분 (캐시됨, 비용 절감)      │
│  "You are a Coding Agent..."      │
│  + SOFT_RULES_PROMPT              │
├────────────────────────────────────┤
│  동적 부분 (매번 변경)              │
│  "Workspace: /workspace"          │
│  "todos: [{...}, {...}]"          │
└────────────────────────────────────┘
```

정적 부분이 **앞에** 있으면, LLM provider(Anthropic 등)가 이 접두사를 캐시하여 비용과 지연시간을 줄입니다. 동적 부분이 앞에 오면 매번 전체가 새로 처리됩니다.

## 사전 지식: @dynamic_prompt 데코레이터

LangChain의 `@dynamic_prompt`는 `wrap_model_call`의 간편 버전입니다:

```python
from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dynamic_prompt
def my_middleware(request: ModelRequest) -> str:
    # 반환하는 문자열이 system prompt 전체를 교체합니다
    return "새로운 system prompt 전체 내용"
```

내부적으로는 이렇게 동작합니다:

```python
# @dynamic_prompt가 하는 일 (개념적)
def wrap_model_call(self, request, handler):
    new_prompt = my_middleware(request)  # 개발자가 작성한 함수 호출
    new_system = SystemMessage(content=new_prompt)
    return handler(request.override(system_message=new_system))
```

`request` 객체에서 접근할 수 있는 것:
- `request.state` — 현재 agent state (`messages`, `todos` 등)
- `request.system_message` — 현재 system prompt

## 실습 구조

2개의 TODO를 순서대로 구현합니다. `CODING_AGENT_SYSTEM_PROMPT`(정적 프롬프트)는 이미 제공되어 있으므로, 동적 컨텍스트 구성과 프롬프트 합성에 집중합니다.

| TODO | 구현할 것 | 대응하는 개념 |
|------|----------|-------------|
| TODO 1 | 동적 컨텍스트 구성 | 런타임 상태 주입 |
| TODO 2 | 프롬프트 합성 순서 | Prompt Caching 전략 (정적 → 동적) |

---

## TODO 1: 동적 컨텍스트 구성

**배울 개념:** 런타임 상태 주입, Information Density

Agent가 매 LLM 호출마다 알아야 하는 **현재 상태**를 구성합니다. `request.state`에서 정보를 추출합니다.

**구현할 코드:**

```python
@dynamic_prompt
def coding_agent_dynamic_prompt(request: ModelRequest) -> str:
    state = request.state
    workspace = PermissionConfig().workspace_root

    # TODO 1: 동적 컨텍스트를 구성하세요
    #
    # 포함해야 할 정보:
    #
    # 1. Workspace 경로
    #    Agent가 파일 작업할 때 기준이 되는 디렉토리
    #    힌트: workspace 변수 사용
    #
    # 2. 현재 todos 상태
    #    Agent가 진행 중인 작업 목록을 확인할 수 있어야 함
    #    힌트: state.get("todos", [])
    #
    # 3. write_todos 사용 가이드
    #    Agent에게 todo를 어떻게 관리해야 하는지 지시
    #    - 작업 시작 전 todo 생성
    #    - in_progress는 1개만
    #    - 완료 즉시 상태 업데이트
    #
    dynamic_content = f"""
# CURRENT SESSION CONTEXT

Workspace: ???
(All file operations should be relative to this directory)

todos: ???
"""

    # TODO 2: 프롬프트 합성 순서를 결정하세요 (다음 TODO)
    return ""
```

**확인:** `state.get("todos", [])`로 현재 todo 상태를 포함했는지 확인하세요. 이 정보가 없으면 Agent가 이전에 만든 todo를 모르는 상태로 작업합니다.

---

## TODO 2: 프롬프트 합성 순서

**배울 개념:** Prompt Caching 전략 — 정적 접두사를 캐시하여 비용/지연 최적화

`@dynamic_prompt`는 반환하는 문자열이 system prompt 전체를 교체합니다. 따라서 정적 부분 + 소프트 규칙 + 동적 부분을 올바른 순서로 합쳐야 합니다.

**구현할 코드:**

```python
    # TODO 2: 세 부분을 올바른 순서로 합치세요
    #
    # 사용 가능한 변수:
    #   CODING_AGENT_SYSTEM_PROMPT  — 정적 시스템 프롬프트 (이미 제공됨)
    #   SOFT_RULES_PROMPT           — git 안전, 코드 품질 등 소프트 규칙
    #   dynamic_content             — TODO 1에서 구성한 런타임 컨텍스트
    #
    # 순서가 왜 중요한가?
    #   LLM provider는 시스템 프롬프트의 "접두사(prefix)"를 캐시합니다.
    #   변하지 않는 부분을 앞에 놓으면 → 캐시 적중 → 비용/지연 절감
    #   변하는 부분을 앞에 놓으면 → 매번 전체 재처리 → 비용/지연 증가
    #
    # 올바른 순서:
    #   1. ???  ← 절대 안 변하는 것 (Agent 역할, 규칙)
    #   2. ???  ← 거의 안 변하는 것 (소프트 규칙)
    #   3. ???  ← 매번 변하는 것 (현재 workspace, todos)
    #
    return ???
```

**확인:** 반환값이 `CODING_AGENT_SYSTEM_PROMPT + SOFT_RULES_PROMPT + dynamic_content` 순서인지 확인하세요. 순서를 바꾸면 캐싱이 깨집니다.

---

## Agent에 미들웨어 연결하기

구현이 끝나면, `agent_specs.py`에서 미들웨어 스택에 `coding_agent_dynamic_prompt`가 이미 등록되어 있는지 확인합니다:

```python
# ax_advanced_class/src/agents/agent_specs.py

middleware = [
    ToolValidationMiddleware(config),
    _create_filesystem_middleware(config),
    TodoListMiddleware(),
    SummarizationMiddleware(...),
    coding_agent_dynamic_prompt,          # ← TODO에서 구현한 함수
]
```

**왜 맨 마지막인가?** `@dynamic_prompt`는 내부적으로 `wrap_model_call`입니다. 미들웨어 리스트의 마지막 = 가장 안쪽 = system prompt의 최종 형태를 결정합니다. 다른 미들웨어(Filesystem, TodoList)가 먼저 prompt를 수정하고, `dynamic_prompt`가 이를 포함한 최종 버전을 조립합니다.

---

## 검증 방법

```python
uv run python -c "
from ax_advanced_class.src.prompts.coding_agent_prompt import coding_agent_dynamic_prompt
print('Import successful — middleware is ready')
"
```

전체 동작 테스트:

```bash
uv run python -m ax_advanced_class.src.main
```

프롬프트에서 `"블로그 플랫폼 만들어줘"` 입력 → coding 에이전트가 PHASE 1(Recovery)부터 시작하는지 확인

---

## 흔한 실패와 대처

| 증상 | 원인 | 해결 |
|------|------|------|
| Agent가 Phase 순서를 무시함 | 프롬프트가 "권장"으로 작성됨 | "MUST", "ALWAYS", "NEVER"로 강제 어투 사용 (예: "You MUST run pwd first") |
| Prompt Caching이 작동 안 함 | 동적 내용이 정적 부분 앞에 위치 | TODO 2의 합성 순서 확인: `STATIC + SOFT_RULES + dynamic` 순서 유지 |
| Dynamic context에 todos가 비어있음 | Agent가 아직 `write_todos`를 호출 안 함 | 초기 상태에서 todos가 빈 리스트인 건 정상 — "No active todos" 표시 |
| Agent가 PHASE 3를 건너뜀 | 프롬프트에 종료 조건이 불명확 | "PHASE 3 is NOT optional. You MUST complete all steps before ending." 명시 |

---

## 개념 연결 맵

```
배운 개념                       →  이 실습에서 구현한 것
│
├─ 런타임 상태 주입 ───────────→ dynamic_content 구성 (TODO 1)
│   "매 호출마다 변하는 정보"       workspace, todos, 사용 가이드
│
├─ Prompt Caching 전략 ────────→ 합성 순서 (TODO 2)
│   "고정을 앞에, 동적을 뒤에"      STATIC + SOFT_RULES + dynamic
│
└─ 정적/동적 분리 ─────────────→ 전체 설계
    "Expert 선택 혼란 방지"         역할(정적) ≠ 상태(동적)
```
