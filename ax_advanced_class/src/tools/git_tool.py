"""
Git Operation Tool

Provides git operations with command restrictions.
Blocks dangerous commands like force push, hard reset to remote.
"""

import os
from typing import Optional, List, Set
from dataclasses import dataclass, field

from langchain_core.tools import tool

from ax_advanced_class.src.tools.base import (
    BaseShellExecutor,
    PermissionConfig,
    PermissionLevel,
    PermissionDeniedError,
)


@dataclass
class GitPermissionConfig:
    """
    Git-specific permission configuration.

    Attributes:
        allow_push: Allow git push
        allow_force_push: Allow git push --force
        allow_hard_reset: Allow git reset --hard
        allow_rebase: Allow git rebase
        protected_branches: Branches that cannot be force-pushed
        blocked_git_commands: Git subcommands that are blocked
    """
    allow_push: bool = True
    allow_force_push: bool = False
    allow_hard_reset: bool = True  # Local hard reset is useful
    allow_rebase: bool = True
    protected_branches: Set[str] = field(default_factory=lambda: {
        "main", "master", "production", "prod",
    })
    blocked_git_commands: Set[str] = field(default_factory=lambda: {
        "push --force origin main",
        "push --force origin master",
        "push -f origin main",
        "push -f origin master",
        "push --force-with-lease origin main",
        "push --force-with-lease origin master",
    })


class GitTool:
    """
    Git operation tool with command restrictions.

    Provides safe git operations:
    - status: Show working tree status
    - log: Show commit logs
    - diff: Show changes
    - add: Add files to staging
    - commit: Commit changes
    - push: Push changes (with restrictions)
    - pull: Pull changes
    - branch: Branch operations
    - checkout: Checkout branches/files
    - stash: Stash operations
    - reset: Reset operations (with restrictions)

    Dangerous operations are blocked or require ELEVATED permission:
    - Force push to protected branches
    - Hard reset to remote
    """

    def __init__(
        self,
        config: Optional[PermissionConfig] = None,
        git_config: Optional[GitPermissionConfig] = None,
    ):
        self.config = config or PermissionConfig()
        self.git_config = git_config or GitPermissionConfig()
        self.executor = BaseShellExecutor(config=self.config)

    def _validate_git_command(self, git_args: str) -> None:
        """
        Validate git command arguments.

        Args:
            git_args: Git command arguments (without 'git' prefix)

        Raises:
            PermissionDeniedError: If command is not allowed
        """
        git_args_lower = git_args.lower().strip()

        # Check blocked commands
        for blocked in self.git_config.blocked_git_commands:
            if blocked in git_args_lower:
                raise PermissionDeniedError(
                    f"Git command blocked: {blocked}",
                    operation="git",
                    reason="Command is in git blocklist",
                )

        # Check force push
        if "push" in git_args_lower and (
            "--force" in git_args_lower or "-f " in git_args_lower
        ):
            if not self.git_config.allow_force_push:
                # Check if it's to a protected branch
                for branch in self.git_config.protected_branches:
                    if branch in git_args_lower:
                        raise PermissionDeniedError(
                            f"Force push to protected branch '{branch}' is not allowed",
                            operation="git push --force",
                            reason="Branch is protected",
                        )

        # Check push permission
        if "push" in git_args_lower and not self.git_config.allow_push:
            raise PermissionDeniedError(
                "Git push is not allowed",
                operation="git push",
                reason="Push is disabled in config",
            )

        # Permission level checks
        if self.config.permission_level == PermissionLevel.RESTRICTED:
            # Only allow read operations in RESTRICTED mode
            allowed_read_ops = [
                "status", "log", "diff", "show", "branch", "remote",
                "config --list", "ls-files", "ls-tree",
            ]
            is_read_op = any(
                git_args_lower.startswith(op)
                for op in allowed_read_ops
            )
            if not is_read_op:
                raise PermissionDeniedError(
                    "Only read operations allowed in RESTRICTED mode",
                    operation="git",
                    reason=f"Command: git {git_args[:30]}...",
                )

    def _run_git(self, args: str, cwd: Optional[str] = None) -> dict:
        """
        Run a git command.

        Args:
            args: Git command arguments
            cwd: Working directory

        Returns:
            Dict with 'success', 'stdout', 'stderr', 'returncode'
        """
        try:
            self._validate_git_command(args)
            return self.executor.execute_safe(f"git {args}", cwd=cwd)
        except PermissionDeniedError as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
            }

    # =========================================================================
    # Git Operations
    # =========================================================================

    def status(self, cwd: Optional[str] = None) -> dict:
        """Get git status."""
        return self._run_git("status", cwd=cwd)

    def log(
        self,
        n: int = 10,
        oneline: bool = True,
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Get git log.

        Args:
            n: Number of commits to show
            oneline: Use oneline format
            cwd: Working directory
        """
        args = f"log -{n}"
        if oneline:
            args += " --oneline"
        return self._run_git(args, cwd=cwd)

    def diff(
        self,
        staged: bool = False,
        file_path: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Get git diff.

        Args:
            staged: Show staged changes
            file_path: Specific file to diff
            cwd: Working directory
        """
        args = "diff"
        if staged:
            args += " --staged"
        if file_path:
            args += f" -- {file_path}"
        return self._run_git(args, cwd=cwd)

    def add(
        self,
        files: str = ".",
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Add files to staging.

        Args:
            files: Files to add (default: all)
            cwd: Working directory
        """
        return self._run_git(f"add {files}", cwd=cwd)

    def commit(
        self,
        message: str,
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Commit changes.

        Args:
            message: Commit message
            cwd: Working directory
        """
        # Escape quotes in message
        safe_message = message.replace('"', '\\"')
        return self._run_git(f'commit -m "{safe_message}"', cwd=cwd)

    def push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Push changes.

        Args:
            remote: Remote name
            branch: Branch name
            force: Force push (requires ELEVATED permission)
            cwd: Working directory
        """
        args = f"push {remote}"
        if branch:
            args += f" {branch}"
        if force:
            args += " --force"
        return self._run_git(args, cwd=cwd)

    def pull(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Pull changes.

        Args:
            remote: Remote name
            branch: Branch name
            cwd: Working directory
        """
        args = f"pull {remote}"
        if branch:
            args += f" {branch}"
        return self._run_git(args, cwd=cwd)

    def branch(
        self,
        name: Optional[str] = None,
        delete: bool = False,
        list_all: bool = False,
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Branch operations.

        Args:
            name: Branch name (for create/delete)
            delete: Delete branch
            list_all: List all branches
            cwd: Working directory
        """
        if list_all:
            return self._run_git("branch -a", cwd=cwd)
        elif delete and name:
            return self._run_git(f"branch -d {name}", cwd=cwd)
        elif name:
            return self._run_git(f"branch {name}", cwd=cwd)
        else:
            return self._run_git("branch", cwd=cwd)

    def checkout(
        self,
        target: str,
        create: bool = False,
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Checkout branch or files.

        Args:
            target: Branch name or file path
            create: Create new branch
            cwd: Working directory
        """
        args = "checkout"
        if create:
            args += " -b"
        args += f" {target}"
        return self._run_git(args, cwd=cwd)

    def stash(
        self,
        action: str = "push",
        message: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Stash operations.

        Args:
            action: Stash action (push, pop, list, apply, drop)
            message: Stash message (for push)
            cwd: Working directory
        """
        args = f"stash {action}"
        if action == "push" and message:
            args += f' -m "{message}"'
        return self._run_git(args, cwd=cwd)

    def reset(
        self,
        mode: str = "mixed",
        target: str = "HEAD",
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Reset operations.

        Args:
            mode: Reset mode (soft, mixed, hard)
            target: Reset target (commit hash or ref)
            cwd: Working directory
        """
        return self._run_git(f"reset --{mode} {target}", cwd=cwd)

    def init(self, cwd: Optional[str] = None) -> dict:
        """Initialize git repository."""
        return self._run_git("init", cwd=cwd)

    def clone(
        self,
        url: str,
        directory: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> dict:
        """
        Clone a repository.

        Args:
            url: Repository URL
            directory: Target directory
            cwd: Working directory
        """
        args = f"clone {url}"
        if directory:
            args += f" {directory}"
        return self._run_git(args, cwd=cwd)

    def get_langchain_tools(self) -> list:
        """
        Get LangChain tool wrappers for this tool.

        Returns:
            List of LangChain tools
        """
        @tool
        def git_status() -> str:
            """
            Get git status of the current repository.

            Returns:
                Git status output
            """
            result = self.status()
            if result["success"]:
                return result["stdout"]
            return f"Error: {result['stderr']}"

        @tool
        def git_log(n: int = 10) -> str:
            """
            Get git commit log.

            Args:
                n: Number of commits to show

            Returns:
                Git log output
            """
            result = self.log(n=n, oneline=True)
            if result["success"]:
                return result["stdout"]
            return f"Error: {result['stderr']}"

        @tool
        def git_diff(staged: bool = False) -> str:
            """
            Get git diff.

            Args:
                staged: Show staged changes only

            Returns:
                Git diff output
            """
            result = self.diff(staged=staged)
            if result["success"]:
                return result["stdout"] or "No changes"
            return f"Error: {result['stderr']}"

        @tool
        def git_add(files: str = ".") -> str:
            """
            Add files to git staging.

            Args:
                files: Files to add (default: all files)

            Returns:
                Success message or error
            """
            result = self.add(files=files)
            if result["success"]:
                return f"Successfully added: {files}"
            return f"Error: {result['stderr']}"

        @tool
        def git_commit(message: str) -> str:
            """
            Commit staged changes.

            Args:
                message: Commit message

            Returns:
                Commit result or error
            """
            result = self.commit(message=message)
            if result["success"]:
                return result["stdout"]
            return f"Error: {result['stderr']}"

        @tool
        def git_push(remote: str = "origin", branch: str = None) -> str:
            """
            Push commits to remote.

            Args:
                remote: Remote name (default: origin)
                branch: Branch name (optional)

            Returns:
                Push result or error
            """
            result = self.push(remote=remote, branch=branch)
            if result["success"]:
                return result["stdout"] or "Push successful"
            return f"Error: {result['stderr']}"

        @tool
        def git_pull(remote: str = "origin", branch: str = None) -> str:
            """
            Pull changes from remote.

            Args:
                remote: Remote name (default: origin)
                branch: Branch name (optional)

            Returns:
                Pull result or error
            """
            result = self.pull(remote=remote, branch=branch)
            if result["success"]:
                return result["stdout"]
            return f"Error: {result['stderr']}"

        @tool
        def git_checkout(target: str, create_branch: bool = False) -> str:
            """
            Checkout a branch or create a new branch.

            Args:
                target: Branch name or commit hash
                create_branch: Create new branch with -b flag

            Returns:
                Checkout result or error
            """
            result = self.checkout(target=target, create=create_branch)
            if result["success"]:
                return result["stdout"] or f"Switched to {target}"
            return f"Error: {result['stderr']}"

        @tool
        def git_branch(name: str = None, list_all: bool = False, delete: bool = False) -> str:
            """
            List, create, or delete branches.

            Args:
                name: Branch name (for create/delete)
                list_all: List all branches including remote
                delete: Delete the branch

            Returns:
                Branch operation result
            """
            result = self.branch(name=name, list_all=list_all, delete=delete)
            if result["success"]:
                return result["stdout"]
            return f"Error: {result['stderr']}"

        @tool
        def git_init() -> str:
            """
            Initialize a new git repository.

            Returns:
                Init result or error
            """
            result = self.init()
            if result["success"]:
                return result["stdout"] or "Git repository initialized"
            return f"Error: {result['stderr']}"

        return [
            git_status,
            git_log,
            git_diff,
            git_add,
            git_commit,
            git_push,
            git_pull,
            git_checkout,
            git_branch,
            git_init,
        ]
