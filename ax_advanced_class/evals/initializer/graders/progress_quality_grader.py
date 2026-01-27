"""
Progress Quality Grader for progress.md validation.

Model-based grader using LLM to evaluate CCAP criteria:
- Clarity: Is the session summary clear and understandable?
- Completeness: Does it capture what was done and why?
- Actionable: Is the "next priority" specific enough for Coding Agent?
- Parseable: Can a Coding Agent easily extract key info?
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Optional

from pydantic import BaseModel


PROGRESS_QUALITY_RUBRIC = """You are evaluating the quality of a progress.md file for a long-running coding project.

This file is used by Coding Agents to understand:
- What work was completed in previous sessions
- What the next priority is
- Any known issues or context needed

Score the progress file on these 4 criteria (0.0 to 1.0 each):

## CLARITY (Is the session summary clear and understandable?)
- 1.0: Crystal clear, any developer can understand immediately
- 0.5: Somewhat clear but requires some interpretation
- 0.0: Confusing or poorly written

## COMPLETENESS (Does it capture what was done and why?)
- 1.0: Comprehensive - includes what was done, decisions made, and reasoning
- 0.5: Partial - mentions what was done but lacks context/reasoning
- 0.0: Incomplete - missing key information about completed work

## ACTIONABLE (Is the "next priority" specific enough for Coding Agent?)
- 1.0: Clear next steps with specific feature IDs or tasks
- 0.5: General direction but lacks specificity
- 0.0: No clear next steps or vague instructions

## PARSEABLE (Can a Coding Agent easily extract key info programmatically?)
- 1.0: Well-structured with consistent formatting (headers, bullet points, labels)
- 0.5: Has some structure but inconsistent
- 0.0: Unstructured prose, hard to parse

---

Progress file content:
```markdown
{progress_content}
```

---

Respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{{"clarity": 0.8, "completeness": 0.7, "actionable": 0.9, "parseable": 0.6}}
"""


class ProgressScores(BaseModel):
    """Scores for progress.md quality."""

    clarity: float
    completeness: float
    actionable: float
    parseable: float


@dataclass
class ProgressQualityGradeResult:
    """Result from progress quality grading."""

    passed: bool
    score: float  # 0.0-1.0 (average of all CCAP scores)
    clarity: float = 0.0
    completeness: float = 0.0
    actionable: float = 0.0
    parseable: float = 0.0
    errors: list[str] = field(default_factory=list)


class ProgressQualityGrader:
    """LLM-based grader for progress.md quality (CCAP criteria)."""

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

    def grade(self, progress_path: str | Path) -> ProgressQualityGradeResult:
        """
        Grade progress.md quality using LLM.

        Args:
            progress_path: Path to progress.md file

        Returns:
            ProgressQualityGradeResult with CCAP scores
        """
        path = Path(progress_path)

        # Check file exists
        if not path.exists():
            return ProgressQualityGradeResult(
                passed=False,
                score=0.0,
                errors=["File does not exist"],
            )

        # Read content
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return ProgressQualityGradeResult(
                passed=False,
                score=0.0,
                errors=[f"Cannot read file: {e}"],
            )

        # Check not empty
        if not content.strip():
            return ProgressQualityGradeResult(
                passed=False,
                score=0.0,
                errors=["File is empty"],
            )

        # Grade with LLM
        try:
            scores = self._grade_content(content)
        except Exception as e:
            return ProgressQualityGradeResult(
                passed=False,
                score=0.0,
                errors=[f"LLM grading failed: {e}"],
            )

        # Calculate average score
        avg_score = mean([
            scores.clarity,
            scores.completeness,
            scores.actionable,
            scores.parseable,
        ])

        # Pass threshold: average >= 0.6
        passed = avg_score >= 0.6

        return ProgressQualityGradeResult(
            passed=passed,
            score=avg_score,
            clarity=scores.clarity,
            completeness=scores.completeness,
            actionable=scores.actionable,
            parseable=scores.parseable,
        )

    def _grade_content(self, content: str) -> ProgressScores:
        """Grade progress.md content using LLM."""
        # Truncate if too long (keep first 3000 chars)
        if len(content) > 3000:
            content = content[:3000] + "\n... (truncated)"

        prompt = PROGRESS_QUALITY_RUBRIC.format(progress_content=content)

        response = self.llm.invoke(prompt)
        response_content = response.content.strip()

        # Parse JSON response
        scores = self._parse_scores(response_content)
        return scores

    def _parse_scores(self, content: str) -> ProgressScores:
        """Parse LLM response into ProgressScores."""
        # Try direct JSON parse
        try:
            data = json.loads(content)
            return ProgressScores(**data)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return ProgressScores(**data)
            except json.JSONDecodeError:
                pass

        # Try to find JSON object anywhere in response
        json_match = re.search(r"\{[^{}]*\}", content)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return ProgressScores(**data)
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse LLM response as JSON: {content[:200]}")
