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

from langchain.tools import ToolRuntime
from langgraph.types import Command
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage


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
        def todo_write(runtime: ToolRuntime, todos: list[dict], merge: bool = False) -> Command:
            """
            Update your todo list to track task progress.

            Args:
                todos: List of todo items. Each item must have:
                    - id (str): Unique identifier
                    - content (str): Imperative form (e.g., "Run tests")
                    - activeForm (str): Present continuous (e.g., "Running tests")
                    - status (str): "pending", "in_progress", or "completed"
                merge: If True, updates/adds by id, keeps others. If False, replaces entire list.

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
            # Include ToolMessage to satisfy LangGraph validation
            return Command(
                update={
                    "todo_list": {"todos": validated_todos, "merge": merge},
                    "messages": [
                        ToolMessage(
                            content=f"Todo list updated ({len(validated_todos)} items)",
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                }
            )

        return [todo_write]
