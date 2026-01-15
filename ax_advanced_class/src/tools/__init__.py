"""
Tools Module

Contains permission-controlled tools for the long-running agent:
- ShellTool: General shell execution with permission checks
- FileOperationTool: File read/write/delete with path restrictions
- GitTool: Git operations with command restrictions

All tools are built on a base shell executor with permission control.
"""

from ax_advanced_class.src.tools.base import (
    PermissionLevel,
    PermissionConfig,
    PermissionDeniedError,
)
from ax_advanced_class.src.tools.shell_tool import ShellTool
from ax_advanced_class.src.tools.file_tool import FileOperationTool
from ax_advanced_class.src.tools.git_tool import GitTool

__all__ = [
    # Permission system
    "PermissionLevel",
    "PermissionConfig",
    "PermissionDeniedError",
    # Tools
    "ShellTool",
    "FileOperationTool",
    "GitTool",
]


def create_default_tools(
    workspace_path: str = "./workspace",
    permission_level: PermissionLevel = PermissionLevel.STANDARD,
) -> list:
    """
    Create a default set of LangChain tools for the agents.

    Args:
        workspace_path: The root workspace path for file operations
        permission_level: The permission level for tool execution

    Returns:
        List of LangChain tools (callable tools)
    """
    import os

    config = PermissionConfig(
        workspace_root=os.path.abspath(workspace_path),
        permission_level=permission_level,
    )

    # Create tool instances
    file_tool = FileOperationTool(config=config)
    git_tool = GitTool(config=config)
    shell_tool = ShellTool(config=config)

    # Return the actual LangChain tools (decorated functions)
    tools = []
    tools.extend(file_tool.get_langchain_tools())
    tools.extend(git_tool.get_langchain_tools())
    tools.extend(shell_tool.get_langchain_tools())

    return tools
