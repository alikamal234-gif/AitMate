"""API Routes for Desktop Notifications and Background Manager."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from backend.app.core.security import verify_session_token
from backend.app.services.notifications import (
    NotificationItem,
    NotificationPreferences,
    notification_service,
)
from backend.app.services.background_manager import background_manager

router = APIRouter(prefix="/api/v1", tags=["Notifications & Background Mode"])


class NotificationListResponse(BaseModel):
    unread_count: int
    notifications: List[NotificationItem]


class UpdatePreferencesRequest(BaseModel):
    enabled: Optional[bool] = None
    sound: Optional[bool] = None


@router.get(
    "/notifications",
    response_model=NotificationListResponse,
    dependencies=[Depends(verify_session_token)],
    summary="List recent notifications and unread count",
)
def list_notifications(limit: int = 20) -> NotificationListResponse:
    return NotificationListResponse(
        unread_count=notification_service.get_unread_count(),
        notifications=notification_service.list_recent(limit=limit),
    )


@router.post(
    "/notifications/{notification_id}/read",
    dependencies=[Depends(verify_session_token)],
    summary="Mark single notification as read",
)
def mark_notification_read(notification_id: str) -> Dict[str, Any]:
    success = notification_service.mark_read(notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{notification_id}' not found.",
        )
    return {"status": "read", "id": notification_id}


@router.post(
    "/notifications/read-all",
    dependencies=[Depends(verify_session_token)],
    summary="Mark all notifications as read",
)
def mark_all_notifications_read() -> Dict[str, Any]:
    count = notification_service.mark_all_read()
    return {"status": "all_read", "marked_count": count}


@router.post(
    "/notifications/clear",
    dependencies=[Depends(verify_session_token)],
    summary="Clear notification history",
)
def clear_notifications() -> Dict[str, Any]:
    notification_service.clear()
    return {"status": "cleared"}


@router.get(
    "/notifications/preferences",
    response_model=NotificationPreferences,
    dependencies=[Depends(verify_session_token)],
    summary="Get notification settings",
)
def get_preferences() -> NotificationPreferences:
    return notification_service.get_preferences()


@router.put(
    "/notifications/preferences",
    response_model=NotificationPreferences,
    dependencies=[Depends(verify_session_token)],
    summary="Update notification preferences",
)
def update_preferences(req: UpdatePreferencesRequest) -> NotificationPreferences:
    return notification_service.update_preferences(enabled=req.enabled, sound=req.sound)


@router.get(
    "/background/status",
    dependencies=[Depends(verify_session_token)],
    summary="Query background execution status and active tasks",
)
def get_background_status() -> Dict[str, Any]:
    return background_manager.get_status()


@router.post(
    "/background/pause",
    dependencies=[Depends(verify_session_token)],
    summary="Pause agent task execution queue",
)
def pause_background_execution() -> Dict[str, Any]:
    return background_manager.pause()


@router.post(
    "/background/resume",
    dependencies=[Depends(verify_session_token)],
    summary="Resume agent task execution queue",
)
def resume_background_execution() -> Dict[str, Any]:
    return background_manager.resume()


@router.post(
    "/background/cancel-all",
    dependencies=[Depends(verify_session_token)],
    summary="Emergency Kill Switch: cancel all pending and running tasks",
)
def emergency_cancel_all() -> Dict[str, Any]:
    return background_manager.emergency_cancel_all()
