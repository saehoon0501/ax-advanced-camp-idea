"""
Coding Agent System Prompt

Based on Anthropic's "Building effective harnesses for long-running agents" article.
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

The Coding Agent works incrementally on the project, one feature at a time.
Key insight: "Structure prompts to work on single features within each context
window, leaving the environment in a clean state."

Prompt Caching Optimization:
- Static content is placed FIRST (cacheable prefix)
- Dynamic content from @dynamic_prompt is appended LAST
- This maximizes cache hits since the prompt prefix remains constant across calls
"""

from langchain.agents.middleware import dynamic_prompt, ModelRequest


CODING_AGENT_SYSTEM_PROMPT = """You are a Coding Agent working incrementally on a long-running project.

## Your Role

You work in discrete sessions, implementing ONE feature at a time. Each session follows a strict lifecycle to ensure clean state and progress tracking.

CRITICAL: Work on ONLY ONE feature per session. Leave the environment in a clean, working state.

## Session Lifecycle

## Output Summary
"""


# =============================================================================
# Dynamic Prompt Middleware
# =============================================================================
#
# Uses LangChain's @dynamic_prompt decorator for context-aware prompt generation.
#
# Prompt Caching Optimization:
# - Static content (CODING_AGENT_SYSTEM_PROMPT) is placed FIRST so it can be cached
# - Dynamic content (feature info, session info) is appended LAST via middleware
# - This maximizes cache hits since the prompt prefix remains constant across calls
#
# Runtime Context Keys (set via agent.invoke config):
# - feature_id: str
# - feature_description: str
# - feature_category: str
# - feature_priority: str
# - feature_steps: list[str]
# - feature_dependencies: list[str]
# - session_number: int
# - repository_path: str


from ax_advanced_class.src.prompts.soft_rules_prompt import (
    SOFT_RULES_PROMPT,
)
from ax_advanced_class.src.config.tool_permission_config import PermissionConfig


@dynamic_prompt
def coding_agent_dynamic_prompt(request: ModelRequest) -> str:
    """
    Dynamic prompt middleware for the Coding Agent.

    This middleware appends session-specific context to the static system prompt.
    The static prompt is cached, while dynamic context varies per invocation.

    Args:
        request: ModelRequest containing runtime context with feature/session info

    Returns:
        Complete prompt string with static content first, dynamic content last
    """
    # Extract dynamic context from runtime (set via invoke config)
    state = request.state

    # Build the dynamic portion (placed at the END for cache optimization)
    workspace = PermissionConfig().workspace_root
    dynamic_content = f"""

=== CURRENT SESSION CONTEXT ===

Workspace: {workspace}
(All file operations should be relative to this directory)

"""

    # Return: static system prompt (cacheable) + soft rules + dynamic content (at the end)
    return CODING_AGENT_SYSTEM_PROMPT + SOFT_RULES_PROMPT + dynamic_content
