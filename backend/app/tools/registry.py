"""Registered Tools and Tool Registry Interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from backend.app.core.config import settings
from backend.app.core.policy import RiskLevel


class BaseTool(ABC):
    """Abstract base contract for all AitMate tools."""

    name: str
    description: str
    risk_level: RiskLevel
    requires_approval: bool
    parameters_schema: Type[BaseModel]

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with validated arguments."""
        pass


# -------------------------------------------------------------
# Tool 1: App Status Tool (Safe Read-Only)
# -------------------------------------------------------------
class AppStatusParams(BaseModel):
    include_domains: bool = Field(default=True, description="Whether to include domain list")


class AppStatusTool(BaseTool):
    name = "app_status_tool"
    description = "Read AitMate local agent status, version, and configured provider."
    risk_level = RiskLevel.LOW
    requires_approval = False
    parameters_schema = AppStatusParams

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.parameters_schema(**parameters)
        res = {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "provider": settings.AI_PROVIDER,
            "status": "operational",
        }
        if validated.include_domains:
            res["allowed_domains"] = settings.get_allowed_domain_list()
        return res


# -------------------------------------------------------------
# Tool 2: Text Summarizer Tool (Safe Local Computation)
# -------------------------------------------------------------
class SummarizerParams(BaseModel):
    content: str = Field(..., description="Text content to summarize")
    max_sentences: int = Field(default=3, description="Maximum summary sentences")


class TextSummarizerTool(BaseTool):
    name = "text_summarizer_tool"
    description = "Summarize user-provided or retrieved text into concise bullet points."
    risk_level = RiskLevel.LOW
    requires_approval = False
    parameters_schema = SummarizerParams

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.parameters_schema(**parameters)
        sentences = [s.strip() for s in validated.content.split(".") if s.strip()]
        chosen = sentences[: validated.max_sentences]
        summary_text = ". ".join(chosen) + ("." if chosen else "")
        return {
            "summary": summary_text,
            "sentence_count": len(chosen),
            "original_length": len(validated.content),
        }


# -------------------------------------------------------------
# Tool 3: Draft Generator Tool (Safe Drafting Without Sending)
# -------------------------------------------------------------
class DraftParams(BaseModel):
    topic: str = Field(..., description="Subject or topic of the draft")
    recipient: Optional[str] = Field(default=None, description="Optional intended recipient")
    instructions: Optional[str] = Field(default=None, description="Drafting style or context")


class DraftGeneratorTool(BaseTool):
    name = "draft_generator_tool"
    description = "Draft response or note without performing any transmission."
    risk_level = RiskLevel.LOW
    requires_approval = False
    parameters_schema = DraftParams

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.parameters_schema(**parameters)
        draft_body = (
            f"Draft Briefing: {validated.topic}\n"
            f"Prepared for: {validated.recipient or 'Internal Review'}\n\n"
            f"Summary Notes: {validated.instructions or 'Standard draft'}\n"
            f"Status: DRAFT_ONLY (Not Sent)"
        )
        return {
            "topic": validated.topic,
            "recipient": validated.recipient,
            "draft_body": draft_body,
            "is_sent": False,
        }


# -------------------------------------------------------------
# Tool 4: Scoped File Reader Tool (Medium Risk, Local Workspace Only)
# -------------------------------------------------------------
class FileReaderParams(BaseModel):
    relative_path: str = Field(..., description="Relative file path within workspace")


class ScopedFileReaderTool(BaseTool):
    name = "file_reader_tool"
    description = "Read a file from within the authorized workspace."
    risk_level = RiskLevel.MEDIUM
    requires_approval = False
    parameters_schema = FileReaderParams

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        import os
        validated = self.parameters_schema(**parameters)
        cleaned_path = os.path.normpath(validated.relative_path)
        # Prevent directory traversal
        if cleaned_path.startswith("..") or os.path.isabs(cleaned_path):
            raise PermissionError("Access denied: File access outside the workspace is prohibited.")

        if not os.path.exists(cleaned_path):
            raise FileNotFoundError(f"File not found: {cleaned_path}")

        with open(cleaned_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(50000)  # Max 50KB read bound

        return {
            "path": cleaned_path,
            "bytes_read": len(content),
            "content": content,
        }


# -------------------------------------------------------------
# Tool 5: External Dispatch Tool (High Risk — Human Approval Required)
# -------------------------------------------------------------
class DispatchParams(BaseModel):
    target_destination: str = Field(..., description="Destination address, URL, or channel")
    payload: str = Field(..., description="Exact content to transmit")
    urgency: str = Field(default="normal", description="Urgency level: normal or high")


class ExternalDispatchTool(BaseTool):
    name = "external_dispatch_tool"
    description = "Transmit content or perform side-effect actions outside the local environment."
    risk_level = RiskLevel.HIGH
    requires_approval = True
    parameters_schema = DispatchParams

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.parameters_schema(**parameters)
        return {
            "status": "dispatched",
            "target": validated.target_destination,
            "bytes_transmitted": len(validated.payload),
            "verified_by_human_approval": True,
        }


# -------------------------------------------------------------
# Central Tool Registry
# -------------------------------------------------------------
class ToolRegistry:
    """Manages all registered, mediated tool instances."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # Auto-register core baseline tools
        self.register(AppStatusTool())
        self.register(TextSummarizerTool())
        self.register(DraftGeneratorTool())
        self.register(ScopedFileReaderTool())
        self.register(ExternalDispatchTool())

    def register(self, tool: BaseTool) -> None:
        """Register a new mediated tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Lookup tool by name."""
        return self._tools.get(name)

    def list_all(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "risk_level": tool.risk_level.value,
                "requires_approval": tool.requires_approval,
                "schema": tool.parameters_schema.model_json_schema(),
            }
            for tool in self._tools.values()
        ]


# Global tool registry instance
tool_registry = ToolRegistry()
