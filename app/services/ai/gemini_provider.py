import json
import httpx
from typing import Dict, Any, Optional
from app.services.ai.base import BaseAIProvider
from app.core.logger import get_logger

logger = get_logger("gemini_provider")


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini API Adapter supporting Gemini 1.5 Pro and Gemini 1.5 Flash.
    """
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        super().__init__(api_key, model)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def get_token_estimate(self, text: str) -> int:
        return max(1, len(text) // 4)

    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will strictly follow these instructions."}]
            })
            
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.4
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join([p.get("text", "") for p in parts]).strip()

    async def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        full_system = f"{system_prompt}\nYou MUST return a single valid JSON object. No explanation, no code fences."
        contents.append({
            "role": "user",
            "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{full_system}"}]
        })
        contents.append({
            "role": "model",
            "parts": [{"text": "Understood. I will respond ONLY with valid JSON."}]
        })
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return {}
            parts = candidates[0].get("content", {}).get("parts", [])
            raw_text = "".join([p.get("text", "") for p in parts]).strip()
            # Clean possible markdown wrapping if returned
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            return json.loads(raw_text.strip())
