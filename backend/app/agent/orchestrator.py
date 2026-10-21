"""Agent Orchestrator & Bounded Execution Loop."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlmodel import Session, select
from backend.app.agent.fsm import (
    InvalidStateTransitionError,
    TaskState,
    validate_transition,
)
from backend.app.core.policy import PolicyAction, policy_engine
from backend.app.core.security import redact_dict
from backend.app.storage.database import engine
from backend.app.storage.models import ApprovalRecord, AuditEventRecord, TaskRecord
from backend.app.tools.registry import tool_registry
from backend.app.services.notifications import notification_service, NotificationPriority
from backend.app.services.background_manager import background_manager, BackgroundMode

logger = logging.getLogger("aitmate.orchestrator")


class Orchestrator:
    """Bounded task lifecycle executor and policy enforcement coordinator."""

    MAX_STEPS_PER_TASK = 10
    APPROVAL_TIMEOUT_MINUTES = 10

    def create_task(self, instruction: str) -> TaskRecord:
        """Create and persist a new task in QUEUED state."""
        with Session(engine, expire_on_commit=False) as session:
            task = TaskRecord(
                instruction=instruction,
                status=TaskState.QUEUED.value,
            )
            session.add(task)
            session.commit()
            session.refresh(task)

            # Record audit event
            self._record_audit(
                session,
                event_type="task_created",
                task_id=task.id,
                summary=f"Task created with instruction: '{instruction[:60]}...'",
                details={"instruction": instruction},
            )
            return task

    async def plan_task(self, task_id: str) -> TaskRecord:
        """Generate a bounded step-by-step plan for the task using configured AI provider."""
        from backend.app.agent.providers.factory import get_ai_provider

        with Session(engine, expire_on_commit=False) as session:
            task = session.get(TaskRecord, task_id)
            if not task:
                raise ValueError(f"Task '{task_id}' not found.")

            validate_transition(task.status, TaskState.PLANNING.value)
            task.status = TaskState.PLANNING.value
            task.updated_at = datetime.now(timezone.utc).isoformat()
            session.add(task)
            session.commit()

            # Delegate to active AI provider (Mock, Ollama, Groq, etc.)
            provider = get_ai_provider()
            plan = await provider.generate_plan(task.instruction, tool_registry.list_all())
            task.set_plan(plan)
            session.add(task)
            session.commit()
            session.refresh(task)

            self._record_audit(
                session,
                event_type="state_transition",
                task_id=task.id,
                summary=f"Task planned with {len(plan)} steps.",
                details={"plan": plan},
            )
            return task

    async def execute_task(self, task_id: str) -> TaskRecord:
        """Execute task steps within bounded loop until completion or approval gate."""
        if background_manager.mode == BackgroundMode.PAUSED:
            logger.warning("Execution of task '%s' deferred: background execution is paused.", task_id)
            with Session(engine, expire_on_commit=False) as session:
                return session.get(TaskRecord, task_id)

        with Session(engine, expire_on_commit=False) as session:
            task = session.get(TaskRecord, task_id)
            if not task:
                raise ValueError(f"Task '{task_id}' not found.")

            plan = task.get_plan()
            if not plan:
                task = await self.plan_task(task_id)
                plan = task.get_plan()

            # If task is in planning or awaiting_approval, move to running
            if task.status in (TaskState.PLANNING.value, TaskState.AWAITING_APPROVAL.value):
                validate_transition(task.status, TaskState.RUNNING.value)
                task.status = TaskState.RUNNING.value
                task.updated_at = datetime.now(timezone.utc).isoformat()
                session.add(task)
                session.commit()

        # Step through plan sequentially
        while True:
            with Session(engine, expire_on_commit=False) as session:
                task = session.get(TaskRecord, task_id)
                if not task or task.status != TaskState.RUNNING.value:
                    break

                plan = task.get_plan()
                idx = task.current_step_index

                # If all steps are completed
                if idx >= len(plan):
                    validate_transition(task.status, TaskState.COMPLETED.value)
                    task.status = TaskState.COMPLETED.value
                    task.completed_at = datetime.now(timezone.utc).isoformat()
                    task.summary = f"All {len(plan)} task steps executed successfully."
                    session.add(task)
                    session.commit()
                    self._record_audit(
                        session,
                        event_type="task_completed",
                        task_id=task.id,
                        summary=task.summary,
                    )
                    notification_service.send(
                        title="Task Completed",
                        body=task.summary,
                        priority=NotificationPriority.INFO,
                        task_id=task.id,
                    )
                    break

                current_step = plan[idx]
                tool_name = current_step["tool_name"]
                target = current_step.get("target", "localhost")
                parameters = current_step.get("parameters", {})

                tool = tool_registry.get(tool_name)
                if not tool:
                    task.status = TaskState.FAILED.value
                    task.error = f"Registered tool '{tool_name}' not found."
                    session.add(task)
                    session.commit()
                    break

                # 1. Central Policy Evaluation
                decision = policy_engine.evaluate_tool_call(
                    tool_name=tool_name,
                    target=target,
                    parameters=parameters,
                    is_tool_high_risk=tool.requires_approval,
                )

                # Case A: Denied by Policy
                if decision.action == PolicyAction.DENIED:
                    current_step["status"] = "failed"
                    current_step["result"] = f"Policy Denial: {decision.reason}"
                    task.status = TaskState.FAILED.value
                    task.error = decision.reason
                    task.set_plan(plan)
                    session.add(task)
                    session.commit()
                    self._record_audit(
                        session,
                        event_type="security_violation",
                        task_id=task.id,
                        tool_name=tool_name,
                        summary=f"Tool call blocked by policy: {decision.reason}",
                        details={"target": target, "decision": decision.model_dump()},
                    )
                    notification_service.send(
                        title="Policy Denial",
                        body=f"Execution blocked: {decision.reason}",
                        priority=NotificationPriority.ERROR,
                        task_id=task.id,
                    )
                    break

                # Case B: Requires Human Approval
                if decision.action == PolicyAction.REQUIRES_APPROVAL:
                    # Check if an existing approval was already granted for this step
                    statement = select(ApprovalRecord).where(
                        ApprovalRecord.task_id == task.id,
                        ApprovalRecord.step_index == idx,
                        ApprovalRecord.status == "approved",
                    )
                    approved_record = session.exec(statement).first()

                    if not approved_record:
                        # Pause task execution and transition to AWAITING_APPROVAL
                        validate_transition(task.status, TaskState.AWAITING_APPROVAL.value)
                        task.status = TaskState.AWAITING_APPROVAL.value

                        # Create approval record with parameter hash
                        expires_at = (
                            datetime.now(timezone.utc) + timedelta(minutes=self.APPROVAL_TIMEOUT_MINUTES)
                        ).isoformat()
                        approval = ApprovalRecord(
                            task_id=task.id,
                            step_index=idx,
                            tool_name=tool_name,
                            target=target,
                            parameters_json=json.dumps(parameters),
                            parameter_hash=ApprovalRecord.compute_hash(parameters),
                            reason=decision.reason,
                            risk_level=decision.risk_level.value,
                            status="pending",
                            expires_at=expires_at,
                        )
                        session.add(approval)
                        task.set_plan(plan)
                        session.add(task)
                        session.commit()

                        self._record_audit(
                            session,
                            event_type="approval_requested",
                            task_id=task.id,
                            tool_name=tool_name,
                            summary=f"Approval requested for tool '{tool_name}' on target '{target}'",
                            details={"reason": decision.reason, "expires_at": expires_at},
                        )
                        notification_service.send(
                            title="Approval Required",
                            body=f"Tool '{tool_name}' requires authorization on '{target}'.",
                            priority=NotificationPriority.APPROVAL_REQUIRED,
                            task_id=task.id,
                        )
                        # Halt execution until user approval is received
                        break

                # Case C: Permitted or Approved — Execute Scoped Tool
                current_step["status"] = "running"
                task.set_plan(plan)
                session.add(task)
                session.commit()

            # Execute tool asynchronously outside the database session
            try:
                result = await tool.execute(parameters)
                step_status = "completed"
                step_error = None
            except Exception as exc:
                logger.exception("Error executing tool %s", tool_name)
                result = {"error": str(exc)}
                step_status = "failed"
                step_error = str(exc)

            # Update step outcome in database
            with Session(engine, expire_on_commit=False) as session:
                task = session.get(TaskRecord, task_id)
                if not task:
                    break
                plan = task.get_plan()
                plan[idx]["status"] = step_status
                plan[idx]["result"] = str(result)
                task.set_plan(plan)

                if step_status == "failed":
                    task.status = TaskState.FAILED.value
                    task.error = step_error
                    session.add(task)
                    session.commit()
                    self._record_audit(
                        session,
                        event_type="tool_failed",
                        task_id=task.id,
                        tool_name=tool_name,
                        summary=f"Tool '{tool_name}' execution failed: {step_error}",
                    )
                    notification_service.send(
                        title="Task Failed",
                        body=f"Tool '{tool_name}' failed: {step_error}",
                        priority=NotificationPriority.ERROR,
                        task_id=task.id,
                    )
                    break
                else:
                    task.current_step_index += 1
                    session.add(task)
                    session.commit()
                    self._record_audit(
                        session,
                        event_type="tool_invoked",
                        task_id=task.id,
                        tool_name=tool_name,
                        summary=f"Tool '{tool_name}' executed successfully.",
                        details={"result": redact_dict(result)},
                    )

        with Session(engine, expire_on_commit=False) as session:
            task = session.get(TaskRecord, task_id)
            return task

    async def decide_approval(self, approval_id: str, decision: str) -> ApprovalRecord:
        """Handle human approval decision ('approved' or 'rejected')."""
        with Session(engine, expire_on_commit=False) as session:
            approval = session.get(ApprovalRecord, approval_id)
            if not approval:
                raise ValueError(f"Approval request '{approval_id}' not found.")

            if approval.status != "pending":
                raise ValueError(f"Approval is already resolved with status '{approval.status}'.")

            # Check expiration
            now = datetime.now(timezone.utc)
            expires_at = datetime.fromisoformat(approval.expires_at)
            if now > expires_at:
                approval.status = "expired"
                session.add(approval)
                session.commit()
                raise ValueError("Approval request has expired and cannot be authorized.")

            # Validate parameter hash to guarantee zero payload tampering
            current_hash = ApprovalRecord.compute_hash(approval.get_parameters())
            if current_hash != approval.parameter_hash:
                approval.status = "rejected"
                session.add(approval)
                session.commit()
                raise ValueError("Security violation: Approval parameter hash mismatch (tampering detected).")

            if decision.lower() in ("approve", "approved"):
                approval.status = "approved"
                session.add(approval)
                session.commit()
                self._record_audit(
                    session,
                    event_type="approval_decided",
                    task_id=approval.task_id,
                    tool_name=approval.tool_name,
                    summary=f"Approval GRANTED for '{approval.tool_name}' on target '{approval.target}'",
                )
            else:
                approval.status = "rejected"
                task = session.get(TaskRecord, approval.task_id)
                if task:
                    task.status = TaskState.FAILED.value
                    task.error = f"Human user rejected approval for '{approval.tool_name}'."
                    session.add(task)
                session.add(approval)
                session.commit()
                self._record_audit(
                    session,
                    event_type="approval_decided",
                    task_id=approval.task_id,
                    tool_name=approval.tool_name,
                    summary=f"Approval REJECTED by user for '{approval.tool_name}'",
                )
                return approval

        # Resume execution if approved
        await self.execute_task(approval.task_id)
        with Session(engine, expire_on_commit=False) as session:
            return session.get(ApprovalRecord, approval_id)

    def cancel_task(self, task_id: str) -> TaskRecord:
        """Cancel a task immediately."""
        with Session(engine, expire_on_commit=False) as session:
            task = session.get(TaskRecord, task_id)
            if not task:
                raise ValueError(f"Task '{task_id}' not found.")

            validate_transition(task.status, TaskState.CANCELLED.value)
            task.status = TaskState.CANCELLED.value
            task.completed_at = datetime.now(timezone.utc).isoformat()
            task.summary = "Task cancelled by user."
            session.add(task)
            session.commit()
            session.refresh(task)

            self._record_audit(
                session,
                event_type="task_cancelled",
                task_id=task.id,
                summary="Task cancelled by user request.",
            )
            notification_service.send(
                title="Task Cancelled",
                body="Task cancelled by user.",
                priority=NotificationPriority.WARNING,
                task_id=task.id,
            )
            return task

    def _generate_plan(self, instruction: str) -> List[Dict[str, Any]]:
        """Generate structured bounded plan from user natural language instruction."""
        lowered = instruction.lower()

        # Plan for dispatch / sending requests
        if any(w in lowered for w in ("send", "dispatch", "transmit", "post")):
            return [
                {
                    "step_number": 1,
                    "description": "Draft content and format payload",
                    "tool_name": "draft_generator_tool",
                    "target": "internal",
                    "parameters": {"topic": instruction, "instructions": "Review format"},
                    "status": "pending",
                },
                {
                    "step_number": 2,
                    "description": "Transmit content to destination (Approval Required)",
                    "tool_name": "external_dispatch_tool",
                    "target": "external-service",
                    "parameters": {"target_destination": "https://api.approved-service.com", "payload": instruction},
                    "status": "pending",
                },
            ]

        # Plan for reading / summarizing requests
        if any(w in lowered for w in ("read", "summarize", "analyze", "explain")):
            return [
                {
                    "step_number": 1,
                    "description": "Read application status and telemetry",
                    "tool_name": "app_status_tool",
                    "target": "127.0.0.1",
                    "parameters": {"include_domains": True},
                    "status": "pending",
                },
                {
                    "step_number": 2,
                    "description": "Summarize provided instruction",
                    "tool_name": "text_summarizer_tool",
                    "target": "memory",
                    "parameters": {"content": instruction, "max_sentences": 2},
                    "status": "pending",
                },
            ]

        # Default bounded plan
        return [
            {
                "step_number": 1,
                "description": "Check system status and configuration",
                "tool_name": "app_status_tool",
                "target": "127.0.0.1",
                "parameters": {"include_domains": True},
                "status": "pending",
            }
        ]

    def _record_audit(
        self,
        session: Session,
        event_type: str,
        summary: str,
        task_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write audit event to database and append-only audit log file."""
        details_json = json.dumps(redact_dict(details)) if details else None
        event = AuditEventRecord(
            event_type=event_type,
            task_id=task_id,
            tool_name=tool_name,
            summary=summary,
            details_json=details_json,
        )
        session.add(event)
        session.commit()

        # Append to audit file
        try:
            with open("aitmate_audit.log", "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "id": event.id,
                            "timestamp": event.timestamp,
                            "event_type": event_type,
                            "task_id": task_id,
                            "tool_name": tool_name,
                            "summary": summary,
                        }
                    )
                    + "\n"
                )
        except Exception as e:
            logger.warning("Could not write to audit log file: %s", e)


# Global orchestrator instance
orchestrator = Orchestrator()
