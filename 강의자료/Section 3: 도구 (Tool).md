목차



Tool Definition 문제
실제 시나리오
Tool Search Tool(Defer loading)
defer_loading 패턴
효과 
Claude Skills로의 발전
Programmatic Tool Calling(코드 기반 오케스트레이션)
기존 LLM-Tool 상호작용 방식의 문제
Programmatic 방식
Programmatic 방식 적용 조건:
Tool Output 관리
Intermediate Result Pollution
Tool Ouput 크기 제한 전략


Tool Definition 문제
Anthropic의 연구에 따르면, Tool 정의만으로 50,000+ 토큰이 소비될 수 있습니다.

실제 시나리오
MCP(Model Context Protocol) 서버 여러 개를 연결한 개발 환경을 생각해보겠습니다:

GitHub	15	~ 8,000
Slack	10	~5,000
Sentry	8	~ 4,000
Grafana	12	~ 6,000
Splunk	10	~ 5,000
합계	55	~ 28,000
여기에 각 Toold 상세 스키마(파라미터, 예시 등)까지 포함하면, 많은 Tool만으로 Context의 많은 부분을 차지합니다. 



MCP란?

MCP 서버는 LLM이 동적으로 발견(discover)하고 호출할 수 있는 Tool들을 표준 형식으로 제공하는 레지스트리(registry) 겸 실행 엔드포인트입니다.
즉, 에이전트가 런타임에 list_tools()로 사용 가능한 Tool 목록을 조회한 뒤, Function Calling을 통해 필요한 Tool을 MCP 서버에 요청하면 서버가 실제 로직을 실행하고 결과를 반환하는 구조입니다.



문제: 사용자가 Input을 넣기도 전에 Context의 절반이 이미 차 있습니다.



[200K 컨텍스트 윈도우]

┌────────────────────────────────────────────────────────────┐
│████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│← Tool 정의 55K →          │← 실제 작업 가능 영역 145K →   │
└────────────────────────────────────────────────────────────┘


Tool Search Tool(Defer loading)
Anthropic이 제안한 해결책은 필요할 때만 도구를 로드하는 것입니다.





기존 방식:
  시작 시 모든 Tool 로드 → 77K 토큰 소비 → 작업 시작

새로운 방식:
  핵심 Tool만 로드 (5개) → 8.7K 토큰
  필요 시 Tool 검색 → 해당 Tool만 추가 로드


defer_loading 패턴


tools = [
    # 항상 로드 (핵심 도구)
    {"name": "read_file", "defer_loading": False},
    {"name": "write_file", "defer_loading": False},
    {"name": "bash", "defer_loading": False},

    # 필요 시 로드 (지연 로딩)
    {"name": "github_create_pr", "defer_loading": True},
    {"name": "slack_send_message", "defer_loading": True},
    {"name": "database_query", "defer_loading": True},
    # ... 수십 개의 다른 도구들
]
효과 
토큰만 절약되는 게 아니라 정확도도 상승합니다. Context가 깔끔해지면서 모델이 더 집중할 수 있기 때문입니다.



초기 토큰	77K	8.7K
감소율	-	88.7%
Opus 4 정확도	49%	74%
Opus 4.5 정확도	79.5%	88.1%


Claude Skills로의 발전
Tool Search Tool 개념은 Claude Code의 Skill 시스템으로 발전했습니다.

목적	필요한 Tool 동적 발견	필요한 능력 동적 Load
트리거	검색 쿼리	'/skill-name' 호출
로드 시점	검색 결과 매칭 시	Agent/사용자 명시적 호출 시
저장 위치	Tool 레지스트리	파일 시스템('.claude/skills/')
defer loading 관점에서, Claude Skills는 Tool Search Tool의 확장된 개념입니다.
복잡한 워크플로우, 도메인 지식, Tool 등을 캡슐화하여 재사용 가능하도록 합니다.



Programmatic Tool Calling(코드 기반 오케스트레이션) — 심화 참고

> 이 패턴은 심화 참고자료입니다. 이 과정에서는 위의 **Defer Loading**과 아래의 **Tool Output 관리**에 집중합니다.

Context를 급직적으로 최적화는 방법으로 Agent가 단순 Tool 호출 대신 코드를 작성하여 Tool을 조율하는 것 입니다.



기존 LLM-Tool 상호작용 방식의 문제


Agent가 2,000개의 경비 항목을 분석해야 한다고 가정하겠습니다:



기존 방식 (순차적 Tool 호출):

Turn 1: AI "경비 목록을 가져오겠습니다"
Turn 2: Tool Call: get_expenses()
Turn 3: Tool Result: [2000개 항목, 50KB JSON]  ← 컨텍스트에 전부 들어감
Turn 4: AI "항목을 분석하겠습니다"
Turn 5: AI "카테고리별 합계는..."

→ 50KB가 컨텍스트를 점유, 이후 모든 턴에서 처리해야 함


Programmatic 방식


*User: Backend: Agent에게 제공한 Tool을 실행하는 서버 
*API&Code Execution Tool: 서버와 LLM 사이에 존재하는 Middeware 역할하는 Platform




새로운 방식 (코드 기반):

Turn 1: AI "Python 코드를 작성하여 분석하겠습니다"
Turn 2: Tool Call: execute_code("""
    expenses = get_expenses()  # 샌드박스 내에서 실행
    by_category = {}
    for e in expenses:
        cat = e['category']
        by_category[cat] = by_category.get(cat, 0) + e['amount']
    return by_category  # 요약 결과만 반환
""")
Turn 3: Tool Result: {"식비": 50000, "교통비": 30000, ...}  ← 1KB만 컨텍스트에

→ 50KB 데이터가 컨텍스트를 거치지 않음
기존처럼 Tool 결과 하나하나 LLM에서 처리하는 대신 코드로 처리하게 작업 효율성과 Context 최적화를 극대화 했습니다.

유의할 점: Programmatic 방식을 위해서는 Sandbox 환경 및 Permission Control을 통해 코드를 수행할 수 있도록 하여, 자칫 발생할 수 있는 사고를 사전에 예방할 수 있어야 합니다.

Programmatic 방식 적용 조건:
대량 데이터 집계/필터링

다단계 종속(Dependency) 작업(A결과로 B 호출)

병렬 처리 가능한 작업

데이터 변화 후 모델에 전달


Tool Output 관리
Intermediate Result Pollution
Tool이 Return하는 결과는 기본적으로 메세지 형태로 LLM에 제공됩니다.
때문에 Tool 결과의 형태에 문제가 있다면, Context에 일부분으로서 최적화 대상입니다.



# 문제 상황: 날씨 API가 과도한 정보 반환
weather_result = {
    "location": {"city": "Seoul", "country": "KR", "lat": 37.5, "lon": 127.0, ...},
    "current": {"temp": 25, "feels_like": 27, "humidity": 60, ...},
    "forecast": [/* 7일치 예보 데이터 */],
    "historical": [/* 과거 30일 데이터 */],
    "alerts": [...],
    "metadata": {"station_id": "...", "update_time": "...", ...}
}
# → 2,000+ 토큰

# Agent가 실제로 필요한 것: "서울 25도"


Tool Ouput 크기 제한 전략
Hard Truncation	최대 문자 수 제한	'output[:1000]'
Schema Extraction	필요한 필드만 추출	
def extract_weather(raw_result: dict) -> str:
    """200줄 JSON → 50자 미만 문자열"""
    temp = raw_result.get("current", {}).get("temp", "N/A")
    city = raw_result.get("location", {}).get("city", "Unknown")



    return f"{city}: {temp}°C"
Summarization	LLM으로 요약	에러 로그 요약
Sampling	대표 샘플만	1000개 중 10개만 Message에


실습 연결: Filesystem Middleware 실습에서의 적용

이 섹션에서 배운 개념을 **Filesystem Middleware 실습**에서 직접 구현합니다:

| 이론 | 실습에서의 적용 |
|------|---------------|
| **Defer Loading** | `FilesystemMiddleware`가 핵심 도구 7개만 등록 (전체 MCP 서버 대신) |
| **Tool Output 크기 제한** | `wrap_tool_call`에서 대형 결과(20K+ 토큰)를 파일로 저장하고 미리보기만 반환 |
| **Schema Extraction** | 전용 도구(`edit_file` 등)가 구조화된 입출력으로 불필요한 데이터 최소화 |
| **Soft Rules** | `wrap_model_call`에서 "파일 작업에는 bash 대신 전용 도구 사용" 가이드라인 주입 |