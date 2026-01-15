"""
Mock message data for testing RollingWindowMiddleware.
Simulates a long-running coding agent session implementing "feature-005: Message Streaming".
"""

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)


SYSTEM_PROMPT = SystemMessage(
    content="""You are a Software Engineer, an expert coding assistant. You help implement features, debug code, and run tests.
Current Task: Implement feature-005 - Message Streaming
Repository: /workspace/chat-app
Always verify changes with tests before completing."""
)

FEATURE_SPEC_MESSAGE = HumanMessage(
    content="""Implement Message Streaming (feature-005):
- Add WebSocket support for real-time message delivery
- Implement streaming response for AI completions
- Add progress indicators during long operations
- Ensure backward compatibility with existing REST endpoints"""
)

# Simulated tool calls and outputs from a long coding session
MOCK_CONVERSATION_HISTORY = [
    SYSTEM_PROMPT,
    FEATURE_SPEC_MESSAGE,
    # Turn 1: Initial exploration
    AIMessage(
        content="I'll start by examining the current message handling implementation.",
        tool_calls=[
            {
                "id": "call_1",
                "name": "read_file",
                "args": {"path": "src/api/messages.py"},
            }
        ],
    ),
    ToolMessage(
        content="""# src/api/messages.py - 500 lines of code
class MessageHandler:
    def __init__(self, db):
        self.db = db

    async def send_message(self, user_id, content):
        message = Message(user_id=user_id, content=content)
        await self.db.save(message)
        return message

    async def get_messages(self, channel_id, limit=50):
        return await self.db.query(
            "SELECT * FROM messages WHERE channel_id = ? ORDER BY created_at DESC LIMIT ?",
            [channel_id, limit]
        )
# ... (truncated 450 more lines with helper methods, validation, etc.)
""",
        tool_call_id="call_1",
    ),
    # Turn 2: Read another file
    AIMessage(
        content="Now let me check the WebSocket configuration.",
        tool_calls=[
            {
                "id": "call_2",
                "name": "read_file",
                "args": {"path": "src/websocket/config.py"},
            }
        ],
    ),
    ToolMessage(
        content="""# src/websocket/config.py
WEBSOCKET_CONFIG = {
    "host": "0.0.0.0",
    "port": 8765,
    "max_connections": 1000,
    "ping_interval": 30,
    "ping_timeout": 10,
}

class WebSocketManager:
    def __init__(self):
        self.connections = {}

    async def connect(self, websocket, user_id):
        self.connections[user_id] = websocket

    async def disconnect(self, user_id):
        if user_id in self.connections:
            del self.connections[user_id]

    async def broadcast(self, message):
        for ws in self.connections.values():
            await ws.send(message)
""",
        tool_call_id="call_2",
    ),
    # Turn 3: Run tests (long output)
    AIMessage(
        content="Let me run the existing tests to understand the current state.",
        tool_calls=[
            {"id": "call_3", "name": "run_command", "args": {"command": "npm test"}}
        ],
    ),
    ToolMessage(
        content="""> chat-app@1.0.0 test
> jest --coverage

PASS  tests/api/messages.test.js
  MessageHandler
    ✓ should send message successfully (45 ms)
    ✓ should retrieve messages by channel (23 ms)
    ✓ should handle invalid user_id (12 ms)
    ✓ should paginate results correctly (34 ms)

PASS  tests/websocket/connection.test.js
  WebSocketManager
    ✓ should establish connection (67 ms)
    ✓ should handle disconnection gracefully (21 ms)
    ✓ should broadcast to all connections (89 ms)

PASS  tests/utils/validation.test.js
  Validators
    ✓ should validate message content (5 ms)
    ✓ should reject empty messages (3 ms)
    ✓ should sanitize HTML (8 ms)

Test Suites: 3 passed, 3 total
Tests:       10 passed, 10 total
Snapshots:   0 total
Time:        4.523 s

--------------------------|---------|----------|---------|---------|-------------------
File                      | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
--------------------------|---------|----------|---------|---------|-------------------
All files                 |   78.45 |    72.31 |   85.00 |   79.12 |
 src/api                  |   82.14 |    75.00 |   88.89 |   83.33 |
  messages.py             |   82.14 |    75.00 |   88.89 |   83.33 | 45-52,78-85
 src/websocket            |   75.00 |    68.42 |   80.00 |   74.07 |
  config.py               |   75.00 |    68.42 |   80.00 |   74.07 | 23-31,56-67
 src/utils                |   78.95 |    73.33 |   85.71 |   80.00 |
  validation.py           |   78.95 |    73.33 |   85.71 |   80.00 | 34-38
--------------------------|---------|----------|---------|---------|-------------------
""",
        tool_call_id="call_3",
    ),
    # Turn 4: Read big file (very long output - main pruning target)
    AIMessage(
        content="I need to examine the main application file.",
        tool_calls=[
            {"id": "call_4", "name": "read_file", "args": {"path": "src/app.py"}}
        ],
    ),
    ToolMessage(
        content="# src/app.py - Main Application\n" + "x" * 5000 + "\n# End of file",
        tool_call_id="call_4",
    ),
    # Turn 5: User clarification
    HumanMessage(
        content="Focus on the streaming part first, we can add WebSocket later."
    ),
    AIMessage(
        content="Understood. I'll implement the streaming response first. Let me create the streaming handler.",
        tool_calls=[
            {
                "id": "call_5",
                "name": "write_file",
                "args": {"path": "src/api/streaming.py", "content": "..."},
            }
        ],
    ),
    ToolMessage(
        content="File written successfully: src/api/streaming.py", tool_call_id="call_5"
    ),
    # Turn 6: More file reads
    AIMessage(
        content="Let me check if there are any existing streaming utilities.",
        tool_calls=[
            {"id": "call_6", "name": "search_files", "args": {"pattern": "stream"}}
        ],
    ),
    ToolMessage(
        content="""Found 15 matches:
src/utils/stream_buffer.py:12: class StreamBuffer:
src/utils/stream_buffer.py:45: def create_stream():
src/api/responses.py:78: async def stream_response(data):
src/api/responses.py:102: class StreamingResponse:
src/tests/test_streaming.py:5: def test_stream_buffer():
...(10 more matches)""",
        tool_call_id="call_6",
    ),
    # Turn 7-10: More back and forth
    AIMessage(
        content="Good, there's already a StreamBuffer. Let me read it.",
        tool_calls=[
            {
                "id": "call_7",
                "name": "read_file",
                "args": {"path": "src/utils/stream_buffer.py"},
            }
        ],
    ),
    ToolMessage(
        content="""# src/utils/stream_buffer.py
import asyncio
from typing import AsyncIterator, Generic, TypeVar

T = TypeVar('T')

class StreamBuffer(Generic[T]):
    def __init__(self, max_size: int = 1000):
        self.buffer = asyncio.Queue(maxsize=max_size)
        self._closed = False

    async def write(self, item: T) -> None:
        if self._closed:
            raise RuntimeError("Buffer is closed")
        await self.buffer.put(item)

    async def read(self) -> T:
        return await self.buffer.get()

    async def __aiter__(self) -> AsyncIterator[T]:
        while not self._closed or not self.buffer.empty():
            try:
                yield await asyncio.wait_for(self.read(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

    def close(self) -> None:
        self._closed = True
""",
        tool_call_id="call_7",
    ),
    # Recent turns (should be preserved)
    AIMessage(
        content="Now I'll integrate this with the AI completion endpoint.",
        tool_calls=[
            {
                "id": "call_8",
                "name": "read_file",
                "args": {"path": "src/api/completions.py"},
            }
        ],
    ),
    ToolMessage(
        content="""# src/api/completions.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 1000
    temperature: float = 0.7

@router.post("/completions")
async def create_completion(request: CompletionRequest):
    # Current implementation returns full response
    response = await ai_client.complete(
        prompt=request.prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature
    )
    return {"completion": response}
""",
        tool_call_id="call_8",
    ),
    # Latest turn (must be preserved)
    HumanMessage(content="Add the streaming endpoint now."),
    AIMessage(
        content="I'll add a new streaming endpoint to the completions API.",
        tool_calls=[
            {
                "id": "call_9",
                "name": "edit_file",
                "args": {"path": "src/api/completions.py", "changes": "..."},
            }
        ],
    ),
]


# For testing: calculate approximate token counts
def get_mock_token_count(messages):
    """Approximate token count (1 char = 1 token for testing)."""
    return sum(len(m.content) for m in messages)
