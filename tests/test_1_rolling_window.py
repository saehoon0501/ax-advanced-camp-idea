import unittest
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from ax_advanced_class.src.middleware.rolling_window_middleware import RollingWindowMiddleware
from ax_advanced_class.data.mock_messages import (
    MOCK_CONVERSATION_HISTORY,
    SYSTEM_PROMPT,
    get_mock_token_count,
)


class _State:
    """Mock state object for testing before_model hook."""

    def __init__(self, messages):
        self.messages = messages


class TestRollingWindowMiddleware(unittest.TestCase):
    """Tests for RollingWindowMiddleware with LangChain 1.0 patterns."""

    def _create_middleware(
        self, max_tokens: int, max_tool_output_chars: int = 1000, recent_n: int = 5
    ) -> RollingWindowMiddleware:
        return RollingWindowMiddleware(
            max_tokens=max_tokens,
            max_tool_output_chars=max_tool_output_chars,
            recent_n=recent_n,
        )

    def _count_tokens(self, mw: RollingWindowMiddleware, messages) -> int:
        return mw._count_tokens(messages)

    # ==========================================================================
    # Basic Pruning Tests
    # ==========================================================================

    def test_no_prune_when_within_budget(self):
        """Messages should not be pruned when total tokens are within budget."""
        system = SystemMessage(content="You are a helpful assistant.")
        user = HumanMessage(content="Hello, how are you?")
        assistant = AIMessage(content="I'm doing well, thank you!")
        history = [system, user, assistant]

        mw = self._create_middleware(max_tokens=1000)
        pruned = mw._prune_messages(history)

        self.assertEqual(len(pruned), 3)
        self.assertEqual(pruned[0].content, system.content)
        self.assertEqual(pruned[-1].content, assistant.content)

    def test_system_prompt_always_preserved(self):
        """System prompt (index 0) must never be deleted."""
        system = SystemMessage(content="System prompt that must be preserved.")
        messages = [system] + [
            HumanMessage(content=f"Message {i}") for i in range(10)
        ]

        # Set very low token limit
        mw = self._create_middleware(max_tokens=100, recent_n=2)
        pruned = mw._prune_messages(messages)

        self.assertIsInstance(pruned[0], SystemMessage)
        self.assertEqual(pruned[0].content, system.content)

    def test_latest_message_always_preserved(self):
        """The latest message must always be preserved."""
        system = SystemMessage(content="System")
        latest = HumanMessage(content="This is the latest and must be kept!")
        messages = [system] + [HumanMessage(content="old" * 100) for _ in range(5)] + [latest]

        mw = self._create_middleware(max_tokens=100, recent_n=1)
        pruned = mw._prune_messages(messages)

        self.assertEqual(pruned[-1].content, latest.content)

    def test_prunes_oldest_messages_first(self):
        """Older messages should be pruned before newer ones."""
        system = SystemMessage(content="System")
        m1 = HumanMessage(content="Oldest - should be removed first")
        m2 = AIMessage(content="Second oldest")
        m3 = HumanMessage(content="Third")
        m4 = AIMessage(content="Recent - should be kept")
        m5 = HumanMessage(content="Latest - must be kept")
        history = [system, m1, m2, m3, m4, m5]

        # Budget fits system + last 2 messages only
        mw = self._create_middleware(max_tokens=80, recent_n=2)
        pruned = mw._prune_messages(history)

        self.assertEqual(pruned[0].content, system.content)
        self.assertIn(m5, pruned)
        self.assertNotIn(m1, pruned)

    # ==========================================================================
    # Tool Output Truncation Tests
    # ==========================================================================

    def test_truncate_long_tool_output(self):
        """Long tool outputs should be truncated with middle portion removed."""
        mw = self._create_middleware(max_tokens=10000, max_tool_output_chars=100)

        long_content = "x" * 500
        truncated = mw._truncate_tool_output(long_content)

        self.assertLess(len(truncated), len(long_content))
        self.assertIn("truncated", truncated)
        self.assertIn("400 chars", truncated)  # 500 - 100 = 400 truncated

    def test_short_tool_output_not_truncated(self):
        """Tool outputs within limit should not be modified."""
        mw = self._create_middleware(max_tokens=10000, max_tool_output_chars=1000)

        short_content = "This is a short output."
        result = mw._truncate_tool_output(short_content)

        self.assertEqual(result, short_content)

    def test_old_tool_outputs_truncated_recent_preserved(self):
        """Old tool outputs should be truncated but the most recent one preserved."""
        system = SystemMessage(content="System")
        ai1 = AIMessage(
            content="Reading file",
            tool_calls=[{"id": "call_1", "name": "read", "args": {}}],
        )
        tool1 = ToolMessage(content="x" * 2000, tool_call_id="call_1")  # Old, should truncate
        ai2 = AIMessage(
            content="Running tests",
            tool_calls=[{"id": "call_2", "name": "test", "args": {}}],
        )
        tool2 = ToolMessage(content="y" * 2000, tool_call_id="call_2")  # Recent, preserve

        history = [system, ai1, tool1, ai2, tool2]
        mw = self._create_middleware(max_tokens=50000, max_tool_output_chars=500)

        pruned = mw._truncate_old_tool_outputs(history)

        # Old tool output should be truncated
        old_tool = next(m for m in pruned if isinstance(m, ToolMessage) and m.tool_call_id == "call_1")
        self.assertIn("truncated", old_tool.content)

        # Recent tool output should be preserved
        recent_tool = next(m for m in pruned if isinstance(m, ToolMessage) and m.tool_call_id == "call_2")
        self.assertEqual(recent_tool.content, "y" * 2000)

    # ==========================================================================
    # Tool Call Pair Tests
    # ==========================================================================

    def test_tool_call_pairs_identified(self):
        """AIMessage with tool_calls and corresponding ToolMessage should be paired."""
        system = SystemMessage(content="System")
        ai = AIMessage(
            content="Let me check",
            tool_calls=[{"id": "call_abc", "name": "check", "args": {}}],
        )
        tool = ToolMessage(content="Result", tool_call_id="call_abc")
        user = HumanMessage(content="Thanks")

        history = [system, ai, tool, user]
        mw = self._create_middleware(max_tokens=10000)

        pairs = mw._find_tool_call_pairs(history)

        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0], (1, 2))  # ai at index 1, tool at index 2

    def test_multiple_tool_call_pairs(self):
        """Multiple tool call pairs should be identified correctly."""
        system = SystemMessage(content="System")
        ai1 = AIMessage(
            content="First call",
            tool_calls=[{"id": "call_1", "name": "tool1", "args": {}}],
        )
        tool1 = ToolMessage(content="Result 1", tool_call_id="call_1")
        ai2 = AIMessage(
            content="Second call",
            tool_calls=[{"id": "call_2", "name": "tool2", "args": {}}],
        )
        tool2 = ToolMessage(content="Result 2", tool_call_id="call_2")

        history = [system, ai1, tool1, ai2, tool2]
        mw = self._create_middleware(max_tokens=10000)

        pairs = mw._find_tool_call_pairs(history)

        self.assertEqual(len(pairs), 2)

    # ==========================================================================
    # wrap_tool_call Hook Tests
    # ==========================================================================

    def test_wrap_tool_call_truncates_long_output(self):
        """wrap_tool_call should truncate long tool outputs."""
        mw = self._create_middleware(max_tokens=10000, max_tool_output_chars=100)

        mock_request = MagicMock()
        mock_handler = MagicMock(
            return_value=ToolMessage(content="z" * 500, tool_call_id="test_id")
        )

        result = mw.wrap_tool_call(mock_request, mock_handler)

        mock_handler.assert_called_once_with(mock_request)
        self.assertIsInstance(result, ToolMessage)
        self.assertIn("truncated", result.content)
        self.assertEqual(result.tool_call_id, "test_id")

    def test_wrap_tool_call_preserves_short_output(self):
        """wrap_tool_call should not modify short tool outputs."""
        mw = self._create_middleware(max_tokens=10000, max_tool_output_chars=1000)

        short_content = "Short result"
        mock_request = MagicMock()
        mock_handler = MagicMock(
            return_value=ToolMessage(content=short_content, tool_call_id="test_id")
        )

        result = mw.wrap_tool_call(mock_request, mock_handler)

        self.assertEqual(result.content, short_content)

    # ==========================================================================
    # before_model Hook Tests
    # ==========================================================================

    def test_before_model_with_dict_state(self):
        """before_model should handle dict state correctly."""
        system = SystemMessage(content="System")
        latest = HumanMessage(content="Latest")
        state = {
            "messages": [system] + [HumanMessage(content="old" * 50) for _ in range(10)] + [latest]
        }

        mw = self._create_middleware(max_tokens=200, recent_n=1)
        result = mw.before_model(state, runtime=None)

        self.assertEqual(result["messages"][0].content, system.content)
        self.assertEqual(result["messages"][-1].content, latest.content)
        self.assertLessEqual(mw._count_tokens(result["messages"]), 200)

    def test_before_model_with_object_state(self):
        """before_model should handle object state correctly."""
        system = SystemMessage(content="System")
        latest = HumanMessage(content="Latest")
        state = _State(
            [system] + [HumanMessage(content="old" * 50) for _ in range(10)] + [latest]
        )

        mw = self._create_middleware(max_tokens=200, recent_n=1)
        mw.before_model(state, runtime=None)

        self.assertEqual(state.messages[0].content, system.content)
        self.assertEqual(state.messages[-1].content, latest.content)

    # ==========================================================================
    # Integration Tests with Mock Data
    # ==========================================================================

    def test_prune_mock_conversation_history(self):
        """Test pruning with realistic mock conversation data."""
        history = list(MOCK_CONVERSATION_HISTORY)
        original_token_count = get_mock_token_count(history)

        # Set budget to about half the original
        target_tokens = original_token_count // 2
        mw = self._create_middleware(
            max_tokens=target_tokens,
            max_tool_output_chars=500,
            recent_n=5,
        )

        pruned = mw._prune_messages(history)

        # Verify system prompt preserved
        self.assertEqual(pruned[0].content, SYSTEM_PROMPT.content)

        # Verify we're within budget (or close, allowing for truncation overhead)
        pruned_tokens = mw._count_tokens(pruned)
        self.assertLessEqual(pruned_tokens, target_tokens + 100)

        # Verify latest messages are preserved
        self.assertTrue(len(pruned) >= 2)  # At least system + latest

    def test_10k_to_4k_token_reduction(self):
        """Test reducing 10k tokens to 4k as per scenario requirements."""
        # Create a large conversation
        system = SystemMessage(content="System prompt " * 50)  # ~700 chars
        messages = [system]

        # Add messages to reach ~10k tokens
        for i in range(20):
            messages.append(
                AIMessage(
                    content=f"AI response {i} " * 30,
                    tool_calls=[{"id": f"call_{i}", "name": "tool", "args": {"x": i}}],
                )
            )
            messages.append(
                ToolMessage(content="Tool output " * 100, tool_call_id=f"call_{i}")
            )

        messages.append(HumanMessage(content="Final user message"))

        mw = self._create_middleware(
            max_tokens=4000,
            max_tool_output_chars=200,
            recent_n=5,
        )

        pruned = mw._prune_messages(messages)
        final_tokens = mw._count_tokens(pruned)

        # Verify reduction
        self.assertLessEqual(final_tokens, 4000)

        # Verify system prompt preserved
        self.assertIsInstance(pruned[0], SystemMessage)

        # Verify latest message preserved
        self.assertEqual(pruned[-1].content, "Final user message")


if __name__ == "__main__":
    unittest.main()
