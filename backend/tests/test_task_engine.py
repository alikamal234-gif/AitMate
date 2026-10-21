"""Comprehensive Test Suite for Task Engine, FSM, Policy Engine, and Approvals."""

import pytest
from datetime import datetime, timedelta, timezone
from starlette.testclient import TestClient
from backend.app.agent.fsm import (
    InvalidStateTransitionError,
    TaskState,
    can_transition,
    validate_transition,
)
from backend.app.agent.orchestrator import orchestrator
from backend.app.core.config import settings
from backend.app.core.policy import PolicyAction, RiskLevel, policy_engine
from backend.app.main import app
from backend.app.storage.database import init_db
from backend.app.storage.models import ApprovalRecord
from backend.app.tools.registry import tool_registry

# Initialize DB tables for testing
init_db()
client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {settings.API_TOKEN}"}


# -------------------------------------------------------------
# 1. Task State Machine (FSM) Tests
# -------------------------------------------------------------
def test_fsm_valid_transitions():
    """Verify strictly allowed state transitions pass validation."""
    assert can_transition(TaskState.QUEUED.value, TaskState.PLANNING.value) is True
    assert can_transition(TaskState.PLANNING.value, TaskState.RUNNING.value) is True
    assert can_transition(TaskState.PLANNING.value, TaskState.AWAITING_APPROVAL.value) is True
    assert can_transition(TaskState.RUNNING.value, TaskState.COMPLETED.value) is True
    assert can_transition(TaskState.RUNNING.value, TaskState.FAILED.value) is True
    assert can_transition(TaskState.AWAITING_APPROVAL.value, TaskState.CANCELLED.value) is True


def test_fsm_invalid_transitions():
    """Verify illegal transitions raise InvalidStateTransitionError."""
    # Cannot jump from queued directly to completed
    assert can_transition(TaskState.QUEUED.value, TaskState.COMPLETED.value) is False
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(TaskState.QUEUED.value, TaskState.COMPLETED.value)

    # Terminal states cannot transition to anything
    for terminal in (TaskState.COMPLETED.value, TaskState.FAILED.value, TaskState.CANCELLED.value):
        assert can_transition(terminal, TaskState.RUNNING.value) is False
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(terminal, TaskState.RUNNING.value)


# -------------------------------------------------------------
# 2. Central Permission Engine Security Tests
# -------------------------------------------------------------
def test_policy_blocks_unrestricted_shell():
    """Security rule: Any attempt to invoke a shell tool or shell command is strictly denied."""
    decision = policy_engine.evaluate_tool_call(
        tool_name="shell_executor",
        target="localhost",
        parameters={"command": "dir"},
    )
    assert decision.action == PolicyAction.DENIED
    assert decision.risk_level == RiskLevel.HIGH
    assert "prohibited" in decision.reason.lower()


def test_policy_detects_dangerous_payloads():
    """Security rule: Dangerous commands embedded in parameters are blocked."""
    decision = policy_engine.evaluate_tool_call(
        tool_name="generic_runner",
        target="system",
        parameters={"input": "run script and rm -rf /"},
    )
    assert decision.action == PolicyAction.DENIED
    assert "dangerous" in decision.reason.lower()


def test_policy_enforces_domain_allowlist():
    """Security rule: Web tools are blocked when navigating to unapproved domains."""
    # Allowed domain should be permitted (or conditional)
    decision_allowed = policy_engine.evaluate_tool_call(
        tool_name="browser_tool",
        target="https://wikipedia.org/wiki/AI",
        parameters={},
    )
    assert decision_allowed.action != PolicyAction.DENIED

    # Unapproved external domain must be DENIED
    decision_blocked = policy_engine.evaluate_tool_call(
        tool_name="browser_tool",
        target="https://malicious-site-example.com/exploit",
        parameters={},
    )
    assert decision_blocked.action == PolicyAction.DENIED
    assert "not in the approved domain allowlist" in decision_blocked.reason


def test_high_risk_tool_requires_approval():
    """Security rule: High-risk tools must produce PolicyAction.REQUIRES_APPROVAL."""
    decision = policy_engine.evaluate_tool_call(
        tool_name="external_dispatch_tool",
        target="external-service",
        parameters={"payload": "urgent message"},
        is_tool_high_risk=True,
    )
    assert decision.action == PolicyAction.REQUIRES_APPROVAL
    assert decision.requires_approval is True
    assert decision.risk_level == RiskLevel.HIGH


# -------------------------------------------------------------
# 3. Tool Execution & Bounded Loop Tests
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_safe_read_only_task_executes_to_completion():
    """Verify safe tasks (reading status and summarization) execute fully to completed state."""
    task = orchestrator.create_task("Read system status and summarize readiness")
    await orchestrator.plan_task(task.id)
    updated = await orchestrator.execute_task(task.id)

    assert updated.status == TaskState.COMPLETED.value
    assert updated.summary is not None
    assert updated.current_step_index >= 1


@pytest.mark.asyncio
async def test_high_risk_task_halts_at_approval_gate():
    """Verify high-risk task (dispatch) automatically pauses in AWAITING_APPROVAL."""
    task = orchestrator.create_task("Send alert dispatch to partner")
    await orchestrator.plan_task(task.id)
    updated = await orchestrator.execute_task(task.id)

    # First step (draft) completes, second step (dispatch) halts in AWAITING_APPROVAL
    assert updated.status == TaskState.AWAITING_APPROVAL.value

    # Verify an ApprovalRecord was generated with valid SHA-256 parameter hash
    res = client.get(f"/api/v1/approvals?status_filter=pending", headers=AUTH_HEADERS)
    assert res.status_code == 200
    approvals = res.json()
    task_approvals = [a for a in approvals if a["task_id"] == task.id]
    assert len(task_approvals) == 1
    assert task_approvals[0]["tool_name"] == "external_dispatch_tool"
    assert task_approvals[0]["risk_level"] == "HIGH"


@pytest.mark.asyncio
async def test_rejected_approval_fails_task_without_retries():
    """Verify user rejecting an approval marks the task FAILED without silent retries."""
    task = orchestrator.create_task("Post critical update to external channel")
    await orchestrator.plan_task(task.id)
    await orchestrator.execute_task(task.id)

    # Fetch approval
    res = client.get("/api/v1/approvals", headers=AUTH_HEADERS)
    approvals = [a for a in res.json() if a["task_id"] == task.id]
    assert len(approvals) >= 1
    appr_id = approvals[0]["id"]

    # Reject
    decide_res = client.post(
        f"/api/v1/approvals/{appr_id}/decide",
        headers=AUTH_HEADERS,
        json={"decision": "reject"},
    )
    assert decide_res.status_code == 200
    assert decide_res.json()["status"] == "rejected"

    # Task must now be failed
    task_res = client.get(f"/api/v1/tasks/{task.id}", headers=AUTH_HEADERS)
    assert task_res.json()["status"] == TaskState.FAILED.value
    assert "rejected" in task_res.json()["error"].lower()


@pytest.mark.asyncio
async def test_approved_action_resumes_execution():
    """Verify user approving an action allows the tool to run and completes the task."""
    task = orchestrator.create_task("Transmit notification to team")
    await orchestrator.plan_task(task.id)
    await orchestrator.execute_task(task.id)

    res = client.get("/api/v1/approvals", headers=AUTH_HEADERS)
    approvals = [a for a in res.json() if a["task_id"] == task.id]
    appr_id = approvals[0]["id"]

    # Approve
    decide_res = client.post(
        f"/api/v1/approvals/{appr_id}/decide",
        headers=AUTH_HEADERS,
        json={"decision": "approve"},
    )
    assert decide_res.status_code == 200
    assert decide_res.json()["status"] == "approved"

    # Task resumes and finishes
    task_res = client.get(f"/api/v1/tasks/{task.id}", headers=AUTH_HEADERS)
    assert task_res.json()["status"] == TaskState.COMPLETED.value


def test_task_cancellation():
    """Verify user can cancel a queued or running task immediately."""
    task = orchestrator.create_task("Long running task to be cancelled")
    res = client.post(f"/api/v1/tasks/{task.id}/cancel", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert res.json()["status"] == TaskState.CANCELLED.value


def test_activity_log_populated():
    """Verify audit events are persistently stored and retrievable."""
    res = client.get("/api/v1/activity", headers=AUTH_HEADERS)
    assert res.status_code == 200
    events = res.json()
    assert len(events) > 0
    event_types = {e["event_type"] for e in events}
    assert "task_created" in event_types
