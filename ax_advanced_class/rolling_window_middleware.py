from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import BaseMessage
from typing import List, Any

class _CharTokenizer:
    """Deterministic tokenizer for tests: 1 token per character."""

    def encode(self, text: str):
        return list(text or "")


class RollingWindowMiddleware(AgentMiddleware):
    """
    Middleware to limit the number of tokens in the conversation history.
    """
    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens
        self.tokenizer = _CharTokenizer()
        
    def _prune_messages(self, history: List[BaseMessage]) -> List[BaseMessage]:
        """
        요구사항
        **반드시 만족**:
            - `messages[0]`(System Prompt)은 삭제 금지
            - 결과의 총 토큰 수가 `max_tokens` 이하
            - **가장 최신 메시지**(마지막)는 반드시 포함
        **권장 사항**:
            - “최소 삭제” 원칙: 한도를 만족하는 선에서 **가장 적게 삭제**
            - 삭제는 **오래된 순서부터**
        """

        # if not history:
        #     return history

        # system = history[0]
        # tail = list(history[1:])  # deletion candidates (oldest -> newest)

        # def count_tokens(messages: List[BaseMessage]) -> int:
        #     return sum(len(self.tokenizer.encode(m.content)) for m in messages)

        # if count_tokens([system] + tail) <= self.max_tokens:
        #     return history

        # Prune oldest messages first, but never drop the system message or the latest message.
        # while len(tail) > 1 and count_tokens([system] + tail) > self.max_tokens:
            # tail.pop(0)

        # If even [system] + [latest] exceeds the budget, we still preserve both (per invariants).
        # return [system] + tail
        return history
    
    def before_model(self, state, runtime) -> dict[str, Any] | None:
        state.messages = self._prune_messages(state.messages)
        return state
