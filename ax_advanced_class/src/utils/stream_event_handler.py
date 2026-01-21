import json
import logging
import os
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

# Module-level logger reference
_current_logger: Optional[logging.Logger] = None


def init_session_logger(session_id: str) -> logging.Logger:
    """
    Initialize a file logger for a specific session.

    Args:
        session_id: Unique session identifier

    Returns:
        Configured logger for this session
    """
    global _current_logger

    # Create a unique logger name for this session
    logger_name = f"stream_event_handler.{session_id}"
    logger = logging.getLogger(logger_name)

    # Clear any existing handlers
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Create log file with dd_mm_yyyy_session format
    date_str = datetime.now().strftime("%d_%m_%Y")
    log_file = os.path.join(logs_dir, f"{date_str}_{session_id}.log")

    # File handler - logs everything to file
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    # Prevent propagation to root logger (no console output)
    logger.propagate = False

    _current_logger = logger
    return logger


def _get_logger() -> logging.Logger:
    """Get the current session logger or a default one."""
    global _current_logger
    if _current_logger is None:
        # Fallback to default logger if session not initialized
        return init_session_logger("default")
    return _current_logger


def _safe_serialize(obj: Any, max_length: int = 500) -> str:
    """Safely serialize an object to JSON string for logging.

    Args:
        obj: Object to serialize
        max_length: Maximum length of serialized string (0 for no limit)

    Returns:
        JSON string representation or repr() fallback
    """
    try:
        # Handle common LangChain message types
        if hasattr(obj, "dict"):
            serialized = json.dumps(obj.dict(), default=str, ensure_ascii=False)
        elif hasattr(obj, "__dict__"):
            serialized = json.dumps(obj.__dict__, default=str, ensure_ascii=False)
        else:
            serialized = json.dumps(obj, default=str, ensure_ascii=False)

        if max_length > 0 and len(serialized) > max_length:
            return serialized[:max_length] + "...[truncated]"
        return serialized
    except (TypeError, ValueError):
        result = repr(obj)
        if max_length > 0 and len(result) > max_length:
            return result[:max_length] + "...[truncated]"
        return result


def _log_raw_event(event_stream: Dict[str, Any]) -> None:
    """Log raw event with all fields for debugging.

    Based on LangChain BaseStreamEvent schema:
    - event: Event type (on_chain_start, on_tool_end, etc.)
    - name: Name of the runnable
    - run_id: Unique UUID for the run
    - tags: List of tags
    - metadata: Contains langgraph_node, langgraph_step, etc.
    - data: Payload (input/chunk/output depending on lifecycle)
    """
    # Skip noisy streaming events
    event_type = event_stream.get("event", "")
    if event_type in ("on_chat_model_stream", "on_llm_stream", "on_chain_stream"):
        return

    logger = _get_logger()
    name = event_stream.get("name", "")
    run_id = event_stream.get("run_id", "")
    tags = event_stream.get("tags", [])
    metadata = event_stream.get("metadata", {})
    data = event_stream.get("data", {})

    # Extract LangGraph-specific metadata
    langgraph_node = metadata.get("langgraph_node", "") if isinstance(metadata, dict) else ""
    langgraph_step = metadata.get("langgraph_step", "") if isinstance(metadata, dict) else ""

    # Log structured summary
    logger.info(
        f"[RAW EVENT] "
        f"event={event_type} | "
        f"name={name} | "
        f"node={langgraph_node} | "
        f"step={langgraph_step} | "
        f"run_id={str(run_id)[:8]}..."
    )

    # Log data payload separately (no truncation)
    if data:
        data_full = _safe_serialize(data, max_length=0)
        logger.info(f"[RAW EVENT DATA] {data_full}")

async def handle_chain_start_event(
    node: str, chain_stack: List[Dict[str, Any]]
) -> None:
    """Handle chain start events.
    
    Args:
        node: The node name
        chain_stack: Mutable list tracking the chain stack state
    """
    _get_logger().info(f"[Chain Start] Node: {node}")
    chain_stack.append({"node": node})


async def handle_tool_start_event(
    node: str,
    data: Dict[str, Any],
    chain_stack: List[Dict[str, Any]],
    event_stream: Dict[str, Any],
) -> None:
    """Handle tool start events.
    
    Args:
        node: The node name
        data: The event data
        chain_stack: The chain stack state
        event_stream: The raw event stream
    """
    tool_name = data.get("name") or event_stream.get("name") or "unknown_tool"
    tool_input = data.get("input") or event_stream.get("tool_input") or {}
    _get_logger().info(f"[Tool Start] Tool: {tool_name}, Input: {tool_input}")


async def handle_chain_end_event(
    node: str,
    data: Dict[str, Any],
    chain_stack: List[Dict[str, Any]],
) -> None:
    """Handle chain end events.
    
    Args:
        node: The node name
        data: The event data
        chain_stack: Mutable list tracking the chain stack state
    """
    if chain_stack:
        # Ideally we should pop the matching node, but for simple logging we just pop
        chain_stack.pop()
    
    output = data.get("output")
    _get_logger().info(f"[Chain End] Node: {node}, Output: {output}")


async def handle_streaming_token_event(
    data: Dict[str, Any],
    chain_stack: List[Dict[str, Any]],
    node: str,
) -> None:
    """Handle streaming token events (on_chat_model_stream, on_llm_stream).

    Args:
        data: The event data
        chain_stack: The chain stack state
        node: The node name
    """
    chunk = data.get("chunk")
    # Simplify chunk text extraction
    text = ""
    if hasattr(chunk, "content"):
        content = chunk.content
        # Handle list content (multimodal)
        if isinstance(content, list):
            text = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        elif isinstance(content, str):
            text = content
        else:
            text = str(content) if content else ""
    elif isinstance(chunk, dict):
        text = chunk.get("content", "")
        if isinstance(text, list):
            text = str(text)
    elif isinstance(chunk, str):
        text = chunk

    if text and isinstance(text, str):
        _get_logger().debug(f"[Token] Node: {node}, Text: {text[:100]}")


async def handle_tool_end_event(
    node: str,
    data: Dict[str, Any],
) -> None:
    """Handle tool end events.

    Args:
        node: The node name
        data: The event data
    """
    output = data.get("output", "")
    output_str = str(output)[:500]  # Truncate for logging
    _get_logger().info(f"[Tool End] Node: {node}, Output: {output_str}")


async def process_stream_event(
    event_stream: Any,  # StreamEvent from LangGraph
    chain_stack: List[Dict[str, Any]],
) -> None:
    """Orchestrator function that routes stream events to appropriate handlers.

    Args:
        event_stream: The raw event stream from LangGraph
        chain_stack: Mutable list tracking the chain stack state
    """
    # Log raw event first for debugging
    _log_raw_event(event_stream)

    event_type = event_stream.get("event") or ""
    metadata = event_stream.get("metadata", {}) or {}

    # Prefer langgraph_node from metadata (more reliable)
    node = (
        metadata.get("langgraph_node")
        or event_stream.get("name")
        or "unknown"
    )
    data = event_stream.get("data", {}) or {}

    # Route to appropriate event handler
    if event_type == "on_chain_start":
        await handle_chain_start_event(node, chain_stack)

    elif event_type == "on_chain_end":
        await handle_chain_end_event(node, data, chain_stack)

    elif event_type == "on_tool_start":
        await handle_tool_start_event(node, data, chain_stack, event_stream)

    elif event_type == "on_tool_end":
        await handle_tool_end_event(node, data)

    elif event_type in ("on_chat_model_stream", "on_llm_stream"):
        await handle_streaming_token_event(data, chain_stack, node)

