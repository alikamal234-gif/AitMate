"""AI Provider Factory."""

from backend.app.agent.providers.base import BaseAIProvider
from backend.app.agent.providers.mock_provider import MockProvider
from backend.app.agent.providers.ollama_provider import OllamaProvider
from backend.app.core.config import settings


def get_ai_provider() -> BaseAIProvider:
    """Instantiate and return the configured AI provider adapter."""
    provider_type = settings.AI_PROVIDER.lower().strip()
    if provider_type == "ollama":
        return OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
        )
    # Default safe mock provider
    return MockProvider()


# Global active provider instance
active_provider = get_ai_provider()
