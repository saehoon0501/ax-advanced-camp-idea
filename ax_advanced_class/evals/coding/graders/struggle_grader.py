"""
Struggle Grader for coding agent evals.

LLM-based grader that assesses how smoothly the agent completed the task.
Evaluates debugging efficiency, recovery from errors, and focus.

Scores on ERFC criteria:
- Efficiency: Direct path to solution, minimal backtracking
- Recovery: Quick recovery from errors
- Focus: Stayed on task, no tangents
- Completion: Task fully completed with verification
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
from pydantic import BaseModel


STRUGGLE_RUBRIC = """You are analyzing an AI coding agent's work transcript to assess how smoothly it completed its task.

## Agent Transcript Summary:
{transcript_summary}

---

Score the agent's performance on these criteria (0.0 to 1.0 each):

## EFFICIENCY (Direct path to solution?)
- 1.0: Direct path to solution, minimal backtracking
- 0.5: Some trial-and-error but reasonable
- 0.0: Excessive debugging loops, repeated failures

## RECOVERY (Quick recovery from errors?)
- 1.0: When errors occurred, recovered quickly and correctly
- 0.5: Recovered but with some wasted effort
- 0.0: Got stuck, made things worse, or gave up

## FOCUS (Stayed on task?)
- 1.0: Stayed on task, no tangents
- 0.5: Minor distractions but completed task
- 0.0: Significant tangents, scope creep attempts

## COMPLETION (Task fully done?)
- 1.0: Task fully completed with verification
- 0.5: Task mostly done, minor issues remain
- 0.0: Task incomplete or broken state left

---

Respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{{"efficiency": 0.8, "recovery": 0.7, "focus": 0.9, "completion": 0.6}}
"""


class ERFCScores(BaseModel):
    """ERFC scores for struggle assessment."""

    efficiency: float
    recovery: float
    focus: float
    completion: float


@dataclass
class StruggleGradeResult:
    """Result from struggle grading."""

    passed: bool
    score: float  # 0.0-1.0 (average of ERFC scores)
    efficiency: float = 0.0
    recovery: float = 0.0
    focus: float = 0.0
    completion: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class StruggleGrader:
    """LLM-based grader for agent struggle/efficiency (ERFC criteria)."""

    def __init__(self, llm: Optional[Any] = None):
        """
        Initialize with optional LLM instance.

        Args:
            llm: LangChain LLM instance. If None, will create from BedrockClient.
        """
        self._llm = llm

    @property
    def llm(self):
        """Lazy-load LLM from BedrockClient if not provided."""
        if self._llm is None:
            from ax_advanced_class.src.llm.bedrock_client import BedrockClient

            self._llm = BedrockClient().get_core()
        return self._llm

    def grade(self, messages: list[BaseMessage]) -> StruggleGradeResult:
        """
        Grade agent struggle/efficiency using LLM.

        Args:
            messages: Full conversation messages from agent.invoke()

        Returns:
            StruggleGradeResult with ERFC scores
        """
        errors: list[str] = []

        if not messages:
            return StruggleGradeResult(
                passed=False,
                score=0.0,
                errors=["No messages to analyze"],
            )

        # Summarize transcript for LLM
        transcript_summary = self._summarize_transcript(messages)

        # Build prompt
        prompt = STRUGGLE_RUBRIC.format(transcript_summary=transcript_summary)

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            scores = self._parse_scores(content)
        except Exception as e:
            errors.append(f"LLM grading failed: {e}")
            return StruggleGradeResult(
                passed=False,
                score=0.0,
                errors=errors,
            )

        # Calculate average score
        avg_score = (
            scores.efficiency + scores.recovery + scores.focus + scores.completion
        ) / 4

        # Pass threshold: average >= 0.5 (more lenient than code quality)
        passed = avg_score >= 0.5

        return StruggleGradeResult(
            passed=passed,
            score=avg_score,
            efficiency=scores.efficiency,
            recovery=scores.recovery,
            focus=scores.focus,
            completion=scores.completion,
            errors=errors,
        )

    def _summarize_transcript(self, messages: list[BaseMessage]) -> str:
        """Summarize the transcript for LLM analysis."""
        summary_parts = []
        tool_call_count = 0
        error_count = 0
        retry_patterns = 0

        for i, msg in enumerate(messages):
            if isinstance(msg, HumanMessage):
                content = str(msg.content)[:200]
                summary_parts.append(f"[Human] {content}")

            elif isinstance(msg, AIMessage):
                # Count tool calls
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_call_count += len(msg.tool_calls)
                    tool_names = [tc.get("name", "unknown") for tc in msg.tool_calls]
                    summary_parts.append(f"[Agent] Called tools: {', '.join(tool_names)}")
                else:
                    content = str(msg.content)[:300]
                    summary_parts.append(f"[Agent] {content}")

            elif isinstance(msg, ToolMessage):
                content = str(msg.content)
                # Check for errors
                if "error" in content.lower() or "failed" in content.lower():
                    error_count += 1
                    summary_parts.append(f"[Tool:{msg.name}] ERROR: {content[:200]}")
                else:
                    summary_parts.append(f"[Tool:{msg.name}] Success (truncated)")

        # Add statistics
        stats = f"""
--- Transcript Statistics ---
Total messages: {len(messages)}
Tool calls: {tool_call_count}
Errors encountered: {error_count}
"""

        # Limit summary length
        full_summary = "\n".join(summary_parts[-50:])  # Last 50 entries
        if len(full_summary) > 8000:
            full_summary = full_summary[:8000] + "\n... (truncated)"

        return stats + "\n--- Transcript ---\n" + full_summary

    def _parse_scores(self, content: str) -> ERFCScores:
        """Parse LLM response into ERFCScores."""
        # Try direct JSON parse
        try:
            data = json.loads(content)
            return ERFCScores(**data)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return ERFCScores(**data)
            except json.JSONDecodeError:
                pass

        # Try to find JSON object anywhere in response
        json_match = re.search(r"\{[^{}]*\}", content)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return ERFCScores(**data)
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse LLM response as JSON: {content[:200]}")
