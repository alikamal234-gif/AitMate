"""Groq Cloud Provider Adapter with Ultra-Fast LPU Inference."""

import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from backend.app.agent.providers.base import BaseAIProvider, PlannedStepSchema, ProviderTestResult
from backend.app.agent.providers.mock_provider import MockProvider
from backend.app.core.config import settings

logger = logging.getLogger("aitmate.provider.groq")


class GroqProvider(BaseAIProvider):
    """Ultra-fast Groq LPU provider adapter using OpenAI-compatible chat API."""

    name = "groq"
    is_local = False

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = settings.GROQ_MODEL,
        base_url: str = settings.GROQ_BASE_URL,
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.base_url = (base_url or settings.GROQ_BASE_URL).rstrip("/")
        self.fallback = MockProvider()

    async def test_connection(self) -> ProviderTestResult:
        """Test Groq API reachability, validate API key, and measure latency."""
        if not self.api_key:
            return ProviderTestResult(
                provider_name=self.name,
                is_available=False,
                model_name=self.model,
                details="Groq API key is missing. Set GROQ_API_KEY=gsk_... in your .env file or Settings.",
                is_local=False,
            )

        start = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(f"{self.base_url}/models", headers=headers)
                latency = (time.perf_counter() - start) * 1000.0
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("id") for m in data.get("data", [])]
                    model_found = self.model in models
                    return ProviderTestResult(
                        provider_name=self.name,
                        is_available=True,
                        model_name=self.model if model_found else (models[0] if models else self.model),
                        latency_ms=round(latency, 2),
                        details=f"Groq LPU operational. Model: {self.model} (Latency: {round(latency, 1)}ms)",
                        is_local=False,
                    )
                elif res.status_code == 401:
                    return ProviderTestResult(
                        provider_name=self.name,
                        is_available=False,
                        model_name=self.model,
                        details="Groq authentication failed: Invalid API key (HTTP 401).",
                        is_local=False,
                    )
                else:
                    return ProviderTestResult(
                        provider_name=self.name,
                        is_available=False,
                        model_name=self.model,
                        details=f"Groq API returned HTTP {res.status_code}: {res.text[:120]}",
                        is_local=False,
                    )
        except Exception as exc:
            return ProviderTestResult(
                provider_name=self.name,
                is_available=False,
                model_name=self.model,
                details=f"Unable to connect to Groq endpoint ({self.base_url}): {str(exc)}",
                is_local=False,
            )

    async def generate_plan(
        self,
        instruction: str,
        available_tools: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate structured plan using Groq LPU with fallback on network/key failure."""
        if not self.api_key:
            logger.warning("Groq API key not provided. Falling back to deterministic plan.")
            return await self.fallback.generate_plan(instruction, available_tools)

        tool_specs = [
            {"name": t["name"], "description": t["description"], "parameters": t.get("schema", {})}
            for t in available_tools
        ]

        system_prompt = (
            "You are the autonomous planning engine for AitMate desktop assistant.\n"
            "Given the user instruction, analyze the goal and decompose it into a bounded sequence of tool calls.\n"
            f"Available tools: {json.dumps(tool_specs)}\n\n"
            "Respond ONLY with a JSON object containing a 'steps' array matching this structure:\n"
            "{\n"
            '  "steps": [\n'
            '    {\n'
            '      "step_number": 1,\n'
            '      "description": "Short explanation",\n'
            '      "tool_name": "exact_tool_name_from_list",\n'
            '      "target": "file or url or service target",\n'
            '      "parameters": { ... }\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": instruction},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if res.status_code == 200:
                    data = res.json()
                    raw_content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(raw_content)
                    steps_list = parsed.get("steps", parsed if isinstance(parsed, list) else [])
                    if isinstance(steps_list, list) and len(steps_list) > 0:
                        validated_steps = []
                        for s in steps_list:
                            step_obj = PlannedStepSchema(**s)
                            validated_steps.append(step_obj.model_dump())
                        return validated_steps
                else:
                    logger.error("Groq plan generation returned HTTP %d: %s", res.status_code, res.text[:200])
        except Exception as exc:
            logger.warning("Groq plan generation failed: %s. Using safe fallback.", exc)

        return await self.fallback.generate_plan(instruction, available_tools)
