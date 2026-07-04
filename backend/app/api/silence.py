"""
F02 — Silence classification REST endpoint.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.ai.silence_detector import classify_silence, KeystrokeData

router = APIRouter(prefix="/api/silence", tags=["silence"])


class KeystrokeItem(BaseModel):
    delay_ms: float = 0
    is_backspace: bool = False
    idle_ms: float = 0


class SilenceRequest(BaseModel):
    session_id: str
    keydata: list[KeystrokeItem]


class SilenceResponse(BaseModel):
    state: str
    confidence: float
    signals: dict


@router.post("/classify", response_model=SilenceResponse)
async def classify_endpoint(req: SilenceRequest) -> SilenceResponse:
    raw = [{"delay_ms": k.delay_ms, "is_backspace": k.is_backspace, "idle_ms": k.idle_ms} for k in req.keydata]
    result = classify_silence(raw)
    return SilenceResponse(state=result.state, confidence=result.confidence, signals=result.signals)
