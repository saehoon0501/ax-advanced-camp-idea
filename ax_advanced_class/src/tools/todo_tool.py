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
        def todo_write(todos: list[dict], merge: bool = False) -> Command:
            """
            Update your todo list to track task progress.

            Args:
                todos: List of todo items to update or create. Each item must have:
                    - id (str): Unique identifier for the todo
                    - content (str): Imperative form (e.g., "Run tests")
                    - activeForm (str): Present continuous (e.g., "Running tests")
                    - status (str): "pending", "in_progress", or "completed"
                merge: If True, updates existing todos by matching 'id' field and
                       keeps other todos unchanged. If False, replaces entire list.

            MERGE BEHAVIOR:

            When merge=True:
            - Each todo must have an 'id' field
            - Todos with matching IDs are updated
            - Todos without matching IDs are added
            - Existing todos not in the list remain unchanged
            - Use this when updating status of specific tasks

            When merge=False:
            - Entire list is replaced with provided todos
            - Use this when creating initial todo list

            RULES:
            - Only ONE task should be in_progress at a time
            - Mark tasks complete IMMEDIATELY after finishing
            - Use merge=true to update individual tasks
            - Use merge=false to replace entire list

            TASK STATES:
            - pending: Task not yet started
            - in_progress: Currently working on (only ONE at a time)
            - completed: Task finished successfully

            Example (initial creation with merge=False):
                todo_write([
                    {"id": "1", "content": "Read progress file", "activeForm": "Reading progress file", "status": "pending"},
                    {"id": "2", "content": "Implement feature", "activeForm": "Implementing feature", "status": "pending"}
                ], merge=False)

            Example (update single task with merge=True):
                todo_write([
                    {"id": "1", "content": "Read progress file", "activeForm": "Reading progress file", "status": "completed"}
                ], merge=True)

            Returns:
                Command to update the agent's todo_list state
            """
            # Validate and normalize todos
            validated_todos = []
            for t in todos:
                if not isinstance(t, dict):
                    continue

                todo_id = t.get("id", "")
                content = t.get("content", "")
                active_form = t.get("activeForm", "")
                status = t.get("status", "pending")

                # Validate status
                if status not in ("pending", "in_progress", "completed"):
                    status = "pending"

                validated_todos.append(
                    {
                        "id": todo_id,
                        "content": content,
                        "activeForm": active_form,
                        "status": status,
                    }
                )

            # Return Command to update agent's state
            # Wrap todos with merge flag for the custom reducer
            return Command(update={"todo_list": {"todos": validated_todos, "merge": merge}})

        return [todo_write]
