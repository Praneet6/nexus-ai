"""
F06 — Apology Economy
Trust balance tracking, automatic debit on failures, coupon issuance on threshold breach.
"""
import random
import string
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

DEBIT_RULES: dict[str, int] = {
    "escalation_to_human": 20,
    "unresolved_after_3_turns": 10,
    "wait_over_2_min": 5,
    "wrong_answer_corrected": 8,
    "session_abandoned": 15,
}

# (min_debt, max_debt): (coupon_prefix, inr_value)
CREDIT_TABLE = [
    (0,  15, "NEXUS5",  50),
    (15, 30, "NEXUS10", 100),
    (30, 50, "NEXUS20", 200),
    (50, 999, "NEXUS50", 500),
]

HEALTH_THRESHOLDS = {
    "excellent": 80,
    "good": 60,
    "at_risk": 40,
}


@dataclass
class TrustCredit:
    coupon_code: str
    inr_value: int
    message: str


def get_debit_amount(reason: str) -> int:
    return DEBIT_RULES.get(reason, 5)


def calculate_credit(trust_debt: int) -> tuple[str, int]:
    for min_d, max_d, prefix, inr in CREDIT_TABLE:
        if min_d <= trust_debt < max_d:
            return prefix, inr
    return "NEXUS50", 500


def generate_coupon_code() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"NEXUS{suffix}"


def calculate_trust_health(balance: int) -> str:
    if balance >= HEALTH_THRESHOLDS["excellent"]:
        return "excellent"
    elif balance >= HEALTH_THRESHOLDS["good"]:
        return "good"
    elif balance >= HEALTH_THRESHOLDS["at_risk"]:
        return "at_risk"
    return "critical"


async def debit_trust(db, session_id: str, customer_id: str, reason: str) -> int:
    """Debit trust balance and return new balance. Writes to DB."""
    from sqlalchemy import select, func
    from app.models.models import TrustEvent, Customer

    amount = get_debit_amount(reason)

    # Write debit event
    event = TrustEvent(
        session_id=session_id,
        customer_id=customer_id,
        event_type="debit",
        amount=amount,
        reason=reason,
    )
    db.add(event)

    # Recalculate balance from all events
    result = await db.execute(
        select(func.sum(TrustEvent.amount)).where(
            TrustEvent.customer_id == customer_id,
            TrustEvent.event_type == "debit",
        )
    )
    total_debited = result.scalar() or 0
    new_balance = max(0, 100 - int(total_debited))

    # Update customer record
    cust_result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = cust_result.scalar_one_or_none()
    if customer:
        customer.trust_balance = new_balance

    await db.commit()
    logger.info(f"[F06] Trust debit: {amount}pts ({reason}), new balance: {new_balance}")
    return new_balance


async def issue_credit(db, session_id: str, customer_id: str, trust_debt: int) -> Optional[TrustCredit]:
    """Issue a coupon credit when trust falls below threshold."""
    from app.models.models import TrustEvent

    _, inr_value = calculate_credit(trust_debt)
    coupon = generate_coupon_code()

    event = TrustEvent(
        session_id=session_id,
        customer_id=customer_id,
        event_type="credit",
        amount=trust_debt,
        reason="auto_credit_threshold",
        credit_code=coupon,
        credit_value_inr=inr_value,
    )
    db.add(event)
    await db.commit()

    message = (
        f"We sincerely apologise for the inconvenience. "
        f"As a gesture of goodwill, we've issued you a ₹{inr_value} credit. "
        f"Your coupon code is: {coupon} 🎁"
    )

    logger.info(f"[F06] Credit issued: ₹{inr_value} ({coupon}) to customer {customer_id}")
    return TrustCredit(coupon_code=coupon, inr_value=inr_value, message=message)


async def get_trust_balance(db, customer_id: str) -> dict:
    """Get full trust status for a customer."""
    from sqlalchemy import select, func
    from app.models.models import TrustEvent

    result = await db.execute(
        select(TrustEvent).where(TrustEvent.customer_id == customer_id).order_by(TrustEvent.created_at)
    )
    events = result.scalars().all()

    total_debited = sum(e.amount for e in events if e.event_type == "debit")
    total_credited_inr = sum(e.credit_value_inr or 0 for e in events if e.event_type == "credit")
    balance = max(0, 100 - total_debited)
    health = calculate_trust_health(balance)

    return {
        "balance": balance,
        "health": health,
        "total_debited": total_debited,
        "total_credited_inr": total_credited_inr,
        "events": [
            {
                "id": e.id,
                "type": e.event_type,
                "amount": e.amount,
                "reason": e.reason,
                "credit_code": e.credit_code,
                "credit_value_inr": e.credit_value_inr,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }
