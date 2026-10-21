"""Unit and Integration Tests for AI Provider Abstraction and Health Diagnostics."""

import pytest
from starlette.testclient import TestClient
from backend.app.agent.providers.base import PlannedStepSchema
from backend.app.agent.providers.factory import active_provider, get_ai_provider
from backend.app.agent.providers.mock_provider import MockProvider
from backend.app.agent.providers.ollama_provider import OllamaProvider
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.tools.registry import tool_registry

client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {settings.API_TOKEN}"}


@pytest.mark.asyncio
async def test_mock_provider_generates_valid_plan():
    """Verify MockProvider produces structured plans matching available tools."""
    provider = MockProvider()
    tools = tool_registry.list_all()

    plan = await provider.generate_plan("Summarize system security", tools)
    assert len(plan) >= 1
    for step in plan:
        validated = PlannedStepSchema(**step)
        assert validated.step_number >= 1
        assert validated.tool_name in [t["name"] for t in tools]


@pytest.mark.asyncio
async def test_mock_provider_test_connection():
    """Verify MockProvider test_connection reports available and reports latency."""
    provider = MockProvider()
    result = await provider.test_connection()
    assert result.is_available is True
    assert result.provider_name == "mock"
    assert result.latency_ms is not None
    assert result.is_local is True


@pytest.mark.asyncio
async def test_ollama_provider_handles_offline_gracefully():
    """Verify OllamaProvider reports offline honestly without crashing when Ollama is not running."""
    # Point to an unallocated loopback port
    ollama = OllamaProvider(base_url="http://127.0.0.1:59999", model="llama3.2:latest")
    result = await ollama.test_connection()
    assert result.is_available is False
    assert result.provider_name == "ollama"
    assert "offline" in result.details.lower() or "unreachable" in result.details.lower()


@pytest.mark.asyncio
async def test_ollama_provider_falls_back_to_safe_plan_when_unreachable():
    """Verify that when Ollama is offline, generate_plan falls back safely to mock plan."""
    ollama = OllamaProvider(base_url="http://127.0.0.1:59999", model="llama3.2:latest")
    tools = tool_registry.list_all()
    plan = await ollama.generate_plan("Read app status", tools)
    assert len(plan) >= 1
    assert plan[0]["tool_name"] == "app_status_tool"


def test_provider_test_api_endpoint():
    """Verify /api/v1/provider/test endpoint returns real status and latency."""
    res = client.get("/api/v1/provider/test", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "provider_name" in data
    assert "is_available" in data
    assert "details" in data


def test_planned_step_validation_rejects_malformed_step():
    """Verify PlannedStepSchema rejects invalid step numbers or missing fields."""
    with pytest.raises(Exception):
        # step_number must be >= 1
        PlannedStepSchema(step_number=0, description="Invalid", tool_name="tool")

    with pytest.raises(Exception):
        # description cannot be empty
        PlannedStepSchema(step_number=1, description="", tool_name="tool")
