import unittest

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ax_advanced_class.rolling_window_middleware import RollingWindowMiddleware


class _CharTokenizer:
    """Deterministic tokenizer for tests: 1 token per character."""

    def encode(self, text: str):
        return list(text or "")


class _State:
    def __init__(self, messages):
        self.messages = messages


class TestRollingWindowMiddleware(unittest.TestCase):
    def _mw(self, max_tokens: int) -> RollingWindowMiddleware:
        mw = RollingWindowMiddleware(max_tokens=max_tokens)
        mw.tokenizer = _CharTokenizer()
        return mw
    
    def _count_tokens(self, mw: RollingWindowMiddleware, messages) -> int:
        return sum(len(mw.tokenizer.encode(m.content)) for m in messages)

    def test_no_prune_when_within_budget(self):
        system = SystemMessage(
            content=(
                "You are a helpful assistant. Follow the user's instructions. "
                "If you don't know an answer, say you don't know."
            )
        )
        user = HumanMessage(content="Hey—can you summarize the meeting notes I paste next?")
        assistant = AIMessage(content="Sure. Paste them here and tell me the audience and desired length.")
        history = [system, user, assistant]

        mw = self._mw(max_tokens=self._count_tokens(self._mw(10_000), history) + 10)

        pruned = mw._prune_messages(history)

        self.assertEqual([m.content for m in pruned], [system.content, user.content, assistant.content])
        self.assertIsInstance(pruned[0], SystemMessage)
        self.assertEqual(pruned[-1].content, assistant.content)

    def test_prunes_oldest_non_system_first_minimally(self):
        system = SystemMessage(
            content=(
                "System: You are 'Dexter', an assistant for internal tools. "
                "Be concise. Never reveal secrets. Ask clarifying questions when needed."
            )
        )
        m1 = HumanMessage(
            content=(
                "Context: I'm writing a weekly status update. The highlights were shipping the MVP, "
                "fixing a login bug, and aligning with design on the dashboard."
            )
        )
        m2 = AIMessage(
            content=(
                "Got it. Do you want a version for leadership (high-level) or for the team (more detail)?"
            )
        )
        m3 = HumanMessage(content="Leadership version. Keep it to 3 bullet points.")  # latest
        history = [system, m1, m2, m3]

        mw = self._mw(max_tokens=self._count_tokens(self._mw(10_000), [system, m2, m3]))

        pruned = mw._prune_messages(history)

        self.assertEqual([m.content for m in pruned], [system.content, m2.content, m3.content])
        self.assertIs(pruned[0], system)  # system preserved
        self.assertIs(pruned[-1], m3)     # latest preserved

    def test_can_prune_down_to_system_plus_latest(self):
        system = SystemMessage(
            content=(
                "System: You are a customer support assistant. "
                "Be polite, avoid making promises, and request missing order details."
            )
        )
        old1 = HumanMessage(content="My package says delivered but I can't find it anywhere.")
        old2 = AIMessage(content="Sorry about that—can you confirm the delivery address and the tracking number?")
        latest = HumanMessage(content="Tracking: 1Z999AA10123456784. Address ends with Apt 12B.")
        history = [system, old1, old2, latest]

        mw = self._mw(max_tokens=self._count_tokens(self._mw(10_000), [system, latest]))

        pruned = mw._prune_messages(history)

        self.assertEqual([m.content for m in pruned], [system.content, latest.content])
        self.assertIs(pruned[0], system)
        self.assertIs(pruned[-1], latest)

    def test_before_model_updates_state_messages(self):
        system = SystemMessage(
            content=(
                "System: You are an assistant that helps draft emails. "
                "Match the user's tone. Keep private data out."
            )
        )
        latest = HumanMessage(content="Draft a friendly follow-up asking if they saw my last message.")
        state = _State(
            [
                system,
                HumanMessage(content="Earlier: I'm applying for the role and want to follow up next week."),
                AIMessage(content="Sure—who is the recipient and what's your preferred tone?"),
                latest,
            ]
        )
        mw = self._mw(max_tokens=self._count_tokens(self._mw(10_000), [system, latest]))

        mw.before_model(state, runtime=None)

        self.assertEqual([m.content for m in state.messages], [system.content, latest.content])


if __name__ == "__main__":
    unittest.main()