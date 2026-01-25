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

---

## 🧩 Small Scenarios: Context Engineering Components

각 시나리오는 **Main Scenario를 구현하는 데 필요한 Context Engineering 패턴**을 학습합니다.

### Phase 1: Session Context Management

#### 1. Rolling Window

**원칙**: 토큰 한도를 지키되 System Prompt는 보존  
**적용**: Coding Agent의 대화가 길어질 때 오래된 메시지 제거  
**학습 목표**: 컨텍스트 예산 관리의 기본

#### 2. Auto Summarizer

**원칙**: 오래된 히스토리를 압축해 의미 보존  
**적용**: `progress.md` 파일이 너무 길어질 때 요약  
**학습 목표**: 정보 손실 최소화하며 압축

#### 3. Tool Output Trimmer

**원칙**: 장황한 툴 출력을 핵심만 남김  
**적용**: 브라우저 자동화 도구의 상세 로그 압축  
**학습 목표**: 관측값 컴팩션

### Phase 2: State Persistence & Recovery

#### 4. Feature List Manager

**원칙**: 구조화된 JSON으로 작업 상태 추적  
**적용**: `feature_list.json` 생성/업데이트/읽기  
**학습 목표**: 텍스트 vs 구조화 데이터 트레이드오프  
**파일**: `4.feature_list_manager.md`

#### 5. Git Progress Tracker

**원칙**: Git history + progress file로 진행 상황 기록  
**적용**: 매 세션마다 의미 있는 커밋 + progress 업데이트  
**학습 목표**: 버전 관리를 상태 관리로 활용  
**파일**: `5.git_progress_tracker.md`

#### 6. State Recovery Agent

**원칙**: 새 세션 시작 시 이전 컨텍스트 빠르게 복원  
**적용**: `git log`, `progress.md`, `feature_list.json` 읽기  
**학습 목표**: 제로 메모리에서 작업 컨텍스트 재구성  
**파일**: `6.state_recovery.md` (revised)

### Phase 3: Quality Assurance (Week 5-6)

#### 7. Incremental Work Controller

**원칙**: 한 번에 하나의 기능만 구현  
**적용**: Feature list에서 우선순위 높은 미완료 기능 선택  
**학습 목표**: 점진적 개발 패턴 구현  
**파일**: `7.incremental_work_controller.md`

#### 8. End-to-End Test Validator

**원칙**: 브라우저 자동화로 사용자 관점 테스트  
**적용**: Puppeteer/Playwright로 실제 웹앱 동작 검증  
**학습 목표**: 코드만으로는 놓치는 버그 발견  
**파일**: `8.test_validator.md`

#### 9. Clean State Committer

**원칙**: 세션 종료 전 clean state로 정리  
**적용**: 버그 없는 상태로 git commit + 문서화  
**학습 목표**: 다음 개발자가 바로 시작 가능한 상태 유지  
**파일**: `9.clean_state_committer.md`

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
- [ ] End-to-end 테스트가 자동화되어 있는가?

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

# Browser automation (for testing)
pip install playwright
playwright install chromium
```

### 프로젝트 구조

```
ax_advanced_class/
├── scenarios/               # 시나리오 문서 (이 폴더)
├── main.py                  # Main Scenario 실행
├── initializer_agent.py     # Initializer Agent 구현
├── coding_agent.py          # Coding Agent 구현
├── middlewares/             # Context Engineering 미들웨어
│   ├── rolling_window.py    # Scenario 1
│   ├── summarizer.py        # Scenario 2
│   ├── trimmer.py           # Scenario 3
│   ├── feature_manager.py   # Scenario 4
│   ├── git_tracker.py       # Scenario 5
│   ├── state_recovery.py    # Scenario 6
│   ├── work_controller.py   # Scenario 7
│   ├── test_validator.py    # Scenario 8
│   └── state_committer.py   # Scenario 9
└── tests/                   # 각 시나리오 테스트
    ├── test_1_rolling_window.py
    ├── test_2_summarizer.py
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
- [End-to-End Testing with Playwright](https://playwright.dev/docs/intro)

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
pytest tests/test_1_rolling_window.py -v

# 3. Main Scenario 실행
python main.py --scenario web_app_builder --agent initializer
python main.py --scenario web_app_builder --agent coding
```

Happy coding! 🎉
