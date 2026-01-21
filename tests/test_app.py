import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure settings read env from tests
os.environ.setdefault("USE_SAMPLE_DATA", "true")
os.environ.setdefault("API_AUTH_TOKEN", "secret")

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def test_sync_endpoint_success(client: TestClient):
    response = client.post("/sync", headers={"x-api-token": "secret"})
    assert response.status_code == 200
    assert "detalle" in response.json()


def test_recommend_endpoint_success(client: TestClient):
    response = client.post("/recommend", headers={"x-api-token": "secret"})
    assert response.status_code == 200
    data = response.json()
    assert "recomendaciones" in data
    assert isinstance(data["recomendaciones"], list)
    assert len(data["recomendaciones"]) > 0
    assert all(isinstance(item, str) for item in data["recomendaciones"])


def test_requires_auth(client: TestClient):
    response = client.post("/recommend")
    assert response.status_code == 401
