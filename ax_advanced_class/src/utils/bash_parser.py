"""
Bash Command Parser

Tree-sitter based parser for bash commands.
Extracts command structure from shell command strings.
"""

from dataclasses import dataclass, field
from typing import List, Optional

import tree_sitter_bash
from tree_sitter import Language, Parser


@dataclass
class ParsedCommand:
    """
    Represents a single parsed command from the AST.

    Attributes:
        name: The command name (e.g., "rm", "git")
        arguments: List of all arguments including flags and values
        paths: List of path-like arguments extracted from the command
        has_pipe: Whether this command is part of a pipeline
        raw_text: The original text of the command
    """

    name: str
    arguments: List[str] = field(default_factory=list)
    paths: List[str] = field(default_factory=list)
    has_pipe: bool = False
    raw_text: str = ""


class BashParser:
    """
    Tree-sitter based parser for bash commands.

    Parses shell command strings into structured ParsedCommand objects,
    extracting command names, arguments, and paths.
    """

    # Initialize tree-sitter parser once at class level
    _BASH_LANGUAGE = Language(tree_sitter_bash.language())
    _parser = Parser(_BASH_LANGUAGE)

    def parse(self, command: str) -> List[ParsedCommand]:
        """
        Parse a command string into a list of ParsedCommand objects.

        Args:
            command: The shell command string to parse

        Returns:
            List of ParsedCommand objects representing each command in the string
        """
        if not command or not command.strip():
            return []

        tree = self._parser.parse(bytes(command, "utf-8"))
        root_node = tree.root_node

        # Check for pipelines
        has_pipe = self._has_pipeline(root_node)

        # Extract all commands from the AST
        return self._extract_commands(root_node, command, has_pipe)

    def _has_pipeline(self, node) -> bool:
        """Check if the AST contains a pipeline."""
        if node.type == "pipeline":
            return True
        for child in node.children:
            if self._has_pipeline(child):
                return True
        return False

    def _extract_commands(
        self, node, source: str, has_pipe: bool
    ) -> List[ParsedCommand]:
        """Recursively extract all commands from the AST."""
        commands: List[ParsedCommand] = []

        if node.type == "command":
            parsed = self._parse_command_node(node, source, has_pipe)
            if parsed:
                commands.append(parsed)

        for child in node.children:
            commands.extend(self._extract_commands(child, source, has_pipe))

        return commands

    def _parse_command_node(
        self, node, source: str, has_pipe: bool
    ) -> Optional[ParsedCommand]:
        """Parse a single command node from the AST."""
        name = None
        arguments: List[str] = []
        paths: List[str] = []

        for child in node.children:
            if child.type == "command_name":
                name = self._get_node_text(child, source)

            elif child.type in ("word", "concatenation", "string", "raw_string", "number"):
                arg_text = self._get_node_text(child, source)
                arguments.append(arg_text)

                if self._looks_like_path(arg_text):
                    paths.append(arg_text)

            elif child.type in ("simple_expansion", "expansion"):
                arg_text = self._get_node_text(child, source)
                arguments.append(arg_text)

        if not name:
            return None

        return ParsedCommand(
            name=name,
            arguments=arguments,
            paths=paths,
            has_pipe=has_pipe,
            raw_text=self._get_node_text(node, source),
        )

    def _get_node_text(self, node, source: str) -> str:
        """Extract the text content of a node."""
        return source[node.start_byte : node.end_byte]

    def _looks_like_path(self, text: str) -> bool:
        """Check if text looks like a file path."""
        if not text:
            return False
        return (
            text.startswith("/")
            or text.startswith("./")
            or text.startswith("../")
            or text.startswith("~")
            or ("/" in text and not text.startswith("-"))
        )
