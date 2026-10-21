"""Local Ollama Provider Adapter with Structured Output and Timeouts."""

import json
import logging
import time
from typing import Any, Dict, List
import httpx
from backend.app.agent.providers.base import BaseAIProvider, PlannedStepSchema, ProviderTestResult
from backend.app.agent.providers.mock_provider import MockProvider
from backend.app.core.config import settings

logger = logging.getLogger("aitmate.provider.ollama")


class OllamaProvider(BaseAIProvider):
    """Local Ollama LLM provider adapter using loopback HTTP API."""

    name = "ollama"
    is_local = True

    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = settings.OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.fallback = MockProvider()

    async def test_connection(self) -> ProviderTestResult:
        """Query Ollama API to test availability and measure latency."""
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                latency = (time.perf_counter() - start) * 1000.0
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    model_found = self.model in models or any(self.model.split(":")[0] in m for m in models)
                    return ProviderTestResult(
                        provider_name=self.name,
                        is_available=True,
                        model_name=self.model if model_found else (models[0] if models else self.model),
                        latency_ms=round(latency, 2),
                        details=f"Ollama running at {self.base_url}. Installed models: {len(models)}",
                        is_local=True,
                    )
                return ProviderTestResult(
                    provider_name=self.name,
                    is_available=False,
                    details=f"Ollama responded with HTTP {res.status_code}",
                    is_local=True,
                )
        except Exception as e:
            return ProviderTestResult(
                provider_name=self.name,
                is_available=False,
                details=f"Ollama offline or unreachable at {self.base_url}: {str(e)}",
                is_local=True,
            )

    async def generate_plan(
        self,
        instruction: str,
        available_tools: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate structured plan from Ollama, with fallback on failure."""
        tool_names = [t["name"] for t in available_tools]
        system_prompt = (
            f"You are the planner for AitMate. Generate a JSON list of steps.\n"
            f"Available tools: {tool_names}.\n"
            f"Output ONLY a valid JSON array of objects with keys: step_number, description, tool_name, target, parameters."
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": instruction},
                    ],
                    "format": "json",
                    "stream": False,
                }
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("message", {}).get("content", "[]")
                    parsed = json.loads(content)
                    if isinstance(parsed, dict) and "steps" in parsed:
                        parsed = parsed["steps"]
                    if isinstance(parsed, list) and len(parsed) > 0:
                        # Validate each step with Pydantic
                        valid_steps = []
                        for s in parsed:
                            validated = PlannedStepSchema(**s)
                            valid_steps.append(validated.model_dump())
                        return valid_steps
        except Exception as exc:
            logger.warning("Ollama plan generation failed or timed out: %s. Using fallback.", exc)

        # Graceful fallback to deterministic mock planner
        return await self.fallback.generate_plan(instruction, available_tools)
