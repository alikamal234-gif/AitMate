"""Central Permission Engine & Tool Policy Enforcement."""

from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from pydantic import BaseModel
from backend.app.core.config import settings


class RiskLevel(str, Enum):
    """Categorized risk tiers for tool operations."""

    LOW = "LOW"        # Read-only, safe local summarization, app telemetry
    MEDIUM = "MEDIUM"  # Scoped local reading, drafting, allowlisted domain navigation
    HIGH = "HIGH"      # Mutations, external messaging, file writes/deletions, form submissions


class PolicyAction(str, Enum):
    """Policy evaluation outcomes."""

    PERMITTED = "PERMITTED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    DENIED = "DENIED"


class PolicyDecision(BaseModel):
    """Immutable outcome of a permission engine policy check."""

    action: PolicyAction
    risk_level: RiskLevel
    reason: str
    target: str
    requires_approval: bool = False


class PermissionEngine:
    """Central server-side policy enforcement engine.

    All tool calls must be passed through this engine before execution.
    The frontend is never trusted for authorization decisions.
    """

    def __init__(self, allowed_domains: Optional[List[str]] = None):
        self.allowed_domains = allowed_domains or settings.get_allowed_domain_list()

    def evaluate_tool_call(
        self,
        tool_name: str,
        target: str,
        parameters: Dict[str, Any],
        is_tool_high_risk: bool = False,
    ) -> PolicyDecision:
        """Evaluate a planned tool call against security policies."""
        cleaned_target = target.strip()

        # 1. Zero Unrestricted Shell Policy Check
        forbidden_tool_signatures = {"shell", "terminal", "exec", "system_command", "bash", "cmd"}
        if any(sig in tool_name.lower() for sig in forbidden_tool_signatures):
            return PolicyDecision(
                action=PolicyAction.DENIED,
                risk_level=RiskLevel.HIGH,
                reason="Direct or unrestricted shell execution is strictly prohibited by AitMate policy.",
                target=cleaned_target,
                requires_approval=False,
            )

        # 2. Check for shell injections or dangerous command parameters in arguments
        param_str = str(parameters).lower()
        dangerous_patterns = [
            "rm -rf",
            "format c:",
            "powershell -enc",
            "curl -o",
            "wget -o",
            "drop table",
            "drop database",
        ]
        if any(pat in param_str for pat in dangerous_patterns):
            return PolicyDecision(
                action=PolicyAction.DENIED,
                risk_level=RiskLevel.HIGH,
                reason=f"Dangerous command pattern detected in tool parameters: target={cleaned_target}",
                target=cleaned_target,
                requires_approval=False,
            )

        # 3. Domain Allowlist Check for Browser / Web Tools
        if "browser" in tool_name.lower() or "web" in tool_name.lower() or "http" in cleaned_target.lower():
            parsed_domain = self._extract_domain(cleaned_target)
            if parsed_domain and not self._is_domain_allowed(parsed_domain):
                return PolicyDecision(
                    action=PolicyAction.DENIED,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Domain '{parsed_domain}' is not in the approved domain allowlist: {self.allowed_domains}",
                    target=cleaned_target,
                    requires_approval=False,
                )

        # Dynamic Check: Browser form submission is high-risk
        if tool_name == "browser_tool" and parameters.get("action") == "submit_form":
            is_tool_high_risk = True

        # 4. High-Risk Tools Require Human Approval
        if is_tool_high_risk:
            return PolicyDecision(
                action=PolicyAction.REQUIRES_APPROVAL,
                risk_level=RiskLevel.HIGH,
                reason=f"Tool '{tool_name}' performs high-risk side effects on target '{cleaned_target}'.",
                target=cleaned_target,
                requires_approval=True,
            )

        # 5. Low-Risk Default Permission
        return PolicyDecision(
            action=PolicyAction.PERMITTED,
            risk_level=RiskLevel.LOW,
            reason=f"Tool '{tool_name}' operates within safe read-only or drafting boundaries.",
            target=cleaned_target,
            requires_approval=False,
        )

    def _extract_domain(self, target: str) -> Optional[str]:
        """Extract clean hostname from URL or target string."""
        if "://" in target:
            parsed = urlparse(target)
            return parsed.netloc.lower().split(":")[0]
        # Direct hostname
        return target.split("/")[0].split(":")[0].lower()

    def _is_domain_allowed(self, domain: str) -> bool:
        """Check if domain or a parent domain is in the allowlist."""
        for allowed in self.allowed_domains:
            if domain == allowed or domain.endswith("." + allowed):
                return True
        return False


# Global central policy engine instance
policy_engine = PermissionEngine()
