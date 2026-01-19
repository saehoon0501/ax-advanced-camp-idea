"""
Prompts Module

Contains all system prompts for the orchestrator and agents.
"""

from ax_advanced_class.src.prompts.base_prompt import BasePrompt
from ax_advanced_class.src.prompts.initializer_prompt import (
    INITIALIZER_SYSTEM_PROMPT,
    initializer_prompt,
    initializer_agent_dynamic_prompt,
)
from ax_advanced_class.src.prompts.coding_agent_prompt import (
    CODING_AGENT_SYSTEM_PROMPT,
    coding_agent_dynamic_prompt,
    coding_agent_prompt,
)
from ax_advanced_class.src.prompts.orchestrator_prompt import orchestrator_prompt

__all__ = [
    # Base
    "BasePrompt",
    # Legacy BasePrompt instances
    "initializer_prompt",
    "coding_agent_prompt",
    "orchestrator_prompt",
]
