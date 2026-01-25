"""
Agent Streaming Service

Wraps the orchestrator and provides a consistent event format for the UI layer.
Handles raw LangGraph events and transforms them into semantic StreamEvent objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Literal, Optional
from collections.abc import Iterable

from ax_advanced_class.src.orchestrator import LongRunningOrchestrator


EventType = Literal[
    "thinking",  # LLM is processing
    "token",  # Streaming text token
    "tool_call",  # Tool is being called
    "tool_result",  # Tool returned result
    "agent_transition",  # Moving to a new agent
    "message",  # Complete message from agent
    "permission_required",  # Interrupt - needs user approval
    "complete",  # Workflow finished
    "error",  # Error occurred
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
        self._last_message_history: Optional[list] = None

    async def astream(
        self,
        user_message: str,
        message_history: Optional[list] = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream events for a user message.

        Args:
            user_message: The user's input message
            message_history: Optional conversation history (list of {role, content} dicts)

        Yields:
            StreamEvent objects for the UI to display
        """
        self._last_message_history = message_history

        async for event in self._arun_stream(
            user_message=user_message,
            message_history=message_history,
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
        resume_value: Optional[bool] = None,
        message_history: Optional[list] = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Internal method that handles streaming and interrupt detection."""
        message_history = message_history or getattr(self, "_last_message_history", None)

        raw_stream = self.orchestrator.astream_events(
            config=self.config,
            resume_value=resume_value,
            user_message=user_message,
            message_history=message_history,
        )
        try:
            async for raw_event in raw_stream:
                stream_event = self._transform_event(raw_event)
                if stream_event:
                    yield stream_event

            # Workflow completed
            yield StreamEvent(type="complete", content="Session complete.")

        except Exception as e:
            yield StreamEvent(
                type="error",
                content=str(e),
                metadata={"exception_type": type(e).__name__},
            )
        finally:
            if hasattr(raw_stream, "aclose"):
                try:
                    await raw_stream.aclose()
                except Exception:
                    pass

    def _transform_event(self, raw_event: Dict[str, Any]) -> Optional[StreamEvent]:
        """
        Transform a raw LangGraph event into a StreamEvent.

        Args:
            raw_event: Raw event from LangGraph astream_events

        Returns:
            StreamEvent or None if the event should be filtered out
        """
        # Handle interrupts directly when they appear in the event stream
        if "__interrupt__" in raw_event:
            return self._interrupt_event_from_value(raw_event["__interrupt__"])

        event_type = raw_event.get("event", "")
        metadata = raw_event.get("metadata", {})
        node = (metadata.get("langgraph_node") if isinstance(metadata, dict) else "") or ""
        run_id = str(raw_event.get("run_id") or "")
        data = raw_event.get("data", {}) or {}

        if event_type == "on_chain_stream":
            chunk = data.get("chunk")
            if isinstance(chunk, dict) and "__interrupt__" in chunk:
                return self._interrupt_event_from_value(chunk["__interrupt__"])

        # Route to appropriate transformation
        stream_event: Optional[StreamEvent] = None
        if event_type == "on_chain_start":
            stream_event = self._transform_chain_start(node, data)
        elif event_type == "on_chain_end":
            stream_event = self._transform_chain_end(node, data)
        elif event_type == "on_tool_start":
            stream_event = self._transform_tool_start(node, data, raw_event)
        elif event_type == "on_tool_end":
            stream_event = self._transform_tool_end(node, data)
        elif event_type in ("on_chat_model_stream", "on_llm_stream"):
            stream_event = self._transform_token(node, data, raw_event)
        elif event_type in ("on_chat_model_end", "on_llm_end"):
            stream_event = self._transform_model_end(node, data, raw_event)

        # Filter out other event types
        if stream_event:
            stream_event.metadata.setdefault("run_id", run_id)
        return stream_event

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

        # Some LangGraph versions surface interrupts inside chain output
        if isinstance(output, dict) and "__interrupt__" in output:
            return self._interrupt_event_from_value(output["__interrupt__"])

        # Check for router transition based on structured output
        if node == "router" and isinstance(output, dict) and "next_agent" in output:
            return StreamEvent(
                type="agent_transition",
                content="",
                node=node,
                metadata={"next_agent": output.get("next_agent")},
            )

        return None

    def _transform_model_end(self, node: str, data: Dict[str, Any], raw_event: Dict[str, Any]) -> Optional[StreamEvent]:
        """Transform on_chat_model_end/on_llm_end event."""
        output = data.get("output")
        if not output:
            return None

        content = self._extract_content(output)
        if not content:
            return None

        return StreamEvent(
            type="message",
            content=content,
            node=node,
            metadata={
                "run_id": raw_event.get("run_id", ""),
            },
        )

    def _transform_tool_start(self, node: str, data: Dict[str, Any], raw_event: Dict[str, Any]) -> StreamEvent:
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

    def _transform_token(self, node: str, data: Dict[str, Any], raw_event: Dict[str, Any]) -> Optional[StreamEvent]:
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
            metadata={
                "run_id": raw_event.get("run_id", ""),
            },
        )

    def _extract_content(self, obj: Any) -> str:
        """Extract text content from various object types."""

        def _join_blocks(blocks: Iterable) -> str:
            parts = []
            for item in blocks:
                if isinstance(item, dict):
                    parts.append(str(item.get("text", "") or ""))
                elif hasattr(item, "text"):
                    text = getattr(item, "text")
                    parts.append(str(text) if text else "")
                else:
                    parts.append(str(item))
            return "".join(parts)

        def _is_block_sequence(value: Any) -> bool:
            return isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict))

        if hasattr(obj, "content"):
            content = obj.content
            if isinstance(content, str):
                return content
            if _is_block_sequence(content):
                return _join_blocks(content)
            return str(content) if content else ""
        elif isinstance(obj, dict):
            content = obj.get("content", "")
            if isinstance(content, str):
                return content
            if _is_block_sequence(content):
                return _join_blocks(content)
            return str(content) if content else ""
        elif isinstance(obj, str):
            return obj
        if _is_block_sequence(obj):
            return _join_blocks(obj)
        return ""

    def _interrupt_event_from_value(self, interrupt_value: Any) -> StreamEvent:
        """Normalize interrupt payloads into a permission_required StreamEvent."""
        # Interrupts can be tuples/lists of Interrupt objects
        value = interrupt_value
        if isinstance(value, (list, tuple)) and value:
            value = value[0]

        if hasattr(value, "value"):
            value = value.value

        if isinstance(value, dict):
            question = value.get("question", "Permission required")
        else:
            question = str(value)

        message = self._format_permission_message(question)
        return StreamEvent(
            type="permission_required",
            content=message,
            metadata={"interrupt_data": interrupt_value},
        )

    def _format_permission_message(self, question: str) -> str:
        """Make approval prompts concise and gentle."""
        text = (question or "").strip()
        if text.lower().startswith("approval needed:"):
            return text

        for prefix in ("permission denied:", "permission required:", "permission denied", "permission required"):
            if text.lower().startswith(prefix):
                text = text[len(prefix) :].strip()
                break

        if not text:
            text = "This action needs your approval."

        return f"Approval needed: {text}"
