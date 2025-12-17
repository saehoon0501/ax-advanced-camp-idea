## ax-incubation-advanced-camp-idea-dexter

**Context Engineering(컨텍스트 엔지니어링) 실습용 미니 레포**입니다.  
문서(`scenarios/`)로 패턴을 이해하고, 코드(`ax_advanced_class/`)로 구현한 뒤, 테스트(`tests/`)로 검증하는 형태로 구성되어 있습니다.

### Directory guide (무슨 폴더가 무슨 용도인가?)

- **`ax_advanced_class/`**: 실습용 파이썬 구현 코드("정답"이 아니라 **학생이 채워 넣는 과제 코드**)

  - 주요 미들웨어: `rolling_window_middleware.py`, `summarizer_middleware.py`, `tool_output_trimmer.py`, `tool_selector.py` 등
  - **`scenarios/`**: 1~9 시나리오 문서(원칙 → 요구사항 → 실패모드 → 테스트 아이디어)
  - **`orchestrator.py`**: 여러 컨텍스트 엔지니어링 기법을 조합하여 실제 에이전트 구성
  - **`data/`**: (필요 시) 실습용 입력/예시 데이터 보관 장소

- **`tests/`**: 각 시나리오의 요구사항을 고정하는 단위테스트(= “정의된 Done”)

  - 예: `test_1_rolling_window.py`, `test_3_tool_output_trimmer.py`, `test_7_tool_selector.py`

- **`pyproject.toml` / `uv.lock`**: 의존성/환경 정의(uv 사용 권장)

### How to practice context engineering (이 레포로 연습하는 방법)

이 레포는 “프롬프트를 길게 쓰는 법”보다, **컨텍스트를 설계/관리하는 로직을 코드로 고정**하는 연습에 초점이 있습니다.

- **1) 시나리오 문서로 패턴을 먼저 이해**  
  `ax_advanced_class/scenarios/`에서 해당 번호 문서를 읽고,

  - **무엇을 보존해야 하는지**(System, 최신 메시지, 근거 컨텍스트 등)
  - **무엇을 줄여야 하는지**(오래된 히스토리, 장황한 관측값, 불필요한 툴 스키마 등)
  - **실패 모드**(정책 유실, 최신 질의 누락, 단위 혼동, 도구 과다 노출 등)
    를 체크합니다.

- **2) 코드를 구현(또는 확장)해서 "컨텍스트 파이프라인"을 만든다**  
  각 시나리오(Rolling Window, Auto Summarizer, Tool Output Trimmer, Tool Selector 등)를 구현하여 컨텍스트를 효율적으로 관리합니다.

- **3) 테스트로 검증하고, 실패 모드 케이스를 추가한다**
  `tests/`는 “컨텍스트 엔지니어링 정책을 코드로 고정(Policy-as-Code)”하는 장치입니다.
  시나리오 문서의 실패 모드를 테스트로 추가하면 실무 감각이 빠르게 늘어납니다.

### Initialize (init) and run tests

#### Option A) Using `uv` (recommended)

```bash
cd /Users/sehoonbyun/Documents/ax-incubation-advanced-camp-idea-dexter
uv sync
uv run python -m unittest discover -s tests -p 'test*.py' -q
```

#### Option B) Plain venv + pip (fallback)

```bash
cd /Users/sehoonbyun/Documents/ax-incubation-advanced-camp-idea-dexter
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install langchain langchain-aws langgraph
python -m unittest discover -s tests -p 'test*.py' -q
```

### Suggested progression (권장 순서)

문서에 적힌 권장 순서 그대로 진행하면 좋습니다:
`1 → 2 → 6 → 5 → 3 → 4 → 7 → 8 → 9`

### Final Integration: Building the Coach Agent (최종 통합)

개별 시나리오에서 구현한 컨텍스트 엔지니어링 기법들은 **`orchestrator.py`**에서 조합되어 실제 동작하는 에이전트를 구성합니다.

- **Orchestrator**: 여러 미들웨어(Rolling Window, Tool Selector, Summarizer 등)를 파이프라인으로 연결
- **Coach Agent**: Orchestrator가 관리하는 컨텍스트를 기반으로 학습자에게 맞춤형 코칭 제공
- 각 기법이 독립적으로 동작하면서도 함께 작동하여 효율적이고 안정적인 에이전트 시스템 구현

실습을 완료한 후 `main.py`나 `orchestrator.py`를 실행하여 통합된 Coach Agent가 어떻게 동작하는지 확인할 수 있습니다.
