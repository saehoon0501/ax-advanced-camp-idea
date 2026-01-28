"""
Initializer Agent System Prompt

Based on Anthropic's "Building effective harnesses for long-running agents" article.
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

The Initializer Agent sets up the foundation for a long-running project.
Key insight: "Use structured JSON files (over Markdown) containing 10-20
granular features marked as passing/failing."

Prompt Caching Optimization:
- Static content is placed FIRST (cacheable prefix)
- Dynamic content from @dynamic_prompt is appended LAST
- This maximizes cache hits since the prompt prefix remains constant across calls
"""

from langchain.agents.middleware import dynamic_prompt, ModelRequest


INITIALIZER_SYSTEM_PROMPT = """You are an Initializer Agent responsible for setting up the foundation for a long-running coding project.

## Your Role

You are the FIRST agent to work on a new project. Your job is to analyze the user's request and create a solid foundation that future Coding Agents will build upon incrementally.

CRITICAL: You do NOT implement features. You ONLY set up the project foundation.

## Core Responsibilities

### 1. Feature List Generation (MOST IMPORTANT)

### 2. Progress Tracking Setup

### 3. Init Script - Session Continuity Bridge

## Output Summary
"""


# =============================================================================
# Dynamic Prompt Middleware
# =============================================================================
#
# Uses LangChain's @dynamic_prompt decorator for context-aware prompt generation.
#
# Runtime Context Keys (set via agent.invoke config):
# - project_name: str
# - project_description: str
# - repository_path: str


from ax_advanced_class.src.prompts.soft_rules_prompt import (
    SOFT_RULES_PROMPT,
)
from ax_advanced_class.src.config.tool_permission_config import PermissionConfig


@dynamic_prompt
def initializer_agent_dynamic_prompt(request: ModelRequest) -> str:
    """
    Dynamic prompt middleware for the Initializer Agent.

    This middleware appends project-specific context to the static system prompt.
    The static prompt is cached, while dynamic context varies per invocation.

    Args:
        request: ModelRequest containing runtime context with project info

    Returns:
        Complete prompt string with static content first, dynamic content last
    """
    # Build the dynamic portion (placed at the END for cache optimization)
    workspace = PermissionConfig().workspace_root
    dynamic_content = f"""

=== PROJECT CONTEXT ===

Workspace: {workspace}
(All file operations should be relative to this directory)


Remember: Your job is ONLY setup - do not implement features!"""

    # Return: static system prompt (cacheable) + soft rules + dynamic content (at the end)
    return INITIALIZER_SYSTEM_PROMPT + SOFT_RULES_PROMPT + dynamic_content
