"""
Progress Grader for progress.md validation.

Code-based deterministic grader that validates:
- File exists
- Has required sections (Project name, Status, Session History)
- Has proper structure for Coding Agent to parse
"""

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProgressGradeResult:
    """Result from progress.md grading."""

    passed: bool
    score: float  # 0.0-1.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sections_found: list[str] = field(default_factory=list)


# Required patterns in progress.md
# Based on initializer prompt template:
# ```
# # Project Progress Log
# Project: [project_name]
# Initialized: [timestamp]
# Status: Initialized
#
# ## Session History
# ### Session 1 - Initialization
# - Created feature list with [N] features
# ```

REQUIRED_PATTERNS = {
    "header": (r"#\s*Project\s+Progress", "Header '# Project Progress Log' or similar"),
    "project_name": (r"Project:\s*.+", "Project: [name] line"),
    "session_history": (r"##?\s*Session\s*(History|1)", "Session History or Session 1 section"),
}

OPTIONAL_PATTERNS = {
    "initialized": (r"Initialized:\s*.+", "Initialized: [timestamp] line"),
    "status": (r"Status:\s*.+", "Status: [status] line"),
    "next_priority": (r"Next\s*(priority)?:\s*.+", "Next priority indication"),
    "feature_count": (r"(\d+)\s*features?", "Feature count mention"),
}


class ProgressGrader:
    """Validates progress.md structure and content."""

    def grade(self, progress_path: str | Path) -> ProgressGradeResult:
        """
        Grade a progress.md file.

        Args:
            progress_path: Path to the progress.md file

        Returns:
            ProgressGradeResult with pass/fail, score, and error details
        """
        path = Path(progress_path)
        errors: list[str] = []
        warnings: list[str] = []
        sections_found: list[str] = []

        # Check 1: File exists
        if not path.exists():
            return ProgressGradeResult(
                passed=False,
                score=0.0,
                errors=["File does not exist"],
            )

        # Check 2: File is readable
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return ProgressGradeResult(
                passed=False,
                score=0.0,
                errors=[f"Cannot read file: {e}"],
            )

        # Check 3: File is not empty
        if not content.strip():
            return ProgressGradeResult(
                passed=False,
                score=0.0,
                errors=["File is empty"],
            )

        # Check 4: Required patterns
        checks_passed = 0
        total_required = len(REQUIRED_PATTERNS)

        for name, (pattern, description) in REQUIRED_PATTERNS.items():
            if re.search(pattern, content, re.IGNORECASE):
                checks_passed += 1
                sections_found.append(name)
            else:
                errors.append(f"Missing required section: {description}")

        # Check 5: Optional patterns (contribute to score but don't fail)
        total_optional = len(OPTIONAL_PATTERNS)
        optional_found = 0

        for name, (pattern, description) in OPTIONAL_PATTERNS.items():
            if re.search(pattern, content, re.IGNORECASE):
                optional_found += 1
                sections_found.append(name)
            else:
                warnings.append(f"Missing optional section: {description}")

        # Check 6: Content quality checks
        quality_checks = self._check_content_quality(content)
        warnings.extend(quality_checks["warnings"])

        # Calculate score
        # Required: 70% weight, Optional: 30% weight
        required_score = checks_passed / total_required if total_required > 0 else 0
        optional_score = optional_found / total_optional if total_optional > 0 else 0
        score = required_score * 0.7 + optional_score * 0.3

        # Passed if all required patterns found
        passed = len(errors) == 0

        return ProgressGradeResult(
            passed=passed,
            score=score,
            errors=errors,
            warnings=warnings,
            sections_found=sections_found,
        )

    def _check_content_quality(self, content: str) -> dict[str, list[str]]:
        """Check additional content quality metrics."""
        warnings: list[str] = []

        # Check minimum length (should have some substance)
        if len(content) < 100:
            warnings.append("Content is very short (< 100 chars)")

        # Check for markdown structure
        if not re.search(r"^#+\s", content, re.MULTILINE):
            warnings.append("No markdown headers found")

        # Check for bullet points or structured content
        if not re.search(r"^[\-\*]\s", content, re.MULTILINE):
            warnings.append("No bullet points found - may lack detail")

        return {"warnings": warnings}
