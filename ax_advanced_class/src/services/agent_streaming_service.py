"""
Agent Streaming Service

Wraps the orchestrator and provides a consistent event format for the UI layer.
Handles raw LangGraph events and transforms them into semantic StreamEvent objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Literal, Optional

from ax_advanced_class.src.orchestrator import LongRunningOrchestrator


# Only emit events from these nodes
ALLOWED_NODES = {"router", "initializer", "coding"}


EventType = Literal[
    "thinking",           # LLM is processing
    "token",              # Streaming text token
    "tool_call",          # Tool is being called
    "tool_result",        # Tool returned result
    "agent_transition",   # Moving to a new agent
    "message",            # Complete message from agent
    "permission_required", # Interrupt - needs user approval
    "complete",           # Workflow finished
    "error",              # Error occurred
]


@dataclass
class StreamEvent:
    """Consistent event format for the UI layer."""

    type: EventType
    content: str = ""
    node: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class AgentStreamingService:
    """
    Service that wraps the orchestrator and provides consistent streaming events.

    Transforms raw LangGraph events into semantic StreamEvent objects that
    the UI layer can easily consume and display.
    """

    def __init__(
        self,
        orchestrator: LongRunningOrchestrator,
        config: Optional[dict] = None,
    ):
        self.orchestrator = orchestrator
        self.config = config or {"configurable": {"thread_id": "default"}}
        self._pending_interrupt = None
        # Store params for resume
        self._last_project_name: Optional[str] = None
        self._last_project_description: Optional[str] = None
        self._last_repository_path: Optional[str] = None

    async def astream(
        self,
        user_message: str,
        project_name: str,
        project_description: str,
        repository_path: str,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream events for a user message.

        Args:
            user_message: The user's input message
            project_name: Name of the project
            project_description: Description of the project
            repository_path: Path to the repository

        Yields:
            StreamEvent objects for the UI to display
        """
        # Store for potential resume
        self._last_project_name = project_name
        self._last_project_description = project_description
        self._last_repository_path = repository_path

        async for event in self._arun_stream(
            user_message=user_message,
            project_name=project_name,
            project_description=project_description,
            repository_path=repository_path,
        ):
            yield event

    async def aresume(self, approved: bool) -> AsyncGenerator[StreamEvent, None]:
        """
        Resume from an interrupt with user's approval decision.

        Args:
            approved: Whether the user approved the action

        Yields:
            StreamEvent objects for the UI to display
        """
        async for event in self._arun_stream(resume_value=approved):
            yield event

    async def _arun_stream(
        self,
        user_message: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
        repository_path: Optional[str] = None,
        resume_value: Optional[bool] = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Internal method that handles streaming and interrupt detection."""
        # Use stored values for resume
        project_name = project_name or self._last_project_name or "default-project"
        project_description = project_description or self._last_project_description or "A default project"
        repository_path = repository_path or self._last_repository_path or "./workspace"

        try:
            async for raw_event in self.orchestrator.astream_events(
                project_name=project_name,
                project_description=project_description,
                repository_path=repository_path,
                config=self.config,
                resume_value=resume_value,
                user_message=user_message,
            ):
                stream_event = self._transform_event(raw_event)
                if stream_event:
                    yield stream_event

            # Check for interrupts after streaming completes
            interrupt_event = self._check_for_interrupt()
            if interrupt_event:
                yield interrupt_event
            else:
                # Workflow completed
                yield StreamEvent(type="complete", content="Session complete.")

        except Exception as e:
            yield StreamEvent(
                type="error",
                content=str(e),
                metadata={"exception_type": type(e).__name__},
            )

    def _transform_event(self, raw_event: Dict[str, Any]) -> Optional[StreamEvent]:
        """
        Transform a raw LangGraph event into a StreamEvent.

        Args:
            raw_event: Raw event from LangGraph astream_events

        Returns:
            StreamEvent or None if the event should be filtered out
        """
        event_type = raw_event.get("event", "")
        node = (
            raw_event.get("langgraph_node")
            or raw_event.get("name")
            or raw_event.get("node_name")
            or "unknown"
        )
        data = raw_event.get("data", {}) or {}

        # Filter out events from nodes not in ALLOWED_NODES
        if node not in ALLOWED_NODES:
            return None

        # Route to appropriate transformation
        if event_type == "on_chain_start":
            return self._transform_chain_start(node, data)
        elif event_type == "on_chain_end":
            return self._transform_chain_end(node, data)
        elif event_type == "on_tool_start":
            return self._transform_tool_start(node, data, raw_event)
        elif event_type == "on_tool_end":
            return self._transform_tool_end(node, data)
        elif event_type in ("on_chat_model_stream", "on_llm_stream"):
            return self._transform_token(node, data)

        # Filter out other event types
        return None

    def _transform_chain_start(self, node: str, data: Dict[str, Any]) -> StreamEvent:
        """Transform on_chain_start event."""
        return StreamEvent(
            type="thinking",
            content=f"Processing in {node}...",
            node=node,
        )

    def _transform_chain_end(self, node: str, data: Dict[str, Any]) -> Optional[StreamEvent]:
        """Transform on_chain_end event."""
        output = data.get("output", {})

        # Check for messages in output (agent responses)
        if isinstance(output, dict) and "messages" in output:
            messages = output["messages"]
            if messages:
                last_msg = messages[-1] if isinstance(messages, list) else messages
                content = self._extract_content(last_msg)

                # Check if it's a router transition
                if node == "router" and "[Router]" in content:
                    return StreamEvent(
                        type="agent_transition",
                        content=content,
                        node=node,
                        metadata={"next_agent": output.get("next_agent")},
                    )

                return StreamEvent(
                    type="message",
                    content=content,
                    node=node,
                )

        return None

    def _transform_tool_start(
        self, node: str, data: Dict[str, Any], raw_event: Dict[str, Any]
    ) -> StreamEvent:
        """Transform on_tool_start event."""
        tool_name = data.get("name") or raw_event.get("name") or "unknown_tool"
        tool_input = data.get("input") or raw_event.get("tool_input") or {}

        # Truncate tool input for display
        input_preview = str(tool_input)[:100]
        if len(str(tool_input)) > 100:
            input_preview += "..."

        return StreamEvent(
            type="tool_call",
            content=f"Calling {tool_name}",
            node=node,
            metadata={
                "tool_name": tool_name,
                "tool_input": tool_input,
                "input_preview": input_preview,
            },
        )

    def _transform_tool_end(self, node: str, data: Dict[str, Any]) -> StreamEvent:
        """Transform on_tool_end event."""
        output = data.get("output", "")

        # Truncate output for display
        output_str = str(output)
        output_preview = output_str[:200]
        if len(output_str) > 200:
            output_preview += "..."

        return StreamEvent(
            type="tool_result",
            content=output_preview,
            node=node,
            metadata={
                "full_output": output_str,
                "output_preview": output_preview,
            },
        )

    def _transform_token(self, node: str, data: Dict[str, Any]) -> Optional[StreamEvent]:
        """Transform streaming token event."""
        chunk = data.get("chunk")
        if not chunk:
            return None

        text = self._extract_content(chunk)
        if not text:
            return None

        return StreamEvent(
            type="token",
            content=text,
            node=node,
        )

    def _extract_content(self, obj: Any) -> str:
        """Extract text content from various object types."""
        if hasattr(obj, "content"):
            content = obj.content
            if isinstance(content, list):
                # Handle multimodal content
                return "".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                )
            elif isinstance(content, str):
                return content
            else:
                return str(content) if content else ""
        elif isinstance(obj, dict):
            content = obj.get("content", "")
            if isinstance(content, list):
                return str(content)
            return content
        elif isinstance(obj, str):
            return obj
        return ""

    def _check_for_interrupt(self) -> Optional[StreamEvent]:
        """Check if there's a pending interrupt that needs user approval."""
        state_snapshot = self.orchestrator.workflow.get_state(self.config)

        if state_snapshot and state_snapshot.tasks:
            for task in state_snapshot.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    for interrupt_data in task.interrupts:
                        interrupt_value = (
                            interrupt_data.value
                            if hasattr(interrupt_data, "value")
                            else interrupt_data
                        )

                        if isinstance(interrupt_value, dict):
                            question = interrupt_value.get("question", "Permission required")
                        else:
                            question = str(interrupt_value)

                        return StreamEvent(
                            type="permission_required",
                            content=question,
                            metadata={"interrupt_data": interrupt_value},
                        )

        return None
