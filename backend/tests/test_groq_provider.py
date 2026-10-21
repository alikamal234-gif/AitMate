"""Unit and integration tests for Groq LPU provider adapter."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from backend.app.agent.providers.groq_provider import GroqProvider
from backend.app.core.security import redact_secrets
from backend.app.tools.registry import tool_registry


@pytest.mark.asyncio
async def test_groq_provider_missing_key_behavior():
    provider = GroqProvider(api_key=None)
    res = await provider.test_connection()
    assert res.is_available is False
    assert "Groq API key is missing" in res.details

    # Generating plan without key should gracefully use fallback without crashing
    plan = await provider.generate_plan("Analyze repository status", tool_registry.list_all())
    assert isinstance(plan, list)
    assert len(plan) >= 1


@pytest.mark.asyncio
async def test_groq_provider_connection_success_mocked():
    provider = GroqProvider(api_key="gsk_test1234567890abcdef1234567890")

    mock_resp = httpx.Response(
        status_code=200,
        json={"data": [{"id": "llama-3.3-70b-versatile"}, {"id": "llama-3.1-8b-instant"}]},
        request=httpx.Request("GET", "https://api.groq.com/openai/v1/models"),
    )

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await provider.test_connection()
        assert res.is_available is True
        assert res.model_name == "llama-3.3-70b-versatile"
        assert "Groq LPU operational" in res.details


@pytest.mark.asyncio
async def test_groq_provider_auth_failure_mocked():
    provider = GroqProvider(api_key="gsk_invalid_key_1234567890abcdef")

    mock_resp = httpx.Response(
        status_code=401,
        json={"error": {"message": "Invalid API Key"}},
        request=httpx.Request("GET", "https://api.groq.com/openai/v1/models"),
    )

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await provider.test_connection()
        assert res.is_available is False
        assert "Invalid API key" in res.details


@pytest.mark.asyncio
async def test_groq_provider_generates_valid_plan_mocked():
    provider = GroqProvider(api_key="gsk_valid_key_1234567890abcdef")

    sample_plan_json = {
        "steps": [
            {
                "step_number": 1,
                "description": "Inspect repository files",
                "tool_name": "file_reader_tool",
                "target": "README.md",
                "parameters": {"relative_path": "README.md"},
            }
        ]
    }

    mock_resp = httpx.Response(
        status_code=200,
        json={
            "choices": [
                {
                    "message": {
                        "content": str(sample_plan_json).replace("'", '"')
                    }
                }
            ]
        },
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        steps = await provider.generate_plan("Read the README file", tool_registry.list_all())
        assert len(steps) == 1
        assert steps[0]["tool_name"] == "file_reader_tool"
        assert steps[0]["target"] == "README.md"


@pytest.mark.asyncio
async def test_groq_provider_network_failure_falls_back():
    provider = GroqProvider(api_key="gsk_valid_key_1234567890abcdef")

    with patch.object(httpx.AsyncClient, "post", side_effect=httpx.ConnectError("Connection refused")):
        # Should gracefully fall back to deterministic plan
        plan = await provider.generate_plan("Check app status", tool_registry.list_all())
        assert isinstance(plan, list)
        assert len(plan) >= 1
        assert plan[0]["tool_name"] == "app_status_tool"


def test_groq_api_key_redaction():
    text_with_key = "Groq configured with gsk_abcdef1234567890abcdef1234567890 and normal text"
    sanitized = redact_secrets(text_with_key)
    assert "gsk_abcdef1234567890abcdef1234567890" not in sanitized
    assert "[REDACTED_GROQ_KEY]" in sanitized
