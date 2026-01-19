"""
Shell Execution Tool

Provides unified access to system shell commands.
This tool covers:
- System Navigation (ls, cd, pwd)
- Git Operations (git status, add, commit, push, etc.)
- Script Execution (bash scripts, python scripts)
- Package Management (pip, npm, uv)
"""

import os
import subprocess
from typing import Optional

from langchain_core.tools import tool

from ax_advanced_class.src.config.tool_permission_config import PermissionConfig
from ax_advanced_class.src.middleware.tool_validation_middleware import (
    ToolValidationMiddleware,
)


class ShellTool:
    """
    Unified shell execution tool.

    Serves as the primary interface for all command-line operations.
    Security and validation are handled by ToolValidationMiddleware.
    """

    def __init__(self, config: Optional[PermissionConfig] = None):
        self.config = config or PermissionConfig()
        # Create middleware instance to be used by agents
        self.validation_middleware = ToolValidationMiddleware(self.config)

    def run(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
    ) -> dict:
        """
        Execute a shell command.
        """
        work_dir = cwd if cwd else self.config.workspace_root

        # Ensure workspace exists
        if not os.path.exists(work_dir):
            try:
                os.makedirs(work_dir, exist_ok=True)
            except OSError:
                pass

        try:
            # shell=True allows complex commands, pipes (if permitted), and shell expansion
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
        def bash(command: str, timeout: int = 60) -> str:
            """
            Execute a shell command (Bash).

            Use this tool for:
            - File system operations: ls, cd, pwd, mkdir, mv, cp
            - Git operations: git status, add, commit, push, pull, checkout
            - Running scripts: ./script.sh, python main.py
            - System tools: grep, find, cat (for small checks)

            Args:
                command: The bash command to execute
                timeout: Command timeout in seconds (default: 60)
            """
            result = self.run(command, timeout=timeout)
            if result["success"]:
                output = result["stdout"]
                if result["stderr"]:
                    output += f"\n[stderr]: {result['stderr']}"
                return output or "Command completed successfully"
            return f"Error (exit code {result['returncode']}): {result['stderr']}"

        return [bash]
