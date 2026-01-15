from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ToolMessage,
)
from typing import Any, List


class _CharTokenizer:
    """Deterministic tokenizer for tests: 1 token per character."""

    def encode(self, text: str):
        return list(text or "")


class RollingWindowMiddleware(AgentMiddleware):
    """
    LangChain 1.0 Middleware for managing conversation context with rolling window.

    Uses wrap_tool_call to intercept tool executions and trim tool outputs,
    and before_model to prune older messages while preserving:
    - System prompt (index 0)
    - Latest messages (recent N)
    - Tool call / Tool output pairs integrity
    """

    def __init__(
        self,
        max_tokens: int,
        max_tool_output_chars: int = 1000,
        recent_n: int = 5,
    ):
        self.max_tokens = max_tokens
        self.max_tool_output_chars = max_tool_output_chars
        self.recent_n = recent_n
        self.tokenizer = _CharTokenizer()

    def _count_tokens(self, messages: List[BaseMessage]) -> int:
        """Count total tokens across all messages."""
        total = 0
        for m in messages:
            total += len(self.tokenizer.encode(m.content))
            # Count tool_calls content if present
            if isinstance(m, AIMessage) and m.tool_calls:
                for tc in m.tool_calls:
                    total += len(self.tokenizer.encode(str(tc.get("args", {}))))
        return total

    def _truncate_tool_output(self, content: str) -> str:
        """Truncate tool output content if it exceeds max_tool_output_chars."""
        if len(content) <= self.max_tool_output_chars:
            return content

        # Keep first and last portions, truncate middle
        keep_chars = self.max_tool_output_chars // 2
        truncated_count = len(content) - self.max_tool_output_chars
        return (
            content[:keep_chars]
            + f"\n... (truncated {truncated_count} chars) ...\n"
            + content[-keep_chars:]
        )

    def _find_tool_call_pairs(
        self, messages: List[BaseMessage]
    ) -> List[tuple[int, int]]:
        """
        Find pairs of (AIMessage with tool_calls, corresponding ToolMessage).
        Returns list of (ai_index, tool_index) tuples.
        """
        pairs = []
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_call_id = tc.get("id")
                    # Find corresponding ToolMessage
                    for j in range(i + 1, len(messages)):
                        if (
                            isinstance(messages[j], ToolMessage)
                            and messages[j].tool_call_id == tool_call_id
                        ):
                            pairs.append((i, j))
                            break
        return pairs

    def _prune_messages(self, history: List[BaseMessage]) -> List[BaseMessage]:
        """
        Prune conversation history to fit within max_tokens.

        Priority (highest to lowest):
        1. System Prompt (index 0) - never delete
        2. Latest N messages - preserve current context
        3. First user message (feature spec) - try to preserve
        4. Tool outputs - truncate first, then remove
        5. Old conversation - remove as needed
        """
        if not history:
            return history

        # Step 1: Truncate all tool outputs (except most recent)
        history = self._truncate_old_tool_outputs(history)

        # Check if within budget
        if self._count_tokens(history) <= self.max_tokens:
            return history

        # Step 2: Separate messages by priority
        system = history[0]
        others = list(history[1:])

        # Protect recent N messages
        if len(others) > self.recent_n:
            old_history = others[: -self.recent_n]
            recent = others[-self.recent_n :]
        else:
            old_history = []
            recent = others

        # Step 3: Remove old messages (oldest first) while maintaining tool call pairs
        tool_pairs = self._find_tool_call_pairs([system] + old_history)
        paired_indices = set()
        for ai_idx, tool_idx in tool_pairs:
            # Adjust indices since we separated system message
            paired_indices.add(ai_idx - 1)  # -1 because old_history starts at index 1
            paired_indices.add(tool_idx - 1)

        # Remove unpaired messages first, then paired messages together
        while old_history and self._count_tokens([system] + old_history + recent) > self.max_tokens:
            # Try to find an unpaired message to remove first
            removed = False
            for i in range(len(old_history)):
                if i not in paired_indices:
                    old_history.pop(i)
                    # Update paired_indices after removal
                    paired_indices = {idx - 1 if idx > i else idx for idx in paired_indices}
                    paired_indices.discard(-1)
                    removed = True
                    break

            if not removed:
                # Remove oldest pair together
                if old_history:
                    old_history.pop(0)
                    paired_indices = {idx - 1 for idx in paired_indices}
                    paired_indices.discard(-1)
                    if old_history:
                        old_history.pop(0)
                        paired_indices = {idx - 1 for idx in paired_indices}
                        paired_indices.discard(-1)

        return [system] + old_history + recent

    def _truncate_old_tool_outputs(
        self, history: List[BaseMessage]
    ) -> List[BaseMessage]:
        """Truncate tool outputs except the most recent one."""
        result = []
        tool_messages = [
            (i, m) for i, m in enumerate(history) if isinstance(m, ToolMessage)
        ]

        # Find the most recent tool message index
        most_recent_tool_idx = tool_messages[-1][0] if tool_messages else -1

        for i, msg in enumerate(history):
            if isinstance(msg, ToolMessage) and i != most_recent_tool_idx:
                # Truncate old tool outputs
                truncated_content = self._truncate_tool_output(msg.content)
                result.append(
                    ToolMessage(
                        content=truncated_content,
                        tool_call_id=msg.tool_call_id,
                    )
                )
            else:
                result.append(msg)

        return result

    def wrap_tool_call(self, request, handler):
        """
        LangChain 1.0 wrap_tool_call hook.

        Intercepts tool calls to:
        1. Execute the tool normally
        2. Potentially truncate the result if it's too long
        """
        # Execute the tool call
        result = handler(request)

        # If result is a ToolMessage with long content, truncate it
        if isinstance(result, ToolMessage):
            if len(result.content) > self.max_tool_output_chars:
                return ToolMessage(
                    content=self._truncate_tool_output(result.content),
                    tool_call_id=result.tool_call_id,
                )

        return result

    def before_model(self, state, runtime) -> dict[str, Any] | None:
        """
        LangChain 1.0 before_model hook.

        Prunes conversation history before each model call to ensure
        we stay within the token budget.
        """
        if isinstance(state, dict):
            if "messages" in state:
                state["messages"] = self._prune_messages(state["messages"])
        else:
            state.messages = self._prune_messages(state.messages)
        return state
