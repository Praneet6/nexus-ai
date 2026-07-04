"""
FastAPI main application — startup, routers, CORS, health check.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.postgres import init_db
from app.db.redis_client import ping_redis
from app.api import auth, chat, silence, replay, trust

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    logger.info("🚀 Nexus AI starting up...")

    # Init database
    try:
        await init_db(settings.database_url)
        db_ok = True
        logger.info("✅ Database initialised")
    except Exception as e:
        db_ok = False
        logger.error(f"❌ Database init failed: {e}")

    # Pre-load spaCy (F04 Style Mirror)
    spacy_ok = False
    try:
        from app.ai.style_mirror import get_nlp
        get_nlp()
        spacy_ok = True
    except Exception as e:
        logger.warning(f"⚠ spaCy not available: {e}")

    # Train / verify silence model (F02)
    silence_ok = False
    silence_detail = "training failed — check ml/ logs"
    try:
        from app.ai.silence_detector import train_if_missing, MODEL_PATH
        silence_ok = train_if_missing(MODEL_PATH)
        silence_detail = "model ready" if silence_ok else "training failed — check ml/ logs"
    except Exception as e:
        logger.warning(f"⚠ F02 silence model setup failed: {e}")
        silence_detail = f"error: {e}"

    # Pre-load embedding model + Pinecone index (F05 Collective Memory)
    pinecone_ok = False
    if settings.pinecone_api_key:
        try:
            from app.ai.collective_memory import get_embedding_model, get_pinecone_index
            get_embedding_model()
            idx = get_pinecone_index(settings.pinecone_api_key, settings.pinecone_index)
            pinecone_ok = idx is not None
        except Exception as e:
            logger.warning(f"⚠ F05 Collective Memory init failed: {e}")

    # ── Feature banner ────────────────────────────────────────
    def _flag(ok: bool) -> str:
        return "✓" if ok else "✗"

    logger.info(
        "\n"
        "╔══════════════════════════════════════════════════════╗\n"
        "║              NEXUS AI — Feature Status               ║\n"
        "╠══════════════════════════════════════════════════════╣\n"
        f"║  {_flag(db_ok)}  Core (DB + Redis)                            ║\n"
        f"║  ✓  F01 Conversation Will       (always on)          ║\n"
        f"║  {_flag(silence_ok)}  F02 Silence Detection     ({silence_detail})  ║\n"
        f"║  ✓  F03 Resolution Replay       (always on)          ║\n"
        f"║  {_flag(spacy_ok)}  F04 Style Mirror          "
        f"{'(spaCy ready)' if spacy_ok else '(heuristic fallback)'}{'         ' if spacy_ok else '  '}║\n"
        f"║  {_flag(pinecone_ok)}  F05 Collective Memory     "
        f"{'(Pinecone ready)' if pinecone_ok else '(no PINECONE_API_KEY — disabled)'}{'  ' if pinecone_ok else ''}║\n"
        f"║  ✓  F06 Apology Economy         (always on)          ║\n"
        "╚══════════════════════════════════════════════════════╝"
    )

    logger.info("✅ Nexus AI ready!")
    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("Nexus AI shutting down...")


app = FastAPI(
    title="Nexus AI",
    description="AI-powered customer care bot with 6 novel features",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(silence.router)
app.include_router(replay.router)
app.include_router(trust.router)


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health():
    db_ok = False
    redis_ok = False

    try:
        from app.db.postgres import get_engine
        engine = get_engine(settings.database_url)
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        redis_ok = await ping_redis(settings.redis_url)
    except Exception:
        pass

    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "db": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "version": "1.0.0",
        "features": {
            "f01_conversation_will": True,
            "f02_silence_detection": True,
            "f03_resolution_replay": True,
            "f04_empathy_mirroring": True,
            "f05_collective_memory": bool(settings.pinecone_api_key),
            "f06_apology_economy": True,
        },
    }


@app.get("/", tags=["root"])
async def root():
    return {"message": "Nexus AI API", "docs": "/docs"}
