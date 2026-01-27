"""
Schema Grader for feature_list.json validation.

Code-based deterministic grader that validates:
- File exists and is valid JSON
- Required fields present in each feature
- Field types are correct
- ID format matches pattern
- Unique IDs
- Feature count in valid range
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SchemaGradeResult:
    """Result from schema grading."""

    passed: bool
    score: float  # 0.0-1.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    feature_count: int = 0


# Schema constants
REQUIRED_FIELDS = {"id", "category", "description", "priority", "steps", "passes", "dependencies"}
VALID_CATEGORIES = {"functional", "ui", "performance", "security"}
VALID_PRIORITIES = {"high", "medium", "low"}
ID_PATTERN = re.compile(r"^feature-\d+$")
MIN_FEATURES = 10
MAX_FEATURES = 200


class SchemaGrader:
    """Validates feature_list.json schema and structure."""

    def grade(self, feature_list_path: str | Path) -> SchemaGradeResult:
        """
        Grade a feature_list.json file.

        Args:
            feature_list_path: Path to the feature_list.json file

        Returns:
            SchemaGradeResult with pass/fail, score, and error details
        """
        path = Path(feature_list_path)
        errors: list[str] = []
        warnings: list[str] = []

        # Check 1: File exists
        if not path.exists():
            return SchemaGradeResult(
                passed=False,
                score=0.0,
                errors=["File does not exist"],
            )

        # Check 2: Valid JSON
        try:
            with open(path, "r", encoding="utf-8") as f:
                features = json.load(f)
        except json.JSONDecodeError as e:
            return SchemaGradeResult(
                passed=False,
                score=0.0,
                errors=[f"Invalid JSON: {e}"],
            )

        # Check 3: Is a list
        if not isinstance(features, list):
            return SchemaGradeResult(
                passed=False,
                score=0.0,
                errors=["Root element must be a list"],
            )

        # Check 4: Feature count
        feature_count = len(features)
        if feature_count < MIN_FEATURES:
            errors.append(f"Too few features: {feature_count} < {MIN_FEATURES}")
        elif feature_count > MAX_FEATURES:
            warnings.append(f"Many features: {feature_count} > {MAX_FEATURES} (allowed but may be hard to manage)")

        # Track IDs for uniqueness check
        seen_ids: set[str] = set()
        checks_passed = 0
        total_checks = 0

        for i, feature in enumerate(features):
            feature_errors = self._validate_feature(feature, i, seen_ids)
            total_checks += len(REQUIRED_FIELDS) + 3  # fields + id_format + id_unique + types
            checks_passed += (len(REQUIRED_FIELDS) + 3) - len(feature_errors)
            errors.extend(feature_errors)

        # Calculate score
        if total_checks == 0:
            score = 0.0
        else:
            score = checks_passed / total_checks

        # Passed if no errors (warnings are OK)
        passed = len(errors) == 0

        return SchemaGradeResult(
            passed=passed,
            score=score,
            errors=errors,
            warnings=warnings,
            feature_count=feature_count,
        )

    def _validate_feature(self, feature: Any, index: int, seen_ids: set[str]) -> list[str]:
        """Validate a single feature object."""
        errors: list[str] = []
        prefix = f"Feature [{index}]"

        # Must be a dict
        if not isinstance(feature, dict):
            return [f"{prefix}: Must be an object, got {type(feature).__name__}"]

        # Check required fields
        missing = REQUIRED_FIELDS - set(feature.keys())
        if missing:
            errors.append(f"{prefix}: Missing required fields: {missing}")

        # Validate field types and values
        if "id" in feature:
            fid = feature["id"]
            if not isinstance(fid, str):
                errors.append(f"{prefix}: 'id' must be string, got {type(fid).__name__}")
            elif not ID_PATTERN.match(fid):
                errors.append(f"{prefix}: 'id' must match pattern 'feature-NNN', got '{fid}'")
            elif fid in seen_ids:
                errors.append(f"{prefix}: Duplicate id '{fid}'")
            else:
                seen_ids.add(fid)

        if "category" in feature:
            cat = feature["category"]
            if not isinstance(cat, str):
                errors.append(f"{prefix}: 'category' must be string")
            elif cat not in VALID_CATEGORIES:
                errors.append(f"{prefix}: Invalid category '{cat}', must be one of {VALID_CATEGORIES}")

        if "priority" in feature:
            pri = feature["priority"]
            if not isinstance(pri, str):
                errors.append(f"{prefix}: 'priority' must be string")
            elif pri not in VALID_PRIORITIES:
                errors.append(f"{prefix}: Invalid priority '{pri}', must be one of {VALID_PRIORITIES}")

        if "description" in feature:
            desc = feature["description"]
            if not isinstance(desc, str):
                errors.append(f"{prefix}: 'description' must be string")
            elif len(desc) < 10:
                errors.append(f"{prefix}: 'description' too short (< 10 chars)")

        if "steps" in feature:
            steps = feature["steps"]
            if not isinstance(steps, list):
                errors.append(f"{prefix}: 'steps' must be list")
            elif len(steps) == 0:
                errors.append(f"{prefix}: 'steps' must have at least one step")
            elif not all(isinstance(s, str) for s in steps):
                errors.append(f"{prefix}: 'steps' must contain only strings")

        if "passes" in feature:
            passes = feature["passes"]
            if not isinstance(passes, bool):
                errors.append(f"{prefix}: 'passes' must be boolean, got {type(passes).__name__}")

        if "dependencies" in feature:
            deps = feature["dependencies"]
            if not isinstance(deps, list):
                errors.append(f"{prefix}: 'dependencies' must be list")
            elif not all(isinstance(d, str) for d in deps):
                errors.append(f"{prefix}: 'dependencies' must contain only strings")

        return errors
