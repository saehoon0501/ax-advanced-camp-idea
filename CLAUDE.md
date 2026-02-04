# AI Agent 개발 심화 학습 가이드

> 이 프로젝트는 Anthropic의 ["Building Effective Agents"](https://www.anthropic.com/research/building-effective-agents)와 ["Effective harnesses for long-running agents"](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 아티클을 기반으로 한 **학습용 프로젝트**입니다.

---

## 응답 규칙

- **항상 한국어로 응답합니다** (학생이 한국어로 질문할 경우)
- 기술 용어는 영어 그대로 사용해도 됩니다 (예: Context Engineering, LangGraph, Agent)
- 코드와 파일 경로는 영어 그대로 유지합니다

---

## 기술 질문 대응 (Python, LangChain, LangGraph)

학생이 Python, LangChain, LangGraph에 대한 기술적 질문을 하면, **반드시 공식 문서를 참조**하여 답변하세요.

### 공식 문서 URL

| 기술 | 공식 문서 | 주요 참조 페이지 |
|------|----------|-----------------|
| **Python** | https://docs.python.org/3/ | - [asyncio](https://docs.python.org/3/library/asyncio.html) - 비동기 프로그래밍<br>- [typing](https://docs.python.org/3/library/typing.html) - 타입 힌트<br>- [dataclasses](https://docs.python.org/3/library/dataclasses.html) |
| **LangChain** | https://python.langchain.com/docs/ | - [Introduction](https://python.langchain.com/docs/introduction/)<br>- [How-to Guides](https://python.langchain.com/docs/how_to/)<br>- [Conceptual Guide](https://python.langchain.com/docs/concepts/) |
| **LangGraph** | https://langchain-ai.github.io/langgraph/ | - [Quick Start](https://langchain-ai.github.io/langgraph/tutorials/introduction/)<br>- [How-to Guides](https://langchain-ai.github.io/langgraph/how-tos/)<br>- [Conceptual Guide](https://langchain-ai.github.io/langgraph/concepts/) |
| **LangSmith** | https://docs.smith.langchain.com/ | - 트레이싱, 평가, 모니터링 |

### 기술 질문 대응 원칙

1. **공식 문서 우선**: 학생이 API 사용법, 패턴, 베스트 프랙티스를 물으면 공식 문서를 검색하고 인용하세요
2. **최신 정보 확인**: LangChain/LangGraph는 빠르게 변하므로, 답변 전 최신 문서를 확인하세요
3. **코드 예시 제공**: 문서에서 관련 코드 예시를 찾아 학생에게 보여주세요
4. **프로젝트 연결**: 가능하면 이 프로젝트의 코드가 해당 패턴을 어떻게 사용하는지 연결해주세요

### 자주 묻는 기술 질문 예시

| 질문 유형 | 참조할 문서 |
|----------|------------|
| "StateGraph 어떻게 만들어요?" | LangGraph Conceptual Guide → [State Management](https://langchain-ai.github.io/langgraph/concepts/low_level/#state) |
| "노드 간 데이터 전달은?" | LangGraph How-to → [Pass data between nodes](https://langchain-ai.github.io/langgraph/how-tos/) |
| "Tool 만드는 방법?" | LangChain How-to → [Custom Tools](https://python.langchain.com/docs/how_to/custom_tools/) |
| "메시지 타입 종류?" | LangChain Conceptual Guide → [Messages](https://python.langchain.com/docs/concepts/messages/) |
| "체크포인터 설정?" | LangGraph How-to → [Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/) |
| "비동기 실행?" | LangGraph How-to → [Async](https://langchain-ai.github.io/langgraph/how-tos/async/) |

### 이 프로젝트에서의 사용 예시

학생이 기술 질문을 하면, 문서 설명과 함께 **이 프로젝트에서 어떻게 사용되는지** 보여주세요:

```
학생: "StateGraph는 어떻게 사용하나요?"

답변 예시:
"StateGraph는 LangGraph의 핵심 컴포넌트로, 노드와 엣지로 구성된 그래프를 정의합니다.

📚 공식 문서: https://langchain-ai.github.io/langgraph/concepts/low_level/#stategraph

이 프로젝트에서는 `ax_advanced_class/src/orchestrator.py`에서 사용합니다:
[코드 위치와 설명]

더 자세한 내용은 공식 문서의 How-to Guides를 참조하세요."
```

---

## 학습 지원 방침

학생이 질문하면, **먼저 어떤 종류의 도움이 필요한지 확인**하세요:

1. **개념 이해**: 이론과 배경 설명이 필요한 경우
2. **코드 탐색**: 특정 패턴이 어디에 구현되어 있는지 찾는 경우
3. **직접 구현**: TODO로 남겨진 미들웨어나 기능을 구현하려는 경우
4. **디버깅**: 코드 실행 중 오류를 해결하려는 경우

예시 응답:
```
어떤 종류의 도움이 필요하신가요?
1. 개념 이해 - Context Engineering이 무엇인지 설명
2. 코드 탐색 - 관련 코드가 어디 있는지 안내
3. 직접 구현 - 함께 코드 작성
4. 디버깅 - 오류 해결
```

---

## 프로젝트 개요

### 해결하려는 문제

AI 에이전트가 복잡한 애플리케이션을 구축하려면 **여러 세션**에 걸쳐 작업해야 합니다.
하지만 각 세션은 새로운 컨텍스트 윈도우로 시작하므로 (채팅 기록 없음):

- 컨텍스트 한계에 도달하면 길을 잃음
- 프로젝트가 불완전하거나 일관성 없는 상태로 남음
- 2-3개 기능 구현 이상으로 확장 불가

### 해결책: Two-Agent 아키텍처

```
┌─────────────────┐
│   Orchestrator  │ ← 라우팅만 담당
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌───────┐
│ Init  │  │Coding │
│ Agent │  │ Agent │
└───────┘  └───────┘
    │          │
    ▼          ▼
  1회 실행   세션마다 실행
  (scaffolding) (구현)
```

1. **Initializer Agent**: 프로젝트 구조 설정 (1회)
2. **Coding Agent**: 기능을 하나씩 구현 (여러 세션)

---

## 핵심 개념 3가지

### 1. Context Engineering (컨텍스트 엔지니어링)

**정의**: 토큰 한계 내에서 에이전트가 효과적으로 작동하도록 컨텍스트를 관리하는 기법

**왜 중요한가?**
- LLM의 컨텍스트 윈도우는 유한함 (128K 토큰이라도 금방 소진)
- 불필요한 정보가 쌓이면 중요한 정보가 밀려남
- 비용과 지연시간이 토큰 수에 비례

**관련 시나리오**:
| 시나리오 | 문제 | 해결책 |
|---------|------|--------|
| 1. Orchestrator-Agent Boundary | 서브에이전트 대화가 오케스트레이터 컨텍스트를 오염 | 최종 요약만 전달 (8000→200 토큰) |
| 2. Auto Summarizer | 디버깅 세션이 30턴 이상 확장 | 오래된 메시지 자동 압축 |
| 3. Tool Output Trimmer | 도구 출력이 5KB JSON 반환 | 스키마 기반 필드 추출 |

**코드 위치**:
- `ax_advanced_class/src/middleware/summarizer_middleware.py` (TODO: 구현 필요)
- `ax_advanced_class/src/middleware/tool_output_trimmer_middleware.py` (TODO: 구현 필요)
- `ax_advanced_class/src/orchestrator.py` → `_initializer_node()`, `_coding_node()`

---

### 2. Agent Harness (에이전트 하네스)

**정의**: 에이전트가 여러 세션에 걸쳐 일관되게 작동하도록 지원하는 인프라 패턴

**핵심 패턴**:

#### Cold Start Recovery (냉시작 복구)
새 세션은 이전 기억이 없습니다. 복구 과정:
1. `pwd` - 작업 디렉토리 확인
2. `git log --oneline -10` - 최근 작업 확인
3. `progress.md` 읽기 - 세션 히스토리 + 다음 작업
4. `feature_list.json` 읽기 - 다음 기능 선택
5. `init.sh` 실행 - 개발 서버 시작

#### Incremental Work (점진적 작업)
**핵심 규칙**: 세션당 **하나의 기능만** 구현

왜?
- 여러 기능 시도 → 범위 확장 → 불완전한 상태
- 하나씩 완료 → 예측 가능한 세션 종료 → 깨끗한 상태

#### Structured State (구조화된 상태)
- `feature_list.json`: 기능 목록 (JSON = 파싱 안정성)
- `progress.md`: 세션 히스토리 (사람이 읽기 쉬움)
- Git: 버전 관리 + 커뮤니케이션 매체

**관련 시나리오**: 4, 5, 6, 7, 8

**코드 위치**:
- `ax_advanced_class/src/prompts/initializer_prompt.py` - Initializer 시스템 프롬프트
- `ax_advanced_class/src/prompts/coding_agent_prompt.py` - Coding Agent 시스템 프롬프트
- `ax_advanced_class/src/tools/todo_tool.py` - 내부 Todo 관리

---

### 3. Agent Evals (에이전트 평가)

**정의**: 에이전트 출력물을 체계적으로 검증하는 방법

**왜 중요한가?**
- "에이전트가 완료했다고 함" ≠ "실제로 완료됨"
- 자동화된 품질 게이트 필요
- 실패를 조기에 감지

**평가 유형**:

| 유형 | 특징 | 예시 |
|------|------|------|
| Code-based Grader | 빠름, 객관적, 결정론적 | JSON 스키마 검증, 파일 존재 확인 |
| LLM-based Grader | 유연함, 뉘앙스 판단 | 품질 평가, 고군분투 감지 |

**Initializer Agent 평가** (`evals/initializer/`):
- SchemaGrader (25%): feature_list.json 스키마 검증
- DependencyGrader (15%): 의존성 그래프 유효성
- QualityGrader (20%): 기능이 ATIS인가? (Atomic, Testable, Independent, Specific)
- ProgressGrader (10%): progress.md 구조 검증
- InitScriptGrader (15%): init.sh 스크립트 검증

**Coding Agent 평가** (`evals/coding/`):
- SingleFeatureGrader (40%): 정확히 하나의 기능만 변경됐는가?
- SessionLifecycleGrader (26.7%): 워크플로우 준수 여부
- TodoListGrader (20%): Todo 관리 상태
- StruggleGrader (13.3%): 효율성 평가

**코드 위치**:
- `ax_advanced_class/evals/initializer/` - Initializer 평가
- `ax_advanced_class/evals/coding/` - Coding Agent 평가

---

## 시나리오 가이드

각 시나리오는 `ax_advanced_class/scenarios/` 디렉토리에 있습니다.

| # | 시나리오 | 핵심 개념 | 난이도 |
|---|---------|----------|--------|
| 1 | Orchestrator-Agent Boundary | Context Engineering | ⭐⭐ |
| 2 | Auto Summarizer | Context Engineering | ⭐⭐⭐ |
| 3 | Tool Output Trimmer | Context Engineering | ⭐⭐ |
| 4 | Feature List Manager | Agent Harness | ⭐⭐ |
| 5 | Progress Tracker | Agent Harness | ⭐⭐ |
| 6 | State Recovery | Agent Harness | ⭐⭐⭐ |
| 7 | Incremental Work Controller | Agent Harness | ⭐⭐ |
| 8 | Session Task Planner | Agent Harness | ⭐⭐ |
| 9 | Agent Evaluator | Agent Evals | ⭐⭐⭐ |

**학습 순서 추천**:
1. 먼저 `MAIN_SCENARIO.md` 읽기 (전체 CLI 정의)
2. Phase 1 (시나리오 1-3): 토큰 관리 이해
3. Phase 2 (시나리오 4-5): Initializer Agent 이해
4. Phase 3 (시나리오 6-8): Coding Agent 이해
5. Phase 4 (시나리오 9): 평가 시스템 이해

---

## 코드 구조

```
ax_advanced_class/
├── scenarios/           # 9개 학습 시나리오 문서
├── src/
│   ├── main.py          # CLI 진입점
│   ├── orchestrator.py  # 라우터 + 멀티에이전트 조율
│   ├── agents/          # 에이전트 팩토리 & 스펙
│   ├── prompts/         # 시스템 프롬프트
│   ├── middleware/      # Context Engineering 미들웨어
│   ├── tools/           # 도구 (bash, file, todo)
│   ├── config/          # 권한 & LLM 설정
│   └── llm/             # LLM 클라이언트 (AWS Bedrock)
└── evals/               # 평가 시스템
    ├── initializer/     # Initializer Agent 평가
    └── coding/          # Coding Agent 평가
```

---

## 참고 자료

### Anthropic 아티클 (필독)
1. [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) - 에이전트 패턴과 아키텍처
2. [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) - 이 프로젝트의 핵심 패턴
3. [Demystifying Evals for AI Agents](https://www.anthropic.com/news/evaluating-ai-agents) - 평가 방법론
4. [Tool Use Best Practices](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/best-practices-and-limitations) - 도구 설계 패턴

### 강의 자료
- `강의자료/AI Agent 실무 가이드.md` - 프로덕션 Q&A 가이드
- `강의자료/AI Agent 개발 심화 노트.md` - 심화 개발 노트

---

## 자주 묻는 질문

### Q: LangGraph는 어디서 사용되나요?
`src/orchestrator.py`에서 `StateGraph`를 사용합니다:
```python
graph = StateGraph(OrchestratorState)
graph.add_node("router", router_node)
graph.add_node("initializer", initializer_node)
graph.add_node("coding", coding_node)
```

### Q: 미들웨어는 어떻게 적용되나요?
`src/agents/agent_specs.py`에서 에이전트 스펙에 미들웨어를 정의하고,
`src/agents/agent_factory.py`에서 에이전트 생성 시 적용합니다.

### Q: TODO가 있는 파일은 어디인가요?
- `src/middleware/summarizer_middleware.py` - Auto Summarizer 구현
- `src/middleware/tool_output_trimmer_middleware.py` - Tool Output Trimmer 구현
- `evals/coding/` - Coding Agent 평가 grader 구현

---

## 학습 팁

1. **시나리오 문서를 먼저 읽으세요** - 문제와 해결책을 이해한 후 코드를 보면 더 명확합니다
2. **Anthropic 아티클과 연결하세요** - 이 프로젝트는 아티클의 실제 구현입니다
3. **작은 것부터 시작하세요** - 시나리오 1부터 순서대로 진행하세요
4. **직접 실행해보세요** - 이론보다 실습이 효과적입니다
5. **평가를 활용하세요** - evals를 실행해서 구현이 올바른지 확인하세요
