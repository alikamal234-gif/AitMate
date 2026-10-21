"""Background Execution Manager and System Control."""

import logging
from enum import Enum
from typing import Dict, Any
from sqlmodel import Session, select
from backend.app.storage.database import engine
from backend.app.storage.models import TaskRecord
from backend.app.agent.fsm import TaskState
from backend.app.services.notifications import notification_service, NotificationPriority

logger = logging.getLogger("aitmate.services.background")


class BackgroundMode(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"


class BackgroundManager:
    """Manages background task execution state, pause controls, and emergency halts."""

    def __init__(self):
        self.mode = BackgroundMode.ACTIVE

    def get_status(self) -> Dict[str, Any]:
        """Query current execution state and active task count."""
        with Session(engine, expire_on_commit=False) as session:
            running_tasks = session.exec(
                select(TaskRecord).where(
                    TaskRecord.status.in_([TaskState.RUNNING.value, TaskState.AWAITING_APPROVAL.value])
                )
            ).all()

            return {
                "mode": self.mode.value,
                "is_paused": self.mode == BackgroundMode.PAUSED,
                "active_task_count": len(running_tasks),
                "unread_notifications": notification_service.get_unread_count(),
            }

    def pause(self) -> Dict[str, Any]:
        """Pause agent execution queue."""
        self.mode = BackgroundMode.PAUSED
        logger.warning("Background execution paused by user.")
        notification_service.send(
            title="AitMate Paused",
            body="Task scheduling has been suspended.",
            priority=NotificationPriority.WARNING,
        )
        return self.get_status()

    def resume(self) -> Dict[str, Any]:
        """Resume active agent execution."""
        self.mode = BackgroundMode.ACTIVE
        logger.info("Background execution resumed by user.")
        notification_service.send(
            title="AitMate Resumed",
            body="Active background execution restored.",
            priority=NotificationPriority.INFO,
        )
        return self.get_status()

    def emergency_cancel_all(self, reason: str = "User initiated emergency halt") -> Dict[str, Any]:
        """Kill switch: Cancel all pending, planning, and running tasks immediately."""
        cancelled_count = 0
        with Session(engine, expire_on_commit=False) as session:
            active_tasks = session.exec(
                select(TaskRecord).where(
                    TaskRecord.status.in_([
                        TaskState.QUEUED.value,
                        TaskState.PLANNING.value,
                        TaskState.AWAITING_APPROVAL.value,
                        TaskState.RUNNING.value,
                    ])
                )
            ).all()

            for task in active_tasks:
                task.status = TaskState.CANCELLED.value
                task.error = reason
                session.add(task)
                cancelled_count += 1
            session.commit()

        logger.critical("Emergency halt executed: %d active tasks cancelled.", cancelled_count)
        notification_service.send(
            title="Emergency Halt Triggered",
            body=f"Cancelled {cancelled_count} active tasks.",
            priority=NotificationPriority.ERROR,
        )
        return {
            "status": "halted",
            "cancelled_count": cancelled_count,
            "mode": self.mode.value,
        }


background_manager = BackgroundManager()
