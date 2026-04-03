"""
Session Lifecycle Grader for coding agent evals.

Code-based grader that validates the agent followed the 3-phase session lifecycle
and used todo list as intended.

PHASE 1 - START: pwd, init.sh, read context files
PHASE 2 - WORK: feature focused, todo usage
PHASE 3 - END: git commit, update progress.md, update feature_list.json
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.messages import BaseMessage, ToolMessage, AIMessage


@dataclass
class PhaseResult:
    """Result for a single phase."""

    passed: bool
    score: float
    checks: dict[str, bool] = field(default_factory=dict)
    details: list[str] = field(default_factory=list)


@dataclass
class SessionLifecycleGradeResult:
    """Result from session lifecycle grading."""

    passed: bool
    score: float  # 0.0-1.0
    phase1_result: PhaseResult = field(default_factory=lambda: PhaseResult(False, 0.0))
    phase2_result: PhaseResult = field(default_factory=lambda: PhaseResult(False, 0.0))
    phase3_result: PhaseResult = field(default_factory=lambda: PhaseResult(False, 0.0))
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SessionLifecycleGrader:
    """Validates the agent followed the session lifecycle and used todo list properly."""

    def grade(
        self,
        messages: list[BaseMessage],
        workspace: Path,
    ) -> SessionLifecycleGradeResult:
        """
        Grade the session lifecycle adherence.

        Args:
            messages: Full conversation messages from agent.invoke()
            workspace: Path to the workspace directory

        Returns:
            SessionLifecycleGradeResult with pass/fail, score, and details
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Extract tool calls from messages
        tool_calls = self._extract_tool_calls(messages)

        # Grade each phase
        phase1_result = self._grade_phase1(tool_calls)
        phase2_result = self._grade_phase2(tool_calls, messages)
        phase3_result = self._grade_phase3(tool_calls, workspace)

        # Aggregate errors/warnings
        errors.extend(phase1_result.details)
        errors.extend(phase2_result.details)
        errors.extend(phase3_result.details)

        # Calculate overall score (equal weight per phase)
        overall_score = (
            phase1_result.score * 0.33
            + phase2_result.score * 0.34
            + phase3_result.score * 0.33
        )

        # Pass if all phases pass
        passed = phase1_result.passed and phase2_result.passed and phase3_result.passed

        return SessionLifecycleGradeResult(
            passed=passed,
            score=overall_score,
            phase1_result=phase1_result,
            phase2_result=phase2_result,
            phase3_result=phase3_result,
            errors=errors,
            warnings=warnings,
        )

    def _extract_tool_calls(
        self, messages: list[BaseMessage]
    ) -> list[dict[str, Any]]:
        """Extract tool call information from messages."""
        tool_calls = []

        for msg in messages:
            # Check AIMessage for tool_calls
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
                for tc in msg.tool_calls or []:
                    tool_calls.append({
                        "name": tc.get("name", ""),
                        "args": tc.get("args", {}),
                        "type": "call",
                    })

            # Check ToolMessage for results
            if isinstance(msg, ToolMessage):
                tool_calls.append({
                    "name": msg.name,
                    "content": msg.content,
                    "type": "result",
                })

        return tool_calls

    def _grade_phase1(self, tool_calls: list[dict[str, Any]]) -> PhaseResult:
        """
        Grade PHASE 1 - START (Recovery & Orientation).

        Checks:
        - pwd executed
        - init.sh executed
        - Read progress.md and feature_list.json
        """
        checks = {
            "pwd_executed": False,
            "init_sh_executed": False,
            "progress_read": False,
            "feature_list_read": False,
        }
        details = []

        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("args", {})

            # Check for bash commands
            if name in ("bash", "execute"):
                command = args.get("command", "")
                if "pwd" in command:
                    checks["pwd_executed"] = True
                if "init.sh" in command or "./init.sh" in command:
                    checks["init_sh_executed"] = True

            # Check for file reads
            if name in ("read_file", "file_read", "read"):
                file_path = (
                    args.get("validated_path", "")
                    or args.get("file_path", "")
                    or args.get("path", "")
                )
                if "progress.md" in file_path:
                    checks["progress_read"] = True
                if "feature_list.json" in file_path:
                    checks["feature_list_read"] = True

        # Calculate score
        required_checks = ["pwd_executed", "init_sh_executed", "progress_read", "feature_list_read"]
        passed_count = sum(1 for c in required_checks if checks[c])
        score = passed_count / len(required_checks)

        if not checks["pwd_executed"]:
            details.append("PHASE1: pwd not executed")
        if not checks["init_sh_executed"]:
            details.append("PHASE1: init.sh not executed")
        if not checks["progress_read"]:
            details.append("PHASE1: progress.md not read")
        if not checks["feature_list_read"]:
            details.append("PHASE1: feature_list.json not read")

        passed = all(checks[c] for c in required_checks)

        return PhaseResult(passed=passed, score=score, checks=checks, details=details)

    def _grade_phase2(
        self,
        tool_calls: list[dict[str, Any]],
        messages: list[BaseMessage],
    ) -> PhaseResult:
        """
        Grade PHASE 2 - WORK (Feature Implementation + Todo Usage).

        Checks:
        - Todos created early
        - Status updates (in_progress before, completed after)
        - Single in_progress at a time
        """
        checks = {
            "todos_created": False,
            "status_updates": False,
            "single_in_progress": True,  # Assume true, set false if violated
        }
        details = []

        todo_write_calls = []
        todo_write_indices = []

        for i, tc in enumerate(tool_calls):
            name = tc.get("name", "")
            if name in ("todo_write", "write_todos"):
                todo_write_calls.append(tc)
                todo_write_indices.append(i)

        # Check: Todos created
        if todo_write_calls:
            checks["todos_created"] = True

            # Check: Created early (in first 30% of tool calls)
            if tool_calls and todo_write_indices:
                first_todo_index = todo_write_indices[0]
                if first_todo_index > len(tool_calls) * 0.3:
                    details.append("PHASE2: Todos created late in session")
        else:
            details.append("PHASE2: No todo_write calls found")

        # Check: Status updates occurred
        if len(todo_write_calls) > 1:
            checks["status_updates"] = True
        elif len(todo_write_calls) == 1:
            # Only one call - check if it was just creation or included updates
            args = todo_write_calls[0].get("args", {})
            todos = args.get("todos", [])
            has_completed = any(t.get("status") == "completed" for t in todos)
            if has_completed:
                checks["status_updates"] = True
            else:
                details.append("PHASE2: No status updates - todos created but not updated")

        # Check: Single in_progress (analyze todo states)
        # This is a simplified check - would need full state tracking for accuracy
        for tc in todo_write_calls:
            args = tc.get("args", {})
            todos = args.get("todos", [])
            in_progress_count = sum(1 for t in todos if t.get("status") == "in_progress")
            if in_progress_count > 1:
                checks["single_in_progress"] = False
                details.append("PHASE2: Multiple todos in_progress simultaneously")
                break

        # Calculate score
        score = 0.0
        if checks["todos_created"]:
            score += 0.4
        if checks["status_updates"]:
            score += 0.4
        if checks["single_in_progress"]:
            score += 0.2

        passed = checks["todos_created"] and checks["status_updates"]

        return PhaseResult(passed=passed, score=score, checks=checks, details=details)

    def _grade_phase3(
        self,
        tool_calls: list[dict[str, Any]],
        workspace: Path,
    ) -> PhaseResult:
        """
        Grade PHASE 3 - END (Commit & Handoff).

        Checks:
        - Git commit created
        - progress.md updated
        - feature_list.json updated
        """
        checks = {
            "git_commit": False,
            "progress_updated": False,
            "feature_list_updated": False,
        }
        details = []

        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("args", {})

            # Check for git commit
            if name in ("bash", "execute"):
                command = args.get("command", "")
                if "git commit" in command:
                    checks["git_commit"] = True

            # Check for file writes/edits
            if name in ("write_file", "file_write", "write", "edit", "edit_file", "file_edit"):
                file_path = (
                    args.get("validated_path", "")
                    or args.get("file_path", "")
                    or args.get("path", "")
                )
                if "progress.md" in file_path:
                    checks["progress_updated"] = True
                if "feature_list.json" in file_path:
                    checks["feature_list_updated"] = True

        # Also check workspace files exist and were modified
        progress_file = workspace / "progress.md"
        feature_list_file = workspace / "feature_list.json"

        if progress_file.exists():
            # Could add content check here
            pass

        if feature_list_file.exists():
            # Could add content check here
            pass

        # Build details for missing checks
        if not checks["git_commit"]:
            details.append("PHASE3: No git commit created")
        if not checks["progress_updated"]:
            details.append("PHASE3: progress.md not updated")
        if not checks["feature_list_updated"]:
            details.append("PHASE3: feature_list.json not updated")

        # Calculate score
        required_checks = ["git_commit", "progress_updated", "feature_list_updated"]
        passed_count = sum(1 for c in required_checks if checks[c])
        score = passed_count / len(required_checks)

        passed = all(checks[c] for c in required_checks)

        return PhaseResult(passed=passed, score=score, checks=checks, details=details)
