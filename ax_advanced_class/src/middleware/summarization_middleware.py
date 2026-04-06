"""Summarization middleware — 학생 구현 파일.

대화가 길어지면 토큰이 초과됩니다. 이 미들웨어는 ``before_model``에서 이를
감지하고, 오래된 메시지를 LLM 요약으로 교체하여 컨텍스트 윈도우를 관리합니다.

구현해야 할 메서드 3개:
  1. ``_should_summarize``  — 압축이 필요한지 판단
  2. ``_create_summary``    — LLM으로 요약 생성
  3. ``before_model``       — 점진적 요약 패턴 조립
"""

from typing import Any

from langchain_core.messages import AnyMessage, RemoveMessage
from langchain_core.messages.utils import get_buffer_string
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from langchain.agents.middleware.types import AgentState, ContextT

from ._internals.summarization_helpers import (
    SummarizationMiddlewareBase,
    ContextFraction,
    ContextMessages,
    ContextSize,
    ContextTokens,
    DEFAULT_SUMMARY_PROMPT,
    TokenCounter,
    _get_approximate_token_counter,
)

# Re-export helpers so external imports keep working
__all__ = [
    "SummarizationMiddleware",
    "ContextFraction",
    "ContextMessages",
    "ContextSize",
    "ContextTokens",
    "DEFAULT_SUMMARY_PROMPT",
    "TokenCounter",
    "_get_approximate_token_counter",
]


class SummarizationMiddleware(SummarizationMiddlewareBase):
    """Summarizes conversation history when token limits are approached.

    ``SummarizationMiddlewareBase`` 에 모든 헬퍼가 준비되어 있습니다.
    아래 세 메서드만 완성하면 동작합니다.
    """

    # ------------------------------------------------------------------
    # TODO 1: 압축이 필요한지 판단하세요
    # ------------------------------------------------------------------
    def _should_summarize(self, messages: list[AnyMessage], total_tokens: int) -> bool:
        """대화 상태를 보고 요약을 실행할지 결정합니다.

        Hints:
            - self._trigger_conditions 는 [(kind, value), ...] 형태입니다.
            - kind 는 "messages", "tokens", "fraction" 중 하나입니다.

            각 kind별 판단:
              "messages" -> len(messages) >= value 이면 True
              "tokens"   -> total_tokens >= value 이면 True
              "fraction" -> self._get_profile_limits()로 최대 토큰을 구한 뒤
                            max_input_tokens * value 와 total_tokens 를 비교

            하나라도 True면 압축 필요. 모든 조건이 False면 압축 불필요.
            self._trigger_conditions 가 비어있으면 항상 False 를 반환합니다.
        """
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

    # ------------------------------------------------------------------
    # TODO 2: 메시지 목록을 LLM으로 요약하세요
    # ------------------------------------------------------------------
    def _create_summary(self, messages_to_summarize: list[AnyMessage]) -> str:
        """메시지를 LLM에 보내 요약 텍스트를 생성합니다."""
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

    # ------------------------------------------------------------------
    # TODO 3: 점진적 요약 패턴을 조립하세요
    # ------------------------------------------------------------------
    def before_model(
        self, state: AgentState[Any], runtime: Runtime[ContextT]
    ) -> dict[str, Any] | None:
        """모델 호출 전에 실행되어, 필요하면 오래된 메시지를 요약으로 교체합니다."""
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
