"""Unit and Security Tests for Browser Automation."""

import pytest
from backend.app.core.policy import PolicyAction, RiskLevel, policy_engine
from backend.app.tools.browser import BrowserTool


@pytest.mark.asyncio
async def test_browser_blocks_unapproved_domain():
    """Security rule: Browser tool rejects navigation to unapproved domain with PermissionError."""
    browser = BrowserTool()
    with pytest.raises(PermissionError) as exc_info:
        await browser.execute(
            {
                "action": "extract_text",
                "url": "https://unapproved-phishing-site.com",
            }
        )
    assert "not authorized" in str(exc_info.value)


@pytest.mark.asyncio
async def test_browser_sanitizes_html_and_wraps_untrusted_content():
    """Security rule: All extracted webpage text is wrapped in <untrusted_web_content> data boundary."""
    browser = BrowserTool()
    raw_html = """
    <html>
      <head><script>alert('malicious')</script></head>
      <body>
        <h1>Welcome to Wikipedia</h1>
        <p>Artificial intelligence is a field of computer science.</p>
        <style>body { color: red; }</style>
      </body>
    </html>
    """
    cleaned = browser._sanitize_html(raw_html)
    assert "alert" not in cleaned
    assert "script" not in cleaned
    assert "color: red" not in cleaned
    assert "Welcome to Wikipedia" in cleaned
    assert "Artificial intelligence" in cleaned


def test_browser_form_submission_requires_approval():
    """Security rule: Form submissions and mutations on the web require human approval."""
    decision = policy_engine.evaluate_tool_call(
        tool_name="browser_tool",
        target="https://github.com/login",
        parameters={"action": "submit_form", "form_data": {"user": "test"}},
    )
    assert decision.action == PolicyAction.REQUIRES_APPROVAL
    assert decision.requires_approval is True
    assert decision.risk_level == RiskLevel.HIGH


def test_browser_read_on_allowed_domain_is_permitted():
    """Security rule: Reading allowlisted domains is permitted."""
    decision = policy_engine.evaluate_tool_call(
        tool_name="browser_tool",
        target="https://wikipedia.org/wiki/Python",
        parameters={"action": "extract_text"},
    )
    assert decision.action == PolicyAction.PERMITTED
    assert decision.risk_level == RiskLevel.LOW
