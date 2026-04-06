# Agent Harness

## Sentence-by-Sentence Translation Map

---

### Section: Introduction / Reference

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | 참고: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | Reference: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents |
| 2 | 이 글은 Anthropic의 tech 아티클을 기반으로, 장기 실행 AI 에이전트가 겪는 문제를 Context Engineering 관점에서 어떻게 정의하고, 어떤 설계로 해결했는지를 설명하기 위한 교육용 정리입니다. | This document is an educational summary based on Anthropic's tech article, explaining how the problems faced by long-running AI agents are defined from a Context Engineering perspective and what design solutions were applied. |

---

### Section: What is Agent Harness

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 3 | Agent Harness는 LLM을 감싸는 제어 계층(control layer)입니다. | Agent Harness is a control layer that wraps around an LLM. |
| 4 | Stateless인 모델을 도구를 사용하고, 스스로 수정하며, 여러 세션에 걸쳐 작동하는 프로덕션 에이전트로 변환하는 모든 코드, 설정, 실행 로직을 의미합니다. | It refers to all the code, configuration, and execution logic that transforms a stateless model into a production agent capable of using tools, self-correcting, and operating across multiple sessions. |
| 5 | 공식적으로는 Agent = Model + Harness로 정의됩니다. | Officially, it is defined as Agent = Model + Harness. |
| 6 | 비유하자면, 말(Horse)은 혼자서도 강력하지만 농사에는 쓸 수 없습니다. | By analogy, a horse is powerful on its own but cannot be used for farming. |
| 7 | 마구(Harness)가 말의 힘을 유용한 작업으로 방향을 잡아줍니다. | A harness directs the horse's power toward useful work. |
| 8 | LLM도 마찬가지입니다 — 모델은 강력하지만, harness 없이는 프로덕션에서 신뢰할 수 없습니다. | The same applies to LLMs — the model is powerful, but without a harness, it cannot be trusted in production. |

---

### Section: Why Harness Matters More Than the Model

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 9 | 직관적으로는 "더 좋은 모델 = 더 좋은 결과"라고 생각합니다. | Intuitively, we assume "better model = better results." |
| 10 | 하지만 실증 데이터가 이를 뒤집습니다. | But empirical data overturns this assumption. |
| 11 | 같은 모델 가중치로, harness만 바꿔서 이 정도의 차이가 발생합니다. | With the same model weights, just changing the harness produces this much of a difference. |
| 12 | 왜 그런가? LLM이 채울 수 없는 6가지 근본적 gap 때문입니다. | Why? Because there are six fundamental gaps that LLMs cannot fill on their own. |
| 13 | 핵심: 프로덕션 에이전트의 품질은 모델 지능이 아니라 인프라(harness)가 결정합니다. | Key point: The quality of a production agent is determined not by model intelligence but by infrastructure (harness). |

---

### Section: Anthropic's Goal — From Context to Harness

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 14 | 목표: Claude 기반 코딩 에이전트를 통해, 여러 번의 실행과 많은 Context window에 걸쳐서 웹 애플리케이션을 점진적으로 구현·개선하여, 미리 정해진 기능 목록을 실제로 만족하고 브라우저에서 끝까지 동작하는 상태에 도달하는 것입니다. | The goal is to use a Claude-based coding agent to incrementally build and improve a web application across multiple runs and context windows, ultimately satisfying a predefined feature list and reaching a state where everything works end-to-end in the browser. |
| 15 | 좀 더 풀어서 말하면, 에이전트는 다음을 목표로 합니다. | In more detail, the agent aims for the following. |
| 16 | 단순히 "코드를 좀 쓰는 것"이 아니라, 사전에 정의된 기능 목록의 각 항목을 실제로 동작할 때까지 구현하고, 그때에만 완료로 표시하는 것. | Not simply "writing some code," but implementing each item in a predefined feature list until it actually works, and only then marking it as complete. |
| 17 | 레포지토리, 테스트, 진행 로그, 브라우저 확인 등을 활용해 여러 번의 실행에 걸쳐 앱을 반복적으로 디버깅하고 개선하는 것. | Using the repository, tests, progress logs, and browser verification to iteratively debug and improve the app across multiple runs. |
| 18 | 이후 실행될 다른 에이전트나 사람이 "어디까지 되었고, 무엇이 깨져 있고, 다음에 무엇을 해야 하는지"를 명확히 이해할 수 있도록, 프로젝트를 장기 개발에 적합한 상태로 남겨두는 것. | Leaving the project in a state suitable for long-term development, so that subsequent agents or humans can clearly understand "what has been done, what is broken, and what needs to be done next." |

---

### Section: Problems Faced

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 19 | LLM은 stateless 기반이기에, 상태 정보를 보존하지 않습니다. | Since LLMs are stateless by nature, they do not preserve state information. |
| 20 | 따라서, 세션이 끊기면 모델은 이전 작업의 맥락을 전혀 알 수 없습니다. | Therefore, when a session ends, the model has no knowledge of the previous work context. |
| 21 | 이때 에이전트는 이전까지 작업 상태를 알 수 없기 때문에 스스로 그 상태를 추론하거나 상상하려고 시도하고 그 추론이 점점 누적되면서 작업이 틀어집니다. | At this point, since the agent cannot know the previous work state, it tries to infer or imagine that state on its own, and as these inferences accumulate, the work goes off track. |
| 22 | 실제 장기 실행 시나리오에서는 다음과 같은 치명적인 Agent 실행 패턴이 반복됩니다. | In real long-running scenarios, the following critical agent execution patterns recur. |
| 23 | 한 번에 너무 많은 것을 시도하는 경우 (one-shotting) → context 중간에 기능이 반만 구현되고 끊긴다. | Trying too much at once (one-shotting) — features end up half-implemented when the context runs out. |
| 24 | 이미 구현된 기능을 다시 구현하는 경우 → "이게 끝났는지 아닌지"를 판단할 근거가 없음. | Re-implementing features that were already built — there is no basis for judging "whether this is done or not." |
| 25 | 전체 작업이 끝났다고 잘못 판단하고 종료하는 경우 → 명시적인 완료 조건이 없음. | Incorrectly concluding that all work is done and terminating — there are no explicit completion criteria. |
| 26 | Q. 그런데 Claude Agent SDK에는 compaction이 있는데, 왜 이걸로는 충분하지 않나요? | Q. But the Claude Agent SDK has compaction — why isn't that sufficient? |
| 27 | A. compaction은 대화를 요약해 다음 컨텍스트에 넘겨줄 수 있지만, 중요한 구현 의도나 중간 상태가 요약 과정에서 사라지거나 애매하게 남으면서, 다음 세션의 에이전트가 추측해야 하는 상황이 자주 발생합니다. | A. Compaction can summarize conversations and pass them to the next context, but important implementation intentions and intermediate states often get lost or become ambiguous during summarization, frequently leaving the next session's agent guessing. |

---

### Section: Anthropic's Solution

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 28 | Anthropic에서는 먼저 문제를 두 부분으로 나눴습니다. | Anthropic first split the problem into two parts. |
| 29 | 초기 환경 세팅: 첫 세션에서, 이후의 모든 기능 구현을 위한 뼈대를 갖춘 환경을 세팅. → Initializer agent | Initial environment setup: In the first session, set up a scaffolded environment for all subsequent feature implementation. → Initializer agent |
| 30 | 매 세션마다 점진적(Progressive) 작업: 이후의 코딩 에이전트는 매 세션마다 한두 개의 기능에 집중해 점진적 개발을 진행 → Coding agent | Progressive work each session: The subsequent coding agent focuses on one or two features per session for incremental development. → Coding agent |

---

### Section: Harness Design

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 31 | 정의: 단일 context나 에이전트를 넘어, 에이전트가 여러 context window와 세션에 걸쳐 일관되게 작업하고 상태를 인수인계하도록 강제하는 전체적인 실행/환경 관리 프레임워크 | Definition: A comprehensive execution/environment management framework that goes beyond a single context or agent, enforcing consistent work and state handoff across multiple context windows and sessions. |
| 32 | 구체적으로는 다음과 같은 "외부 구조" 전체를 포함합니다. | Specifically, it encompasses the following "external structures." |
| 33 | initializer agent와 coding agent라는 두 종류의 프롬프트 구성 | Two types of prompt configurations: the initializer agent and the coding agent. |
| 34 | init.sh, claude-progress.txt, git 히스토리 및 커밋 내용, 구조화된 feature 리스트(json), 브라우저 자동화 테스트 도구 등 | init.sh, claude-progress.txt, git history and commit contents, a structured feature list (JSON), browser automation testing tools, etc. |
| 35 | 이를 통해 각 세션이 모델의 기억에 기대지 않고 외부 상태를 읽음으로써 자연스럽게 따르게 됩니다. | This ensures that each session naturally follows along by reading external state rather than relying on the model's memory. |

---

### Section: Core Idea — Implicit Memory to Explicit State

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 36 | Anthropic의 핵심 해결책은 context를 모델 내부의 암묵적 기억에서, 파일·리포지토리·테스트 결과로 구성된 명시적 상태(explicit state)로 전환하는 것이었습니다. | Anthropic's core solution was to shift context from implicit memory inside the model to explicit state composed of files, repositories, and test results. |
| 37 | 이 전략은 크게 네 가지 Context Engineering 요소로 나뉩니다. | This strategy breaks down into four major Context Engineering elements. |

---

### Section: 1. Externalization of Context

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 38 | 첫 번째 요소는 context를 모델 내부가 아니라 외부 아티팩트로 이동시키는 것입니다. | The first element is moving context from inside the model to external artifacts. |
| 39 | Initializer Agent는 초기 세션에서 다음을 수행합니다. | The Initializer Agent performs the following in the initial session. |
| 40 | 전체 요구사항을 구조화된 feature list로 정의하고, 각 기능에 대해 passes: false로 초기화 | Define all requirements as a structured feature list and initialize each feature with passes: false. |
| 41 | 각 기능의 완료 여부를 명확한 boolean 상태로 관리 | Manage the completion status of each feature as a clear boolean state. |
| 42 | 이전 작업 내역과 의사결정을 claude-progress.txt 같은 진행 로그로 기록 | Record previous work history and decisions in a progress log such as claude-progress.txt. |
| 43 | 실행 가능한 초기 코드 상태를 git으로 고정 | Lock the initial runnable code state with git. |
| 44 | 이로 인해 context는 더 이상 "대화 속에 흩어진 정보"가 아니라, 파일 시스템과 리포지토리에 존재하는 상태가 됩니다. | As a result, context is no longer "information scattered across conversations" but state that exists in the file system and repository. |
| 45 | 에이전트는 기억할 필요 없이 읽기만 하면 됩니다. | The agent only needs to read — it does not need to remember. |

---

### Section: 2. Context Interpretation Protocol ("Getting Up to Speed")

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 46 | 두 번째 요소는 에이전트가 상태를 해석하는 과정을 시스템적으로 강제한 것입니다. | The second element is systematically enforcing the process by which the agent interprets state. |
| 47 | 모든 Coding Agent는 세션 시작 시 다음과 같은 4단계 프로토콜을 반드시 수행합니다. | Every Coding Agent must perform the following four-step protocol at the start of each session. |
| 48 | pwd 및 ls로 현재 작업 디렉토리 확인 | Check the current working directory with pwd and ls. |
| 49 | git log와 진행 로그 파일을 읽어 과거 이력 파악 | Read git log and the progress log file to understand past history. |
| 50 | features.json을 읽어 우선순위가 높은 미완료 기능 하나를 선택 | Read features.json and select one high-priority incomplete feature. |
| 51 | init.sh를 실행하여 개발 서버를 띄우고 기본 상태 점검 | Run init.sh to start the development server and perform basic status checks. |
| 52 | 이 프로토콜은 모델의 "창의성"이 개입할 여지를 없애고, 모든 세션이 동일한 관찰 절차를 거쳐 같은 전제 위에서 판단하게 만들어 줍니다. | This protocol eliminates room for the model's "creativity" to intervene and ensures all sessions go through the same observation procedure to make decisions on the same foundation. |

---

### Section: 3. Git as Safety Net and Work Unit Isolation

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 53 | 세 번째 요소는 에이전트의 실수를 전제로 한 복구 메커니즘입니다. | The third element is a recovery mechanism that assumes the agent will make mistakes. |
| 54 | Git Revert 활용: git commit은 단순한 기록용이 아닙니다. | Using Git Revert: git commit is not just for record-keeping. |
| 55 | 에이전트가 코드를 망가뜨렸을 때, 즉시 이전의 작동하는 상태로 되돌리는 안전장치입니다. | It is a safety mechanism for immediately reverting to a previous working state when the agent breaks the code. |
| 56 | 작업 단위 제한: Coding 에이전트에게 한 번에 하나의 기능만 처리하도록 강제했습니다. | Work unit restriction: The coding agent was forced to handle only one feature at a time. |
| 57 | 이는 컨텍스트가 복잡해지는 것을 막고, 각 단계가 독립적으로 검증 가능하게 만듭니다. | This prevents context from becoming overly complex and makes each step independently verifiable. |

---

### Section: 4. Enforcing End-to-End Testing

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 58 | 마지막으로 가장 중요한 요소는, "완료"의 정의를 모델의 판단이 아닌 실제 E2E 테스트 통과 여부로 고정하는 것입니다. | Finally, the most important element is anchoring the definition of "done" not to the model's judgment but to whether actual E2E tests pass. |
| 59 | 실제 브라우저를 띄워 페이지를 로드하고, 버튼 클릭, 폼 입력 등 사용자 시나리오를 실행 | Launch a real browser, load the page, and execute user scenarios such as button clicks and form inputs. |
| 60 | 이 테스트를 통과해야만 features.json의 해당 항목을 passes: true로 변경할 수 있습니다. | Only after passing these tests can the corresponding entry in features.json be changed to passes: true. |

---

### Section: Compound Reliability — Why One at a Time

| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 61 | Anthropic이 "한 번에 하나의 기능만"을 강제하는 것은 단순한 경험 법칙이 아니라, 수학적 근거가 있습니다. | Anthropic's enforcement of "only one feature at a time" is not just a rule of thumb — it has a mathematical basis. |
| 62 | 각 step의 성공률이 95%라고 가정합니다. | Assume each step has a 95% success rate. |
| 63 | 충분히 높아 보입니다. | That seems high enough. |
| 64 | 하지만 10개 step을 순차적으로 실행하면: 전체 성공률 = 0.95^10 = 59.9% | But if you run 10 steps sequentially: overall success rate = 0.95^10 = 59.9%. |
| 65 | 이것이 Compound Reliability Problem입니다. | This is the Compound Reliability Problem. |
| 66 | Google DeepMind의 2025년 연구에서 180개 설정을 테스트한 결과, 비구조화된 multi-agent 네트워크는 단일 에이전트 대비 오류를 최대 17.2배 증폭시켰습니다. | In a 2025 Google DeepMind study testing 180 configurations, unstructured multi-agent networks amplified errors by up to 17.2x compared to a single agent. |
| 67 | Anthropic의 "하나의 기능만" 규칙은 이 문제에 대한 직접적 대응입니다. | Anthropic's "one feature only" rule is a direct response to this problem. |
| 68 | 작업 단위를 작게 유지하면: 각 세션의 성공 확률이 높아지고 | Keeping work units small increases the success probability of each session, |
| 69 | 실패해도 git revert로 복구 가능하고 | allows recovery via git revert even upon failure, |
| 70 | 다음 세션에서 깨끗한 상태로 재시도할 수 있습니다. | and enables retrying from a clean state in the next session. |
| 71 | 핵심: Harness가 작업 단위를 격리하는 이유는 "모범 사례"가 아니라, compound reliability를 제어하기 위한 엔지니어링적 필수 조건입니다. | Key point: The reason Harness isolates work units is not "best practice" — it is an engineering requirement for controlling compound reliability. |
