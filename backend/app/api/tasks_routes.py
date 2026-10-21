"""Task, Approval, and Activity REST Endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session, desc, select
from backend.app.agent.orchestrator import orchestrator
from backend.app.core.security import verify_session_token
from backend.app.storage.database import get_session
from backend.app.storage.models import ApprovalRecord, AuditEventRecord, TaskRecord

router = APIRouter(prefix="/api/v1", tags=["Tasks & Approvals"])


class CreateTaskRequest(BaseModel):
    instruction: str = Field(..., min_length=3, description="Natural language user instruction")


class DecideApprovalRequest(BaseModel):
    decision: str = Field(..., description="Approval decision: 'approve' or 'reject'")


# -------------------------------------------------------------
# Tasks Endpoints
# -------------------------------------------------------------
@router.post("/tasks", summary="Create and Launch Task")
async def create_task(
    payload: CreateTaskRequest,
    token: str = Depends(verify_session_token),
):
    """Create a new task, generate a bounded plan, and start execution."""
    task = orchestrator.create_task(payload.instruction)
    orchestrator.plan_task(task.id)
    # Execute until completion or approval pause
    updated_task = await orchestrator.execute_task(task.id)
    return {
        "id": updated_task.id,
        "instruction": updated_task.instruction,
        "status": updated_task.status,
        "current_step_index": updated_task.current_step_index,
        "plan": updated_task.get_plan(),
        "summary": updated_task.summary,
        "error": updated_task.error,
        "created_at": updated_task.created_at,
    }


@router.get("/tasks", summary="List Tasks")
async def list_tasks(
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    token: str = Depends(verify_session_token),
):
    """List recent tasks in reverse chronological order."""
    statement = select(TaskRecord).order_by(desc(TaskRecord.created_at)).limit(limit)
    tasks = session.exec(statement).all()
    return [
        {
            "id": t.id,
            "instruction": t.instruction,
            "status": t.status,
            "current_step_index": t.current_step_index,
            "plan": t.get_plan(),
            "summary": t.summary,
            "error": t.error,
            "created_at": t.created_at,
            "completed_at": t.completed_at,
        }
        for t in tasks
    ]


@router.get("/tasks/{task_id}", summary="Get Task Details")
async def get_task(
    task_id: str,
    session: Session = Depends(get_session),
    token: str = Depends(verify_session_token),
):
    """Retrieve detailed task record by ID."""
    task = session.get(TaskRecord, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return {
        "id": task.id,
        "instruction": task.instruction,
        "status": task.status,
        "current_step_index": task.current_step_index,
        "plan": task.get_plan(),
        "summary": task.summary,
        "error": task.error,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
    }


@router.post("/tasks/{task_id}/cancel", summary="Cancel Task")
async def cancel_task(
    task_id: str,
    token: str = Depends(verify_session_token),
):
    """Cancel an active or pending task."""
    try:
        task = orchestrator.cancel_task(task_id)
        return {"id": task.id, "status": task.status, "message": "Task cancelled successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------
# Approvals Endpoints
# -------------------------------------------------------------
@router.get("/approvals", summary="List Pending Approvals")
async def list_approvals(
    status_filter: Optional[str] = Query(default="pending"),
    session: Session = Depends(get_session),
    token: str = Depends(verify_session_token),
):
    """List human authorization requests."""
    statement = select(ApprovalRecord)
    if status_filter:
        statement = statement.where(ApprovalRecord.status == status_filter)
    statement = statement.order_by(desc(ApprovalRecord.created_at))
    approvals = session.exec(statement).all()
    return [
        {
            "id": a.id,
            "task_id": a.task_id,
            "step_index": a.step_index,
            "tool_name": a.tool_name,
            "target": a.target,
            "parameters": a.get_parameters(),
            "reason": a.reason,
            "risk_level": a.risk_level,
            "status": a.status,
            "created_at": a.created_at,
            "expires_at": a.expires_at,
        }
        for a in approvals
    ]


@router.post("/approvals/{approval_id}/decide", summary="Decide Approval")
async def decide_approval(
    approval_id: str,
    payload: DecideApprovalRequest,
    token: str = Depends(verify_session_token),
):
    """Grant or reject an approval request."""
    try:
        updated = await orchestrator.decide_approval(approval_id, payload.decision)
        return {
            "id": updated.id,
            "status": updated.status,
            "tool_name": updated.tool_name,
            "target": updated.target,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------
# Activity & Audit Log Endpoints
# -------------------------------------------------------------
@router.get("/activity", summary="List Activity Log")
async def list_activity(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    token: str = Depends(verify_session_token),
):
    """Retrieve chronologically ordered audit events."""
    statement = select(AuditEventRecord).order_by(desc(AuditEventRecord.timestamp)).limit(limit)
    events = session.exec(statement).all()
    return [
        {
            "id": e.id,
            "timestamp": e.timestamp,
            "event_type": e.event_type,
            "task_id": e.task_id,
            "tool_name": e.tool_name,
            "summary": e.summary,
            "details": e.get_details(),
        }
        for e in events
    ]
