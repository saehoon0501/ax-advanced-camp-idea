# Summarizer Middleware 실습

Coding Agent가 "Message Streaming" 기능을 구현하는 중입니다. 30턴의 디버깅을 거치면서 컨텍스트가 60,000 토큰에 달합니다. 턴 31에서 LLM이 이전 결정사항을 잊어버리고, 이미 해결한 버그를 다시 디버깅하기 시작합니다.

이 실습에서는 **Compaction(압축)** 개념을 직접 구현합니다.

**구현 파일:** `ax_advanced_class/src/middleware/summarization_middleware.py`

## 배운 개념과 실습의 연결

| Section 1 개념 | 이 실습에서 적용하는 방법 |
|----------------|-------------------------|
| Context rot 현상 | 토큰이 쌓이면 성능이 저하됨 → threshold 초과 시 자동 압축 |
| Truncation vs Summarization | 단순 삭제 대신 LLM으로 의미를 보존한 요약 생성 |
| 점진적 요약 패턴 | 최근 N개는 원문 유지, 나머지만 요약으로 교체 |
| Information Density | 요약 프롬프트가 핵심 정보만 추출하도록 설계 |
| Prompt Caching | 미들웨어 순서 — Summarizer를 dynamic_prompt 앞에 배치 |

## 우리가 만들 것

```
LLM 호출 직전 (before_model 훅)
  ↓
토큰 수 체크 — threshold 이하? → 그대로 통과
  ↓
threshold 초과!
  ↓
cutoff 지점 결정 (최근 N개 보존)
  ↓
메시지를 분할: [요약 대상 | 보존 대상]
  ↓
요약 대상 → 별도 LLM으로 요약 생성
  ↓
[요약 HumanMessage] + [보존된 원문] → 압축된 메시지 리스트로 교체
```

**Before:** 30턴, 60,000 토큰
**After:** 요약 1개 + 최근 20개 메시지, ~15,000 토큰 (75% 절감)

## 실습 구조

`summarization_middleware.py`의 3개 메서드가 비워져 있습니다. 순서대로 구현하세요.

`SummarizationMiddlewareBase`(부모 클래스)에 모든 헬퍼가 준비되어 있으므로, 아래 3개 메서드만 override하면 동작합니다.

| TODO | 메서드 | 구현할 것 | 대응하는 개념 |
|------|--------|----------|-------------|
| TODO 1 | `_should_summarize()` | 압축 필요 여부 판단 | Context rot 방지 |
| TODO 2 | `_create_summary()` | LLM으로 요약 생성 | Summarization |
| TODO 3 | `before_model()` | 전체 흐름 조립 | 점진적 요약 패턴 |

---

## TODO 1: _should_summarize() — 압축이 필요한가?

**배울 개념:** Context rot 방지 — 토큰이 임계값을 넘으면 성능이 저하되므로, 그 전에 압축해야 합니다.

이 메서드는 현재 메시지의 토큰 수를 확인하고, 설정된 trigger 조건과 비교하여 압축 여부를 결정합니다.

**이미 제공된 것:**
- `self._trigger_conditions` — `[("tokens", 60000)]` 같은 (종류, 값) 튜플 리스트
- `total_tokens` — 이미 계산된 현재 토큰 수

**구현할 코드:**

```python
def _should_summarize(self, messages: list[AnyMessage], total_tokens: int) -> bool:
    # TODO 1: trigger 조건을 순회하며 압축 필요 여부를 판단하세요
    #
    # self._trigger_conditions는 [(kind, value), ...] 형태입니다.
    # kind는 "messages", "tokens", "fraction" 중 하나입니다.
    #
    # 각 kind별 판단:
    #   "messages" → len(messages) >= value 이면 True
    #   "tokens"   → total_tokens >= value 이면 True
    #   "fraction" → model의 max_input_tokens * value와 비교
    #                (self._get_profile_limits()로 max_input_tokens를 가져옴)
    #
    # 어떤 조건이든 하나라도 True면 압축 필요
    # 모든 조건이 False면 압축 불필요
    #
    return False
```

**확인 포인트:**
- trigger 조건이 비어있으면(`not self._trigger_conditions`) 항상 `False`
- `"fraction"` 조건에서 `self._get_profile_limits()`가 `None`을 반환하면 해당 조건 건너뛰기
- `"tokens"` 조건은 `total_tokens`뿐 아니라 마지막 AIMessage의 `usage_metadata`도 확인 가능 (힌트: `_should_summarize_based_on_reported_tokens()` 이미 구현됨)

---

## TODO 2: _create_summary() — LLM으로 요약 생성

**배울 개념:** Summarization — 의미를 보존하면서 토큰을 줄이는 압축. Information Density가 높은 요약을 생성하는 것이 핵심입니다.

오래된 메시지를 별도의 LLM(Haiku)에게 보내서 구조화된 요약을 받습니다.

**이미 제공된 것:**
- `self.model` — 요약에 사용할 LLM
- `self.summary_prompt` — `{messages}` 플레이스홀더가 있는 요약 프롬프트 (DEFAULT_SUMMARY_PROMPT)
- `self._trim_messages_for_summary()` — 요약 대상 메시지가 너무 길면 잘라주는 헬퍼
- `get_buffer_string()` — 메시지 리스트를 문자열로 변환

**구현할 코드:**

```python
def _create_summary(self, messages_to_summarize: list[AnyMessage]) -> str:
    # TODO 2: 메시지 목록을 LLM으로 요약하세요
    #
    # Step 1: 메시지가 비어있으면 "No previous conversation history." 반환
    #
    # Step 2: self._trim_messages_for_summary(messages_to_summarize)
    #   요약 LLM에 보낼 메시지가 너무 길면 잘라냄
    #   결과가 비어있으면 "Previous conversation was too long to summarize." 반환
    #
    # Step 3: get_buffer_string(trimmed_messages)로 문자열 변환
    #   메시지 객체를 그대로 str()하면 metadata까지 포함되어 토큰이 낭비됨
    #
    # Step 4: self.summary_prompt.format(messages=formatted_messages)
    #   DEFAULT_SUMMARY_PROMPT에 {messages} 자리에 대화 내용을 삽입
    #
    # Step 5: self.model.invoke(formatted_prompt)로 요약 생성
    #   response.text.strip()으로 결과 추출
    #
    # Step 6: 에러 발생 시 "Error generating summary: {error}" 반환
    #   try/except로 감싸기 — 요약 실패가 에이전트 전체를 멈추면 안 됩니다
    #
    return ""
```

**확인 포인트:**
- `get_buffer_string()`을 사용했는지 — 메시지에 `str()`을 직접 쓰면 metadata가 포함되어 토큰 낭비
- try/except로 감쌌는지 — 요약 실패가 에이전트를 멈추면 안 됩니다
- `response.text.strip()`으로 결과를 추출했는지

---

## TODO 3: before_model() — 점진적 요약 패턴 조립

**배울 개념:** 점진적 요약 — 최근 메시지는 원문 유지, 오래된 메시지는 요약으로 교체

`AgentMiddleware`의 `before_model` 훅은 LLM 호출 직전에 실행됩니다. 여기서 메시지를 확인하고, 필요하면 압축된 버전으로 교체합니다.

**이미 제공된 것:**
- `self._should_summarize()` — TODO 1에서 구현
- `self._determine_cutoff_index()` — 이미 구현됨 (보존할 메시지 수에 따라 cutoff 위치 계산)
- `self._partition_messages()` — 이미 구현됨 (cutoff 기준으로 메시지를 둘로 분할)
- `self._create_summary()` — TODO 2에서 구현
- `self._build_new_messages()` — 이미 구현됨 (요약을 HumanMessage로 래핑)
- `self._ensure_message_ids()` — 이미 구현됨 (RemoveMessage에 필요한 ID 부여)
- `REMOVE_ALL_MESSAGES` — 기존 메시지 전부 삭제하는 상수 (langgraph)
- `RemoveMessage` — 특정 메시지 삭제를 지시하는 메시지 타입

**구현할 코드:**

```python
def before_model(self, state: AgentState[Any], runtime: Runtime[ContextT]) -> dict[str, Any] | None:
    # TODO 3: 점진적 요약 패턴을 조립하세요
    #
    # Step 1: state["messages"]에서 메시지 추출
    #   self._ensure_message_ids(messages) 호출 — ID가 없으면 RemoveMessage가 작동 안 함
    #
    # Step 2: 토큰 수 계산
    #   total_tokens = self.token_counter(messages)
    #
    # Step 3: _should_summarize() 호출
    #   False면 None 반환 (변경 없음, 원본 메시지 그대로 LLM에 전달)
    #
    # Step 4: cutoff 지점 결정
    #   cutoff_index = self._determine_cutoff_index(messages)
    #   cutoff_index <= 0이면 None 반환 (요약할 메시지가 없음)
    #
    # Step 5: 메시지 분할
    #   messages_to_summarize, preserved = self._partition_messages(messages, cutoff_index)
    #
    # Step 6: 요약 생성
    #   summary = self._create_summary(messages_to_summarize)
    #
    # Step 7: 새 메시지 구성
    #   new_messages = self._build_new_messages(summary)
    #
    # Step 8: 압축된 상태 반환
    #   return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages, *preserved]}
    #
    #   RemoveMessage(id=REMOVE_ALL_MESSAGES)가 기존 메시지를 전부 지우고,
    #   그 뒤에 [요약 + 보존된 최근 메시지]를 새로 넣는 구조입니다.
    #
    return None
```

**확인 포인트:**
- `None` 반환 = 변경 없음 (압축 불필요할 때)
- `{"messages": [...]}` 반환 = 메시지 교체 (압축 실행)
- `RemoveMessage(id=REMOVE_ALL_MESSAGES)`가 **맨 앞**에 있어야 기존 메시지가 먼저 삭제됨
- `_find_safe_cutoff_point()`(AI/Tool 메시지 쌍 보존)은 부모 클래스에 이미 구현되어 있습니다.

---

## 검증 방법

모든 TODO를 구현한 후:

```bash
uv run python -c "
from ax_advanced_class.src.middleware.summarization_middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage

# _should_summarize 테스트
mw = SummarizationMiddleware(
    model='anthropic:claude-haiku-4-5-20251001',
    trigger=('tokens', 100),
    keep=('messages', 2),
)
short = [HumanMessage(content='hi')]
assert mw._should_summarize(short, 50) == False, 'Short: should not summarize'

long_msgs = [HumanMessage(content='x' * 500) for _ in range(20)]
assert mw._should_summarize(long_msgs, 5000) == True, 'Long: should summarize'
print('_should_summarize — OK')

print('All tests passed')
"
```

---

## 흔한 실패와 대처

| 증상 | 원인 | 해결 |
|------|------|------|
| 요약 후 agent가 이전 작업을 잊음 | 요약이 핵심 결정사항/파일명을 누락 | `DEFAULT_SUMMARY_PROMPT`에 "반드시 보존: 파일 경로, 결정 사항, 에러 해결 방법" 추가 |
| `_find_safe_cutoff_point`가 0 반환 | AI/Tool 메시지 쌍이 전체를 차지 | `keep` 값을 줄이거나 `trigger` threshold를 높여 더 일찍 압축 시작 |
| 요약 LLM 호출 실패 (타임아웃) | Haiku 모델 응답 지연 | `_create_summary`에서 `try/except`로 감싸고 실패 시 truncation fallback |
| 압축 후에도 토큰이 줄지 않음 | `keep` 메시지 수가 너무 많음 | `keep=("messages", 5)` 등으로 줄임 — 최근 대화만 원문 유지 |
| `RemoveMessage`가 적용 안 됨 | messages reducer가 `operator.add`가 아님 | `AgentState`의 messages 필드에 `Annotated[list, operator.add]` 확인 |

---

## 개념 연결 맵

```
배운 개념                       →  이 실습에서 구현한 것
│
├─ Context rot 현상 ──────────→ _should_summarize() (TODO 1)
│   "토큰이 쌓이면 성능 저하"      trigger 조건 체크
│
├─ Truncation vs Summarization → _create_summary() (TODO 2)
│   "삭제 대신 의미 보존 요약"      LLM + 구조화된 프롬프트
│
├─ 점진적 요약 패턴 ──────────→ before_model() (TODO 3)
│   "최근은 원문, 과거는 요약"      분할 → 요약 → RemoveMessage로 교체
│
├─ Information Density ───────→ DEFAULT_SUMMARY_PROMPT (부모 클래스에 제공)
│   "토큰당 정보 밀도를 높여라"     SESSION INTENT / SUMMARY / ARTIFACTS / NEXT STEPS
│
└─ AI/Tool 쌍 무결성 ─────────→ _find_safe_cutoff_point() (부모 클래스에 구현됨)
    "tool_call과 결과는 함께"       cutoff이 ToolMessage면 AIMessage까지 포함
```
