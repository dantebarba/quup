from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_sync_endpoint():
    resp = client.post("/sync", headers={"x-api-token": "test-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert "synced" in data


def test_recommend_endpoint_after_sync():
    client.post("/sync", headers={"x-api-token": "test-token"})
    resp = client.post(
        "/recommend", headers={"x-api-token": "test-token"}, json={"history": []}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "titles" in data
    assert isinstance(data["titles"], list)
