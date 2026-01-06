# Main Scenario: Long-Running Web App Builder

## 🎯 Overview

이 메인 시나리오는 Anthropic의 ["Effective harnesses for long-running agents"](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 아티클을 구현합니다.

**목표**: "Build a clone of claude.ai" 같은 고수준 요구사항을 받아, 200+ 기능을 가진 풀스택 웹 애플리케이션을 **여러 세션에 걸쳐 점진적으로** 완성하는 AI 에이전트 시스템을 만듭니다.

## 🧩 핵심 문제 (The Long-Running Agent Problem)

### 문제 정의

AI 에이전트가 복잡한 프로젝트를 수행할 때, 컨텍스트 윈도우 제한으로 인해 작업을 여러 세션으로 나눠야 합니다. 이는 마치 **교대 근무하는 엔지니어 팀**과 같습니다:

```
Session 1 Engineer → 컨텍스트 윈도우 소진
Session 2 Engineer → 제로 메모리로 시작, 이전 작업 파악 필요
Session 3 Engineer → 또다시 제로 메모리...
```

### 실패 패턴 (Anthropic이 관찰한 것)

#### 1. One-Shotting

**문제**: 에이전트가 한 번에 모든 기능을 구현하려 시도

```
[Session 1]
Agent: "완전한 claude.ai clone을 만들겠습니다!"
- 50개 파일 생성
- 인증 시스템 70% 완성
- 메시지 스트리밍 시작했지만 미완성
- 컨텍스트 윈도우 소진 (토큰 한도 도달)
→ 중간에 멈춤, 앱은 작동 안 함

[Session 2]
Agent: "뭐... 이게 뭐지? 뭘 하려고 했던 거야?"
- 30분 동안 미완성 코드 이해하느라 시간 소비
- 잘못 추측하여 더 망가뜨림
```

#### 2. Premature Completion

**문제**: 일부 기능만 완성했는데 "완료"라고 선언

```
[Session 3]
Agent: "기본 기능들이 구현되었으니 프로젝트 완료!"
(실제로는 200개 기능 중 10개만 완성)
```

#### 3. Untested Features

**문제**: 코드만 작성하고 실제 동작 확인 안 함

```
Agent: "NewChatButton 컴포넌트를 만들었고, 단위 테스트도 통과합니다. 완료!"
(실제로는 버튼이 클릭해도 아무 일도 안 일어남)
```

## 💡 해결책: Two-Agent Architecture

### Initializer Agent (첫 세션)

**역할**: 미래의 Coding Agent들이 점진적으로 작업할 수 있는 환경 구축

**생성하는 것들**:

1. **feature_list.json**: 200+ 기능의 구조화된 목록
2. **claude-progress.txt**: 진행 상황 추적 파일
3. **init.sh**: 개발 서버 시작 스크립트
4. **Git repository**: 초기 커밋
5. **Project scaffolding**: 기본 프로젝트 구조

**System Prompt 예시**:

```
You are an Initializer Agent. Your job is to set up the foundation
for a long-running project that will be built incrementally by future agents.

Given the user request: "{project_description}"

1. Break it down into 50-200 specific, testable features
2. Create feature_list.json with this structure:
   {
     "id": "feature-001",
     "category": "functional|ui|performance|security",
     "description": "User can create a new chat",
     "priority": "high|medium|low",
     "steps": ["Step 1", "Step 2", ...],
     "passes": false,
     "dependencies": []
   }

3. Create init.sh that starts the development server
4. Initialize git repository with clear first commit
5. Create claude-progress.txt for tracking

DO NOT implement features yourself. Your job is ONLY setup.
```

**예시 출력**:

```json
// feature_list.json (excerpt)
{
  "features": [
    {
      "id": "feature-001",
      "category": "functional",
      "description": "User can create a new chat conversation",
      "priority": "high",
      "steps": [
        "Click the 'New Chat' button in the sidebar",
        "Verify a new conversation is created with unique ID",
        "Verify the chat area shows a welcome message",
        "Verify the new conversation appears in the sidebar list"
      ],
      "passes": false,
      "dependencies": []
    },
    {
      "id": "feature-002",
      "category": "ui",
      "description": "User can switch between light and dark themes",
      "priority": "medium",
      "steps": [
        "Locate the theme toggle button",
        "Click to switch from light to dark",
        "Verify CSS variables change",
        "Reload page and verify theme persists"
      ],
      "passes": false,
      "dependencies": []
    }
    // ... 198 more features
  ]
}
```

### Coding Agent (모든 후속 세션)

**역할**: 매 세션마다 하나의 기능을 완전히 구현

**세션 시작 루틴**:

1. `pwd` 실행 → 현재 디렉토리 확인
2. `git log --oneline -10` → 최근 작업 파악
3. `claude-progress.txt` 읽기 → 맥락 이해
4. `feature_list.json` 읽기 → 다음 작업 선택
5. `init.sh` 실행 → 개발 서버 시작
6. 기본 E2E 테스트 → 앱이 동작하는지 확인

**세션 작업**:

1. 하나의 `passes=false` 기능 선택 (우선순위 기반)
2. 기능 구현 (코드 + 테스트)
3. End-to-end 테스트로 검증
4. `passes=true`로 업데이트
5. Git 커밋 (형식화된 메시지)
6. `claude-progress.txt` 업데이트

**세션 종료 루틴**:

1. 모든 테스트 통과 확인
2. Git 상태 깨끗한지 확인
3. 앱이 동작하는 상태인지 확인
4. Handoff 메시지 작성 (다음 세션을 위해)

**System Prompt 예시**:

```
You are a Coding Agent working incrementally on a long-running project.

AT THE START OF EVERY SESSION:
1. Run `pwd` to see your working directory
2. Read git logs: `git log --oneline -10`
3. Read claude-progress.txt to understand what happened
4. Read feature_list.json to see all features
5. Run init.sh to start the dev server
6. Run basic E2E test to verify the app works

DURING THE SESSION:
1. Select ONE feature where passes=false (highest priority)
2. Work ONLY on that feature
3. Implement it completely (code + tests + docs)
4. Test it end-to-end (like a real user would)
5. Only mark passes=true after E2E test succeeds

AT THE END OF EVERY SESSION:
1. Commit your work with clear message
2. Update claude-progress.txt
3. Ensure the app is in a working state
4. Leave clear notes for the next agent

CRITICAL RULES:
- Work on ONE feature at a time (no feature-hopping)
- Do NOT declare project complete until all features pass
- Do NOT mark a feature done without E2E testing
- Do NOT end session with broken app state
```

## 🏗️ 구현 아키텍처

### 파일 구조

```
project_root/
├── feature_list.json          # 모든 기능 목록 (Single Source of Truth)
├── claude-progress.txt        # 세션별 진행 노트
├── init.sh                    # 개발 서버 시작 스크립트
├── .git/                      # Git repository
│   └── (commit history)       # 각 커밋 = 하나의 완성된 기능
├── src/                       # 애플리케이션 코드
│   ├── components/
│   ├── utils/
│   └── ...
└── tests/
    ├── unit/
    └── e2e/                   # End-to-end 테스트
        ├── test_feature_001.py
        ├── test_feature_002.py
        └── ...
```

### 데이터 흐름

```
┌─────────────────────────────────────────────────────────────┐
│  Session N-1 (Coding Agent)                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Recover context (git log + progress file)         │  │
│  │ 2. Select feature-004 (next priority)                │  │
│  │ 3. Implement & test                                  │  │
│  │ 4. Commit: "feat(streaming): Message streaming ✓"   │  │
│  │ 5. Update progress file                              │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │ Context window exhausted
                            │ Session ends
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Session N (Coding Agent - FRESH CONTEXT)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Read git log:                                     │  │
│  │    "feat(streaming): Message streaming ✓"           │  │
│  │ 2. Read progress file:                               │  │
│  │    "Last completed: feature-004                      │  │
│  │     Next priority: feature-006                       │  │
│  │     Known issues: Streaming drops last token"        │  │
│  │ 3. Read feature_list.json:                           │  │
│  │    feature-004: passes=true                          │  │
│  │    feature-006: passes=false (NEXT)                  │  │
│  │ 4. Verify app works (basic E2E test)                 │  │
│  │ 5. Start working on feature-006...                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Context Engineering Components

각 시나리오는 이 Main Scenario의 특정 부분을 담당합니다:

| 시나리오                 | Main Scenario에서의 역할            | Initializer | Coding |
| ------------------------ | ----------------------------------- | ----------- | ------ |
| 1. Rolling Window        | 대화가 길어질 때 오래된 메시지 제거 | -           | ✓      |
| 2. Auto Summarizer       | Progress file이 너무 길어질 때 압축 | -           | ✓      |
| 3. Tool Output Trimmer   | 브라우저 자동화 로그 압축           | -           | ✓      |
| 4. Feature List Manager  | feature_list.json 생성 및 업데이트  | ✓           | ✓      |
| 5. Git Progress Tracker  | Git 커밋 + progress file 관리       | ✓           | ✓      |
| 6. State Recovery        | 세션 시작 시 컨텍스트 복원          | -           | ✓      |
| 7. Incremental Work      | 한 번에 하나의 기능만 작업          | -           | ✓      |
| 8. Test Validator        | End-to-end 테스트 실행 및 검증      | -           | ✓      |
| 9. Clean State Committer | 세션 종료 시 깨끗한 상태 유지       | -           | ✓      |

## 📊 성공 메트릭

### 정량적 지표

- **Feature Completion Rate**: 완료된 기능 / 전체 기능
- **Session Productivity**: 세션당 완료된 기능 수
- **Bug Introduction Rate**: 새 기능이 기존 기능을 망가뜨리는 비율
- **Context Recovery Time**: 세션 시작 후 생산적 작업까지 걸리는 시간

### 정성적 지표

- **Clean Handoffs**: 다음 세션이 즉시 작업 시작 가능한가?
- **Code Quality**: 코드가 읽기 쉽고 유지보수 가능한가?
- **Test Coverage**: 기능들이 실제로 동작하는가?

## 🎓 실습 계획 (7주)

### Week 1-2: Context Fundamentals

**목표**: 컨텍스트 예산 관리 기초

- Day 1-2: **시나리오 1 (Rolling Window)**
  - 구현: `rolling_window_middleware.py`
  - 테스트: `test_1_rolling_window.py`
- Day 3-4: **시나리오 2 (Auto Summarizer)**
  - 구현: `summarizer_middleware.py`
  - 테스트: `test_2_summarizer.py`
- Day 5-6: **시나리오 3 (Tool Output Trimmer)**
  - 구현: `tool_output_trimmer.py`
  - 테스트: `test_3_trimmer.py`

### Week 3-4: State Management

**목표**: 상태 영속성 및 복원

- Day 1-2: **시나리오 4 (Feature List Manager)**
  - 구현: `feature_manager.py`
  - 테스트: `test_4_feature_manager.py`
- Day 3-4: **시나리오 5 (Git Progress Tracker)**
  - 구현: `git_tracker.py`
  - 테스트: `test_5_git_tracker.py`
- Day 5-6: **시나리오 6 (State Recovery)**
  - 구현: `state_recovery.py`
  - 테스트: `test_6_state_recovery.py`

### Week 5-6: Quality Assurance

**목표**: 점진적 개발 및 검증

- Day 1-2: **시나리오 7 (Incremental Work)**
  - 구현: `work_controller.py`
  - 테스트: `test_7_work_controller.py`
- Day 3-4: **시나리오 8 (Test Validator)**
  - 구현: `test_validator.py`
  - 테스트: `test_8_test_validator.py`
- Day 5-6: **시나리오 9 (Clean State)**
  - 구현: `state_committer.py`
  - 테스트: `test_9_state_committer.py`

### Week 7: Full Integration

**목표**: Main Scenario 구현

**Day 1-2: Initializer Agent**

```python
# initializer_agent.py
class InitializerAgent:
    def run(self, project_description: str):
        # 1. Parse requirements
        features = self.extract_features(project_description)

        # 2. Create feature list (Scenario 4)
        feature_list = create_feature_list(features)
        save_json("feature_list.json", feature_list)

        # 3. Initialize git (Scenario 5)
        initialize_git_repo(project_description)

        # 4. Create init.sh
        self.create_init_script()

        # 5. Create progress file
        Path("claude-progress.txt").write_text(
            f"# {project_description}\n\nProject initialized.\n"
        )

        # 6. First commit
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "Initial project setup"])
```

**Day 3-4: Coding Agent**

```python
# coding_agent.py
class CodingAgent:
    def run_session(self):
        # 1. Recover context (Scenario 6)
        state = recover_session_state()
        inject_context_to_prompt(state)

        # 2. Select next feature (Scenario 7)
        feature_list = load_json("feature_list.json")
        next_feature = select_next_feature(feature_list)

        if next_feature is None:
            print("🎉 All features complete!")
            return

        # 3. Implement feature
        print(f"Working on: {next_feature['id']}")
        self.implement_feature(next_feature)

        # 4. Test (Scenario 8)
        test_result = run_e2e_test(next_feature["id"])
        if not test_result.passed:
            self.fix_issues(test_result)

        # 5. Commit (Scenario 5 + 9)
        commit_progress(next_feature["id"], next_feature["description"])

        # 6. Clean state check (Scenario 9)
        report = verify_clean_state()
        if not report.is_clean:
            self.fix_state_issues(report)
```

**Day 5: Testing**

- Integration test: Run Initializer + 3 Coding sessions
- Verify: 3 features completed, clean state maintained

**Day 6-7: Real Project**

- 실제 웹앱 구축 (선택):
  - Todo App (간단)
  - Blog Platform (중간)
  - Chat App (복잡)

## 🚀 Quick Start

### 1. 환경 설정

```bash
cd ax_advanced_class
pip install -r requirements.txt
playwright install chromium
```

### 2. 개별 시나리오 실습

```bash
# 시나리오 1부터 순서대로
pytest tests/test_1_rolling_window.py -v
pytest tests/test_2_summarizer.py -v
# ...
```

### 3. Main Scenario 실행

```bash
# Initializer Agent
python main.py init "Build a simple blog with posts and comments"

# Coding Agent (Session 1)
python main.py code

# Coding Agent (Session 2)
python main.py code

# ... repeat until all features complete
```

### 4. 진행 상황 확인

```bash
# Feature list 상태
python -c "import json; f=json.load(open('feature_list.json')); print(f'Progress: {sum(1 for x in f[\"features\"] if x[\"passes\"])}/{len(f[\"features\"])}')"

# Git history
git log --oneline --graph

# Latest progress
head -n 20 claude-progress.txt
```

## 📚 참고 자료

### 필독

- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Claude Prompting Guide](https://docs.anthropic.com/claude/docs/prompts)

### 추가 학습

- [LangGraph Multi-Agent Systems](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Test-Driven Development](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [Playwright End-to-End Testing](https://playwright.dev/docs/intro)

## 🎉 Expected Outcomes

이 Main Scenario를 완료하면:

1. ✅ **Long-running agent의 핵심 문제**를 이해하고 해결책을 구현할 수 있습니다
2. ✅ **Context Engineering 9가지 패턴**을 실전에 적용할 수 있습니다
3. ✅ **Two-agent architecture** (Initializer + Coding)를 설계하고 구현할 수 있습니다
4. ✅ **여러 세션에 걸친 점진적 개발** 전략을 실무에 적용할 수 있습니다
5. ✅ **프로덕션급 에이전트 시스템**을 설계할 수 있는 역량을 갖춥니다

---

**Ready to build long-running agents? Let's start with Scenario 1!** 🚀
