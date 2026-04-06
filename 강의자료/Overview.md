# Block Schedule

## Course Intro

안녕하세요 (함박 미소) 만나뵙게 되서 반갑습니다. 잘 부탁 드립니다. (엄지 손가락 위로)
앞으로 AX 개발 심화 과정을 진행할 OOO 입니다.
간단히 Camp 소개를 합니다. 궁금하신 점은 언제나 문의 주세요.

### 사전 학습 요구사항

- Python: 기본적인 syntax 이해

### AX Incubation 심화과정 Camp는 무엇을 하나요?

AI agent가 한 번의 대화로 끝나지 않는 복잡한 프로젝트를 여러 세션에 걸쳐 완성하려면 어떤 문제들이 생길까요?
컨텍스트 윈도우가 초기화되고, 이전 작업을 잊고, 범위가 발산하며, 결과물이 미완성으로 남습니다.

이 과정은 프로덕션 수준의 AI agent 개발에 필요한 핵심 역량을 습득합니다:

- **Context Engineering** — 유한한 토큰 예산 안에서 agent가 길을 잃지 않도록 컨텍스트를 압축·격리·관리하는 기법
- **Agent Harness** — 매 세션 기억이 없는 agent가 스스로 상태를 복구하고, 점진적으로 작업을 완성해 나가는 인프라 패턴

단순히 기법을 적용하는 것이 아니라, 왜 Context Engineering과 Harness가 필요한지 그 근본적인 이유를 먼저 이해한 뒤 직접 구현합니다.
LangChain & LangGraph 기반으로 진행됩니다.

# 실습 프로젝트 소개

## 무엇을 만드는가

**CLI 기반 AI 코딩 에이전트** — 여러 세션에 걸쳐 웹 애플리케이션을 점진적으로 완성하는 장기 실행 에이전트입니다.

```
사용자: "블로그 플랫폼 만들어줘"

세션 1 (init)  → Initializer Agent가 feature_list.json, progress.md, init.sh 생성
세션 2 (code)  → Coding Agent가 feature-001 구현 → commit
세션 3 (code)  → Coding Agent가 feature-002 구현 → commit  (이전 기억 없이 시작!)
  ...
세션 N (code)  → 모든 feature 완료
```

핵심 도전: 매 세션이 **빈 컨텍스트 윈도우**로 시작합니다. 이전 대화 기록이 없어도 작업을 이어갈 수 있어야 합니다.

## 아키텍처

```
┌──────────────────────────────────────────────┐
│  Orchestrator (LangGraph StateGraph)          │
│                                               │
│  사용자 메시지 → Router Node → 어디로 보낼지 결정  │
│                    │                          │
│         ┌──────────┼──────────┐               │
│         ▼          ▼          ▼               │
│    Initializer   Coding    Finish(END)        │
│      Agent       Agent                        │
│    (1회 실행)   (반복 실행)                      │
└──────────────────────────────────────────────┘
```

- **Orchestrator**: 라우팅만 담당 (LangGraph의 StateGraph + Conditional Edge)
- **Initializer Agent**: 프로젝트 구조 설정 — feature_list.json, progress.md, init.sh 생성
- **Coding Agent**: 기능 구현 — 세션당 하나의 feature만 구현하고 commit

## 코드 구조

```
ax_advanced_class/
├── src/
│   ├── main.py              ← CLI 진입점
│   ├── orchestrator.py      ← Orchestrator (StateGraph + Router)
│   ├── agents/
│   │   ├── agent_factory.py ← AgentSpec → create_agent() 변환
│   │   └── agent_specs.py   ← 미들웨어 스택 조립
│   ├── prompts/
│   │   ├── orchestrator_prompt.py   ← 라우팅 시스템 프롬프트
│   │   ├── coding_agent_prompt.py   ← Coding Agent 프롬프트 + @dynamic_prompt
│   │   ├── initializer_prompt.py    ← Initializer 프롬프트
│   │   └── soft_rules_prompt.py     ← Soft Rules (git, 파일, 코드 품질)
│   ├── middleware/
│   │   ├── summarization_middleware.py  ← 컨텍스트 자동 압축
│   │   ├── filesystem_middleware.py     ← 파일/셸 도구 7개 + Soft Rules 주입
│   │   ├── todo_middleware.py           ← write_todos 도구 + 상태 관리
│   │   └── tool_validation_middleware.py ← DENY > ALLOW > ASK 권한 검증
│   ├── config/
│   │   └── tool_permission_config.py    ← Permission 규칙 정의
│   └── llm/
│       └── bedrock_client.py            ← AWS Bedrock LLM 연결
└── evals/                   ← 평가 시스템 (참고용)
    ├── initializer/         ← Initializer Agent 평가
    └── coding/              ← Coding Agent 평가
```

## 실습에서 구현하는 것

이 과정의 6개 실습은 위 코드베이스의 핵심 부분을 직접 구현합니다:

| 실습 | 구현 파일 | 무엇을 만드는가 |
|------|----------|---------------|
| **Orchestrator 구성** | `orchestrator.py` | StateGraph + Router + Agent Node 연결 |
| **Summarizer** | `summarization_middleware.py` | 토큰 초과 시 자동 요약 압축 |
| **Dynamic Prompt** | `coding_agent_prompt.py` | 정적 프롬프트 + 런타임 컨텍스트 주입 |
| **Filesystem Middleware** | `filesystem_middleware.py` | Tool 정의 + Soft Rules + 대형 결과 처리 |
| **Tool Validation** | `tool_validation_middleware.py` | DENY > ALLOW > ASK 권한 시스템 |
| **Agent Harness** | `todo_middleware.py` + `coding_agent_prompt.py` | TodoList 메커니즘 + PHASE 1/2/3 행동 규칙 |

## 실행 방법

```bash
# 의존성 설치
uv sync

# CLI 실행
uv run python -m ax_advanced_class.src.main
```

프롬프트에서:
- `"블로그 플랫폼 만들어줘"` → Initializer Agent가 프로젝트 설정
- `"로그인 기능 구현해줘"` → Coding Agent가 기능 구현
- `"안녕하세요"` → 직접 응답 (Finish 라우팅)

---

## Block Schedule

| 일차 | 시간대 | 구분 | 유형 | 이론 자료 | 실습 자료 | 시간(분) |
|------|--------|------|------|----------|----------|----------|
| 4일차 | 오전 | Intro (실습 프로젝트 소개) | 이론 | 이 문서 상단 참조 | — | 8 |
| 4일차 | 오전 | Context Engineering 소개 | 이론 | [Context Engineering: LLM에서 AI Agent로](Context%20Engineering:%20LLM에서%20AI%20Agent로:%20지능의%20확장%20단계.md) | — | 22 |
| 4일차 | 오전 | LangChain & LangGraph 설명 | 이론 | [LangChain & LangGraph 설명](LangChain%20&%20LangGraph%20설명.md) | — | 50 |
| 4일차 | 오전 | Orchestrator 구성 | 실습 | — | [Orchestrator 구성](실습/Orchestrator%20구성.md) | 30 |
| 4일차 | 오후 | Middleware 설명 | 이론 | [Middleware](Middleware.md) | — | 25 |
| 4일차 | 오후 | Agent Context + Token / Summarizer | 이론+실습 | [Agent Context](Agent%20Context.md) → [Section 1: 토큰](Section%201:%20토큰%20(Token).md) | [Summarizer 실습](실습/Summarizer%20실습.md) | 70 |
| 4일차 | 오후 | Prompt 심화 / Dynamic Prompt | 이론+실습 | [Section 2: 프롬프트](Section%202:%20프롬프트%20(Prompt)%20심화.md) | [Dynamic Prompt 실습](실습/Dynamic%20Prompt%20실습.md) | 55 |
| 4일차 | 오후 | Tool 설계 / Filesystem Middleware | 이론+실습 | [Section 3: 도구](Section%203:%20도구%20(Tool).md), [Tool 설계 가이드](AI%20에이전트를%20위한%20Tool%20설계%20가이드.md) | [Filesystem Middleware 실습](실습/Filesystem%20Middleware%20실습.md) | 75 |
| 5일차 | 오전 | Tool Permission System | 이론+실습 | [Tool Permission System](Tool%20Permission%20System.md) | [Tool Validation Middleware 실습](실습/Tool%20Validation%20Middleware%20실습.md) | 100 |
| 5일차 | 오후 | Agent Harness 이론 | 이론 | [Agent Harness](Agent%20Harness.md) | — | 30 |
| 5일차 | 오후 | TodoMiddleware 실습 | 실습 | — | [Agent Harness 실습 Part 1](실습/Agent%20Harness%20실습.md) | 45 |
| 5일차 | 오후 | Harness Prompting 실습 | 실습 | — | [Agent Harness 실습 Part 2](실습/Agent%20Harness%20실습.md) | 40 |
| 5일차 | 오후 | deepagents 소개 + 과정 마무리 | 이론 | [deepagents 소개](deepagents소개.md) | — | 20 |

---

## 세션 간 학습 흐름

```
4일차 오전: WHY & WHAT
  프로젝트 소개(8분) ──→ Context Engineering(왜 필요한가) ──→ LangChain/LangGraph(무엇으로 만드는가, 50분) ──→ Orchestrator 실습(직접 만들기)

4일차 오후: CONTEXT ENGINEERING 실천 — 3대 컨텍스트 요소
  Middleware(확장 구조) ──→ Token/Summarizer(압축) ──→ Prompt/Dynamic Prompt(주입) ──→ Tool/Filesystem(도구 관리)
                                  ↓                         ↓                              ↓
                           "컨텍스트를 줄여라"        "컨텍스트를 넣어라"            "컨텍스트를 통제하라"

5일차 오전: SAFETY — 도구 권한 관리
  Tool Permission System(Soft Rules + Hard Rules) ──→ Validation Middleware 실습(DENY > ALLOW > ASK 구현)

5일차 오후: HARNESS — 다중 세션 인프라
  Agent Harness 이론(Implicit→Explicit) ──→ TodoMiddleware(메커니즘) ──→ Harness Prompting(행동 규칙) ──→ deepagents(통합 리뷰)
```


