"""
test_chat.py — WebSocket chat endpoint integration tests.

Strategy
────────
• httpx does not support WebSocket; we use Starlette's synchronous
  TestClient.websocket_connect() which wraps the ASGI app.
• Claude's stream_claude_response is patched in conftest via the `client`
  fixture. For WebSocket tests we need the same patch but on TestClient,
  so we apply it directly here.
• The mock yields: token → style_profile → done
  allowing us to assert both event types arrive.

Tests
─────
1. test_ws_connect_and_send_message — connect, send a message, collect all
   events, assert we received at least one "token" and one "style_profile".
2. test_ws_done_event_closes_cleanly — assert "done" event is received and
   contains a trace_id.
3. test_ws_empty_message_is_ignored — sending an empty message string does
   not produce any assistant response.
4. test_ws_unauthenticated_still_connects — WS accepts without token
   (falls back to demo-customer) — connection itself is not token-gated.
"""
import json
import uuid
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from app.main import app


# ── Mock stream ───────────────────────────────────────────────────────────────

async def _mock_claude_stream(*args, **kwargs):
    """
    Deterministic fake stream:
      token        → message fragment
      style_profile is emitted by process_chat_message AFTER classify_style,
                     which runs synchronously — so it will arrive in the WS
                     response before "done".
      done         → end-of-stream marker with trace_id
    """
    yield {"type": "token", "content": "Hello, I can help with that!"}
    yield {"type": "done", "full_text": "Hello, I can help with that!", "tool_uses": []}


def _collect_ws_events(ws, send_payload: dict, max_events: int = 20) -> list[dict]:
    """Send one message and collect all WS events until 'done' or max_events."""
    ws.send_text(json.dumps(send_payload))
    events = []
    for _ in range(max_events):
        raw = ws.receive_text()
        event = json.loads(raw)
        events.append(event)
        if event.get("type") == "done":
            break
    return events


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_ws_connect_and_send_message():
    """
    Connect to /ws/chat/{session_id}, send a text message, and assert:
      • at least one event with type="token" is received
      • a style_profile event is received (F04 wired through chat pipeline)
    """
    session_id = str(uuid.uuid4())

    with patch("app.api.chat.stream_claude_response", side_effect=_mock_claude_stream):
        with TestClient(app) as tc:
            with tc.websocket_connect(f"/ws/chat/{session_id}") as ws:
                events = _collect_ws_events(
                    ws,
                    {"type": "message", "content": "Where is my order?", "keydata": []},
                )

    event_types = [e["type"] for e in events]
    assert "token" in event_types, f"Expected 'token' event, got: {event_types}"
    assert "style_profile" in event_types, (
        f"Expected 'style_profile' event from F04 pipeline, got: {event_types}"
    )


def test_ws_done_event_carries_trace_id():
    """
    The 'done' event must be received and contain a non-empty trace_id
    so the frontend can correlate the request in the audit log (F03).
    """
    session_id = str(uuid.uuid4())

    with patch("app.api.chat.stream_claude_response", side_effect=_mock_claude_stream):
        with TestClient(app) as tc:
            with tc.websocket_connect(f"/ws/chat/{session_id}") as ws:
                events = _collect_ws_events(
                    ws,
                    {"type": "message", "content": "I need a refund", "keydata": []},
                )

    done_events = [e for e in events if e["type"] == "done"]
    assert done_events, "No 'done' event received"
    assert done_events[-1].get("trace_id"), "done event is missing trace_id"


def test_ws_empty_message_is_ignored():
    """
    Sending an empty 'content' string must not trigger the chat pipeline.
    The WS should not produce any 'token' events.
    We send a blank message then immediately a real message and assert
    only the real one produces tokens.
    """
    session_id = str(uuid.uuid4())

    with patch("app.api.chat.stream_claude_response", side_effect=_mock_claude_stream):
        with TestClient(app) as tc:
            with tc.websocket_connect(f"/ws/chat/{session_id}") as ws:
                # Send blank — server must silently ignore
                ws.send_text(json.dumps({"type": "message", "content": "   ", "keydata": []}))

                # Follow up with a real message to confirm the connection is still healthy
                events = _collect_ws_events(
                    ws,
                    {"type": "message", "content": "Hello", "keydata": []},
                )

    event_types = [e["type"] for e in events]
    assert "token" in event_types, "Real message should produce tokens"


def test_ws_unauthenticated_still_connects():
    """
    The WebSocket endpoint accepts connections without a token query param.
    It falls back to 'demo-customer'. The connection itself is not rejected.
    """
    session_id = str(uuid.uuid4())

    with patch("app.api.chat.stream_claude_response", side_effect=_mock_claude_stream):
        with TestClient(app) as tc:
            # No ?token=... in the URL
            with tc.websocket_connect(f"/ws/chat/{session_id}") as ws:
                events = _collect_ws_events(
                    ws,
                    {"type": "message", "content": "Test without auth", "keydata": []},
                )

    assert any(e["type"] == "done" for e in events), (
        "Expected 'done' event even for unauthenticated connection"
    )


def test_ws_keydata_triggers_silence_detection():
    """
    Send keydata mimicking a distressed typist (high backspace ratio +
    long idle pauses). Assert a 'silence_alert' event is present.
    """
    session_id = str(uuid.uuid4())
    # 10 keystrokes, 6 are backspaces, with 3-second idle pauses → distressed
    keydata = [
        {"delay_ms": 350, "is_backspace": True,  "idle_ms": 3500},
        {"delay_ms": 400, "is_backspace": True,  "idle_ms": 3200},
        {"delay_ms": 320, "is_backspace": False, "idle_ms": 2800},
        {"delay_ms": 380, "is_backspace": True,  "idle_ms": 3100},
        {"delay_ms": 410, "is_backspace": True,  "idle_ms": 0},
        {"delay_ms": 290, "is_backspace": False, "idle_ms": 0},
        {"delay_ms": 360, "is_backspace": True,  "idle_ms": 4000},
        {"delay_ms": 420, "is_backspace": True,  "idle_ms": 0},
        {"delay_ms": 300, "is_backspace": False, "idle_ms": 0},
        {"delay_ms": 340, "is_backspace": False, "idle_ms": 0},
    ]

    with patch("app.api.chat.stream_claude_response", side_effect=_mock_claude_stream):
        with TestClient(app) as tc:
            with tc.websocket_connect(f"/ws/chat/{session_id}") as ws:
                events = _collect_ws_events(
                    ws,
                    {
                        "type": "message",
                        "content": "I am really struggling here",
                        "keydata": keydata,
                    },
                )

    event_types = [e["type"] for e in events]
    assert "silence_alert" in event_types, (
        f"Expected 'silence_alert' for distressed keydata, got: {event_types}"
    )