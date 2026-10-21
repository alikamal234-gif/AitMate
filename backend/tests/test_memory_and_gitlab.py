"""Unit and API integration tests for user-controlled local memory and GitLab read-only tools."""

import pytest
from fastapi.testclient import TestClient
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.services.memory_service import memory_service
from backend.app.tools.gitlab_tool import (
    GitLabCiStatusTool,
    GitLabMergeRequestTool,
    GitLabProjectSummaryTool,
)
from backend.app.tools.registry import tool_registry

client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {settings.API_TOKEN}"}


@pytest.fixture(autouse=True)
def clean_memory_store():
    """Ensure clean memory table before each test."""
    memory_service.clear()


def test_memory_service_crud_and_search():
    # 1. Create memories
    m1 = memory_service.set("preferred_editor", "vscode", category="preference")
    m2 = memory_service.set("target_platform", "windows-x64", category="project")
    assert m1.id is not None
    assert m2.id is not None

    # 2. Search memories
    results = memory_service.list(search="vscode")
    assert len(results) == 1
    assert results[0].key == "preferred_editor"

    # 3. Filter by category
    project_mems = memory_service.list(category="project")
    assert len(project_mems) == 1
    assert project_mems[0].key == "target_platform"

    # 4. Export all
    exported = memory_service.export_all()
    assert len(exported) == 2

    # 5. Delete single
    assert memory_service.delete(m1.id) is True
    assert memory_service.get(m1.id) is None

    # 6. Clear all
    purged = memory_service.clear()
    assert purged == 1
    assert len(memory_service.list()) == 0


def test_memory_api_endpoints():
    # Create memory via API
    res = client.post(
        "/api/v1/memory",
        headers=AUTH_HEADERS,
        json={"key": "api_pref", "content": "REST only", "category": "preference"},
    )
    assert res.status_code == 200
    created = res.json()
    assert created["key"] == "api_pref"
    mem_id = created["id"]

    # List memories
    res_list = client.get("/api/v1/memory", headers=AUTH_HEADERS)
    assert res_list.status_code == 200
    assert res_list.json()["count"] == 1

    # Export memories
    res_export = client.get("/api/v1/memory/export", headers=AUTH_HEADERS)
    assert res_export.status_code == 200
    assert res_export.json()["total_records"] == 1

    # Delete memory
    res_del = client.delete(f"/api/v1/memory/{mem_id}", headers=AUTH_HEADERS)
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "deleted"

    # Clear memories
    res_clear = client.post("/api/v1/memory/clear", headers=AUTH_HEADERS)
    assert res_clear.status_code == 200
    assert res_clear.json()["status"] == "cleared"


@pytest.mark.asyncio
async def test_gitlab_project_summary_tool():
    tool = GitLabProjectSummaryTool()
    assert tool.is_read_only if hasattr(tool, "is_read_only") else True
    assert not tool.requires_approval

    res = await tool.execute({"project_path": "organization/repo", "gitlab_host": "gitlab.com"})
    assert res["status"] == "success"
    assert res["is_read_only"] is True
    assert "<untrusted_web_content>" in res["description"]
    assert "</untrusted_web_content>" in res["description"]


@pytest.mark.asyncio
async def test_gitlab_merge_request_tool():
    tool = GitLabMergeRequestTool()
    res = await tool.execute({"project_path": "organization/repo", "gitlab_host": "gitlab.com"})
    assert res["status"] == "success"
    assert len(res["merge_requests"]) >= 1
    mr = res["merge_requests"][0]
    assert "<untrusted_web_content>" in mr["description"]


@pytest.mark.asyncio
async def test_gitlab_ci_status_tool():
    tool = GitLabCiStatusTool()
    res = await tool.execute({"project_path": "organization/repo", "ref": "main", "gitlab_host": "gitlab.com"})
    assert res["status"] == "success"
    assert res["pipeline_status"] == "success"
    assert len(res["jobs"]) >= 1


@pytest.mark.asyncio
async def test_gitlab_blocks_unauthorized_host():
    tool = GitLabProjectSummaryTool()
    with pytest.raises(PermissionError) as exc_info:
        await tool.execute({"project_path": "repo", "gitlab_host": "evil-untrusted-host.com"})
    assert "not in the approved domain allowlist" in str(exc_info.value)


def test_registry_contains_gitlab_tools():
    assert tool_registry.get("gitlab_project_tool") is not None
    assert tool_registry.get("gitlab_mr_tool") is not None
    assert tool_registry.get("gitlab_ci_tool") is not None
