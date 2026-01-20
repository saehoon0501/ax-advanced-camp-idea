"""
Prompts Module

Contains all system prompts for the orchestrator and agents.
"""

from ax_advanced_class.src.prompts.initializer_prompt import (
    INITIALIZER_SYSTEM_PROMPT,
    initializer_agent_dynamic_prompt,
)
from ax_advanced_class.src.prompts.coding_agent_prompt import (
    CODING_AGENT_SYSTEM_PROMPT,
    coding_agent_dynamic_prompt,
)
from ax_advanced_class.src.prompts.orchestrator_prompt import (
    ORCHESTRATOR_SYSTEM_PROMPT,
)
from ax_advanced_class.src.prompts.soft_rules_prompt import (
    SOFT_RULES_PROMPT,
    TOOL_SELECTION_RULES,
    WORKING_DIRECTORY_RULES,
    GIT_SAFETY_RULES,
    PR_CREATION_RULES,
    FILE_OPERATION_RULES,
    COMMAND_EXECUTION_RULES,
    TASK_TOOL_RULES,
    TODO_TRACKING_RULES,
    CODE_QUALITY_RULES,
    TONE_AND_STYLE_RULES,
    SECURITY_GUIDELINES,
    EXECUTION_PATTERNS_RULES,
)

__all__ = [
    # System Prompts
    "INITIALIZER_SYSTEM_PROMPT",
    "CODING_AGENT_SYSTEM_PROMPT",
    "ORCHESTRATOR_SYSTEM_PROMPT",
    # Dynamic Prompt Middleware
    "initializer_agent_dynamic_prompt",
    "coding_agent_dynamic_prompt",
    # Soft Rules Prompts
    "SOFT_RULES_PROMPT",
    "TOOL_SELECTION_RULES",
    "WORKING_DIRECTORY_RULES",
    "GIT_SAFETY_RULES",
    "PR_CREATION_RULES",
    "FILE_OPERATION_RULES",
    "COMMAND_EXECUTION_RULES",
    "TASK_TOOL_RULES",
    "TODO_TRACKING_RULES",
    "CODE_QUALITY_RULES",
    "TONE_AND_STYLE_RULES",
    "SECURITY_GUIDELINES",
    "EXECUTION_PATTERNS_RULES",
]
