"""
conftest.py — shared fixtures for all Nexus AI integration tests.

Isolation strategy
──────────────────
• Database  : SQLite (aiosqlite) in-memory, created fresh per test.
              The postgres.py module-level singletons are reset between
              tests so each function gets a clean engine + session factory.
• Redis     : fakeredis.aioredis in-process fake, injected per test.
• Settings  : get_settings() lru_cache cleared so env overrides take effect.
• Claude    : stream_claude_response patched to avoid real API calls.
• App       : FastAPI lifespan is bypassed — fixtures own startup/teardown.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from jose import jwt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import get_settings
from app.main import app
from app.models.models import Base, Customer, UserRole
from app.api.auth import hash_password
import app.db.postgres as pg_module
import app.db.redis_client as redis_module


# ── Event loop (session-scoped, one loop for the whole run) ──────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Single event loop shared across the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── In-memory SQLite engine ───────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_engine():
    """
    Fresh in-memory SQLite engine per test.
    Resets the postgres.py module-level singletons so get_db() uses this engine.
    """
    # Use a unique DB name so parallel tests don't share state
    db_url = f"sqlite+aiosqlite:///:memory:?cache=shared&uri=true"
    # Actually use a named in-memory DB so the same connection sees the schema
    db_name = uuid.uuid4().hex
    db_url = f"sqlite+aiosqlite:///file:{db_name}?mode=memory&cache=shared&uri=true"

    engine = create_async_engine(db_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Inject into postgres module singletons
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    pg_module._engine = engine
    pg_module._AsyncSessionLocal = session_factory

    yield engine

    # Teardown: drop tables and reset singletons
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    pg_module._engine = None
    pg_module._AsyncSessionLocal = None


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Async DB session bound to the test engine."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


# ── Fake Redis ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def fake_redis():
    """
    In-process fakeredis instance injected into redis_client module.
    Requires: pip install fakeredis[aioredis]
    """
    import fakeredis.aioredis as fakeredis_async
    redis = fakeredis_async.FakeRedis(decode_responses=True)
    # Inject into module singleton so cache_get/cache_set use the fake
    redis_module._redis_client = redis
    yield redis
    await redis.flushall()
    redis_module._redis_client = None


# ── Settings override ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Clear the @lru_cache on get_settings() before each test so any
    monkeypatched env vars take effect cleanly.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ── Seed users ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def regular_user(db_session) -> Customer:
    """A persisted Customer with role='user'."""
    customer = Customer(
        id=str(uuid.uuid4()),
        email="user@test.com",
        name="Test User",
        hashed_password=hash_password("password123"),
        role=UserRole.user,
        trust_balance=100,
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def admin_user(db_session) -> Customer:
    """A persisted Customer with role='admin'."""
    customer = Customer(
        id=str(uuid.uuid4()),
        email="admin@test.com",
        name="Admin User",
        hashed_password=hash_password("adminpass"),
        role=UserRole.admin,
        trust_balance=100,
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)
    return customer


# ── Pre-minted JWTs ───────────────────────────────────────────────────────────

def _mint_token(customer: Customer) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(minutes=60)
    payload = {
        "sub": customer.id,
        "email": customer.email,
        "role": customer.role.value,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@pytest.fixture
def user_token(regular_user) -> str:
    """Valid JWT for role='user'."""
    return _mint_token(regular_user)


@pytest.fixture
def admin_token(admin_user) -> str:
    """Valid JWT for role='admin'."""
    return _mint_token(admin_user)


# ── HTTP client ───────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db_engine, fake_redis) -> AsyncGenerator[AsyncClient, None]:
    """
    httpx AsyncClient pointed at the FastAPI app.
    Lifespan events are skipped — fixtures own DB/Redis setup.
    The Claude stream is patched to a no-op generator so chat tests
    don't need a real API key.
    """
    async def _mock_stream(*args, **kwargs):
        """Minimal mock: emit one token then style_profile then done."""
        yield {"type": "token", "content": "Hello! How can I help?"}
        yield {"type": "done", "full_text": "Hello! How can I help?", "tool_uses": []}

    with patch("app.api.chat.stream_claude_response", side_effect=_mock_stream):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
