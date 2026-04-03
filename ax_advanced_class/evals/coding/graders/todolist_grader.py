"""
TodoList Grader for coding agent evals.

Code-based grader that validates the agent's final todos state.
Checks that todos were created and all completed.
Uses TodoListMiddleware's state key: "todos"
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TodoListGradeResult:
    """Result from todo list grading."""


class TodoListGrader:
    """Validates the agent's final todos state."""

    def grade(self, final_state: dict[str, Any]) -> TodoListGradeResult:
        """
        Grade the final todos state.

        Args:
            final_state: Final agent state containing todos (from TodoListMiddleware)

        Returns:
            TodoListGradeResult with pass/fail, score, and details
        """

        return TodoListGradeResult()
