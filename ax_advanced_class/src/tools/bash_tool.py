"""
Bash Execution Tool

Provides unified access to system shell commands.

This tool covers:
- System Navigation (ls, pwd, mkdir, mv, cp)
- Git Operations (git status, add, commit, push, pull, checkout)
- Script Execution (bash scripts, python scripts)
- Package Management (pip, npm, uv)

IMPORTANT - Prefer File Tools for these operations:
- Reading files: Use Read tool instead of cat/head/tail
- Searching content: Use Grep tool instead of grep/rg
- Finding files: Use Glob tool instead of find
- Editing files: Use Edit tool instead of sed/awk
- Writing files: Use Write tool instead of echo/cat redirects

File tools are purpose-built, safer, and provide better validation.
"""

import os
import subprocess
from typing import Optional

from langchain_core.tools import tool

from ax_advanced_class.src.config.tool_permission_config import PermissionConfig


class BashTool:
    """
    Unified bash execution tool.

    Serves as the primary interface for all command-line operations.
    Security and validation are handled by ToolValidationMiddleware.
    """

    # Tool names exposed by this class
    _TOOL_NAMES = ("bash",)

    def __init__(self, config: Optional[PermissionConfig] = None):
        self.config = config or PermissionConfig()

    @staticmethod
    def get_tool_names() -> tuple[str, ...]:
        """
        Return names of all LangChain tools provided by this class.

        This is a static method to allow ToolValidationMiddleware to
        check tool names without instantiating the tool.
        """
        return BashTool._TOOL_NAMES

    def run(
        self,
        command: str,
        timeout: Optional[int] = 120,
    ) -> dict:
        """
        Execute a shell command.
        """
        work_dir = self.config.workspace_root

        # Ensure workspace exists
        if not os.path.exists(work_dir):
            try:
                os.makedirs(work_dir, exist_ok=True)
            except OSError:
                pass

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                timeout=timeout,
                capture_output=True,
                text=True,
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "returncode": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
                "returncode": -1,
            }

    def get_langchain_tools(self) -> list:
        """
        Get LangChain tool wrappers for this tool.
        """

        @tool
        def bash(command: str, timeout: Optional[int] = 120) -> str:
            """
            Execute a shell command (Bash).

            Use this tool for:
            - File system navigation: ls, pwd, mkdir, mv, cp
            - Git operations: git status, add, commit, push, pull, checkout
            - Running scripts: ./script.sh, python main.py
            - Package management: npm, pip, uv

            PREFER FILE TOOLS instead of bash for:
            - Reading files: Use Read (not cat/head/tail)
            - Searching content: Use Grep (not grep/rg)
            - Finding files: Use Glob (not find)
            - Editing files: Use Edit (not sed/awk)
            - Writing files: Use Write (not echo/cat redirects)

            Args:
                command: The bash command to execute
                timeout: Command timeout in seconds (default: 120, max: 600)
            """
            result = self.run(command, timeout=timeout)
            if result["success"]:
                output = result["stdout"]
                if result["stderr"]:
                    output += f"\n[stderr]: {result['stderr']}"
                return output or "Command completed successfully"
            return f"Error (exit code {result['returncode']}): {result['stderr']}"

        return [bash]
