"""
Prompts Module

Contains all system prompts for the orchestrator and agents.
"""

from ax_advanced_class.src.prompts.base_prompt import BasePrompt
from ax_advanced_class.src.prompts.initializer_prompt import (
    INITIALIZER_SYSTEM_PROMPT,
    initializer_prompt,
)
from ax_advanced_class.src.prompts.coding_agent_prompt import (
    CODING_AGENT_SYSTEM_PROMPT,
    coding_agent_prompt,
)
from ax_advanced_class.src.prompts.orchestrator_prompt import orchestrator_prompt
from ax_advanced_class.src.prompts.curriculum_planner_prompt import curriculum_planner_prompt
from ax_advanced_class.src.prompts.progress_assessment_prompt import progress_assessment_prompt

__all__ = [
    # Base
    "BasePrompt",
    # New system prompts (string constants)
    "INITIALIZER_SYSTEM_PROMPT",
    "CODING_AGENT_SYSTEM_PROMPT",
    # Legacy BasePrompt instances
    "initializer_prompt",
    "coding_agent_prompt",
    "orchestrator_prompt",
    "curriculum_planner_prompt",
    "progress_assessment_prompt",
]
