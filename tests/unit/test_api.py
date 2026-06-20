import logging

from fastapi.testclient import TestClient

from app.api.app import app, create_app


class _CaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record):
        self.records.append(record)


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


def test_request_middleware_sets_request_id_header():
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.headers["X-Request-ID"]


def test_request_middleware_logs_method_path_and_status():
    handler = _CaptureHandler()
    logger = logging.getLogger("app.api.request")
    logger.addHandler(handler)
    try:
        with TestClient(app) as client:
            client.get("/healthz")
    finally:
        logger.removeHandler(handler)
    record = next(r for r in handler.records if r.getMessage() == "request")
    assert record.method == "GET"
    assert record.path == "/healthz"
    assert record.status_code == 200


def test_request_middleware_logs_unhandled_exception():
    test_app = create_app()

    @test_app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("kaboom")

    handler = _CaptureHandler()
    logger = logging.getLogger("app.api.request")
    logger.addHandler(handler)
    try:
        with TestClient(test_app, raise_server_exceptions=False) as client:
            response = client.get("/boom")
    finally:
        logger.removeHandler(handler)
    assert response.status_code == 500
    assert any(r.getMessage() == "request_failed" for r in handler.records)
