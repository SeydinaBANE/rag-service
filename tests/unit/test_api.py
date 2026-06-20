from fastapi.testclient import TestClient

from app.api.app import app


def test_healthz_ok():
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_readyz_ready():
    with TestClient(app) as client:
        response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_greet_nominal():
    with TestClient(app) as client:
        response = client.get("/greet", params={"recipient": "Ada", "locale": "fr"})
    assert response.status_code == 200
    assert response.json()["message"] == "Bonjour, Ada !"


def test_greet_too_long_recipient_returns_422():
    with TestClient(app) as client:
        response = client.get("/greet", params={"recipient": "x" * 200})
    assert response.status_code == 422
