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
        # Just log a summary or the token content (might be verbose)
        # _get_logger().debug(f"[Token] Node: {node}, Text: {text}")
        pass


async def process_stream_event(
    event_stream: Any,  # StreamEvent from LangGraph
    chain_stack: List[Dict[str, Any]],
) -> None:
    """Orchestrator function that routes stream events to appropriate handlers.
    
    Args:
        event_stream: The raw event stream from LangGraph
        chain_stack: Mutable list tracking the chain stack state
    """
    event_type = event_stream.get("event") or ""
    node = (
        event_stream.get("langgraph_node")
        or event_stream.get("name")
        or event_stream.get("node_name")
        or "unknown"
    )
    data = event_stream.get("data", {}) or {}

    _get_logger().debug(f"Processing event: {event_type} for node: {node}")

    # Route to appropriate event handler
    if event_type == "on_chain_start":
        await handle_chain_start_event(node, chain_stack)

    elif event_type == "on_tool_start":
        await handle_tool_start_event(node, data, chain_stack, event_stream)

    elif event_type == "on_chain_end":
        await handle_chain_end_event(node, data, chain_stack)

    elif event_type in ("on_chat_model_stream", "on_llm_stream"):
        await handle_streaming_token_event(data, chain_stack, node)

