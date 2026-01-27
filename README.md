# Context Engineering 실습 시나리오: Long-Running Coding Agents

## 📋 Overview

이 프로젝트는 [Anthropic의 "Effective harnesses for long-running agents"](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 아티클을 기반으로, **복잡한 웹 애플리케이션을 여러 세션에 걸쳐 점진적으로 구축하는 AI 에이전트 시스템**을 학습합니다.

### 핵심 문제

AI 에이전트가 복잡한 작업을 수행할 때, 컨텍스트 윈도우 제한으로 인해 여러 세션에 걸쳐 작업해야 합니다. 마치 교대 근무하는 엔지니어처럼, 각 세션은 이전 세션의 기억 없이 시작됩니다.

### 해결 방법

**두 가지 전문화된 에이전트**를 사용:

1. **Initializer Agent**: 첫 실행 시 환경을 설정 (feature list, progress tracking, git repo)
2. **Coding Agent**: 매 세션마다 점진적 진행 + 다음 세션을 위한 명확한 상태 저장

---

## 🎯 Main Scenario: Web App Builder

### 목표

"Build a clone of claude.ai"처럼 고수준 요구사항을 받아, 200+ 기능을 가진 풀스택 웹 앱을 여러 세션에 걸쳐 완성합니다.

### 최종 형태(개념도)

각 실행은 “대화의 기억”이 아니라, **워크스페이스/깃에 남아 있는 상태**를 기반으로 이어서 달리는 것을 목표로 합니다.

```
User/CLI
  ↓
Orchestrator (라우팅 + 상태 인계)
  ↓
Agents (initializer / coding)
  ↓
Middleware (컨텍스트 예산 + 정규화 + 가드)
  ↓
Tools (bash/files/etc.)
  ↓
Workspace + Git (지속 상태)
```

### 두 가지 에이전트

#### 1. Initializer Agent (최초 세션)

**역할**: 프로젝트 기반 구축

- 200+ 기능 요구사항을 구조화된 JSON 파일로 생성
- `progress.md` 진행 상황 추적 파일 생성
- `init.sh` 개발 서버 시작 스크립트 작성
- Git 저장소 초기화 및 첫 커밋
- 기본 프로젝트 스캐폴딩

**System Prompt 특징**:

```
You are an Initializer Agent. Your job is to set up a clean environment
for future coding agents to work incrementally. Create:
1. A comprehensive feature list (JSON format)
2. A progress tracking system (git + progress file)
3. An init.sh script to start development servers
4. Initial project structure

Do NOT try to implement all features at once.
```

#### 2. Coding Agent (이후 모든 세션)

**역할**: 점진적 기능 구현

- 매 세션 시작: 이전 진행 상황 파악 (git log + progress file)
- 하나의 기능만 선택하여 구현
- End-to-end 테스트로 검증
- Git 커밋 + progress 업데이트
- 다음 세션을 위한 clean state 유지

**System Prompt 특징**:

```
You are a Coding Agent. At the start of each session:
1. Run `pwd` and read git logs to understand current state
2. Read progress.md and feature_list.json
3. Choose ONE feature to work on
4. Test it end-to-end before marking complete
5. Commit your work with clear messages
6. Update progress file before ending session

NEVER work on multiple features simultaneously.
NEVER declare project complete until all features pass.
```

### 주요 실패 모드와 해결책

| 실패 모드                    | Initializer 해결책              | Coding Agent 해결책                         |
| ---------------------------- | ------------------------------- | ------------------------------------------- |
| 프로젝트를 조기에 완료 선언  | 구조화된 feature list 설정      | Feature list 읽고 하나씩 선택               |
| 버그/미완성 상태로 세션 종료 | Git repo + progress file 초기화 | 세션 시작 시 기본 테스트 실행, 종료 전 커밋 |
| 기능을 검증 없이 완료 표시   | Feature list에 테스트 단계 포함 | End-to-end 테스트 후에만 passes=true        |
| 앱 실행 방법을 매번 파악     | init.sh 스크립트 작성           | 세션 시작 시 init.sh 읽기                   |

### 시나리오가 합쳐지는 방식 (Aggregation Story)

시나리오들을 순서대로 구현하면, 최종적으로 시스템은 이런 흐름으로 자연스럽게 연결됩니다:

1. Orchestrator가 agent를 호출하되, orchestrator에는 **핵심 요약만** 남겨 컨텍스트가 터지지 않게 합니다.
2. Agent 내부에서 대화가 길어지거나 tool output이 장황해도, middleware가 **압축/정규화**해 다음 추론이 가능하게 합니다.
3. Initializer가 “다음에 할 일”을 구조화해 남기고, Coding agent는 그걸 읽어 **한 번에 하나씩** 완성합니다.
4. 세션이 끝날 때는 “다음 실행이 바로 이어받을 수 있게” 인계 정보를 남깁니다.
5. “완료처럼 보이는 것”이 “완료”로 넘어가지 않도록, 산출물은 평가/검증으로 한번 더 걸러냅니다.

---

## 🧩 Small Scenarios: Context Engineering Components

각 시나리오는 **Main Scenario를 구현하는 데 필요한 Context Engineering 패턴**을 학습합니다.

### 시나리오 인덱스 (구현 순서)

아래 목록은 `ax_advanced_class/scenarios/`에 있는 파일 기준으로 정리했습니다.

1. `1.orchestrator_agent_boundary.md`
2. `2.auto_summarizer.md`
3. `3.tool_output_trimmer.md`
4. `4.feature_list_manager.md`
5. `5.progress_tracker.md`
6. `6.state_recovery.md`
7. `7.incremental_work_controller.md`
8. `8.session_task_planner.md`
9. `9.agent_evaluator.md`

### Phase 1: Token Management (토큰 효율적 관리)

#### 1. Orchestrator-Agent Context Boundary

**원칙**: Sub-agent의 내부 대화는 Orchestrator에 전파하지 않음
**적용**: Initializer/Coding Agent → Orchestrator: 최종 요약 메시지만 반환
**학습 목표**: 계층적 컨텍스트 분리, Orchestrator-Workers 패턴 이해
**파일**: `1.orchestrator_agent_boundary.md`

#### 2. Auto Summarizer

**원칙**: Agent 내부 대화가 길어지면 오래된 부분을 요약으로 압축
**적용**: Coding/Initializer Agent의 긴 디버깅 세션 압축 (middleware로 구현)
**학습 목표**: 정보 손실 최소화하며 압축, Middleware 패턴
**파일**: `2.auto_summarizer.md`

#### 3. Tool Output Trimmer

**원칙**: 장황한 툴 출력을 핵심만 남김
**적용**: 파일 읽기, 테스트 로그, 브라우저 자동화 출력 압축 (middleware로 구현)
**학습 목표**: 관측값 컴팩션
**파일**: `3.tool_output_trimmer.md`

> **참고**: Scenario 2, 3은 middleware로 구현되어 Initializer Agent와 Coding Agent 모두에 자동 적용됩니다.

### Phase 2: Initializer Agent - 프로젝트 기반 구축

#### 4. Feature List Manager

**원칙**: 고수준 요구사항을 구조화된 JSON으로 분해
**적용**: Initializer Agent가 `feature_list.json` 생성
**학습 목표**: 테스트 가능한 기능 분해, JSON Schema 검증
**파일**: `4.feature_list_manager.md`

#### 5. Progress Tracker

**원칙**: 세션 간 컨텍스트 전달을 위한 파일 생성
**적용**: Initializer Agent가 `progress.md` + `init.sh` 생성
**학습 목표**: Coding Agent가 파싱 가능한 구조화된 형식
**파일**: `5.progress_tracker.md`

### Phase 3: Coding Agent - 세션 시작 및 컨텍스트 복원

#### 6. State Recovery

**원칙**: 새 세션 시작 시 이전 컨텍스트 빠르게 복원
**적용**: Coding Agent가 `git log`, `progress.md`, `feature_list.json` 읽기
**학습 목표**: 제로 메모리에서 작업 컨텍스트 재구성
**파일**: `6.state_recovery.md`

### Phase 4: Coding Agent - 기능 구현 및 검증

#### 7. Incremental Work Controller

**원칙**: 한 번에 하나의 기능만 구현
**적용**: Coding Agent가 feature 선택 → 구현 → 상태 업데이트
**학습 목표**: 점진적 개발 패턴, scope 제어
**파일**: `7.incremental_work_controller.md`

#### 8. Session Task Planner

**원칙**: 세션 시작 시 계획을 세우고(체크리스트), 계획에 맞춰 진행하며 드리프트를 막기
**적용**: Coding Agent가 feature steps를 todolist로 만들고 상태(pending/in_progress/completed)로 추적
**학습 목표**: 계획을 “컨텍스트 앵커”로 쓰는 방법, todolist 기반 진행 제어
**파일**: `8.session_task_planner.md`

#### 9. Agent Evaluator

**원칙**: 에이전트 산출물을 체계적으로 검증 (Code-based + LLM-based)
**적용**: feature_list.json, progress.md, init.sh 등 산출물 품질 평가
**학습 목표**: ATIS 품질 기준, 가중 평균 점수 계산, Grader 패턴
**파일**: `9.agent_evaluator.md`

---

## 🧪 Evaluation (Evals)

### Initializer Agent Eval

Initializer Agent의 산출물(feature_list.json, progress.md, init.sh)을 평가합니다.

#### Graders

| Grader              | 가중치 | 설명                                          |
| ------------------- | ------ | --------------------------------------------- |
| SchemaGrader        | 25%    | feature_list.json JSON 스키마 검증            |
| DependencyGrader    | 15%    | feature 간 의존성 그래프 유효성 검증          |
| QualityGrader       | 20%    | LLM 기반 feature 품질 평가 (ATIS 기준)        |
| ProgressGrader      | 10%    | progress.md 파일 구조 검증                    |
| ProgressQualityGrader | 15%  | LLM 기반 progress.md 내용 품질 평가           |
| InitScriptGrader    | 15%    | init.sh 스크립트 검증                         |

#### 실행 방법

```bash
# Test case JSON 파일로 실행
uv run -m ax_advanced_class.evals.initializer.run_eval \
  ax_advanced_class/evals/initializer/test_cases/simple_todo_app.json

# Quality grading sample size 조정 (기본값: 10)
uv run -m ax_advanced_class.evals.initializer.run_eval \
  ax_advanced_class/evals/initializer/test_cases/simple_todo_app.json \
  --quality-sample-size 20

# 결과를 JSON 파일로 저장
uv run -m ax_advanced_class.evals.initializer.run_eval \
  ax_advanced_class/evals/initializer/test_cases/simple_todo_app.json \
  --output results/initializer_eval_result.json
```

#### Test Case 형식

```json
{
  "name": "Simple Todo App",
  "description": "A basic todo list web application with...",
  "expected_min_features": 10,
  "expected_categories": ["functional", "ui", "security"],
  "notes": "Should include CRUD operations, auth, and basic UI components"
}
```

---

### Coding Agent Eval

Coding Agent의 세션 행동을 평가합니다.

#### Graders

| Grader                 | 가중치 | 설명                                              |
| ---------------------- | ------ | ------------------------------------------------- |
| SingleFeatureGrader    | 40%    | 한 세션에 하나의 기능만 구현했는지 검증           |
| SessionLifecycleGrader | 26.7%  | START → WORK → END 세션 라이프사이클 준수 검증   |
| TodoListGrader         | 20%    | 에이전트 상태의 todo list 관리 품질               |
| StruggleGrader         | 13.3%  | 디버깅 반복, 무한 루프 등 struggling 패턴 감지    |

#### 실행 방법

```bash
# 기본 실행 (./workspace 디렉토리 사용)
# 먼저 initializer agent로 workspace를 설정해야 함
uv run -m ax_advanced_class.evals.coding.run_eval

# Test case JSON 파일로 실행
uv run -m ax_advanced_class.evals.coding.run_eval \
  --test-case ax_advanced_class/evals/coding/test_cases/basic.json

# 특정 workspace 디렉토리 지정
uv run -m ax_advanced_class.evals.coding.run_eval \
  --workspace ./my_workspace

# Agent 실행 없이 기존 workspace grading만 수행
uv run -m ax_advanced_class.evals.coding.run_eval \
  --workspace ./workspace \
  --skip-agent

# 결과를 JSON 파일로 저장
uv run -m ax_advanced_class.evals.coding.run_eval \
  --output results/coding_eval_result.json
```

#### 사전 요구사항

Coding Agent eval을 실행하기 전에 workspace에 다음 파일이 필요합니다:
- `feature_list.json` - Initializer Agent가 생성
- `init.sh` - Initializer Agent가 생성

```bash
# 먼저 Initializer Agent 실행
python ax_advanced_class/main.py init "Build a simple todo app"

# 그 다음 Coding Agent eval 실행
uv run -m ax_advanced_class.evals.coding.run_eval
```

#### Pass 기준

- Overall score ≥ 0.7
- SingleFeatureGrader passed
- TodoListGrader passed

---

## ✅ 평가 체크리스트

### 기술적 정확성

- [ ] 각 시나리오의 요구사항이 테스트로 검증되는가?
- [ ] System Prompt가 고정되고 필수 정보가 보존되는가?
- [ ] 토큰 한도를 초과하지 않는가?

### Context Engineering 품질

- [ ] 불필요한 텍스트가 컨텍스트에 포함되지 않는가?
- [ ] 정보 손실 없이 압축이 이루어지는가?
- [ ] 구조화된 상태와 텍스트 히스토리가 적절히 분리되는가?

### 에이전트 효과성

- [ ] Initializer Agent가 충분한 스캐폴딩을 제공하는가?
- [ ] Coding Agent가 이전 세션 상태를 정확히 파악하는가?
- [ ] 한 세션에서 하나의 기능만 구현하는가?
- [ ] 에이전트 산출물이 Grader로 검증되는가?

### 회복 탄력성

- [ ] 포맷 불일치/키 누락 시 폴백이 있는가?
- [ ] Git history가 손상되어도 복구 가능한가?
- [ ] Feature list가 손상되어도 최소 기능이 동작하는가?

---

## 🔧 실습 환경

### 필수 도구

```bash
# LangChain + LangGraph
pip install langchain langchain-aws langgraph

# Git (already installed on most systems)
git --version

# Pydantic (for LLM response parsing)
pip install pydantic
```

### 프로젝트 구조

```
ax_advanced_class/
├── scenarios/               # 시나리오 문서 (이 폴더)
├── main.py                  # Main Scenario 실행
├── initializer_agent.py     # Initializer Agent 구현
├── coding_agent.py          # Coding Agent 구현
├── middlewares/             # Context Engineering 미들웨어
│   ├── summarizer.py        # Scenario 2 (Auto Summarizer)
│   ├── trimmer.py           # Scenario 3 (Tool Output Trimmer)
│   ├── feature_manager.py   # Scenario 4
│   ├── git_tracker.py       # Scenario 5
│   ├── state_recovery.py    # Scenario 6
│   ├── work_controller.py   # Scenario 7
│   └── state_committer.py   # Scenario 9
├── evals/                   # Agent Evaluators
│   ├── initializer/         # Initializer Agent Eval
│   │   ├── graders/         # Code-based & LLM-based graders
│   │   │   ├── schema_grader.py
│   │   │   ├── dependency_grader.py
│   │   │   ├── quality_grader.py
│   │   │   ├── progress_grader.py
│   │   │   ├── progress_quality_grader.py
│   │   │   └── init_script_grader.py
│   │   ├── test_cases/      # Test case JSON files
│   │   └── run_eval.py      # Eval orchestrator
│   └── coding/              # Coding Agent Eval
│       ├── graders/
│       │   ├── todolist_grader.py
│       │   ├── single_feature_grader.py
│       │   ├── session_lifecycle_grader.py
│       │   └── struggle_grader.py
│       └── run_eval.py      # Eval orchestrator
└── tests/                   # 각 시나리오 테스트
    ├── test_1_orchestrator_boundary.py
    ├── test_2_summarizer.py
    ├── test_3_tool_output_trimmer.py
    └── ...
```

---

## 📖 참고 자료

### 필독

- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Claude Prompting Guide](https://docs.anthropic.com/claude/docs/prompts)
- [LangGraph Multi-Agent Documentation](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/)

### 추가 학습

- [Context Window Management Best Practices](https://docs.anthropic.com/claude/docs/context-window-management)
- [Git as a State Machine for AI Agents](https://martinfowler.com/articles/practical-test-pyramid.html)
- [LangSmith: Evaluating LLM Applications](https://docs.smith.langchain.com/evaluation)

---

## 🎓 학습 성과

이 과정을 완료하면:

1. ✅ Long-running agent의 핵심 문제와 해결책 이해
2. ✅ Context Engineering 9가지 핵심 패턴 실습
3. ✅ Initializer + Coding Agent 이중 에이전트 아키텍처 구현
4. ✅ 실제 웹앱을 여러 세션에 걸쳐 구축하는 경험
5. ✅ 프로덕션급 에이전트 시스템 설계 능력

---

## 🚀 Quick Start

```bash
# 1. 환경 설정
cd ax_advanced_class
pip install -r requirements.txt

# 2. Scenario 1부터 순차 실습
pytest tests/test_1_orchestrator_boundary.py -v

# 3. Main Scenario 실행
python main.py --scenario web_app_builder --agent initializer
python main.py --scenario web_app_builder --agent coding

# 4. Evals 실행
# Initializer Agent Eval
uv run -m ax_advanced_class.evals.initializer.run_eval \
  ax_advanced_class/evals/initializer/test_cases/simple_todo_app.json

# Coding Agent Eval
uv run -m ax_advanced_class.evals.coding.run_eval
```

Happy coding! 🎉
