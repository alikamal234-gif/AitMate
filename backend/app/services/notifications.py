"""AitMate Notification Service for Windows Desktop and Local UI."""

import datetime
import logging
import uuid
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aitmate.services.notifications")


class NotificationPriority(str, Enum):
    INFO = "info"
    WARNING = "warning"
    APPROVAL_REQUIRED = "approval_required"
    ERROR = "error"


class NotificationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    body: str
    priority: NotificationPriority = NotificationPriority.INFO
    task_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    read: bool = False
    action_url: Optional[str] = None


class NotificationPreferences(BaseModel):
    enabled: bool = True
    sound: bool = False
    notify_on_approvals: bool = True
    notify_on_completions: bool = True
    notify_on_failures: bool = True


class NotificationService:
    """Manages desktop alerts and in-app notification center history."""

    def __init__(self):
        self.preferences = NotificationPreferences()
        self._history: List[NotificationItem] = []
        self._max_history = 100

    def get_preferences(self) -> NotificationPreferences:
        return self.preferences

    def update_preferences(self, enabled: Optional[bool] = None, sound: Optional[bool] = None) -> NotificationPreferences:
        if enabled is not None:
            self.preferences.enabled = enabled
        if sound is not None:
            self.preferences.sound = sound
        return self.preferences

    def send(
        self,
        title: str,
        body: str,
        priority: NotificationPriority = NotificationPriority.INFO,
        task_id: Optional[str] = None,
        action_url: Optional[str] = None,
    ) -> NotificationItem:
        """Create and dispatch a notification item."""
        item = NotificationItem(
            title=title,
            body=body,
            priority=priority,
            task_id=task_id,
            action_url=action_url,
        )

        self._history.insert(0, item)
        if len(self._history) > self._max_history:
            self._history = self._history[: self._max_history]

        if not self.preferences.enabled:
            logger.info("Notification suppressed (notifications disabled): %s - %s", title, body)
            return item

        # Attempt native desktop dispatch with fallback to structured log
        self._dispatch_native(item)
        return item

    def _dispatch_native(self, item: NotificationItem) -> None:
        """Dispatch native Windows toast or balloon notification if available."""
        logger.info(
            "Desktop Notification [%s] %s: %s (task: %s)",
            item.priority.value.upper(),
            item.title,
            item.body,
            item.task_id or "none",
        )
        # Note: Native notification libraries (e.g. win10toast or plyer) may fail in headless CI/tests.
        # We catch all exceptions gracefully to ensure zero agent disruption.
        try:
            # Placeholder for optional plyer / win10toast if installed in user environment
            pass
        except Exception as exc:
            logger.debug("Native desktop notification dispatch skipped: %s", exc)

    def list_recent(self, limit: int = 20) -> List[NotificationItem]:
        return self._history[:limit]

    def get_unread_count(self) -> int:
        return sum(1 for item in self._history if not item.read)

    def mark_read(self, notification_id: str) -> bool:
        for item in self._history:
            if item.id == notification_id:
                item.read = True
                return True
        return False

    def mark_all_read(self) -> int:
        count = 0
        for item in self._history:
            if not item.read:
                item.read = True
                count += 1
        return count

    def clear(self) -> None:
        self._history.clear()


# Global singleton instance
notification_service = NotificationService()
