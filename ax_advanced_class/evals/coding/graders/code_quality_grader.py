"""
Code Quality Grader for coding agent evals.

LLM-based grader that evaluates whether the code implementation
correctly fulfills the feature specification without overengineering.

Scores on FMCT criteria:
- Fulfillment: Does code satisfy feature requirements?
- Minimal: No overengineering?
- Consistent: Follows existing codebase patterns?
- Testable: Can be verified per acceptance criteria?
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel


CODE_QUALITY_RUBRIC = """You are evaluating code changes against a feature specification.

## Feature Being Implemented:
ID: {feature_id}
Description: {feature_description}
Category: {feature_category}
Priority: {feature_priority}
Acceptance Criteria:
{feature_steps}

## Code Changes (git diff):
```
{git_diff}
```

---

Score the implementation on these criteria (0.0 to 1.0 each):

## FULFILLMENT (Does the code satisfy the feature requirements?)
- 1.0: All acceptance criteria are fully implemented
- 0.7: Most criteria implemented, minor gaps
- 0.5: Partial implementation, some criteria missing
- 0.0: Does not address the feature requirements

## MINIMAL (Only what's needed, no overengineering?)
- 1.0: Only changes necessary for this feature, no extras
- 0.7: Minor unnecessary additions (extra validation, unused helpers)
- 0.5: Noticeable overengineering (premature abstractions)
- 0.0: Significant overengineering (frameworks, future-proofing, unrelated refactoring)

## CONSISTENT (Follows existing codebase patterns?)
- 1.0: Follows existing patterns exactly
- 0.7: Minor style deviations
- 0.5: Introduces some inconsistent patterns
- 0.0: Completely different style from codebase

## TESTABLE (Can the implementation be verified per the acceptance criteria?)
- 1.0: Clear verification path, tests included if appropriate
- 0.7: Verifiable but missing some test coverage
- 0.5: Difficult to verify against criteria
- 0.0: Cannot be verified or tests broken

---

Respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{{"fulfillment": 0.8, "minimal": 0.7, "consistent": 0.9, "testable": 0.6}}
"""


class FMCTScores(BaseModel):
    """FMCT scores for code quality."""

    fulfillment: float
    minimal: float
    consistent: float
    testable: float


@dataclass
class CodeQualityGradeResult:
    """Result from code quality grading."""

    passed: bool
    score: float  # 0.0-1.0 (average of FMCT scores)
    fulfillment: float = 0.0
    minimal: float = 0.0
    consistent: float = 0.0
    testable: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CodeQualityGrader:
    """LLM-based grader for code quality (FMCT criteria)."""

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

    def grade(
        self,
        git_diff: str,
        implemented_feature: Optional[dict[str, Any]],
    ) -> CodeQualityGradeResult:
        """
        Grade code quality using LLM.

        Args:
            git_diff: The git diff output showing code changes
            implemented_feature: The feature_list item that was implemented

        Returns:
            CodeQualityGradeResult with FMCT scores
        """
        errors: list[str] = []

        # Handle missing inputs
        if not git_diff or git_diff.strip() == "":
            return CodeQualityGradeResult(
                passed=False,
                score=0.0,
                errors=["No code changes (empty git diff)"],
            )

        if not implemented_feature:
            return CodeQualityGradeResult(
                passed=False,
                score=0.0,
                errors=["No implemented feature to evaluate against"],
            )

        # Format feature steps
        steps = implemented_feature.get("steps", [])
        steps_formatted = "\n".join(f"- {step}" for step in steps)

        # Build prompt
        prompt = CODE_QUALITY_RUBRIC.format(
            feature_id=implemented_feature.get("id", "unknown"),
            feature_description=implemented_feature.get("description", "No description"),
            feature_category=implemented_feature.get("category", "unknown"),
            feature_priority=implemented_feature.get("priority", "unknown"),
            feature_steps=steps_formatted or "No acceptance criteria specified",
            git_diff=git_diff[:10000],  # Limit diff size
        )

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            scores = self._parse_scores(content)
        except Exception as e:
            errors.append(f"LLM grading failed: {e}")
            return CodeQualityGradeResult(
                passed=False,
                score=0.0,
                errors=errors,
            )

        # Calculate average score
        avg_score = (
            scores.fulfillment + scores.minimal + scores.consistent + scores.testable
        ) / 4

        # Pass threshold: average >= 0.6
        passed = avg_score >= 0.6

        return CodeQualityGradeResult(
            passed=passed,
            score=avg_score,
            fulfillment=scores.fulfillment,
            minimal=scores.minimal,
            consistent=scores.consistent,
            testable=scores.testable,
            errors=errors,
        )

    def _parse_scores(self, content: str) -> FMCTScores:
        """Parse LLM response into FMCTScores."""
        # Try direct JSON parse
        try:
            data = json.loads(content)
            return FMCTScores(**data)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return FMCTScores(**data)
            except json.JSONDecodeError:
                pass

        # Try to find JSON object anywhere in response
        json_match = re.search(r"\{[^{}]*\}", content)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return FMCTScores(**data)
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse LLM response as JSON: {content[:200]}")
