from fastapi.testclient import TestClient

from app.api.app import app, create_app
from app.config import get_settings

_QUERY = {"question": "anything"}
_OPERATOR = {"X-API-Key": "dev-key-operator"}


def test_rag_query_missing_api_key_returns_422():
    with TestClient(app) as client:
        response = client.post("/rag/query", json=_QUERY)
    assert response.status_code == 422


def test_rag_query_invalid_api_key_returns_401():
    with TestClient(app) as client:
        response = client.post("/rag/query", json=_QUERY, headers={"X-API-Key": "nope"})
    assert response.status_code == 401


def test_rag_index_viewer_role_forbidden_returns_403():
    with TestClient(app) as client:
        response = client.post(
            "/rag/index",
            json={"documents": [{"doc_id": "d1", "text": "content"}]},
            headers={"X-API-Key": "dev-key-viewer"},
        )
    assert response.status_code == 403


def test_health_probes_stay_public():
    with TestClient(app) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 200


def test_request_id_header_is_echoed_from_request():
    with TestClient(app) as client:
        response = client.get("/healthz", headers={"X-Request-ID": "trace-123"})
    assert response.headers["X-Request-ID"] == "trace-123"


def test_rate_limit_returns_429_over_limit(monkeypatch):
    monkeypatch.setenv("APP_RATE_LIMIT_MAX_REQUESTS", "2")
    get_settings.cache_clear()
    try:
        limited_app = create_app()
        with TestClient(limited_app) as client:
            statuses = [
                client.post("/rag/query", json=_QUERY, headers=_OPERATOR).status_code
                for _ in range(3)
            ]
    finally:
        get_settings.cache_clear()
    assert statuses[0] != 429
    assert statuses[1] != 429
    assert statuses[2] == 429
