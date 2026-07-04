"""
test_trust.py — Trust admin endpoint RBAC tests.

Verifies the require_admin dependency on GET /api/trust/admin/summary:
  • No token       → 401 (OAuth2 scheme rejects unauthenticated)
  • User-role JWT  → 403 (authenticated but not admin)
  • Admin-role JWT → 200 (correct role, returns expected shape)

Also verifies the per-customer trust endpoint is accessible without admin.
"""
import pytest


ADMIN_SUMMARY_URL = "/api/trust/admin/summary"


# ── Authorization boundary tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_summary_no_token_returns_401(client):
    """
    No Authorization header at all.
    The OAuth2PasswordBearer scheme returns 401 before require_admin is reached.
    """
    response = await client.get(ADMIN_SUMMARY_URL)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_summary_user_token_returns_403(client, user_token):
    """
    Valid JWT with role='user' must be rejected with 403 by require_admin.
    The response detail must mention admin access.
    """
    response = await client.get(
        ADMIN_SUMMARY_URL,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_summary_invalid_token_returns_401(client):
    """A garbage token must return 401, not 403 or 500."""
    response = await client.get(
        ADMIN_SUMMARY_URL,
        headers={"Authorization": "Bearer not.a.real.token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_summary_admin_token_returns_200(client, admin_token):
    """
    Valid JWT with role='admin' must return 200.
    Response must include the expected aggregate keys with correct types.
    """
    response = await client.get(
        ADMIN_SUMMARY_URL,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()

    # Shape assertions
    assert "avg_trust_balance" in body
    assert "at_risk_count" in body
    assert "total_credits_issued_inr" in body
    assert "top_failure_reasons" in body
    assert "health" in body

    # Type assertions
    assert isinstance(body["avg_trust_balance"], float)
    assert isinstance(body["at_risk_count"], int)
    assert isinstance(body["top_failure_reasons"], list)
    assert body["health"] in ("excellent", "good", "at_risk", "critical")


@pytest.mark.asyncio
async def test_admin_summary_fresh_db_has_default_balance(client, admin_token):
    """
    On a freshly seeded DB (no trust events yet), avg balance defaults to 100
    and at_risk_count is 0 (both seeded customers have balance=100).
    """
    response = await client.get(
        ADMIN_SUMMARY_URL,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    # avg of 100, 100 = 100.0
    assert body["avg_trust_balance"] == 100.0
    assert body["at_risk_count"] == 0
    assert body["health"] == "excellent"


# ── Per-customer endpoint (no admin required) ─────────────────────────────────

@pytest.mark.asyncio
async def test_get_trust_per_customer_accessible_without_admin(client, regular_user):
    """
    GET /api/trust/{customer_id} does not require admin role.
    Any request (even unauthenticated) can query a balance by ID.
    """
    response = await client.get(f"/api/trust/{regular_user.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["balance"] == 100
    assert body["health"] == "excellent"
