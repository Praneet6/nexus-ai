"""
test_auth.py — Auth endpoint integration tests.

Covers:
  • POST /auth/register  — creates account, returns JWT + role="user"
  • POST /auth/login     — happy path returns JWT + correct role
  • POST /auth/login     — wrong password returns 401
  • POST /auth/login     — unknown email returns 401
  • POST /auth/register  — duplicate email returns 400
"""
import pytest
from jose import jwt

from app.config import get_settings


# ── Register ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_creates_user_role_account(client):
    """
    Happy path: new registration returns 200, a valid JWT, and role='user'.
    The JWT payload must also encode role='user'.
    """
    response = await client.post(
        "/auth/register",
        json={"email": "new@test.com", "password": "secret123", "name": "New User"},
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["role"] == "user"
    assert body["token_type"] == "bearer"
    assert body["name"] == "New User"
    assert "access_token" in body
    assert "customer_id" in body

    # Decode token and verify role claim
    settings = get_settings()
    payload = jwt.decode(
        body["access_token"],
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["role"] == "user"
    assert payload["sub"] == body["customer_id"]


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_400(client):
    """Registering the same email twice must return 400."""
    payload = {"email": "dup@test.com", "password": "pass", "name": "Dup"}
    await client.post("/auth/register", json=payload)  # first registration
    response = await client.post("/auth/register", json=payload)  # duplicate
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_happy_path_returns_jwt_and_role(client, regular_user):
    """
    Login with correct credentials returns 200 with a valid JWT.
    The token must encode the user's role and customer_id.
    """
    response = await client.post(
        "/auth/login",
        data={"username": "user@test.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["role"] == "user"
    assert body["name"] == regular_user.name
    assert body["customer_id"] == regular_user.id

    settings = get_settings()
    payload = jwt.decode(
        body["access_token"],
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["role"] == "user"
    assert payload["sub"] == regular_user.id


@pytest.mark.asyncio
async def test_login_admin_role_is_preserved_in_jwt(client, admin_user):
    """Admin login must return role='admin' in both the response and the JWT."""
    response = await client.post(
        "/auth/login",
        data={"username": "admin@test.com", "password": "adminpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "admin"

    settings = get_settings()
    payload = jwt.decode(
        body["access_token"],
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["role"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client, regular_user):
    """Incorrect password must return 401, never 200."""
    response = await client.post(
        "/auth/login",
        data={"username": "user@test.com", "password": "WRONG"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(client):
    """Non-existent email must return 401."""
    response = await client.post(
        "/auth/login",
        data={"username": "ghost@nowhere.com", "password": "whatever"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
