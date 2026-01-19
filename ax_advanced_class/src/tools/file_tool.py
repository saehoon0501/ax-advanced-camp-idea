"""
File Operation Tools

Provides specialized tools for file manipulation:
- read: Read file contents (text)
- write: Create or overwrite files
- edit: Exact string replacement in files
- glob: Find files by pattern
- grep: Search file contents with regex
"""

import os
import json
from typing import Optional, List
import subprocess

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ax_advanced_class.src.config.tool_permission_config import (
    PermissionConfig,
)


class FileOperationTool:
    """
    File operation tools with permission control.
    """

    def read_file(self, validated_path: str, encoding: str = "utf-8") -> dict:
        """Read the contents of a file."""
        try:
            if not os.path.exists(validated_path):
                return {"success": False, "error": f"File not found: {validated_path}"}

            if not os.path.isfile(validated_path):
                return {"success": False, "error": f"Not a file: {validated_path}"}

            with open(validated_path, "r", encoding=encoding) as f:
                content = f.read()

            return {"success": True, "content": content, "path": validated_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, validated_path: str, content: str) -> dict:
        """Write content to a file."""
        try:
            parent_dir = os.path.dirname(validated_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            with open(validated_path, "w", encoding="utf-8") as f:
                bytes_written = f.write(content)

            return {
                "success": True,
                "bytes_written": bytes_written,
                "path": validated_path,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def edit_file(self, validated_path: str, old_string: str, new_string: str) -> dict:
        """Replace exact string in file."""
        try:
            read_result = self.read_file(validated_path)
            if not read_result["success"]:
                return read_result

            content = read_result["content"]
            if old_string not in content:
                return {
                    "success": False,
                    "error": "Exact match for `old_string` not found in file. Ensure whitespace matches exactly.",
                }

            # Check for multiple occurrences
            count = content.count(old_string)
            if count > 1:
                return {
                    "success": False,
                    "error": f"Found {count} occurrences of `old_string`. Edit must be unique.",
                }

            new_content = content.replace(old_string, new_string)
            return self.write_file(validated_path, new_content)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def glob_files(self, validated_search_root: str, pattern: str = "**/*") -> dict:
        """Find files by glob pattern."""
        try:
            # We use python's glob or just list_files logic with pattern
            # Or assume the user wants recursive search from workspace root
            # Let's map this to a recursive list_files implementation or use subprocess 'find' via shell if preferred?
            # Sticking to python for safety.
            import glob

            # Ensure pattern is safe? Glob patterns are generally safe-ish but let's constrain to workspace
            # Glob doesn't strictly respect 'root' arg like walk does easily without chdir.
            # Safest is to walk and match.

            files_list = []
            import fnmatch

            for root, _, files in os.walk(validated_search_root):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, validated_search_root)

                    if fnmatch.fnmatch(rel_path, pattern):
                        files_list.append(rel_path)

            return {"success": True, "files": files_list}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def grep_files(self, pattern: str, validated_path: str = ".", recursive: bool = True) -> dict:
        """Search file contents with regex."""
        try:
            # Using subprocess grep is faster and standard
            work_dir = self.config.workspace_root
            cmd = ["grep", "-n"]  # -n for line numbers
            if recursive:
                cmd.append("-r")
            cmd.extend([pattern, validated_path])

            # This is a read operation, so it should be allowed generally
            # But we must validate paths. 'path' arg is relative to workspace.

            # Since we have ShellTool for general commands, maybe Grep should be there?
            # But the user requested "Grep" as a tool alongside "Read/Write".
            # We can implement it using python to avoid shell injection risks or rely on validated shell.
            # Let's use python for consistency with "FileOperationTool".

            import re

            regex = re.compile(pattern)
            matches = []

            if os.path.isfile(validated_path):
                # Search single file
                with open(validated_path, "r", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            matches.append(f"{validated_path}:{i}:{line.strip()}")

            elif os.path.isdir(validated_path) and recursive:
                for root, _, files in os.walk(validated_path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, work_dir)
                        try:
                            with open(full_path, "r", errors="ignore") as f:
                                for i, line in enumerate(f, 1):
                                    if regex.search(line):
                                        matches.append(f"{rel_path}:{i}:{line.strip()}")
                        except:
                            continue  # Skip binary/unreadable

            return {"success": True, "matches": matches}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_langchain_tools(self) -> list:
        """
        Get LangChain tool wrappers for this tool.
        """

        @tool
        def read(validated_path: str, encoding: str = "utf-8") -> str:
            """
            Read files (including text, code, config).

            Args:
                path: Path to the file (relative to workspace)
                encoding: File encoding (default: utf-8)
            """
            result = self.read_file(validated_path, encoding)
            if result["success"]:
                return result["content"]
            return f"Error: {result['error']}"

        @tool
        def write(validated_path: str, content: str) -> str:
            """
            Create/overwrite files.

            Args:
                path: Path to the file (relative to workspace)
                content: Content to write
            """
            result = self.write_file(validated_path, content)
            if result["success"]:
                return f"Successfully wrote {result['bytes_written']} bytes to {result['path']}"
            return f"Error: {result['error']}"

        @tool
        def edit(validated_path: str, old_string: str, new_string: str) -> str:
            """
            Exact string replacement in files.

            Args:
                path: Path to the file
                old_string: The exact string to replace (must be unique in file)
                new_string: The new string to replace with
            """
            result = self.edit_file(validated_path, old_string, new_string)
            if result["success"]:
                return f"Successfully edited {result['path']}"
            return f"Error: {result['error']}"

        @tool
        def glob(pattern: str = "**/*") -> str:
            """
            Find files by pattern (e.g., **/*.ts).

            Args:
                pattern: Glob pattern to match
            """
            result = self.glob_files(pattern)
            if result["success"]:
                return json.dumps(result["files"], indent=2)
            return f"Error: {result['error']}"

        @tool
        def grep(pattern: str, validated_path: str = ".", recursive: bool = True) -> str:
            """
            Search file contents with regex.

            Args:
                pattern: Regex pattern to search for
                path: File or directory to search in (default: .)
                recursive: Search recursively (default: True)
            """
            result = self.grep_files(pattern, validated_path, recursive)
            if result["success"]:
                return "\n".join(result["matches"]) if result["matches"] else "No matches found."
            return f"Error: {result['error']}"

        return [read, write, edit, glob, grep]
