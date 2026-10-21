"""Unit and Integration Tests for Health and Auth Boundaries."""

from starlette.testclient import TestClient
from backend.app.core.config import settings
from backend.app.core.security import redact_dict, redact_secrets
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify public health endpoint returns 200 and accurate system metadata."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == settings.APP_NAME
    assert data["bound_host"] in ("127.0.0.1", "localhost")
    assert data["bound_port"] == 8000
    assert "timestamp" in data
    assert isinstance(data["allowed_domains"], list)


def test_status_endpoint_unauthorized():
    """Verify accessing protected telemetry without a token returns 401 Unauthorized."""
    response = client.get("/api/v1/status")
    assert response.status_code == 401


def test_status_endpoint_invalid_token():
    """Verify accessing protected telemetry with an invalid token returns 403 Forbidden."""
    headers = {"Authorization": "Bearer totally_invalid_token"}
    response = client.get("/api/v1/status", headers=headers)
    assert response.status_code == 403


def test_status_endpoint_authorized():
    """Verify accessing protected telemetry with valid token returns 200 OK."""
    headers = {"Authorization": f"Bearer {settings.API_TOKEN}"}
    response = client.get("/api/v1/status", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["db_connected"] is True
    assert data["session_token_prefix"].startswith(settings.API_TOKEN[:6])


def test_secret_redaction():
    """Verify regex redactor properly scrubs keys, bearer tokens, and passwords."""
    raw_str = "Connecting with sk-proj-1234567890abcdef1234567890 to service"
    redacted = redact_secrets(raw_str)
    assert "sk-proj-" not in redacted
    assert "[REDACTED_API_KEY]" in redacted

    raw_dict = {
        "user": "alice",
        "api_key": "secret_key_value",
        "nested": {"password": "super_secret_123"},
    }
    cleaned = redact_dict(raw_dict)
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["nested"]["password"] == "[REDACTED]"
    assert cleaned["user"] == "alice"
