"""
F03 — Resolution Replay REST endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends

from app.ai.replay_tracer import get_session_traces, build_trace_plain_english, generate_trace_pdf
from app.config import get_settings
from app.db.postgres import get_db

router = APIRouter(prefix="/api/replay", tags=["replay"])


async def _get_db_dep():
    settings = get_settings()
    async for session in get_db(settings.database_url):
        yield session


@router.get("/{session_id}")
async def get_replay(session_id: str):
    traces = get_session_traces(session_id)
    summary = build_trace_plain_english(traces)
    return {
        "session_id": session_id,
        "summary_text": summary,
        "steps": traces,
        "total_steps": len(traces),
        "pdf_url": f"/api/replay/{session_id}/pdf",
    }


@router.get("/{session_id}/pdf")
async def get_replay_pdf(session_id: str):
    traces = get_session_traces(session_id)
    summary = build_trace_plain_english(traces)
    pdf_bytes = generate_trace_pdf(session_id, traces, summary)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="nexus-replay-{session_id[:8]}.pdf"'},
    )
