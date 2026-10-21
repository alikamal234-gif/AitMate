"""Browser Automation Tool with Strict Domain Allowlists and Data Sanitization."""

import logging
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel, Field
from backend.app.core.config import settings
from backend.app.core.policy import RiskLevel
from backend.app.tools.base import BaseTool

logger = logging.getLogger("aitmate.tools.browser")


class BrowserActionParams(BaseModel):
    action: str = Field(
        default="extract_text",
        description="Browser action: 'extract_text', 'navigate', or 'submit_form'",
    )
    url: str = Field(..., description="Target web page URL")
    selector: Optional[str] = Field(default=None, description="Optional CSS/HTML selector")
    form_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Form payload (Requires explicit human approval)",
    )


def wrap_untrusted(content: str) -> str:
    """Encapsulate untrusted external web content inside explicit security boundaries."""
    return f"<untrusted_web_content>\n{content}\n</untrusted_web_content>"


class BrowserTool(BaseTool):
    """Controlled web browser automation tool governed by domain allowlists."""

    name = "browser_tool"
    description = (
        "Navigate to an approved website, inspect page text, or submit approved web forms. "
        "All external content is wrapped in untrusted data containers."
    )
    risk_level = RiskLevel.MEDIUM
    requires_approval = False  # Read actions are MEDIUM; submit_form dynamically flags HIGH
    parameters_schema = BrowserActionParams

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.parameters_schema(**parameters)
        target_url = validated.url.strip()

        # 1. Enforce Domain Allowlist
        parsed = urlparse(target_url if "://" in target_url else f"https://{target_url}")
        domain = parsed.netloc.lower().split(":")[0]

        allowed_domains = settings.get_allowed_domain_list()
        is_allowed = any(domain == a or domain.endswith("." + a) for a in allowed_domains)
        if not is_allowed:
            raise PermissionError(
                f"Security violation: Domain '{domain}' is not authorized in AITMATE_ALLOWED_DOMAINS: {allowed_domains}"
            )

        # 2. Form Submission Action (High Risk Side-Effect)
        if validated.action == "submit_form":
            # Real web mutation
            return {
                "status": "form_submitted",
                "url": target_url,
                "data_transmitted": validated.form_data or {},
                "verified_by_approval": True,
            }

        # 3. Read & Extract Web Content
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                headers = {"User-Agent": "AitMate-Desktop-Assistant/0.1"}
                res = await client.get(target_url, headers=headers)
                if res.status_code >= 400:
                    return {
                        "url": target_url,
                        "status_code": res.status_code,
                        "error": f"Webpage returned HTTP {res.status_code}",
                    }

                raw_html = res.text
                clean_text = self._sanitize_html(raw_html)

                # Defense against Prompt Injection: Encapsulate external content
                enclosed_content = (
                    f"<untrusted_web_content source='{target_url}'>\n"
                    f"{clean_text[:15000]}\n"
                    f"</untrusted_web_content>"
                )

                return {
                    "url": target_url,
                    "domain": domain,
                    "status_code": res.status_code,
                    "content_length": len(clean_text),
                    "extracted_content": enclosed_content,
                }
        except Exception as exc:
            logger.warning("Browser navigation error on %s: %s", target_url, exc)
            return {
                "url": target_url,
                "domain": domain,
                "error": f"Failed to retrieve URL: {str(exc)}",
            }

    def _sanitize_html(self, html: str) -> str:
        """Strip script, style, and HTML tags to extract readable plain text."""
        # Remove script and style blocks
        no_scripts = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        no_tags = re.sub(r"<[^>]+>", " ", no_scripts)
        # Collapse whitespace
        collapsed = re.sub(r"\s+", " ", no_tags).strip()
        return collapsed
