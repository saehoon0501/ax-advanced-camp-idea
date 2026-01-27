"""
Single Feature Grader for coding agent evals.

Code-based grader that validates the agent implemented exactly ONE feature.
Checks for scope creep and priority adherence.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}


@dataclass
class SingleFeatureGradeResult:
    """Result from single feature grading."""

    passed: bool
    score: float  # 0.0-1.0
    features_completed: int = 0
    implemented_feature_id: Optional[str] = None
    priority_respected: bool = True
    dependencies_satisfied: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SingleFeatureGrader:
    """Validates the agent implemented exactly ONE feature."""

    def grade(
        self,
        initial_feature_list: list[dict[str, Any]],
        final_feature_list: list[dict[str, Any]],
    ) -> SingleFeatureGradeResult:
        """
        Grade by comparing initial and final feature lists.

        Args:
            initial_feature_list: feature_list.json before agent run
            final_feature_list: feature_list.json after agent run

        Returns:
            SingleFeatureGradeResult with pass/fail, score, and details
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Build lookup maps
        initial_map = {f["id"]: f for f in initial_feature_list}
        final_map = {f["id"]: f for f in final_feature_list}

        # Find features that changed from passes=false to passes=true
        newly_completed = []
        for feature_id, final_feature in final_map.items():
            initial_feature = initial_map.get(feature_id)

            if initial_feature is None:
                warnings.append(f"New feature added: {feature_id}")
                continue

            initial_passes = initial_feature.get("passes", False)
            final_passes = final_feature.get("passes", False)

            if not initial_passes and final_passes:
                newly_completed.append(final_feature)

        features_completed = len(newly_completed)

        # Check: Exactly one feature completed
        if features_completed == 0:
            errors.append("No feature completed - agent did not mark any feature as passes=true")
            return SingleFeatureGradeResult(
                passed=False,
                score=0.0,
                features_completed=0,
                errors=errors,
                warnings=warnings,
            )

        if features_completed > 1:
            completed_ids = [f["id"] for f in newly_completed]
            errors.append(
                f"Scope creep: {features_completed} features completed instead of 1: {completed_ids}"
            )
            return SingleFeatureGradeResult(
                passed=False,
                score=0.3,  # Partial credit for completing work, but scope creep
                features_completed=features_completed,
                implemented_feature_id=completed_ids[0],
                errors=errors,
                warnings=warnings,
            )

        # Exactly one feature completed
        implemented_feature = newly_completed[0]
        implemented_id = implemented_feature["id"]

        # Check priority: Was this the highest priority available feature?
        priority_respected = self._check_priority_respected(
            initial_feature_list, implemented_feature
        )
        if not priority_respected:
            warnings.append(
                f"Priority not optimal: {implemented_id} is not the highest priority available feature"
            )

        # Check dependencies: Were all dependencies satisfied?
        dependencies_satisfied = self._check_dependencies_satisfied(
            initial_feature_list, implemented_feature
        )
        if not dependencies_satisfied:
            errors.append(
                f"Dependencies not satisfied for {implemented_id}"
            )

        # Calculate score
        if not dependencies_satisfied:
            score = 0.5  # Major issue: dependencies not met
        elif not priority_respected:
            score = 0.7  # Minor issue: suboptimal priority
        else:
            score = 1.0  # Perfect

        passed = features_completed == 1 and dependencies_satisfied

        return SingleFeatureGradeResult(
            passed=passed,
            score=score,
            features_completed=features_completed,
            implemented_feature_id=implemented_id,
            priority_respected=priority_respected,
            dependencies_satisfied=dependencies_satisfied,
            errors=errors,
            warnings=warnings,
        )

    def _check_priority_respected(
        self,
        initial_feature_list: list[dict[str, Any]],
        implemented_feature: dict[str, Any],
    ) -> bool:
        """Check if implemented feature was the highest priority available."""
        implemented_priority = PRIORITY_ORDER.get(
            implemented_feature.get("priority", "low"), 1
        )

        for feature in initial_feature_list:
            # Skip already completed features
            if feature.get("passes", False):
                continue

            # Skip the implemented feature itself
            if feature["id"] == implemented_feature["id"]:
                continue

            # Check if this feature has higher priority
            feature_priority = PRIORITY_ORDER.get(
                feature.get("priority", "low"), 1
            )

            if feature_priority > implemented_priority:
                # Check if this higher priority feature had satisfied dependencies
                if self._check_dependencies_satisfied(initial_feature_list, feature):
                    return False  # There was a higher priority feature available

        return True

    def _check_dependencies_satisfied(
        self,
        feature_list: list[dict[str, Any]],
        feature: dict[str, Any],
    ) -> bool:
        """Check if all dependencies of a feature are satisfied (passes=true)."""
        dependencies = feature.get("dependencies", [])

        if not dependencies:
            return True

        feature_map = {f["id"]: f for f in feature_list}

        for dep_id in dependencies:
            dep_feature = feature_map.get(dep_id)
            if dep_feature is None:
                return False  # Dependency not found
            if not dep_feature.get("passes", False):
                return False  # Dependency not completed

        return True
