import unittest

from ax_advanced_class.tool_selector import email_tool, math_tool, select_relevant_tools


class TestToolSelector(unittest.TestCase):
    def test_math_query_returns_only_math(self):
        tools = [email_tool, math_tool]
        selected = select_relevant_tools("What is 25 * 50?", tools)
        self.assertEqual([t.name for t in selected], ["math_tool"])

    def test_email_query_returns_only_email(self):
        tools = [math_tool, email_tool]
        selected = select_relevant_tools("Please send an email to the team", tools)
        self.assertEqual([t.name for t in selected], ["email_tool"])

    def test_ambiguous_query_returns_empty(self):
        tools = [math_tool, email_tool]
        selected = select_relevant_tools("Can you help me with this?", tools)
        self.assertEqual(selected, [])

    def test_combined_query_returns_math_and_email(self):
        tools = [math_tool, email_tool]
        selected = select_relevant_tools("Calculate 25 * 50 and email the result to me", tools)
        self.assertEqual([t.name for t in selected], ["math_tool", "email_tool"])

    def test_missing_tool_in_pool_is_skipped(self):
        tools = [math_tool]
        selected = select_relevant_tools("Send an email please", tools)
        self.assertEqual(selected, [])


if __name__ == "__main__":
    unittest.main()


