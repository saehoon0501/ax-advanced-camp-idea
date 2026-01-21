"""
File Reader Utility

Reads text files (.md and .json) from relative paths.
"""

import json
from pathlib import Path
from typing import Union


class FileReader:
    """
    Utility for reading text files at relative paths.

    Supports reading .md files as plain text and .json files as parsed data.
    """

    SUPPORTED_EXTENSIONS = {".md", ".json"}

    def __init__(self, base_path: Union[str, Path, None] = None):
        """
        Initialize the FileReader.

        Args:
            base_path: Base directory for resolving relative paths.
                      Defaults to current working directory.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def read(self, relative_path: str) -> Union[str, dict, list]:
        """
        Read a file at the given relative path.

        Args:
            relative_path: Path relative to base_path

        Returns:
            For .md files: string content
            For .json files: parsed JSON (dict or list)

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file extension is not supported
            json.JSONDecodeError: If .json file has invalid JSON
        """
        path = self.base_path / relative_path
        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension '{extension}'. "
                f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = path.read_text(encoding="utf-8")

        if extension == ".json":
            return json.loads(content)

        return content
