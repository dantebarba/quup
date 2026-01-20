import os
from fastapi.testclient import TestClient

from app.main import app


def _client():
    os.environ.setdefault("API_AUTH_TOKEN", "test-token")
    return TestClient(app)


def test_sync_starts_background_job():
    client = _client()
    r = client.post("/sync", headers={"x-api-token": "test-token"})
    assert r.status_code == 200
    body = r.json()
    assert body.get("started") is True
    assert "Sincronización" in body.get("mensaje", "")


def test_recommend_returns_titles():
    client = _client()
    # Ensure sync has run at least once to create local store
    client.post("/sync", headers={"x-api-token": "test-token"})

    r = client.post("/recommend", headers={"x-api-token": "test-token"})
    assert r.status_code == 200
    body = r.json()
    titles = body.get("peliculas")
    assert isinstance(titles, list)
    assert 0 < len(titles) <= 15
    # Simple sanity: titles are non-empty strings
    assert all(isinstance(t, str) and t.strip() for t in titles)

