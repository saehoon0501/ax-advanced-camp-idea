"""
TodoList Grader for coding agent evals.

Code-based grader that validates the agent's final todo_list state.
Checks that todos were created and all completed.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TodoListGradeResult:
    """Result from todo list grading."""


class TodoListGrader:
    """Validates the agent's final todo_list state."""

    def grade(self, final_state: dict[str, Any]) -> TodoListGradeResult:
        """
        Grade the final todo_list state.

        Args:
            final_state: Final agent state containing todo_list

        Returns:
            TodoListGradeResult with pass/fail, score, and details
        """

        return TodoListGradeResult()
