import pytest


@pytest.mark.asyncio
async def test_root_endpoint(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "Token Optimizer API"


@pytest.mark.asyncio
async def test_tokenize_endpoint(client):
    resp = await client.post(
        "/api/tokenize",
        json={"text": "Hola mundo"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_count"] == 2
    assert data["detected_language"] in ("es", "pt")
    assert data["text"] == "Hola mundo"


@pytest.mark.asyncio
async def test_tokenize_empty(client):
    resp = await client.post(
        "/api/tokenize",
        json={"text": ""}
    )
    assert resp.status_code == 200
    assert resp.json()["token_count"] == 0


@pytest.mark.asyncio
async def test_projection_endpoint(client):
    resp = await client.post(
        "/api/analyze/projection",
        json={
            "tokens_original": 27,
            "tokens_translated": 19,
            "reviews_per_day": 10000,
            "cost_per_million_tokens_usd": 2.5,
            "days": 30
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["daily_token_diff"] == 80000
    assert data["monthly_token_diff"] == 2400000
    assert data["monthly_savings_usd"] == 6.0


@pytest.mark.asyncio
async def test_config_status_endpoint(client):
    resp = await client.get("/api/config/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "ollama_available" in data
    assert "deepl_configured" in data


@pytest.mark.asyncio
async def test_analyze_endpoint_returns_200(client):
    resp = await client.post(
        "/api/analyze",
        json={"text": "Hola mundo", "engine": "ollama", "classify": False}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "original" in data
    assert "translated" in data
    assert "spanglish" in data
    assert data["engine_used"] in ("ollama", "deepl", "google", "fallback", "none")
