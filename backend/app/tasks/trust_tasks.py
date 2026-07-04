"""
Celery async task worker — Trust Engine background tasks.
"""
import asyncio
import logging
from celery import Celery
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery(
    "nexus",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(name="tasks.fire_trust_debit", bind=True, max_retries=3)
def fire_trust_debit(self, session_id: str, customer_id: str, reason: str):
    """Async trust debit — runs in Celery worker, doesn't block chat."""
    try:
        async def _run():
            from app.ai.trust_engine import debit_trust, issue_credit, calculate_trust_health
            from app.db.postgres import get_db
            async for db in get_db(settings.database_url):
                try:
                    new_balance = await debit_trust(db, session_id, customer_id, reason)
                    health = calculate_trust_health(new_balance)
                    logger.info(f"[Celery] Trust debit fired: {reason}, balance={new_balance}, health={health}")

                    if new_balance < 60:
                        credit = await issue_credit(db, session_id, customer_id, 100 - new_balance)
                        logger.info(f"[Celery] Credit auto-issued: {credit.coupon_code} (₹{credit.inr_value})")
                except Exception as e:
                    logger.error(f"[Celery] Trust debit DB error: {e}")
                break

        asyncio.run(_run())
    except Exception as exc:
        logger.error(f"[Celery] fire_trust_debit failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="tasks.store_collective_pattern")
def store_collective_pattern(query_text: str, resolution_text: str, next_issue: str = ""):
    """Store resolved query to Pinecone in background."""
    if not settings.pinecone_api_key:
        return

    async def _run():
        from app.ai.collective_memory import store_resolved_query, get_pinecone_index
        try:
            index = get_pinecone_index(settings.pinecone_api_key, settings.pinecone_index)
            await store_resolved_query(query_text, resolution_text, next_issue, index)
            logger.info("[Celery] Collective pattern stored")
        except Exception as e:
            logger.warning(f"[Celery] store_collective_pattern failed: {e}")

    asyncio.run(_run())
