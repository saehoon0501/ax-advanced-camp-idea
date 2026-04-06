# Summarizer Middleware 실습 - 정답 및 해설

**구현 파일:** `ax_advanced_class/src/middleware/summarization_middleware.py`

이 문서는 Summarizer 실습의 3개 TODO에 대한 정답 코드와 상세 해설을 제공합니다. (`_find_safe_cutoff_point`는 부모 클래스에 구현되어 있습니다.)

---

## TODO 1: _should_summarize() -- 압축이 필요한가?

**개념:** Context rot 방지 -- 토큰이 임계값을 넘기 전에 압축을 시작합니다.

```python
def _should_summarize(self, messages: list[AnyMessage], total_tokens: int) -> bool:
    if not self._trigger_conditions:
        return False

    for kind, value in self._trigger_conditions:
        if kind == "messages" and len(messages) >= value:
            return True
        if kind == "tokens" and total_tokens >= value:
            return True
        if kind == "tokens" and self._should_summarize_based_on_reported_tokens(
            messages, value
        ):
            return True
        if kind == "fraction":
            max_input_tokens = self._get_profile_limits()
            if max_input_tokens is None:
                continue
            threshold = int(max_input_tokens * value)
            if threshold <= 0:
                threshold = 1
            if total_tokens >= threshold:
                return True

            if self._should_summarize_based_on_reported_tokens(messages, threshold):
                return True
    return False
```

**해설:**

- **`self._trigger_conditions`**: `__init__`에서 설정한 trigger 조건 리스트입니다. 예: `[("tokens", 60000)]` 또는 `[("messages", 50), ("fraction", 0.8)]`.

- **빈 조건 체크**: trigger 조건이 없으면 절대 압축하지 않습니다. 이는 명시적으로 trigger를 설정하지 않은 경우입니다.

- **세 가지 조건 종류**:
  - `"messages"`: 메시지 개수 기반. `len(messages) >= value`이면 압축 시작. 가장 단순하지만 메시지 길이를 고려하지 않습니다.
  - `"tokens"`: 토큰 수 기반. `total_tokens >= value`이면 압축 시작. 더 정확하지만 토큰 계산 비용이 있습니다.
  - `"fraction"`: 모델의 최대 입력 토큰 대비 비율. 예를 들어 모델이 200K 토큰을 지원하고 `("fraction", 0.8)`이면, 160K 토큰을 넘으면 압축합니다.

- **`_should_summarize_based_on_reported_tokens()`**: `"tokens"`와 `"fraction"` 조건에서 추가로 호출됩니다. 마지막 AIMessage의 `usage_metadata`에 보고된 실제 토큰 수를 확인합니다. 근사 계산보다 정확한 값을 사용할 수 있을 때 활용합니다.

- **OR 로직**: 여러 조건 중 **하나라도** True면 압축을 시작합니다. 모든 조건이 False일 때만 압축하지 않습니다.

---

## TODO 2: _create_summary() -- LLM으로 요약 생성

**개념:** Summarization -- 의미를 보존하면서 토큰을 줄이는 압축

```python
def _create_summary(self, messages_to_summarize: list[AnyMessage]) -> str:
    if not messages_to_summarize:
        return "No previous conversation history."

    trimmed_messages = self._trim_messages_for_summary(messages_to_summarize)
    if not trimmed_messages:
        return "Previous conversation was too long to summarize."

    formatted_messages = get_buffer_string(trimmed_messages)

    try:
        response = self.model.invoke(
            self.summary_prompt.format(messages=formatted_messages).rstrip(),
            config={"metadata": {"lc_source": "summarization"}},
        )
        return response.text.strip()
    except Exception as e:
        return f"Error generating summary: {e!s}"
```

**해설:**

- **빈 메시지 체크**: 요약할 메시지가 없으면 기본 메시지를 반환합니다. 이 경우는 드물지만 방어적 프로그래밍입니다.

- **`self._trim_messages_for_summary()`**: 요약 대상 메시지가 너무 길면 잘라냅니다.
  - 요약 LLM 자체에도 입력 제한이 있으므로, `trim_tokens_to_summarize` 설정값(기본 4000 토큰)에 맞춰 최근 메시지만 남깁니다.
  - 결과가 비어있으면 "Previous conversation was too long to summarize."를 반환합니다.

- **`get_buffer_string(trimmed_messages)`**: 메시지 객체를 사람이 읽기 좋은 문자열로 변환합니다.
  - `str(message)`를 직접 쓰면 `id`, `response_metadata` 같은 메타데이터까지 포함되어 토큰이 낭비됩니다.
  - `get_buffer_string`은 `"Human: 내용\nAI: 내용"` 형태로 깔끔하게 변환합니다.

- **`self.summary_prompt.format(messages=...)`**: `DEFAULT_SUMMARY_PROMPT`에서 `{messages}` 플레이스홀더에 대화 내용을 삽입합니다.
  - `.rstrip()`으로 뒤의 공백을 제거합니다.

- **`self.model.invoke(...)`**: 별도의 LLM(보통 Haiku 같은 경량 모델)으로 요약을 생성합니다.
  - `config={"metadata": {"lc_source": "summarization"}}`는 LangSmith 등에서 이 호출이 요약용임을 추적하기 위한 메타데이터입니다.

- **`response.text.strip()`**: LLM 응답에서 텍스트만 추출하고 앞뒤 공백을 제거합니다.

- **try/except**: 요약 생성 실패가 에이전트 전체를 멈추면 안 됩니다.
  - 네트워크 오류, 모델 타임아웃 등이 발생할 수 있습니다.
  - 실패 시 에러 메시지를 요약으로 사용하므로, 에이전트는 계속 동작합니다.

---

## TODO 3: before_model() -- 점진적 요약 패턴 조립

**개념:** 점진적 요약 -- 최근 메시지는 원문 유지, 오래된 메시지는 요약으로 교체

```python
def before_model(
    self, state: AgentState[Any], runtime: Runtime[ContextT]
) -> dict[str, Any] | None:
    messages = state["messages"]
    self._ensure_message_ids(messages)

    total_tokens = self.token_counter(messages)
    if not self._should_summarize(messages, total_tokens):
        return None

    cutoff_index = self._determine_cutoff_index(messages)

    if cutoff_index <= 0:
        return None

    messages_to_summarize, preserved_messages = self._partition_messages(messages, cutoff_index)

    summary = self._create_summary(messages_to_summarize)
    new_messages = self._build_new_messages(summary)

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages,
            *preserved_messages,
        ]
    }
```

**해설:**

- **`self._ensure_message_ids(messages)`**: 모든 메시지에 고유 ID를 부여합니다.
  - `RemoveMessage`가 특정 메시지를 삭제하려면 ID가 필요합니다.
  - ID가 없는 메시지가 있으면 UUID를 자동 생성합니다.

- **`self.token_counter(messages)`**: 현재 메시지의 총 토큰 수를 계산합니다.
  - `count_tokens_approximately`를 사용하여 근사값을 빠르게 계산합니다.

- **`self._should_summarize()`**: TODO 1에서 구현한 함수입니다. `False`면 `None`을 반환합니다.
  - `None` 반환 = "State를 변경하지 않음" -- 원본 메시지가 그대로 LLM에 전달됩니다.

- **`self._determine_cutoff_index(messages)`**: 보존할 메시지 수에 따라 cutoff 위치를 계산합니다.
  - 이미 구현된 헬퍼로, `keep` 설정(기본: 최근 20개 메시지)에 따라 결정합니다.
  - 내부적으로 `_find_safe_cutoff_point()`를 호출하여 AI/Tool 쌍을 보존합니다 (부모 클래스에 구현됨).
  - `cutoff_index <= 0`이면 요약할 메시지가 없으므로 `None`을 반환합니다.

- **`self._partition_messages(messages, cutoff_index)`**: 메시지를 두 그룹으로 분할합니다.
  - `messages_to_summarize`: `messages[:cutoff_index]` -- 요약 대상
  - `preserved_messages`: `messages[cutoff_index:]` -- 원문 유지 대상

- **`self._create_summary()`**: TODO 2에서 구현한 함수입니다. 요약 대상 메시지를 LLM으로 요약합니다.

- **`self._build_new_messages(summary)`**: 요약 텍스트를 HumanMessage로 래핑합니다.
  - `"Here is a summary of the conversation to date:\n\n{summary}"` 형태입니다.

- **반환값 구조**:
  ```python
  {
      "messages": [
          RemoveMessage(id=REMOVE_ALL_MESSAGES),  # 1. 기존 메시지 전부 삭제
          *new_messages,                           # 2. 요약 메시지 추가
          *preserved_messages,                     # 3. 보존된 최근 메시지 추가
      ]
  }
  ```
  - `RemoveMessage(id=REMOVE_ALL_MESSAGES)`가 맨 앞에 와야 합니다. 이것이 먼저 처리되어 기존 메시지를 전부 지우고, 그 뒤에 새 메시지(요약 + 보존)가 추가됩니다.

- **비동기 버전 (`abefore_model`)**: 부모 클래스(`SummarizationMiddlewareBase`)에 구현되어 있으며, 동기 `_create_summary`를 호출합니다.

- **`_find_safe_cutoff_point()`**: AI/Tool 메시지 쌍 보존 로직은 부모 클래스에 구현되어 있습니다. `_determine_cutoff_index()` 내부에서 자동으로 호출됩니다.

---

## 전체 흐름 요약

```
Agent가 LLM을 호출하기 직전 (before_model 훅)
  |
  v
메시지 ID 확인 (_ensure_message_ids)
  |
  v
토큰 수 계산 (token_counter)
  |
  v
압축 필요? (_should_summarize) -- No --> 그대로 통과 (return None)
  |                                       
  | Yes
  v
cutoff 지점 결정 (_determine_cutoff_index)
  |  내부에서 _find_safe_cutoff_point 호출하여 AI/Tool 쌍 보존
  |
  v
메시지 분할 (_partition_messages)
  |  [messages[:cutoff]] = 요약 대상
  |  [messages[cutoff:]] = 보존 대상
  |
  v
LLM으로 요약 생성 (_create_summary)
  |
  v
압축된 메시지 반환:
  [RemoveMessage(REMOVE_ALL)] + [요약 HumanMessage] + [보존된 메시지들]
```

**Before:** 30턴, 60,000 토큰
**After:** 요약 1개 + 최근 20개 메시지, 약 15,000 토큰 (75% 절감)
