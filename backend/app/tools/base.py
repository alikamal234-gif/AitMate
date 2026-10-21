"""Base Tool Interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type
from pydantic import BaseModel
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
