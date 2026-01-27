"""
Init Script Grader for init.sh validation.

Code-based deterministic grader that validates:
- File exists and is executable (has shebang)
- Contains required commands for session continuity:
  - git log (to see recent commits)
  - cat progress.md (display current progress)
  - cat feature_list.json (show feature list)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class InitScriptGradeResult:
    """Result from init.sh grading."""

    passed: bool
    score: float  # 0.0-1.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    requirements_found: list[str] = field(default_factory=list)
    unnecessary_commands: list[str] = field(default_factory=list)


# Required elements in init.sh based on initializer prompt:
# ```bash
# #!/bin/bash
# git log --oneline -20
# cat progress.md
# cat feature_list.json
# ```

REQUIRED_PATTERNS = {
    "shebang": (
        r"^#!.*(?:bash|sh)",
        "Shebang (#!/bin/bash or similar)",
    ),
    "git_log": (
        r"git\s+log",
        "git log command (to see recent commits)",
    ),
    "cat_progress": (
        r"(?:cat|less|head|tail|more).*progress\.md",
        "Display progress.md content",
    ),
    "cat_feature_list": (
        r"(?:cat|less|head|tail|more|jq).*feature_list\.json",
        "Display feature_list.json content",
    ),
}

# Allowed patterns - these won't count as unnecessary
# Includes: comments, echo for display, git commands, cat for required files
ALLOWED_PATTERNS = [
    r"^#",                                    # Comments
    r"^\s*$",                                 # Empty lines
    r"echo\s+",                               # Echo statements (display)
    r"git\s+",                                # Any git command
    r"(?:cat|less|head|tail|more).*progress\.md",    # progress.md access
    r"(?:cat|less|head|tail|more|jq).*feature_list\.json",  # feature_list.json access
]

# Patterns that indicate unnecessary commands (penalty)
UNNECESSARY_PATTERNS = {
    "npm_commands": (
        r"npm\s+(?:install|start|run|test)",
        "npm commands (should not be in init.sh)",
    ),
    "node_commands": (
        r"(?<![a-zA-Z])node\s+",
        "node execution (should not be in init.sh)",
    ),
    "package_json": (
        r"package\.json",
        "package.json access (not essential for context recovery)",
    ),
    "env_file": (
        r"\.env",
        ".env file access (not essential for context recovery)",
    ),
    "server_check": (
        r"lsof|netstat|curl.*localhost",
        "Server status check (not essential for context recovery)",
    ),
    "mkdir_commands": (
        r"mkdir\s+",
        "mkdir commands (should not modify filesystem)",
    ),
    "rm_commands": (
        r"rm\s+",
        "rm commands (should not modify filesystem)",
    ),
    "chmod_commands": (
        r"chmod\s+",
        "chmod commands (should not modify filesystem)",
    ),
}


class InitScriptGrader:
    """Validates init.sh structure and required commands."""

    def grade(self, init_script_path: str | Path) -> InitScriptGradeResult:
        """
        Grade an init.sh file.

        Args:
            init_script_path: Path to the init.sh file

        Returns:
            InitScriptGradeResult with pass/fail, score, and error details
        """
        path = Path(init_script_path)
        errors: list[str] = []
        warnings: list[str] = []
        requirements_found: list[str] = []

        # Check 1: File exists
        if not path.exists():
            return InitScriptGradeResult(
                passed=False,
                score=0.0,
                errors=["File does not exist"],
            )

        # Check 2: File is readable
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return InitScriptGradeResult(
                passed=False,
                score=0.0,
                errors=[f"Cannot read file: {e}"],
            )

        # Check 3: File is not empty
        if not content.strip():
            return InitScriptGradeResult(
                passed=False,
                score=0.0,
                errors=["File is empty"],
            )

        # Check 4: Required patterns
        checks_passed = 0
        total_required = len(REQUIRED_PATTERNS)

        for name, (pattern, description) in REQUIRED_PATTERNS.items():
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                checks_passed += 1
                requirements_found.append(name)
            else:
                errors.append(f"Missing required element: {description}")

        # Check 5: Unnecessary commands (penalty)
        unnecessary_commands: list[str] = []
        penalty = 0.0

        for name, (pattern, description) in UNNECESSARY_PATTERNS.items():
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                unnecessary_commands.append(name)
                warnings.append(f"Unnecessary command found: {description}")
                penalty += 0.1  # 10% penalty per unnecessary command

        # Calculate score
        # Required patterns: 100% base, then subtract penalties
        required_score = checks_passed / total_required if total_required > 0 else 0
        score = max(0.0, required_score - penalty)  # Don't go below 0

        # Passed if all required patterns found (unnecessary commands don't cause failure)
        passed = len(errors) == 0

        return InitScriptGradeResult(
            passed=passed,
            score=score,
            errors=errors,
            warnings=warnings,
            requirements_found=requirements_found,
            unnecessary_commands=unnecessary_commands,
        )

