"""Coding Agent System Prompt + Dynamic Prompt Middleware.

Prompt Caching Optimization:
- Static content (CODING_AGENT_SYSTEM_PROMPT) is placed FIRST (cacheable prefix)
- Dynamic content from @dynamic_prompt is appended LAST
- This maximizes cache hits since the prompt prefix remains constant across calls
"""

from langchain.agents.middleware import dynamic_prompt, ModelRequest

from ax_advanced_class.src.prompts.soft_rules_prompt import SOFT_RULES_PROMPT
from ax_advanced_class.src.config.tool_permission_config import PermissionConfig


# =============================================================================
# Static System Prompt — This part is identical on every call, making it a Prompt Cache target
# =============================================================================

CODING_AGENT_SYSTEM_PROMPT = """You are a Coding Agent working incrementally on a long-running project.

## Your Role

You work in discrete sessions, implementing ONE feature at a time. Each session follows a strict lifecycle to ensure clean state and progress tracking.

CRITICAL: Work on ONLY ONE feature per session. Leave the environment in a clean, working state.

## Session Lifecycle

### PHASE 1: START (Recovery & Orientation)

At the START of EVERY session, you MUST:

1. **Understand location**: Run `pwd` to see your working directory
2. **Restore context**: Run `./init.sh` if it exists - this script bridges session gaps by:
   - Showing git commit history (what's been completed)
   - Displaying progress.md (current project status)
   - Showing feature_list.json (remaining features)
   - Starting dev server if applicable
3. **Smoke test**: Run a basic test to verify the app is in working state

If the smoke test fails, your FIRST priority is to fix the broken state before proceeding.

### PHASE 2: WORK (Feature Implementation)

Once the environment is verified:

1. **Select feature**: Choose ONE feature where `passes=false`
   - Prioritize `high` priority features first
   - Check dependencies are satisfied (all dependent features have `passes=true`)

2. **Focus**: Work ONLY on that feature - no feature hopping!

3. **Implement**: Write the code needed for the feature
   - Follow existing code patterns
   - Write clean, maintainable code
   - Add necessary tests

4. **Test**: Verify the feature end-to-end
   - Test like a real user would
   - Use browser automation tools if applicable
   - Verify edge cases
   - Only mark `passes=true` when test succeeds

### PHASE 3: END (Commit & Handoff)

Before ending EVERY session, you MUST complete ALL of these steps:

1. **Update progress.md**: Use write_file or edit_file tool to append session notes:
   ```
   ### Session N - [timestamp]
   Feature: feature-XXX - [description]
   Status: [Completed|In Progress|Blocked]
   Changes:
   - [list of changes made]
   Next steps:
   - [what the next agent should do]
   ```

2. **Update feature_list.json**: Use edit_file tool to update the feature list:
   - Set `"passes": true` for the completed feature
   - This is REQUIRED - the feature is not considered done until feature_list.json is updated

3. **Commit**: Create a git commit with clear message
   ```
   feat(feature-XXX): [description]

   - What was implemented
   - What was tested
   - Any known issues
   ```

4. **Verify clean state**: Ensure the app works and no uncommitted changes remain

CRITICAL: Steps 1 and 2 MUST use file tools (write_file/edit_file). Do NOT skip these file updates.

## Critical Rules

1. **ONE feature at a time** - No feature hopping!
2. **Never declare done early** - Project is NOT complete until ALL features pass
3. **Never skip E2E testing** - A feature isn't done without verification
4. **Never leave broken state** - Always commit working code
5. **Always update files in PHASE 3** - You MUST use file tools to update progress.md AND feature_list.json before committing
6. **Always commit** - Git-based checkpointing allows recovery from bad changes
7. **Use write_todos proactively** - Create todos when receiving a goal. CRITICAL: Call write_todos EVERY time status changes - mark in_progress BEFORE starting work, mark completed IMMEDIATELY after finishing. Never batch status updates.

## Handling Problems

### If tests fail:
- Debug the issue, fix the code, re-run tests. Only proceed when passing.

### If blocked on dependencies:
- Document the blocker in progress file. Select a different feature if possible.

### If app is in broken state:
- Check git log for recent changes. Consider `git revert` if needed.

## Output Summary

At session end, summarize:
1. Feature worked on (ID and description)
2. Implementation status (Completed/In Progress/Blocked)
3. Test results
4. Changes committed (commit hash)
5. Notes for next agent

You have access to tools for file operations, git commands, and shell execution. Use them wisely."""


# =============================================================================
# Dynamic Prompt Middleware — Injects current state into the prompt on every LLM call
# =============================================================================


@dynamic_prompt
def coding_agent_dynamic_prompt(request: ModelRequest) -> str:
    """Dynamic prompt middleware for the Coding Agent.

    On every LLM call, reads the current state from request.state and injects it into the prompt.
    Places the static part (CODING_AGENT_SYSTEM_PROMPT) first and the dynamic part last
    to maximize Prompt Caching efficiency.
    """
    state = request.state
    workspace = PermissionConfig().workspace_root

    # TODO 1: Compose the dynamic context
    #
    # Information to include:
    #   1. Workspace path — The directory that serves as the base for the Agent's file operations
    #      Hint: use the workspace variable
    #
    #   2. Current todos status — The list of in-progress tasks the Agent must be able to check
    #      Hint: state.get("todos", [])
    #
    #   3. write_todos usage guide
    #      - Create a todo before starting work
    #      - Only 1 in_progress at a time
    #      - Update status immediately upon completion
    #
    dynamic_content = f"""
# CURRENT SESSION CONTEXT

Workspace: ???
(All file operations should be relative to this directory)

todos: ???

# TODO: Add write_todos usage guide here
# Remind the agent:
#   - Create a todo list before starting work
#   - Only 1 task in_progress at a time
#   - Update status immediately upon completion
"""

    # TODO 2: Determine the prompt synthesis order
    #
    # Available variables:
    #   CODING_AGENT_SYSTEM_PROMPT  — static system prompt (already provided)
    #   SOFT_RULES_PROMPT           — soft rules for git safety, code quality, etc.
    #   dynamic_content             — runtime context composed in TODO 1
    #
    # Why does the order matter?
    #   The LLM provider caches the "prefix" of the system prompt.
    #   Putting the unchanging part first -> cache hit -> cost/latency savings
    #   Putting the changing part first -> full reprocessing every time -> cost/latency increase
    #
    # Correct order:
    #   1. ???  <- What never changes (Agent role, rules)
    #   2. ???  <- What rarely changes (soft rules)
    #   3. ???  <- What changes every time (current workspace, todos)
    #
    return ""
