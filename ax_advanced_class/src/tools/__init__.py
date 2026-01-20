"""
Tools Module

Contains permission-controlled tools for the long-running agent:
- BashTool: Shell commands (git, scripts, package managers)
- FileOperationTool: File read/write/edit/glob/grep

TOOL SELECTION GUIDE:
For file operations, ALWAYS prefer FileOperationTool over bash commands:
- Reading files: Use Read (not cat/head/tail)
- Writing files: Use Write (not echo/cat redirects)
- Editing files: Use Edit (not sed/awk)
- Finding files: Use Glob (not find)
- Searching content: Use Grep (not grep/rg)

All tools are built on a middleware-based permission system.
"""

from ax_advanced_class.src.tools.bash_tool import BashTool
from ax_advanced_class.src.tools.file_tool import FileOperationTool
from ax_advanced_class.src.config.tool_permission_config import (
    PermissionConfig,
    PermissionLevel,
)

__all__ = [
    # Tools
    "BashTool",
    "FileOperationTool",
    # Config
    "PermissionConfig",
    "PermissionLevel",
]


def create_default_tools(
    workspace_path: str = "./workspace",
) -> list:
    """
    Create a default set of LangChain tools for the agents.

    Args:
        workspace_path: The root workspace path for file operations

    Returns:
        List of LangChain tools (callable tools)
    """
    import os

    config = PermissionConfig(
        workspace_root=os.path.abspath(workspace_path),
    )

    # Create tool instances
    file_tool = FileOperationTool(config=config)
    bash_tool = BashTool(config=config)

    # Return the actual LangChain tools (decorated functions)
    tools = []
    tools.extend(file_tool.get_langchain_tools())
    tools.extend(bash_tool.get_langchain_tools())

    return tools
