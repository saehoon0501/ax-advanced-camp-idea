"""
Quality Grader for feature_list.json validation.

Model-based grader using LLM to evaluate ATIS criteria:
- Atomic: Can be completed in single session
- Testable: Has clear pass/fail criteria
- Independent: Minimal coupling
- Specific: Unambiguous implementation
"""

import json
import random
import re
from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Optional

from pydantic import BaseModel


QUALITY_RUBRIC = """You are evaluating the quality of a feature specification for a coding project.

Score the feature on these 4 criteria (0.0 to 1.0 each):

## ATOMIC (Can this feature be completed in a single coding session?)
- 1.0: Clear single task (e.g., "Add login button to header")
- 0.5: Multiple related tasks bundled together
- 0.0: Vague scope (e.g., "Build authentication system")

## TESTABLE (Can a user verify this with a clear pass/fail test?)
- 1.0: Explicit test steps or clear verification method
- 0.5: Implicit but derivable test
- 0.0: No clear verification method

## INDEPENDENT (Does this feature minimize coupling to other features?)
- 1.0: No dependencies or all dependencies clearly listed
- 0.5: Has implicit dependencies not listed
- 0.0: Tightly coupled, missing dependencies

## SPECIFIC (Could any developer implement this unambiguously?)
- 1.0: Clear requirements, no interpretation needed
- 0.5: Some ambiguity but reasonable defaults exist
- 0.0: Vague, multiple valid interpretations possible

---

Feature to evaluate:
{feature_json}

---

Respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{{"atomic": 0.8, "testable": 0.7, "independent": 0.9, "specific": 0.6}}
"""


class FeatureScores(BaseModel):
    """Scores for a single feature."""

    atomic: float
    testable: float
    independent: float
    specific: float


@dataclass
class QualityGradeResult:
    """Result from quality grading."""

    passed: bool
    score: float  # 0.0-1.0 (average of all ATIS scores)
    atomic: float = 0.0
    testable: float = 0.0
    independent: float = 0.0
    specific: float = 0.0
    sample_size: int = 0
    errors: list[str] = field(default_factory=list)
    feature_scores: list[dict[str, Any]] = field(default_factory=list)


class QualityGrader:
    """LLM-based grader for feature quality (ATIS criteria)."""

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
        self, features: list[dict[str, Any]], sample_size: int = 10
    ) -> QualityGradeResult:
        """
        Grade feature quality using LLM.

        Args:
            features: List of feature dicts
            sample_size: Number of features to sample (for efficiency)

        Returns:
            QualityGradeResult with ATIS scores
        """
        if not features:
            return QualityGradeResult(
                passed=False,
                score=0.0,
                errors=["No features to evaluate"],
            )

        # Sample features for efficiency
        sampled = random.sample(features, min(sample_size, len(features)))

        all_scores: list[FeatureScores] = []
        feature_scores: list[dict[str, Any]] = []
        errors: list[str] = []

        for feature in sampled:
            try:
                scores = self._grade_single_feature(feature)
                all_scores.append(scores)
                feature_scores.append({
                    "id": feature.get("id", "unknown"),
                    "scores": scores.model_dump(),
                })
            except Exception as e:
                errors.append(f"Failed to grade {feature.get('id', 'unknown')}: {e}")

        if not all_scores:
            return QualityGradeResult(
                passed=False,
                score=0.0,
                errors=errors or ["No features could be graded"],
            )

        # Calculate averages
        avg_atomic = mean([s.atomic for s in all_scores])
        avg_testable = mean([s.testable for s in all_scores])
        avg_independent = mean([s.independent for s in all_scores])
        avg_specific = mean([s.specific for s in all_scores])
        avg_score = mean([avg_atomic, avg_testable, avg_independent, avg_specific])

        # Pass threshold: average >= 0.6
        passed = avg_score >= 0.6

        return QualityGradeResult(
            passed=passed,
            score=avg_score,
            atomic=avg_atomic,
            testable=avg_testable,
            independent=avg_independent,
            specific=avg_specific,
            sample_size=len(sampled),
            errors=errors,
            feature_scores=feature_scores,
        )

    def _grade_single_feature(self, feature: dict[str, Any]) -> FeatureScores:
        """Grade a single feature using LLM."""
        prompt = QUALITY_RUBRIC.format(feature_json=json.dumps(feature, indent=2))

        response = self.llm.invoke(prompt)
        content = response.content.strip()

        # Parse JSON response
        scores = self._parse_scores(content)
        return scores

    def _parse_scores(self, content: str) -> FeatureScores:
        """Parse LLM response into FeatureScores."""
        # Try direct JSON parse
        try:
            data = json.loads(content)
            return FeatureScores(**data)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return FeatureScores(**data)
            except json.JSONDecodeError:
                pass

        # Try to find JSON object anywhere in response
        json_match = re.search(r"\{[^{}]*\}", content)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return FeatureScores(**data)
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse LLM response as JSON: {content[:200]}")
