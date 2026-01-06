# Long-Running AI Agents: Context Engineering 실습

**이 프로젝트는 Anthropic의 ["Effective harnesses for long-running agents"](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 아티클을 기반으로 설계되었습니다.**

복잡한 웹 애플리케이션을 **여러 세션에 걸쳐 점진적으로 구축하는 AI 에이전트 시스템**을 학습하고 구현하는 실습용 레포지토리입니다.

---

## 🎯 Main Scenario

**목표**: "Build a clone of claude.ai" 같은 고수준 요구사항을 받아, 200+ 기능을 가진 웹 애플리케이션을 여러 세션에 걸쳐 완성하는 두 가지 전문 에이전트를 구현합니다.

### Two-Agent Architecture

1. **Initializer Agent** (첫 세션)

   - 200+ 기능을 구조화된 JSON 파일로 생성
   - Git repository 초기화
   - Progress tracking 시스템 설정

2. **Coding Agent** (이후 모든 세션)
   - 매 세션 시작: 이전 상태 복원 (git log + progress file)
   - 하나의 기능만 선택하여 완전히 구현
   - End-to-end 테스트로 검증
   - Clean state로 커밋 후 종료

자세한 내용은 [`scenarios/MAIN_SCENARIO.md`](ax_advanced_class/scenarios/MAIN_SCENARIO.md)를 참고하세요.

---

## 📁 Directory Structure

```
ax-incubation-advanced-camp-idea-dexter/
├── ax_advanced_class/              # 실습 구현 코드
│   ├── scenarios/                  # 시나리오 문서 (1~9)
│   │   ├── README.md               # 전체 시나리오 개요
│   │   ├── MAIN_SCENARIO.md        # 메인 시나리오 상세 설명
│   │   ├── 1.rolling_window.md
│   │   ├── 2.auto_summarizer.md
│   │   ├── 3.tool_output_trimmer.md
│   │   ├── 4.feature_list_manager.md    # NEW
│   │   ├── 5.git_progress_tracker.md    # NEW
│   │   ├── 6.state_recovery.md          # NEW
│   │   ├── 7.incremental_work_controller.md  # NEW
│   │   ├── 8.test_validator.md          # NEW
│   │   └── 9.clean_state_committer.md   # NEW
│   ├── middlewares/                # Context Engineering 미들웨어
│   │   ├── rolling_window.py
│   │   ├── summarizer.py
│   │   ├── trimmer.py
│   │   ├── feature_manager.py      # Scenario 4
│   │   ├── git_tracker.py          # Scenario 5
│   │   ├── state_recovery.py       # Scenario 6
│   │   ├── work_controller.py      # Scenario 7
│   │   ├── test_validator.py       # Scenario 8
│   │   └── state_committer.py      # Scenario 9
│   ├── initializer_agent.py        # Initializer Agent 구현
│   ├── coding_agent.py             # Coding Agent 구현
│   └── main.py                     # Main entry point
├── tests/                          # 시나리오별 테스트
│   ├── test_1_rolling_window.py
│   ├── test_2_summarizer.py
│   ├── test_3_tool_output_trimmer.py
│   ├── test_4_feature_manager.py
│   └── ...
├── pyproject.toml                  # 프로젝트 설정
└── README.md                       # 이 파일
```

---

## 🧩 9가지 Context Engineering Scenarios

각 시나리오는 Main Scenario를 구현하는 데 필요한 핵심 패턴을 학습합니다.

### Phase 1: Session Context Management (Week 1-2)

| #   | 시나리오                | 설명                                    | 파일                       |
| --- | ----------------------- | --------------------------------------- | -------------------------- |
| 1   | **Rolling Window**      | 토큰 한도를 지키되 System Prompt는 보존 | `1.rolling_window.md`      |
| 2   | **Auto Summarizer**     | 오래된 히스토리를 압축해 의미 보존      | `2.auto_summarizer.md`     |
| 3   | **Tool Output Trimmer** | 장황한 툴 출력을 핵심만 남김            | `3.tool_output_trimmer.md` |

### Phase 2: State Persistence & Recovery (Week 3-4)

| #   | 시나리오                 | 설명                                         | 파일                        |
| --- | ------------------------ | -------------------------------------------- | --------------------------- |
| 4   | **Feature List Manager** | 구조화된 JSON으로 작업 상태 추적             | `4.feature_list_manager.md` |
| 5   | **Git Progress Tracker** | Git history + progress file로 진행 상황 기록 | `5.git_progress_tracker.md` |
| 6   | **State Recovery Agent** | 새 세션 시작 시 이전 컨텍스트 빠르게 복원    | `6.state_recovery.md`       |

### Phase 3: Quality Assurance (Week 5-6)

| #   | 시나리오                        | 설명                                 | 파일                               |
| --- | ------------------------------- | ------------------------------------ | ---------------------------------- |
| 7   | **Incremental Work Controller** | 한 번에 하나의 기능만 구현           | `7.incremental_work_controller.md` |
| 8   | **End-to-End Test Validator**   | 브라우저 자동화로 사용자 관점 테스트 | `8.test_validator.md`              |
| 9   | **Clean State Committer**       | 세션 종료 시 깨끗한 상태 유지        | `9.clean_state_committer.md`       |

---

## 🚀 Quick Start

### 1. 환경 설정

#### Option A: Using `uv` (권장)

```bash
cd ax-incubation-advanced-camp-idea-dexter
uv sync
```

#### Option B: Using `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 브라우저 자동화 도구 설치 (Scenario 8 필요)

```bash
playwright install chromium
```

### 2. 개별 시나리오 실습

시나리오 1부터 순서대로 진행하는 것을 권장합니다:

```bash
# Week 1-2: Context Management
pytest tests/test_1_rolling_window.py -v
pytest tests/test_2_summarizer.py -v
pytest tests/test_3_tool_output_trimmer.py -v

# Week 3-4: State Management
pytest tests/test_4_feature_manager.py -v
pytest tests/test_5_git_tracker.py -v
pytest tests/test_6_state_recovery.py -v

# Week 5-6: Quality Assurance
pytest tests/test_7_work_controller.py -v
pytest tests/test_8_test_validator.py -v
pytest tests/test_9_state_committer.py -v
```

### 3. Main Scenario 실행 (Week 7)

```bash
# Step 1: Initializer Agent 실행
python ax_advanced_class/main.py init "Build a simple blog with posts and comments"

# Step 2: Coding Agent - Session 1
python ax_advanced_class/main.py code

# Step 3: Coding Agent - Session 2
python ax_advanced_class/main.py code

# ... 모든 기능이 완료될 때까지 반복
```

### 4. 진행 상황 확인

```bash
# Feature completion status
python -c "
import json
f = json.load(open('feature_list.json'))
total = len(f['features'])
completed = sum(1 for x in f['features'] if x['passes'])
print(f'Progress: {completed}/{total} ({completed/total*100:.1f}%)')
"

# Recent work
git log --oneline --graph -10

# Latest progress notes
head -n 30 claude-progress.txt
```

---

## 📖 학습 방법

### 1. 시나리오 문서 읽기

각 시나리오 문서(`scenarios/*.md`)는 다음 구조로 되어 있습니다:

- **개발 Principle**: Context Engineering 관점의 핵심 원칙
- **시나리오**: Long-Running Agent 맥락에서의 문제 상황
- **학습 목표**: 이 시나리오로 무엇을 배울 것인가
- **요구사항**: 구체적으로 구현할 함수/클래스
- **실패 모드**: 주의할 점과 대응 방법
- **테스트**: 검증 방법
- **확장 과제**: 추가 도전 과제

### 2. 코드 구현

- `ax_advanced_class/middlewares/`에 각 시나리오의 미들웨어 구현
- 시나리오 문서의 요구사항을 코드로 구현
- 테스트를 통과하도록 작성

### 3. 테스트로 검증

- `tests/`의 테스트를 실행하여 구현 검증
- 테스트가 통과하면 다음 시나리오로 진행
- 실패 모드 케이스를 추가 테스트로 작성하면 실무 감각 향상

### 4. Main Scenario 통합

- Week 7에 모든 시나리오를 통합
- Initializer Agent + Coding Agent 구현
- 실제 웹앱 빌드 경험

---

## 🎓 학습 로드맵 (7주)

### Week 1-2: Context Fundamentals

```
Day 1-2: Scenario 1 (Rolling Window)
Day 3-4: Scenario 2 (Auto Summarizer)
Day 5-6: Scenario 3 (Tool Output Trimmer)
```

### Week 3-4: State Management

```
Day 1-2: Scenario 4 (Feature List Manager)
Day 3-4: Scenario 5 (Git Progress Tracker)
Day 5-6: Scenario 6 (State Recovery)
```

### Week 5-6: Quality Assurance

```
Day 1-2: Scenario 7 (Incremental Work Controller)
Day 3-4: Scenario 8 (End-to-End Test Validator)
Day 5-6: Scenario 9 (Clean State Committer)
```

### Week 7: Full Integration

```
Day 1-2: Initializer Agent 구현
Day 3-4: Coding Agent 구현
Day 5:   Integration Testing
Day 6-7: Real Project (Todo App / Blog / Chat UI)
```

---

## 🎯 핵심 학습 목표

이 실습을 완료하면:

1. ✅ **Long-running agent의 핵심 문제**와 해결 방법을 이해합니다
2. ✅ **Context Engineering 9가지 패턴**을 실전에 적용할 수 있습니다
3. ✅ **Two-agent architecture**를 설계하고 구현할 수 있습니다
4. ✅ **여러 세션에 걸친 점진적 개발** 전략을 체득합니다
5. ✅ **프로덕션급 에이전트 시스템** 설계 역량을 갖춥니다

---

## 🔗 참고 자료

### 필독

- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Claude Prompting Guide](https://docs.anthropic.com/claude/docs/prompts)

### 추가 학습

- [LangGraph Multi-Agent Documentation](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Playwright End-to-End Testing](https://playwright.dev/docs/intro)
- [Test-Driven Development](https://martinfowler.com/bliki/TestDrivenDevelopment.html)

---

## 💡 Why Context Engineering?

단순히 "프롬프트를 길게 쓰는 것"이 아니라, **컨텍스트를 설계하고 관리하는 로직을 코드로 구현**하는 것이 핵심입니다:

- **컨텍스트 예산 관리**: 토큰 한도 내에서 최대한 효율적으로
- **상태 영속성**: 세션이 끝나도 정보를 보존
- **점진적 개발**: 한 번에 하나씩, 완전하게
- **자동 검증**: 테스트로 품질 보장
- **Clean Handoff**: 다음 세션이 즉시 시작 가능

이러한 원칙들을 **Policy-as-Code**로 구현하면, 안정적이고 확장 가능한 에이전트 시스템을 만들 수 있습니다.

---

**Ready to build long-running agents? Start with [`scenarios/README.md`](ax_advanced_class/scenarios/README.md)!** 🚀
