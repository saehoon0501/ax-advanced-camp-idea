"""
File Operation Tools

Provides specialized tools for file manipulation.
ALWAYS PREFER these tools over bash equivalents for file operations.

Available tools:
- read: Read file contents (PREFER over cat/head/tail)
- write: Create or overwrite files (PREFER over echo/cat redirects)
- edit: Exact string replacement in files (PREFER over sed/awk)
- find: Find files by pattern (PREFER over bash glob)
- search: Search file contents with regex (PREFER over bash grep/rg)

These tools are purpose-built, safer, and provide better validation
than their bash command equivalents.
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

    # Tool names exposed by this class
    _TOOL_NAMES = ("read", "write", "edit", "find", "search")

    def __init__(self, config: Optional[PermissionConfig] = None):
        self.config = config or PermissionConfig()

    @staticmethod
    def get_tool_names() -> tuple[str, ...]:
        """
        Return names of all LangChain tools provided by this class.

        This is a static method to allow ToolValidationMiddleware to
        check tool names without instantiating the tool.
        """
        return FileOperationTool._TOOL_NAMES

    def _read_file_raw(self, validated_path: str, encoding: str = "utf-8") -> dict:
        """
        Read raw contents of a file without formatting.
        Used internally by edit_file to get unformatted content.

        Args:
            validated_path: Path to the file to read
            encoding: File encoding (default: utf-8)

        Returns:
            dict with success status and raw content
        """
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

    def read_file(
        self,
        validated_path: str,
        encoding: str = "utf-8",
        offset: int = 0,
        limit: int = 2000,
    ) -> dict:
        """
        Read the contents of a file with offset, limit, line truncation, and cat -n format.

        Args:
            validated_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            offset: Line number to start reading from (0-based index, default: 0)
            limit: Maximum number of lines to read (default: 2000)

        Returns:
            dict with success status and content in cat -n format:
            "     1→first line\\n     2→second line\\n"
            Lines longer than 2000 characters are truncated.
        """
        try:
            if not os.path.exists(validated_path):
                return {"success": False, "error": f"File not found: {validated_path}"}

            if not os.path.isfile(validated_path):
                return {"success": False, "error": f"Not a file: {validated_path}"}

            max_line_length = 2000

            with open(validated_path, "r", encoding=encoding) as f:
                lines = f.readlines()

            # Apply offset and limit
            selected_lines = lines[offset : offset + limit]

            # Format lines in cat -n style with line numbers starting at offset + 1
            formatted_lines = []
            for i, line in enumerate(selected_lines):
                line_number = offset + i + 1  # 1-based line number
                # Remove trailing newline for processing
                line_content = line.rstrip("\n")
                # Truncate lines longer than 2000 characters
                if len(line_content) > max_line_length:
                    line_content = line_content[:max_line_length] + "..."
                # Format: right-aligned line number (6 chars) + tab arrow + content
                formatted_line = f"{line_number:>6}\t{line_content}"
                formatted_lines.append(formatted_line)

            content = "\n".join(formatted_lines)

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

    def edit_file(self, validated_path: str, old_string: str, new_string: str, replace_all: bool = False) -> dict:
        """Replace exact string in file.

        Args:
            validated_path: Path to the file to edit
            old_string: The exact string to replace
            new_string: The new string to replace with
            replace_all: If True, replace all occurrences. If False (default),
                         the edit must be unique (only one occurrence allowed).
        """
        try:
            read_result = self._read_file_raw(validated_path)
            if not read_result["success"]:
                return read_result

            content = read_result["content"]
            if old_string not in content:
                return {
                    "success": False,
                    "error": "Exact match for `old_string` not found in file. Ensure whitespace matches exactly.",
                }

            # Check for multiple occurrences (only if replace_all is False)
            count = content.count(old_string)
            if count > 1 and not replace_all:
                return {
                    "success": False,
                    "error": f"Found {count} occurrences of `old_string`. Edit must be unique. Use replace_all=True to replace all occurrences.",
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

    def _find_ripgrep(self) -> Optional[str]:
        """Find the ripgrep binary from common locations."""
        import shutil

        # Check if rg is in PATH
        rg_path = shutil.which("rg")
        if rg_path:
            return rg_path

        # Check common installation locations
        common_paths = [
            "/opt/homebrew/bin/rg",  # Homebrew on Apple Silicon
            "/usr/local/bin/rg",  # Homebrew on Intel Mac
            os.path.expanduser("~/.cargo/bin/rg"),  # Cargo install
        ]

        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return None

    def grep_files(
        self,
        pattern: str,
        validated_path: str = ".",
        recursive: bool = True,
        multiline: bool = False,
        output_mode: str = "files_with_matches",
        case_insensitive: bool = False,
        glob_filter: Optional[str] = None,
        file_type: Optional[str] = None,
        context_before: int = 0,
        context_after: int = 0,
        context: int = 0,
        head_limit: int = 0,
    ) -> dict:
        """Search file contents using ripgrep.

        Args:
            pattern: Regex pattern to search for
            validated_path: File or directory to search in
            recursive: Search recursively in directories (default: True)
            multiline: Enable multiline mode where . matches newlines (rg -U --multiline-dotall)
            output_mode: One of "files_with_matches" (file paths only), "content" (matching lines), "count" (match counts)
            case_insensitive: Case insensitive search (rg -i)
            glob_filter: Glob pattern to filter files (rg --glob)
            file_type: File type filter (rg --type), e.g., "py", "js", "rust"
            context_before: Lines before each match (rg -B)
            context_after: Lines after each match (rg -A)
            context: Lines before and after each match (rg -C)
            head_limit: Limit output to first N lines/entries (0 = unlimited)

        Returns:
            dict with success status, matches list, and raw_output
        """
        try:
            # Find ripgrep binary
            rg_path = self._find_ripgrep()
            if not rg_path:
                return {
                    "success": False,
                    "error": "ripgrep (rg) not found. Please install it via: brew install ripgrep",
                }

            cmd = [rg_path]

            # Output mode
            if output_mode == "files_with_matches":
                cmd.append("-l")  # files only
            elif output_mode == "count":
                cmd.append("-c")  # count mode
            # "content" is default (shows matching lines)

            # Line numbers for content mode
            if output_mode == "content":
                cmd.append("-n")

            # Multiline
            if multiline:
                cmd.extend(["-U", "--multiline-dotall"])

            # Case insensitive
            if case_insensitive:
                cmd.append("-i")

            # Glob filter
            if glob_filter:
                cmd.extend(["--glob", glob_filter])

            # File type
            if file_type:
                cmd.extend(["--type", file_type])

            # Context lines (only relevant for content mode)
            if output_mode == "content":
                if context > 0:
                    cmd.extend(["-C", str(context)])
                else:
                    if context_before > 0:
                        cmd.extend(["-B", str(context_before)])
                    if context_after > 0:
                        cmd.extend(["-A", str(context_after)])

            # Pattern and path
            cmd.append(pattern)
            cmd.append(validated_path)

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.config.workspace_root,
            )

            output = result.stdout.strip()

            # Apply head limit if specified
            if head_limit > 0 and output:
                lines = output.split("\n")
                output = "\n".join(lines[:head_limit])

            # Parse output based on mode
            if output:
                matches = output.split("\n")
            else:
                matches = []

            return {"success": True, "matches": matches, "raw_output": output}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Grep timed out after 60 seconds"}
        except FileNotFoundError:
            return {"success": False, "error": "ripgrep (rg) not found. Please install it."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_langchain_tools(self) -> list:
        """
        Get LangChain tool wrappers for this tool.
        """

        @tool
        def read(
            validated_path: str,
            encoding: str = "utf-8",
            offset: int = 0,
            limit: int = 2000,
        ) -> str:
            """
            Reads a file from the local filesystem.

            You can access any file directly by using this tool. Assume this tool
            is able to read all files on the machine. If the User provides a path
            to a file assume that path is valid. It is okay to read a file that
            does not exist; an error will be returned.

            Usage:
            - The file_path parameter must be an absolute path, not a relative path
            - By default, it reads up to 2000 lines starting from the beginning of the file
            - You can optionally specify a line offset and limit (especially handy for long files),
              but it's recommended to read the whole file by not providing these parameters
            - Any lines longer than 2000 characters will be truncated
            - Results are returned using cat -n format, with line numbers starting at 1
            - This tool can only read files, not directories. To read a directory,
              use an ls command via the Bash tool.
            - If you read a file that exists but has empty contents you will receive
              a system reminder warning in place of file contents.

            Args:
                file_path: The absolute path to the file to read
                encoding: File encoding (default: utf-8)
                offset: The line number to start reading from. Only provide if the file
                        is too large to read at once.
                limit: The number of lines to read. Only provide if the file is too
                       large to read at once. (default: 2000)
            """
            result = self.read_file(validated_path, encoding, offset, limit)
            if result["success"]:
                return result["content"]
            return f"Error: {result['error']}"

        @tool
        def write(validated_path: str, content: str) -> str:
            """
            Writes a file to the local filesystem.

            Usage:
            - This tool will overwrite the existing file if there is one at the provided path.
            - If this is an existing file, you MUST use the Read tool first to read the file's
              contents. This tool will fail if you did not read the file first.
            - ALWAYS prefer editing existing files in the codebase. NEVER write new files
              unless explicitly required.
            - NEVER proactively create documentation files (*.md) or README files. Only create
              documentation files if explicitly requested by the User.
            - Only use emojis if the user explicitly requests it. Avoid writing emojis to
              files unless asked.

            Args:
                path: Absolute path to the file to write
                content: The content to write to the file
            """
            result = self.write_file(validated_path, content)
            if result["success"]:
                return f"Successfully wrote {result['bytes_written']} bytes to {result['path']}"
            return f"Error: {result['error']}"

        @tool
        def edit(validated_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
            """
            Performs exact string replacements in files.

            Usage:
            - You must use your Read tool at least once in the conversation before
              editing. This tool will error if you attempt an edit without reading.
            - When editing text from Read tool output, ensure you preserve the exact
              indentation (tabs/spaces) as it appears AFTER the line number prefix.
              The line number prefix format is: spaces + line number + tab. Everything
              after that tab is the actual file content to match. Never include any
              part of the line number prefix in the old_string or new_string.
            - ALWAYS prefer editing existing files in the codebase. NEVER write new
              files unless explicitly required.
            - Only use emojis if the user explicitly requests it. Avoid adding emojis
              to files unless asked.
            - The edit will FAIL if old_string is not unique in the file. Either
              provide a larger string with more surrounding context to make it unique
              or use replace_all to change every instance of old_string.
            - Use replace_all for replacing and renaming strings across the file.
              This parameter is useful if you want to rename a variable for instance.

            Best Practices:
            - Read the file first before editing to understand its content
            - Include enough context in old_string to ensure uniqueness
            - If old_string appears multiple times, either include more surrounding lines
              or use replace_all=True to replace all occurrences

            Args:
                path: Path to the file (absolute path required)
                old_string: The exact string to replace (must be unique unless replace_all=True)
                new_string: The new string to replace with (must be different from old_string)
                replace_all: If True, replace all occurrences of old_string (default: False)
            """
            result = self.edit_file(validated_path, old_string, new_string, replace_all)
            if result["success"]:
                return f"Successfully edited {result['path']}"
            return f"Error: {result['error']}"

        @tool
        def find(pattern: str = "**/*", path: Optional[str] = None) -> str:
            """
            Fast file pattern matching tool that works with any codebase size.

            Supports glob patterns like "**/*.js" or "src/**/*.ts".
            Returns matching file paths sorted by modification time.
            Use this tool when you need to find files by name patterns.

            Pattern Examples:
            - *.py           : Python files in current directory
            - **/*.py        : Python files recursively
            - src/**/*.ts    : TypeScript files under src/
            - test_*.py      : Files starting with test_
            - *.{js,ts}      : JS and TS files

            Args:
                pattern: Glob pattern to match (e.g., **/*.py, src/**/*.ts)
                path: The directory to search in. If not specified, the current working
                      directory will be used. IMPORTANT: Omit this field to use the default
                      directory. DO NOT enter 'undefined' or 'null' - simply omit it for
                      the default behavior.
            """
            search_root = path or self.config.workspace_root
            result = self.glob_files(search_root, pattern)
            if result["success"]:
                return json.dumps(result["files"], indent=2)
            return f"Error: {result['error']}"

        @tool
        def search(
            pattern: str,
            validated_path: Optional[str] = None,
            recursive: bool = True,
            multiline: bool = False,
            output_mode: str = "files_with_matches",
            case_insensitive: bool = False,
            glob_filter: Optional[str] = None,
            file_type: Optional[str] = None,
            context_before: int = 0,
            context_after: int = 0,
            context: int = 0,
            head_limit: int = 0,
        ) -> str:
            """
            A powerful search tool built on ripgrep.

            ALWAYS use this tool instead of grep or rg bash commands.
            This tool is optimized for correct permissions and access.

            Features:
            - Supports full regex syntax (e.g., "log.*Error", "function\\s+\\w+")
            - Filter files with glob parameter (e.g., "*.js", "**/*.tsx") or type parameter (e.g., "js", "py", "rust")
            - Output modes: "content" shows matching lines, "files_with_matches" shows only file paths (default), "count" shows match counts
            - Pattern syntax: Uses ripgrep (not grep) - literal braces need escaping (use `interface\\{\\}` to find `interface{}` in Go code)
            - Multiline matching: By default patterns match within single lines only. For cross-line patterns like `struct \\{[\\s\\S]*?field`, use `multiline=True`

            Pattern Syntax Notes:
            - Uses ripgrep regex syntax
            - Literal braces need escaping: interface\\{\\} to find interface{}
            - Dots are metacharacters: config\\.json for literal dot

            Args:
                pattern: Regex pattern to search for in file contents
                path: File or directory to search in (default: workspace root)
                recursive: Search recursively in directories (default: True)
                multiline: Enable multiline mode where . matches newlines (rg -U --multiline-dotall). Default: False
                output_mode: Output mode: "content" shows matching lines (supports context lines), "files_with_matches" shows file paths (default), "count" shows match counts
                case_insensitive: Case insensitive search (rg -i). Default: False
                glob_filter: Glob pattern to filter files (e.g., "*.js", "*.{ts,tsx}") - maps to rg --glob
                file_type: File type to search (rg --type). Common types: js, py, rust, go, java, etc. More efficient than glob for standard file types
                context_before: Number of lines to show before each match (rg -B). Requires output_mode="content"
                context_after: Number of lines to show after each match (rg -A). Requires output_mode="content"
                context: Number of lines to show before and after each match (rg -C). Requires output_mode="content"
                head_limit: Limit output to first N lines/entries (0 = unlimited). Works across all output modes
            """
            search_path = validated_path or self.config.workspace_root
            result = self.grep_files(
                pattern=pattern,
                validated_path=search_path,
                recursive=recursive,
                multiline=multiline,
                output_mode=output_mode,
                case_insensitive=case_insensitive,
                glob_filter=glob_filter,
                file_type=file_type,
                context_before=context_before,
                context_after=context_after,
                context=context,
                head_limit=head_limit,
            )
            if result["success"]:
                return result["raw_output"] if result["raw_output"] else "No matches found."
            return f"Error: {result['error']}"

        return [read, write, edit, find, search]
