from typing import Optional, Tuple
from app.core.config import settings
from app.core.logger import get_logger
from app.services.ai.base import BaseAIProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.mock_provider import MockAIProvider

logger = get_logger("ai_factory")


def get_ai_provider(requested_provider: Optional[str] = None) -> Tuple[BaseAIProvider, str, str]:
    """
    Factory function resolving the appropriate AI Provider based on settings and API key availability.
    Returns: (provider_instance, provider_name, model_name)
    """
    target = (requested_provider or settings.DEFAULT_PROVIDER or "auto").lower()

    # 1. Explicit OpenAI
    if target == "openai":
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
            logger.info("Using OpenAI Provider")
            return OpenAIProvider(settings.OPENAI_API_KEY, settings.OPENAI_MODEL), "openai", settings.OPENAI_MODEL
        logger.warning("OpenAI requested but OPENAI_API_KEY not configured. Falling back to Mock Simulation.")
        return MockAIProvider(model="simulation-v1"), "mock", "simulation-v1"

    # 2. Explicit Gemini
    if target == "gemini":
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            logger.info("Using Google Gemini Provider")
            return GeminiProvider(settings.GEMINI_API_KEY, settings.GEMINI_MODEL), "gemini", settings.GEMINI_MODEL
        logger.warning("Gemini requested but GEMINI_API_KEY not configured. Falling back to Mock Simulation.")
        return MockAIProvider(model="simulation-v1"), "mock", "simulation-v1"

    # 3. Explicit Mock
    if target == "mock":
        return MockAIProvider(model="simulation-v1"), "mock", "simulation-v1"

    # 4. Auto-Resolution
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
        logger.info("Auto-selected OpenAI Provider")
        return OpenAIProvider(settings.OPENAI_API_KEY, settings.OPENAI_MODEL), "openai", settings.OPENAI_MODEL

    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        logger.info("Auto-selected Google Gemini Provider")
        return GeminiProvider(settings.GEMINI_API_KEY, settings.GEMINI_MODEL), "gemini", settings.GEMINI_MODEL

    logger.info("No external AI API keys found in environment. Initializing High-Fidelity Mock Provider.")
    return MockAIProvider(model="simulation-v1"), "mock", "simulation-v1"
