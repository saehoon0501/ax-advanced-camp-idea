## ax-incubation-advanced-camp-idea-dexter

**Context Engineering(컨텍스트 엔지니어링) 실습용 미니 레포**입니다.  
문서(`scenarios/`)로 패턴을 이해하고, 코드(`ax_advanced_class/`)로 구현한 뒤, 테스트(`tests/`)로 검증하는 형태로 구성되어 있습니다.

### Directory guide (무슨 폴더가 무슨 용도인가?)
- **`ax_advanced_class/`**: 실습용 파이썬 구현 코드(“정답”이 아니라 **학생이 채워 넣는 과제 코드**)
  - **`rolling_window_middleware.py`**: 시나리오 1) Rolling Window — 토큰 예산 내에서 오래된 메시지를 제거하되 **System(0번) + 최신 메시지는 보존**
  - **`summarizer_middleware.py`**: 시나리오 2) Auto Summarizer — 오래된 히스토리를 요약으로 압축(계층형 메모리)
  - **`tool_output_trimmer.py`**: 시나리오 3) Tool Output Trimmer — 장황한 툴 JSON을 스키마 기반으로 핵심만 남김(Observation compaction)
  - **`tool_selector.py`**: 시나리오 7) Tool Selector — 질의 의도에 따라 **필요한 툴만 노출/선택**(least privilege + context budget)
  - **`scenarios/`**: 1~9 시나리오 문서(원칙 → 요구사항 → 실패모드 → 테스트 아이디어)
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

- **2) 코드를 구현(또는 확장)해서 “컨텍스트 파이프라인”을 만든다**
  - **Rolling Window**: 토큰 예산을 지키되 System/최신을 강제 보존
  - **Auto Summarizer**: 삭제 대신 요약으로 의미를 보존(계층형 메모리)
  - **Tool Output Trimmer**: Observation을 짧게 정규화해 컨텍스트 낭비 제거
  - **Tool Selector**: 지금 필요한 툴만 노출해 비용/혼란/리스크 감소

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

