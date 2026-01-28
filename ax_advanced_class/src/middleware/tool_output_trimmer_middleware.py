"""
Tool Output Trimmer Middleware

Compresses verbose tool outputs to save context tokens.
Uses schema-based extraction to keep only essential information.

Example:
    Input: 5KB JSON from weather API with 200+ fields
    Output: "Temperature: 25C @ Seoul (2025-01-28T10:00:00Z)" (~50 chars)
"""

from typing import Callable, Any

from langchain_core.messages import ToolMessage
from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command


class ToolOutputTrimmerMiddleware(AgentMiddleware):
    """
    Middleware that compresses tool outputs to save context tokens.

    Applies schema-based extraction to reduce verbose tool outputs
    while preserving essential information for the agent.

    Features:
    - Schema-driven field extraction
    - Configurable output length limits
    - Tool-specific compression strategies
    """

    def __init__(self, max_output_length: int = 500):
        """
        Initialize the middleware.

        Args:
            max_output_length: Maximum length of compressed output (default: 500 chars)
        """
        self.max_output_length = max_output_length

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """
        Intercepts tool outputs and compresses them.

        TODO: Implement compression logic:
        1. Execute the tool via handler
        2. Parse the tool output
        3. Apply schema-based extraction (keep only essential fields)
        4. Return compressed output
        """
        # Execute the tool
        result = handler(request)

        # TODO: Implement compression
        # - Detect output type (JSON, text, error)
        # - Apply appropriate compression strategy
        # - Ensure output stays within max_output_length

        return result

    def _compress_json_output(self, output: str, tool_name: str) -> str:
        """
        Compress JSON output using schema-based extraction.

        TODO: Implement JSON compression:
        - Parse JSON
        - Extract fields based on tool-specific schema
        - Format as concise string
        """
        return output

    def _compress_text_output(self, output: str) -> str:
        """
        Compress plain text output.

        TODO: Implement text compression:
        - Truncate with ellipsis if too long
        - Preserve first and last lines for context
        """
        return output
