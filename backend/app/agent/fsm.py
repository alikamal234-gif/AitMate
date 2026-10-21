"""Deterministic Task State Machine (FSM)."""

from enum import Enum
from typing import Dict, Set


class TaskState(str, Enum):
    """Permitted task lifecycle states."""

    QUEUED = "queued"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InvalidStateTransitionError(Exception):
    """Raised when an illegal state machine transition is attempted."""

    def __init__(self, from_state: str, to_state: str, reason: str = ""):
        message = f"Illegal task transition from '{from_state}' to '{to_state}'. {reason}".strip()
        super().__init__(message)
        self.from_state = from_state
        self.to_state = to_state


# Directed graph of strictly permitted state transitions
VALID_TRANSITIONS: Dict[TaskState, Set[TaskState]] = {
    TaskState.QUEUED: {
        TaskState.PLANNING,
        TaskState.CANCELLED,
    },
    TaskState.PLANNING: {
        TaskState.RUNNING,
        TaskState.AWAITING_APPROVAL,
        TaskState.FAILED,
        TaskState.CANCELLED,
    },
    TaskState.AWAITING_APPROVAL: {
        TaskState.RUNNING,
        TaskState.FAILED,
        TaskState.CANCELLED,
    },
    TaskState.RUNNING: {
        TaskState.AWAITING_APPROVAL,
        TaskState.RUNNING,  # Consecutive steps within execution loop
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.CANCELLED,
    },
    # Terminal states: Once reached, no transitions are permitted
    TaskState.COMPLETED: set(),
    TaskState.FAILED: set(),
    TaskState.CANCELLED: set(),
}


def can_transition(from_state: str, to_state: str) -> bool:
    """Check if transition between states is permissible."""
    try:
        source = TaskState(from_state)
        target = TaskState(to_state)
        return target in VALID_TRANSITIONS.get(source, set())
    except ValueError:
        return False


def validate_transition(from_state: str, to_state: str) -> None:
    """Validate transition and raise InvalidStateTransitionError on violation."""
    try:
        source = TaskState(from_state)
        target = TaskState(to_state)
    except ValueError as e:
        raise InvalidStateTransitionError(from_state, to_state, reason=f"Unknown state value: {e}")

    allowed_targets = VALID_TRANSITIONS.get(source, set())
    if target not in allowed_targets:
        if not allowed_targets:
            raise InvalidStateTransitionError(
                from_state,
                to_state,
                reason=f"State '{from_state}' is terminal and cannot transition further.",
            )
        raise InvalidStateTransitionError(
            from_state,
            to_state,
            reason=f"Allowed targets from '{from_state}' are: {[s.value for s in allowed_targets]}",
        )
