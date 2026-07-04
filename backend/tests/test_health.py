"""
test_health.py — GET /health endpoint tests.

Verifies that the health check correctly reflects db and redis connectivity
when both are available (via test fixtures) and returns status: "ok".
"""
import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    """Both db and redis are connected via fixtures → status should be 'ok'."""
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["db"] == "connected"
    assert body["redis"] == "connected"
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_health_reports_all_features(client):
    """Feature flags are reported in the health response."""
    response = await client.get("/health")
    assert response.status_code == 200
    features = response.json()["features"]
    assert features["f01_conversation_will"] is True
    assert features["f02_silence_detection"] is True
    assert features["f03_resolution_replay"] is True
    assert features["f04_empathy_mirroring"] is True
    assert features["f06_apology_economy"] is True
    # f05 depends on PINECONE_API_KEY — just check it's present as a bool
    assert isinstance(features["f05_collective_memory"], bool)


@pytest.mark.asyncio
async def test_health_has_version(client):
    """Version field is present and non-empty."""
    response = await client.get("/health")
    body = response.json()
    assert "version" in body
    assert body["version"]
