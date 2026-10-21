"""Deterministic Mock AI Provider for Safe Offline Operation and Tests."""

import time
from typing import Any, Dict, List
from backend.app.agent.providers.base import BaseAIProvider, ProviderTestResult


class MockProvider(BaseAIProvider):
    """Zero-cost, offline deterministic provider requiring no API keys or local GPU."""

    name = "mock"
    is_local = True

    async def generate_plan(
        self,
        instruction: str,
        available_tools: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate structured plan matching registered tools based on instruction keywords."""
        lowered = instruction.lower()

        # Plan for external dispatch / sending
        if any(w in lowered for w in ("send", "dispatch", "transmit", "post")):
            return [
                {
                    "step_number": 1,
                    "description": "Draft content and format payload",
                    "tool_name": "draft_generator_tool",
                    "target": "internal",
                    "parameters": {"topic": instruction, "instructions": "Review format"},
                },
                {
                    "step_number": 2,
                    "description": "Transmit content to destination (Approval Required)",
                    "tool_name": "external_dispatch_tool",
                    "target": "external-service",
                    "parameters": {"target_destination": "https://api.approved-service.com", "payload": instruction},
                },
            ]

        # Plan for reading / summarizing / explaining
        if any(w in lowered for w in ("read", "summarize", "analyze", "explain")):
            return [
                {
                    "step_number": 1,
                    "description": "Read application status and telemetry",
                    "tool_name": "app_status_tool",
                    "target": "127.0.0.1",
                    "parameters": {"include_domains": True},
                },
                {
                    "step_number": 2,
                    "description": "Summarize provided instruction",
                    "tool_name": "text_summarizer_tool",
                    "target": "memory",
                    "parameters": {"content": instruction, "max_sentences": 2},
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
            }
        ]

    async def test_connection(self) -> ProviderTestResult:
        """Simulate instantaneous healthy local test."""
        start = time.perf_counter()
        # Simulated fast local check
        latency = (time.perf_counter() - start) * 1000.0
        return ProviderTestResult(
            provider_name=self.name,
            is_available=True,
            model_name="deterministic-mock-v1",
            latency_ms=round(latency + 0.5, 2),
            details="Mock provider is operational. Offline zero-cost execution active.",
            is_local=True,
        )
