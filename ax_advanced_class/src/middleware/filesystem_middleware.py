"""Middleware for providing filesystem tools to an agent.

This file contains 3 TODOs:
  TODO 1: _get_edit_file_description() - Write the edit_file tool description
  TODO 2: wrap_model_call()            - System prompt injection + tool filtering
  TODO 3: wrap_tool_call()             - Replace large Tool results with files (eviction)

All production code is implemented in FilesystemMiddlewareBase in
_internals/filesystem_helpers.py. You only need to override 3 methods here.
"""

from collections.abc import Callable

from langchain.agents.middleware.types import (
    ContextT,
    ModelRequest,
    ModelResponse,
    ResponseT,
)
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from ax_advanced_class.src.middleware._internals.filesystem_helpers import (
    EDIT_FILE_TOOL_DESCRIPTION,
    EXECUTION_SYSTEM_PROMPT,
    FILESYSTEM_SYSTEM_PROMPT,
    TOOLS_EXCLUDED_FROM_EVICTION,
    FilesystemMiddlewareBase,
    _supports_execution,
    append_to_system_message,
)

# Re-export public types so existing imports keep working
from ax_advanced_class.src.middleware._internals.filesystem_helpers import (  # noqa: F401
    BACKEND_TYPES,
    FileData,
    FilesystemState,
    _file_data_reducer,
)


class FilesystemMiddleware(FilesystemMiddlewareBase):
    """Filesystem middleware with 3 TODO exercises.

    The base class (``FilesystemMiddlewareBase``) creates the ls, read_file, write_file,
    glob, grep, and execute tools. Implement the 3 methods below.
    """

    # ------------------------------------------------------------------
    # TODO 1: Write the edit_file tool description
    # ------------------------------------------------------------------
    def _get_edit_file_description(self) -> str:
        # TODO 1: Return the description for the edit_file tool
        #
        # The LLM reads the tool's description, not its code, to decide how to use it.
        # Checklist for a good Tool description:
        #   - Purpose: What this tool does
        #   - When to use: Must use the Read tool first
        #   - Failure case: Fails if old_string is not unique
        #   - Resolution: Include more context or use replace_all
        #
        # Hint: Refer to the EDIT_FILE_TOOL_DESCRIPTION constant or write your own
        #   Use self._custom_tool_descriptions.get("edit_file") first if it exists
        #
        # The parent class automatically handles StructuredTool creation.
        # You only need to return the description string here.
        #
        return ""

    # ------------------------------------------------------------------
    # TODO 2: System prompt injection + tool filtering
    # ------------------------------------------------------------------
    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        # TODO 2: Inject the system prompt and filter tools
        #
        # Step 1: Check if the execute tool is in request.tools
        # Step 2: If the backend doesn't support execution, remove execute from tools
        # Step 3: Assemble the system prompt
        #   Use self._custom_system_prompt if available
        #   Otherwise use FILESYSTEM_SYSTEM_PROMPT + (EXECUTION_SYSTEM_PROMPT if execute is available)
        # Step 4: Append to the system message with append_to_system_message()
        # Step 5: return handler(request)
        return handler(request)

    # ------------------------------------------------------------------
    # TODO 3: Replace large Tool results with files (eviction)
    # ------------------------------------------------------------------
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        # TODO 3: Replace Tool execution results with files if they are too large
        #
        # Step 1: If self._tool_token_limit_before_evict is None -> return handler(request) as-is
        # Step 2: If tool name is in TOOLS_EXCLUDED_FROM_EVICTION -> return handler(request) as-is
        # Step 3: tool_result = handler(request)
        # Step 4: return self._intercept_large_tool_result(tool_result, request.runtime)
        return handler(request)
