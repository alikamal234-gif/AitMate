"""Unit and API integration tests for notifications and background manager."""

import pytest
from fastapi.testclient import TestClient
from backend.app.agent.orchestrator import orchestrator
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.services.background_manager import BackgroundMode, background_manager
from backend.app.services.notifications import (
    NotificationPriority,
    notification_service,
)

client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {settings.API_TOKEN}"}


@pytest.fixture(autouse=True)
def reset_services():
    """Ensure clean state before each test."""
    background_manager.mode = BackgroundMode.ACTIVE
    notification_service.clear()
    notification_service.update_preferences(enabled=True)


def test_notification_service_send_and_read():
    item = notification_service.send(
        title="Test Notification",
        body="This is a test notification body.",
        priority=NotificationPriority.INFO,
    )
    assert item.title == "Test Notification"
    assert not item.read
    assert notification_service.get_unread_count() == 1

    marked = notification_service.mark_read(item.id)
    assert marked is True
    assert notification_service.get_unread_count() == 0


def test_notification_suppression_when_disabled():
    notification_service.update_preferences(enabled=False)
    item = notification_service.send(
        title="Suppressed",
        body="Should not trigger native notifications",
        priority=NotificationPriority.WARNING,
    )
    assert item is not None
    # Still saved in history
    assert len(notification_service.list_recent()) == 1


def test_background_manager_pause_and_resume():
    status = background_manager.get_status()
    assert status["mode"] == BackgroundMode.ACTIVE.value
    assert not status["is_paused"]

    paused = background_manager.pause()
    assert paused["mode"] == BackgroundMode.PAUSED.value
    assert paused["is_paused"] is True

    resumed = background_manager.resume()
    assert resumed["mode"] == BackgroundMode.ACTIVE.value
    assert not resumed["is_paused"]


@pytest.mark.asyncio
async def test_orchestrator_triggers_notifications():
    # 1. Approval Required Notification
    high_risk_task = orchestrator.create_task("Send a critical report to client")
    await orchestrator.execute_task(high_risk_task.id)

    recent = notification_service.list_recent()
    approval_notifications = [
        n for n in recent if n.priority == NotificationPriority.APPROVAL_REQUIRED
    ]
    assert len(approval_notifications) >= 1
    assert "Approval Required" in approval_notifications[0].title

    # 2. Safe Completed Task Notification
    safe_task = orchestrator.create_task("Read system telemetry and app status")
    await orchestrator.execute_task(safe_task.id)

    recent = notification_service.list_recent()
    completion_notifications = [
        n for n in recent if n.title == "Task Completed"
    ]
    assert len(completion_notifications) >= 1


def test_notifications_api_endpoints():
    notification_service.send(
        title="API Test",
        body="Testing via HTTP",
        priority=NotificationPriority.INFO,
    )

    # 1. List notifications
    res = client.get("/api/v1/notifications", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["unread_count"] >= 1
    notif_id = data["notifications"][0]["id"]

    # 2. Mark read
    res_read = client.post(f"/api/v1/notifications/{notif_id}/read", headers=AUTH_HEADERS)
    assert res_read.status_code == 200
    assert res_read.json()["status"] == "read"

    # 3. Background status and pause/resume
    res_bg = client.get("/api/v1/background/status", headers=AUTH_HEADERS)
    assert res_bg.status_code == 200
    assert "mode" in res_bg.json()

    res_pause = client.post("/api/v1/background/pause", headers=AUTH_HEADERS)
    assert res_pause.status_code == 200
    assert res_pause.json()["mode"] == "paused"

    res_resume = client.post("/api/v1/background/resume", headers=AUTH_HEADERS)
    assert res_resume.status_code == 200
    assert res_resume.json()["mode"] == "active"
