"""
Dependency Grader for feature_list.json validation.

Code-based deterministic grader that validates:
- All dependencies reference existing feature IDs
- No circular dependencies (graph is a DAG)
- Priority distribution (not all same priority)
- Category coverage (at least 2 categories)
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DependencyGradeResult:
    """Result from dependency grading."""

    passed: bool
    score: float  # 0.0-1.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    priority_distribution: dict[str, int] = field(default_factory=dict)
    category_distribution: dict[str, int] = field(default_factory=dict)


class DependencyGrader:
    """Validates feature dependencies and distribution."""

    def grade(self, features: list[dict[str, Any]]) -> DependencyGradeResult:
        """
        Grade feature dependencies and distribution.

        Args:
            features: List of feature dicts (already parsed from JSON)

        Returns:
            DependencyGradeResult with pass/fail, score, and details
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Build ID set for reference checking
        feature_ids = {f.get("id") for f in features if "id" in f}

        # Check 1: Dependency validity
        invalid_deps = self._check_dependency_references(features, feature_ids)
        errors.extend(invalid_deps)

        # Check 2: Circular dependencies
        cycles = self._detect_cycles(features)
        errors.extend(cycles)

        # Check 3: Priority distribution
        priority_dist = self._get_priority_distribution(features)
        priority_errors, priority_warnings = self._check_priority_distribution(priority_dist)
        errors.extend(priority_errors)
        warnings.extend(priority_warnings)

        # Check 4: Category coverage
        category_dist = self._get_category_distribution(features)
        category_errors = self._check_category_coverage(category_dist)
        errors.extend(category_errors)

        # Calculate score
        total_checks = 4
        checks_passed = sum([
            len(invalid_deps) == 0,
            len(cycles) == 0,
            len(priority_errors) == 0,
            len(category_errors) == 0,
        ])
        score = checks_passed / total_checks

        return DependencyGradeResult(
            passed=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            priority_distribution=priority_dist,
            category_distribution=category_dist,
        )

    def _check_dependency_references(
        self, features: list[dict], valid_ids: set[str]
    ) -> list[str]:
        """Check that all dependencies reference existing feature IDs."""
        errors = []
        for feature in features:
            fid = feature.get("id", "unknown")
            deps = feature.get("dependencies", [])
            for dep in deps:
                if dep not in valid_ids:
                    errors.append(f"Feature '{fid}' has invalid dependency '{dep}'")
        return errors

    def _detect_cycles(self, features: list[dict]) -> list[str]:
        """Detect circular dependencies using DFS."""
        # Build adjacency list
        graph: dict[str, list[str]] = defaultdict(list)
        for feature in features:
            fid = feature.get("id")
            if fid:
                graph[fid] = feature.get("dependencies", [])

        # Track visited and recursion stack
        visited: set[str] = set()
        rec_stack: set[str] = set()
        cycles: list[str] = []

        def dfs(node: str, path: list[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path + [neighbor]):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(f"Circular dependency: {' -> '.join(cycle)}")
                    return True

            rec_stack.remove(node)
            return False

        for fid in graph:
            if fid not in visited:
                dfs(fid, [fid])

        return cycles

    def _get_priority_distribution(self, features: list[dict]) -> dict[str, int]:
        """Get count of features by priority."""
        dist: dict[str, int] = defaultdict(int)
        for feature in features:
            priority = feature.get("priority", "unknown")
            dist[priority] += 1
        return dict(dist)

    def _check_priority_distribution(
        self, dist: dict[str, int]
    ) -> tuple[list[str], list[str]]:
        """Check priority distribution for gaming."""
        errors = []
        warnings = []
        total = sum(dist.values())

        if total == 0:
            return errors, warnings

        # Check if all same priority (gaming)
        if len(dist) == 1:
            priority = list(dist.keys())[0]
            errors.append(f"All features have same priority '{priority}' (likely gaming)")

        # Check if high priority is overused (> 80%)
        high_count = dist.get("high", 0)
        if high_count / total > 0.8:
            warnings.append(f"High priority overused: {high_count}/{total} ({high_count/total:.0%})")

        return errors, warnings

    def _get_category_distribution(self, features: list[dict]) -> dict[str, int]:
        """Get count of features by category."""
        dist: dict[str, int] = defaultdict(int)
        for feature in features:
            category = feature.get("category", "unknown")
            dist[category] += 1
        return dict(dist)

    def _check_category_coverage(self, dist: dict[str, int]) -> list[str]:
        """Check that at least 2 categories are represented."""
        errors = []
        valid_categories = {"functional", "ui", "performance", "security"}
        covered = set(dist.keys()) & valid_categories

        if len(covered) < 2:
            errors.append(f"Insufficient category coverage: only {covered} represented (need at least 2)")

        return errors
