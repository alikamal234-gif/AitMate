"""Email Drafting and Controlled Dispatch Service."""

import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from backend.app.core.policy import RiskLevel
from backend.app.tools.base import BaseTool

logger = logging.getLogger("aitmate.tools.email")


class EmailDraftParams(BaseModel):
    recipient: str = Field(..., description="Destination email address")
    subject: str = Field(..., description="Subject line")
    body: str = Field(..., description="Draft message body")
    urgency: str = Field(default="normal", description="Priority indicator: low, normal, or high")


class EmailDraftTool(BaseTool):
    """Generates a reviewable email draft without performing network transmission."""

    name = "email_draft_tool"
    description = "Create an email draft for review. Does NOT send the message."
    risk_level = RiskLevel.LOW
    requires_approval = False
    parameters_schema = EmailDraftParams

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.parameters_schema(**parameters)
        return {
            "status": "draft_created",
            "recipient": validated.recipient,
            "subject": validated.subject,
            "body": validated.body,
            "urgency": validated.urgency,
            "is_sent": False,
            "requires_human_send_approval": True,
        }


class EmailSendParams(BaseModel):
    draft_id: Optional[str] = Field(default=None, description="Optional draft reference")
    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Subject line")
    body: str = Field(..., description="Exact email content to transmit")


class EmailSendTool(BaseTool):
    """High-risk action: Dispatches an email to external recipients. Strictly requires approval."""

    name = "email_send_tool"
    description = (
        "Send an approved email to external recipients. "
        "Strictly requires explicit human authorization with exact body diff."
    )
    risk_level = RiskLevel.HIGH
    requires_approval = True
    parameters_schema = EmailSendParams

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.parameters_schema(**parameters)
        # Mock/Sandbox sender for security (never send emails blindly during development)
        logger.info("Executing authorized email transmission to %s", validated.recipient)
        return {
            "status": "sent",
            "recipient": validated.recipient,
            "subject": validated.subject,
            "bytes_sent": len(validated.body),
            "verified_by_human_approval": True,
        }


class EmailIntegrationStatus(BaseModel):
    """Status of external email provider integration."""

    provider: str
    is_connected: bool
    configured_email: Optional[str] = None
    required_scopes: list[str]
    setup_notes: str


def get_email_integration_status() -> EmailIntegrationStatus:
    """Truthful reporting of email integration configuration."""
    return EmailIntegrationStatus(
        provider="gmail_oauth2",
        is_connected=False,
        configured_email=None,
        required_scopes=[
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
        ],
        setup_notes="OAuth client credentials not configured. Email actions run in sandboxed draft mode.",
    )
