"""
Eval runner for initializer agent.

Invokes the initializer agent with a test case, then runs graders
to validate the output.
"""

# Load environment FIRST (before any other imports)
from ax_advanced_class.src.utils.env_loader import load_dotenv
load_dotenv()

# SSL certificate handling
import truststore
truststore.inject_into_ssl()

import argparse
import json
import os
import tempfile
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

from langchain_core.messages import HumanMessage

from ax_advanced_class.evals.initializer.graders import (
    SchemaGrader,
    DependencyGrader,
    QualityGrader,
    ProgressGrader,
    ProgressQualityGrader,
    InitScriptGrader,
)
from ax_advanced_class.evals.initializer.graders.schema_grader import SchemaGradeResult
from ax_advanced_class.evals.initializer.graders.dependency_grader import DependencyGradeResult
from ax_advanced_class.evals.initializer.graders.quality_grader import QualityGradeResult
from ax_advanced_class.evals.initializer.graders.progress_grader import ProgressGradeResult
from ax_advanced_class.evals.initializer.graders.progress_quality_grader import ProgressQualityGradeResult
from ax_advanced_class.evals.initializer.graders.init_script_grader import InitScriptGradeResult


@dataclass
class EvalReport:
    """Complete eval report for an initializer agent run."""

    test_case_name: str
    passed: bool
    overall_score: float  # 0.0-1.0

    # Individual grader results
    schema_result: Optional[SchemaGradeResult] = None
    dependency_result: Optional[DependencyGradeResult] = None
    quality_result: Optional[QualityGradeResult] = None
    progress_result: Optional[ProgressGradeResult] = None
    progress_quality_result: Optional[ProgressQualityGradeResult] = None
    init_script_result: Optional[InitScriptGradeResult] = None

    # Execution details
    agent_error: Optional[str] = None
    workspace_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        result = {
            "test_case_name": self.test_case_name,
            "passed": self.passed,
            "overall_score": self.overall_score,
            "agent_error": self.agent_error,
            "workspace_path": self.workspace_path,
        }
        if self.schema_result:
            result["schema"] = asdict(self.schema_result)
        if self.dependency_result:
            result["dependency"] = asdict(self.dependency_result)
        if self.quality_result:
            result["quality"] = asdict(self.quality_result)
        if self.progress_result:
            result["progress"] = asdict(self.progress_result)
        if self.progress_quality_result:
            result["progress_quality"] = asdict(self.progress_quality_result)
        if self.init_script_result:
            result["init_script"] = asdict(self.init_script_result)
        return result


def load_test_case(path: Path) -> dict[str, Any]:
    """Load a test case from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _clean_workspace(workspace_dir: Path) -> None:
    """Remove agent output files from workspace before a fresh run."""
    files_to_remove = ["feature_list.json", "progress.md", "init.sh"]
    for filename in files_to_remove:
        filepath = workspace_dir / filename
        if filepath.exists():
            filepath.unlink()


def run_eval(
    test_case: dict[str, Any],
    workspace_dir: Optional[Path] = None,
    skip_agent: bool = False,
    quality_sample_size: int = 10,
    clean_workspace: bool = True,
) -> EvalReport:
    """
    Run eval for a test case.

    Args:
        test_case: Test case dict with 'name' and 'description'
        workspace_dir: Directory to use for agent output. If None, creates temp dir.
        skip_agent: If True, skip agent invocation (for testing graders on existing files)
        quality_sample_size: Number of features to sample for quality grading
        clean_workspace: If True, remove existing agent output files before running

    Returns:
        EvalReport with all grader results
    """
    test_name = test_case.get("name", "unknown")

    # Setup workspace
    if workspace_dir is None:
        workspace_dir = Path(tempfile.mkdtemp(prefix="eval_"))
    workspace_dir = Path(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    feature_list_path = workspace_dir / "feature_list.json"

    # Clean workspace before agent run
    if not skip_agent and clean_workspace:
        _clean_workspace(workspace_dir)

    # Run agent if not skipping
    if not skip_agent:
        try:
            _run_agent(test_case, workspace_dir)
        except Exception as e:
            return EvalReport(
                test_case_name=test_name,
                passed=False,
                overall_score=0.0,
                agent_error=str(e),
                workspace_path=str(workspace_dir),
            )

    progress_path = workspace_dir / "progress.md"
    init_script_path = workspace_dir / "init.sh"

    # Run schema grader
    schema_grader = SchemaGrader()
    schema_result = schema_grader.grade(feature_list_path)

    # Run progress graders (independent of schema)
    progress_grader = ProgressGrader()
    progress_result = progress_grader.grade(progress_path)

    progress_quality_grader = ProgressQualityGrader()
    progress_quality_result = progress_quality_grader.grade(progress_path)

    # Run init script grader (independent of schema)
    init_script_grader = InitScriptGrader()
    init_script_result = init_script_grader.grade(init_script_path)

    # If schema fails, can't run feature-dependent graders
    if not schema_result.passed:
        # Calculate partial score: Schema 25%, Progress 10%, Progress Quality 10%, Init Script 5%
        overall_score = (
            schema_result.score * 0.25
            + progress_result.score * 0.10
            + progress_quality_result.score * 0.10
            + init_script_result.score * 0.05
        )
        return EvalReport(
            test_case_name=test_name,
            passed=False,
            overall_score=overall_score,
            schema_result=schema_result,
            progress_result=progress_result,
            progress_quality_result=progress_quality_result,
            init_script_result=init_script_result,
            workspace_path=str(workspace_dir),
        )

    # Load features for other graders
    with open(feature_list_path, "r", encoding="utf-8") as f:
        features = json.load(f)

    # Run dependency grader
    dependency_grader = DependencyGrader()
    dependency_result = dependency_grader.grade(features)

    # Run quality grader
    quality_grader = QualityGrader()
    quality_result = quality_grader.grade(features, sample_size=quality_sample_size)

    # Calculate overall score (weighted average)
    # Schema: 25%, Dependency: 15%, Quality: 20%, Progress: 10%, Progress Quality: 15%, Init Script: 15%
    overall_score = (
        schema_result.score * 0.25
        + dependency_result.score * 0.15
        + quality_result.score * 0.20
        + progress_result.score * 0.10
        + progress_quality_result.score * 0.15
        + init_script_result.score * 0.15
    )

    # Passed if all graders pass
    passed = (
        schema_result.passed
        and dependency_result.passed
        and quality_result.passed
        and progress_result.passed
        and progress_quality_result.passed
        and init_script_result.passed
    )

    return EvalReport(
        test_case_name=test_name,
        passed=passed,
        overall_score=overall_score,
        schema_result=schema_result,
        dependency_result=dependency_result,
        quality_result=quality_result,
        progress_result=progress_result,
        progress_quality_result=progress_quality_result,
        init_script_result=init_script_result,
        workspace_path=str(workspace_dir),
    )


class EvalInterruptError(Exception):
    """Raised when agent hits an interrupt (ASK permission) during eval."""
    pass


def _run_agent(test_case: dict[str, Any], workspace_dir: Path) -> None:
    """
    Run the initializer agent directly with the test case.

    Args:
        test_case: Test case dict with 'description'
        workspace_dir: Directory for agent output

    Raises:
        EvalInterruptError: If agent hits an interrupt (ASK permission)
    """
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.errors import GraphInterrupt
    from langchain.agents import create_agent

    from ax_advanced_class.src.llm.bedrock_client import BedrockClient
    from ax_advanced_class.src.agents import initializer_agent_spec
    from ax_advanced_class.evals.initializer.eval_permission_config import (
        create_eval_permission_config,
    )

    # Ensure workspace exists
    workspace_dir = Path(workspace_dir).resolve()
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Create eval-specific permission config:
    # - File operations within workspace: ALLOW
    # - Git commands: DENY (no interrupt, just error)
    # - No ASK permissions (would hang test)
    permission_config = create_eval_permission_config(str(workspace_dir))

    # Create initializer agent directly with eval-specific config
    llm = BedrockClient().get_core()
    spec = initializer_agent_spec(config=permission_config)

    # Create agent with MemorySaver (required for root graph)
    agent = create_agent(
        model=llm,
        tools=list(spec.tools),
        middleware=list(spec.middleware),
        name=spec.name,
        state_schema=spec.state_schema,
        checkpointer=MemorySaver(),
    )
    agent = agent.with_config({"recursion_limit": 500})

    # Build prompt from test case
    description = test_case.get("description", "")
    prompt = f"""Please set up a new project with the following requirements:

{description}

Create the feature_list.json file in {workspace_dir} with all features needed for this project."""

    # Invoke agent with thread_id
    thread_id = f"eval_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        _result = agent.invoke(
            {"messages": [HumanMessage(content=prompt)], "todo_list": []},
            config=config,
        )
    except GraphInterrupt as e:
        # Convert interrupt to error so test fails instead of hanging
        interrupt_data = e.args[0] if e.args else "Unknown"
        raise EvalInterruptError(
            f"Agent hit ASK permission (interrupt). "
            f"This should not happen in eval - check permission config. "
            f"Interrupt data: {interrupt_data}"
        ) from e


def run_eval_on_existing(
    feature_list_path: Path,
    quality_sample_size: int = 10,
) -> EvalReport:
    """
    Run eval on an existing feature_list.json file (skip agent invocation).

    Args:
        feature_list_path: Path to existing feature_list.json
        quality_sample_size: Number of features to sample for quality grading

    Returns:
        EvalReport with all grader results
    """
    test_case = {"name": f"existing:{feature_list_path.name}"}
    return run_eval(
        test_case=test_case,
        workspace_dir=feature_list_path.parent,
        skip_agent=True,
        quality_sample_size=quality_sample_size,
    )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run initializer agent evals")
    parser.add_argument(
        "--test-case",
        type=Path,
        help="Path to test case JSON file",
    )
    parser.add_argument(
        "--existing",
        type=Path,
        help="Path to existing feature_list.json (skip agent)",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Workspace directory for agent output",
    )
    parser.add_argument(
        "--quality-sample-size",
        type=int,
        default=10,
        help="Number of features to sample for quality grading",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip workspace cleanup before agent run",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to write JSON report",
    )

    args = parser.parse_args()

    if args.existing:
        report = run_eval_on_existing(
            args.existing,
            quality_sample_size=args.quality_sample_size,
        )
    elif args.test_case:
        test_case = load_test_case(args.test_case)
        report = run_eval(
            test_case=test_case,
            workspace_dir=args.workspace,
            quality_sample_size=args.quality_sample_size,
            clean_workspace=not args.no_clean,
        )
    else:
        parser.error("Either --test-case or --existing is required")

    # Print report
    report_dict = report.to_dict()
    print(json.dumps(report_dict, indent=2))

    # Write to file if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)

    # Exit with appropriate code
    exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
