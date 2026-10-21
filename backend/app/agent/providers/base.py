"""Base AI Provider Interface and Structured Contracts."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProviderTestResult(BaseModel):
    """Result of provider connectivity test."""

    provider_name: str
    is_available: bool
    model_name: Optional[str] = None
    latency_ms: Optional[float] = None
    details: str
    is_local: bool


class PlannedStepSchema(BaseModel):
    """Validated structured plan step from model output."""

    step_number: int = Field(..., ge=1, le=10)
    description: str = Field(..., min_length=3)
    tool_name: str = Field(..., min_length=2)
    target: str = Field(default="localhost")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class BaseAIProvider(ABC):
    """Abstract model provider contract for AitMate."""

    name: str
    is_local: bool

    @abstractmethod
    async def generate_plan(
        self,
        instruction: str,
        available_tools: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate a validated, bounded execution plan from user instruction."""
        pass

    @abstractmethod
    async def test_connection(self) -> ProviderTestResult:
        """Test provider availability and report latency."""
        pass
