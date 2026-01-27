"""
Eval runner for coding agent.

Invokes the coding agent with a test case, then runs graders
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
import subprocess
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

from langchain_core.messages import HumanMessage, BaseMessage

from ax_advanced_class.evals.coding.graders import (
    TodoListGrader,
    SingleFeatureGrader,
    SessionLifecycleGrader,
    CodeQualityGrader,
    StruggleGrader,
)
from ax_advanced_class.evals.coding.graders.todolist_grader import TodoListGradeResult
from ax_advanced_class.evals.coding.graders.single_feature_grader import SingleFeatureGradeResult
from ax_advanced_class.evals.coding.graders.session_lifecycle_grader import SessionLifecycleGradeResult
from ax_advanced_class.evals.coding.graders.code_quality_grader import CodeQualityGradeResult
from ax_advanced_class.evals.coding.graders.struggle_grader import StruggleGradeResult


TIMEOUT_SECONDS = 600  # 10 minutes

# Eval workspace directory - use ./workspace directly (same as agent's workspace)
EVAL_WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent / "workspace"


@dataclass
class EvalReport:
    """Complete eval report for a coding agent run."""

    test_case_name: str
    passed: bool
    overall_score: float  # 0.0-1.0

    # Individual grader results
    todolist_result: Optional[TodoListGradeResult] = None
    single_feature_result: Optional[SingleFeatureGradeResult] = None
    session_lifecycle_result: Optional[SessionLifecycleGradeResult] = None
    code_quality_result: Optional[CodeQualityGradeResult] = None
    struggle_result: Optional[StruggleGradeResult] = None

    # Execution details
    agent_error: Optional[str] = None
    workspace_path: Optional[str] = None
    implemented_feature: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        result = {
            "test_case_name": self.test_case_name,
            "passed": self.passed,
            "overall_score": self.overall_score,
            "agent_error": self.agent_error,
            "workspace_path": self.workspace_path,
            "implemented_feature": self.implemented_feature,
        }
        if self.todolist_result:
            result["todolist"] = asdict(self.todolist_result)
        if self.single_feature_result:
            result["single_feature"] = asdict(self.single_feature_result)
        if self.session_lifecycle_result:
            result["session_lifecycle"] = asdict(self.session_lifecycle_result)
        if self.code_quality_result:
            result["code_quality"] = asdict(self.code_quality_result)
        if self.struggle_result:
            result["struggle"] = asdict(self.struggle_result)
        return result


def load_test_case(path: Path) -> dict[str, Any]:
    """Load a test case from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_eval(
    test_case: dict[str, Any],
    workspace_dir: Optional[Path] = None,
    skip_agent: bool = False,
) -> EvalReport:
    """
    Run eval for a coding agent test case.

    Args:
        test_case: Test case dict with setup files and expected behavior
        workspace_dir: Directory to use for agent output. If None, creates temp dir.
        skip_agent: If True, skip agent invocation (for testing graders on existing workspace)

    Returns:
        EvalReport with all grader results
    """
    test_name = test_case.get("name", "unknown")

    # Use ./workspace directly (same as agent's workspace from PermissionConfig)
    if workspace_dir is None:
        workspace_dir = EVAL_WORKSPACE_ROOT
    workspace_dir = Path(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Setup workspace files from test case
    if not skip_agent:
        _setup_workspace(test_case, workspace_dir)

    # Capture initial feature_list
    initial_feature_list = _load_feature_list(workspace_dir)

    # Run agent if not skipping
    messages: list[BaseMessage] = []
    final_state: dict[str, Any] = {}

    if not skip_agent:
        try:
            messages, final_state = _run_agent(test_case, workspace_dir)
        except Exception as e:
            return EvalReport(
                test_case_name=test_name,
                passed=False,
                overall_score=0.0,
                agent_error=str(e),
                workspace_path=str(workspace_dir),
            )

    # Capture final feature_list
    final_feature_list = _load_feature_list(workspace_dir)

    # Determine implemented feature
    implemented_feature = _get_implemented_feature(
        initial_feature_list, final_feature_list
    )

    # Get git diff
    git_diff = _get_git_diff(workspace_dir)

    # Run graders
    todolist_grader = TodoListGrader()
    todolist_result = todolist_grader.grade(final_state)

    single_feature_grader = SingleFeatureGrader()
    single_feature_result = single_feature_grader.grade(
        initial_feature_list, final_feature_list
    )

    session_lifecycle_grader = SessionLifecycleGrader()
    session_lifecycle_result = session_lifecycle_grader.grade(
        messages, workspace_dir
    )

    code_quality_grader = CodeQualityGrader()
    code_quality_result = code_quality_grader.grade(
        git_diff, implemented_feature
    )

    struggle_grader = StruggleGrader()
    struggle_result = struggle_grader.grade(messages)

    # Calculate overall score (weighted)
    overall_score = (
        single_feature_result.score * 0.30
        + code_quality_result.score * 0.25
        + session_lifecycle_result.score * 0.20
        + todolist_result.score * 0.15
        + struggle_result.score * 0.10
    )

    # Pass criteria: overall >= 0.7 AND critical graders pass
    passed = (
        overall_score >= 0.7
        and single_feature_result.passed
        and todolist_result.passed
    )

    return EvalReport(
        test_case_name=test_name,
        passed=passed,
        overall_score=overall_score,
        todolist_result=todolist_result,
        single_feature_result=single_feature_result,
        session_lifecycle_result=session_lifecycle_result,
        code_quality_result=code_quality_result,
        struggle_result=struggle_result,
        workspace_path=str(workspace_dir),
        implemented_feature=implemented_feature,
    )


def _setup_workspace(test_case: dict[str, Any], workspace_dir: Path) -> None:
    """Verify workspace has required files.

    The eval uses existing files from ./workspace:
    - feature_list.json
    - progress.md
    - init.sh

    These should be created by the initializer agent or manually.
    """
    # Verify required files exist
    required_files = ["feature_list.json", "init.sh"]
    for filename in required_files:
        filepath = workspace_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(
                f"Required file '{filename}' not found in {workspace_dir}. "
                f"Run the initializer agent first or create it manually."
            )


def _load_feature_list(workspace_dir: Path = None) -> list[dict[str, Any]]:
    """Load feature_list.json from the default workspace (./workspace).

    The agent uses the feature_list.json from ./workspace, not the eval workspace.
    """
    # Always read from ./workspace (the default workspace)
    default_workspace = Path("./workspace")
    feature_list_path = default_workspace / "feature_list.json"
    if not feature_list_path.exists():
        return []
    with open(feature_list_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_implemented_feature(
    initial: list[dict[str, Any]],
    final: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """Find the feature that changed from passes=false to passes=true."""
    initial_map = {f["id"]: f for f in initial}

    for feature in final:
        feature_id = feature["id"]
        initial_feature = initial_map.get(feature_id)

        if initial_feature is None:
            continue

        initial_passes = initial_feature.get("passes", False)
        final_passes = feature.get("passes", False)

        if not initial_passes and final_passes:
            return feature

    return None


def _get_git_diff(workspace_dir: Path) -> str:
    """Get git diff for code changes."""
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD"],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout
        # If no previous commit, diff against empty
        result = subprocess.run(
            ["git", "diff", "--cached"],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except Exception:
        return ""


class EvalTimeoutError(Exception):
    """Raised when agent execution times out."""
    pass


class EvalInterruptError(Exception):
    """Raised when agent hits an interrupt (ASK permission) during eval."""
    pass


def _run_agent(
    test_case: dict[str, Any],
    workspace_dir: Path,
) -> tuple[list[BaseMessage], dict[str, Any]]:
    """
    Run the coding agent and return messages + final state.

    Args:
        test_case: Test case configuration
        workspace_dir: Workspace directory

    Returns:
        Tuple of (messages, final_state)

    Raises:
        EvalInterruptError: If agent hits an interrupt
        EvalTimeoutError: If agent times out
    """
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.errors import GraphInterrupt
    from langchain.agents import create_agent

    from ax_advanced_class.src.llm.bedrock_client import BedrockClient
    from ax_advanced_class.src.agents.agent_factory import DefaultAgentState
    from ax_advanced_class.src.tools import BashTool, FileOperationTool, TodoWriteTool
    from ax_advanced_class.src.prompts import coding_agent_dynamic_prompt
    from ax_advanced_class.evals.coding.eval_middleware import EvalToolValidationMiddleware

    # Ensure workspace exists
    workspace_dir = Path(workspace_dir).resolve()
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Create tools
    tools = []
    tools.extend(BashTool().get_langchain_tools())
    tools.extend(FileOperationTool().get_langchain_tools())
    tools.extend(TodoWriteTool().get_langchain_tools())

    # Create minimal middleware for eval (only blocks dangerous commands, no ASK)
    eval_middleware = EvalToolValidationMiddleware()

    # Create coding agent with eval middleware
    llm = BedrockClient().get_core()

    agent = create_agent(
        model=llm,
        tools=tools,
        middleware=[eval_middleware, coding_agent_dynamic_prompt],
        name="coding_agent",
        state_schema=DefaultAgentState,
        checkpointer=MemorySaver(),
    )
    agent = agent.with_config({"recursion_limit": 500})

    # Build prompt
    thread_id = f"eval_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    prompt = "Start your coding session. Follow the session lifecycle (START, WORK, END phases)."

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=prompt)], "todo_list": []},
            config=config,
        )
    except GraphInterrupt as e:
        interrupt_data = e.args[0] if e.args else "Unknown"
        raise EvalInterruptError(
            f"Agent hit ASK permission (interrupt). "
            f"This should not happen in eval - check middleware config. "
            f"Interrupt data: {interrupt_data}"
        ) from e

    return result["messages"], result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run coding agent evals")
    parser.add_argument(
        "--test-case",
        type=Path,
        help="Path to test case JSON file",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Workspace directory for agent output",
    )
    parser.add_argument(
        "--skip-agent",
        action="store_true",
        help="Skip agent invocation (grade existing workspace)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to write JSON report",
    )

    args = parser.parse_args()

    if args.test_case:
        test_case = load_test_case(args.test_case)
    else:
        # Default minimal test case
        test_case = {
            "name": "default",
            "setup": {
                "feature_list": [],
                "progress_md": "# Progress\n",
                "init_sh": "#!/bin/bash\necho 'Ready'\n",
            }
        }

    report = run_eval(
        test_case=test_case,
        workspace_dir=args.workspace,
        skip_agent=args.skip_agent,
    )

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
