from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAIProvider(ABC):
    """
    Abstract AI Provider Interface.
    Enforces a standardized contract across OpenAI, Google Gemini, Anthropic, and local LLMs.
    """
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generates standard text completion."""
        pass

    @abstractmethod
    async def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generates structured JSON output strictly conforming to the requested schema."""
        pass

    @abstractmethod
    def get_token_estimate(self, text: str) -> int:
        """Rough token count estimation for observability & cost tracking."""
        pass
