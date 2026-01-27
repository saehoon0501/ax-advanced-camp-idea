# Coding Agent Eval Design

## Overview

This document outlines the evaluation system for the Coding Agent based on:
- Anthropic's "Demystifying Evals for AI Agents" article
- The coding agent prompt and expected behaviors
- Scenarios 6 (State Recovery), 7 (Incremental Work), 8 (Session Task Planner)

## Eval Philosophy

Following Anthropic's guidance:
- **Code-based graders**: Fast, cheap, objective, reproducible - use for deterministic checks
- **Model-based graders**: Flexible, nuanced - use for quality/subjective assessments
- **Balance**: Test both positive behaviors (does the right thing) and negative behaviors (avoids wrong things)

## Test Case Structure

```json
{
  "name": "test_single_feature_implementation",
  "description": "Agent should implement exactly one feature from the list",
  "setup": {
    "feature_list": [...],
    "progress_md": "...",
    "init_files": {...}
  },
  "target_feature": "feature-003",
  "expected": {
    "feature_completed": true,
    "other_features_unchanged": true,
    "commit_created": true
  }
}
```

---

## Graders

### 1. TodoListGrader (Code-based)

**Purpose**: Validate that the agent's final todo_list state is correct.

**What it checks**:
| Check | Type | Description |
|-------|------|-------------|
| Todos exist | Required | Agent created todos (list not empty) |
| All completed | Required | All todos have `status: completed` |
| No pending | Required | No todos left in `pending` state |
| No in_progress | Required | No todos stuck in `in_progress` state |

**Scoring**:
- 1.0: All todos completed
- 0.7: Most todos completed, some in_progress (session may have timed out)
- 0.3: Most todos still pending
- 0.0: No todos created at all

**Implementation approach**:
```python
class TodoListGrader:
    def grade(self, final_state: dict) -> TodoListGradeResult:
        todo_list = final_state.get("todo_list", [])
        # Check todos exist
        # Count by status: pending, in_progress, completed
        # Score based on completion ratio
```

---

### 2. SingleFeatureGrader (Code-based)

**Purpose**: Verify the agent implemented exactly ONE feature (no scope creep).

**What it checks**:
| Check | Type | Description |
|-------|------|-------------|
| Feature selected | Required | Agent chose a valid `passes=false` feature |
| Only one feature | Required | feature_list.json shows exactly ONE feature changed to `passes=true` |
| Priority respected | Warning | High priority features selected before low |
| Dependencies satisfied | Required | Selected feature's dependencies all `passes=true` |

**Scoring**:
- 1.0: Exactly one feature completed, correct priority
- 0.7: One feature completed, but priority not optimal
- 0.3: Multiple features touched (scope creep)
- 0.0: No feature completed or wrong feature selected

**Implementation approach**:
```python
class SingleFeatureGrader:
    def grade(
        self,
        initial_feature_list: list[dict],
        final_feature_list: list[dict]
    ) -> SingleFeatureGradeResult:
        # Diff the two feature lists
        # Count features changed from passes=false to passes=true
        # Verify exactly one changed
```

---

### 3. SessionLifecycleGrader (Code-based)

**Purpose**: Validate the agent followed the 3-phase session lifecycle and used todo list as intended.

**What it checks**:

**PHASE 1 - START**:
| Check | Type | Description |
|-------|------|-------------|
| `pwd` executed | Required | Agent checked working directory |
| `init.sh` executed | Required | Agent ran recovery script |
| Context read | Required | Read progress.md and feature_list.json |
| Smoke test | Warning | Basic test run before starting work |

**PHASE 2 - WORK**:
| Check | Type | Description |
|-------|------|-------------|
| Feature focused | Required | Work relates to selected feature |
| Tests written | Warning | Tests created/run for the feature |
| Todo usage | Required | Created todos and updated status during work |

**PHASE 3 - END**:
| Check | Type | Description |
|-------|------|-------------|
| Git commit | Required | Changes committed with proper message format |
| progress.md updated | Required | Session notes appended |
| feature_list updated | Required | Feature marked `passes=true` |
| Clean state | Warning | No uncommitted changes remain |

**Todo Usage Evaluation** (part of PHASE 2):
| Check | Type | Description |
|-------|------|-------------|
| Todos created early | Required | Todo list created before implementation starts |
| Status updates | Required | `in_progress` marked before work, `completed` after |
| Single in_progress | Warning | Only one todo `in_progress` at a time |
| No batch updates | Warning | Status updated incrementally, not all at once at end |

**Scoring**:
- Each phase: 0.33 weight
- Within phase: Required checks must pass, warnings are bonus

**Implementation approach**:
```python
class SessionLifecycleGrader:
    def grade(self, messages: list[BaseMessage], workspace: Path) -> SessionLifecycleGradeResult:
        # Parse messages for tool calls (ToolMessage)
        # Check PHASE 1: Look for pwd, init.sh, file reads
        # Check PHASE 2: Verify work + todo usage patterns
        # Check PHASE 3: Verify git commit, file updates
```

---

### 4. StruggleGrader (LLM-based)

**Purpose**: Assess how smoothly the agent completed the task (debugging efficiency).

**Rubric**:
```
Analyze the agent's work transcript and score on these criteria:

## EFFICIENCY
- 1.0: Direct path to solution, minimal backtracking
- 0.5: Some trial-and-error but reasonable
- 0.0: Excessive debugging loops, repeated failures

## RECOVERY
- 1.0: When errors occurred, recovered quickly and correctly
- 0.5: Recovered but with some wasted effort
- 0.0: Got stuck, made things worse, or gave up

## FOCUS
- 1.0: Stayed on task, no tangents
- 0.5: Minor distractions but completed task
- 0.0: Significant tangents, scope creep attempts

## COMPLETION
- 1.0: Task fully completed with verification
- 0.5: Task mostly done, minor issues remain
- 0.0: Task incomplete or broken state left
```

**Implementation approach**:
```python
class StruggleGrader:
    def grade(self, transcript: list[Message]) -> StruggleGradeResult:
        # Send summarized transcript to LLM
        # Get ERFC scores
        # Calculate struggle index (inverse of average)
```

---

## Eval Runner Structure

```
ax_advanced_class/evals/coding/
├── __init__.py
├── run_eval.py              # Main eval runner
├── eval_permission_config.py # PermissionConfig for eval environment
├── graders/
│   ├── __init__.py
│   ├── todolist_grader.py       # Code-based
│   ├── single_feature_grader.py # Code-based
│   ├── session_lifecycle_grader.py  # Code-based
│   └── struggle_grader.py       # LLM-based
└── test_cases/
    ├── simple_feature.json
    ├── feature_with_dependencies.json
    └── broken_state_recovery.json
```

---

## Permission Config

Following the pattern from `ax_advanced_class/evals/initializer/eval_permission_config.py`:

```python
# ax_advanced_class/evals/coding/eval_permission_config.py
"""
PermissionConfig for coding agent evals.

Design principles:
- File operations within workspace: ALLOW
- Git operations: ALLOW (coding agent needs git for commits)
- No ASK permissions (would cause eval to hang)
- 10 minute timeout
"""

from ax_advanced_class.src.config.tool_permission_config import PermissionConfig


def create_eval_permission_config(workspace_root: str) -> PermissionConfig:
    """
    Create a PermissionConfig for coding agent eval.

    Key differences from initializer eval:
    - Git commands ALLOWED (coding agent needs to commit)
    - Timeout set to 10 minutes

    Args:
        workspace_root: Absolute path to the eval workspace directory

    Returns:
        PermissionConfig configured for coding agent eval
    """
    default_blocked = {
        "cd",
        "mkfs", "fdisk", "dd", "mount", "umount",
        "shutdown", "reboot", "init", "systemctl", "service",
        "sudo", "su",
    }

    return PermissionConfig(
        workspace_root=workspace_root,
        blocked_commands=frozenset(default_blocked),
    )
```

---

## Graders Module

```python
# ax_advanced_class/evals/coding/graders/__init__.py
"""
Graders for coding agent evals.
"""

from ax_advanced_class.evals.coding.graders.todolist_grader import TodoListGrader
from ax_advanced_class.evals.coding.graders.single_feature_grader import SingleFeatureGrader
from ax_advanced_class.evals.coding.graders.session_lifecycle_grader import SessionLifecycleGrader
from ax_advanced_class.evals.coding.graders.struggle_grader import StruggleGrader

__all__ = [
    "TodoListGrader",
    "SingleFeatureGrader",
    "SessionLifecycleGrader",
    "StruggleGrader",
]
```

---

## Run Eval (Following Initializer Pattern)

```python
# ax_advanced_class/evals/coding/run_eval.py
"""
Eval runner for coding agent.

Invokes the coding agent with a test case, then runs graders
to validate the output.
"""

from ax_advanced_class.src.utils.env_loader import load_dotenv
load_dotenv()

import truststore
truststore.inject_into_ssl()

import json
import tempfile
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent

from ax_advanced_class.src.llm.bedrock_client import BedrockClient
from ax_advanced_class.src.agents import coding_agent_spec
from ax_advanced_class.evals.coding.eval_permission_config import create_eval_permission_config
from ax_advanced_class.evals.coding.graders import (
    TodoListGrader,
    SingleFeatureGrader,
    SessionLifecycleGrader,
    StruggleGrader,
)


TIMEOUT_SECONDS = 600  # 10 minutes


@dataclass
class EvalReport:
    """Complete eval report for a coding agent run."""

    test_case_name: str
    passed: bool
    overall_score: float  # 0.0-1.0

    # Individual grader results
    todolist_result: Optional[dict] = None
    single_feature_result: Optional[dict] = None
    session_lifecycle_result: Optional[dict] = None
    struggle_result: Optional[dict] = None

    # Execution details
    agent_error: Optional[str] = None
    workspace_path: Optional[str] = None
    implemented_feature: Optional[dict] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_eval(
    test_case: dict[str, Any],
    workspace_dir: Optional[Path] = None,
) -> EvalReport:
    """
    Run eval for a coding agent test case.

    Args:
        test_case: Test case dict with setup files and expected behavior
        workspace_dir: Directory to use for agent output

    Returns:
        EvalReport with all grader results
    """
    test_name = test_case.get("name", "unknown")

    # Setup workspace
    if workspace_dir is None:
        workspace_dir = Path(tempfile.mkdtemp(prefix="coding_eval_"))
    workspace_dir = Path(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Setup workspace files from test case
    _setup_workspace(test_case, workspace_dir)

    # Capture initial feature_list
    initial_feature_list = _load_feature_list(workspace_dir)

    # Run agent
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

    struggle_grader = StruggleGrader()
    struggle_result = struggle_grader.grade(messages)

    # Calculate overall score (re-normalized)
    remaining_weight = 0.30 + 0.20 + 0.15 + 0.10
    overall_score = (
        single_feature_result.score * 0.30
        + session_lifecycle_result.score * 0.20
        + todolist_result.score * 0.15
        + struggle_result.score * 0.10
    ) / remaining_weight

    passed = (
        overall_score >= 0.7
        and single_feature_result.passed
        and todolist_result.passed
    )

    return EvalReport(
        test_case_name=test_name,
        passed=passed,
        overall_score=overall_score,
        todolist_result=asdict(todolist_result),
        single_feature_result=asdict(single_feature_result),
        session_lifecycle_result=asdict(session_lifecycle_result),
        struggle_result=asdict(struggle_result),
        workspace_path=str(workspace_dir),
        implemented_feature=implemented_feature,
    )


def _run_agent(
    test_case: dict[str, Any],
    workspace_dir: Path
) -> tuple[list[BaseMessage], dict]:
    """Run the coding agent and return messages + final state."""
    permission_config = create_eval_permission_config(str(workspace_dir))

    llm = BedrockClient().get_core()
    spec = coding_agent_spec(config=permission_config)

    agent = create_agent(
        model=llm,
        tools=list(spec.tools),
        middleware=list(spec.middleware),
        name=spec.name,
        state_schema=spec.state_schema,
        checkpointer=MemorySaver(),
    )
    agent = agent.with_config({"recursion_limit": 500})

    thread_id = f"eval_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    # Start session prompt
    prompt = "Start your coding session. Follow the session lifecycle."

    result = agent.invoke(
        {"messages": [HumanMessage(content=prompt)], "todo_list": []},
        config=config,
    )

    return result["messages"], result
```

---

## Score Weights

| Grader | Weight | Rationale |
|--------|--------|-----------|
| SingleFeatureGrader | 40% | Most critical: no scope creep |
| SessionLifecycleGrader | 26.7% | Proper workflow adherence |
| TodoListGrader | 20% | Core behavior for tracking |
| StruggleGrader | 13.3% | Efficiency assessment |

**Pass criteria**: Overall score >= 0.7 AND all required checks pass

---

## Test Case Categories

### 1. Happy Path Tests
- `simple_feature.json`: Straightforward feature, no dependencies
- `feature_with_tests.json`: Feature that requires writing tests

### 2. Dependency Tests
- `feature_with_dependencies.json`: Feature that requires completed dependencies
- `blocked_by_dependencies.json`: All available features are blocked

### 3. Recovery Tests
- `broken_state_recovery.json`: App starts in broken state, must fix first
- `incomplete_previous_session.json`: Previous session left work uncommitted

### 4. Edge Cases
- `all_features_complete.json`: No features left to implement
- `conflicting_progress.json`: progress.md and feature_list.json disagree

---

## Eval Data Capture

Data captured from `agent.invoke()` result:

```python
@dataclass
class CodingEvalData:
    # From agent.invoke() result
    messages: list[BaseMessage]      # Full conversation (includes ToolMessages)
    final_state: dict                # Final agent state (includes todo_list)

    # From workspace (before/after)
    initial_feature_list: list[dict] # feature_list.json before agent run
    final_feature_list: list[dict]   # feature_list.json after agent run

    # Derived
    implemented_feature: dict | None # The feature that changed to passes=true
```

**Grader inputs**:
| Grader | Inputs |
|--------|--------|
| TodoListGrader | `final_state` |
| SingleFeatureGrader | `initial_feature_list`, `final_feature_list` |
| SessionLifecycleGrader | `messages`, workspace path |
| StruggleGrader | `messages` |

---

## Implementation Priority

1. **Phase 1 - Core graders** (MVP)
   - SingleFeatureGrader (most critical check)
   - SessionLifecycleGrader (workflow compliance)

2. **Phase 2 - Behavior graders**
   - TodoListGrader (todo management)

3. **Phase 3 - Polish**
   - StruggleGrader (efficiency)
   - Additional test cases

---

## Design Decisions

| Question | Decision |
|----------|----------|
| **Transcript format** | Use LangChain's `BaseMessage` list directly from `agent.invoke()` result |
| **Todo list access** | Extract from `ToolMessage` results + final agent state's `todo_list` field |
| **Workspace setup** | Minimal scaffold: `feature_list.json`, `progress.md`, `init.sh` |
| **Feature implementation** | Agent creates files from scratch, OR modifies existing code (if previous features implemented) |
| **Timeout** | 10 minutes time limit |

---

## Workspace Scaffold

Each eval run creates a minimal workspace with:

```
workspace/
├── feature_list.json    # Features to implement (some may be passes=true)
├── progress.md          # Session history from previous agents
├── init.sh              # Recovery script
└── src/                 # (Optional) Existing code from previous features
    └── ...
```

The agent will:
1. Read these files during PHASE 1 (START)
2. Create/modify code files during PHASE 2 (WORK)
3. Update feature_list.json and progress.md during PHASE 3 (END)
