"""
Shell Execution Tool

Provides general shell execution with permission checks.
Uses the base shell executor for all permission validation.
"""

from typing import Optional

from langchain_core.tools import tool

from ax_advanced_class.src.tools.base import (
    BaseShellExecutor,
    PermissionConfig,
    PermissionLevel,
    PermissionDeniedError,
)


class ShellTool:
    """
    General shell execution tool with permission control.

    Provides:
    - run: Execute any shell command (with permission checks)
    - run_script: Execute a script file
    - get_cwd: Get current working directory

    All commands are validated against:
    - Blocked commands list
    - Blocked patterns (regex)
    - Permission level restrictions
    - Path restrictions (for file operations)
    """

    def __init__(self, config: Optional[PermissionConfig] = None):
        self.config = config or PermissionConfig()
        self.executor = BaseShellExecutor(config=self.config)

    def run(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
    ) -> dict:
        """
        Execute a shell command.

        Args:
            command: The command to execute
            cwd: Working directory (defaults to workspace)
            timeout: Command timeout in seconds

        Returns:
            Dict with 'success', 'stdout', 'stderr', 'returncode'
        """
        return self.executor.execute_safe(command, cwd=cwd, timeout=timeout)

    def run_script(
        self,
        script_path: str,
        args: str = "",
        cwd: Optional[str] = None,
        timeout: int = 120,
    ) -> dict:
        """
        Execute a script file.

        Args:
            script_path: Path to the script
            args: Arguments to pass to the script
            cwd: Working directory
            timeout: Script timeout in seconds

        Returns:
            Dict with 'success', 'stdout', 'stderr', 'returncode'
        """
        # Validate script path
        try:
            validated_path = self.executor.validate_path(script_path)
        except PermissionDeniedError as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
            }

        command = f"bash {validated_path}"
        if args:
            command += f" {args}"

        return self.executor.execute_safe(command, cwd=cwd, timeout=timeout)

    def get_cwd(self) -> dict:
        """
        Get current working directory.

        Returns:
            Dict with 'success', 'cwd'
        """
        return {
            "success": True,
            "cwd": self.config.workspace_root,
        }

    def which(self, program: str) -> dict:
        """
        Find the path to a program.

        Args:
            program: Program name

        Returns:
            Dict with 'success', 'path'
        """
        result = self.executor.execute_safe(f"which {program}")
        if result["success"]:
            return {
                "success": True,
                "path": result["stdout"].strip(),
            }
        return {
            "success": False,
            "error": f"Program not found: {program}",
        }

    def env(self, var: Optional[str] = None) -> dict:
        """
        Get environment variable(s).

        Args:
            var: Specific variable name (or None for all)

        Returns:
            Dict with 'success', 'value' or 'env'
        """
        if var:
            result = self.executor.execute_safe(f"echo ${var}")
            if result["success"]:
                return {
                    "success": True,
                    "variable": var,
                    "value": result["stdout"].strip(),
                }
        else:
            result = self.executor.execute_safe("env")
            if result["success"]:
                env_dict = {}
                for line in result["stdout"].strip().split("\n"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_dict[key] = value
                return {
                    "success": True,
                    "env": env_dict,
                }

        return {
            "success": False,
            "error": result.get("stderr", "Failed to get environment"),
        }

    def get_langchain_tools(self) -> list:
        """
        Get LangChain tool wrappers for this tool.

        Returns:
            List of LangChain tools
        """
        @tool
        def shell_run(command: str, timeout: int = 60) -> str:
            """
            Execute a shell command.

            Use this for running build commands, tests, starting servers, etc.
            Commands are restricted to the workspace directory.

            Blocked operations:
            - Destructive system commands (rm -rf /, etc.)
            - Commands outside workspace
            - Dangerous patterns (curl|bash, eval, etc.)

            Args:
                command: The shell command to execute
                timeout: Command timeout in seconds (default: 60)

            Returns:
                Command output (stdout + stderr) or error message
            """
            result = self.run(command, timeout=timeout)
            if result["success"]:
                output = result["stdout"]
                if result["stderr"]:
                    output += f"\n[stderr]: {result['stderr']}"
                return output or "Command completed successfully"
            return f"Error (exit code {result['returncode']}): {result['stderr']}"

        @tool
        def shell_script(script_path: str, args: str = "") -> str:
            """
            Execute a bash script file.

            Args:
                script_path: Path to the script (relative to workspace)
                args: Arguments to pass to the script

            Returns:
                Script output or error message
            """
            result = self.run_script(script_path, args)
            if result["success"]:
                return result["stdout"] or "Script completed successfully"
            return f"Error: {result['stderr']}"

        @tool
        def shell_pwd() -> str:
            """
            Get the current working directory (workspace root).

            Returns:
                Current working directory path
            """
            result = self.get_cwd()
            return result["cwd"]

        @tool
        def shell_which(program: str) -> str:
            """
            Find the path to a program.

            Args:
                program: Program name to find

            Returns:
                Path to program or error message
            """
            result = self.which(program)
            if result["success"]:
                return result["path"]
            return f"Error: {result['error']}"

        return [shell_run, shell_script, shell_pwd, shell_which]
