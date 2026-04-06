목차


토큰의 정의: 글자도, 단어도 아닌 것
영어 vs 한글 Tokenization 비교
메세지 포맷이 토큰 효율에 미치는 영향
비효율적인 포맷 vs 효율적인 포맷
Information Density 원칙
Prompt Caching 작동 원리
캐싱 원리
캐싱 최대화 전략
Dynamic Prompt에서 캐시 적중률 높이기
방법 1: 조건부 내용을 뒤로 밀기
방법 2: Tool 정의 순서 고정
방법 3: 자주 쓰는 Tool은 항상 포함
Compaction(압축)
Truncation(잘라내기) vs Summarization(요약)
점진적 요약(Progressive Summarization) 패턴
Sub-Agent를 이용한 요약


토큰의 정의: 글자도, 단어도 아닌 것
LLM에서 "토큰"은 모델이 처리하는 기본 단위입니다. 중요한 점은 토큰 ≠ 글자 ≠ 단어라는 것입니다.
토큰은 Byte Pair Encoding (BPE) 또는 유사한 알고리즘으로 생성된 서브워드(subword) 단위입니다. 자주 등장하는 문자열은 하나의 토큰으로, 드문 문자열은 여러 토큰으로 분해됩니다.

LLM 모델마다 다른 Token을 가지고 있기에 Input이 같더라도 모델에 따라 Token 수는 다를 수 있습니다. 



영어 vs 한글 Tokenization 비교
"Hello, world!"	영어	4 토큰
"안녕하세요!"	한글	5~7 토큰
"The quick brown fox"	영어	4 토큰
"빠른 갈색 여우"	한글	6~8 토큰


기본적으로 한글은 영어보다 토큰 효율이 낮습니다.
같은 의미를 전달하는데 더 많은 토큰이 필요합니다. 이는 대부분의 LLM이 영어 중심으로 학습되었기 때문입니다.
또한 이 때문에 프롬프팅 시, 영어로 구성했을 때 성능이 더 개선될 수 있습니다.



메세지 포맷이 토큰 효율에 미치는 영향
같은 정보라도 어떻게 표현하느냐에 따라 토큰 소비가 크게 달라집니다.

비효율적인 포맷 vs 효율적인 포맷
예시 1: Tool 결과 반환



// 비효율적 (장황한 자연어)
{
  "role": "tool",
  "content": "The weather API has returned the following information: The current temperature in Seoul, South Korea is 25 degrees Celsius. The humidity level is at 60 percent, and the wind speed is 10 kilometers per hour from the northwest direction."
}
// → 약 60 토큰

// 효율적 (구조화된 간결한 표현)
{
  "role": "tool",
  "content": "Seoul: 25°C, humidity 60%, wind 10km/h NW"
}
// → 약 20 토큰
3배의 토큰 절약이 가능합니다.



예시 2: 에러 메세지



// 비효율적
{
  "content": "An error occurred while trying to execute the requested operation. The system encountered an issue with the database connection. The specific error message from the database server indicates that the connection was refused because the maximum number of connections has been reached. Please try again later or contact the system administrator for assistance."
}
// → 약 70 토큰

// 효율적
{
  "content": "Error: DB connection refused (max connections). Retry later."
}
// → 약 15 토큰


Information Density 원칙
정보 밀도(Information Density)란 토큰당 전달되는 유용한 정보의 양입니다.

불필요한 수식어 제거	"very", "really", "actually" 등	
"very important" → "CRITICAL"(영어의 경우 단어를 대문자로 사용할 경우 의미가 강조됨)

구조화된 포맷 사용	JSON, 표, 리스트	문단 설명 → key:value 쌍
약어/기호 활용	문맥상 명확할 때	"temperature" → "temp"
중복 제거	같은 정보 반복 금지	매번 "서울의 날씨는..." 반복 x


Prompt Caching 작동 원리
대부분의 LLM API는 Prompt Caching을 지원합니다. 이전 요청과 동일한 prefix가 있으면, 해당 부분의 연산을 재사용하여 비용과 지연 시간을 절감합니다.

캐싱 원리




요청 1: [System Prompt] + [Tool 정의] + [User: "안녕"]
        ─────────────────────────────────
        이 부분이 캐시됨

요청 2: [System Prompt] + [Tool 정의] + [User: "날씨 알려줘"]
        ─────────────────────────────────
        캐시 히트! 재계산 불필요    ↑ 이 부분만 새로 처리


캐싱 최대화 전략
핵심은 고정된 부분(prefix)을 앞에, 동적인 부분을 뒤에 배치하는 것입니다.





┌─────────────────────────────────────────────────────────────┐
│  [1. System Prompt]     - 항상 동일                         │
│  [2. 고정 Tool 정의]    - 변하지 않는 도구 스키마           │  ← 캐시 가능 영역
│  [3. 공통 Examples]     - 표준 예시들                       │
├─────────────────────────────────────────────────────────────┤
│  [4. 동적 Tool 정의]    - 이번 요청에만 필요한 도구          │
│  [5. 대화 히스토리]     - 이전 메시지들                      │  ← 매번 새로 처리
│  [6. 현재 User 입력]    - 이번 요청                          │
└─────────────────────────────────────────────────────────────┘


Dynamic Prompt에서 캐시 적중률 높이기
Agent는 상황에 따라 다른 도구나 지시사항이 필요합니다. 이때도 캐싱을 최대화할 수 있습니다:

방법 1: 조건부 내용을 뒤로 밀기




# 나쁜 예: 동적 내용이 앞에
prompt = f"""
현재 작업: {current_task}  # 매번 다름 → 캐시 무효화
당신은 코딩 에이전트입니다...
"""

# 좋은 예: 고정 내용이 앞에
prompt = f"""
당신은 코딩 에이전트입니다...  # 항상 동일 → 캐시 유지
[긴 고정 지시사항들...]

---
현재 작업: {current_task}  # 동적 부분은 뒤에
"""


방법 2: Tool 정의 순서 고정




# 나쁜 예: Tool 순서가 매번 다름
tools = random.shuffle([tool_a, tool_b, tool_c])

# 좋은 예: Tool 순서 고정
tools = sorted([tool_a, tool_b, tool_c], key=lambda t: t.name)


방법 3: 자주 쓰는 Tool은 항상 포함




# 3-5개의 핵심 도구는 항상 로드 (캐시 대상)
CORE_TOOLS = [read_file, write_file, bash, search]

# 나머지는 필요할 때만 동적 로드
OPTIONAL_TOOLS = [database_query, api_call, ...]


Compaction(압축)
컨텍스트가 한계에 가까워지면 Conversation History에 대한 압축이 필요합니다. 크게 두 가지 접근법이 있습니다

Truncation(잘라내기) vs Summarization(요약)
Truncation	빠름, 결정적	중요한 정보 손실
Summarization	의미 보존	LLM 호출 필요(비용, 지연)
대부분의 경우 Summarization이 더 효과적입니다. 단, 적절한 전략이 필요합니다.



점진적 요약(Progressive Summarization) 패턴
모든 것을 한 번에 요약하는 대신, 단계적으로 요약합니다.





[원본: 30턴 대화, 60K 토큰]
        │
        ▼ 임계값 초과 시
[압축 후]
┌─────────────────────────────────────────────────────────────┐
│ ## 이전 대화 요약 (System Message로 삽입)                    │
│                                                              │
│ - 파일 읽음: src/api.ts (REST API 구조 확인)                 │
│ - 파일 생성: src/streaming.ts (WebSocket 엔드포인트)         │
│ - 해결한 이슈: async 핸들러 누락, 이벤트 포맷, 인증          │
│ - 결정사항: SSE 대신 WebSocket 선택 (양방향 통신 필요)       │
│ - 현재 상태: 기본 스트리밍 동작, 엣지 케이스 남음            │
└─────────────────────────────────────────────────────────────┘
        +
[최근 5개 메시지는 원문 유지]
        │
        ▼
[결과: ~15K 토큰, 핵심 정보 보존]

이를 통해 현재 LLM이 집중해야 하는 작업에 대한 정보는 모두 보존하는 동시에, 이전 기록의 context 크기를 줄일 수 있습니다.



Sub-Agent를 이용한 요약
Orchestrator-Workers 패턴과 같이 Sub-agent를 활용하여, 부수적인 작업 과정은 모두 Sub에게 위임하고 필요한 결과만 요약하여 받을 수 있습니다.





# Sub-Agent 내부: 30턴, 8000 토큰의 작업
messages = [
    User: "블로그 앱 만들어",
    AI: "요구사항 분석 중...",
    Tool: mkdir("src"),
    Tool: write_file("feature_list.json", ...),
    # ... 많은 중간 과정 ...
    AI: "✓ 15개 기능 정의 완료, 코딩 준비됨"
]

# Orchestrator에게 반환: 요약만
return AIMessage(content="✓ 15개 기능 정의 완료, 코딩 준비됨")
# → 1개 메시지, ~50 토큰