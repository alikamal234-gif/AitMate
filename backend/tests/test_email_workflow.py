"""Unit and integration tests for email drafting and dispatch workflow."""

import pytest
from backend.app.core.policy import RiskLevel
from backend.app.tools.email_workflow import (
    EmailDraftTool,
    EmailSendTool,
    get_email_integration_status,
)
from backend.app.tools.registry import tool_registry


@pytest.mark.asyncio
async def test_email_draft_tool_safe_execution():
    tool = EmailDraftTool()
    assert tool.risk_level == RiskLevel.LOW
    assert not tool.requires_approval

    params = {
        "recipient": "partner@example.com",
        "subject": "Q3 Progress Review",
        "body": "Here is our quarterly status update.",
        "urgency": "normal",
    }
    result = await tool.execute(params)
    assert result["status"] == "draft_created"
    assert result["is_sent"] is False
    assert result["requires_human_send_approval"] is True
    assert result["recipient"] == "partner@example.com"


@pytest.mark.asyncio
async def test_email_send_tool_requires_approval():
    tool = EmailSendTool()
    assert tool.risk_level == RiskLevel.HIGH
    assert tool.requires_approval is True

    params = {
        "recipient": "client@example.com",
        "subject": "Production Deployment Notice",
        "body": "System maintenance is complete.",
    }
    result = await tool.execute(params)
    assert result["status"] == "sent"
    assert result["verified_by_human_approval"] is True
    assert result["bytes_sent"] == len(params["body"])


def test_email_integration_status_truthful():
    status = get_email_integration_status()
    assert status.provider == "gmail_oauth2"
    assert status.is_connected is False
    assert "https://www.googleapis.com/auth/gmail.readonly" in status.required_scopes
    assert "https://www.googleapis.com/auth/gmail.compose" in status.required_scopes


def test_registry_contains_email_tools():
    draft_tool = tool_registry.get("email_draft_tool")
    send_tool = tool_registry.get("email_send_tool")
    assert draft_tool is not None
    assert send_tool is not None
    assert draft_tool.requires_approval is False
    assert send_tool.requires_approval is True
