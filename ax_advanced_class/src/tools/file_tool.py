"""
File Operation Tool

Provides file read/write/delete operations with path restrictions.
All operations are restricted to the workspace directory.
"""

import os
import json
from typing import Optional, Literal
from pathlib import Path

from langchain_core.tools import tool, BaseTool
from pydantic import BaseModel, Field

from ax_advanced_class.src.tools.base import (
    BaseShellExecutor,
    PermissionConfig,
    PermissionLevel,
    PermissionDeniedError,
)


class FileReadInput(BaseModel):
    """Input for file read operation."""
    path: str = Field(description="Path to the file to read (relative to workspace)")
    encoding: str = Field(default="utf-8", description="File encoding")


class FileWriteInput(BaseModel):
    """Input for file write operation."""
    path: str = Field(description="Path to the file to write (relative to workspace)")
    content: str = Field(description="Content to write to the file")
    encoding: str = Field(default="utf-8", description="File encoding")
    create_dirs: bool = Field(default=True, description="Create parent directories if needed")


class FileDeleteInput(BaseModel):
    """Input for file delete operation."""
    path: str = Field(description="Path to the file to delete (relative to workspace)")


class FileListInput(BaseModel):
    """Input for listing directory contents."""
    path: str = Field(default=".", description="Path to the directory (relative to workspace)")
    recursive: bool = Field(default=False, description="List recursively")
    pattern: Optional[str] = Field(default=None, description="Glob pattern to filter files")


class FileOperationTool:
    """
    File operation tool with permission control.

    Provides safe file operations restricted to the workspace directory:
    - read_file: Read file contents
    - write_file: Write content to file
    - delete_file: Delete a file
    - list_files: List directory contents

    All paths are validated against the workspace root.
    """

    def __init__(self, config: Optional[PermissionConfig] = None):
        self.config = config or PermissionConfig()
        self.executor = BaseShellExecutor(config=self.config)

    def _resolve_path(self, path: str) -> str:
        """
        Resolve a path relative to workspace and validate it.

        Args:
            path: Path (can be relative or absolute)

        Returns:
            Validated absolute path
        """
        # If relative, make it relative to workspace
        if not os.path.isabs(path):
            path = os.path.join(self.config.workspace_root, path)

        # Validate the path
        return self.executor.validate_path(path)

    def read_file(self, path: str, encoding: str = "utf-8") -> dict:
        """
        Read file contents.

        Args:
            path: Path to file (relative to workspace)
            encoding: File encoding

        Returns:
            Dict with 'success', 'content' or 'error'
        """
        try:
            resolved_path = self._resolve_path(path)

            if not os.path.exists(resolved_path):
                return {
                    "success": False,
                    "error": f"File not found: {path}",
                }

            if not os.path.isfile(resolved_path):
                return {
                    "success": False,
                    "error": f"Not a file: {path}",
                }

            with open(resolved_path, "r", encoding=encoding) as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "path": resolved_path,
            }

        except PermissionDeniedError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Read error: {e}",
            }

    def write_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
    ) -> dict:
        """
        Write content to file.

        Args:
            path: Path to file (relative to workspace)
            content: Content to write
            encoding: File encoding
            create_dirs: Create parent directories if needed

        Returns:
            Dict with 'success', 'path' or 'error'
        """
        # Check permission level
        if self.config.permission_level == PermissionLevel.RESTRICTED:
            return {
                "success": False,
                "error": "Write operations not allowed in RESTRICTED mode",
            }

        try:
            resolved_path = self._resolve_path(path)

            # Create parent directories if needed
            if create_dirs:
                os.makedirs(os.path.dirname(resolved_path), exist_ok=True)

            with open(resolved_path, "w", encoding=encoding) as f:
                f.write(content)

            return {
                "success": True,
                "path": resolved_path,
                "bytes_written": len(content.encode(encoding)),
            }

        except PermissionDeniedError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Write error: {e}",
            }

    def delete_file(self, path: str) -> dict:
        """
        Delete a file.

        Args:
            path: Path to file (relative to workspace)

        Returns:
            Dict with 'success' or 'error'
        """
        # Check permission level
        if self.config.permission_level == PermissionLevel.RESTRICTED:
            return {
                "success": False,
                "error": "Delete operations not allowed in RESTRICTED mode",
            }

        try:
            resolved_path = self._resolve_path(path)

            if not os.path.exists(resolved_path):
                return {
                    "success": False,
                    "error": f"File not found: {path}",
                }

            if not os.path.isfile(resolved_path):
                return {
                    "success": False,
                    "error": f"Not a file: {path}",
                }

            os.remove(resolved_path)

            return {
                "success": True,
                "deleted": resolved_path,
            }

        except PermissionDeniedError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Delete error: {e}",
            }

    def list_files(
        self,
        path: str = ".",
        recursive: bool = False,
        pattern: Optional[str] = None,
    ) -> dict:
        """
        List directory contents.

        Args:
            path: Path to directory (relative to workspace)
            recursive: List recursively
            pattern: Glob pattern to filter

        Returns:
            Dict with 'success', 'files' or 'error'
        """
        try:
            resolved_path = self._resolve_path(path)

            if not os.path.exists(resolved_path):
                return {
                    "success": False,
                    "error": f"Directory not found: {path}",
                }

            if not os.path.isdir(resolved_path):
                return {
                    "success": False,
                    "error": f"Not a directory: {path}",
                }

            files = []
            base_path = Path(resolved_path)

            if recursive:
                if pattern:
                    items = base_path.rglob(pattern)
                else:
                    items = base_path.rglob("*")
            else:
                if pattern:
                    items = base_path.glob(pattern)
                else:
                    items = base_path.iterdir()

            for item in items:
                rel_path = item.relative_to(base_path)
                files.append({
                    "name": str(rel_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                })

            return {
                "success": True,
                "path": resolved_path,
                "files": files,
                "count": len(files),
            }

        except PermissionDeniedError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"List error: {e}",
            }

    def get_langchain_tools(self) -> list:
        """
        Get LangChain tool wrappers for this tool.

        Returns:
            List of LangChain tools
        """
        @tool
        def read_file(path: str, encoding: str = "utf-8") -> str:
            """
            Read the contents of a file.

            Args:
                path: Path to the file (relative to workspace)
                encoding: File encoding (default: utf-8)

            Returns:
                File contents or error message
            """
            result = self.read_file(path, encoding)
            if result["success"]:
                return result["content"]
            return f"Error: {result['error']}"

        @tool
        def write_file(path: str, content: str) -> str:
            """
            Write content to a file.

            Args:
                path: Path to the file (relative to workspace)
                content: Content to write

            Returns:
                Success message or error
            """
            result = self.write_file(path, content)
            if result["success"]:
                return f"Successfully wrote {result['bytes_written']} bytes to {result['path']}"
            return f"Error: {result['error']}"

        @tool
        def delete_file(path: str) -> str:
            """
            Delete a file.

            Args:
                path: Path to the file (relative to workspace)

            Returns:
                Success message or error
            """
            result = self.delete_file(path)
            if result["success"]:
                return f"Successfully deleted {result['deleted']}"
            return f"Error: {result['error']}"

        @tool
        def list_files(path: str = ".", recursive: bool = False, pattern: str = None) -> str:
            """
            List files in a directory.

            Args:
                path: Directory path (relative to workspace)
                recursive: Whether to list recursively
                pattern: Glob pattern to filter files

            Returns:
                List of files or error
            """
            result = self.list_files(path, recursive, pattern)
            if result["success"]:
                files_str = "\n".join(
                    f"  {'[D]' if f['type'] == 'directory' else '[F]'} {f['name']}"
                    for f in result["files"]
                )
                return f"Files in {result['path']} ({result['count']} items):\n{files_str}"
            return f"Error: {result['error']}"

        return [read_file, write_file, delete_file, list_files]
