"""
F06 — Trust ledger REST endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.ai.trust_engine import get_trust_balance
from app.models.models import TrustEvent, Customer
from app.config import get_settings
from app.db.postgres import get_db
from app.ai.trust_engine import calculate_trust_health
from app.api.auth import require_admin

router = APIRouter(prefix="/api/trust", tags=["trust"])


async def _get_db_dep():
    settings = get_settings()
    async for session in get_db(settings.database_url):
        yield session


# ── Per-customer endpoint (self-service, any authenticated user) ──────────────

@router.get("/{customer_id}")
async def get_trust(customer_id: str, db: AsyncSession = Depends(_get_db_dep)):
    return await get_trust_balance(db, customer_id)


# ── Admin-only endpoints ──────────────────────────────────────────────────────
# All routes below require role == "admin" in the JWT.
# A regular user hitting these will receive HTTP 403.

@router.get("/admin/summary", dependencies=[Depends(require_admin)])
async def admin_summary(db: AsyncSession = Depends(_get_db_dep)):
    """Aggregate trust metrics across all customers — admin only."""
    # Average trust balance
    result = await db.execute(select(func.avg(Customer.trust_balance)))
    avg_balance = result.scalar() or 100

    # At-risk customers (balance < 60)
    at_risk = await db.execute(select(func.count()).where(Customer.trust_balance < 60))
    at_risk_count = at_risk.scalar() or 0

    # Total credits issued
    credits = await db.execute(
        select(func.sum(TrustEvent.credit_value_inr)).where(TrustEvent.event_type == "credit")
    )
    total_credits_inr = credits.scalar() or 0

    # Top failure reasons
    reasons = await db.execute(
        select(TrustEvent.reason, func.count().label("count"))
        .where(TrustEvent.event_type == "debit")
        .group_by(TrustEvent.reason)
        .order_by(func.count().desc())
        .limit(5)
    )
    top_reasons = [{"reason": r, "count": c} for r, c in reasons.all()]

    return {
        "avg_trust_balance": round(float(avg_balance), 1),
        "at_risk_count": at_risk_count,
        "total_credits_issued_inr": total_credits_inr,
        "top_failure_reasons": top_reasons,
        "health": calculate_trust_health(int(avg_balance)),
    }
