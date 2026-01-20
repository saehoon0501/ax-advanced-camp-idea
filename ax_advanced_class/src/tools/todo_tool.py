"""
TodoWrite Tool

Allows agents to manage their task list by updating state via Command.

This tool enables agents to track their progress through a todo list,
following the same pattern as Claude Code's TodoWrite tool.

Usage:
- Agents call todo_write with the COMPLETE updated list of todos
- Only ONE task should be in_progress at a time
- Mark tasks complete IMMEDIATELY after finishing
"""

from typing import Optional
from langgraph.types import Command
from langchain_core.tools import tool


class TodoWriteTool:
    """
    Tool for managing the agent's todo list.

    Updates the agent's state by returning a Command with the new todo list.
    The agent should send the COMPLETE updated list each time (replace semantics).

    Each todo item has:
    - content: Imperative form (e.g., "Run tests")
    - activeForm: Present continuous form (e.g., "Running tests")
    - status: "pending" | "in_progress" | "completed"
    """

    # Tool names exposed by this class
    _TOOL_NAMES = ("todo_write",)

    @staticmethod
    def get_tool_names() -> tuple[str, ...]:
        """
        Return names of all LangChain tools provided by this class.
        """
        return TodoWriteTool._TOOL_NAMES

    def get_langchain_tools(self) -> list:
        """
        Get LangChain tool wrappers for this tool.
        """

        @tool
        def todo_write(todos: list[dict]) -> Command:
            """
            Update your todo list to track task progress.

            Send the COMPLETE updated list of todos each time you call this tool.
            The entire list will be replaced with your new list.

            RULES:
            - Only ONE task should be in_progress at a time
            - Mark tasks complete IMMEDIATELY after finishing
            - Always include content, activeForm, and status for each todo
            - Use this tool BEFORE starting work on a new task

            TASK STATES:
            - pending: Task not yet started
            - in_progress: Currently working on (only ONE at a time)
            - completed: Task finished successfully

            Args:
                todos: Complete updated list of todo items. Each item must have:
                    - content (str): Imperative form (e.g., "Run tests")
                    - activeForm (str): Present continuous (e.g., "Running tests")
                    - status (str): "pending", "in_progress", or "completed"

            Example:
                todo_write([
                    {"content": "Read progress file", "activeForm": "Reading progress file", "status": "completed"},
                    {"content": "Implement feature", "activeForm": "Implementing feature", "status": "in_progress"},
                    {"content": "Run tests", "activeForm": "Running tests", "status": "pending"}
                ])

            Returns:
                Command to update the agent's todo_list state
            """
            # Validate and normalize todos
            validated_todos = []
            for t in todos:
                if not isinstance(t, dict):
                    continue

                content = t.get("content", "")
                active_form = t.get("activeForm", "")
                status = t.get("status", "pending")

                # Validate status
                if status not in ("pending", "in_progress", "completed"):
                    status = "pending"

                validated_todos.append({
                    "content": content,
                    "activeForm": active_form,
                    "status": status,
                })

            # Return Command to update agent's state
            return Command(update={"todo_list": validated_todos})

        return [todo_write]
