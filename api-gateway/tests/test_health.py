import json
import logging
from uuid import UUID

import pytest
from app.logging_config import JsonFormatter
from app.main import create_app
from app.settings import Settings
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with TestClient(
        create_app(
            Settings(service_name="api-gateway", cors_allowed_origins="http://localhost:5173"),
            configure_logging=False,
        )
    ) as instance:
        yield instance


@pytest.mark.parametrize("path,status", [("/health", "healthy"), ("/ready", "ready")])
def test_foundation(client, path, status):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"service": "api-gateway", "status": status}


def test_request_id(client):
    UUID(client.get("/health").headers["x-request-id"])
    assert (
        client.get("/health", headers={"X-Request-ID": "phase1-safe-request"}).headers[
            "x-request-id"
        ]
        == "phase1-safe-request"
    )
    UUID(client.get("/health", headers={"X-Request-ID": "x" * 129}).headers["x-request-id"])


def test_openapi_no_proxy_routes(client):
    assert set(client.get("/openapi.json").json()["paths"]) == {"/health", "/ready"}
    assert client.get("/docs").status_code == 200
    assert client.get("/auth/verify").status_code == 502
    assert client.post("/auth/login").status_code == 502


def test_cors(client):
    assert (
        client.get("/health", headers={"Origin": "http://localhost:5173"}).headers[
            "access-control-allow-origin"
        ]
        == "http://localhost:5173"
    )
    assert (
        "access-control-allow-origin"
        not in client.get("/health", headers={"Origin": "https://untrusted.invalid"}).headers
    )
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Request-ID",
        },
    )
    assert response.status_code == 200


def test_request_log_no_secrets(client, caplog):
    with caplog.at_level(logging.INFO, logger="foundation.request"):
        client.get(
            "/health?otp=sensitive-otp",
            headers={"Authorization": "Bearer sensitive-token", "X-Request-ID": "safe-log-request"},
        )
    record = next(r for r in caplog.records if r.name == "foundation.request")
    data = json.loads(JsonFormatter("api-gateway").format(record))
    assert data["request_id"] == "safe-log-request"
    assert data["path"] == "/health"
    assert data["status_code"] == 200
    assert data["duration_ms"] >= 0
    assert "sensitive" not in json.dumps(data)


def test_formatter_never_serializes_external_message():
    import logging

    record = logging.LogRecord(
        "external.library",
        logging.INFO,
        __file__,
        1,
        "password=sensitive-value otp=sensitive-otp",
        (),
        None,
    )
    serialized = JsonFormatter("test-service").format(record)
    assert "sensitive" not in serialized
    assert "password" not in serialized
    assert "otp" not in serialized
