import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

# Configure a simple logger for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def handle_chain_start_event(
    node: str, chain_stack: List[Dict[str, Any]]
) -> None:
    """Handle chain start events.
    
    Args:
        node: The node name
        chain_stack: Mutable list tracking the chain stack state
    """
    logger.info(f"[Chain Start] Node: {node}")
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
    logger.info(f"[Tool Start] Tool: {tool_name}, Input: {tool_input}")


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
    logger.info(f"[Chain End] Node: {node}, Output: {output}")


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
        text = chunk.content
    elif isinstance(chunk, dict):
        text = chunk.get("content", "")
    elif isinstance(chunk, str):
        text = chunk
    
    if text:
        # Just log a summary or the token content (might be verbose)
        # For this implementation, we'll just print/log it if it's not empty
        # logger.debug(f"[Token] Node: {node}, Text: {text}")
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

    logger.debug(f"Processing event: {event_type} for node: {node}")

    # Route to appropriate event handler
    if event_type == "on_chain_start":
        await handle_chain_start_event(node, chain_stack)

    elif event_type == "on_tool_start":
        await handle_tool_start_event(node, data, chain_stack, event_stream)

    elif event_type == "on_chain_end":
        await handle_chain_end_event(node, data, chain_stack)

    elif event_type in ("on_chat_model_stream", "on_llm_stream"):
        await handle_streaming_token_event(data, chain_stack, node)

