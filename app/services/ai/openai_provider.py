import json
import httpx
from typing import Dict, Any, Optional
from app.services.ai.base import BaseAIProvider
from app.core.logger import get_logger

logger = get_logger("openai_provider")


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI API Adapter supporting GPT-4o, GPT-4o-mini, and compatible models.
    """
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(api_key, model)
        self.base_url = "https://api.openai.com/v1"

    def get_token_estimate(self, text: str) -> int:
        # Standard rule of thumb: ~4 characters per token
        return max(1, len(text) // 4)

    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    async def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        full_system = f"{system_prompt}\nReturn ONLY a valid JSON object. No Markdown code fences, no extra text."
        messages.append({"role": "system", "content": full_system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"].strip()
            return json.loads(raw_content)
