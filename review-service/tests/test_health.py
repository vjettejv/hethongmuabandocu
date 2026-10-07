import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from common import health
from common.logging import JsonFormatter
from django.conf import settings
from django.db import OperationalError


@pytest.mark.parametrize("path", ["/health", "/ready"])
def test_foundation_json(client, monkeypatch, path):
    monkeypatch.setattr(health, "database_connected", lambda: True)
    response = client.get(path)
    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/json")
    assert response.json()["service"] == Path(__file__).resolve().parents[1].name
    assert response.json()["status"] == ("healthy" if path == "/health" else "ready")


def test_health_does_not_connect_database(client, monkeypatch):
    def fail():
        raise AssertionError("health must not access DB")

    monkeypatch.setattr(health, "database_connected", fail)
    assert client.get("/health", HTTP_AUTHORIZATION="Bearer invalid").json() == {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
    }


def test_readiness_failure_is_safe(client, monkeypatch):
    monkeypatch.setattr(health, "database_connected", lambda: False)
    response = client.get("/ready")
    if settings.DATABASE_BACKED:
        assert response.status_code == 503
        assert response.json() == {
            "service": settings.SERVICE_NAME,
            "status": "not_ready",
            "database": "unavailable",
        }
    else:
        assert response.status_code == 200
        assert "database" not in response.json()


def test_readiness_query_is_read_only(monkeypatch):
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)
    context = MagicMock()
    context.__enter__.return_value = cursor
    monkeypatch.setattr(health, "connection", SimpleNamespace(cursor=lambda: context))
    assert health.database_connected() is True
    cursor.execute.assert_called_once_with("SELECT 1")


def test_readiness_hides_database_error(monkeypatch):
    def unavailable():
        raise OperationalError("sensitive connection details")

    monkeypatch.setattr(health, "connection", SimpleNamespace(cursor=unavailable))
    assert health.database_connected() is False


def test_request_id_generated(client):
    response = client.get("/health")
    UUID(response["X-Request-ID"])


def test_request_id_preserved(client):
    response = client.get("/health", HTTP_X_REQUEST_ID="phase1-safe-request")
    assert response["X-Request-ID"] == "phase1-safe-request"


def test_invalid_request_id_replaced(client):
    UUID(client.get("/health", HTTP_X_REQUEST_ID="x" * 129)["X-Request-ID"])


def test_cors_allowlist(client):
    response = client.get("/health", HTTP_ORIGIN="http://localhost:5173")
    assert response["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert "Origin" in response["Vary"]
    blocked = client.get("/health", HTTP_ORIGIN="https://untrusted.invalid")
    assert "Access-Control-Allow-Origin" not in blocked


def test_cors_preflight(client):
    response = client.options(
        "/health", HTTP_ORIGIN="http://localhost:5173", HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET"
    )
    assert response.status_code == 204
    assert "X-Request-ID" in response["Access-Control-Allow-Headers"]


def test_schema_documents_business_and_foundation(client):
    response = client.get("/schema/", HTTP_ACCEPT="application/vnd.oai.openapi+json")
    assert response.status_code == 200
    assert set(response.json()["paths"]) == {"/health", "/ready", "/", "/user/{userId}", "/{id}"}
    assert client.get("/docs/").status_code == 200


def test_no_business_routes(client):
    assert client.post("/login", data={"password": "do-not-log"}).status_code == 404


def test_no_system_models_or_pagination():
    assert "django.contrib.auth" not in settings.INSTALLED_APPS
    assert "django.contrib.sessions" not in settings.INSTALLED_APPS
    assert settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] == []
    assert "DEFAULT_PAGINATION_CLASS" not in settings.REST_FRAMEWORK
    if not settings.DATABASE_BACKED:
        assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.dummy"


def test_request_log_metadata_no_secrets(client, caplog):
    import logging

    with caplog.at_level(logging.INFO, logger="foundation.request"):
        client.get(
            "/health?otp=sensitive-otp",
            HTTP_AUTHORIZATION="Bearer sensitive-token",
            HTTP_X_REQUEST_ID="safe-log-request",
        )
    record = next(r for r in caplog.records if r.name == "foundation.request")
    data = json.loads(JsonFormatter(settings.SERVICE_NAME).format(record))
    assert data["request_id"] == "safe-log-request"
    assert data["method"] == "GET"
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
