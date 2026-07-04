import asyncio
from unittest.mock import patch
from starlette.testclient import TestClient
from app.main import app

async def _mock(*args, **kwargs):
    yield {"type": "token", "content": "mocked!"}
    yield {"type": "done", "full_text": "mocked!", "tool_uses": []}

def run_test(path):
    print(f"Testing path: {path}")
    try:
        with patch(path, side_effect=_mock):
            with TestClient(app) as tc:
                with tc.websocket_connect("/ws/chat/1234") as ws:
                    ws.send_json({"type": "message", "content": "hello", "keydata": []})
                    event = ws.receive_json()
                    print(f"Result: {event}")
                    if event.get("content") == "mocked!":
                        print("SUCCESS")
                        return True
    except Exception as e:
        print(f"Error: {e}")
    return False

import sys
paths = [
    "app.api.chat.stream_claude_response",
    "app.ai.claude_client.stream_claude_response",
    "api.chat.stream_claude_response"
]
for p in paths:
    if run_test(p):
        sys.exit(0)
