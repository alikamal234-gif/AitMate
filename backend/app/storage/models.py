"""SQLModel Database Models for Tasks, Approvals, and Audit Logs."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlmodel import Field, SQLModel


def generate_uuid() -> str:
    """Generate a clean hex UUID string."""
    return str(uuid.uuid4())


def utc_now_iso() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class TaskRecord(SQLModel, table=True):
    """Persistent task entity managed by the deterministic state machine."""

    __tablename__ = "tasks"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    instruction: str = Field(..., description="Original user instruction")
    status: str = Field(
        default="queued",
        index=True,
        description="FSM state: queued, planning, awaiting_approval, running, completed, failed, cancelled",
    )
    plan_json: str = Field(
        default="[]",
        description="Serialized list of PlanStep dictionaries",
    )
    current_step_index: int = Field(default=0)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    completed_at: Optional[str] = Field(default=None)
    summary: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)

    def get_plan(self) -> List[Dict[str, Any]]:
        """Deserialize plan JSON."""
        try:
            return json.loads(self.plan_json)
        except Exception:
            return []

    def set_plan(self, plan: List[Dict[str, Any]]) -> None:
        """Serialize plan JSON."""
        self.plan_json = json.dumps(plan)


class ApprovalRecord(SQLModel, table=True):
    """Pending or decided human authorization gate record."""

    __tablename__ = "approvals"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    task_id: str = Field(..., index=True, description="Associated task ID")
    step_index: int = Field(default=0, description="Step index awaiting approval")
    tool_name: str = Field(..., description="Target tool name")
    target: str = Field(..., description="Action target (e.g. domain, recipient, file)")
    parameters_json: str = Field(..., description="Exact JSON serialized parameters")
    parameter_hash: str = Field(
        ...,
        description="Cryptographic SHA-256 hash of parameters to prevent tampering",
    )
    reason: str = Field(..., description="Human-understandable justification")
    risk_level: str = Field(default="HIGH", description="LOW, MEDIUM, or HIGH")
    status: str = Field(
        default="pending",
        index=True,
        description="pending, approved, rejected, expired",
    )
    created_at: str = Field(default_factory=utc_now_iso)
    expires_at: str = Field(..., description="Timestamp after which approval cannot be granted")

    @classmethod
    def compute_hash(cls, parameters: Dict[str, Any]) -> str:
        """Compute deterministic SHA-256 hash of serialized parameters."""
        sorted_json = json.dumps(parameters, sort_keys=True)
        return hashlib.sha256(sorted_json.encode("utf-8")).hexdigest()

    def get_parameters(self) -> Dict[str, Any]:
        """Deserialize parameters JSON."""
        try:
            return json.loads(self.parameters_json)
        except Exception:
            return {}


class AuditEventRecord(SQLModel, table=True):
    """Append-only audit record of task lifecycles and tool decisions."""

    __tablename__ = "audit_events"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    timestamp: str = Field(default_factory=utc_now_iso, index=True)
    event_type: str = Field(
        ...,
        index=True,
        description="task_created, state_transition, tool_invocation, approval_requested, approval_decided, task_completed, task_cancelled, task_failed, security_violation",
    )
    task_id: Optional[str] = Field(default=None, index=True)
    tool_name: Optional[str] = Field(default=None)
    summary: str = Field(..., description="Human-readable event description")
    details_json: Optional[str] = Field(default=None)

    def get_details(self) -> Dict[str, Any]:
        """Deserialize details JSON."""
        if not self.details_json:
            return {}
        try:
            return json.loads(self.details_json)
        except Exception:
            return {}


class MemoryRecord(SQLModel, table=True):
    """User-controlled local memory entity."""

    __tablename__ = "memories"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    key: str = Field(..., index=True, description="Topic, preference key, or identifier")
    content: str = Field(..., description="Stored text memory or preference value")
    category: str = Field(default="preference", index=True, description="preference, snippet, project, custom")
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

