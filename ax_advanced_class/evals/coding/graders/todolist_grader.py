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

    passed: bool
    score: float  # 0.0-1.0
    todos_created: bool = False
    total_todos: int = 0
    completed_count: int = 0
    in_progress_count: int = 0
    pending_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


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
        errors: list[str] = []
        warnings: list[str] = []

        # Extract todo_list from state
        todo_list = final_state.get("todo_list", [])

        # Check 1: Todos exist
        if not todo_list:
            return TodoListGradeResult(
                passed=False,
                score=0.0,
                todos_created=False,
                errors=["No todos created - agent did not use todo_list"],
            )

        # Count by status
        total = len(todo_list)
        completed = 0
        in_progress = 0
        pending = 0

        for todo in todo_list:
            status = todo.get("status", "unknown")
            if status == "completed":
                completed += 1
            elif status == "in_progress":
                in_progress += 1
            elif status == "pending":
                pending += 1
            else:
                warnings.append(f"Unknown todo status: {status}")

        # Check 2: All completed
        if in_progress > 0:
            errors.append(
                f"{in_progress} todo(s) still in_progress - session may have timed out"
            )

        if pending > 0:
            errors.append(f"{pending} todo(s) still pending - work incomplete")

        # Calculate score based on completion ratio
        if total > 0:
            score = completed / total
        else:
            score = 0.0

        # Determine pass/fail
        # Pass if all todos completed (score == 1.0)
        passed = score == 1.0

        return TodoListGradeResult(
            passed=passed,
            score=score,
            todos_created=True,
            total_todos=total,
            completed_count=completed,
            in_progress_count=in_progress,
            pending_count=pending,
            errors=errors,
            warnings=warnings,
        )
