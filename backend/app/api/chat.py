"""
Chat WebSocket + REST endpoint — the central pipeline.
Orchestrates all 6 features on every message.
"""
import json
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.db.postgres import get_db
from app.db import redis_client
from app.models.models import Session as ChatSession, Message
from app.ai.claude_client import stream_claude_response
from app.ai.silence_detector import classify_silence
from app.ai.style_mirror import classify_style, StyleProfile
from app.ai.collective_memory import find_similar_queries, store_resolved_query, get_pinecone_index
from app.ai.contract_manager import (
    parse_contract_from_response, contract_to_dict, contract_from_dict, Contract
)
from app.ai.trust_engine import debit_trust, issue_credit, calculate_trust_health

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)

# Active WebSocket connections: session_id → WebSocket
_connections: dict[str, WebSocket] = {}


async def _get_db_dep():
    settings = get_settings()
    async for session in get_db(settings.database_url):
        yield session


# ── Session helpers ──────────────────────────────────────────────────────────

async def get_or_create_session(db: AsyncSession, session_id: str, customer_id: str) -> ChatSession:
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        session = ChatSession(id=session_id, customer_id=customer_id)
        db.add(session)
        await db.commit()
        await db.refresh(session)
    return session


async def load_message_history(db: AsyncSession, session_id: str) -> list[dict]:
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]


async def save_message(db: AsyncSession, session_id: str, role: str, content: str, silence_state: str = None):
    msg = Message(session_id=session_id, role=role, content=content, silence_state=silence_state)
    db.add(msg)
    await db.commit()


# ── Style profile cache helpers ──────────────────────────────────────────────

async def get_style_profile(session_id: str) -> Optional[StyleProfile]:
    settings = get_settings()
    data = await redis_client.cache_get(settings.redis_url, f"style:{session_id}")
    return StyleProfile.from_dict(data) if data else None


async def update_style_profile(session_id: str, user_messages: list[str]) -> StyleProfile:
    settings = get_settings()
    profile = classify_style(user_messages)
    await redis_client.cache_set(settings.redis_url, f"style:{session_id}", profile.to_dict(), ttl=1800)
    return profile


# ── Contract cache helpers ───────────────────────────────────────────────────

async def get_contract(session_id: str) -> Optional[Contract]:
    settings = get_settings()
    data = await redis_client.cache_get(settings.redis_url, f"contract:{session_id}")
    return contract_from_dict(data) if data else None


async def save_contract(session_id: str, contract: Contract):
    settings = get_settings()
    await redis_client.cache_set(settings.redis_url, f"contract:{session_id}", contract_to_dict(contract), ttl=86400)


# ── Main chat pipeline ────────────────────────────────────────────────────────

async def process_chat_message(
    session_id: str,
    customer_id: str,
    user_message: str,
    keydata: list[dict],
    db: AsyncSession,
    ws: Optional[WebSocket] = None,
) -> dict:
    settings = get_settings()

    async def send_ws(data: dict):
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                pass

    # F02 — Silence Detection
    silence_result = classify_silence(keydata) if keydata else None
    silence_state = silence_result.state if silence_result else "confident"

    if silence_state != "confident":
        await send_ws({"type": "silence_alert", "state": silence_state, "confidence": silence_result.confidence if silence_result else 0})

    # Save user message
    await save_message(db, session_id, "user", user_message, silence_state)

    # Load message history
    history = await load_message_history(db, session_id)

    # F04 — Update style profile and push to frontend
    user_texts = [m["content"] for m in history if m["role"] == "user"]
    style_profile = await update_style_profile(session_id, user_texts)
    await send_ws({
        "type": "style_profile",
        "profile": style_profile.to_dict(),
    })

    # F01 — Load contract state
    contract = await get_contract(session_id)

    # F05 — Collective memory
    pinecone_index = None
    collective_matches = []
    if settings.pinecone_api_key:
        try:
            pinecone_index = get_pinecone_index(settings.pinecone_api_key, settings.pinecone_index)
            collective_matches = await find_similar_queries(user_message, pinecone_index)
        except Exception as e:
            logger.warning(f"[F05] Collective memory unavailable: {e}")

    # Stream Claude response
    full_text = ""
    tool_events = []

    async for event in stream_claude_response(
        messages=history,
        session_id=session_id,
        contract=contract,
        silence_state=silence_state,
        style_profile=style_profile,
        collective_matches=collective_matches,
    ):
        if event["type"] == "token":
            full_text += event["content"]
            await send_ws({"type": "token", "content": event["content"]})

        elif event["type"] == "tool_use":
            tool_events.append(event)
            await send_ws({
                "type": "tool_executing",
                "tool": event["tool"],
                "tool_input": event.get("tool_input", {}),
            })

            # F06 — Trust debit on escalation
            if event.get("triggers_trust_debit"):
                new_balance = await debit_trust(db, session_id, customer_id, event["debit_reason"])
                health = calculate_trust_health(new_balance)
                credit = None
                if new_balance < 60:
                    credit = await issue_credit(db, session_id, customer_id, 100 - new_balance)

                await send_ws({
                    "type": "trust_event",
                    "balance": new_balance,
                    "health": health,
                    "credit": {
                        "coupon_code": credit.coupon_code,
                        "inr_value": credit.inr_value,
                        "message": credit.message,
                    } if credit else None,
                })

        elif event["type"] == "done":
            # F01 — Parse contract from first response
            if not contract and full_text:
                new_contract = parse_contract_from_response(full_text, session_id)
                if new_contract:
                    await save_contract(session_id, new_contract)
                    await send_ws({"type": "contract", "contract": contract_to_dict(new_contract)})

    # Save assistant reply
    if full_text:
        await save_message(db, session_id, "assistant", full_text)

    trace_id = str(uuid.uuid4())
    await send_ws({"type": "done", "trace_id": trace_id})

    # F05 — Store resolved query async (best effort)
    if full_text and pinecone_index:
        try:
            await store_resolved_query(
                query_text=user_message,
                resolution_text=full_text,
                pinecone_index=pinecone_index,
            )
        except Exception:
            pass

    return {
        "reply": full_text,
        "trace_id": trace_id,
        "silence_state": silence_state,
        "style_profile": style_profile.to_dict() if style_profile else None,
    }


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    _connections[session_id] = websocket

    # Simple token extraction from query param
    token = websocket.query_params.get("token", "")
    customer_id = "demo-customer"  # In production parse from JWT

    if token:
        try:
            from jose import jwt
            settings = get_settings()
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            customer_id = payload.get("sub", "demo-customer")
        except Exception:
            pass

    settings = get_settings()

    try:
        async for session in get_db(settings.database_url):
            await get_or_create_session(session, session_id, customer_id)
            await session.commit()
            break
    except Exception as e:
        logger.error(f"Session init failed: {e}")

    logger.info(f"[WS] Connected: session={session_id}, customer={customer_id}")

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "message":
                user_message = data.get("content", "").strip()
                keydata = data.get("keydata", [])

                if not user_message:
                    continue

                async for db in get_db(settings.database_url):
                    try:
                        await process_chat_message(
                            session_id=session_id,
                            customer_id=customer_id,
                            user_message=user_message,
                            keydata=keydata,
                            db=db,
                            ws=websocket,
                        )
                    except Exception as e:
                        logger.error(f"Chat processing error: {e}")
                        await websocket.send_json({"type": "error", "message": "Processing failed. Please retry."})
                    break

    except WebSocketDisconnect:
        logger.info(f"[WS] Disconnected: session={session_id}")
    finally:
        _connections.pop(session_id, None)


# ── REST fallback ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    customer_id: str = "demo-customer"
    message: str
    keydata: list[dict] = []


@router.post("/api/chat/message")
async def chat_message(req: ChatRequest, db: AsyncSession = Depends(_get_db_dep)):
    await get_or_create_session(db, req.session_id, req.customer_id)
    result = await process_chat_message(
        session_id=req.session_id,
        customer_id=req.customer_id,
        user_message=req.message,
        keydata=req.keydata,
        db=db,
    )
    return result
