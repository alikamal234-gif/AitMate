"""Typed Pydantic Schemas for Local API Contracts."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Public health and connectivity verification payload."""

    status: str = Field(default="ok", description="Overall backend health status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application semantic version")
    bound_host: str = Field(..., description="Bound loopback interface")
    bound_port: int = Field(..., description="Bound local port")
    active_provider: str = Field(..., description="Configured AI provider (e.g. mock, ollama)")
    allowed_domains: List[str] = Field(..., description="Whitelisted domains for browser automation")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp",
    )


class SystemStatusResponse(BaseModel):
    """Authenticated diagnostic and telemetry status."""

    status: str
    version: str
    active_tasks: int
    pending_approvals: int
    db_connected: bool
    provider_available: bool
    allowed_domains_count: int
    session_token_prefix: str = Field(
        ...,
        description="First 6 characters of active session token for identification",
    )


class ApiError(BaseModel):
    """Structured error contract."""

    error: str
    detail: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
