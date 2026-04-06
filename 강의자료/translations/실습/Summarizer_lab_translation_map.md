# Summarizer Middleware Lab
## Sentence-by-Sentence Translation Map
---
### Section: Title and Problem Statement
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 1 | Summarizer Middleware 실습 | Summarizer Middleware Lab |
| 2 | Coding Agent가 "Message Streaming" 기능을 구현하는 중입니다. | The Coding Agent is in the middle of implementing the "Message Streaming" feature. |
| 3 | 30턴의 디버깅을 거치면서 컨텍스트가 60,000 토큰에 달합니다. | After 30 turns of debugging, the context has reached 60,000 tokens. |
| 4 | 턴 31에서 LLM이 이전 결정사항을 잊어버리고, 이미 해결한 버그를 다시 디버깅하기 시작합니다. | At turn 31, the LLM forgets previous decisions and starts re-debugging bugs that were already resolved. |
| 5 | 이 실습에서는 **Compaction(압축)** 개념을 직접 구현합니다. | In this lab, you will implement the **Compaction** concept directly. |
| 6 | **구현 파일:** `ax_advanced_class/src/middleware/summarization_middleware.py` | **Implementation file:** `ax_advanced_class/src/middleware/summarization_middleware.py` |

---
### Section: Concept-to-Lab Connection
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 7 | 배운 개념과 실습의 연결 | Connection Between Learned Concepts and This Lab |
| 8 | Section 1 개념 | Section 1 Concept |
| 9 | 이 실습에서 적용하는 방법 | How It Is Applied in This Lab |
| 10 | Context rot 현상 | Context rot phenomenon |
| 11 | 토큰이 쌓이면 성능이 저하됨 → threshold 초과 시 자동 압축 | Performance degrades as tokens accumulate -> automatic compaction when threshold is exceeded |
| 12 | Truncation vs Summarization | Truncation vs Summarization |
| 13 | 단순 삭제 대신 LLM으로 의미를 보존한 요약 생성 | Instead of simple deletion, generate a summary that preserves meaning using an LLM |
| 14 | 점진적 요약 패턴 | Incremental summarization pattern |
| 15 | 최근 N개는 원문 유지, 나머지만 요약으로 교체 | Keep the most recent N messages as originals, replace the rest with a summary |
| 16 | Information Density | Information Density |
| 17 | 요약 프롬프트가 핵심 정보만 추출하도록 설계 | Design the summary prompt to extract only key information |
| 18 | Prompt Caching | Prompt Caching |
| 19 | 미들웨어 순서 — Summarizer를 dynamic_prompt 앞에 배치 | Middleware ordering -- place Summarizer before dynamic_prompt |

---
### Section: What We Will Build
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 20 | 우리가 만들 것 | What We Will Build |
| 21 | LLM 호출 직전 (before_model 훅) | Just before the LLM call (before_model hook) |
| 22 | 토큰 수 체크 — threshold 이하? → 그대로 통과 | Token count check -- below threshold? -> pass through as-is |
| 23 | threshold 초과! | Threshold exceeded! |
| 24 | cutoff 지점 결정 (최근 N개 보존) | Determine cutoff point (preserve the most recent N messages) |
| 25 | 메시지를 분할: [요약 대상 \| 보존 대상] | Split messages: [to be summarized \| to be preserved] |
| 26 | 요약 대상 → 별도 LLM으로 요약 생성 | Messages to summarize -> generate summary with a separate LLM |
| 27 | [요약 HumanMessage] + [보존된 원문] → 압축된 메시지 리스트로 교체 | [Summary HumanMessage] + [preserved originals] -> replace with compressed message list |

---
### Section: Lab Structure
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 28 | 실습 구조 | Lab Structure |
| 29 | `summarization_middleware.py`의 3개 메서드가 비워져 있습니다. | Three methods in `summarization_middleware.py` are left empty. |
| 30 | 순서대로 구현하세요. | Implement them in order. |
| 31 | `SummarizationMiddlewareBase`(부모 클래스)에 모든 헬퍼가 준비되어 있으므로, 아래 3개 메서드만 override하면 동작합니다. | All helpers are prepared in `SummarizationMiddlewareBase` (parent class), so it will work by overriding only the 3 methods below. |
| 32 | 압축 필요 여부 판단 | Determine whether compaction is needed |
| 33 | LLM으로 요약 생성 | Generate a summary with an LLM |
| 34 | 전체 흐름 조립 | Assemble the overall flow |
| 35 | Context rot 방지 | Context rot prevention |
| 36 | 점진적 요약 패턴 | Incremental summarization pattern |

---
### Section: TODO 1 - _should_summarize()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 37 | TODO 1: _should_summarize() — 압축이 필요한가? | TODO 1: _should_summarize() -- Is compaction needed? |
| 38 | 배울 개념: Context rot 방지 — 토큰이 임계값을 넘으면 성능이 저하되므로, 그 전에 압축해야 합니다. | Concept to learn: Context rot prevention -- performance degrades when tokens exceed the threshold, so compaction must happen before that. |
| 39 | 이 메서드는 현재 메시지의 토큰 수를 확인하고, 설정된 trigger 조건과 비교하여 압축 여부를 결정합니다. | This method checks the current token count of messages and compares it against the configured trigger conditions to decide whether to compact. |
| 40 | 이미 제공된 것: | Already provided: |
| 41 | `self._trigger_conditions` — `[("tokens", 60000)]` 같은 (종류, 값) 튜플 리스트 | `self._trigger_conditions` -- a list of (kind, value) tuples like `[("tokens", 60000)]` |
| 42 | `total_tokens` — 이미 계산된 현재 토큰 수 | `total_tokens` -- the already-calculated current token count |
| 43 | # TODO 1: trigger 조건을 순회하며 압축 필요 여부를 판단하세요 | # TODO 1: Iterate through the trigger conditions to determine whether compaction is needed |
| 44 | # self._trigger_conditions는 [(kind, value), ...] 형태입니다. | # self._trigger_conditions is in the form [(kind, value), ...]. |
| 45 | # kind는 "messages", "tokens", "fraction" 중 하나입니다. | # kind is one of "messages", "tokens", or "fraction". |
| 46 | # 각 kind별 판단: | # Judgment for each kind: |
| 47 | # "messages" → len(messages) >= value 이면 True | # "messages" -> True if len(messages) >= value |
| 48 | # "tokens" → total_tokens >= value 이면 True | # "tokens" -> True if total_tokens >= value |
| 49 | # "fraction" → model의 max_input_tokens * value와 비교 | # "fraction" -> compare with model's max_input_tokens * value |
| 50 | # (self._get_profile_limits()로 max_input_tokens를 가져옴) | # (get max_input_tokens via self._get_profile_limits()) |
| 51 | # 어떤 조건이든 하나라도 True면 압축 필요 | # If any condition is True, compaction is needed |
| 52 | # 모든 조건이 False면 압축 불필요 | # If all conditions are False, compaction is not needed |
| 53 | 확인 포인트: | Verification points: |
| 54 | trigger 조건이 비어있으면(`not self._trigger_conditions`) 항상 `False` | If trigger conditions are empty (`not self._trigger_conditions`), always return `False` |
| 55 | `"fraction"` 조건에서 `self._get_profile_limits()`가 `None`을 반환하면 해당 조건 건너뛰기 | If `self._get_profile_limits()` returns `None` for the "fraction" condition, skip that condition |
| 56 | `"tokens"` 조건은 `total_tokens`뿐 아니라 마지막 AIMessage의 `usage_metadata`도 확인 가능 | The "tokens" condition can check not only `total_tokens` but also the last AIMessage's `usage_metadata` |

---
### Section: TODO 2 - _create_summary()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 57 | TODO 2: _create_summary() — LLM으로 요약 생성 | TODO 2: _create_summary() -- Generate a summary with an LLM |
| 58 | 배울 개념: Summarization — 의미를 보존하면서 토큰을 줄이는 압축. | Concept to learn: Summarization -- compaction that reduces tokens while preserving meaning. |
| 59 | Information Density가 높은 요약을 생성하는 것이 핵심입니다. | The key is generating a summary with high Information Density. |
| 60 | 오래된 메시지를 별도의 LLM(Haiku)에게 보내서 구조화된 요약을 받습니다. | Send old messages to a separate LLM (Haiku) to receive a structured summary. |
| 61 | `self.model` — 요약에 사용할 LLM | `self.model` -- the LLM to use for summarization |
| 62 | `self.summary_prompt` — `{messages}` 플레이스홀더가 있는 요약 프롬프트 (DEFAULT_SUMMARY_PROMPT) | `self.summary_prompt` -- a summary prompt with a `{messages}` placeholder (DEFAULT_SUMMARY_PROMPT) |
| 63 | `self._trim_messages_for_summary()` — 요약 대상 메시지가 너무 길면 잘라주는 헬퍼 | `self._trim_messages_for_summary()` -- a helper that trims messages if they are too long for summarization |
| 64 | `get_buffer_string()` — 메시지 리스트를 문자열로 변환 | `get_buffer_string()` -- converts a message list to a string |
| 65 | # TODO 2: 메시지 목록을 LLM으로 요약하세요 | # TODO 2: Summarize the message list using an LLM |
| 66 | # Step 1: 메시지가 비어있으면 "No previous conversation history." 반환 | # Step 1: If messages are empty, return "No previous conversation history." |
| 67 | # Step 2: self._trim_messages_for_summary(messages_to_summarize) | # Step 2: self._trim_messages_for_summary(messages_to_summarize) |
| 68 | # 요약 LLM에 보낼 메시지가 너무 길면 잘라냄 | # Trim messages if they are too long to send to the summary LLM |
| 69 | # 결과가 비어있으면 "Previous conversation was too long to summarize." 반환 | # If the result is empty, return "Previous conversation was too long to summarize." |
| 70 | # Step 3: get_buffer_string(trimmed_messages)로 문자열 변환 | # Step 3: Convert to string with get_buffer_string(trimmed_messages) |
| 71 | # 메시지 객체를 그대로 str()하면 metadata까지 포함되어 토큰이 낭비됨 | # Using str() directly on message objects includes metadata, wasting tokens |
| 72 | # Step 4: self.summary_prompt.format(messages=formatted_messages) | # Step 4: self.summary_prompt.format(messages=formatted_messages) |
| 73 | # DEFAULT_SUMMARY_PROMPT에 {messages} 자리에 대화 내용을 삽입 | # Insert conversation content into the {messages} placeholder in DEFAULT_SUMMARY_PROMPT |
| 74 | # Step 5: self.model.invoke(formatted_prompt)로 요약 생성 | # Step 5: Generate summary with self.model.invoke(formatted_prompt) |
| 75 | # response.text.strip()으로 결과 추출 | # Extract the result with response.text.strip() |
| 76 | # Step 6: 에러 발생 시 "Error generating summary: {error}" 반환 | # Step 6: If an error occurs, return "Error generating summary: {error}" |
| 77 | # try/except로 감싸기 — 요약 실패가 에이전트 전체를 멈추면 안 됩니다 | # Wrap with try/except -- summary failure should not halt the entire agent |
| 78 | `get_buffer_string()`을 사용했는지 — 메시지에 `str()`을 직접 쓰면 metadata가 포함되어 토큰 낭비 | Check if `get_buffer_string()` was used -- using `str()` directly on messages includes metadata, wasting tokens |
| 79 | try/except로 감쌌는지 — 요약 실패가 에이전트를 멈추면 안 됩니다 | Check if wrapped with try/except -- summary failure should not halt the agent |
| 80 | `response.text.strip()`으로 결과를 추출했는지 | Check if the result was extracted with `response.text.strip()` |

---
### Section: TODO 3 - before_model()
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 81 | TODO 3: before_model() — 점진적 요약 패턴 조립 | TODO 3: before_model() -- Assemble the incremental summarization pattern |
| 82 | 배울 개념: 점진적 요약 — 최근 메시지는 원문 유지, 오래된 메시지는 요약으로 교체 | Concept to learn: Incremental summarization -- keep recent messages as originals, replace old messages with a summary |
| 83 | `AgentMiddleware`의 `before_model` 훅은 LLM 호출 직전에 실행됩니다. | The `before_model` hook of `AgentMiddleware` runs just before the LLM call. |
| 84 | 여기서 메시지를 확인하고, 필요하면 압축된 버전으로 교체합니다. | Here, it checks the messages and, if necessary, replaces them with a compacted version. |
| 85 | `self._should_summarize()` — TODO 1에서 구현 | `self._should_summarize()` -- implemented in TODO 1 |
| 86 | `self._determine_cutoff_index()` — 이미 구현됨 (보존할 메시지 수에 따라 cutoff 위치 계산) | `self._determine_cutoff_index()` -- already implemented (calculates the cutoff position based on the number of messages to preserve) |
| 87 | `self._partition_messages()` — 이미 구현됨 (cutoff 기준으로 메시지를 둘로 분할) | `self._partition_messages()` -- already implemented (splits messages into two groups based on the cutoff) |
| 88 | `self._create_summary()` — TODO 2에서 구현 | `self._create_summary()` -- implemented in TODO 2 |
| 89 | `self._build_new_messages()` — 이미 구현됨 (요약을 HumanMessage로 래핑) | `self._build_new_messages()` -- already implemented (wraps the summary as a HumanMessage) |
| 90 | `self._ensure_message_ids()` — 이미 구현됨 (RemoveMessage에 필요한 ID 부여) | `self._ensure_message_ids()` -- already implemented (assigns IDs required by RemoveMessage) |
| 91 | `REMOVE_ALL_MESSAGES` — 기존 메시지 전부 삭제하는 상수 (langgraph) | `REMOVE_ALL_MESSAGES` -- a constant that deletes all existing messages (langgraph) |
| 92 | `RemoveMessage` — 특정 메시지 삭제를 지시하는 메시지 타입 | `RemoveMessage` -- a message type that instructs deletion of specific messages |
| 93 | # TODO 3: 점진적 요약 패턴을 조립하세요 | # TODO 3: Assemble the incremental summarization pattern |
| 94 | # Step 1: state["messages"]에서 메시지 추출 | # Step 1: Extract messages from state["messages"] |
| 95 | # self._ensure_message_ids(messages) 호출 — ID가 없으면 RemoveMessage가 작동 안 함 | # Call self._ensure_message_ids(messages) -- RemoveMessage won't work without IDs |
| 96 | # Step 2: 토큰 수 계산 | # Step 2: Calculate token count |
| 97 | # Step 3: _should_summarize() 호출 | # Step 3: Call _should_summarize() |
| 98 | # False면 None 반환 (변경 없음, 원본 메시지 그대로 LLM에 전달) | # If False, return None (no changes, original messages passed to LLM as-is) |
| 99 | # Step 4: cutoff 지점 결정 | # Step 4: Determine the cutoff point |
| 100 | # cutoff_index <= 0이면 None 반환 (요약할 메시지가 없음) | # If cutoff_index <= 0, return None (no messages to summarize) |
| 101 | # Step 5: 메시지 분할 | # Step 5: Split messages |
| 102 | # Step 6: 요약 생성 | # Step 6: Generate summary |
| 103 | # Step 7: 새 메시지 구성 | # Step 7: Compose new messages |
| 104 | # Step 8: 압축된 상태 반환 | # Step 8: Return the compacted state |
| 105 | # RemoveMessage(id=REMOVE_ALL_MESSAGES)가 기존 메시지를 전부 지우고, 그 뒤에 [요약 + 보존된 최근 메시지]를 새로 넣는 구조입니다. | # RemoveMessage(id=REMOVE_ALL_MESSAGES) deletes all existing messages, then inserts [summary + preserved recent messages] after it. |
| 106 | `None` 반환 = 변경 없음 (압축 불필요할 때) | `None` return = no changes (when compaction is not needed) |
| 107 | `{"messages": [...]}` 반환 = 메시지 교체 (압축 실행) | `{"messages": [...]}` return = message replacement (compaction executed) |
| 108 | `RemoveMessage(id=REMOVE_ALL_MESSAGES)`가 **맨 앞**에 있어야 기존 메시지가 먼저 삭제됨 | `RemoveMessage(id=REMOVE_ALL_MESSAGES)` must be **at the front** so existing messages are deleted first |
| 109 | `_find_safe_cutoff_point()`(AI/Tool 메시지 쌍 보존)은 부모 클래스에 이미 구현되어 있습니다. | `_find_safe_cutoff_point()` (preserving AI/Tool message pairs) is already implemented in the parent class. |

---
### Section: Verification
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 110 | 검증 방법 | Verification Method |
| 111 | 모든 TODO를 구현한 후: | After implementing all TODOs: |

---
### Section: Common Failures and Solutions
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 112 | 흔한 실패와 대처 | Common Failures and Solutions |
| 113 | 요약 후 agent가 이전 작업을 잊음 | After summarization, the agent forgets previous work |
| 114 | 요약이 핵심 결정사항/파일명을 누락 | The summary omits key decisions/file names |
| 115 | `DEFAULT_SUMMARY_PROMPT`에 "반드시 보존: 파일 경로, 결정 사항, 에러 해결 방법" 추가 | Add "Must preserve: file paths, decisions, error resolutions" to `DEFAULT_SUMMARY_PROMPT` |
| 116 | `_find_safe_cutoff_point`가 0 반환 | `_find_safe_cutoff_point` returns 0 |
| 117 | AI/Tool 메시지 쌍이 전체를 차지 | AI/Tool message pairs occupy the entire space |
| 118 | `keep` 값을 줄이거나 `trigger` threshold를 높여 더 일찍 압축 시작 | Reduce the `keep` value or raise the `trigger` threshold to start compaction earlier |
| 119 | 요약 LLM 호출 실패 (타임아웃) | Summary LLM call fails (timeout) |
| 120 | Haiku 모델 응답 지연 | Haiku model response delay |
| 121 | `_create_summary`에서 `try/except`로 감싸고 실패 시 truncation fallback | Wrap `_create_summary` with `try/except` and fall back to truncation on failure |
| 122 | 압축 후에도 토큰이 줄지 않음 | Token count does not decrease even after compaction |
| 123 | `keep` 메시지 수가 너무 많음 | The number of `keep` messages is too high |
| 124 | `keep=("messages", 5)` 등으로 줄임 — 최근 대화만 원문 유지 | Reduce with `keep=("messages", 5)` etc. -- keep only recent conversations as originals |
| 125 | `RemoveMessage`가 적용 안 됨 | `RemoveMessage` is not applied |
| 126 | messages reducer가 `operator.add`가 아님 | The messages reducer is not `operator.add` |
| 127 | `AgentState`의 messages 필드에 `Annotated[list, operator.add]` 확인 | Verify `Annotated[list, operator.add]` on the messages field of `AgentState` |

---
### Section: Concept Connection Map
| # | Korean (Original) | English (Natural Translation) |
|---|---|---|
| 128 | 배운 개념 → 이 실습에서 구현한 것 | Learned concepts -> What was implemented in this lab |
| 129 | Context rot 현상 | Context rot phenomenon |
| 130 | "토큰이 쌓이면 성능 저하" | "Performance degrades as tokens accumulate" |
| 131 | trigger 조건 체크 | Trigger condition check |
| 132 | Truncation vs Summarization | Truncation vs Summarization |
| 133 | "삭제 대신 의미 보존 요약" | "Summary that preserves meaning instead of deletion" |
| 134 | LLM + 구조화된 프롬프트 | LLM + structured prompt |
| 135 | 점진적 요약 패턴 | Incremental summarization pattern |
| 136 | "최근은 원문, 과거는 요약" | "Recent messages as originals, past messages as summaries" |
| 137 | 분할 → 요약 → RemoveMessage로 교체 | Split -> summarize -> replace with RemoveMessage |
| 138 | Information Density | Information Density |
| 139 | "토큰당 정보 밀도를 높여라" | "Maximize information density per token" |
| 140 | AI/Tool 쌍 무결성 | AI/Tool pair integrity |
| 141 | "tool_call과 결과는 함께" | "tool_call and its result must stay together" |
| 142 | cutoff이 ToolMessage면 AIMessage까지 포함 | If the cutoff is at a ToolMessage, include back to the AIMessage |
